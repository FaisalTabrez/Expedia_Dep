"""Independent M3-002 float32 cosine reference oracle.

This module is validation-only study infrastructure.  It is intentionally
isolated from Query Core: it verifies an M1 Draft package through the M1
Release Reader, decodes its manifest-addressed vector shard itself, performs
its own IEEE-754 binary32 arithmetic, and constructs only the M3-002
comparison projection.  It does not parse QueryRequest or construct
QueryResult envelopes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import struct
from types import MappingProxyType

from expedia_validation.release_reader import ReleaseReaderError, read_release


FLOAT32_SIZE = 4
NORMALIZATION_TOLERANCE = 1e-5
ORDERING_VERSION = "score-desc-record-id-asc-v1"
RECORD_TABLE_PATH = Path("records/genome-record-versions.jsonl")
INSTANCE_TABLE_PATH = Path("embeddings/embedding-instances.jsonl")
VECTOR_SHARD_PATH = Path("embeddings/vectors.float32le")
VECTOR_MANIFEST_PATH = Path("embeddings/vector-shard-manifest.json")
PROFILE_PATH = Path("profiles/m1-generanno-prokaryote-0.5b-assembly-v1.json")


class ReferenceInputError(RuntimeError):
    """The independently read release cannot satisfy the M3-002 binding."""


@dataclass(frozen=True, slots=True)
class ReferenceBinding:
    """The immutable package identities selected by the approved study."""

    release_id: str
    release_digest: str
    profile_id: str
    profile_version: str
    profile_digest: str
    vector_shard_digest: str
    expected_record_count: int


@dataclass(frozen=True, slots=True)
class IndependentReferenceRelease:
    """A reference-owned, verified view of the fixed M3-002 package inputs."""

    binding: ReferenceBinding
    record_ids: tuple[str, ...]
    vectors_by_record_id: Mapping[str, tuple[float, ...]]

    def comparison_object(
        self,
        *,
        query_record_id: str,
        canonical_request_digest: str,
    ) -> dict[str, object]:
        """Compute the study's reference projection for one already-canonical request.

        The caller owns QueryRequest canonicalization.  This boundary prevents
        the oracle from reusing Query Core request, cursor, result, or ordering
        components while still binding its output to the same request identity.
        """

        if query_record_id not in self.vectors_by_record_id:
            raise ReferenceInputError("query_record_id is absent from the verified reference rows")
        if not _is_sha256_digest(canonical_request_digest):
            raise ReferenceInputError("canonical_request_digest must be a sha256 digest")

        query = self.vectors_by_record_id[query_record_id]
        ranked = [
            (record_id, _float32_inner_product(query, self.vectors_by_record_id[record_id]))
            for record_id in self.record_ids
        ]
        ranked.sort(key=lambda item: (-item[1], item[0]))
        return {
            "canonical_request_digest": canonical_request_digest,
            "ordered_record_ids": [record_id for record_id, _ in ranked],
            "decoded_float32_scores": [score for _, score in ranked],
            "provenance": {
                "release_digest": self.binding.release_digest,
                "profile_id": self.binding.profile_id,
                "profile_version": self.binding.profile_version,
                "profile_digest": self.binding.profile_digest,
                "vector_shard_digest": self.binding.vector_shard_digest,
                "ordering_version": ORDERING_VERSION,
            },
        }


def load_reference_release(
    package: str | Path,
    *,
    binding: ReferenceBinding,
) -> IndependentReferenceRelease:
    """Read M3-002 inputs without creating or accepting a Query Core snapshot."""

    package_path = Path(package)
    try:
        release_verification = read_release(package_path)
    except ReleaseReaderError as error:
        raise ReferenceInputError("M1 Release Reader verification failed") from error
    _check_release_identity(release_verification, binding)

    profile_payload = _read_bytes(package_path / PROFILE_PATH, "EmbeddingProfile")
    _check_digest(profile_payload, binding.profile_digest, "EmbeddingProfile")
    profile = _json_object(profile_payload, "EmbeddingProfile")
    _check_profile(profile, binding)
    records = _read_jsonl(package_path / RECORD_TABLE_PATH, "record table")
    instances = _read_jsonl(package_path / INSTANCE_TABLE_PATH, "embedding instance table")
    shard_manifest = _read_json_object(package_path / VECTOR_MANIFEST_PATH, "vector shard manifest")
    payload = _read_bytes(package_path / VECTOR_SHARD_PATH, "vector shard")
    _check_digest(payload, binding.vector_shard_digest, "vector shard")

    record_ids = _record_ids(records, binding.expected_record_count)
    dimension = _check_shard_manifest(shard_manifest, binding, len(record_ids))
    row_by_record_id = _row_bindings(instances, shard_manifest, record_ids, binding)
    vectors_by_record_id = _decode_and_validate_vectors(
        payload,
        record_ids=record_ids,
        row_by_record_id=row_by_record_id,
        dimension=dimension,
    )
    return IndependentReferenceRelease(
        binding=binding,
        record_ids=record_ids,
        vectors_by_record_id=MappingProxyType(vectors_by_record_id),
    )


def _check_release_identity(result: Mapping[str, object], binding: ReferenceBinding) -> None:
    if (
        result.get("release_id") != binding.release_id
        or result.get("release_manifest_digest") != binding.release_digest
        or result.get("vector_shard_digest") != binding.vector_shard_digest
        or result.get("record_count") != binding.expected_record_count
    ):
        raise ReferenceInputError("M1 Release Reader output does not match the M3-002 binding")


def _check_profile(profile: Mapping[str, object], binding: ReferenceBinding) -> None:
    output = profile.get("output")
    metric = profile.get("metric")
    if not isinstance(output, dict) or not isinstance(metric, dict):
        raise ReferenceInputError("EmbeddingProfile output or metric is invalid")
    if (
        profile.get("profile_id") != binding.profile_id
        or profile.get("version") != binding.profile_version
        or output.get("dtype") != "float32"
        or output.get("normalization") != "l2"
        or not isinstance(output.get("dimension"), int)
        or output["dimension"] <= 0
        or metric.get("name") != "cosine"
        or metric.get("direction") != "higher-is-more-similar"
    ):
        raise ReferenceInputError("EmbeddingProfile does not satisfy the M3-002 reference contract")


def _record_ids(records: tuple[Mapping[str, object], ...], expected_count: int) -> tuple[str, ...]:
    if len(records) != expected_count:
        raise ReferenceInputError("record table count differs from the M3-002 binding")
    record_ids = tuple(record.get("record_id") for record in records)
    if not all(isinstance(record_id, str) and record_id for record_id in record_ids):
        raise ReferenceInputError("record table contains an invalid record_id")
    if len(set(record_ids)) != len(record_ids):
        raise ReferenceInputError("record table contains duplicate record_ids")
    return record_ids  # type: ignore[return-value]


def _check_shard_manifest(
    shard_manifest: Mapping[str, object],
    binding: ReferenceBinding,
    record_count: int,
) -> int:
    dimension = shard_manifest.get("dimension")
    row_mapping = shard_manifest.get("row_mapping")
    if (
        shard_manifest.get("profile_id") != binding.profile_id
        or shard_manifest.get("digest") != binding.vector_shard_digest
        or shard_manifest.get("dtype") != "float32"
        or isinstance(dimension, bool)
        or not isinstance(dimension, int)
        or dimension <= 0
        or not isinstance(row_mapping, dict)
        or set(row_mapping) != {str(index) for index in range(record_count)}
        or not all(isinstance(value, str) and value for value in row_mapping.values())
        or len(set(row_mapping.values())) != record_count
    ):
        raise ReferenceInputError("vector shard manifest does not satisfy the M3-002 reference contract")
    return dimension


def _row_bindings(
    instances: tuple[Mapping[str, object], ...],
    shard_manifest: Mapping[str, object],
    record_ids: tuple[str, ...],
    binding: ReferenceBinding,
) -> Mapping[str, int]:
    if len(instances) != len(record_ids):
        raise ReferenceInputError("embedding instance count differs from the record table")
    instance_bindings: dict[str, tuple[str, int]] = {}
    for instance in instances:
        instance_id = instance.get("instance_id")
        record_id = instance.get("record_id")
        reference = instance.get("vector_reference")
        if not isinstance(reference, dict):
            raise ReferenceInputError("EmbeddingInstance lacks a vector reference")
        row = reference.get("row")
        if (
            not isinstance(instance_id, str)
            or not isinstance(record_id, str)
            or instance.get("profile_id") != binding.profile_id
            or isinstance(row, bool)
            or not isinstance(row, int)
            or row < 0
            or reference.get("shard_digest") != binding.vector_shard_digest
            or instance_id in instance_bindings
        ):
            raise ReferenceInputError("EmbeddingInstance does not bind the M3-002 vector shard")
        instance_bindings[instance_id] = (record_id, row)

    row_mapping = shard_manifest["row_mapping"]
    assert isinstance(row_mapping, dict)  # Checked by _check_shard_manifest.
    row_by_record_id: dict[str, int] = {}
    for raw_row, instance_id in row_mapping.items():
        assert isinstance(raw_row, str) and isinstance(instance_id, str)
        record_id, row = instance_bindings.get(instance_id, ("", -1))
        if row != int(raw_row) or record_id not in record_ids or record_id in row_by_record_id:
            raise ReferenceInputError("vector shard row mapping cannot be bound to unique records")
        row_by_record_id[record_id] = row
    if set(row_by_record_id) != set(record_ids):
        raise ReferenceInputError("vector shard rows do not cover every verified record")
    return MappingProxyType(row_by_record_id)


def _decode_and_validate_vectors(
    payload: bytes,
    *,
    record_ids: tuple[str, ...],
    row_by_record_id: Mapping[str, int],
    dimension: int,
) -> dict[str, tuple[float, ...]]:
    expected_size = len(record_ids) * dimension * FLOAT32_SIZE
    if len(payload) != expected_size:
        raise ReferenceInputError("vector shard byte length is incompatible with the declared rows and dimension")
    vectors: dict[str, tuple[float, ...]] = {}
    for record_id in record_ids:
        row = row_by_record_id[record_id]
        start = row * dimension * FLOAT32_SIZE
        values = struct.unpack_from(f"<{dimension}f", payload, start)
        if not all(math.isfinite(value) for value in values):
            raise ReferenceInputError("vector shard contains a non-finite value")
        norm_squared = 0.0
        for value in values:
            norm_squared = _round_float32(norm_squared + _round_float32(value * value))
        if abs(norm_squared - 1.0) > NORMALIZATION_TOLERANCE:
            raise ReferenceInputError("vector shard contains a vector that is not L2-normalized")
        vectors[record_id] = values
    return vectors


def _float32_inner_product(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right):
        raise ReferenceInputError("reference vectors have incompatible dimensions")
    score = 0.0
    for left_value, right_value in zip(left, right, strict=True):
        score = _round_float32(score + _round_float32(left_value * right_value))
    return score


def _round_float32(value: float) -> float:
    """Locally implement deterministic IEEE-754 binary32 rounding."""

    return struct.unpack("<f", struct.pack("<f", value))[0]


def _read_json_object(path: Path, label: str) -> Mapping[str, object]:
    return _json_object(_read_bytes(path, label), label)


def _json_object(payload: bytes, label: str) -> Mapping[str, object]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReferenceInputError(f"cannot decode {label}") from error
    if not isinstance(value, dict):
        raise ReferenceInputError(f"{label} must be an object")
    return MappingProxyType(value)


def _read_jsonl(path: Path, label: str) -> tuple[Mapping[str, object], ...]:
    payload = _read_bytes(path, label)
    try:
        values = [json.loads(line) for line in payload.decode("utf-8").splitlines() if line]
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReferenceInputError(f"cannot decode {label}") from error
    if not all(isinstance(value, dict) for value in values):
        raise ReferenceInputError(f"{label} contains a non-object row")
    return tuple(MappingProxyType(value) for value in values)


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise ReferenceInputError(f"cannot read {label}") from error


def _check_digest(payload: bytes, expected: str, label: str) -> None:
    observed = "sha256:" + sha256(payload).hexdigest()
    if observed != expected:
        raise ReferenceInputError(f"{label} digest differs from the M3-002 binding")


def _is_sha256_digest(value: str) -> bool:
    return value.startswith("sha256:") and len(value) == 71 and all(
        character in "0123456789abcdef" for character in value.removeprefix("sha256:")
    )
