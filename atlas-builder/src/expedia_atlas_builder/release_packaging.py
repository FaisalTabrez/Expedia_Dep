"""Deterministic M1.6 assembly and integrity checking for a Draft package."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import shutil
import struct
import zipfile

from .acquisition import sha256_file
from .embedding import VECTOR_DIMENSION


PROFILE_ID = "m1-generanno-prokaryote-0.5b-assembly-v1"
ADEE_ID = "m1-generanno-t4-cuda12.1-fp32-deterministic-v1"
RECORD_COUNT = 12
SCHEMA_VERSION = "release-manifest/0.1.0"
ROOT_MANIFEST_NAME = "release-manifest.json"
PACKAGE_ENVELOPE_PATH = "provenance/stages/package-stage-envelope.json"


class ReleasePackagingError(RuntimeError):
    """A Draft package cannot safely be assembled or consumed."""


@dataclass(frozen=True, slots=True)
class PackageInputs:
    """Explicit, already-verified inputs consumed by the M1.6 Packager."""

    embedding_artifacts_zip: Path
    record_versions: Path
    entities: Path
    quarantines: Path
    canonical_directory: Path
    source_provenance: Path
    source_inventory: Path
    acquisition_stage: Path
    canonicalization_stage: Path
    build_manifest: Path
    profile: Path
    plugin_descriptor: Path
    execution_environment: Path
    model_license_notice: Path
    accelerator_validation_evidence: Path
    schemas_directory: Path


@dataclass(frozen=True, slots=True)
class Artifact:
    """One content-addressed payload file in a Draft package."""

    path: str
    media_type: str
    contract_version: str


def _json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReleasePackagingError(f"cannot read JSON input: {path}") from error


def _write_json(path: Path, value: Mapping[str, object], *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        serialized = json.dumps(value, sort_keys=True, separators=(",", ":"))
    else:
        serialized = json.dumps(value, sort_keys=True, indent=2) + "\n"
    path.write_text(serialized, encoding="utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _safe_relative_path(path: str) -> None:
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or ".." in parsed.parts or "\\" in path or path in {"", "."}:
        raise ReleasePackagingError("package artifact path must be a safe relative POSIX path")


def _copy(source: Path, package_directory: Path, relative_path: str) -> None:
    _safe_relative_path(relative_path)
    if not source.is_file():
        raise ReleasePackagingError(f"required package input is missing: {source}")
    destination = package_directory / relative_path
    if destination.exists():
        raise ReleasePackagingError(f"package path already populated: {relative_path}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def _canonical_files(canonical_directory: Path) -> tuple[Path, ...]:
    files = tuple(sorted(canonical_directory.glob("GCF_*.txt"), key=lambda path: path.name))
    if len(files) != RECORD_COUNT:
        raise ReleasePackagingError("M1.6 requires exactly twelve canonical assembly files")
    return files


def verify_embedding_artifacts_zip(path: Path) -> dict[str, object]:
    """Verify the M1.5 output bundle before treating it as a packaging input."""

    required = {
        "vectors.float32le",
        "vector-shard-manifest.json",
        "embedding-instances.jsonl",
        "embedding-stage-envelope.json",
    }
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as error:
        raise ReleasePackagingError("embedding artifact input is not a readable ZIP") from error
    with archive:
        names = {entry.filename for entry in archive.infolist() if not entry.is_dir()}
        if names != required:
            raise ReleasePackagingError("embedding artifact ZIP has an unexpected file inventory")
        payloads = {name: archive.read(name) for name in required}
    vectors = payloads["vectors.float32le"]
    if len(vectors) != RECORD_COUNT * VECTOR_DIMENSION * 4:
        raise ReleasePackagingError("embedding vector shard has an unexpected size")
    values = struct.unpack(f"<{RECORD_COUNT * VECTOR_DIMENSION}f", vectors)
    for row in range(RECORD_COUNT):
        vector = values[row * VECTOR_DIMENSION : (row + 1) * VECTOR_DIMENSION]
        if not all(math.isfinite(value) for value in vector):
            raise ReleasePackagingError("embedding vector shard contains a non-finite value")
        norm = math.sqrt(sum(value * value for value in vector))
        if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-6):
            raise ReleasePackagingError("embedding vector shard contains a non-normalized vector")
    try:
        shard_manifest = json.loads(payloads["vector-shard-manifest.json"])
        instances = [json.loads(line) for line in payloads["embedding-instances.jsonl"].decode("utf-8").splitlines()]
        envelope = json.loads(payloads["embedding-stage-envelope.json"])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleasePackagingError("embedding artifact ZIP contains invalid JSON") from error
    if not isinstance(shard_manifest, dict) or not isinstance(envelope, dict) or not all(isinstance(item, dict) for item in instances):
        raise ReleasePackagingError("embedding artifact ZIP has invalid JSON structures")
    shard_digest = _sha256_bytes(vectors)
    if shard_manifest.get("profile_id") != PROFILE_ID or shard_manifest.get("dimension") != VECTOR_DIMENSION:
        raise ReleasePackagingError("embedding shard manifest does not match the sole M1 profile")
    if shard_manifest.get("dtype") != "float32" or shard_manifest.get("digest") != shard_digest:
        raise ReleasePackagingError("embedding shard manifest does not verify the vector payload")
    rows = [item.get("vector_reference", {}).get("row") for item in instances]
    if len(instances) != RECORD_COUNT or rows != list(range(RECORD_COUNT)):
        raise ReleasePackagingError("embedding instances do not define exactly one ordered row per M1 record")
    if len({item.get("record_id") for item in instances}) != RECORD_COUNT:
        raise ReleasePackagingError("embedding instances contain duplicate record identifiers")
    if any(item.get("profile_id") != PROFILE_ID for item in instances):
        raise ReleasePackagingError("embedding instance does not use the sole M1 profile")
    provenance = shard_manifest.get("build_provenance", {}).get("runner_provenance")
    if not isinstance(provenance, dict) or provenance.get("execution_environment_id") != ADEE_ID:
        raise ReleasePackagingError("embedding shard lacks approved ADEE provenance")
    if envelope.get("stage_id") != "embed" or envelope.get("outcome") != "succeeded":
        raise ReleasePackagingError("embedding stage outcome is not successful")
    if envelope.get("verification", {}).get("runner_provenance") != provenance:
        raise ReleasePackagingError("embedding stage and shard runner provenance disagree")
    return {
        "zip_digest": sha256_file(path),
        "vector_shard_digest": shard_digest,
        "profile_id": PROFILE_ID,
        "record_count": RECORD_COUNT,
        "runner_provenance": provenance,
        "payloads": payloads,
    }


def _artifact_descriptor(package_directory: Path, artifact: Artifact) -> dict[str, object]:
    _safe_relative_path(artifact.path)
    file_path = package_directory / artifact.path
    return {
        "path": artifact.path,
        "media_type": artifact.media_type,
        "digest": sha256_file(file_path),
        "size": file_path.stat().st_size,
        "contract_version": artifact.contract_version,
    }


def _copy_static_inputs(inputs: PackageInputs, package_directory: Path, embedding_payloads: Mapping[str, bytes]) -> list[Artifact]:
    artifacts: list[Artifact] = []

    def copied(source: Path, relative_path: str, media_type: str, contract_version: str) -> None:
        _copy(source, package_directory, relative_path)
        artifacts.append(Artifact(relative_path, media_type, contract_version))

    copied(inputs.record_versions, "records/genome-record-versions.jsonl", "application/x-ndjson", "0.1.0")
    copied(inputs.entities, "records/atlas-entities.jsonl", "application/x-ndjson", "0.1.0")
    copied(inputs.quarantines, "records/quarantines.jsonl", "application/x-ndjson", "0.1.0")
    for canonical in _canonical_files(inputs.canonical_directory):
        copied(canonical, f"records/canonical/{canonical.name}", "application/vnd.expedia.canonical-assembly+utf-8;version=1", "1")
    copied(inputs.source_provenance, "provenance/source/source-provenance.json", "application/json", "0.1.0")
    copied(inputs.source_inventory, "provenance/source/m1-refseq-accessions.json", "application/json", "0.1.0")
    copied(inputs.acquisition_stage, "provenance/stages/acquisition-stage-envelope.json", "application/json", "0.1.0")
    copied(inputs.canonicalization_stage, "provenance/stages/canonicalization-stage-envelope.json", "application/json", "0.1.0")
    copied(inputs.build_manifest, "provenance/build/m1-build-manifest.t4-release.json", "application/json", "0.1.0")
    copied(inputs.profile, "profiles/m1-generanno-prokaryote-0.5b-assembly-v1.yaml", "text/yaml", "0.1.0")
    copied(inputs.plugin_descriptor, "profiles/m1-generanno-huggingface-adapter-input-v1.json", "application/json", "0.1.0")
    copied(inputs.execution_environment, f"profiles/{ADEE_ID}.json", "application/json", "1")
    copied(inputs.model_license_notice, "licenses/generanno-prokaryote-0.5b-base-MIT-notice.md", "text/markdown", "1")
    copied(inputs.accelerator_validation_evidence, "evidence/m1-t4-accelerator-implementation-validation.md", "text/markdown", "1")
    for schema in sorted(inputs.schemas_directory.glob("*.schema.json"), key=lambda path: path.name):
        copied(schema, f"schemas/json/{schema.name}", "application/schema+json", "0.1.0")
    catalogue = inputs.schemas_directory / "CONTRACT-CATALOGUE.md"
    copied(catalogue, "schemas/json/CONTRACT-CATALOGUE.md", "text/markdown", "1")
    for name, payload in embedding_payloads.items():
        target = f"embeddings/{name}"
        destination = package_directory / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        media_type = "application/vnd.expedia.embedding-vector+float32;version=1" if name == "vectors.float32le" else "application/x-ndjson" if name.endswith(".jsonl") else "application/json"
        artifacts.append(Artifact(target, media_type, "0.1.0"))
    return artifacts


def _assert_no_credentials(package_directory: Path, artifacts: Sequence[Artifact]) -> None:
    forbidden_names = {".env", "id_rsa", "credentials.json"}
    credential_markers = (b"-----BEGIN PRIVATE KEY-----", b"aws_secret_access_key", b"OPENAI_API_KEY=")
    for artifact in artifacts:
        path = package_directory / artifact.path
        if path.name.lower() in forbidden_names:
            raise ReleasePackagingError("Draft package contains a forbidden credential filename")
        if any(marker in path.read_bytes() for marker in credential_markers):
            raise ReleasePackagingError("Draft package contains a credential marker")


def _release_scope() -> dict[str, object]:
    return {
        "milestone": "M1",
        "population": "12 NCBI RefSeq complete prokaryotic assemblies",
        "distribution": "internal reproducibility validation only",
        "public_distribution": "not authorized",
        "scientific_claims": "none; proof-of-concept infrastructure package",
    }


def assemble_draft_package(
    *,
    inputs: PackageInputs,
    release_directory: Path,
    release_id: str,
    created_at: str,
) -> Path:
    """Build a new, immutable-by-construction M1 Draft package directory."""

    if not release_id.strip():
        raise ReleasePackagingError("release_id must be non-empty")
    try:
        parsed_created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise ReleasePackagingError("created_at must be an ISO 8601 timestamp") from error
    if parsed_created_at.tzinfo is None:
        raise ReleasePackagingError("created_at must include a UTC offset")
    created_at = parsed_created_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if release_directory.exists() and any(release_directory.iterdir()):
        raise ReleasePackagingError("release directory must be new and empty")
    release_directory.mkdir(parents=True, exist_ok=True)
    evidence = verify_embedding_artifacts_zip(inputs.embedding_artifacts_zip)
    artifacts = _copy_static_inputs(inputs, release_directory, evidence["payloads"])  # type: ignore[arg-type]
    _write_json(
        release_directory / "evidence" / "m1.5-release-artifact-validation.json",
        {
            "input_bundle_digest": evidence["zip_digest"],
            "vector_shard_digest": evidence["vector_shard_digest"],
            "record_count": evidence["record_count"],
            "profile_id": evidence["profile_id"],
            "runner_provenance": evidence["runner_provenance"],
            "verification": "M1.6 packager verified exact file inventory, vector finiteness and normalization, row mapping, shard digest, ADEE provenance, and successful embedding stage outcome.",
        },
    )
    artifacts.append(Artifact("evidence/m1.5-release-artifact-validation.json", "application/json", "1"))
    _assert_no_credentials(release_directory, artifacts)
    descriptors = [_artifact_descriptor(release_directory, artifact) for artifact in sorted(artifacts, key=lambda item: item.path)]
    package_envelope = {
        "stage_id": "package",
        "input_artifacts": [
            {"path": "external/m1-t4-release-artifacts.zip", "media_type": "application/zip", "digest": evidence["zip_digest"]},
            {"path": "source/genome-record-versions.jsonl", "media_type": "application/x-ndjson", "digest": sha256_file(inputs.record_versions)},
        ],
        "output_artifacts": descriptors,
        "outcome": "succeeded",
        "verification": {
            "release_id": release_id,
            "payload_artifact_count": len(descriptors),
            "credentials_detected": False,
            "root_manifest": ROOT_MANIFEST_NAME,
            "root_manifest_is_payload": False,
            "reason": "The ReleaseManifest is the package integrity anchor and cannot include its own content digest without a circular hash.",
        },
        "recovery": {"retry_requires": "a new empty release directory"},
    }
    _write_json(release_directory / PACKAGE_ENVELOPE_PATH, package_envelope)
    artifacts.append(Artifact(PACKAGE_ENVELOPE_PATH, "application/json", "0.1.0"))
    descriptors = [_artifact_descriptor(release_directory, artifact) for artifact in sorted(artifacts, key=lambda item: item.path)]
    manifest = {
        "release_id": release_id,
        "schema_version": SCHEMA_VERSION,
        "state": "Draft",
        "scope": _release_scope(),
        "created_at": created_at,
        "citation": {
            "status": "not assigned",
            "persistent_identifier": None,
            "statement": "This internal M1 Draft package is not citable and must not be represented as a Published Atlas Release.",
        },
        "artifacts": descriptors,
        "validation": {
            "status": "M1.6 package assembly passed; M1.7 independent validation pending",
            "embedding_stage_outcome": "provenance/stages/embedding-stage-envelope.json",
            "package_stage_outcome": PACKAGE_ENVELOPE_PATH,
            "vector_shard_digest": evidence["vector_shard_digest"],
            "approved_execution_environment": ADEE_ID,
        },
        "licenses": [
            {"artifact": "licenses/generanno-prokaryote-0.5b-base-MIT-notice.md", "spdx": "MIT"},
            {"artifact": "provenance/source/source-provenance.json", "scope": "internal M1 reproducibility validation only"},
        ],
    }
    _write_json(release_directory / ROOT_MANIFEST_NAME, manifest, compact=True)
    verify_draft_package(release_directory)
    return release_directory / ROOT_MANIFEST_NAME


def verify_draft_package(release_directory: Path) -> Mapping[str, object]:
    """Verify root-manifest structure and every manifest-addressed payload byte."""

    manifest_path = release_directory / ROOT_MANIFEST_NAME
    manifest = _json(manifest_path)
    if not isinstance(manifest, dict):
        raise ReleasePackagingError("ReleaseManifest must be a JSON object")
    required = {"release_id", "schema_version", "state", "scope", "artifacts", "validation"}
    if not required.issubset(manifest) or manifest.get("state") != "Draft":
        raise ReleasePackagingError("ReleaseManifest does not declare a valid Draft release")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ReleasePackagingError("ReleaseManifest has no artifact inventory")
    observed_paths: set[str] = set()
    for descriptor in artifacts:
        if not isinstance(descriptor, dict):
            raise ReleasePackagingError("ReleaseManifest contains a non-object artifact descriptor")
        path = descriptor.get("path")
        if not isinstance(path, str):
            raise ReleasePackagingError("ReleaseManifest artifact path is invalid")
        _safe_relative_path(path)
        if path == ROOT_MANIFEST_NAME or path in observed_paths:
            raise ReleasePackagingError("ReleaseManifest has an invalid artifact inventory")
        observed_paths.add(path)
        artifact_path = release_directory / path
        if not artifact_path.is_file():
            raise ReleasePackagingError(f"manifest-addressed artifact is missing: {path}")
        if descriptor.get("size") != artifact_path.stat().st_size or descriptor.get("digest") != sha256_file(artifact_path):
            raise ReleasePackagingError(f"manifest-addressed artifact integrity mismatch: {path}")
    expected_payloads = {
        file.relative_to(release_directory).as_posix()
        for file in release_directory.rglob("*")
        if file.is_file() and file.name != ROOT_MANIFEST_NAME
    }
    if expected_payloads != observed_paths:
        raise ReleasePackagingError("ReleaseManifest inventory does not cover exactly the package payload files")
    return manifest


def m1_repository_inputs(repository_root: Path, embedding_artifacts_zip: Path) -> PackageInputs:
    """Resolve only the committed M1.3/M1.4/provenance inputs for M1.6."""

    canonical = repository_root / "workspaces" / "m1" / "canonicalize" / "run-20260716"
    acquired = repository_root / "workspaces" / "m1" / "acquire" / "run-20260716-catalogue"
    manifests = repository_root / "atlas-builder" / "manifests" / "m1"
    return PackageInputs(
        embedding_artifacts_zip=embedding_artifacts_zip,
        record_versions=canonical / "genome-record-versions.jsonl",
        entities=canonical / "atlas-entities.jsonl",
        quarantines=canonical / "quarantines.jsonl",
        canonical_directory=canonical / "canonical",
        source_provenance=acquired / "source-provenance.json",
        source_inventory=manifests / "m1-refseq-accessions.json",
        acquisition_stage=acquired / "acquisition-stage-envelope.json",
        canonicalization_stage=canonical / "canonicalization-stage-envelope.json",
        build_manifest=manifests / "m1-build-manifest.t4-release.json",
        profile=repository_root / "profiles" / "embedding" / "m1-generanno-prokaryote-0.5b-assembly-v1.yaml",
        plugin_descriptor=repository_root / "profiles" / "plugins" / "m1-generanno-huggingface-adapter-input-v1.json",
        execution_environment=repository_root / "profiles" / "environments" / f"{ADEE_ID}.json",
        model_license_notice=repository_root / "profiles" / "licenses" / "generanno-prokaryote-0.5b-base-MIT-notice.md",
        accelerator_validation_evidence=repository_root / "validation" / "colab" / "evidence" / "m1-t4-accelerator-implementation-validation-2026-07-19.md",
        schemas_directory=repository_root / "schemas" / "json",
    )


def main(argv: list[str] | None = None) -> int:
    """Assemble a new M1 Draft package from one verified T4 artifact ZIP."""

    parser = argparse.ArgumentParser(description="Assemble and verify an M1.6 Draft release package.")
    parser.add_argument("--embedding-artifacts", type=Path, required=True)
    parser.add_argument("--release-directory", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--created-at", required=True)
    args = parser.parse_args(argv)
    repository_root = Path(__file__).resolve().parents[3]
    manifest_path = assemble_draft_package(
        inputs=m1_repository_inputs(repository_root, args.embedding_artifacts),
        release_directory=args.release_directory,
        release_id=args.release_id,
        created_at=args.created_at,
    )
    print(manifest_path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
