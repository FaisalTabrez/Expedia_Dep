from __future__ import annotations

from pathlib import Path
import unittest


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

    def test_m2_plan_authorizes_contract_work_only(self) -> None:
        content = (ROOT / "docs" / "planning" / "M2-IMPLEMENTATION-PLAN.md").read_text(encoding="utf-8")
        self.assertIn("accepted for M2.1", content)
        self.assertIn("No M2 production implementation is present yet.", content)
        self.assertIn("M2.2 or later implementation remains dependent", content)


if __name__ == "__main__":
    unittest.main()
