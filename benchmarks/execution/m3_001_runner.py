"""Mechanical evidence runner for approved M3-001 Version 1.0.

It deliberately contains no retrieval, cursor, filter, or ranking semantics.
Those are imported only from the detached M2 implementation workspace pinned by
the approved evaluation manifest.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Mapping


MANIFEST_RELATIVE = Path("benchmarks/evaluation-manifests/m3-001-v1.1-evaluation-manifest.json")
PROFILE_ID = "m1-generanno-prokaryote-0.5b-assembly-v1"
PROFILE_VERSION = "1.0.0"
ORDERING_VERSION = "score-desc-record-id-asc-v1"


class EvidenceError(RuntimeError):
    """A required M3-001 evidence step cannot be completed."""


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


def _number(value: float) -> str:
    if not math.isfinite(value):
        raise EvidenceError("canonical evidence JSON rejects non-finite floats")
    decimal = Decimal(repr(value))
    if decimal == 0:
        return "0"
    rendered = format(decimal.normalize(), "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def canonical_json(value: object) -> str:
    """Serialize the study's finite logical evidence without whitespace."""

    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _number(value)
    if isinstance(value, Decimal):
        return _number(float(value))
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


def _record_incident(evidence_root: Path, *, command: str, error: Exception) -> None:
    """Retain a harness-observed failure without classifying it as rerunnable."""

    path = evidence_root / "incident-log.json"
    if path.is_file():
        log = _read_json(path)
    else:
        log = {"incidents": [], "study_id": "M3-001"}
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


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceError(f"cannot read JSON evidence: {path}") from error
    if not isinstance(value, dict):
        raise EvidenceError(f"JSON evidence must be an object: {path}")
    return value


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments], check=False, capture_output=True, text=True
    )
    if completed.returncode != 0:
        raise EvidenceError(f"git verification failed: {' '.join(arguments)}")
    return completed.stdout.strip()


def _implementation_imports(root: Path) -> tuple[Any, Any, Any]:
    locations = [
        root / "schemas" / "python",
        root / "validation" / "src",
        root / "query-core" / "src",
    ]
    if not all(location.is_dir() for location in locations):
        raise EvidenceError("implementation workspace lacks required M2 source directories")
    sys.path[:0] = [str(location) for location in locations]
    from expedia_query_core.exact_cosine import ExactCosineQueryCore  # type: ignore[import-not-found]
    from expedia_query_core.query_contracts import canonicalize_query_request_json  # type: ignore[import-not-found]
    from expedia_query_core.verified_release import open_verified_release  # type: ignore[import-not-found]

    module_path = Path(sys.modules["expedia_query_core.exact_cosine"].__file__).resolve()
    if root.resolve() not in module_path.parents:
        raise EvidenceError("Query Core was not imported from the frozen implementation workspace")
    return ExactCosineQueryCore, canonicalize_query_request_json, open_verified_release


def _manifest(study_root: Path) -> dict[str, Any]:
    return _read_json(study_root / MANIFEST_RELATIVE)


def _environment_identity() -> str:
    architecture = platform.machine().upper()
    if architecture == "AMD64":
        architecture = "X64"
    return f"Microsoft {platform.system()} {platform.version()}, {architecture}"


