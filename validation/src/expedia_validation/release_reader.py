"""Package-only M1.7 reader and clean-room validation evidence generator."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import struct
from typing import Any

from jsonschema import Draft202012Validator


ROOT_MANIFEST_NAME = "release-manifest.json"
PROFILE_ID = "m1-generanno-prokaryote-0.5b-assembly-v1"
PROFILE_VERSION = "1.0.0"
PROFILE_RECORD_PATH = "profiles/m1-generanno-prokaryote-0.5b-assembly-v1.json"
ADEE_ID = "m1-generanno-t4-cuda12.1-fp32-deterministic-v1"
CANONICALIZATION_ID = "m1-assembly-canonical-v1"
VECTOR_DIMENSION = 1280
RECORD_COUNT = 12


class ReleaseReaderError(RuntimeError):
    """A release package failed a mandatory reader integrity gate."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def _sha256_bytes(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseReaderError(f"cannot read JSON: {path.name}") from error


def _require_object(value: object, message: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ReleaseReaderError(message)
    return value


def _safe_relative(path: str) -> None:
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or ".." in parsed.parts or "\\" in path or path in {"", "."}:
        raise ReleaseReaderError("manifest contains an unsafe artifact path")


def _schema(package: Path, name: str) -> dict[str, object]:
    value = _load_json(package / "schemas" / "json" / name)
    return _require_object(value, f"embedded schema is invalid: {name}")


def _validate(schema: Mapping[str, object], payload: object, label: str) -> None:
    try:
        Draft202012Validator(schema).validate(payload)
    except Exception as error:
        raise ReleaseReaderError(f"schema validation failed: {label}") from error


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseReaderError(f"cannot read JSONL: {path.name}") from error
    if not all(isinstance(row, dict) for row in rows):
        raise ReleaseReaderError(f"JSONL contains a non-object row: {path.name}")
    return rows  # type: ignore[return-value]


def _check_manifest_inventory(package: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    manifest = _require_object(_load_json(package / ROOT_MANIFEST_NAME), "ReleaseManifest must be an object")
    _validate(_schema(package, "release-manifest.schema.json"), manifest, "ReleaseManifest")
    if manifest.get("state") != "Draft":
        raise ReleaseReaderError("M1.7 accepts only the declared Draft release")
    scope = _require_object(manifest.get("scope"), "ReleaseManifest scope is invalid")
    citation = _require_object(manifest.get("citation"), "ReleaseManifest citation metadata is invalid")
    if scope.get("distribution") != "internal reproducibility validation only" or citation.get("status") != "not assigned":
        raise ReleaseReaderError("ReleaseManifest does not retain the approved M1 Draft scope")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ReleaseReaderError("ReleaseManifest has no artifacts")
    descriptors: list[dict[str, object]] = []
    seen: set[str] = set()
    for descriptor in artifacts:
        item = _require_object(descriptor, "ReleaseManifest has an invalid artifact descriptor")
        path = item.get("path")
        if not isinstance(path, str):
            raise ReleaseReaderError("ReleaseManifest artifact path is invalid")
        _safe_relative(path)
        if path in seen or path == ROOT_MANIFEST_NAME:
            raise ReleaseReaderError("ReleaseManifest artifact inventory is invalid")
        seen.add(path)
        file_path = package / path
        if not file_path.is_file():
            raise ReleaseReaderError(f"manifest-addressed artifact is missing: {path}")
        if item.get("size") != file_path.stat().st_size:
            raise ReleaseReaderError(f"manifest-addressed artifact size mismatch: {path}")
        if item.get("digest") != _sha256_file(file_path):
            raise ReleaseReaderError(f"manifest-addressed artifact digest mismatch: {path}")
        descriptors.append(item)
    actual = {
        file.relative_to(package).as_posix()
        for file in package.rglob("*")
        if file.is_file() and file.name != ROOT_MANIFEST_NAME
    }
    if actual != seen:
        raise ReleaseReaderError("ReleaseManifest does not cover exactly the payload inventory")
    return manifest, descriptors


def _check_records(package: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    records = _read_jsonl(package / "records" / "genome-record-versions.jsonl")
    entities = _read_jsonl(package / "records" / "atlas-entities.jsonl")
    record_schema = _schema(package, "genome-record-version.schema.json")
    entity_schema = _schema(package, "atlas-entity.schema.json")
    if len(records) != RECORD_COUNT or len(entities) != RECORD_COUNT:
        raise ReleaseReaderError("M1 package must contain exactly twelve records and entities")
    record_ids: set[str] = set()
    for record in records:
        _validate(record_schema, record, "GenomeRecordVersion")
        record_id = record.get("record_id")
        sequence_digest = record.get("sequence_digest")
        if not isinstance(record_id, str) or not isinstance(sequence_digest, str):
            raise ReleaseReaderError("record identity or sequence digest is invalid")
        if record.get("canonicalization_id") != CANONICALIZATION_ID or record.get("lifecycle_state") != "eligible":
            raise ReleaseReaderError("record does not satisfy the frozen M1 eligibility policy")
        if record_id in record_ids:
            raise ReleaseReaderError("package contains a duplicate record identifier")
        record_ids.add(record_id)
        prefix = "ncbi-assembly:"
        suffix = f":{CANONICALIZATION_ID}"
        if not record_id.startswith(prefix) or not record_id.endswith(suffix):
            raise ReleaseReaderError("record identifier is not an M1 canonical assembly record")
        accession = record_id[len(prefix) : -len(suffix)]
        canonical = package / "records" / "canonical" / f"{accession}.txt"
        if not canonical.is_file() or _sha256_file(canonical) != sequence_digest:
            raise ReleaseReaderError("canonical record bytes do not match their declared sequence digest")
    entity_record_ids = {item for entity in entities for item in entity.get("record_versions", []) if isinstance(item, str)}
    for entity in entities:
        _validate(entity_schema, entity, "AtlasEntity")
    if entity_record_ids != record_ids:
        raise ReleaseReaderError("AtlasEntity and GenomeRecordVersion references disagree")
    return records, entities


def _check_embeddings(package: Path, records: Sequence[Mapping[str, object]]) -> tuple[str, list[dict[str, object]]]:
    vector_path = package / "embeddings" / "vectors.float32le"
    payload = vector_path.read_bytes()
    if len(payload) != RECORD_COUNT * VECTOR_DIMENSION * 4:
        raise ReleaseReaderError("vector shard has an unexpected byte length")
    values = struct.unpack(f"<{RECORD_COUNT * VECTOR_DIMENSION}f", payload)
    for row in range(RECORD_COUNT):
        vector = values[row * VECTOR_DIMENSION : (row + 1) * VECTOR_DIMENSION]
        if not all(math.isfinite(value) for value in vector):
            raise ReleaseReaderError("vector shard contains non-finite values")
        norm = math.sqrt(sum(value * value for value in vector))
        if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-6):
            raise ReleaseReaderError("vector shard contains a non-normalized vector")
    shard = _require_object(_load_json(package / "embeddings" / "vector-shard-manifest.json"), "vector shard manifest is invalid")
    _validate(_schema(package, "vector-shard-manifest.schema.json"), shard, "VectorShardManifest")
    shard_digest = _sha256_file(vector_path)
    if shard.get("profile_id") != PROFILE_ID or shard.get("dimension") != VECTOR_DIMENSION:
        raise ReleaseReaderError("vector shard does not match the M1 embedding profile")
    if shard.get("digest") != shard_digest:
        raise ReleaseReaderError("vector shard manifest digest does not match the vector bytes")
    row_mapping = shard.get("row_mapping")
    if not isinstance(row_mapping, dict) or set(row_mapping) != {str(row) for row in range(RECORD_COUNT)}:
        raise ReleaseReaderError("vector shard row mapping is incomplete")
    provenance = _require_object(_require_object(shard.get("build_provenance"), "shard build provenance is missing").get("runner_provenance"), "runner provenance is missing")
    if provenance.get("execution_environment_id") != ADEE_ID:
        raise ReleaseReaderError("vector shard lacks the approved execution environment")
    instances = _read_jsonl(package / "embeddings" / "embedding-instances.jsonl")
    instance_schema = _schema(package, "embedding-instance.schema.json")
    if len(instances) != RECORD_COUNT:
        raise ReleaseReaderError("embedding instance count does not match the M1 record count")
    expected_record_ids = {record["record_id"] for record in records}
    instance_record_ids: set[object] = set()
    rows: list[object] = []
    for instance in instances:
        _validate(instance_schema, instance, "EmbeddingInstance")
        if instance.get("profile_id") != PROFILE_ID or instance.get("runner_provenance") != provenance:
            raise ReleaseReaderError("EmbeddingInstance profile or runner provenance mismatch")
        reference = _require_object(instance.get("vector_reference"), "EmbeddingInstance vector reference is invalid")
        if reference.get("shard_digest") != shard_digest:
            raise ReleaseReaderError("EmbeddingInstance does not reference the verified vector shard")
        instance_record_ids.add(instance.get("record_id"))
        rows.append(reference.get("row"))
    if instance_record_ids != expected_record_ids or rows != list(range(RECORD_COUNT)):
        raise ReleaseReaderError("EmbeddingInstance record or row mapping is invalid")
    if {item.get("instance_id") for item in instances} != set(row_mapping.values()):
        raise ReleaseReaderError("EmbeddingInstance identifiers do not match the vector shard row mapping")
    envelope = _require_object(_load_json(package / "embeddings" / "embedding-stage-envelope.json"), "embedding stage envelope is invalid")
    _validate(_schema(package, "stage-envelope.schema.json"), envelope, "Embedding stage envelope")
    if envelope.get("outcome") != "succeeded" or _require_object(envelope.get("verification"), "embedding verification is missing").get("runner_provenance") != provenance:
        raise ReleaseReaderError("embedding stage outcome does not verify the runner provenance")
    return shard_digest, instances


def _logical_release_digest(
    *,
    release_id: object,
    records: Sequence[Mapping[str, object]],
    entities: Sequence[Mapping[str, object]],
    instances: Sequence[Mapping[str, object]],
    vector_shard_digest: str,
) -> str:
    """Reconstruct the package's logical M1 release graph deterministically."""

    logical = {
        "release_id": release_id,
        "records": [
            {"record_id": record["record_id"], "entity_id": record["entity_id"], "sequence_digest": record["sequence_digest"]}
            for record in sorted(records, key=lambda item: str(item["record_id"]))
        ],
        "entities": [
            {"entity_id": entity["entity_id"], "record_versions": sorted(entity["record_versions"])}
            for entity in sorted(entities, key=lambda item: str(item["entity_id"]))
        ],
        "instances": [
            {"record_id": instance["record_id"], "profile_id": instance["profile_id"], "vector_reference": instance["vector_reference"]}
            for instance in sorted(instances, key=lambda item: int(_require_object(item["vector_reference"], "instance reference is invalid")["row"]))
        ],
        "vector_shard_digest": vector_shard_digest,
    }
    return _sha256_bytes(json.dumps(logical, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _check_optional_profile_declaration(package: Path) -> None:
    """Validate the controlled successor's canonical profile record when present.

    The v2 Draft remains readable as immutable historical evidence. The v3
    successor adds this declaration so later Query Core work can bind a request
    to an explicit profile version and its manifest-addressed digest.
    """

    path = package / PROFILE_RECORD_PATH
    if not path.exists():
        return
    profile = _require_object(_load_json(path), "EmbeddingProfile declaration is invalid")
    _validate(_schema(package, "embedding-profile.schema.json"), profile, "EmbeddingProfile")
    output = _require_object(profile.get("output"), "EmbeddingProfile output is invalid")
    metric = _require_object(profile.get("metric"), "EmbeddingProfile metric is invalid")
    if (
        profile.get("profile_id") != PROFILE_ID
        or profile.get("version") != PROFILE_VERSION
        or output.get("dimension") != VECTOR_DIMENSION
        or output.get("dtype") != "float32"
        or output.get("normalization") != "l2"
        or metric.get("name") != "cosine"
        or metric.get("direction") != "higher-is-more-similar"
    ):
        raise ReleaseReaderError("EmbeddingProfile declaration does not match the frozen M1 vector representation")


def _check_provenance_and_policy(package: Path) -> None:
    source = _require_object(_load_json(package / "provenance" / "source" / "source-provenance.json"), "source provenance is invalid")
    _validate(_schema(package, "source-provenance.schema.json"), source, "SourceProvenance")
    notice = _require_object(source.get("license_notice"), "source license notice is missing")
    if notice.get("scope") != "internal M1 reproducibility validation only":
        raise ReleaseReaderError("source license scope is not the approved M1 restriction")
    plugin = _require_object(_load_json(package / "profiles" / "m1-generanno-huggingface-adapter-input-v1.json"), "plugin descriptor is invalid")
    _validate(_schema(package, "plugin-descriptor.schema.json"), plugin, "PluginDescriptor")
    determinism = _require_object(plugin.get("determinism"), "plugin determinism declaration is missing")
    environment = _require_object(_load_json(package / "profiles" / f"{ADEE_ID}.json"), "ADEE declaration is invalid")
    if determinism.get("declaration_id") != ADEE_ID or environment.get("execution_environment_id") != ADEE_ID:
        raise ReleaseReaderError("plugin and packaged ADEE declaration disagree")
    build_manifest = _require_object(_load_json(package / "provenance" / "build" / "m1-build-manifest.t4-release.json"), "BuildManifest is invalid")
    _validate(_schema(package, "build-manifest.schema.json"), build_manifest, "BuildManifest")
    if build_manifest.get("embedding_profiles") != [PROFILE_ID]:
        raise ReleaseReaderError("BuildManifest does not select the sole M1 embedding profile")
    plugins = build_manifest.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        raise ReleaseReaderError("BuildManifest plugin selection is invalid")
    execution_selection = _require_object(_require_object(plugins[0], "BuildManifest plugin is invalid").get("execution_environment"), "BuildManifest ADEE selection is missing")
    if execution_selection.get("id") != ADEE_ID:
        raise ReleaseReaderError("BuildManifest does not select the approved ADEE")
    try:
        profile = (package / "profiles" / "m1-generanno-prokaryote-0.5b-assembly-v1.yaml").read_text(encoding="utf-8")
    except OSError as error:
        raise ReleaseReaderError("packaged embedding profile is missing") from error
    if f"profile_id: {PROFILE_ID}" not in profile or "dimension: 1280" not in profile:
        raise ReleaseReaderError("packaged embedding profile does not match the M1 vector representation")
    _check_optional_profile_declaration(package)
    for name in ("acquisition-stage-envelope.json", "canonicalization-stage-envelope.json", "package-stage-envelope.json"):
        envelope = _require_object(_load_json(package / "provenance" / "stages" / name), f"stage envelope is invalid: {name}")
        _validate(_schema(package, "stage-envelope.schema.json"), envelope, name)
        if envelope.get("outcome") != "succeeded":
            raise ReleaseReaderError(f"upstream stage did not succeed: {name}")
    for file in package.rglob("*"):
        if not file.is_file():
            continue
        if file.name.lower() in {".env", "id_rsa", "credentials.json"}:
            raise ReleaseReaderError("release package contains a forbidden credential filename")
        payload = file.read_bytes()
        if any(marker in payload for marker in (b"-----BEGIN PRIVATE KEY-----", b"aws_secret_access_key", b"OPENAI_API_KEY=")):
            raise ReleaseReaderError("release package contains a credential marker")


def read_release(package: Path) -> dict[str, object]:
    """Open a package using only its manifest-addressed contents and schemas."""

    if not package.is_dir():
        raise ReleaseReaderError("release package directory does not exist")
    manifest, descriptors = _check_manifest_inventory(package)
    records, entities = _check_records(package)
    shard_digest, instances = _check_embeddings(package, records)
    _check_provenance_and_policy(package)
    manifest_digest = _sha256_file(package / ROOT_MANIFEST_NAME)
    logical_digest = _logical_release_digest(
        release_id=manifest["release_id"],
        records=records,
        entities=entities,
        instances=instances,
        vector_shard_digest=shard_digest,
    )
    checks = [
        {"id": "release-manifest-schema-and-inventory", "status": "passed", "artifact_count": len(descriptors)},
        {"id": "canonical-record-and-entity-integrity", "status": "passed", "record_count": len(records)},
        {"id": "embedding-instance-and-vector-integrity", "status": "passed", "vector_shard_digest": shard_digest},
        {"id": "logical-release-reconstruction", "status": "passed", "logical_release_digest": logical_digest},
        {"id": "provenance-license-and-stage-policy", "status": "passed", "adee": ADEE_ID},
        {"id": "credential-scan", "status": "passed"},
    ]
    return {
        "release_id": manifest["release_id"],
        "release_manifest_digest": manifest_digest,
        "state": manifest["state"],
        "record_count": len(records),
        "artifact_count": len(descriptors),
        "vector_shard_digest": shard_digest,
        "logical_release_digest": logical_digest,
        "checks": checks,
    }


def write_validation_evidence(
    *,
    result: Mapping[str, object],
    validation_bundle_path: Path,
    run_record_path: Path,
    bundle_id: str,
    environment_label: str,
) -> None:
    """Write M1.7 external validation evidence without mutating the package."""

    if not bundle_id.strip() or not environment_label.strip():
        raise ReleaseReaderError("bundle_id and environment_label must be non-empty")
    release_digest = result.get("release_manifest_digest")
    checks = result.get("checks")
    if not isinstance(release_digest, str) or not isinstance(checks, list):
        raise ReleaseReaderError("reader result cannot form a validation bundle")
    bundle = {
        "bundle_id": bundle_id,
        "release_digest": release_digest,
        "checks": checks,
        "waivers": [],
        "review_status": "passed; M1.8 maintainer decision pending",
    }
    run_record = {
        "run_id": f"{bundle_id}-clean-room",
        "environment_label": environment_label,
        "executed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "release_id": result.get("release_id"),
        "release_manifest_digest": release_digest,
        "reader": "expedia_validation.release_reader",
        "reader_inputs": "package directory and embedded schemas only",
        "result": "passed",
        "checks": checks,
    }
    validation_bundle_path.parent.mkdir(parents=True, exist_ok=True)
    validation_bundle_path.write_text(json.dumps(bundle, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    run_record_path.parent.mkdir(parents=True, exist_ok=True)
    run_record_path.write_text(json.dumps(run_record, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Open one Draft package and emit an external M1.7 validation record."""

    parser = argparse.ArgumentParser(description="Independently validate an EXPEDIA Draft package.")
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--validation-bundle", type=Path, required=True)
    parser.add_argument("--run-record", type=Path, required=True)
    parser.add_argument("--bundle-id", required=True)
    parser.add_argument("--environment-label", required=True)
    args = parser.parse_args(argv)
    result = read_release(args.package)
    write_validation_evidence(
        result=result,
        validation_bundle_path=args.validation_bundle,
        run_record_path=args.run_record,
        bundle_id=args.bundle_id,
        environment_label=args.environment_label,
    )
    print(json.dumps(result, sort_keys=True, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
