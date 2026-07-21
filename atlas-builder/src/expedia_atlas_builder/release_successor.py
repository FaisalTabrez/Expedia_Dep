"""Controlled, non-scientific correction of an immutable M1 Draft package."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from .acquisition import sha256_file
from .release_packaging import (
    PACKAGE_ENVELOPE_PATH,
    ROOT_MANIFEST_NAME,
    Artifact,
    _artifact_descriptor,
    _safe_relative_path,
    verify_draft_package,
)


PROFILE_RECORD_PATH = "profiles/m1-generanno-prokaryote-0.5b-assembly-v1.json"
PROFILE_RECORD_MEDIA_TYPE = "application/json"
PROFILE_RECORD_CONTRACT_VERSION = "0.1.0"


class ReleaseSuccessorError(RuntimeError):
    """A controlled M1 Draft successor could not preserve its predecessor."""


@dataclass(frozen=True, slots=True)
class SuccessorCorrectionResult:
    """Integrity anchors and preservation evidence for one Draft successor."""

    predecessor_release_id: str
    predecessor_manifest_digest: str
    successor_release_id: str
    successor_manifest_digest: str
    profile_record_digest: str
    preserved_artifact_count: int
    successor_artifact_count: int


def _digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _read_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseSuccessorError(f"cannot read {label}") from error
    if not isinstance(value, dict):
        raise ReleaseSuccessorError(f"{label} must be a JSON object")
    return value


def _normalized_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ReleaseSuccessorError("successor created_at must be ISO 8601") from error
    if parsed.tzinfo is None:
        raise ReleaseSuccessorError("successor created_at must include a UTC offset")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _artifact_metadata(manifest: Mapping[str, object]) -> dict[str, Artifact]:
    raw_artifacts = manifest.get("artifacts")
    if not isinstance(raw_artifacts, list):
        raise ReleaseSuccessorError("predecessor ReleaseManifest lacks artifact descriptors")
    metadata: dict[str, Artifact] = {}
    for raw in raw_artifacts:
        if not isinstance(raw, dict):
            raise ReleaseSuccessorError("predecessor artifact descriptor is invalid")
        path = raw.get("path")
        media_type = raw.get("media_type")
        contract_version = raw.get("contract_version")
        if not all(isinstance(value, str) for value in (path, media_type, contract_version)):
            raise ReleaseSuccessorError("predecessor artifact metadata is incomplete")
        _safe_relative_path(path)
        metadata[path] = Artifact(path, media_type, contract_version)
    return metadata


def _descriptors(package: Path, metadata: Mapping[str, Artifact], *, include_stage: bool) -> list[dict[str, object]]:
    paths = [path for path in metadata if include_stage or path != PACKAGE_ENVELOPE_PATH]
    descriptors: list[dict[str, object]] = []
    for path in sorted(paths):
        artifact = metadata[path]
        target = package / path
        if not target.is_file():
            raise ReleaseSuccessorError(f"successor artifact is missing: {path}")
        descriptors.append(_artifact_descriptor(package, artifact))
    return descriptors


def _write_json(path: Path, payload: Mapping[str, object], *, compact: bool) -> None:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")) if compact else json.dumps(payload, sort_keys=True, indent=2) + "\n"
    path.write_text(serialized, encoding="utf-8")


def _assert_preserved(
    predecessor: Mapping[str, Artifact],
    successor: Mapping[str, Artifact],
    predecessor_package: Path,
    successor_package: Path,
) -> int:
    preserved = 0
    for path, descriptor in predecessor.items():
        if path == PACKAGE_ENVELOPE_PATH:
            continue
        successor_descriptor = successor.get(path)
        if successor_descriptor != descriptor:
            raise ReleaseSuccessorError(f"successor changed artifact metadata: {path}")
        before = predecessor_package / path
        after = successor_package / path
        if not after.is_file() or sha256_file(before) != sha256_file(after) or before.stat().st_size != after.stat().st_size:
            raise ReleaseSuccessorError(f"successor changed preserved artifact bytes: {path}")
        preserved += 1
    return preserved


def create_m1_profile_successor(
    *,
    predecessor_package: Path,
    profile_record: Path,
    successor_package: Path,
    successor_release_id: str,
    created_at: str,
) -> SuccessorCorrectionResult:
    """Create a new M1 Draft package that adds only the canonical profile record.

    The predecessor is verified before copying and remains untouched. Every
    predecessor payload other than the package-stage envelope is required to be
    byte-identical in the successor; the envelope and root manifest are
    intentionally regenerated to bind the added declaration.
    """

    if not successor_release_id.strip():
        raise ReleaseSuccessorError("successor release_id must be non-empty")
    if successor_package.exists():
        raise ReleaseSuccessorError("successor package directory must not already exist")
    predecessor_manifest = verify_draft_package(predecessor_package)
    if not isinstance(predecessor_manifest, dict) or predecessor_manifest.get("state") != "Draft":
        raise ReleaseSuccessorError("predecessor must be a verified Draft package")
    predecessor_release_id = predecessor_manifest.get("release_id")
    if not isinstance(predecessor_release_id, str) or not predecessor_release_id:
        raise ReleaseSuccessorError("predecessor ReleaseManifest has no release_id")
    if successor_release_id == predecessor_release_id:
        raise ReleaseSuccessorError("successor release_id must differ from predecessor")
    if not profile_record.is_file():
        raise ReleaseSuccessorError("canonical profile record is missing")
    _read_object(profile_record, label="canonical profile record")
    metadata = _artifact_metadata(predecessor_manifest)
    if PROFILE_RECORD_PATH in metadata:
        raise ReleaseSuccessorError("predecessor already contains the canonical profile record")
    predecessor_manifest_digest = _digest((predecessor_package / ROOT_MANIFEST_NAME).read_bytes())
    profile_digest = sha256_file(profile_record)
    created_at = _normalized_timestamp(created_at)

    shutil.copytree(predecessor_package, successor_package)
    try:
        target_profile = successor_package / PROFILE_RECORD_PATH
        target_profile.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(profile_record, target_profile)
        metadata[PROFILE_RECORD_PATH] = Artifact(
            PROFILE_RECORD_PATH,
            PROFILE_RECORD_MEDIA_TYPE,
            PROFILE_RECORD_CONTRACT_VERSION,
        )

        output_descriptors = _descriptors(successor_package, metadata, include_stage=False)
        package_envelope = {
            "stage_id": "package",
            "input_artifacts": [
                {
                    "path": f"predecessor/{predecessor_release_id}/release-manifest.json",
                    "media_type": "application/json",
                    "digest": predecessor_manifest_digest,
                },
                {
                    "path": "repository/profiles/embedding/m1-generanno-prokaryote-0.5b-assembly-v1.json",
                    "media_type": PROFILE_RECORD_MEDIA_TYPE,
                    "digest": profile_digest,
                },
            ],
            "output_artifacts": output_descriptors,
            "outcome": "succeeded",
            "verification": {
                "release_id": successor_release_id,
                "predecessor_release_id": predecessor_release_id,
                "predecessor_manifest_digest": predecessor_manifest_digest,
                "profile_record": PROFILE_RECORD_PATH,
                "profile_record_digest": profile_digest,
                "preservation_policy": "All predecessor payloads except the regenerated package-stage envelope are byte-identical.",
                "root_manifest": ROOT_MANIFEST_NAME,
                "root_manifest_is_payload": False,
            },
            "recovery": {"retry_requires": "a new empty successor directory"},
        }
        _write_json(successor_package / PACKAGE_ENVELOPE_PATH, package_envelope, compact=False)

        successor_manifest = dict(predecessor_manifest)
        successor_manifest["release_id"] = successor_release_id
        successor_manifest["created_at"] = created_at
        successor_manifest["base_release"] = predecessor_release_id
        successor_manifest["artifacts"] = _descriptors(successor_package, metadata, include_stage=True)
        validation = successor_manifest.get("validation")
        if not isinstance(validation, dict):
            raise ReleaseSuccessorError("predecessor ReleaseManifest validation is invalid")
        successor_manifest["validation"] = {
            **validation,
            "status": "M1 controlled Draft successor correction assembled; independent evidence binding pending",
            "profile_declaration": PROFILE_RECORD_PATH,
            "profile_declaration_digest": profile_digest,
            "predecessor_manifest_digest": predecessor_manifest_digest,
        }
        _write_json(successor_package / ROOT_MANIFEST_NAME, successor_manifest, compact=True)
        verified_manifest = verify_draft_package(successor_package)
        successor_metadata = _artifact_metadata(verified_manifest)
        preserved_count = _assert_preserved(
            predecessor=_artifact_metadata(predecessor_manifest),
            successor=successor_metadata,
            predecessor_package=predecessor_package,
            successor_package=successor_package,
        )
    except Exception:
        # The caller must inspect or explicitly remove a failed successor; no
        # existing immutable predecessor is ever modified or deleted here.
        raise

    return SuccessorCorrectionResult(
        predecessor_release_id=predecessor_release_id,
        predecessor_manifest_digest=predecessor_manifest_digest,
        successor_release_id=successor_release_id,
        successor_manifest_digest=_digest((successor_package / ROOT_MANIFEST_NAME).read_bytes()),
        profile_record_digest=profile_digest,
        preserved_artifact_count=preserved_count,
        successor_artifact_count=len(successor_metadata),
    )
