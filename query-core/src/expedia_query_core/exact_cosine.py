"""The deliberately small M2.3 exact-cosine reference executor.

This module accepts an already verified local release snapshot.  It neither
opens packages nor consults mutable paths, and it intentionally provides no
ANN, filtering, cursor, SDK, REST, or Explorer behavior.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from hashlib import sha256
import math
import struct
from typing import Any

from .query_contracts import CanonicalQueryRequest, QueryContractError, canonicalize_query_request_json
from .verified_release import VerifiedRelease


RECORD_TABLE_PATH = "records/genome-record-versions.jsonl"
EMBEDDING_INSTANCE_TABLE_PATH = "embeddings/embedding-instances.jsonl"
REQUEST_VERSION = "query-request/0.1.0"
RESULT_VERSION = "query-result/0.1.1"
ORDERING_VERSION = "score-desc-record-id-asc-v1"
FLOAT32_SIZE = 4
NORMALIZATION_TOLERANCE = 1e-5


def _float32(value: float) -> float:
    """Round a scalar to IEEE-754 binary32 deterministically."""

    return struct.unpack("<f", struct.pack("<f", value))[0]


def _error(
    *,
    code: str,
    message: str,
    stage: str,
    correlation_id: str,
    field: str | None = None,
) -> dict[str, object]:
    error: dict[str, object] = {
        "code": code,
        "message": message,
        "stage": stage,
        "correlation_id": correlation_id,
    }
    if field is not None:
        error["field"] = field
    return {"schema_version": RESULT_VERSION, "outcome": "error", "warnings": [], "error": error}


def _raw_correlation(text: str) -> str:
    return "query:" + sha256(text.encode("utf-8")).hexdigest()


def _canonical_correlation(request: CanonicalQueryRequest) -> str:
    return "query:" + request.digest.removeprefix("sha256:")


def _object(value: object, *, field: str, required: set[str], allowed: set[str]) -> Mapping[str, object] | None:
    if not isinstance(value, dict) or set(value) - allowed or not required.issubset(value):
        return None
    return value


def _string(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _integer(value: object) -> bool:
    return (isinstance(value, int) and not isinstance(value, bool)) or (
        isinstance(value, Decimal) and value == value.to_integral_value()
    )


def _validate_similarity_request(request: CanonicalQueryRequest) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    """Validate only the M2.3 subset without giving it new request semantics."""

    payload = request.payload
    correlation_id = _canonical_correlation(request)
    top_allowed = {
        "schema_version",
        "release_selector",
        "operation",
        "profile_selector",
        "similarity",
        "filter",
        "traversal",
        "pagination",
    }
    if set(payload) - top_allowed or payload.get("schema_version") != REQUEST_VERSION:
        return None, _error(code="validation_error", message="QueryRequest schema version or fields are invalid", stage="validate", correlation_id=correlation_id)
    release_selector = _object(
        payload.get("release_selector"),
        field="release_selector",
        required={"release_id", "release_digest"},
        allowed={"release_id", "release_digest"},
    )
    if release_selector is None or not _string(release_selector["release_id"]) or not _string(release_selector["release_digest"]):
        return None, _error(code="validation_error", message="release_selector is invalid", stage="validate", correlation_id=correlation_id, field="release_selector")
    if payload.get("operation") != "similarity":
        return None, _error(code="unsupported_operation", message="M2.3 implements only similarity requests", stage="plan", correlation_id=correlation_id, field="operation")
    profile = _object(
        payload.get("profile_selector"),
        field="profile_selector",
        required={"profile_id", "profile_version"},
        allowed={"profile_id", "profile_version"},
    )
    similarity = _object(
        payload.get("similarity"),
        field="similarity",
        required={"query_record_id", "metric", "mode"},
        allowed={"query_record_id", "metric", "mode"},
    )
    if (
        profile is None
        or similarity is None
        or not _string(profile["profile_id"])
        or not _string(profile["profile_version"])
        or not _string(similarity["query_record_id"])
        or similarity["metric"] != "cosine"
        or similarity["mode"] != "exact"
    ):
        return None, _error(code="validation_error", message="similarity profile or selector is invalid", stage="validate", correlation_id=correlation_id)
    if payload.get("filter") is not None:
        return None, _error(code="unsupported_filter", message="filter execution is deferred beyond M2.3", stage="plan", correlation_id=correlation_id, field="filter")
    if payload.get("traversal") is not None:
        return None, _error(code="unsupported_relation", message="traversal execution is deferred beyond M2.3", stage="plan", correlation_id=correlation_id, field="traversal")
    pagination = _object(
        payload.get("pagination"),
        field="pagination",
        required={"limit", "cursor", "ordering_version"},
        allowed={"limit", "cursor", "ordering_version"},
    )
    if (
        pagination is None
        or not _integer(pagination["limit"])
        or not 1 <= int(pagination["limit"]) <= 12
        or pagination["ordering_version"] != ORDERING_VERSION
    ):
        return None, _error(code="validation_error", message="pagination is invalid", stage="validate", correlation_id=correlation_id, field="pagination")
    if pagination["cursor"] is not None:
        return None, _error(code="invalid_cursor", message="cursor execution is deferred beyond M2.3", stage="validate", correlation_id=correlation_id, field="pagination.cursor")
    return payload, None


def _profile_and_rows(
    release: VerifiedRelease,
    request: Mapping[str, object],
) -> tuple[object, dict[str, tuple[str | None, int]]] | tuple[None, dict[str, object]]:
    profile_selector = request["profile_selector"]
    similarity = request["similarity"]
    assert isinstance(profile_selector, dict) and isinstance(similarity, dict)
    profile_id = profile_selector["profile_id"]
    profile_version = profile_selector["profile_version"]
    assert isinstance(profile_id, str) and isinstance(profile_version, str)
    try:
        profile = release.embedding_profile(profile_id)
        shard = release.vector_shard(profile_id)
    except KeyError:
        return None, _error(code="profile_incompatible", message="selected profile is not declared by the verified release", stage="resolve", correlation_id="query:profile-unresolved")
    if (
        profile.version != profile_version
        or profile.normalization != "l2"
        or profile.metric_name != "cosine"
        or profile.metric_direction != "higher-is-more-similar"
        or profile.dimension != shard.dimension
        or profile.dtype != "float32"
        or shard.dtype != "float32"
        or len(shard.payload) % (FLOAT32_SIZE * shard.dimension) != 0
    ):
        return None, _error(code="profile_incompatible", message="selected profile is incompatible with exact cosine", stage="plan", correlation_id="query:profile-incompatible")

    try:
        records = release.read_table(RECORD_TABLE_PATH)
        instances = release.read_table(EMBEDDING_INSTANCE_TABLE_PATH)
    except (KeyError, ValueError):
        return None, _error(code="release_untrusted", message="verified release lacks required exact-cosine tables", stage="resolve", correlation_id="query:release-incomplete")
    record_entities: dict[str, str | None] = {}
    for record in records:
        record_id = record.get("record_id")
        entity_id = record.get("entity_id")
        if not _string(record_id) or not (entity_id is None or _string(entity_id)):
            return None, _error(code="release_untrusted", message="verified record table is incompatible", stage="resolve", correlation_id="query:release-incompatible")
        record_entities[record_id] = entity_id
    instance_rows: dict[str, tuple[str, int]] = {}
    for instance in instances:
        reference = instance.get("vector_reference")
        if not isinstance(reference, Mapping):
            continue
        instance_id = instance.get("instance_id")
        record_id = instance.get("record_id")
        instance_profile = instance.get("profile_id")
        row = reference.get("row")
        shard_id = reference.get("shard_id")
        shard_digest = reference.get("shard_digest")
        if (
            _string(instance_id)
            and _string(record_id)
            and instance_profile == profile_id
            and _integer(row)
            and shard_id == shard.shard_id
            and shard_digest == shard.digest
        ):
            instance_rows[instance_id] = (record_id, int(row))
    rows: dict[str, tuple[str | None, int]] = {}
    for key, instance_id in shard.row_mapping.items():
        try:
            declared_row = int(key)
        except ValueError:
            return None, _error(code="release_untrusted", message="vector-shard row mapping is invalid", stage="resolve", correlation_id="query:release-incompatible")
        binding = instance_rows.get(instance_id)
        if binding is None or binding[1] != declared_row or binding[0] not in record_entities or binding[0] in rows:
            return None, _error(code="release_untrusted", message="vector-shard row mapping cannot be bound to records", stage="resolve", correlation_id="query:release-incompatible")
        rows[binding[0]] = (record_entities[binding[0]], declared_row)
    if not rows or len(rows) != len(record_entities):
        return None, _error(code="release_untrusted", message="vector-shard rows do not cover the verified records", stage="resolve", correlation_id="query:release-incompatible")
    query_record_id = similarity["query_record_id"]
    assert isinstance(query_record_id, str)
    if query_record_id not in rows:
        return None, _error(code="validation_error", message="query_record_id is not present in the selected profile", stage="validate", correlation_id="query:record-not-found", field="similarity.query_record_id")
    return (profile, rows), {}


def _vector(payload: bytes, *, row: int, dimension: int) -> tuple[float, ...] | None:
    start = row * dimension * FLOAT32_SIZE
    stop = start + dimension * FLOAT32_SIZE
    if row < 0 or stop > len(payload):
        return None
    values = struct.unpack_from(f"<{dimension}f", payload, start)
    norm_squared = 0.0
    for value in values:
        if not math.isfinite(value):
            return None
        norm_squared = _float32(norm_squared + _float32(value * value))
    if abs(norm_squared - 1.0) > NORMALIZATION_TOLERANCE:
        return None
    return values


def _float32_inner_product(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    score = 0.0
    for left_value, right_value in zip(left, right, strict=True):
        score = _float32(score + _float32(left_value * right_value))
    return score


class ExactCosineQueryCore:
    """M2.3's sole exact reference implementation for one verified release."""

    def __init__(self, release: VerifiedRelease) -> None:
        self._release = release

    def execute(self, request_json: str) -> Mapping[str, object]:
        """Return a deterministic QueryResult/0.1.1 for one raw QueryRequest."""

        try:
            canonical = canonicalize_query_request_json(request_json)
        except QueryContractError as error:
            code = "query_cost_exceeded" if str(error).startswith("query_cost_exceeded:") else "validation_error"
            return _error(code=code, message=str(error), stage="validate", correlation_id=_raw_correlation(request_json))
        request, rejection = _validate_similarity_request(canonical)
        if rejection is not None:
            return rejection
        assert request is not None
        correlation_id = _canonical_correlation(canonical)
        selector = request["release_selector"]
        assert isinstance(selector, dict)
        if selector["release_id"] != self._release.release_id or selector["release_digest"] != self._release.release_digest:
            return _error(code="release_not_found", message="release selector does not identify this verified release", stage="resolve", correlation_id=correlation_id, field="release_selector")
        resolved, failure = _profile_and_rows(self._release, request)
        if resolved is None:
            failure["error"]["correlation_id"] = correlation_id  # type: ignore[index]
            return failure
        profile, rows = resolved
        shard = self._release.vector_shard(profile.profile_id)
        query_record_id = request["similarity"]["query_record_id"]  # type: ignore[index]
        assert isinstance(query_record_id, str)
        query_vector = _vector(shard.payload, row=rows[query_record_id][1], dimension=profile.dimension)
        if query_vector is None:
            return _error(code="profile_incompatible", message="selected profile has non-finite or non-normalized vectors", stage="plan", correlation_id=correlation_id)
        ranked: list[tuple[str, str | None, float]] = []
        for record_id, (entity_id, row) in rows.items():
            candidate = _vector(shard.payload, row=row, dimension=profile.dimension)
            if candidate is None:
                return _error(code="profile_incompatible", message="selected profile has non-finite or non-normalized vectors", stage="plan", correlation_id=correlation_id)
            ranked.append((record_id, entity_id, _float32_inner_product(query_vector, candidate)))
        ranked.sort(key=lambda row: (-row[2], row[0]))
        limit = int(request["pagination"]["limit"])  # type: ignore[index]
        result_rows = [
            {"record_id": record_id, "score": score, "entity_id": entity_id}
            for record_id, entity_id, score in ranked[:limit]
        ]
        return {
            "schema_version": RESULT_VERSION,
            "outcome": "success",
            "context": {
                "release_id": self._release.release_id,
                "release_digest": self._release.release_digest,
                "canonical_request_digest": canonical.digest,
                "ordering_version": ORDERING_VERSION,
                "profile_id": profile.profile_id,
                "metric": profile.metric_name,
                "metric_direction": profile.metric_direction,
                "mode": "exact",
            },
            "rows": result_rows,
            "next_cursor": None,
            "provenance": {
                "release_digest": self._release.release_digest,
                "vector_shard_digest": shard.digest,
                "profile_version": profile.version,
                "profile_digest": profile.digest,
            },
            "evidence_status": {"release_integrity": "verified", "method": "not-evaluated"},
            "warnings": [],
            "error": None,
        }
