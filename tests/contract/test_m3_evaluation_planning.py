"""M3 planning baseline remains evidence-first and scope-bounded."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class M3EvaluationPlanningTests(unittest.TestCase):
    def test_plan_preserves_m2_reference_and_deferred_decisions(self) -> None:
        plan = (ROOT / "docs" / "planning" / "M3-EVALUATION-PLAN.md").read_text(encoding="utf-8")
        self.assertIn("**Status:** Proposed planning baseline. M3 implementation and experiments have\nnot started.", plan)
        self.assertIn("`m2.0.0-complete`", plan)
        self.assertIn("OQ-05", plan)
        self.assertIn("**Blocking; unresolved.**", plan)
        self.assertIn("exact float32 cosine remains the reference retrieval method", plan)
        self.assertIn("OQ-04", plan)
        self.assertIn("Deferred; no ANN study is planned", plan)
        self.assertIn("OQ-08", plan)
        self.assertIn("no cross-profile study is planned", plan)
        self.assertIn("no local ADR-009 or ADR-014 record", plan)
        self.assertIn("no universal numerical threshold", plan)


if __name__ == "__main__":
    unittest.main()
