"""M2.6 provenance-first presentation over already-computed QueryResult data."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


class ExplorerPresentationError(ValueError):
    """A supplied result cannot be presented without inventing missing context."""


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ExplorerPresentationError(f"QueryResult {label} is not an object")
    return value


def _string(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ExplorerPresentationError(f"QueryResult {label} is not a non-empty string")
    return value


class ProvenanceExplorer:
    """Present Core-owned result semantics without recreating them locally.

    ``result_source`` is typically ``LocalExpediaClient.query``. It is injected
    so Explorer has no release path, query planner, vector access, filter,
    cursor, ranking, or transport implementation of its own.
    """

    def __init__(self, result_source: Callable[[Mapping[str, object]], Mapping[str, object]] | None = None) -> None:
        self._result_source = result_source

    def query_and_present(self, request: Mapping[str, object]) -> Mapping[str, object]:
        """Delegate a request unchanged, then present the returned QueryResult."""

        if self._result_source is None:
            raise ExplorerPresentationError("Explorer has no injected QueryResult source")
        return self.present_result(self._result_source(request))

    def present_release(self, release_context: Mapping[str, object]) -> Mapping[str, object]:
        """Display supplied release context without opening or verifying a release."""

        release_id = _string(release_context.get("release_id"), label="release_id")
        release_digest = _string(release_context.get("release_digest"), label="release_digest")
        return {
            "presentation_kind": "release-context",
            "release": {
                "release_id": release_id,
                "release_digest": release_digest,
                "scope": release_context.get("scope", "not-provided"),
                "citation": release_context.get("citation", "not-provided"),
                "compatibility": release_context.get("compatibility", "not-provided"),
                "integrity": release_context.get("integrity", "not-provided"),
            },
        }

    def present_result(self, result: Mapping[str, object]) -> Mapping[str, object]:
        """Build a display-safe view while retaining Core result data verbatim."""

        outcome = result.get("outcome")
        warnings = result.get("warnings")
        if not isinstance(warnings, list):
            raise ExplorerPresentationError("QueryResult warnings is not an array")
        if outcome == "error":
            error = _mapping(result.get("error"), label="error")
            return {
                "presentation_kind": "typed-query-error",
                "schema_version": result.get("schema_version"),
                "error": dict(error),
                "warnings": [dict(_mapping(item, label="warning")) for item in warnings],
                "evidence_note": "Query Core returned a typed error; Explorer did not alter it.",
            }
        if outcome != "success":
            raise ExplorerPresentationError("QueryResult outcome is not recognized")
        context = _mapping(result.get("context"), label="context")
        provenance = _mapping(result.get("provenance"), label="provenance")
        evidence = _mapping(result.get("evidence_status"), label="evidence_status")
        rows = result.get("rows")
        if not isinstance(rows, list):
            raise ExplorerPresentationError("QueryResult rows is not an array")
        rendered_rows: list[dict[str, object]] = []
        for row in rows:
            record = _mapping(row, label="row")
            rendered_rows.append(
                {
                    "kind": "canonical-record",
                    "record_id": _string(record.get("record_id"), label="row.record_id"),
                    "entity_id": record.get("entity_id"),
                    "score": record.get("score"),
                }
            )
        return {
            "presentation_kind": "query-result",
            "schema_version": result.get("schema_version"),
            "release": {
                "release_id": _string(context.get("release_id"), label="context.release_id"),
                "release_digest": _string(context.get("release_digest"), label="context.release_digest"),
                "integrity": evidence.get("release_integrity"),
                "scope": "not-provided-by-query-result",
                "citation": "not-provided-by-query-result",
                "compatibility": "not-provided-by-query-result",
            },
            "query_context": {
                "profile_id": context.get("profile_id"),
                "metric": context.get("metric"),
                "metric_direction": context.get("metric_direction"),
                "mode": context.get("mode"),
                "ordering_version": context.get("ordering_version"),
                "canonical_request_digest": context.get("canonical_request_digest"),
            },
            "provenance": dict(provenance),
            "evidence_status": dict(evidence),
            "warnings": [dict(_mapping(item, label="warning")) for item in warnings],
            "rows": rendered_rows,
            "next_cursor": result.get("next_cursor"),
            "annotation_assertions": "not-returned-by-query-result",
            "relation_lineage": "not-returned-by-query-result",
            "projection": "not-present; derived exploration artifacts are not inferred",
        }
