from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "atlas-builder" / "src"))
from expedia_atlas_builder.canonicalization import CanonicalizationError, canonicalize_assembly  # noqa: E402


class CanonicalizationTests(unittest.TestCase):
    def test_canonical_bytes_sort_accessions_and_normalize_iupac_dna(self) -> None:
        result = canonicalize_assembly("GCF_000000001.1", b">NZ_B.1 second\n nry\n>NZ_A.1 first\n acg t\n", b'{"refseqAccession":"NZ_A.1"}\n{"refseqAccession":"NZ_B.1"}\n')
        expected = b"NZ_A.1\tACGT\nNZ_B.1\tNRY\n"
        self.assertEqual(expected, result.canonical_bytes)
        self.assertEqual(f"sha256:{hashlib.sha256(expected).hexdigest()}", result.sequence_digest)
        self.assertEqual("ncbi-assembly:GCF_000000001", result.entity_id)
        self.assertEqual("ncbi-assembly:GCF_000000001.1:m1-assembly-canonical-v1", result.record_id)

    def test_invalid_symbols_and_report_mismatches_are_rejected(self) -> None:
        with self.assertRaisesRegex(CanonicalizationError, "invalid"):
            canonicalize_assembly("GCF_000000001.1", b">NZ_A.1\nACGU\n", b'{"refseqAccession":"NZ_A.1"}\n')
        with self.assertRaisesRegex(CanonicalizationError, "mismatch"):
            canonicalize_assembly("GCF_000000001.1", b">NZ_A.1\nACGT\n", b'{"refseqAccession":"NZ_B.1"}\n')

    def test_duplicate_sequence_report_accessions_are_rejected(self) -> None:
        with self.assertRaisesRegex(CanonicalizationError, "duplicate"):
            canonicalize_assembly("GCF_000000001.1", b">NZ_A.1\nACGT\n", b'{"refseqAccession":"NZ_A.1"}\n{"refseqAccession":"NZ_A.1"}\n')

    def test_committed_m1_stage_outcome_has_no_quarantines_or_merges(self) -> None:
        outcome = json.loads((ROOT / "atlas-builder" / "manifests" / "m1" / "m1-canonicalization-stage-outcome.json").read_text())
        self.assertEqual("succeeded", outcome["outcome"])
        self.assertEqual(12, outcome["verification"]["eligible_record_count"])
        self.assertEqual(0, outcome["verification"]["quarantine_count"])
        self.assertEqual({}, outcome["verification"]["matching_sequence_digests"])
        self.assertFalse(outcome["verification"]["automatic_merge"])
        self.assertFalse(outcome["verification"]["automatic_split"])


if __name__ == "__main__": unittest.main()
