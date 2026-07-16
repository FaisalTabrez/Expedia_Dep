"""Immutable Python bindings for EDS Appendix A canonical contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import PurePosixPath
from collections.abc import Mapping, Sequence

from .errors import ContractValidationError
from .serialization import (
    FrozenJson,
    canonical_json,
    freeze_json,
    parse_json,
    reject_unknown_fields,
    require_fields,
    require_mapping,
    require_string,
    thaw_json,
)


class ReleaseState(str, Enum):
    """The EDS Atlas Release lifecycle states."""

    DRAFT = "Draft"
    CANDIDATE = "Candidate"
    PUBLISHED = "Published"
    SUPERSEDED = "Superseded"
    WITHDRAWN = "Withdrawn"


def _normalize_timestamp(value: str, *, field: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ContractValidationError(f"{field} must be an ISO 8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ContractValidationError(f"{field} must include a UTC offset")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_relative_artifact_path(value: str) -> None:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or value in {"", "."}:
        raise ContractValidationError("artifact path must be a safe relative POSIX path")


@dataclass(frozen=True, slots=True)
class ArtifactDescriptor:
    """A manifest-addressed immutable package artifact."""

    path: str
    media_type: str
    digest: str
    size: int
    contract_version: str

    def __post_init__(self) -> None:
        _validate_relative_artifact_path(require_string(self.path, field="artifact.path"))
        require_string(self.media_type, field="artifact.media_type")
        require_string(self.digest, field="artifact.digest")
        require_string(self.contract_version, field="artifact.contract_version")
        if isinstance(self.size, bool) or not isinstance(self.size, int) or self.size < 0:
            raise ContractValidationError("artifact.size must be a non-negative integer")

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "media_type": self.media_type,
            "digest": self.digest,
            "size": self.size,
            "contract_version": self.contract_version,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ArtifactDescriptor":
        allowed = {"path", "media_type", "digest", "size", "contract_version"}
        require_fields(payload, required=allowed, contract="ArtifactDescriptor")
        reject_unknown_fields(payload, allowed=allowed, contract="ArtifactDescriptor")
        return cls(
            path=payload["path"],  # type: ignore[arg-type]
            media_type=payload["media_type"],  # type: ignore[arg-type]
            digest=payload["digest"],  # type: ignore[arg-type]
            size=payload["size"],  # type: ignore[arg-type]
            contract_version=payload["contract_version"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class ReleaseManifest:
    """EDS Appendix A release package contract."""

    release_id: str
    schema_version: str
    state: ReleaseState
    scope: Mapping[str, FrozenJson]
    artifacts: tuple[ArtifactDescriptor, ...]
    validation: Mapping[str, FrozenJson]
    created_at: str | None = None
    base_release: str | None = None
    citation: Mapping[str, FrozenJson] | None = None
    licenses: tuple[Mapping[str, FrozenJson], ...] = ()

    def __post_init__(self) -> None:
        require_string(self.release_id, field="release_id")
        require_string(self.schema_version, field="schema_version")
        object.__setattr__(self, "scope", require_mapping(self.scope, field="scope", non_empty=True))
        object.__setattr__(self, "validation", require_mapping(self.validation, field="validation", non_empty=True))
        if self.created_at is not None:
            object.__setattr__(
                self,
                "created_at",
                _normalize_timestamp(require_string(self.created_at, field="created_at"), field="created_at"),
            )
        if self.base_release is not None:
            require_string(self.base_release, field="base_release")
        if self.citation is not None:
            object.__setattr__(self, "citation", require_mapping(self.citation, field="citation", non_empty=True))
        frozen_licenses = tuple(
            require_mapping(license_record, field="licenses[]", non_empty=True)
            for license_record in self.licenses
        )
        object.__setattr__(self, "licenses", frozen_licenses)
        if not self.artifacts:
            raise ContractValidationError("artifacts must contain at least one descriptor")
        if len({artifact.path for artifact in self.artifacts}) != len(self.artifacts):
            raise ContractValidationError("artifacts must not contain duplicate paths")

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "release_id": self.release_id,
            "schema_version": self.schema_version,
            "state": self.state.value,
            "scope": thaw_json(self.scope),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "validation": thaw_json(self.validation),
        }
        if self.created_at is not None:
            payload["created_at"] = self.created_at
        if self.base_release is not None:
            payload["base_release"] = self.base_release
        if self.citation is not None:
            payload["citation"] = thaw_json(self.citation)
        if self.licenses:
            payload["licenses"] = [thaw_json(record) for record in self.licenses]
        return payload

    def to_json(self) -> str:
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ReleaseManifest":
        required = {"release_id", "schema_version", "state", "scope", "artifacts", "validation"}
        allowed = required | {"created_at", "base_release", "citation", "licenses"}
        require_fields(payload, required=required, contract="ReleaseManifest")
        reject_unknown_fields(payload, allowed=allowed, contract="ReleaseManifest")
        raw_artifacts = payload["artifacts"]
        if not isinstance(raw_artifacts, list):
            raise ContractValidationError("artifacts must be an array")
        artifacts = tuple(
            ArtifactDescriptor.from_dict(item)
            for item in raw_artifacts
            if isinstance(item, Mapping)
        )
        if len(artifacts) != len(raw_artifacts):
            raise ContractValidationError("artifacts must contain objects")
        raw_licenses = payload.get("licenses", [])
        if not isinstance(raw_licenses, list):
            raise ContractValidationError("licenses must be an array")
        try:
            state = ReleaseState(payload["state"])
        except (TypeError, ValueError) as error:
            raise ContractValidationError("state is not a valid Atlas Release state") from error
        return cls(
            release_id=payload["release_id"],  # type: ignore[arg-type]
            schema_version=payload["schema_version"],  # type: ignore[arg-type]
            state=state,
            scope=payload["scope"],  # type: ignore[arg-type]
            artifacts=artifacts,
            validation=payload["validation"],  # type: ignore[arg-type]
            created_at=payload.get("created_at"),  # type: ignore[arg-type]
            base_release=payload.get("base_release"),  # type: ignore[arg-type]
            citation=payload.get("citation"),  # type: ignore[arg-type]
            licenses=tuple(raw_licenses),  # type: ignore[arg-type]
        )

    @classmethod
    def from_json(cls, payload: str) -> "ReleaseManifest":
        return cls.from_dict(parse_json(payload))


@dataclass(frozen=True, slots=True)
class GenomeRecordVersion:
    """EDS Appendix A immutable sequence-normalized record."""

    record_id: str
    entity_id: str
    sequence_digest: str
    canonicalization_id: str
    source_provenance_id: str
    lifecycle_state: str

    def __post_init__(self) -> None:
        for field, value in self.to_dict().items():
            require_string(value, field=field)

    def to_dict(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "entity_id": self.entity_id,
            "sequence_digest": self.sequence_digest,
            "canonicalization_id": self.canonicalization_id,
            "source_provenance_id": self.source_provenance_id,
            "lifecycle_state": self.lifecycle_state,
        }

    def to_json(self) -> str:
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "GenomeRecordVersion":
        required = {
            "record_id", "entity_id", "sequence_digest", "canonicalization_id",
            "source_provenance_id", "lifecycle_state",
        }
        require_fields(payload, required=required, contract="GenomeRecordVersion")
        reject_unknown_fields(payload, allowed=required, contract="GenomeRecordVersion")
        return cls(**{field: payload[field] for field in required})  # type: ignore[arg-type]

    @classmethod
    def from_json(cls, payload: str) -> "GenomeRecordVersion":
        return cls.from_dict(parse_json(payload))


@dataclass(frozen=True, slots=True)
class EmbeddingProfile:
    """EDS Appendix A complete profile declaration for one vector representation."""

    profile_id: str
    version: str
    input_contract: Mapping[str, FrozenJson]
    model: Mapping[str, FrozenJson]
    tokenization: Mapping[str, FrozenJson]
    pooling: Mapping[str, FrozenJson]
    preprocessing: Mapping[str, FrozenJson]
    output: Mapping[str, FrozenJson]
    metric: Mapping[str, FrozenJson]
    compatibility: Mapping[str, FrozenJson]
    provenance: Mapping[str, FrozenJson]
    lifecycle: str
    validation_links: tuple[str, ...]

    def __post_init__(self) -> None:
        require_string(self.profile_id, field="profile_id")
        require_string(self.version, field="version")
        for field in ("input_contract", "tokenization", "pooling", "compatibility"):
            object.__setattr__(self, field, require_mapping(getattr(self, field), field=field, non_empty=True))
        object.__setattr__(self, "preprocessing", require_mapping(self.preprocessing, field="preprocessing"))
        model = require_mapping(self.model, field="model", non_empty=True)
        output = require_mapping(self.output, field="output", non_empty=True)
        metric = require_mapping(self.metric, field="metric", non_empty=True)
        provenance = require_mapping(self.provenance, field="provenance", non_empty=True)
        for key in ("artifact", "revision", "content_digest"):
            require_string(model.get(key), field=f"model.{key}")
        dimension = output.get("dimension")
        if isinstance(dimension, bool) or not isinstance(dimension, int) or dimension < 1:
            raise ContractValidationError("output.dimension must be a positive integer")
        require_string(output.get("dtype"), field="output.dtype")
        require_string(metric.get("name"), field="metric.name")
        require_string(metric.get("direction"), field="metric.direction")
        for key in ("plugin_descriptor", "runner_environment", "determinism"):
            require_string(provenance.get(key), field=f"provenance.{key}")
        object.__setattr__(self, "model", model)
        object.__setattr__(self, "output", output)
        object.__setattr__(self, "metric", metric)
        object.__setattr__(self, "provenance", provenance)
        require_string(self.lifecycle, field="lifecycle")
        if any(not isinstance(link, str) or not link.strip() for link in self.validation_links):
            raise ContractValidationError("validation_links must contain non-empty strings")

    def to_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "version": self.version,
            "input_contract": thaw_json(self.input_contract),
            "model": thaw_json(self.model),
            "tokenization": thaw_json(self.tokenization),
            "pooling": thaw_json(self.pooling),
            "preprocessing": thaw_json(self.preprocessing),
            "output": thaw_json(self.output),
            "metric": thaw_json(self.metric),
            "compatibility": thaw_json(self.compatibility),
            "provenance": thaw_json(self.provenance),
            "lifecycle": self.lifecycle,
            "validation_links": list(self.validation_links),
        }

    def to_json(self) -> str:
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "EmbeddingProfile":
        required = {
            "profile_id", "version", "input_contract", "model", "tokenization", "pooling",
            "preprocessing", "output", "metric", "compatibility", "provenance", "lifecycle",
            "validation_links",
        }
        require_fields(payload, required=required, contract="EmbeddingProfile")
        reject_unknown_fields(payload, allowed=required, contract="EmbeddingProfile")
        links = payload["validation_links"]
        if not isinstance(links, list):
            raise ContractValidationError("validation_links must be an array")
        return cls(
            profile_id=payload["profile_id"],  # type: ignore[arg-type]
            version=payload["version"],  # type: ignore[arg-type]
            input_contract=payload["input_contract"],  # type: ignore[arg-type]
            model=payload["model"],  # type: ignore[arg-type]
            tokenization=payload["tokenization"],  # type: ignore[arg-type]
            pooling=payload["pooling"],  # type: ignore[arg-type]
            preprocessing=payload["preprocessing"],  # type: ignore[arg-type]
            output=payload["output"],  # type: ignore[arg-type]
            metric=payload["metric"],  # type: ignore[arg-type]
            compatibility=payload["compatibility"],  # type: ignore[arg-type]
            provenance=payload["provenance"],  # type: ignore[arg-type]
            lifecycle=payload["lifecycle"],  # type: ignore[arg-type]
            validation_links=tuple(links),  # type: ignore[arg-type]
        )

    @classmethod
    def from_json(cls, payload: str) -> "EmbeddingProfile":
        return cls.from_dict(parse_json(payload))


@dataclass(frozen=True, slots=True)
class EmbeddingInstance:
    """EDS Appendix A profile-specific vector reference for one record version."""

    instance_id: str
    record_id: str
    profile_id: str
    vector_reference: Mapping[str, FrozenJson]
    created_in: str
    runner_provenance: Mapping[str, FrozenJson]
    eligibility_status: str

    def __post_init__(self) -> None:
        for field, value in (
            ("instance_id", self.instance_id),
            ("record_id", self.record_id),
            ("profile_id", self.profile_id),
            ("created_in", self.created_in),
            ("eligibility_status", self.eligibility_status),
        ):
            require_string(value, field=field)
        vector_reference = require_mapping(self.vector_reference, field="vector_reference", non_empty=True)
        for key in ("shard_id", "shard_digest"):
            require_string(vector_reference.get(key), field=f"vector_reference.{key}")
        row = vector_reference.get("row")
        if isinstance(row, bool) or not isinstance(row, int) or row < 0:
            raise ContractValidationError("vector_reference.row must be a non-negative integer")
        object.__setattr__(self, "vector_reference", vector_reference)
        object.__setattr__(
            self,
            "runner_provenance",
            require_mapping(self.runner_provenance, field="runner_provenance", non_empty=True),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "instance_id": self.instance_id,
            "record_id": self.record_id,
            "profile_id": self.profile_id,
            "vector_reference": thaw_json(self.vector_reference),
            "created_in": self.created_in,
            "runner_provenance": thaw_json(self.runner_provenance),
            "eligibility_status": self.eligibility_status,
        }

    def to_json(self) -> str:
        return canonical_json(self.to_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "EmbeddingInstance":
        required = {
            "instance_id", "record_id", "profile_id", "vector_reference", "created_in",
            "runner_provenance", "eligibility_status",
        }
        require_fields(payload, required=required, contract="EmbeddingInstance")
        reject_unknown_fields(payload, allowed=required, contract="EmbeddingInstance")
        return cls(**{field: payload[field] for field in required})  # type: ignore[arg-type]

    @classmethod
    def from_json(cls, payload: str) -> "EmbeddingInstance":
        return cls.from_dict(parse_json(payload))
