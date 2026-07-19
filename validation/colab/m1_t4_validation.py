"""Non-release T4 validation harness for the frozen M1 embedding algorithm."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import struct
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "atlas-builder" / "src"))

# Required by CUDA >= 10.2 for deterministic CuBLAS operations. This must be
# set before importing torch or initializing CUDA.
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

from expedia_atlas_builder.embedding import (  # noqa: E402
    BOS_PREFIX,
    VECTOR_DIMENSION,
    pool_and_normalize,
    profile_windows,
    read_canonical_contigs,
)

MODEL_ID = "GenerTeam/GENERanno-prokaryote-0.5b-base"
REVISION = "d02db0f24f2c62fa1efde760217cdf75771b0228"
WEIGHT_DIGEST = "sha256:ed1cfcc64fe890a6a72017d24c02ad6af3b15c9cfa6950e850908cca92882d51"
PROFILE_ID = "m1-generanno-prokaryote-0.5b-assembly-v1"
CANONICALIZATION_ID = "m1-assembly-canonical-v1"
EXPECTED_RECORD_COUNT = 12
SNAPSHOT_DOWNLOAD_WORKERS = 1
SNAPSHOT_DOWNLOAD_ATTEMPTS = 5


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def configure_t4_determinism(torch: object) -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("a CUDA T4 runtime is required for this validation harness")
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


@dataclass(frozen=True, slots=True)
class BatchRecord:
    """One M1.4-verified canonical input for non-release batch validation."""

    accession: str
    record_id: str
    sequence_digest: str
    canonical_path: Path


def load_batch_records(
    canonical_directory: Path,
    record_versions_path: Path,
    expected_accessions: tuple[str, ...],
    expected_record_versions_digest: str,
) -> tuple[BatchRecord, ...]:
    """Accept only the exact M1.4 record table and all of its canonical inputs."""

    if not record_versions_path.is_file():
        raise RuntimeError(f"missing uploaded M1.4 record-version table: {record_versions_path}")
    if not canonical_directory.is_dir():
        raise RuntimeError(f"missing uploaded M1.4 canonical directory: {canonical_directory}")
    if sha256(record_versions_path) != expected_record_versions_digest:
        raise RuntimeError("canonical record-version table digest does not match committed M1.4 evidence")
    try:
        rows = [json.loads(line) for line in record_versions_path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("cannot read canonical record-version table") from error
    if not all(isinstance(row, dict) for row in rows):
        raise RuntimeError("canonical record-version table contains a non-object row")
    by_record_id = {row.get("record_id"): row for row in rows}
    if len(by_record_id) != len(rows):
        raise RuntimeError("canonical record-version table contains duplicate record identifiers")
    records: list[BatchRecord] = []
    expected_ids = {f"ncbi-assembly:{accession}:{CANONICALIZATION_ID}" for accession in expected_accessions}
    if set(by_record_id) != expected_ids:
        raise RuntimeError("canonical record-version table does not contain exactly the frozen M1 records")
    for accession in expected_accessions:
        record_id = f"ncbi-assembly:{accession}:{CANONICALIZATION_ID}"
        row = by_record_id[record_id]
        if row.get("lifecycle_state") != "eligible" or row.get("canonicalization_id") != CANONICALIZATION_ID:
            raise RuntimeError(f"record is not M1 eligible: {record_id}")
        sequence_digest = row.get("sequence_digest")
        if not isinstance(sequence_digest, str):
            raise RuntimeError(f"record lacks a sequence digest: {record_id}")
        canonical_path = canonical_directory / f"{accession}.txt"
        if not canonical_path.is_file() or sha256(canonical_path) != sequence_digest:
            raise RuntimeError(f"canonical input digest mismatch: {record_id}")
        records.append(BatchRecord(accession, record_id, sequence_digest, canonical_path))
    if len(records) != EXPECTED_RECORD_COUNT:
        raise RuntimeError("M1 accelerator validation requires exactly 12 records")
    return tuple(records)


def _m1_batch_inputs() -> tuple[tuple[str, ...], str]:
    inventory = json.loads((ROOT / "atlas-builder" / "manifests" / "m1" / "m1-refseq-accessions.json").read_text())
    accessions = tuple(item["accession"] for item in inventory["assemblies"])
    stage = json.loads((ROOT / "atlas-builder" / "manifests" / "m1" / "m1-canonicalization-stage-outcome.json").read_text())
    record_versions = next(
        artifact for artifact in stage["output_artifacts"] if artifact["path"].endswith("genome-record-versions.jsonl")
    )
    return accessions, record_versions["digest"]


def _load_pinned_model(output_dir: Path) -> tuple[Any, Any, Any, dict[str, object]]:
    import torch
    import transformers
    from huggingface_hub import snapshot_download
    from huggingface_hub.errors import HfHubHTTPError, LocalEntryNotFoundError
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    configure_t4_determinism(torch)
    started = time.perf_counter()
    snapshot_error: Exception | None = None
    snapshot: Path | None = None
    for attempt in range(1, SNAPSHOT_DOWNLOAD_ATTEMPTS + 1):
        try:
            snapshot = Path(
                snapshot_download(
                    MODEL_ID,
                    revision=REVISION,
                    local_dir=output_dir / "snapshot",
                    max_workers=SNAPSHOT_DOWNLOAD_WORKERS,
                )
            )
            break
        except (HfHubHTTPError, LocalEntryNotFoundError) as error:
            snapshot_error = error
            if attempt == SNAPSHOT_DOWNLOAD_ATTEMPTS:
                raise RuntimeError("pinned model snapshot download failed after retrying") from error
            time.sleep(2 ** (attempt - 1))
    if snapshot is None:
        raise RuntimeError("pinned model snapshot download did not return a local path") from snapshot_error
    if sha256(snapshot / "model.safetensors") != WEIGHT_DIGEST:
        raise RuntimeError("pinned model weight digest mismatch")
    tokenizer = AutoTokenizer.from_pretrained(snapshot, trust_remote_code=True, local_files_only=True)
    model = AutoModelForMaskedLM.from_pretrained(
        snapshot, trust_remote_code=True, torch_dtype=torch.float32, local_files_only=True
    ).to("cuda").eval()
    runtime = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0),
        "deterministic_algorithms": True,
        "tf32": False,
        "cublas_workspace_config": os.environ["CUBLAS_WORKSPACE_CONFIG"],
        "snapshot_download_workers": SNAPSHOT_DOWNLOAD_WORKERS,
        "snapshot_download_attempt_limit": SNAPSHOT_DOWNLOAD_ATTEMPTS,
        "model_load_seconds": time.perf_counter() - started,
    }
    return torch, tokenizer, model, runtime


def _embed_record(torch: Any, tokenizer: Any, model: Any, canonical_path: Path) -> tuple[tuple[float, ...], dict[str, float], int]:
    started = time.perf_counter()
    windows = profile_windows(read_canonical_contigs(canonical_path))
    window_generation_seconds = time.perf_counter() - started
    tokenization_seconds = 0.0
    forward_seconds = 0.0
    vectors: list[tuple[float, ...]] = []
    for window in windows:
        started = time.perf_counter()
        encoded = tokenizer(window, add_special_tokens=False, return_tensors="pt").to("cuda")
        tokenization_seconds += time.perf_counter() - started
        started = time.perf_counter()
        with torch.inference_mode():
            hidden = model(**encoded, output_hidden_states=True).hidden_states[-1][0, 0, :]
        forward_seconds += time.perf_counter() - started
        vectors.append(tuple(float(value) for value in hidden.to("cpu", dtype=torch.float32).tolist()))
    started = time.perf_counter()
    vector = pool_and_normalize(tuple(vectors))
    pooling_and_normalization_seconds = time.perf_counter() - started
    if len(vector) != VECTOR_DIMENSION:
        raise RuntimeError("unexpected embedding dimension")
    return vector, {
        "window_generation_seconds": window_generation_seconds,
        "tokenization_seconds": tokenization_seconds,
        "forward_seconds": forward_seconds,
        "pooling_and_normalization_seconds": pooling_and_normalization_seconds,
    }, len(windows)


def _write_vector(path: Path, vector: tuple[float, ...]) -> None:
    path.write_bytes(struct.pack(f"<{VECTOR_DIMENSION}f", *vector))


def _inspect_vector(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    if len(payload) != VECTOR_DIMENSION * 4:
        raise RuntimeError("serialized vector has an unexpected byte length")
    vector = struct.unpack(f"<{VECTOR_DIMENSION}f", payload)
    if not all(math.isfinite(value) for value in vector):
        raise RuntimeError("serialized vector contains non-finite values")
    norm = math.sqrt(sum(value * value for value in vector))
    if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise RuntimeError("serialized vector is not L2 normalized")
    return {"dimension": len(vector), "dtype": "float32le", "l2_norm": norm, "digest": sha256(path)}


def run(canonical_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    torch, tokenizer, model, runtime = _load_pinned_model(output_dir)
    started = time.perf_counter()
    vector, timings, window_count = _embed_record(torch, tokenizer, model, canonical_path)
    vector_path = output_dir / "vector.float32le"
    serialization_started = time.perf_counter()
    _write_vector(vector_path, vector)
    timings["serialization_seconds"] = time.perf_counter() - serialization_started
    metadata = {
        "validation_only": True,
        "profile_id": PROFILE_ID,
        "model": {"id": MODEL_ID, "revision": REVISION, "weight_digest": WEIGHT_DIGEST},
        "algorithm": {"bos_prefix": BOS_PREFIX, "window_bases": 8191, "window_count": window_count, "pooling": "arithmetic-mean-of-window-vectors", "normalization": "l2", "dtype": "float32"},
        "runtime": runtime,
        "timing": {**timings, "forward_pipeline_seconds": time.perf_counter() - started},
        "vector_digest": _inspect_vector(vector_path)["digest"],
    }
    (output_dir / "validation-metadata.json").write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")


def run_batch(canonical_directory: Path, record_versions_path: Path, output_dir: Path) -> None:
    """Validate all M1 canonical records on T4 without producing release artifacts."""

    expected_accessions, expected_table_digest = _m1_batch_inputs()
    records = load_batch_records(canonical_directory, record_versions_path, expected_accessions, expected_table_digest)
    output_dir.mkdir(parents=True, exist_ok=True)
    torch, tokenizer, model, runtime = _load_pinned_model(output_dir)
    runtime_identity = {key: value for key, value in runtime.items() if key != "model_load_seconds"}
    run_identity = {
        "validation_only": True,
        "profile_id": PROFILE_ID,
        "model": {"id": MODEL_ID, "revision": REVISION, "weight_digest": WEIGHT_DIGEST},
        "algorithm": {"bos_prefix": BOS_PREFIX, "window_bases": 8191, "pooling": "arithmetic-mean-of-window-vectors", "normalization": "l2", "dtype": "float32"},
        "record_versions_digest": expected_table_digest,
        "records": [{"accession": record.accession, "record_id": record.record_id, "sequence_digest": record.sequence_digest} for record in records],
        "runtime": runtime_identity,
    }
    identity_path = output_dir / "validation-run-identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != run_identity:
        raise RuntimeError("existing batch workspace does not match the frozen validation configuration")
    if not identity_path.exists():
        identity_path.write_text(json.dumps(run_identity, sort_keys=True, indent=2) + "\n")
    records_dir = output_dir / "records"
    records_dir.mkdir(exist_ok=True)
    completed: list[dict[str, object]] = []
    for position, record in enumerate(records, start=1):
        vector_path = records_dir / f"{record.accession}.float32le"
        record_metadata_path = records_dir / f"{record.accession}.json"
        if vector_path.exists() and record_metadata_path.exists():
            metadata = json.loads(record_metadata_path.read_text())
            vector_state = _inspect_vector(vector_path)
            if metadata.get("record_id") != record.record_id or metadata.get("sequence_digest") != record.sequence_digest or metadata.get("vector") != vector_state:
                raise RuntimeError(f"existing validation evidence is invalid for {record.accession}")
            completed.append(metadata)
            print(f"reused {position}/{len(records)} {record.accession}", flush=True)
            continue
        if vector_path.exists() or record_metadata_path.exists():
            raise RuntimeError(f"incomplete validation evidence for {record.accession}; use a new output directory")
        print(f"embedding {position}/{len(records)} {record.accession}", flush=True)
        started = time.perf_counter()
        vector, timing, window_count = _embed_record(torch, tokenizer, model, record.canonical_path)
        serialization_started = time.perf_counter()
        _write_vector(vector_path, vector)
        timing["serialization_seconds"] = time.perf_counter() - serialization_started
        metadata = {
            "validation_only": True,
            "record_id": record.record_id,
            "accession": record.accession,
            "sequence_digest": record.sequence_digest,
            "algorithm": {"window_count": window_count, "normalization": "l2", "dtype": "float32"},
            "timing": {**timing, "forward_pipeline_seconds": time.perf_counter() - started},
            "vector": _inspect_vector(vector_path),
            "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        record_metadata_path.write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")
        completed.append(metadata)
        print(f"completed {position}/{len(records)} {record.accession}", flush=True)
    if len(completed) != EXPECTED_RECORD_COUNT or len({item["record_id"] for item in completed}) != EXPECTED_RECORD_COUNT:
        raise RuntimeError("batch validation has missing or duplicate record evidence")
    final_metadata = {
        **run_identity,
        "validation_scope": "m1.5-accelerator-implementation-validation",
        "timing": {"model_load_seconds": runtime["model_load_seconds"]},
        "validation_checks": {"expected_record_count": EXPECTED_RECORD_COUNT, "record_count": len(completed), "missing_records": [], "duplicate_records": [], "all_vectors_finite": True, "all_vectors_l2_normalized": True, "all_provenance_complete": True},
        "records": completed,
        "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    (output_dir / "validation-metadata.json").write_text(json.dumps(final_metadata, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path)
    parser.add_argument("--canonical-directory", type=Path)
    parser.add_argument("--record-versions", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.canonical is not None and args.canonical_directory is None and args.record_versions is None:
        run(args.canonical, args.output_dir)
    elif args.canonical is None and args.canonical_directory is not None and args.record_versions is not None:
        run_batch(args.canonical_directory, args.record_versions, args.output_dir)
    else:
        parser.error("provide --canonical, or provide both --canonical-directory and --record-versions")
