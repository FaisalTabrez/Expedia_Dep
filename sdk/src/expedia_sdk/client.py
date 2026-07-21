"""Thin in-process Python SDK adapter required by EDS §11 and ADR-016."""

from __future__ import annotations

from collections.abc import Mapping
import json


class LocalExpediaClient:
    """Serialize a typed request and delegate it unchanged in meaning to Core.

    This adapter deliberately has no release path, vector reader, filter,
    ranking, cursor, or result-construction implementation. Query Core remains
    the only semantic authority.
    """

    def __init__(self, query_core: object) -> None:
        execute = getattr(query_core, "execute", None)
        if not callable(execute):
            raise TypeError("query_core must provide execute(request_json)")
        self._query_core = query_core

    def query(self, request: Mapping[str, object]) -> Mapping[str, object]:
        """Execute one typed QueryRequest through the injected Core instance."""

        request_json = json.dumps(request, ensure_ascii=False, separators=(",", ":"))
        result = self._query_core.execute(request_json)
        if not isinstance(result, Mapping):  # pragma: no cover - protects the adapter boundary.
            raise TypeError("Query Core returned a non-object QueryResult")
        return result
