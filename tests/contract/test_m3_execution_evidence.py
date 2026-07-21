"""Integrity checks for retained M3-001 execution evidence; no claim analysis."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "validation" / "evidence" / "m3-001" / "execution-v1"


class M3ExecutionEvidenceTests(unittest.TestCase):
    def test_complete_raw_bundle_is_bound_to_the_amended_environment(self) -> None:
        required = ("environment.json", "evaluation-lock.json", "release-verification.json", "comparison.json", "comparison.md", "digests.json", "incident-log.json")
        self.assertTrue(all((EVIDENCE / name).is_file() for name in required))
        lock = json.loads((EVIDENCE / "evaluation-lock.json").read_text(encoding="utf-8"))
        release = json.loads((EVIDENCE / "release-verification.json").read_text(encoding="utf-8"))
        self.assertEqual("EE-M3-001-v1.1", lock["environment"]["environment_id"])
        self.assertEqual("6183145f8fd6018431c55fd2e4ee7e1001e5fc87", lock["environment"]["repository_commit"])
        self.assertEqual(12, release["canonical_record_count"])

    def test_each_replicate_retains_the_required_raw_artifacts(self) -> None:
        names = ("canonical-requests.jsonl", "canonical-responses.jsonl", "cursors.jsonl", "warnings.jsonl", "typed-failures.jsonl", "replicate-provenance.json", "digests.json")
        for number in (1, 2, 3):
            with self.subTest(replicate=number):
                root = EVIDENCE / f"replicate-{number}"
                self.assertTrue(all((root / name).is_file() for name in names))

    def test_comparison_retains_observations_without_an_interpretive_outcome(self) -> None:
        comparison = json.loads((EVIDENCE / "comparison.json").read_text(encoding="utf-8"))
        self.assertEqual("canonical-json-sha256-first-v1", comparison["comparison_algorithm"])
        self.assertTrue(comparison["observations"])
        self.assertNotIn("outcome", comparison)
        for observation in comparison["observations"]:
            with self.subTest(request_id=observation["request_id"]):
                self.assertEqual(1, len(set(observation["canonical_request_digests"])))
                self.assertEqual(1, len(set(observation["result_digests"])))
                self.assertEqual([], observation["diagnostic_fields"]["replicate-2"])
                self.assertEqual([], observation["diagnostic_fields"]["replicate-3"])

    def test_digest_inventory_matches_every_non_self_evidence_file(self) -> None:
        inventory = json.loads((EVIDENCE / "digests.json").read_text(encoding="utf-8"))
        for path in sorted(EVIDENCE.rglob("*")):
            if not path.is_file() or path.name == "digests.json":
                continue
            relative = path.relative_to(EVIDENCE).as_posix()
            self.assertEqual("sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(), inventory[relative])


if __name__ == "__main__":
    unittest.main()
