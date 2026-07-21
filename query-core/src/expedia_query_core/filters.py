"""Deterministic M2.4 evaluation of the accepted FilterExpression subset."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


CANONICAL_FIELD_NAMES = frozenset(
    {"record_id", "entity_id", "canonicalization_id", "source_provenance_id", "lifecycle_state"}
)


@dataclass(frozen=True, slots=True)
class FilterFailure(Exception):
    """A typed Core planning failure; filter contents are never ignored."""

    code: str
    message: str


def _object(value: object, *, required: set[str], allowed: set[str]) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping) or set(value) - allowed or not required.issubset(value):
        return None
    return value


def _scalar(value: object) -> bool:
    return isinstance(value, (str, bool, Decimal)) and not isinstance(value, type(None))


def _canonical_field(value: object) -> str:
    field = _object(value, required={"kind", "name"}, allowed={"kind", "name"})
    if field is None or field.get("kind") != "canonical" or field.get("name") not in CANONICAL_FIELD_NAMES:
        if isinstance(value, Mapping) and value.get("kind") == "annotation":
            annotation = _object(value, required={"kind", "source", "predicate"}, allowed={"kind", "source", "predicate"})
            if annotation is not None and isinstance(annotation["source"], str) and annotation["source"] and isinstance(annotation["predicate"], str) and annotation["predicate"]:
                raise FilterFailure("unsupported_filter", "annotation assertions are not declared by this verified release")
        raise FilterFailure("validation_error", "FilterExpression FieldRef is invalid")
    name = field["name"]
    assert isinstance(name, str)
    return name


def _comparison(value: object, *, field: str, record: Mapping[str, object]) -> bool:
    condition = _object(value, required={"field", "value"}, allowed={"field", "value"})
    if condition is None or not _scalar(condition["value"]):
        raise FilterFailure("validation_error", "equality filter is invalid")
    name = _canonical_field(condition["field"])
    return record.get(name) == condition["value"]


def _membership(value: object, *, record: Mapping[str, object]) -> bool:
    condition = _object(value, required={"field", "values"}, allowed={"field", "values"})
    values = None if condition is None else condition.get("values")
    if not isinstance(values, list) or not values or not all(_scalar(item) for item in values):
        raise FilterFailure("validation_error", "membership filter is invalid")
    name = _canonical_field(condition["field"])
    return record.get(name) in values


def _state(value: object, *, record: Mapping[str, object]) -> bool:
    condition = _object(value, required={"field", "is"}, allowed={"field", "is"})
    if condition is None or condition.get("is") not in {"present", "missing", "unavailable", "false"}:
        raise FilterFailure("validation_error", "state filter is invalid")
    name = _canonical_field(condition["field"])
    requested = condition["is"]
    exists = name in record
    field_value = record.get(name)
    if requested == "missing":
        return not exists
    if requested == "unavailable":
        # Canonical M1 record fields have declared, directly comparable meaning.
        return False
    if requested == "false":
        return exists and field_value is False
    return exists and field_value is not None and field_value is not False


def _range(value: object) -> bool:
    condition = _object(value, required={"field", "unit"}, allowed={"field", "gte", "gt", "lte", "lt", "unit"})
    if condition is None or not isinstance(condition.get("unit"), str) or not condition["unit"]:
        raise FilterFailure("validation_error", "range filter is invalid")
    _canonical_field(condition["field"])
    lower = [key for key in ("gte", "gt") if key in condition]
    upper = [key for key in ("lte", "lt") if key in condition]
    if len(lower) != 1 or len(upper) != 1 or not all(isinstance(condition[key], Decimal) for key in [*lower, *upper]):
        raise FilterFailure("validation_error", "range filter requires one lower and one upper numeric bound")
    raise FilterFailure("unsupported_filter", "no numeric canonical field with declared units is available in this verified release")


def _relation(value: object) -> bool:
    relation = _object(value, required={"relation_type", "direction"}, allowed={"relation_type", "direction", "artifact_id"})
    if (
        relation is None
        or not isinstance(relation["relation_type"], str)
        or not relation["relation_type"]
        or relation["direction"] not in {"outbound", "inbound"}
        or ("artifact_id" in relation and (not isinstance(relation["artifact_id"], str) or not relation["artifact_id"]))
    ):
        raise FilterFailure("validation_error", "relation filter is invalid")
    raise FilterFailure("unsupported_relation", "relation filters require a declared DerivedRelation artifact")


def evaluate_filter(expression: object, record: Mapping[str, object]) -> bool:
    """Evaluate one normalized FilterExpression against one canonical record."""

    operator = _object(expression, required=set(), allowed={"all", "any", "not", "eq", "in", "range", "state", "relation"})
    if operator is None or len(operator) != 1:
        raise FilterFailure("validation_error", "FilterExpression must contain exactly one operator")
    name, value = next(iter(operator.items()))
    if name in {"all", "any"}:
        if not isinstance(value, list) or not value:
            raise FilterFailure("validation_error", f"{name} filter requires one or more operands")
        outcomes = [evaluate_filter(child, record) for child in value]
        return all(outcomes) if name == "all" else any(outcomes)
    if name == "not":
        return not evaluate_filter(value, record)
    if name == "eq":
        return _comparison(value, field="eq", record=record)
    if name == "in":
        return _membership(value, record=record)
    if name == "state":
        return _state(value, record=record)
    if name == "range":
        return _range(value)
    if name == "relation":
        return _relation(value)
    raise FilterFailure("validation_error", "FilterExpression operator is invalid")


def selected_record_ids(expression: object | None, records: Mapping[str, Mapping[str, object]]) -> frozenset[str]:
    """Return record IDs selected by a filter, or every ID for no filter."""

    if expression is None:
        return frozenset(records)
    return frozenset(record_id for record_id, record in records.items() if evaluate_filter(expression, record))
