"""Approved-T4 execution adapter for the frozen M1 embedding stage.

This module owns execution selection and runtime verification only.  It reuses
the profile-bound windowing, pooling, normalization, and release-artifact stage
without changing the M1 EmbeddingProfile.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import platform
import time
from typing import Any

from .acquisition import sha256_file
from .embedding import VECTOR_DIMENSION, pool_and_normalize, profile_windows, read_canonical_contigs
from .embedding_stage import EmbeddingStageError, execute_embedding_stage, load_eligible_records


PROFILE_ID = "m1-generanno-prokaryote-0.5b-assembly-v1"
CANONICALIZATION_ID = "m1-assembly-canonical-v1"
ADEE_ID = "m1-generanno-t4-cuda12.1-fp32-deterministic-v1"
EXPECTED_RECORD_COUNT = 12
SNAPSHOT_DOWNLOAD_ATTEMPTS = 5
SNAPSHOT_DOWNLOAD_WORKERS = 1


class T4ReleaseError(RuntimeError):
    """The approved M1 T4 environment or release inputs are invalid."""


@dataclass(frozen=True, slots=True)
class ApprovedT4Environment:
    """The digest-pinned execution declaration selected by the BuildManifest."""

    declaration_path: Path
    declaration_digest: str
    payload: Mapping[str, object]

    @property
    def model(self) -> Mapping[str, object]:
        return _mapping(self.payload.get("model"), "ADEE model")

    @property
    def runtime(self) -> Mapping[str, object]:
        return _mapping(self.payload.get("runtime"), "ADEE runtime")

    @property
    def accelerator(self) -> Mapping[str, object]:
        return _mapping(self.payload.get("accelerator"), "ADEE accelerator")

    @property
    def numeric_policy(self) -> Mapping[str, object]:
        return _mapping(self.payload.get("numeric_policy"), "ADEE numeric policy")


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise T4ReleaseError(f"{label} must be an object")
    return value


def _string(mapping: Mapping[str, object], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise T4ReleaseError(f"{label}.{key} must be a non-empty string")
    return value


def load_approved_t4_environment(declaration_path: Path) -> ApprovedT4Environment:
    """Load exactly the M1 ADEE declaration and bind it to its file digest."""

    try:
        payload = json.loads(declaration_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise T4ReleaseError("cannot read approved T4 execution declaration") from error
    if not isinstance(payload, dict):
        raise T4ReleaseError("approved T4 execution declaration must be an object")
    if payload.get("execution_environment_id") != ADEE_ID:
        raise T4ReleaseError("execution declaration is not the approved M1 T4 environment")
    if payload.get("kind") != "approved-deterministic-execution-environment":
        raise T4ReleaseError("execution declaration has an unexpected kind")
    environment = ApprovedT4Environment(declaration_path, sha256_file(declaration_path), payload)
    if _string(environment.runtime, "python", "ADEE runtime") != "3.12.13":
        raise T4ReleaseError("approved T4 declaration has an unexpected Python version")
    if _string(environment.runtime, "torch", "ADEE runtime") != "2.4.1+cu121":
        raise T4ReleaseError("approved T4 declaration has an unexpected torch version")
    if _string(environment.runtime, "transformers", "ADEE runtime") != "4.44.0":
        raise T4ReleaseError("approved T4 declaration has an unexpected transformers version")
    if _string(environment.accelerator, "device_name", "ADEE accelerator") != "Tesla T4":
        raise T4ReleaseError("approved T4 declaration has an unexpected accelerator")
    if _string(environment.accelerator, "cuda", "ADEE accelerator") != "12.1":
        raise T4ReleaseError("approved T4 declaration has an unexpected CUDA version")
    if _string(environment.model, "artifact", "ADEE model") != "GenerTeam/GENERanno-prokaryote-0.5b-base":
        raise T4ReleaseError("approved T4 declaration has an unexpected model artifact")
    return environment


def validate_release_build_manifest(build_manifest_path: Path, environment: ApprovedT4Environment) -> tuple[str, str]:
    """Verify that a BuildManifest explicitly selects this ADEE and M1 profile."""

    try:
        manifest = json.loads(build_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise T4ReleaseError("cannot read T4 release BuildManifest") from error
    if not isinstance(manifest, dict):
        raise T4ReleaseError("T4 release BuildManifest must be an object")
    build_id = manifest.get("build_id")
    if not isinstance(build_id, str) or not build_id:
        raise T4ReleaseError("T4 release BuildManifest lacks a build_id")
    if manifest.get("canonicalization_profile") != CANONICALIZATION_ID:
        raise T4ReleaseError("T4 release BuildManifest has an unexpected canonicalization profile")
    if manifest.get("embedding_profiles") != [PROFILE_ID]:
        raise T4ReleaseError("T4 release BuildManifest must select the sole M1 embedding profile")
    inventory = manifest.get("source_inventory")
    if not isinstance(inventory, list) or len(inventory) != 1 or not isinstance(inventory[0], dict):
        raise T4ReleaseError("T4 release BuildManifest must contain one source inventory")
    record_versions_digest = inventory[0].get("record_versions_digest")
    if not isinstance(record_versions_digest, str):
        raise T4ReleaseError("T4 release BuildManifest lacks the canonical record-table digest")
    plugins = manifest.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1 or not isinstance(plugins[0], dict):
        raise T4ReleaseError("T4 release BuildManifest must contain one plugin declaration")
    selection = plugins[0].get("execution_environment")
    if not isinstance(selection, dict):
        raise T4ReleaseError("T4 release BuildManifest does not select an execution environment")
    if selection.get("id") != ADEE_ID or selection.get("declaration_digest") != environment.declaration_digest:
        raise T4ReleaseError("T4 release BuildManifest ADEE selection does not match the approved declaration")
    return build_id, record_versions_digest


def _configure_t4_determinism(torch: Any, environment: ApprovedT4Environment) -> None:
    policy = environment.numeric_policy
    cublas = _string(policy, "cublas_workspace_config", "ADEE numeric policy")
    existing = os.environ.get("CUBLAS_WORKSPACE_CONFIG")
    if existing is not None and existing != cublas:
        raise T4ReleaseError("CUBLAS_WORKSPACE_CONFIG conflicts with the approved T4 declaration")
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = cublas
    if not torch.cuda.is_available():
        raise T4ReleaseError("approved M1 release generation requires CUDA on a Tesla T4")
    if torch.version.cuda != _string(environment.accelerator, "cuda", "ADEE accelerator"):
        raise T4ReleaseError("CUDA runtime does not match the approved T4 declaration")
    if torch.cuda.get_device_name(0) != _string(environment.accelerator, "device_name", "ADEE accelerator"):
        raise T4ReleaseError("CUDA device does not match the approved T4 declaration")
    torch.manual_seed(int(policy["seed"]))
    torch.cuda.manual_seed_all(int(policy["seed"]))
    torch.use_deterministic_algorithms(bool(policy["deterministic_algorithms"]))
    torch.backends.cudnn.benchmark = bool(policy["cudnn_benchmark"])
    torch.backends.cudnn.deterministic = bool(policy["cudnn_deterministic"])
    torch.backends.cuda.matmul.allow_tf32 = bool(policy["tf32"])
    torch.backends.cudnn.allow_tf32 = bool(policy["tf32"])


def _download_pinned_snapshot(environment: ApprovedT4Environment, destination: Path) -> Path:
    """Download the pinned model revision once and verify its immutable weight."""

    from huggingface_hub import snapshot_download
    from huggingface_hub.errors import HfHubHTTPError, LocalEntryNotFoundError

    model = environment.model
    snapshot: Path | None = None
    failure: Exception | None = None
    for attempt in range(1, SNAPSHOT_DOWNLOAD_ATTEMPTS + 1):
        try:
            snapshot = Path(
                snapshot_download(
                    _string(model, "artifact", "ADEE model"),
                    revision=_string(model, "revision", "ADEE model"),
                    local_dir=destination,
                    max_workers=SNAPSHOT_DOWNLOAD_WORKERS,
                )
            )
            break
        except (HfHubHTTPError, LocalEntryNotFoundError) as error:
            failure = error
            if attempt == SNAPSHOT_DOWNLOAD_ATTEMPTS:
                raise T4ReleaseError("pinned model snapshot download failed after retrying") from error
            time.sleep(2 ** (attempt - 1))
    if snapshot is None:
        raise T4ReleaseError("pinned model snapshot download did not return a path") from failure
    if sha256_file(snapshot / "model.safetensors") != _string(model, "weight_digest", "ADEE model"):
        raise T4ReleaseError("pinned model weight digest mismatch")
    return snapshot


@dataclass(slots=True)
class PinnedT4Embedder:
    """One verified, float32 T4 model instance reused across all M1 records."""

    torch: Any
    tokenizer: Any
    model: Any
    snapshot_path: Path

    def __call__(self, canonical_path: Path, snapshot_path: Path, _weight_digest: str, timings: dict[str, float]) -> tuple[float, ...]:
        if snapshot_path.resolve() != self.snapshot_path.resolve():
            raise T4ReleaseError("embedding stage attempted to use a different model snapshot")
        started = time.perf_counter()
        windows = profile_windows(read_canonical_contigs(canonical_path))
        timings["window_generation_seconds"] = time.perf_counter() - started
        timings["window_count"] = float(len(windows))
        tokenization_seconds = 0.0
        forward_seconds = 0.0
        window_vectors: list[tuple[float, ...]] = []
        for window in windows:
            started = time.perf_counter()
            encoded = self.tokenizer(window, add_special_tokens=False, return_tensors="pt").to("cuda")
            tokenization_seconds += time.perf_counter() - started
            started = time.perf_counter()
            with self.torch.inference_mode():
                hidden = self.model(**encoded, output_hidden_states=True).hidden_states[-1][0, 0, :]
            forward_seconds += time.perf_counter() - started
            window_vectors.append(tuple(float(value) for value in hidden.to("cpu", dtype=self.torch.float32).tolist()))
        timings["tokenization_seconds"] = tokenization_seconds
        timings["forward_seconds"] = forward_seconds
        started = time.perf_counter()
        vector = pool_and_normalize(tuple(window_vectors))
        timings["pooling_and_normalization_seconds"] = time.perf_counter() - started
        if len(vector) != VECTOR_DIMENSION or not all(math.isfinite(value) for value in vector):
            raise T4ReleaseError("T4 adapter produced an invalid embedding vector")
        return vector


def _load_t4_embedder(environment: ApprovedT4Environment, snapshot_directory: Path) -> tuple[PinnedT4Embedder, dict[str, object]]:
    """Load the declared model after every runtime and weight check has passed."""

    policy = environment.numeric_policy
    cublas = _string(policy, "cublas_workspace_config", "ADEE numeric policy")
    existing = os.environ.get("CUBLAS_WORKSPACE_CONFIG")
    if existing is not None and existing != cublas:
        raise T4ReleaseError("CUBLAS_WORKSPACE_CONFIG conflicts with the approved T4 declaration")
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = cublas
    try:
        import torch
        import transformers
        from transformers import AutoModelForMaskedLM, AutoTokenizer
    except ImportError as error:
        raise T4ReleaseError("approved T4 runner dependencies are not installed") from error
    if platform.python_version() != _string(environment.runtime, "python", "ADEE runtime"):
        raise T4ReleaseError("Python runtime does not match the approved T4 declaration")
    if torch.__version__ != _string(environment.runtime, "torch", "ADEE runtime"):
        raise T4ReleaseError("torch runtime does not match the approved T4 declaration")
    if transformers.__version__ != _string(environment.runtime, "transformers", "ADEE runtime"):
        raise T4ReleaseError("transformers runtime does not match the approved T4 declaration")
    _configure_t4_determinism(torch, environment)
    snapshot = _download_pinned_snapshot(environment, snapshot_directory)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, trust_remote_code=True, local_files_only=True)
    model = AutoModelForMaskedLM.from_pretrained(
        snapshot, trust_remote_code=True, local_files_only=True, torch_dtype=torch.float32
    ).to("cuda").eval()
    runtime = {
        "execution_environment_id": ADEE_ID,
        "execution_environment_declaration_digest": environment.declaration_digest,
        "accelerator": torch.cuda.get_device_name(0),
        "cuda": torch.version.cuda,
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "precision": _string(policy, "precision", "ADEE numeric policy"),
        "seed": policy["seed"],
        "deterministic_algorithms": policy["deterministic_algorithms"],
        "cublas_workspace_config": cublas,
        "cudnn_benchmark": policy["cudnn_benchmark"],
        "cudnn_deterministic": policy["cudnn_deterministic"],
        "tf32": policy["tf32"],
        "window_batch_size": policy["window_batch_size"],
        "inference_mode": policy["inference_mode"],
        "model_artifact": _string(environment.model, "artifact", "ADEE model"),
        "model_revision": _string(environment.model, "revision", "ADEE model"),
        "model_weight_digest": _string(environment.model, "weight_digest", "ADEE model"),
        "tokenizer_revision": _string(environment.model, "tokenizer_revision", "ADEE model"),
    }
    return PinnedT4Embedder(torch, tokenizer, model, snapshot), runtime


def execute_t4_release_stage(
    *,
    record_versions_path: Path,
    canonical_directory: Path,
    workspace: Path,
    build_manifest_path: Path,
    execution_environment_path: Path,
) -> dict[str, object]:
    """Generate the M1 release embedding artifacts under the approved T4 ADEE."""

    environment = load_approved_t4_environment(execution_environment_path)
    build_id, expected_record_table_digest = validate_release_build_manifest(build_manifest_path, environment)
    if sha256_file(record_versions_path) != expected_record_table_digest:
        raise T4ReleaseError("record-version table does not match the T4 release BuildManifest")
    records = load_eligible_records(record_versions_path, canonical_directory)
    if len(records) != EXPECTED_RECORD_COUNT:
        raise T4ReleaseError("T4 release generation requires exactly the 12 canonical M1 records")
    snapshot_directory = workspace / "pinned-model-snapshot"
    embedder, runner_provenance = _load_t4_embedder(environment, snapshot_directory)
    try:
        return execute_embedding_stage(
            record_versions_path=record_versions_path,
            canonical_directory=canonical_directory,
            snapshot_path=snapshot_directory,
            expected_weight_digest=_string(environment.model, "weight_digest", "ADEE model"),
            workspace=workspace,
            build_id=build_id,
            runner_provenance=runner_provenance,
            embedder=embedder,
        )
    except EmbeddingStageError as error:
        raise T4ReleaseError(str(error)) from error


def main(argv: list[str] | None = None) -> int:
    """Run the release-eligible M1.5 stage on the approved Colab T4 runtime."""

    parser = argparse.ArgumentParser(description="Generate M1.5 release artifacts on the approved deterministic T4 environment.")
    parser.add_argument("--record-versions", type=Path, required=True)
    parser.add_argument("--canonical-directory", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--build-manifest", type=Path, required=True)
    parser.add_argument("--execution-environment", type=Path, required=True)
    args = parser.parse_args(argv)
    envelope = execute_t4_release_stage(
        record_versions_path=args.record_versions,
        canonical_directory=args.canonical_directory,
        workspace=args.workspace,
        build_manifest_path=args.build_manifest,
        execution_environment_path=args.execution_environment,
    )
    print(json.dumps(envelope, sort_keys=True, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