def verify_environment(*, study_root: Path, implementation_root: Path, evidence_root: Path) -> None:
    manifest = _manifest(study_root)
    implementation = manifest["implementation"]
    environment = manifest["execution_environment"]
    if not isinstance(implementation, dict) or not isinstance(environment, dict):
        raise EvidenceError("evaluation manifest implementation/environment is invalid")
    required_commit = implementation["required_commit"]
    if not isinstance(required_commit, str) or _git(implementation_root, "rev-parse", "HEAD") != required_commit:
        raise EvidenceError("implementation workspace is not at the approved commit")
    if _git(implementation_root, "status", "--porcelain"):
        raise EvidenceError("implementation workspace is not clean")
    checks = {
        "repository_commit": required_commit,
        "working_tree": "clean",
        "environment_id": environment["id"],
        "operating_system": _environment_identity(),
        "python_executable": str(Path(sys.executable).resolve()),
        "python_executable_digest": _sha256_file(Path(sys.executable)),
        "runner_digest": _sha256_file(Path(__file__)),
        "dependency_manifest_digest": _sha256_file(implementation_root / "pyproject.toml"),
        "dependency_lock_digest": _sha256_file(implementation_root / "uv.lock"),
    }
    expected = {
        "environment_id": environment["id"],
        "operating_system": environment["operating_system"],
        "python_executable_digest": environment["python_executable_digest"],
        "dependency_manifest_digest": environment["dependency_manifest_digest"],
        "dependency_lock_digest": environment["dependency_lock_digest"],
    }
    if any(checks[key] != value for key, value in expected.items()):
        raise EvidenceError("active execution-environment verification did not match the approved manifest")
    preregistration = study_root / manifest["preregistration"]["path"]
    lock = {
        "environment": checks,
        "evaluation_manifest_digest": _sha256_file(study_root / MANIFEST_RELATIVE),
        "execution_started_at": _utc_now(),
        "lock_id": "m3-001-evaluation-lock-v1",
        "preregistration_digest": _sha256_file(preregistration),
        "profile_digest": manifest["profile"]["profile_digest"],
        "release_digest": manifest["atlas_release"]["release_digest"],
        "vector_shard_digest": manifest["profile"]["vector_shard_digest"],
    }
    _write_json(evidence_root / "environment.json", checks)
    _write_json(evidence_root / "evaluation-lock.json", lock)
    if not (evidence_root / "incident-log.json").exists():
        _write_json(evidence_root / "incident-log.json", {"incidents": [], "study_id": "M3-001"})


def verify_release(*, study_root: Path, implementation_root: Path, release_package: Path, evidence_root: Path) -> None:
    manifest = _manifest(study_root)
    _, _, open_verified_release = _implementation_imports(implementation_root)
    release = open_verified_release(release_package)
    profile = release.embedding_profile(PROFILE_ID)
    shard = release.vector_shard(PROFILE_ID)
    records = release.read_table("records/genome-record-versions.jsonl")
    observed = {
        "canonical_record_count": len(records),
        "profile_digest": profile.digest,
        "profile_id": profile.profile_id,
        "profile_version": profile.version,
        "release_digest": release.release_manifest_digest,
        "release_id": release.release_id,
        "vector_shard_digest": shard.digest,
    }
    expected = {
        "canonical_record_count": 12,
        "profile_digest": manifest["profile"]["profile_digest"],
        "profile_id": manifest["profile"]["profile_id"],
        "profile_version": manifest["profile"]["profile_version"],
        "release_digest": manifest["atlas_release"]["release_digest"],
        "release_id": manifest["atlas_release"]["release_id"],
        "vector_shard_digest": manifest["profile"]["vector_shard_digest"],
    }
    if observed != expected:
        raise EvidenceError("verified release does not match the approved M3-001 manifest")
    _write_json(evidence_root / "release-verification.json", observed)


def _request(release: Any, record_id: str, *, limit: int, cursor: str | None, profile_version: str = PROFILE_VERSION) -> str:
    return json.dumps(
        {
            "schema_version": "query-request/0.1.0",
            "release_selector": {"release_id": release.release_id, "release_digest": release.release_manifest_digest},
            "operation": "similarity",
            "profile_selector": {"profile_id": PROFILE_ID, "profile_version": profile_version},
            "similarity": {"query_record_id": record_id, "metric": "cosine", "mode": "exact"},
            "pagination": {"limit": limit, "cursor": cursor, "ordering_version": ORDERING_VERSION},
        },
        separators=(",", ":"),
    )


def _execute(core: Any, canonicalizer: Any, *, request_id: str, family: str, record_id: str, raw: str) -> dict[str, object]:
    canonical = canonicalizer(raw)
    result = dict(core.execute(canonical.canonical_json))
    result_json = canonical_json(result)
    return {
        "canonical_request": canonical.canonical_json,
        "canonical_request_digest": canonical.digest,
        "canonical_result": result_json,
        "family": family,
        "record_id": record_id,
        "request_id": request_id,
        "result_digest": _sha256_bytes(result_json.encode("utf-8")),
        "result": result,
    }


