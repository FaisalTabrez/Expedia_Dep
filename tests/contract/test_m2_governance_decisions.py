from __future__ import annotations

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
ADR_PATHS = (
    ROOT / "specification" / "adr" / "ADR-010-trusted-local-release-boundary.md",
    ROOT / "specification" / "adr" / "ADR-011-exact-cosine-m2-reference-search.md",
    ROOT / "specification" / "adr" / "ADR-016-query-core-semantic-authority.md",
)


class M2GovernanceDecisionTests(unittest.TestCase):
    def test_accepted_adrs_are_complete_and_nonempty(self) -> None:
        required_sections = ("## Decision", "## Rationale", "## Consequences", "## Acceptance criteria", "## EDS clauses affected", "## Non-goals")
        for path in ADR_PATHS:
            content = path.read_text(encoding="utf-8")
            self.assertIn("**Status:** Accepted", content, path.name)
            self.assertGreater(len(content), 1_000, path.name)
            for section in required_sections:
                self.assertIn(section, content, f"{path.name}: {section}")

    def test_oq11_accepts_one_canonical_request_interpretation(self) -> None:
        content = (ROOT / "specification" / "open-questions" / "OQ-11-M2-filter-grammar-and-cost-limits.md").read_text(encoding="utf-8")
        self.assertIn("**Status:** Accepted M2 disposition", content)
        self.assertIn("A QueryRequest has exactly one canonical interpretation.", content)
        self.assertIn("Whitespace, JSON", content)
        self.assertIn("object-member ordering SHALL NOT affect", content)
        self.assertIn("canonical_request_digest", content)
        self.assertIn("duplicate object-member names", content)

    def test_m2_plan_records_m2_4_completion_without_authorizing_sdk_or_rest(self) -> None:
        content = (ROOT / "docs" / "planning" / "M2-IMPLEMENTATION-PLAN.md").read_text(encoding="utf-8")
        self.assertIn("M2.1 Query Contract Gate is approved", content)
        self.assertIn("M2.2 Verified Release Adapter and", content)
        self.assertIn("M2.3 exact cosine reference search are implemented", content)
        self.assertIn("M2.4 Core filtering, bounded traversal\nselection, warnings/errors, and stable cursors are implemented", content)
        self.assertIn("**Complete:** adapter refuses unverified artifacts", content)
        self.assertIn("**Complete:** normalized profile-scoped vectors", content)
        self.assertIn("**Complete:** Core evaluates supported canonical filters", content)

    def test_m2_contract_conformance_matrix_authorizes_m2_2(self) -> None:
        content = (ROOT / "docs" / "planning" / "M2-QUERY-CONTRACT-CONFORMANCE-MATRIX.md").read_text(encoding="utf-8")
        self.assertIn("Approved M2.1 query-contract gate", content)
        self.assertIn("M2.2 verified-release-adapter work is authorized", content)
        for contract in ("QueryRequest", "QueryResult", "Filter", "Cursor", "Errors and warnings"):
            self.assertIn(f"| {contract} |", content)
        self.assertEqual(5, content.count("| **Pass** |"))
        self.assertIn("m2-query-contract-gate-approval-2026-07-21.json", content)
        self.assertIn("m2-query-result-contract-defect-correction-approval-2026-07-21.json", content)
        self.assertIn("m2-filter-expression-contract-defect-correction-approval-2026-07-21.json", content)
        self.assertIn("query-result/0.1.1", content)
        self.assertIn("filter-expression/0.1.1", content)

    def test_m2_query_contract_gate_approval_is_schema_valid_and_scoped(self) -> None:
        decision = json.loads((ROOT / "validation" / "evidence" / "m2-query-contract-gate-approval-2026-07-21.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "schemas" / "json" / "approval-record.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(decision)
        self.assertEqual("m2-query-contract-gate-approved", decision["action"])
        self.assertEqual("m2-query-contracts-0.1.0", decision["subject_id"])
        self.assertIn("M2.2 Verified Release Adapter work only", decision["rationale"])
        self.assertIn("no ANN, release publication", decision["rationale"])

    def test_query_result_defect_correction_is_schema_valid_and_narrowly_scoped(self) -> None:
        decision = json.loads(
            (ROOT / "validation" / "evidence" / "m2-query-result-contract-defect-correction-approval-2026-07-21.json").read_text(encoding="utf-8")
        )
        schema = json.loads((ROOT / "schemas" / "json" / "approval-record.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(decision)
        self.assertEqual("m2-query-result-contract-defect-correction-approved", decision["action"])
        self.assertEqual("query-result/0.1.1", decision["subject_id"])
        self.assertIn("metric direction", decision["rationale"])
        self.assertIn("vector-shard digest", decision["rationale"])
        self.assertIn("QueryRequest semantics", decision["rationale"])

    def test_filter_expression_defect_correction_is_schema_valid_and_narrowly_scoped(self) -> None:
        decision = json.loads(
            (ROOT / "validation" / "evidence" / "m2-filter-expression-contract-defect-correction-approval-2026-07-21.json").read_text(encoding="utf-8")
        )
        schema = json.loads((ROOT / "schemas" / "json" / "approval-record.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(decision)
        self.assertEqual("m2-filter-expression-contract-defect-correction-approved", decision["action"])
        self.assertEqual("filter-expression/0.1.1", decision["subject_id"])
        self.assertIn("object-based FieldRef", decision["rationale"])
        self.assertIn("false state", decision["rationale"])
        self.assertIn("QueryRequest semantics", decision["rationale"])


if __name__ == "__main__":
    unittest.main()
