"""Deterministic M2.1 QueryRequest normalization and request-digest support.

This module deliberately does not read releases, search vectors, encode cursors,
or execute queries. Those concerns remain M2.2+ work behind the ADR-010 reader
boundary. It implements the OQ-11 rule that equivalent JSON requests have one
canonical interpretation before their request digest is calculated.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


MAX_REQUEST_BYTES = 16 * 1024
MAX_FILTER_NODES = 32
MAX_FILTER_DEPTH = 8
MAX_MEMBERSHIP_VALUES = 100
DEFAULT_PAGINATION = {
    "limit": 12,
    "cursor": None,
    "ordering_version": "score-desc-record-id-asc-v1",
}


class QueryContractError(ValueError):
    """A deterministic request-normalization or M2 query-cost failure."""


@dataclass(frozen=True)
class CanonicalQueryRequest:
    """Canonical JSON and its SHA-256 digest for one QueryRequest."""

    payload: dict[str, Any]
    canonical_json: str
    digest: str


def _reject_constant(value: str) -> None:
    raise QueryContractError(f"non-finite JSON numeric constant is not permitted: {value}")


def _object_without_duplicate_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise QueryContractError(f"duplicate JSON object member is not permitted: {name}")
        result[name] = value
    return result


def _parse_json(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_members,
            parse_int=Decimal,
            parse_float=Decimal,
            parse_constant=_reject_constant,
        )
    except (TypeError, json.JSONDecodeError) as error:
        raise QueryContractError(f"invalid JSON QueryRequest: {error}") from error
    if not isinstance(parsed, dict):
        raise QueryContractError("QueryRequest must be a JSON object")
    return parsed


def _number_json(value: Decimal) -> str:
    if not value.is_finite():
        raise QueryContractError("non-finite decimal is not permitted")
    if value == 0:
        return "0"
    normalized = value.normalize()
    rendered = format(normalized, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _canonical_json(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, Decimal):
        return _number_json(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        raise QueryContractError("native floating-point values are not accepted for canonicalization")
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(_canonical_json(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(
            _canonical_json(key) + ":" + _canonical_json(value[key])
            for key in sorted(value)
        ) + "}"
    raise QueryContractError(f"unsupported JSON value type: {type(value).__name__}")


def _semantic_sort_and_deduplicate(values: list[Any]) -> list[Any]:
    by_key: dict[str, Any] = {}
    for value in values:
        normalized = _normalize_value(value)
        key = _canonical_json(normalized)
        by_key[key] = normalized
    return [by_key[key] for key in sorted(by_key)]


def _normalize_filter(expression: Any) -> Any:
    if not isinstance(expression, dict) or len(expression) != 1:
        return _normalize_value(expression)
    operator, value = next(iter(expression.items()))
    if operator in {"all", "any"}:
        if not isinstance(value, list):
            return {operator: _normalize_value(value)}
        return {operator: _semantic_sort_and_deduplicate([_normalize_filter(item) for item in value])}
    if operator == "not":
        return {operator: _normalize_filter(value)}
    if operator == "in" and isinstance(value, dict):
        normalized = _normalize_value(value)
        values = value.get("values")
        if isinstance(values, list):
            normalized["values"] = _semantic_sort_and_deduplicate(values)
        return {operator: normalized}
    return {operator: _normalize_value(value)}


def _normalize_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_value(value[key]) for key in sorted(value)}
    return value


def _filter_cost(expression: Any, depth: int = 1) -> tuple[int, int]:
    if not isinstance(expression, dict) or len(expression) != 1:
        return 1, depth
    operator, value = next(iter(expression.items()))
    if operator in {"all", "any"} and isinstance(value, list):
        child_costs = [_filter_cost(item, depth + 1) for item in value]
        return 1 + sum(cost for cost, _ in child_costs), max([depth, *(item_depth for _, item_depth in child_costs)])
    if operator == "not":
        cost, child_depth = _filter_cost(value, depth + 1)
        return 1 + cost, max(depth, child_depth)
    return 1, depth


def _validate_query_cost(payload: dict[str, Any], canonical_json: str) -> None:
    if len(canonical_json.encode("utf-8")) > MAX_REQUEST_BYTES:
        raise QueryContractError("query_cost_exceeded: canonical request exceeds 16 KiB")
    expression = payload.get("filter")
    if expression is None:
        return
    nodes, depth = _filter_cost(expression)
    if nodes > MAX_FILTER_NODES:
        raise QueryContractError("query_cost_exceeded: filter exceeds 32 predicate nodes")
    if depth > MAX_FILTER_DEPTH:
        raise QueryContractError("query_cost_exceeded: filter exceeds depth 8")

    def validate_membership(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                validate_membership(item)
        elif isinstance(value, dict):
            if "in" in value and isinstance(value["in"], dict):
                members = value["in"].get("values")
                if isinstance(members, list) and len(members) > MAX_MEMBERSHIP_VALUES:
                    raise QueryContractError("query_cost_exceeded: membership exceeds 100 values")
            for item in value.values():
                validate_membership(item)

    validate_membership(expression)


def canonicalize_query_request_json(text: str) -> CanonicalQueryRequest:
    """Parse, normalize, cost-check, and digest one JSON QueryRequest.

    Structural schema validation remains a separate conformance step. This keeps
    canonicalization usable by every future transport while preventing it from
    becoming a release adapter or query executor.
    """

    parsed = _parse_json(text)
    normalized = _normalize_value(parsed)
    normalized["filter"] = _normalize_filter(parsed["filter"]) if "filter" in parsed else None
    pagination = parsed.get("pagination")
    if pagination is None:
        normalized["pagination"] = dict(DEFAULT_PAGINATION)
    elif isinstance(pagination, dict):
        normalized_pagination = dict(DEFAULT_PAGINATION)
        normalized_pagination.update(_normalize_value(pagination))
        normalized["pagination"] = normalized_pagination
    canonical = _canonical_json(normalized)
    _validate_query_cost(normalized, canonical)
    digest = "sha256:" + sha256(canonical.encode("utf-8")).hexdigest()
    return CanonicalQueryRequest(payload=normalized, canonical_json=canonical, digest=digest)


def cursor_binding_digest(request: CanonicalQueryRequest) -> str:
    """Return the stable selection digest used by an opaque pagination cursor.

    A cursor chooses a continuation point; it is not part of the selected
    release/profile/filter/ranking semantics. Replacing only its opaque value
    with ``null`` gives every page of one logical request one binding digest,
    while any release, profile, filter, query-record, or ordering change still
    produces a different binding.
    """

    payload = _normalize_value(request.payload)
    pagination = payload.get("pagination")
    if not isinstance(pagination, dict):  # pragma: no cover - canonicalizer supplies defaults.
        raise QueryContractError("canonical QueryRequest has no pagination object")
    pagination["cursor"] = None
    canonical = _canonical_json(payload)
    return "sha256:" + sha256(canonical.encode("utf-8")).hexdigest()
