"""Canonical JSON helpers shared by contract bindings."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import TypeAlias

from .errors import ContractValidationError

JsonScalar: TypeAlias = str | int | float | bool | None
FrozenJson: TypeAlias = JsonScalar | Mapping[str, "FrozenJson"] | tuple["FrozenJson", ...]


def freeze_json(value: object, *, field: str) -> FrozenJson:
    """Return an immutable, JSON-compatible value or raise a stable validation error."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        frozen: dict[str, FrozenJson] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ContractValidationError(f"{field} contains a non-string object key")
            frozen[key] = freeze_json(item, field=f"{field}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(freeze_json(item, field=field) for item in value)
    raise ContractValidationError(f"{field} is not JSON-serializable")


def thaw_json(value: FrozenJson) -> object:
    """Convert immutable JSON values back to standard JSON container types."""

    if isinstance(value, Mapping):
        return {key: thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_json(item) for item in value]
    return value


def require_mapping(value: object, *, field: str, non_empty: bool = False) -> Mapping[str, FrozenJson]:
    frozen = freeze_json(value, field=field)
    if not isinstance(frozen, Mapping):
        raise ContractValidationError(f"{field} must be an object")
    if non_empty and not frozen:
        raise ContractValidationError(f"{field} must not be empty")
    return frozen


def require_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{field} must be a non-empty string")
    return value


def canonical_json(payload: Mapping[str, object]) -> str:
    """Encode a payload deterministically for reproducible serialization tests."""

    try:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    except (TypeError, ValueError) as error:
        raise ContractValidationError("payload is not JSON-serializable") from error


def parse_json(payload: str) -> Mapping[str, object]:
    """Parse a JSON object, rejecting arrays/scalars as top-level contracts."""

    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ContractValidationError("payload is not valid JSON") from error
    if not isinstance(decoded, dict):
        raise ContractValidationError("contract payload must be a JSON object")
    return decoded


def reject_unknown_fields(payload: Mapping[str, object], *, allowed: set[str], contract: str) -> None:
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ContractValidationError(f"{contract} contains undeclared fields: {', '.join(unknown)}")


def require_fields(payload: Mapping[str, object], *, required: set[str], contract: str) -> None:
    missing = sorted(required - set(payload))
    if missing:
        raise ContractValidationError(f"{contract} is missing required fields: {', '.join(missing)}")
