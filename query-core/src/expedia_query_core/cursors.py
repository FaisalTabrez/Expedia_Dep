"""Opaque, deterministic M2.4 cursor construction and validation."""

from __future__ import annotations

import base64
import json
import math
from typing import Any


CURSOR_PREFIX = "m2c1."
CURSOR_VERSION = "cursor/0.1.0"
ORDERING_VERSION = "score-desc-record-id-asc-v1"


class CursorFailure(ValueError):
    """An opaque cursor cannot be used for the current Core query."""


def encode_cursor(*, release_digest: str, canonical_request_digest: str, score: float, record_id: str) -> str:
    payload = {
        "schema_version": CURSOR_VERSION,
        "release_digest": release_digest,
        "canonical_request_digest": canonical_request_digest,
        "ordering_version": ORDERING_VERSION,
        "last_key": {"score": score, "record_id": record_id},
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).decode("ascii").rstrip("=")
    return CURSOR_PREFIX + encoded


def decode_cursor(value: object) -> dict[str, Any]:
    if not isinstance(value, str) or not value.startswith(CURSOR_PREFIX):
        raise CursorFailure("cursor format is invalid")
    encoded = value.removeprefix(CURSOR_PREFIX)
    if not encoded or any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for character in encoded):
        raise CursorFailure("cursor encoding is invalid")
    try:
        raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
        raise CursorFailure("cursor cannot be decoded") from error
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "release_digest", "canonical_request_digest", "ordering_version", "last_key"}:
        raise CursorFailure("cursor payload is invalid")
    last_key = payload["last_key"]
    if (
        payload["schema_version"] != CURSOR_VERSION
        or payload["ordering_version"] != ORDERING_VERSION
        or not isinstance(payload["release_digest"], str)
        or not isinstance(payload["canonical_request_digest"], str)
        or not isinstance(last_key, dict)
        or set(last_key) != {"score", "record_id"}
        or isinstance(last_key["score"], bool)
        or not isinstance(last_key["score"], (int, float))
        or not math.isfinite(last_key["score"])
        or not isinstance(last_key["record_id"], str)
        or not last_key["record_id"]
    ):
        raise CursorFailure("cursor payload is incompatible")
    return payload