def run_replicate(*, study_root: Path, implementation_root: Path, release_package: Path, evidence_root: Path, replicate: int) -> None:
    if replicate not in {1, 2, 3}:
        raise EvidenceError("M3-001 requires replicate 1, 2, or 3")
    if not (evidence_root / "environment.json").is_file() or not (evidence_root / "release-verification.json").is_file():
        raise EvidenceError("environment and release verification must precede every replicate")
    destination = evidence_root / f"replicate-{replicate}"
    try:
        destination.mkdir()
    except FileExistsError as error:
        raise EvidenceError(f"replicate evidence already exists: {destination}") from error
    ExactCosineQueryCore, canonicalizer, open_verified_release = _implementation_imports(implementation_root)
    release = open_verified_release(release_package)
    core = ExactCosineQueryCore(release)
    records = release.read_table("records/genome-record-versions.jsonl")
    ids = [row.get("record_id") for row in records]
    if len(ids) != 12 or not all(isinstance(record_id, str) for record_id in ids) or len(set(ids)) != 12:
        raise EvidenceError("verified release has no approved twelve-record corpus")
    entries: list[dict[str, object]] = []
    for record_id in ids:
        assert isinstance(record_id, str)
        entries.append(_execute(core, canonicalizer, request_id=f"full:{record_id}", family="full", record_id=record_id, raw=_request(release, record_id, limit=12, cursor=None)))
        page = 1
        cursor: str | None = None
        while True:
            entry = _execute(core, canonicalizer, request_id=f"paginated:{record_id}:{page}", family="paginated", record_id=record_id, raw=_request(release, record_id, limit=2, cursor=cursor))
            entries.append(entry)
            result = entry["result"]
            assert isinstance(result, dict)
            cursor = result.get("next_cursor") if result.get("outcome") == "success" else None
            if cursor is None:
                break
            if not isinstance(cursor, str) or page >= 6:
                raise EvidenceError("pagination did not terminate within the approved corpus")
            page += 1
        entries.append(_execute(core, canonicalizer, request_id=f"invalid-cursor:{record_id}", family="invalid-cursor", record_id=record_id, raw=_request(release, record_id, limit=12, cursor="invalid-m3-001-cursor")))
        entries.append(_execute(core, canonicalizer, request_id=f"profile-mismatch:{record_id}", family="profile-mismatch", record_id=record_id, raw=_request(release, record_id, limit=12, cursor=None, profile_version="0.0.0")))
    request_rows = [{key: entry[key] for key in ("request_id", "family", "record_id", "canonical_request", "canonical_request_digest")} for entry in entries]
    response_rows = [{key: entry[key] for key in ("request_id", "canonical_result", "result_digest")} for entry in entries]
    cursor_rows = [{"request_id": entry["request_id"], "next_cursor": entry["result"].get("next_cursor") if isinstance(entry["result"], dict) else None} for entry in entries]
    warning_rows = [{"request_id": entry["request_id"], "warnings": entry["result"].get("warnings", []) if isinstance(entry["result"], dict) else []} for entry in entries]
    failure_rows = [{"request_id": entry["request_id"], "error": entry["result"].get("error")} for entry in entries if isinstance(entry["result"], dict) and entry["result"].get("outcome") == "error"]
    _write_jsonl(destination / "canonical-requests.jsonl", request_rows)
    _write_jsonl(destination / "canonical-responses.jsonl", response_rows)
    _write_jsonl(destination / "cursors.jsonl", cursor_rows)
    _write_jsonl(destination / "warnings.jsonl", warning_rows)
    _write_jsonl(destination / "typed-failures.jsonl", failure_rows)
    _write_json(destination / "replicate-provenance.json", {"completed_at": _utc_now(), "python_executable_digest": _sha256_file(Path(sys.executable)), "replicate": replicate})
    _write_json(destination / "digests.json", {path.name: _sha256_file(path) for path in sorted(destination.iterdir()) if path.is_file()})


