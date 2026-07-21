"""The narrow M2.2 trusted local release boundary.

This adapter has one responsibility: turn a locally verified M1 Draft package
into an immutable in-memory ``VerifiedRelease`` snapshot. It deliberately does
not inspect query requests, rank vectors, apply filters, encode cursors, or
return query results. Those are later Query Core phases.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Literal

from expedia_contracts.models import ReleaseManifest
from expedia_contracts.serialization import FrozenJson, freeze_json
from expedia_validation.release_reader import ReleaseReaderError, read_release


ROOT_MANIFEST_NAME = "release-manifest.json"
M1_VECTOR_PAYLOAD_PATH = "embeddings/vectors.float32le"
M1_VECTOR_MANIFEST_PATH = "embeddings/vector-shard-manifest.json"
VECTOR_MEDIA_TYPE = "application/vnd.expedia.embedding-vector+float32;version=1"
JSONL_MEDIA_TYPE = "application/x-ndjson"


class ReleaseVerificationFailure(RuntimeError):
    """A typed failure to produce a trusted ``VerifiedRelease``.

    The code values are intentionally drawn from the accepted M2 QueryError
    contract. The exception never carries package payloads; callers may use
    only its fixed code and diagnostic message before query execution exists.
    """

    def __init__(
        self,
        code: Literal["release_not_found", "release_untrusted"],
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class VerifiedArtifact:
    """One manifest-addressed payload retained in a verified snapshot."""

    path: str
    media_type: str
    contract_version: str
    digest: str
    size: int


@dataclass(frozen=True, slots=True)
class VerifiedVectorShard:
    """A profile-scoped vector payload without similarity behavior."""

    profile_id: str
    shard_id: str
    digest: str
    dimension: int
    dtype: str
    row_mapping: Mapping[str, str]
    payload: bytes


@dataclass(frozen=True, slots=True)
class VerifiedRelease:
    """An immutable snapshot produced only after local reader verification."""

    release_id: str
    release_manifest_digest: str
    schema_version: str
    state: str
    manifest: ReleaseManifest
    artifacts: Mapping[str, VerifiedArtifact]
    _payloads: Mapping[str, bytes]
    _vector_shards: Mapping[str, VerifiedVectorShard]

    @property
    def artifact_count(self) -> int:
        """Return the count of manifest-addressed payload artifacts."""

        return len(self.artifacts)

    @property
    def release_digest(self) -> str:
        """Return the ReleaseManifest digest used to bind later query context."""

        return self.release_manifest_digest

    @property
    def vector_profiles(self) -> tuple[str, ...]:
        """Return declared vector profile identifiers in deterministic order."""

        return tuple(sorted(self._vector_shards))

    def read_table(self, path: str) -> tuple[Mapping[str, FrozenJson], ...]:
        """Decode one verified JSONL table from the immutable snapshot.

        The argument is a manifest path, not an arbitrary filesystem path. This
        prevents callers from using a verified handle to read a mutable package
        directory or unrelated local data.
        """

        artifact = self.artifacts.get(path)
        if artifact is None:
            raise KeyError(f"manifest-addressed artifact is not available: {path}")
        if artifact.media_type != JSONL_MEDIA_TYPE:
            raise ValueError(f"artifact is not a JSONL table: {path}")
        try:
            rows = [json.loads(line) for line in self._payloads[path].decode("utf-8").splitlines() if line]
        except (UnicodeDecodeError, json.JSONDecodeError) as error:  # pragma: no cover - verified before snapshot.
            raise ReleaseVerificationFailure("release_untrusted", f"verified table cannot be decoded: {path}") from error
        if not all(isinstance(row, dict) for row in rows):  # pragma: no cover - verified before snapshot.
            raise ReleaseVerificationFailure("release_untrusted", f"verified table has a non-object row: {path}")
        return tuple(freeze_json(row, field=path) for row in rows)  # type: ignore[return-value]

    def vector_shard(self, profile_id: str) -> VerifiedVectorShard:
        """Return a verified profile-scoped vector payload without ranking it."""

        try:
            return self._vector_shards[profile_id]
        except KeyError as error:
            raise KeyError(f"verified release has no vector shard for profile: {profile_id}") from error


def _sha256(payload: bytes) -> str:
    return "sha256:" + sha256(payload).hexdigest()


def _safe_artifact_path(path: str) -> None:
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or ".." in parsed.parts or "\\" in path or path in {"", "."}:
        raise ReleaseVerificationFailure("release_untrusted", "ReleaseManifest contains an unsafe artifact path")


def _load_manifest_snapshot(package: Path, expected_digest: str) -> ReleaseManifest:
    manifest_path = package / ROOT_MANIFEST_NAME
    package_root = package.resolve()
    try:
        manifest_resolved = manifest_path.resolve(strict=True)
    except OSError as error:
        raise ReleaseVerificationFailure("release_untrusted", "ReleaseManifest is unavailable after verification") from error
    if manifest_path.is_symlink() or not manifest_resolved.is_relative_to(package_root):
        raise ReleaseVerificationFailure("release_untrusted", "ReleaseManifest escapes the release package")
    try:
        payload = manifest_path.read_bytes()
        raw_manifest = json.loads(payload.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseVerificationFailure("release_untrusted", "ReleaseManifest cannot be read after verification") from error
    if _sha256(payload) != expected_digest:
        raise ReleaseVerificationFailure("release_untrusted", "ReleaseManifest changed during verification")
    if not isinstance(raw_manifest, dict):
        raise ReleaseVerificationFailure("release_untrusted", "ReleaseManifest is not an object")
    try:
        return ReleaseManifest.from_dict(raw_manifest)
    except Exception as error:
        raise ReleaseVerificationFailure("release_untrusted", "ReleaseManifest is incompatible with the local reader") from error


def _snapshot_artifacts(package: Path, manifest: ReleaseManifest) -> Mapping[str, bytes]:
    package_root = package.resolve()
    snapshots: dict[str, bytes] = {}
    for descriptor in manifest.artifacts:
        _safe_artifact_path(descriptor.path)
        path = package / descriptor.path
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise ReleaseVerificationFailure("release_untrusted", f"manifest-addressed artifact is unavailable: {descriptor.path}") from error
        if path.is_symlink() or not resolved.is_relative_to(package_root):
            raise ReleaseVerificationFailure("release_untrusted", f"manifest-addressed artifact escapes package: {descriptor.path}")
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise ReleaseVerificationFailure("release_untrusted", f"manifest-addressed artifact cannot be read: {descriptor.path}") from error
        if len(payload) != descriptor.size or _sha256(payload) != descriptor.digest:
            raise ReleaseVerificationFailure("release_untrusted", f"manifest-addressed artifact changed during verification: {descriptor.path}")
        snapshots[descriptor.path] = payload
    return MappingProxyType(snapshots)


def _vector_shards(
    artifacts: Mapping[str, VerifiedArtifact],
    payloads: Mapping[str, bytes],
) -> Mapping[str, VerifiedVectorShard]:
    vector_artifact = artifacts.get(M1_VECTOR_PAYLOAD_PATH)
    manifest_artifact = artifacts.get(M1_VECTOR_MANIFEST_PATH)
    if vector_artifact is None or manifest_artifact is None:
        raise ReleaseVerificationFailure("release_untrusted", "verified M1 package lacks its vector shard artifacts")
    if vector_artifact.media_type != VECTOR_MEDIA_TYPE or manifest_artifact.media_type != "application/json":
        raise ReleaseVerificationFailure("release_untrusted", "verified M1 vector shard media types are incompatible")
    try:
        raw = json.loads(payloads[M1_VECTOR_MANIFEST_PATH].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseVerificationFailure("release_untrusted", "verified vector shard manifest cannot be decoded") from error
    if not isinstance(raw, dict):
        raise ReleaseVerificationFailure("release_untrusted", "verified vector shard manifest is not an object")
    profile_id = raw.get("profile_id")
    shard_id = raw.get("shard_id")
    digest = raw.get("digest")
    dimension = raw.get("dimension")
    dtype = raw.get("dtype")
    row_mapping = raw.get("row_mapping")
    if (
        not isinstance(profile_id, str)
        or not isinstance(shard_id, str)
        or not isinstance(digest, str)
        or isinstance(dimension, bool)
        or not isinstance(dimension, int)
        or not isinstance(dtype, str)
        or not isinstance(row_mapping, dict)
        or not all(isinstance(key, str) and isinstance(value, str) for key, value in row_mapping.items())
        or digest != vector_artifact.digest
    ):
        raise ReleaseVerificationFailure("release_untrusted", "verified vector shard declaration is incompatible")
    return MappingProxyType(
        {
            profile_id: VerifiedVectorShard(
                profile_id=profile_id,
                shard_id=shard_id,
                digest=digest,
                dimension=dimension,
                dtype=dtype,
                row_mapping=MappingProxyType(dict(row_mapping)),
                payload=payloads[M1_VECTOR_PAYLOAD_PATH],
            )
        }
    )


def open_verified_release(release_location: str | Path) -> VerifiedRelease:
    """Verify and snapshot one local M1 Draft package, or raise a typed failure."""

    package = Path(release_location)
    if not package.is_dir():
        raise ReleaseVerificationFailure("release_not_found", "release package directory does not exist")
    if package.is_symlink():
        raise ReleaseVerificationFailure("release_untrusted", "release package directory must not be a symbolic link")
    try:
        verification = read_release(package)
    except ReleaseReaderError as error:
        raise ReleaseVerificationFailure("release_untrusted", "local release reader verification failed") from error
    expected_digest = verification.get("release_manifest_digest")
    if not isinstance(expected_digest, str):  # pragma: no cover - protected by the M1 reader contract.
        raise ReleaseVerificationFailure("release_untrusted", "local release reader returned no manifest digest")
    manifest = _load_manifest_snapshot(package, expected_digest)
    payloads = _snapshot_artifacts(package, manifest)
    artifacts = MappingProxyType(
        {
            descriptor.path: VerifiedArtifact(
                path=descriptor.path,
                media_type=descriptor.media_type,
                contract_version=descriptor.contract_version,
                digest=descriptor.digest,
                size=descriptor.size,
            )
            for descriptor in manifest.artifacts
        }
    )
    return VerifiedRelease(
        release_id=manifest.release_id,
        release_manifest_digest=expected_digest,
        schema_version=manifest.schema_version,
        state=manifest.state.value,
        manifest=manifest,
        artifacts=artifacts,
        _payloads=payloads,
        _vector_shards=_vector_shards(artifacts, payloads),
    )
