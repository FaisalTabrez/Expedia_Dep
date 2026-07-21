"""Dependency-free local WSGI transport for the M2 Query Core contract."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import json
from typing import Any


JsonStartResponse = Callable[[str, list[tuple[str, str]]], Any]


class V1QueryApplication:
    """Expose only ``POST /v1/query`` while preserving Core result envelopes."""

    def __init__(self, query_core: object) -> None:
        execute = getattr(query_core, "execute", None)
        if not callable(execute):
            raise TypeError("query_core must provide execute(request_json)")
        self._query_core = query_core

    @staticmethod
    def _response(start_response: JsonStartResponse, status: str, payload: object) -> list[bytes]:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        start_response(status, [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))])
        return [body]

    def __call__(self, environ: dict[str, Any], start_response: JsonStartResponse) -> Iterable[bytes]:
        """Route one WSGI request without interpreting QueryRequest semantics."""

        if environ.get("REQUEST_METHOD") != "POST":
            return self._response(start_response, "405 Method Not Allowed", {"error": "method_not_allowed"})
        if environ.get("PATH_INFO") != "/v1/query":
            return self._response(start_response, "404 Not Found", {"error": "not_found"})
        try:
            length = int(environ.get("CONTENT_LENGTH", "0"))
            if length < 0:
                raise ValueError
        except ValueError:
            return self._response(start_response, "400 Bad Request", {"error": "invalid_content_length"})
        body = environ["wsgi.input"].read(length)
        try:
            request_json = body.decode("utf-8")
        except UnicodeDecodeError:
            return self._response(start_response, "400 Bad Request", {"error": "invalid_utf8"})
        # Core returns both successful and typed query-error envelopes. HTTP
        # transport does not substitute a second semantic error vocabulary.
        return self._response(start_response, "200 OK", self._query_core.execute(request_json))
