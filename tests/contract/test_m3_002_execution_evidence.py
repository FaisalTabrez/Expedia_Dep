"""M3-002 evidence retention checks without interpreting comparison observations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "validation" / "evidence" / "m3-002" / "execution-v1"


class M3002ExecutionEvidenceTests(unittest.TestCase):
    def test_required_raw_evidence_is_present_and_digest_verified(self) -> None:
        required = {
            "environment.json",
            "evaluation-lock.json",
            "release-verification.json",
            "canonical-requests.jsonl",
            "query-core-raw-results.jsonl",
            "query-core-projections.jsonl",
            "reference-projections.jsonl",
            "comparison.json",
            "digests.json",
            "incident-log.json",
            "analysis-location.json",
        }
        self.assertTrue(all((EVIDENCE / name).is_file() for name in required))
        digests = json.loads((EVIDENCE / "digests.json").read_text(encoding="utf-8"))
        self.assertEqual(required - {"digests.json"}, set(digests))
        for relative, expected in digests.items():
            payload = (EVIDENCE / relative).read_bytes()
            self.assertEqual("sha256:" + hashlib.sha256(payload).hexdigest(), expected)

    def test_execution_identities_and_observation_inventory_are_retained(self) -> None:
        environment = json.loads((EVIDENCE / "environment.json").read_text(encoding="utf-8"))
        release = json.loads((EVIDENCE / "release-verification.json").read_text(encoding="utf-8"))
        incidents = json.loads((EVIDENCE / "incident-log.json").read_text(encoding="utf-8"))
        comparison = json.loads((EVIDENCE / "comparison.json").read_text(encoding="utf-8"))
        requests = [json.loads(line) for line in (EVIDENCE / "canonical-requests.jsonl").read_text(encoding="utf-8").splitlines()]

        self.assertEqual("EE-M3-001-v1.1", environment["environment_id"])
        self.assertEqual("6183145f8fd6018431c55fd2e4ee7e1001e5fc87", environment["repository_commit"])
        self.assertEqual("command-scoped", environment["git_trust"]["scope"])
        self.assertEqual("expedia-m1-draft-20260721-v3", release["release_id"])
        self.assertEqual(12, release["canonical_record_count"])
        self.assertEqual(2, len(incidents["incidents"]))
        self.assertEqual(12, len(requests))
        self.assertEqual(12, len({row["canonical_request_digest"] for row in requests}))
        self.assertEqual(12, len(comparison["observations"]))
        self.assertNotIn("outcome", comparison)

    def test_analysis_remains_explicitly_pending(self) -> None:
        location = json.loads((EVIDENCE / "analysis-location.json").read_text(encoding="utf-8"))
        self.assertEqual("pending M3-002.7", location["status"])

    def test_observational_analysis_reports_evidence_without_a_claim_decision(self) -> None:
        analysis = (ROOT / "validation" / "evidence" / "m3-002" / "M3-002-analysis.md").read_text(encoding="utf-8")
        comparison = json.loads((EVIDENCE / "comparison.json").read_text(encoding="utf-8"))
        self.assertIn("Draft observational analysis — no maintainer claim decision.", analysis)
        self.assertIn("`sha256:1ca19ce393c2c475c59922e708401833a49334bea46e508cec574d034353c060`", analysis)
        self.assertIn("It does not classify the study as PASS or FAIL", analysis)
        self.assertIn("does not support or reject\nthe exact-query-correctness claim", analysis)
        self.assertEqual(12, len(comparison["observations"]))
        self.assertEqual(
            0,
            sum(observation["query_core_digest"] != observation["oracle_digest"] for observation in comparison["observations"]),
        )
        self.assertEqual(
            0,
            sum(bool(observation["diagnostic_fields"]) for observation in comparison["observations"]),
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
