"""Deterministic M1.4 assembly canonicalization for versioned RefSeq inputs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable
import zipfile

from .acquisition import AssemblyInput, sha256_file


CANONICALIZATION_ID = "m1-assembly-canonical-v1"
ALLOWED_IUPAC_DNA = frozenset(b"ACGTRYSWKMBDHVN")
ASCII_WHITESPACE = frozenset(b" \t\r\n\f\v")


class CanonicalizationError(ValueError):
    """An input violates the frozen M1 canonicalization contract."""


@dataclass(frozen=True, slots=True)
class CanonicalAssembly:
    accession: str
    canonical_bytes: bytes
    sequence_digest: str

    @property
    def entity_id(self) -> str:
        return f"ncbi-assembly:{self.accession.rsplit('.', 1)[0]}"

    @property
    def record_id(self) -> str:
        return f"ncbi-assembly:{self.accession}:{CANONICALIZATION_ID}"


def canonicalize_assembly(accession: str, fasta: bytes, sequence_report: bytes) -> CanonicalAssembly:
    """Pair, normalize, sort, and hash a single assembly without merging contigs."""

    fasta_records = _parse_fasta(fasta)
    report_accessions = _parse_sequence_report(sequence_report)
    fasta_accessions = set(fasta_records)
    if fasta_accessions != report_accessions:
        missing = sorted(report_accessions - fasta_accessions)
        unreported = sorted(fasta_accessions - report_accessions)
        raise CanonicalizationError(f"FASTA/report accession mismatch; missing={missing}; unreported={unreported}")
    canonical = b"".join(
        sequence_accession.encode("ascii") + b"\t" + fasta_records[sequence_accession] + b"\n"
        for sequence_accession in sorted(fasta_records)
    )
    return CanonicalAssembly(
        accession=accession,
        canonical_bytes=canonical,
        sequence_digest=f"sha256:{hashlib.sha256(canonical).hexdigest()}",
    )


def canonicalize_archive(
    *, archive_path: Path, inventory: Iterable[AssemblyInput], workspace: Path, expected_archive_digest: str,
    source_provenance_id: str = "m1-ncbi-refseq-package-acquisition-v1",
) -> dict[str, object]:
    """Canonicalize every declared assembly and record explicit quarantines."""

    if sha256_file(archive_path) != expected_archive_digest:
        raise CanonicalizationError("acquisition archive digest does not match the declared M1.3 input")
    workspace.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    entities: list[dict[str, object]] = []
    quarantines: list[dict[str, str]] = []
    digests: dict[str, list[str]] = {}
    with zipfile.ZipFile(archive_path) as archive:
        for assembly in inventory:
            try:
                fasta = archive.read(_member(archive, assembly.accession, "_genomic.fna"))
                report = archive.read(_member(archive, assembly.accession, "sequence_report.jsonl"))
                result = canonicalize_assembly(assembly.accession, fasta, report)
            except (CanonicalizationError, KeyError, zipfile.BadZipFile) as error:
                quarantines.append({"accession": assembly.accession, "reason": str(error)})
                continue
            canonical_path = workspace / "canonical" / f"{assembly.accession}.txt"
            canonical_path.parent.mkdir(parents=True, exist_ok=True)
            canonical_path.write_bytes(result.canonical_bytes)
            records.append({"record_id": result.record_id, "entity_id": result.entity_id, "sequence_digest": result.sequence_digest, "canonicalization_id": CANONICALIZATION_ID, "source_provenance_id": source_provenance_id, "lifecycle_state": "eligible"})
            entities.append({"entity_id": result.entity_id, "entity_type": "genome-assembly", "record_versions": [result.record_id]})
            digests.setdefault(result.sequence_digest, []).append(result.record_id)
    _write_jsonl(workspace / "genome-record-versions.jsonl", records)
    _write_jsonl(workspace / "atlas-entities.jsonl", entities)
    _write_jsonl(workspace / "quarantines.jsonl", quarantines)
    matching = {digest: ids for digest, ids in digests.items() if len(ids) > 1}
    outcome = "succeeded" if not quarantines else "quarantined"
    envelope = {"stage_id": "register-canonicalize", "input_artifacts": [{"path": str(archive_path), "media_type": "application/zip", "digest": expected_archive_digest}], "output_artifacts": [{"path": str(workspace / "genome-record-versions.jsonl"), "media_type": "application/x-ndjson", "digest": sha256_file(workspace / "genome-record-versions.jsonl")}, {"path": str(workspace / "atlas-entities.jsonl"), "media_type": "application/x-ndjson", "digest": sha256_file(workspace / "atlas-entities.jsonl")}], "exclusions": quarantines, "outcome": outcome, "verification": {"eligible_record_count": len(records), "quarantine_count": len(quarantines), "matching_sequence_digests": matching, "automatic_merge": False, "automatic_split": False}, "recovery": {"retry_requires": "a new empty canonicalization workspace"}}
    (workspace / "canonicalization-stage-envelope.json").write_text(json.dumps(envelope, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return envelope


def _parse_fasta(payload: bytes) -> dict[str, bytes]:
    records: dict[str, bytearray] = {}
    current: str | None = None
    for line in payload.splitlines():
        if line.startswith(b">"):
            header = line[1:].split(maxsplit=1)[0]
            try: accession = header.decode("ascii")
            except UnicodeDecodeError as error: raise CanonicalizationError("FASTA accession is not ASCII") from error
            if not accession or accession in records: raise CanonicalizationError("missing or duplicate FASTA accession")
            records[accession] = bytearray(); current = accession
        elif current is None: raise CanonicalizationError("sequence encountered before FASTA defline")
        else: records[current].extend(byte for byte in line.upper() if byte not in ASCII_WHITESPACE)
    if not records: raise CanonicalizationError("FASTA contains no records")
    normalized: dict[str, bytes] = {}
    for accession, sequence in records.items():
        if not sequence or any(byte not in ALLOWED_IUPAC_DNA for byte in sequence): raise CanonicalizationError(f"invalid or empty sequence for {accession}")
        normalized[accession] = bytes(sequence)
    return normalized


def _parse_sequence_report(payload: bytes) -> set[str]:
    accessions: set[str] = set()
    for line in payload.splitlines():
        if not line.strip(): continue
        try: row = json.loads(line)
        except json.JSONDecodeError as error: raise CanonicalizationError("sequence report contains invalid JSONL") from error
        accession = row.get("refseqAccession") if isinstance(row, dict) else None
        if not isinstance(accession, str) or not accession or accession in accessions: raise CanonicalizationError("missing or duplicate sequence-report accession")
        accessions.add(accession)
    if not accessions: raise CanonicalizationError("sequence report contains no accessions")
    return accessions


def _member(archive: zipfile.ZipFile, assembly_accession: str, suffix: str) -> str:
    matches = [name for name in archive.namelist() if f"/{assembly_accession}/" in name and name.endswith(suffix)]
    if len(matches) != 1: raise CanonicalizationError(f"archive must contain one {suffix} for {assembly_accession}")
    return matches[0]


def _write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
