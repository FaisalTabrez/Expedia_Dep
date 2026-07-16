"""Contract-bound, resumable execution for the frozen M1.5 embedding stage.

The stage is intentionally sequential: it emits one float32 vector for each
eligible canonical record in the existing record-table order.  The resume file
is explicit, input-bound state; it cannot be reused with changed records,
weights, profile, or build identity.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import json
import math
from pathlib import Path
import platform
import struct
from typing import Any

from .acquisition import sha256_file
from .embedding import VECTOR_DIMENSION, embed_assembly_from_local_snapshot


PROFILE_ID = "m1-generanno-prokaryote-0.5b-assembly-v1"
PROFILE_VERSION = "0.1.0"
SHARD_ID = "m1-generanno-prokaryote-0.5b-assembly-v1-vectors-000"
CANONICALIZATION_ID = "m1-assembly-canonical-v1"
CHECKPOINT_NAME = "embedding-resume-state.json"
PARTIAL_VECTOR_NAME = "vectors.partial.float32le"
VECTOR_NAME = "vectors.float32le"
INSTANCES_NAME = "embedding-instances.jsonl"
SHARD_MANIFEST_NAME = "vector-shard-manifest.json"
STAGE_ENVELOPE_NAME = "embedding-stage-envelope.json"


class EmbeddingStageError(RuntimeError):
    """The M1.5 stage cannot safely continue or emit a release artifact."""


@dataclass(frozen=True, slots=True)
class EligibleRecord:
    """A record table entry and its canonical input, verified before inference."""

    record_id: str
    sequence_digest: str
    canonical_path: Path

    @property
    def accession(self) -> str:
        prefix = "ncbi-assembly:"
        suffix = f":{CANONICALIZATION_ID}"
        if not self.record_id.startswith(prefix) or not self.record_id.endswith(suffix):
            raise EmbeddingStageError("record_id is not an M1 canonical assembly record")
        return self.record_id[len(prefix) : -len(suffix)]


Embedder = Callable[[Path, Path, str, dict[str, float]], tuple[float, ...]]


def collect_cpu_runner_provenance() -> dict[str, object]:
    """Capture the runner facts required to distinguish release evidence."""

    try:
        import torch
        import transformers
    except ImportError as error:
        raise EmbeddingStageError("pinned M1 runner is not available") from error
    if torch.cuda.is_available():
        raise EmbeddingStageError("M1 profile forbids GPU execution")
    return {
        "runner_environment": "m1-generanno-reference-runner-v1",
        "determinism_declaration": "m1-generanno-cpu-fp32-determinism-v1",
        "accelerator": "CPU only",
        "precision": "float32",
        "torch": str(torch.__version__),
        "transformers": str(transformers.__version__),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "seed": 0,
        "threads": 1,
        "interop_threads": 1,
        "deterministic_algorithms": True,
        "mkldnn": "disabled",
        "inference_mode": True,
    }


def execute_embedding_stage(
    *,
    record_versions_path: Path,
    canonical_directory: Path,
    snapshot_path: Path,
    expected_weight_digest: str,
    workspace: Path,
    build_id: str,
    runner_provenance: Mapping[str, object] | None = None,
    embedder: Embedder = embed_assembly_from_local_snapshot,
) -> dict[str, object]:
    """Create one M1 vector shard and one EmbeddingInstance per eligible record.

    A failed run retains only the explicitly hashed resume state and partial
    vectors.  It never writes a shard manifest or EmbeddingInstance table until
    all records have completed and passed validation.
    """

    if not build_id.strip():
        raise EmbeddingStageError("build_id must be non-empty")
    records = load_eligible_records(record_versions_path, canonical_directory)
    if not records:
        raise EmbeddingStageError("embedding stage requires at least one eligible record")
    workspace.mkdir(parents=True, exist_ok=True)
    provenance = dict(runner_provenance) if runner_provenance is not None else collect_cpu_runner_provenance()
    if not provenance:
        raise EmbeddingStageError("runner provenance must not be empty")
    run_spec = _run_spec(records, build_id, expected_weight_digest, provenance)
    partial_path = workspace / PARTIAL_VECTOR_NAME
    checkpoint_path = workspace / CHECKPOINT_NAME
    completed = _load_or_initialize_checkpoint(checkpoint_path, partial_path, run_spec)
    try:
        for row, record in enumerate(records):
            if row < completed:
                continue
            timings: dict[str, float] = {}
            vector = embedder(record.canonical_path, snapshot_path, expected_weight_digest, timings)
            _validate_vector(vector)
            _append_vector(partial_path, vector)
            _write_json(
                checkpoint_path,
                {"run_spec": run_spec, "completed_rows": row + 1, "last_timings": timings},
            )
        return _finalize_stage(workspace, records, build_id, expected_weight_digest, provenance, partial_path)
    except Exception as error:
        envelope = _failed_envelope(record_versions_path, workspace, str(error))
        _write_json(workspace / STAGE_ENVELOPE_NAME, envelope)
        if isinstance(error, EmbeddingStageError):
            raise
        raise EmbeddingStageError("embedding inference failed; checkpoint is retained for exact resume") from error


def load_eligible_records(record_versions_path: Path, canonical_directory: Path) -> tuple[EligibleRecord, ...]:
    """Load each eligible M1 record once, preserving canonical table order."""

    try:
        rows = [json.loads(line) for line in record_versions_path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, json.JSONDecodeError) as error:
        raise EmbeddingStageError("cannot read canonical record-version table") from error
    records: list[EligibleRecord] = []
    seen_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise EmbeddingStageError("record-version table contains a non-object row")
        if row.get("lifecycle_state") != "eligible":
            continue
        record_id = row.get("record_id")
        sequence_digest = row.get("sequence_digest")
        canonicalization_id = row.get("canonicalization_id")
        if not isinstance(record_id, str) or not isinstance(sequence_digest, str):
            raise EmbeddingStageError("eligible record lacks an identity or sequence digest")
        if canonicalization_id != CANONICALIZATION_ID:
            raise EmbeddingStageError("eligible record has an undeclared canonicalization profile")
        if record_id in seen_ids:
            raise EmbeddingStageError("record-version table contains duplicate eligible record_id")
        provisional = EligibleRecord(record_id, sequence_digest, canonical_directory / "placeholder")
        path = canonical_directory / f"{provisional.accession}.txt"
        if not path.is_file():
            raise EmbeddingStageError(f"missing canonical input for {record_id}")
        if sha256_file(path) != sequence_digest:
            raise EmbeddingStageError(f"canonical input digest mismatch for {record_id}")
        seen_ids.add(record_id)
        records.append(EligibleRecord(record_id, sequence_digest, path))
    return tuple(records)


def _run_spec(
    records: Sequence[EligibleRecord], build_id: str, expected_weight_digest: str, runner_provenance: Mapping[str, object]
) -> dict[str, object]:
    return {
        "build_id": build_id,
        "profile_id": PROFILE_ID,
        "profile_version": PROFILE_VERSION,
        "weight_digest": expected_weight_digest,
        "records": [{"record_id": record.record_id, "sequence_digest": record.sequence_digest} for record in records],
        "runner_provenance": dict(runner_provenance),
    }


def _load_or_initialize_checkpoint(checkpoint_path: Path, partial_path: Path, run_spec: Mapping[str, object]) -> int:
    if not checkpoint_path.exists():
        if partial_path.exists():
            raise EmbeddingStageError("partial vector exists without explicit resume state")
        _write_json(checkpoint_path, {"run_spec": run_spec, "completed_rows": 0, "last_timings": {}})
        return 0
    try:
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise EmbeddingStageError("cannot read embedding resume state") from error
    if not isinstance(checkpoint, dict) or checkpoint.get("run_spec") != run_spec:
        raise EmbeddingStageError("resume state does not match this frozen embedding run")
    completed = checkpoint.get("completed_rows")
    if isinstance(completed, bool) or not isinstance(completed, int) or completed < 0:
        raise EmbeddingStageError("resume state has an invalid completed row count")
    expected_bytes = completed * VECTOR_DIMENSION * 4
    actual_bytes = partial_path.stat().st_size if partial_path.exists() else 0
    if actual_bytes != expected_bytes:
        raise EmbeddingStageError("partial vector length does not match explicit resume state")
    return completed


def _append_vector(path: Path, vector: Sequence[float]) -> None:
    with path.open("ab") as handle:
        handle.write(struct.pack(f"<{VECTOR_DIMENSION}f", *vector))
        handle.flush()


def _validate_vector(vector: Sequence[float]) -> None:
    if len(vector) != VECTOR_DIMENSION:
        raise EmbeddingStageError("model output dimension does not match the profile")
    if not all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in vector):
        raise EmbeddingStageError("embedding vector contains non-finite values")
    norm = math.sqrt(sum(float(value) * float(value) for value in vector))
    if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise EmbeddingStageError("embedding vector is not L2 normalized within float32 tolerance")


def _finalize_stage(
    workspace: Path,
    records: Sequence[EligibleRecord],
    build_id: str,
    expected_weight_digest: str,
    runner_provenance: Mapping[str, object],
    partial_path: Path,
) -> dict[str, object]:
    if partial_path.stat().st_size != len(records) * VECTOR_DIMENSION * 4:
        raise EmbeddingStageError("completed vector shard has an unexpected byte length")
    vector_path = workspace / VECTOR_NAME
    if vector_path.exists():
        raise EmbeddingStageError("final vector shard already exists; use a new workspace")
    partial_path.replace(vector_path)
    digest = sha256_file(vector_path)
    row_mapping = {str(row): _instance_id(record.record_id) for row, record in enumerate(records)}
    shard_manifest = {
        "profile_id": PROFILE_ID,
        "shard_id": SHARD_ID,
        "dimension": VECTOR_DIMENSION,
        "dtype": "float32",
        "row_mapping": row_mapping,
        "digest": digest,
        "build_provenance": {
            "build_id": build_id,
            "model_weight_digest": expected_weight_digest,
            "runner_provenance": dict(runner_provenance),
        },
    }
    _write_json(workspace / SHARD_MANIFEST_NAME, shard_manifest)
    instances = [
        {
            "instance_id": _instance_id(record.record_id),
            "record_id": record.record_id,
            "profile_id": PROFILE_ID,
            "vector_reference": {"shard_id": SHARD_ID, "row": row, "shard_digest": digest},
            "created_in": build_id,
            "runner_provenance": dict(runner_provenance),
            "eligibility_status": "eligible",
        }
        for row, record in enumerate(records)
    ]
    _write_jsonl(workspace / INSTANCES_NAME, instances)
    envelope = {
        "stage_id": "embed",
        "input_artifacts": [
            {"path": str(record.canonical_path), "media_type": "application/vnd.expedia.canonical-assembly+utf-8;version=1", "digest": record.sequence_digest}
            for record in records
        ],
        "output_artifacts": [
            {"path": str(vector_path), "media_type": "application/vnd.expedia.embedding-vector+float32;version=1", "digest": digest},
            {"path": str(workspace / SHARD_MANIFEST_NAME), "media_type": "application/json", "digest": sha256_file(workspace / SHARD_MANIFEST_NAME)},
            {"path": str(workspace / INSTANCES_NAME), "media_type": "application/x-ndjson", "digest": sha256_file(workspace / INSTANCES_NAME)},
        ],
        "outcome": "succeeded",
        "verification": {
            "eligible_record_count": len(records),
            "embedding_instance_count": len(instances),
            "dimension": VECTOR_DIMENSION,
            "dtype": "float32",
            "normalization": "l2",
            "shard_digest": digest,
            "finite_vectors": True,
            "duplicate_records": False,
        },
        "recovery": {"retry_requires": "a new empty embedding workspace after finalization"},
    }
    _write_json(workspace / STAGE_ENVELOPE_NAME, envelope)
    (workspace / CHECKPOINT_NAME).unlink()
    return envelope


def _failed_envelope(record_versions_path: Path, workspace: Path, reason: str) -> dict[str, object]:
    return {
        "stage_id": "embed",
        "input_artifacts": [{"path": str(record_versions_path), "media_type": "application/x-ndjson"}],
        "output_artifacts": [],
        "outcome": "failed",
        "verification": {"status": "failed", "reason": reason},
        "recovery": {"resume_state": str(workspace / CHECKPOINT_NAME)},
    }


def _instance_id(record_id: str) -> str:
    return f"embedding:{record_id}:{PROFILE_ID}"


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
