from __future__ import annotations

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
TRACEABILITY_PATH = ROOT / "specification" / "requirements" / "m1-traceability.json"
M1_REQUIREMENTS = {
    "REQ-001", "REQ-002", "REQ-003", "REQ-004", "REQ-005",
    "REQ-008", "REQ-009", "REQ-010", "REQ-015", "REQ-018",
    "REQ-019", "REQ-020", "REQ-021", "REQ-022", "REQ-025",
}


class M1TraceabilityTests(unittest.TestCase):
    def test_every_m1_baseline_requirement_has_complete_existing_evidence_links(self) -> None:
        traceability = json.loads(TRACEABILITY_PATH.read_text(encoding="utf-8"))
        self.assertEqual("m1-ers-traceability-v1", traceability["traceability_id"])
        requirements = traceability["requirements"]
        self.assertIsInstance(requirements, list)
        self.assertEqual(M1_REQUIREMENTS, {entry["requirement_id"] for entry in requirements})

        required_fields = {"requirement_id", "eds_anchor", "adr_reference", "implementation", "verification", "documentation", "m1_disposition"}
        for entry in requirements:
            self.assertEqual(required_fields, set(entry), entry["requirement_id"])
            for field in ("eds_anchor", "adr_reference", "m1_disposition"):
                self.assertIsInstance(entry[field], str, f"{entry['requirement_id']} {field}")
                self.assertTrue(entry[field].strip(), f"{entry['requirement_id']} {field}")
            for field in ("implementation", "verification", "documentation"):
                self.assertIsInstance(entry[field], list, f"{entry['requirement_id']} {field}")
                self.assertTrue(entry[field], f"{entry['requirement_id']} {field}")
                for reference in entry[field]:
                    self.assertIsInstance(reference, str, f"{entry['requirement_id']} {field}")
                    self.assertTrue((ROOT / reference).exists(), f"missing {field} reference: {reference}")

    def test_evidence_index_preserves_draft_scope_and_no_claim_boundary(self) -> None:
        index = (ROOT / "validation" / "evidence" / "m1-evidence-index.md").read_text(encoding="utf-8")
        self.assertIn("**Release state:** `Draft`", index)
        self.assertIn("no persistent identifier", index)
        self.assertIn("no biological, scalability, retrieval-quality,", index)
        self.assertIn("does not authorize Candidate, Published, archive, or", index)

    def test_maintainer_decision_is_schema_valid_and_retains_draft_boundary(self) -> None:
        decision = json.loads((ROOT / "validation" / "evidence" / "m1-maintainer-decision-2026-07-21.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "schemas" / "json" / "approval-record.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(decision)
        self.assertEqual("m1-draft-evidence-gate-approved", decision["action"])
        self.assertEqual("expedia-m1-draft-20260721-v2", decision["subject_id"])
        self.assertIn("no Candidate, Published, archival, citation, or public-distribution authorization", decision["rationale"])


if __name__ == "__main__":
    unittest.main()
