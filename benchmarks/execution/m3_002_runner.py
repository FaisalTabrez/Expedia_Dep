"""Mechanical evidence runner for the approved M3-002 exactness study.

This runner records raw observations only.  It never decides PASS/FAIL,
interprets a comparison, retries a mismatch, or changes the frozen Query Core,
Release Reader, reference oracle, contracts, or study artifacts.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from typing import Any, Mapping


MANIFEST_RELATIVE = Path("benchmarks/evaluation-manifests/m3-002-v1-evaluation-manifest.json")
RECORD_TABLE_PATH = "records/genome-record-versions.jsonl"
ORDERING_VERSION = "score-desc-record-id-asc-v1"


class EvidenceError(RuntimeError):
    """A mandatory M3-002 evidence step cannot be completed."""


def _sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _finite_number(value: float) -> str:
    if not math.isfinite(value):
        raise EvidenceError("canonical evidence JSON rejects non-finite floats")
    decimal = Decimal(repr(value))
    if decimal == 0:
        return "0"
    rendered = format(decimal.normalize(), "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def canonical_json(value: object) -> str:
    """Serialize the approved finite comparison object without whitespace."""

    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _finite_number(value)
    if isinstance(value, Decimal):
        return _finite_number(float(value))
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(canonical_json(item) for item in value) + "]"
    if isinstance(value, Mapping):
        return "{" + ",".join(
            canonical_json(str(key)) + ":" + canonical_json(value[key]) for key in sorted(value)
        ) + "}"
    raise EvidenceError(f"unsupported evidence value: {type(value).__name__}")


def _write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError as error:
        raise EvidenceError(f"refusing to overwrite retained evidence: {path}") from error


def _write_json(path: Path, value: Mapping[str, object] | list[object]) -> None:
    _write_new(path, canonical_json(value).encode("utf-8"))


def _write_jsonl(path: Path, rows: list[Mapping[str, object]]) -> None:
    _write_new(path, ("\n".join(canonical_json(row) for row in rows) + "\n").encode("utf-8"))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceError(f"cannot read JSON: {path}") from error
    if not isinstance(value, dict):
        raise EvidenceError(f"JSON must be an object: {path}")
    return value


def _manifest(study_root: Path) -> dict[str, Any]:
    manifest = _read_json(study_root / MANIFEST_RELATIVE)
    if manifest.get("approval_status") != "accepted-immutable":
        raise EvidenceError("M3-002 evaluation manifest is not accepted and immutable")
    return manifest


def resolve_git_executable() -> Path:
    """Resolve Git explicitly for the approved runner environment amendment."""

    configured = os.environ.get("EXPEDIA_GIT_EXECUTABLE")
    candidate = Path(configured) if configured else (Path(found) if (found := shutil.which("git")) else None)
    if candidate is None or not candidate.is_file():
        raise EvidenceError("Git executable is unavailable; set EXPEDIA_GIT_EXECUTABLE to the approved executable")
    return candidate.resolve()


def _git(root: Path, *arguments: str) -> str:
    executable = resolve_git_executable()
    completed = subprocess.run(
        [str(executable), "-C", str(root), *arguments], check=False, capture_output=True, text=True
    )
    if completed.returncode != 0:
        raise EvidenceError(f"git verification failed: {' '.join(arguments)}")
    return completed.stdout.strip()


def _implementation_imports(implementation_root: Path) -> tuple[Any, Any, Any]:
    locations = [
        implementation_root / "schemas" / "python",
        implementation_root / "validation" / "src",
        implementation_root / "query-core" / "src",
    ]
    if not all(location.is_dir() for location in locations):
        raise EvidenceError("implementation workspace lacks required M2 source directories")
    sys.path[:0] = [str(location) for location in locations]
    from expedia_query_core.exact_cosine import ExactCosineQueryCore  # type: ignore[import-not-found]
    from expedia_query_core.query_contracts import canonicalize_query_request_json  # type: ignore[import-not-found]
    from expedia_query_core.verified_release import open_verified_release  # type: ignore[import-not-found]

    module_path = Path(sys.modules["expedia_query_core.exact_cosine"].__file__).resolve()
    if implementation_root.resolve() not in module_path.parents:
        raise EvidenceError("Query Core was not imported from the frozen implementation workspace")
    return ExactCosineQueryCore, canonicalize_query_request_json, open_verified_release


def _oracle_import(study_root: Path, manifest: Mapping[str, Any]) -> tuple[Any, Any]:
    definition = manifest.get("reference_implementation")
    if not isinstance(definition, dict):
        raise EvidenceError("evaluation manifest reference implementation is invalid")
    source = study_root / definition["source_path"]
    if not source.is_file() or _sha256_file(source) != definition["source_digest"]:
        raise EvidenceError("oracle source does not match the immutable evaluation manifest")
    source_directory = str(source.parent)
    if source_directory not in sys.path:
        sys.path.insert(0, source_directory)
    from m3_002_float32_cosine import ReferenceBinding, load_reference_release  # type: ignore[import-not-found]

    module_path = Path(sys.modules["m3_002_float32_cosine"].__file__).resolve()
    if module_path != source.resolve():
        raise EvidenceError("oracle was not imported from the manifest-addressed source")
    return ReferenceBinding, load_reference_release


def _environment_identity() -> str:
    architecture = platform.machine().upper()
    if architecture == "AMD64":
        architecture = "X64"
    return f"Microsoft {platform.system()} {platform.version()}, {architecture}"


def _record_incident(evidence_root: Path, *, command: str, error: Exception) -> None:
    path = evidence_root / "incident-log.json"
    if path.is_file():
        log = _read_json(path)
    else:
        log = {"incidents": [], "study_id": "M3-002"}
    incidents = log.get("incidents")
    if not isinstance(incidents, list):
        raise EvidenceError("incident log is invalid")
    incidents.append(
        {
            "command": command,
            "error": str(error),
            "observed_at": _utc_now(),
            "rerun_permitted": False,
            "type": "harness-observed-failure",
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(log).encode("utf-8"))


def _initialize_incident_log(evidence_root: Path) -> None:
    """Create the log once while preserving any earlier retained incident."""

    path = evidence_root / "incident-log.json"
    if path.is_file():
        log = _read_json(path)
        if log.get("study_id") != "M3-002" or not isinstance(log.get("incidents"), list):
            raise EvidenceError("existing M3-002 incident log is invalid")
        return
    _write_json(path, {"incidents": [], "study_id": "M3-002"})


def verify_environment(*, study_root: Path, implementation_root: Path, evidence_root: Path) -> None:
    manifest = _manifest(study_root)
    implementation = manifest["implementation"]
    environment = manifest["execution_environment"]
    if not isinstance(implementation, dict) or not isinstance(environment, dict):
        raise EvidenceError("evaluation manifest implementation/environment is invalid")
    required_commit = implementation.get("required_commit")
    if not isinstance(required_commit, str) or _git(implementation_root, "rev-parse", "HEAD") != required_commit:
        raise EvidenceError("implementation workspace is not at the frozen M2 commit")
    if _git(implementation_root, "status", "--porcelain"):
        raise EvidenceError("implementation workspace is not clean")
    git_executable = resolve_git_executable()
    checks = {
        "dependency_lock_digest": _sha256_file(implementation_root / "uv.lock"),
        "dependency_manifest_digest": _sha256_file(implementation_root / "pyproject.toml"),
        "environment_id": environment.get("id"),
        "git_executable": str(git_executable),
        "git_executable_digest": _sha256_file(git_executable),
        "operating_system": _environment_identity(),
        "python_executable": str(Path(sys.executable).resolve()),
        "python_executable_digest": _sha256_file(Path(sys.executable)),
        "repository_commit": required_commit,
        "runner_digest": _sha256_file(Path(__file__)),
        "working_tree": "clean",
    }
    expected = {
        "dependency_lock_digest": environment.get("dependency_lock_digest"),
        "dependency_manifest_digest": environment.get("dependency_manifest_digest"),
        "environment_id": environment.get("id"),
        "python_executable_digest": environment.get("python_executable_digest"),
    }
    if any(checks[key] != value for key, value in expected.items()):
        raise EvidenceError("active execution environment does not match the immutable evaluation manifest")
    lock = {
        "environment": checks,
        "evaluation_manifest_digest": _sha256_file(study_root / MANIFEST_RELATIVE),
        "execution_started_at": _utc_now(),
        "lock_id": "m3-002-evaluation-lock-v1",
        "preregistration_digest": manifest["preregistration"]["digest"],
        "profile_digest": manifest["release"]["profile_digest"],
        "release_digest": manifest["release"]["release_digest"],
        "vector_shard_digest": manifest["release"]["vector_shard_digest"],
    }
    _write_json(evidence_root / "environment.json", checks)
    _write_json(evidence_root / "evaluation-lock.json", lock)
    _initialize_incident_log(evidence_root)


def _binding(manifest: Mapping[str, Any], reference_binding: Any) -> Any:
    release = manifest["release"]
    return reference_binding(
        release_id=release["release_id"],
        release_digest=release["release_digest"],
        profile_id=release["profile_id"],
        profile_version=release["profile_version"],
        profile_digest=release["profile_digest"],
        vector_shard_digest=release["vector_shard_digest"],
        expected_record_count=release["expected_record_count"],
    )


def verify_release(*, study_root: Path, implementation_root: Path, release_package: Path, evidence_root: Path) -> None:
    manifest = _manifest(study_root)
    _, _, open_verified_release = _implementation_imports(implementation_root)
    ReferenceBinding, load_reference_release = _oracle_import(study_root, manifest)
    release = open_verified_release(release_package)
    oracle_release = load_reference_release(release_package, binding=_binding(manifest, ReferenceBinding))
    profile_id = manifest["release"]["profile_id"]
    profile = release.embedding_profile(profile_id)
    shard = release.vector_shard(profile_id)
    records = release.read_table(RECORD_TABLE_PATH)
    observed = {
        "canonical_record_count": len(records),
        "oracle_record_count": len(oracle_release.record_ids),
        "profile_digest": profile.digest,
        "profile_id": profile.profile_id,
        "profile_version": profile.version,
        "release_digest": release.release_manifest_digest,
        "release_id": release.release_id,
        "vector_shard_digest": shard.digest,
    }
    expected = {
        "canonical_record_count": manifest["release"]["expected_record_count"],
        "oracle_record_count": manifest["release"]["expected_record_count"],
        "profile_digest": manifest["release"]["profile_digest"],
        "profile_id": manifest["release"]["profile_id"],
        "profile_version": manifest["release"]["profile_version"],
        "release_digest": manifest["release"]["release_digest"],
        "release_id": manifest["release"]["release_id"],
        "vector_shard_digest": manifest["release"]["vector_shard_digest"],
    }
    if observed != expected:
        raise EvidenceError("verified M1 Draft package does not match the immutable evaluation manifest")
    _write_json(evidence_root / "release-verification.json", observed)


def _request(release: Any, *, record_id: str, profile_id: str, profile_version: str) -> str:
    return json.dumps(
        {
            "schema_version": "query-request/0.1.0",
            "release_selector": {"release_id": release.release_id, "release_digest": release.release_digest},
            "operation": "similarity",
            "profile_selector": {"profile_id": profile_id, "profile_version": profile_version},
            "similarity": {"query_record_id": record_id, "metric": "cosine", "mode": "exact"},
            "pagination": {"limit": 12, "cursor": None, "ordering_version": ORDERING_VERSION},
        },
        separators=(",", ":"),
    )


def query_core_projection(*, result: Mapping[str, object], canonical_request_digest: str) -> dict[str, object]:
    """Project only the preregistered logical comparison fields from QueryResult."""

    if result.get("outcome") != "success":
        raise EvidenceError("a preregistered M3-002 request did not produce QueryResult success")
    rows = result.get("rows")
    context = result.get("context")
    provenance = result.get("provenance")
    if not isinstance(rows, list) or not isinstance(context, Mapping) or not isinstance(provenance, Mapping):
        raise EvidenceError("QueryResult cannot be projected into the preregistered comparison object")
    ids: list[str] = []
    scores: list[float] = []
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("record_id"), str) or not isinstance(row.get("score"), float):
            raise EvidenceError("QueryResult row is incompatible with the M3-002 comparison projection")
        ids.append(row["record_id"])
        scores.append(row["score"])
    fields = {
        "release_digest": provenance.get("release_digest"),
        "profile_id": context.get("profile_id"),
        "profile_version": provenance.get("profile_version"),
        "profile_digest": provenance.get("profile_digest"),
        "vector_shard_digest": provenance.get("vector_shard_digest"),
        "ordering_version": context.get("ordering_version"),
    }
    if not all(isinstance(value, str) for value in fields.values()):
        raise EvidenceError("QueryResult provenance is incomplete for M3-002")
    return {
        "canonical_request_digest": canonical_request_digest,
        "ordered_record_ids": ids,
        "decoded_float32_scores": scores,
        "provenance": fields,
    }


def _diagnostic_fields(left: Mapping[str, object], right: Mapping[str, object]) -> list[str]:
    fields = (
        "ordered_record_ids",
        "decoded_float32_scores",
        "provenance",
    )
    return [field for field in fields if left.get(field) != right.get(field)]


def execute(*, study_root: Path, implementation_root: Path, release_package: Path, evidence_root: Path) -> None:
    if not (evidence_root / "environment.json").is_file() or not (evidence_root / "release-verification.json").is_file():
        raise EvidenceError("environment and release verification must precede M3-002 execution")
    manifest = _manifest(study_root)
    ExactCosineQueryCore, canonicalize_query_request_json, open_verified_release = _implementation_imports(implementation_root)
    ReferenceBinding, load_reference_release = _oracle_import(study_root, manifest)
    release = open_verified_release(release_package)
    oracle = load_reference_release(release_package, binding=_binding(manifest, ReferenceBinding))
    records = release.read_table(RECORD_TABLE_PATH)
    record_ids = [record.get("record_id") for record in records]
    if (
        len(record_ids) != manifest["release"]["expected_record_count"]
        or not all(isinstance(record_id, str) for record_id in record_ids)
        or len(set(record_ids)) != len(record_ids)
        or tuple(record_ids) != oracle.record_ids
    ):
        raise EvidenceError("verified Query Core and oracle inputs do not have the preregistered record order")

    core = ExactCosineQueryCore(release)
    raw_core_rows: list[dict[str, object]] = []
    core_projection_rows: list[dict[str, object]] = []
    oracle_rows: list[dict[str, object]] = []
    request_rows: list[dict[str, object]] = []
    comparison_rows: list[dict[str, object]] = []
    for record_id in record_ids:
        assert isinstance(record_id, str)
        request = canonicalize_query_request_json(
            _request(
                release,
                record_id=record_id,
                profile_id=manifest["release"]["profile_id"],
                profile_version=manifest["release"]["profile_version"],
            )
        )
        raw_result = dict(core.execute(request.canonical_json))
        core_projection = query_core_projection(
            result=raw_result,
            canonical_request_digest=request.digest,
        )
        oracle_projection = oracle.comparison_object(
            query_record_id=record_id,
            canonical_request_digest=request.digest,
        )
        core_canonical = canonical_json(core_projection)
        oracle_canonical = canonical_json(oracle_projection)
        core_digest = _sha256_bytes(core_canonical.encode("utf-8"))
        oracle_digest = _sha256_bytes(oracle_canonical.encode("utf-8"))
        request_rows.append(
            {
                "canonical_request": request.canonical_json,
                "canonical_request_digest": request.digest,
                "query_record_id": record_id,
            }
        )
        raw_core_rows.append(
            {
                "canonical_result": canonical_json(raw_result),
                "canonical_request_digest": request.digest,
                "query_record_id": record_id,
                "result": raw_result,
            }
        )
        core_projection_rows.append(
            {
                "canonical_json": core_canonical,
                "canonical_request_digest": request.digest,
                "digest": core_digest,
                "query_record_id": record_id,
                "projection": core_projection,
            }
        )
        oracle_rows.append(
            {
                "canonical_json": oracle_canonical,
                "canonical_request_digest": request.digest,
                "digest": oracle_digest,
                "query_record_id": record_id,
                "projection": oracle_projection,
            }
        )
        comparison_rows.append(
            {
                "canonical_request_digest": request.digest,
                "diagnostic_fields": _diagnostic_fields(core_projection, oracle_projection)
                if core_digest != oracle_digest
                else [],
                "oracle_digest": oracle_digest,
                "query_core_digest": core_digest,
                "query_record_id": record_id,
            }
        )

    _write_jsonl(evidence_root / "canonical-requests.jsonl", request_rows)
    _write_jsonl(evidence_root / "query-core-raw-results.jsonl", raw_core_rows)
    _write_jsonl(evidence_root / "query-core-projections.jsonl", core_projection_rows)
    _write_jsonl(evidence_root / "reference-projections.jsonl", oracle_rows)
    _write_json(evidence_root / "comparison.json", {"observations": comparison_rows, "study_id": "M3-002"})
    _write_json(
        evidence_root / "analysis-location.json",
        {"path": "validation/evidence/m3-002/M3-002-analysis.md", "status": "pending M3-002.7"},
    )
    artifacts = [
        path
        for path in sorted(evidence_root.rglob("*"))
        if path.is_file() and path.name != "digests.json"
    ]
    _write_json(
        evidence_root / "digests.json",
        {path.relative_to(evidence_root).as_posix(): _sha256_file(path) for path in artifacts},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", type=Path, required=True)
    parser.add_argument("--implementation-root", type=Path, required=True)
    parser.add_argument("--release-package", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("verify-environment")
    subparsers.add_parser("verify-release")
    subparsers.add_parser("execute")
    args = parser.parse_args()
    try:
        if args.command == "verify-environment":
            verify_environment(
                study_root=args.study_root,
                implementation_root=args.implementation_root,
                evidence_root=args.evidence_root,
            )
        elif args.command == "verify-release":
            verify_release(
                study_root=args.study_root,
                implementation_root=args.implementation_root,
                release_package=args.release_package,
                evidence_root=args.evidence_root,
            )
        else:
            execute(
                study_root=args.study_root,
                implementation_root=args.implementation_root,
                release_package=args.release_package,
                evidence_root=args.evidence_root,
            )
    except EvidenceError as error:
        _record_incident(args.evidence_root, command=args.command, error=error)
        raise SystemExit(f"M3-002 {args.command} failed; retained incident: {error}") from error


if __name__ == "__main__":
    main()
