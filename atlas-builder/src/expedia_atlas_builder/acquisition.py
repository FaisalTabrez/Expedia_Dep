"""Manifest-bound NCBI Datasets acquisition for EXPEDIA M1.3.

This module deliberately stops at source acquisition and accounting. It neither
canonicalizes sequences nor creates atlas records, which are M1.4 work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable
import zipfile


class AcquisitionError(RuntimeError):
    """Raised when an acquisition input or package cannot be accounted for."""


@dataclass(frozen=True, slots=True)
class AssemblyInput:
    """One versioned source assembly declared by the immutable M1 inventory."""

    accession: str
    domain: str
    organism_name: str


@dataclass(frozen=True, slots=True)
class AcquisitionAccount:
    """Package accounting outcome; every observed or declared item is retained."""

    registered: tuple[str, ...]
    missing: tuple[str, ...]
    unexpected: tuple[str, ...]
    duplicate_observations: tuple[str, ...]

    @property
    def is_complete(self) -> bool:
        return not self.missing and not self.unexpected and not self.duplicate_observations


def load_inventory(path: Path) -> tuple[AssemblyInput, ...]:
    """Load and structurally validate the committed versioned-accession inventory."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AcquisitionError(f"cannot read inventory {path}") from error
    assemblies = payload.get("assemblies")
    if not isinstance(assemblies, list) or not assemblies:
        raise AcquisitionError("inventory.assemblies must be a non-empty array")
    inputs: list[AssemblyInput] = []
    for item in assemblies:
        if not isinstance(item, dict):
            raise AcquisitionError("inventory assemblies must be objects")
        try:
            assembly = AssemblyInput(
                accession=_require_string(item.get("accession"), "assembly.accession"),
                domain=_require_string(item.get("domain"), "assembly.domain"),
                organism_name=_require_string(item.get("organism_name"), "assembly.organism_name"),
            )
        except AcquisitionError:
            raise
        inputs.append(assembly)
    accessions = [assembly.accession for assembly in inputs]
    if len(accessions) != len(set(accessions)):
        raise AcquisitionError("inventory contains duplicate accessions")
    return tuple(inputs)


