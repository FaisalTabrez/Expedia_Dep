"""M3 planning baseline remains evidence-first and scope-bounded."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class M3EvaluationPlanningTests(unittest.TestCase):
    def test_plan_preserves_m2_reference_and_deferred_decisions(self) -> None:
        plan = (ROOT / "docs" / "planning" / "M3-EVALUATION-PLAN.md").read_text(encoding="utf-8")
        self.assertIn("**Status:** M3.1 evaluation governance is complete.", plan)
        self.assertIn("`m2.0.0-complete`", plan)
        self.assertIn("OQ-05", plan)
        self.assertIn("Accepted claim-evidence requirements", plan)
        self.assertIn("**Blocking; not yet authored.**", plan)
        self.assertIn("exact float32 cosine remains the reference retrieval method", plan)
        self.assertIn("OQ-04", plan)
        self.assertIn("Deferred; no ANN study is planned", plan)
        self.assertIn("OQ-08", plan)
        self.assertIn("no cross-profile study is planned", plan)
        self.assertIn("ADR register reconciliation note", plan)
        self.assertIn("no universal numerical threshold", plan)

    def test_oq05_and_adr_reconciliation_preserve_claim_boundaries(self) -> None:
        oq05 = (ROOT / "specification" / "open-questions" / "OQ-05-M3-claim-evidence-requirements.md").read_text(encoding="utf-8")
        reconciliation = (ROOT / "specification" / "adr" / "ADR-REGISTER-RECONCILIATION-009-014.md").read_text(encoding="utf-8")
        self.assertIn("**Status:** Accepted M3 disposition", oq05)
        self.assertIn("M3 defines evidence requirements and claim boundaries", oq05)
        self.assertIn("No numerical threshold is implied", oq05)
        self.assertIn("ANN quality preservation", oq05)
        self.assertIn("this note is not an ADR", reconciliation)
        self.assertIn("EDS-proposed register entries", reconciliation)
        self.assertIn("not recoverable repository artifacts", reconciliation)
        self.assertIn("reconstruct an absent historical decision", reconciliation)

    def test_m31_governance_templates_block_unapproved_experiments(self) -> None:
        register = (ROOT / "benchmarks" / "preregistrations" / "M3-CLAIM-BOUNDARY-REGISTER.md").read_text(encoding="utf-8")
        template = (ROOT / "benchmarks" / "preregistrations" / "M3-PREREGISTRATION-TEMPLATE.md").read_text(encoding="utf-8")
        plan = (ROOT / "docs" / "planning" / "M3-EVALUATION-PLAN.md").read_text(encoding="utf-8")
        self.assertIn("evidence\nrequirements, not results", register)
        self.assertIn("ANN evaluation is not in the M3 reference-study scope", register)
        self.assertIn("An incomplete or unapproved copy MUST NOT be run.", template)
        self.assertIn("M2 Query Core exact float32 cosine", template)
        self.assertIn("No result, outcome, or unsupported claim has been inserted.", template)
        self.assertIn("**Complete:** reusable templates require", plan)

    def test_m3001_is_a_non_executable_deterministic_retrieval_preregistration(self) -> None:
        study = (ROOT / "benchmarks" / "preregistrations" / "m3-001-deterministic-exact-query-reproducibility.md").read_text(encoding="utf-8")
        corpus = (ROOT / "benchmarks" / "data-manifests" / "M3-001-M1-V3-DRAFT-QUERY-CORPUS.md").read_text(encoding="utf-8")
        self.assertIn("**Status:** Draft — not accepted; execution is prohibited.", study)
        self.assertIn("Deterministic retrieval", study)
        self.assertIn("three independent Python process invocations", study)
        self.assertIn("Score tolerance: `0.0`", study)
        self.assertIn("M3-001 MUST NOT execute", study)
        self.assertIn("SHALL NOT evaluate or claim biological", study)
        self.assertIn("Expected record count | 12 canonical GenomeRecordVersions", corpus)
        self.assertIn("No annotations, derived relations, alternate embedding profiles", corpus)


if __name__ == "__main__":
    unittest.main()