def _jsonl(path: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        value = json.loads(line)
        if not isinstance(value, dict) or not isinstance(value.get("request_id"), str) or value["request_id"] in result:
            raise EvidenceError(f"invalid retained JSONL evidence: {path}")
        result[value["request_id"]] = value
    return result


def _diagnostic(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    if left == right:
        return []
    fields: list[tuple[str, object, object]] = [
        ("outcome_type", left.get("outcome"), right.get("outcome")),
        ("typed_error_code_and_stage", left.get("error"), right.get("error")),
        ("ordered_record_ids", [row.get("record_id") for row in left.get("rows", [])], [row.get("record_id") for row in right.get("rows", [])]),
        ("decoded_scores", [row.get("score") for row in left.get("rows", [])], [row.get("score") for row in right.get("rows", [])]),
        ("provenance", left.get("provenance"), right.get("provenance")),
        ("warnings_in_returned_order", left.get("warnings"), right.get("warnings")),
        ("opaque_cursor_payloads_and_continuation_reconstruction", left.get("next_cursor"), right.get("next_cursor")),
    ]
    return [name for name, first, second in fields if first != second]


def compare_replicates(*, evidence_root: Path) -> None:
    requests = [_jsonl(evidence_root / f"replicate-{number}" / "canonical-requests.jsonl") for number in (1, 2, 3)]
    responses = [_jsonl(evidence_root / f"replicate-{number}" / "canonical-responses.jsonl") for number in (1, 2, 3)]
    if set(requests[0]) != set(requests[1]) or set(requests[0]) != set(requests[2]):
        raise EvidenceError("replicate request identities differ")
    observations: list[dict[str, object]] = []
    for request_id in sorted(requests[0]):
        request_digests = [request[request_id]["canonical_request_digest"] for request in requests]
        result_digests = [response[request_id]["result_digest"] for response in responses]
        diagnostics: dict[str, list[str]] = {}
        first = json.loads(responses[0][request_id]["canonical_result"])
        for label, response in zip(("replicate-2", "replicate-3"), responses[1:], strict=True):
            other = json.loads(response[request_id]["canonical_result"])
            diagnostics[label] = _diagnostic(first, other) if responses[0][request_id]["result_digest"] != response[request_id]["result_digest"] else []
        observations.append({"canonical_request_digests": request_digests, "diagnostic_fields": diagnostics, "request_id": request_id, "result_digests": result_digests})
    _write_json(evidence_root / "comparison.json", {"comparison_algorithm": "canonical-json-sha256-first-v1", "observations": observations})
    _write_new(evidence_root / "comparison.md", ("# M3-001 replicate comparison observations\n\n" + "\n".join(f"- `{item['request_id']}`" for item in observations) + "\n").encode("utf-8"))
    files = [path for path in sorted(evidence_root.rglob("*")) if path.is_file() and path.name != "digests.json"]
    _write_json(evidence_root / "digests.json", {path.relative_to(evidence_root).as_posix(): _sha256_file(path) for path in files})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", type=Path, required=True)
    parser.add_argument("--implementation-root", type=Path, required=True)
    parser.add_argument("--release-package", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("verify-environment")
    subparsers.add_parser("verify-release")
    replicate = subparsers.add_parser("replicate")
    replicate.add_argument("--replicate", type=int, required=True)
    subparsers.add_parser("compare")
    args = parser.parse_args()
    try:
        if args.command == "verify-environment":
            verify_environment(study_root=args.study_root, implementation_root=args.implementation_root, evidence_root=args.evidence_root)
        elif args.command == "verify-release":
            verify_release(study_root=args.study_root, implementation_root=args.implementation_root, release_package=args.release_package, evidence_root=args.evidence_root)
        elif args.command == "replicate":
            run_replicate(study_root=args.study_root, implementation_root=args.implementation_root, release_package=args.release_package, evidence_root=args.evidence_root, replicate=args.replicate)
        else:
            compare_replicates(evidence_root=args.evidence_root)
    except EvidenceError as error:
        _record_incident(args.evidence_root, command=args.command, error=error)
        raise SystemExit(f"M3-001 {args.command} failed; retained incident: {error}") from error


if __name__ == "__main__":
    main()