def write_accession_list(inventory: Iterable[AssemblyInput], path: Path) -> None:
    """Write exactly the committed accessions, one versioned value per LF line."""

    accessions = [assembly.accession for assembly in inventory]
    if not accessions:
        raise AcquisitionError("cannot write an empty accession list")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(accessions) + "\n", encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it into memory."""

    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as error:
        raise AcquisitionError(f"cannot hash {path}") from error
    return f"sha256:{digest.hexdigest()}"


def account_dataset_archive(archive_path: Path, inventory: Iterable[AssemblyInput]) -> AcquisitionAccount:
    """Read the NCBI assembly report and account for every declared accession."""

    expected = tuple(inventory)
    expected_accessions = {assembly.accession for assembly in expected}
    if len(expected_accessions) != len(expected):
        raise AcquisitionError("inventory contains duplicate accessions")
    try:
        with zipfile.ZipFile(archive_path) as archive:
            report_name = _find_archive_member(archive, "assembly_data_report.jsonl")
            report = archive.read(report_name).decode("utf-8")
    except (OSError, zipfile.BadZipFile, KeyError, UnicodeDecodeError) as error:
        raise AcquisitionError(f"cannot read an NCBI assembly report from {archive_path}") from error

    observations: list[str] = []
    for line in report.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise AcquisitionError("assembly data report contains invalid JSONL") from error
        if not isinstance(row, dict):
            raise AcquisitionError("assembly data report rows must be objects")
        accession = row.get("accession") or row.get("current_accession")
        observations.append(_require_string(accession, "assembly report accession"))

    counts = {accession: observations.count(accession) for accession in set(observations)}
    duplicate_observations = tuple(sorted(accession for accession, count in counts.items() if count > 1))
    observed = set(observations)
    return AcquisitionAccount(
        registered=tuple(sorted(expected_accessions & observed)),
        missing=tuple(sorted(expected_accessions - observed)),
        unexpected=tuple(sorted(observed - expected_accessions)),
        duplicate_observations=duplicate_observations,
    )


def dataset_catalogue_digest(archive_path: Path) -> str:
    """Validate and digest the NCBI package catalogue inside an acquired archive."""

    try:
        with zipfile.ZipFile(archive_path) as archive:
            catalogue_name = _find_archive_member(archive, "dataset_catalog.json")
            catalogue = archive.read(catalogue_name)
        parsed = json.loads(catalogue.decode("utf-8"))
    except (OSError, zipfile.BadZipFile, KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AcquisitionError(f"cannot read an NCBI dataset catalogue from {archive_path}") from error
    if not isinstance(parsed, dict):
        raise AcquisitionError("dataset catalogue must be a JSON object")
    return f"sha256:{hashlib.sha256(catalogue).hexdigest()}"


def acquire_ncbi_datasets(
    *,
    inventory_path: Path,
    datasets_executable: Path,
    workspace: Path,
    expected_cli_version: str,
    retrieved_at: datetime | None = None,
) -> dict[str, object]:
    """Acquire one inventory package and write an explicit M1.3 stage envelope.

    The caller must supply the M1.1-pinned executable. Existing archives are
    rejected rather than silently reused, preserving declared stage inputs.
    """

    inventory = load_inventory(inventory_path)
    workspace.mkdir(parents=True, exist_ok=True)
    archive_path = workspace / "ncbi-datasets-m1-source.zip"
    accessions_path = workspace / "versioned-accessions.txt"
    stage_path = workspace / "acquisition-stage-envelope.json"
    provenance_path = workspace / "source-provenance.json"
    if archive_path.exists():
        raise AcquisitionError(f"refusing to overwrite existing archive {archive_path}")

    command = [
        str(datasets_executable),
        "download",
        "genome",
        "accession",
        "--inputfile",
        str(accessions_path),
        "--include",
        "genome,seq-report",
        "--filename",
        str(archive_path),
    ]
    try:
        _verify_cli_version(datasets_executable, expected_cli_version)
        write_accession_list(inventory, accessions_path)
        subprocess.run(command, check=True, capture_output=True, text=True)
        account = account_dataset_archive(archive_path, inventory)
        catalogue_digest = dataset_catalogue_digest(archive_path)
        outcome = "succeeded" if account.is_complete else "quarantined"
        verification: dict[str, Any] = {
            "expected_accession_count": len(inventory),
            "registered_accessions": list(account.registered),
            "missing_accessions": list(account.missing),
            "unexpected_accessions": list(account.unexpected),
            "duplicate_observations": list(account.duplicate_observations),
            "archive_digest": sha256_file(archive_path),
            "catalogue_digest": catalogue_digest,
            "retrieved_at": _utc_timestamp(retrieved_at),
        }
        provenance_path.write_text(
            json.dumps(
                {
                    "source_provenance_id": "m1-ncbi-refseq-package-acquisition-v1",
                    "source": "NCBI RefSeq genome package",
                    "source_version": f"NCBI Datasets CLI v{expected_cli_version}",
                    "source_identifier": inventory_path.stem,
                    "acquired_at": verification["retrieved_at"],
                    "acquisition_artifact_digest": verification["archive_digest"],
                    "license_notice": {
                        "notice_reference": "atlas-builder/manifests/m1/m1-source-provenance.json",
                        "scope": "internal M1 reproducibility validation only",
                    },
                },
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except (AcquisitionError, subprocess.CalledProcessError) as error:
        outcome = "failed"
        verification = {"error": str(error), "retrieved_at": _utc_timestamp(retrieved_at)}

    envelope = {
        "stage_id": "acquire",
        "input_artifacts": [{"path": str(inventory_path), "media_type": "application/json"}],
        "output_artifacts": (
            [
                {"path": str(archive_path), "media_type": "application/zip", "digest": verification["archive_digest"]},
                {"path": str(provenance_path), "media_type": "application/json", "digest": sha256_file(provenance_path)},
            ]
            if outcome != "failed"
            else []
        ),
        "exclusions": [],
        "outcome": outcome,
        "verification": verification,
        "recovery": {"retry_requires": "a new empty acquisition workspace"},
    }
    stage_path.write_text(json.dumps(envelope, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return envelope


def _find_archive_member(archive: zipfile.ZipFile, filename: str) -> str:
    matches = [member for member in archive.namelist() if member.endswith(f"/{filename}") or member == filename]
    if len(matches) != 1:
        raise AcquisitionError(f"archive must contain exactly one {filename}")
    return matches[0]


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AcquisitionError(f"{field} must be a non-empty string")
    return value


def _verify_cli_version(executable: Path, expected_version: str) -> None:
    if not executable.is_file():
        raise AcquisitionError(f"datasets executable does not exist: {executable}")
    try:
        result = subprocess.run([str(executable), "version"], check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise AcquisitionError("cannot execute NCBI Datasets CLI") from error
    if expected_version not in result.stdout:
        raise AcquisitionError(f"NCBI Datasets CLI version does not contain {expected_version}")


def _utc_timestamp(value: datetime | None) -> str:
    timestamp = value or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise AcquisitionError("retrieved_at must include a UTC offset")
    return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    """Run the M1.3 acquisition stage from an explicit command-line contract."""

    parser = argparse.ArgumentParser(description="Acquire and account for the EXPEDIA M1 RefSeq inventory.")
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--datasets-executable", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--expected-cli-version", required=True)
    args = parser.parse_args(argv)
    envelope = acquire_ncbi_datasets(
        inventory_path=args.inventory,
        datasets_executable=args.datasets_executable,
        workspace=args.workspace,
        expected_cli_version=args.expected_cli_version,
    )
    print(json.dumps(envelope, sort_keys=True))
    return 0 if envelope["outcome"] == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
