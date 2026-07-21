"""M3 planning baseline remains evidence-first and scope-bounded."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class M3EvaluationPlanningTests(unittest.TestCase):
    def test_plan_preserves_m2_reference_and_deferred_decisions(self) -> None:
        plan = (ROOT / "docs" / "planning" / "M3-EVALUATION-PLAN.md").read_text(encoding="utf-8")
        self.assertIn("**Status:** M3.1 evaluation governance and M3.2 preregistration are complete.", plan)
        self.assertIn("`m2.0.0-complete`", plan)
        self.assertIn("OQ-05", plan)
        self.assertIn("Accepted claim-evidence requirements", plan)
        self.assertIn("**Satisfied:** M3-001 Version 1.0 is approved", plan)
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

    def test_m3001_is_an_approved_manifest_bound_deterministic_retrieval_preregistration(self) -> None:
        study = (ROOT / "benchmarks" / "preregistrations" / "m3-001-deterministic-exact-query-reproducibility.md").read_text(encoding="utf-8")
        corpus = (ROOT / "benchmarks" / "data-manifests" / "M3-001-M1-V3-DRAFT-QUERY-CORPUS.md").read_text(encoding="utf-8")
        manifest_path = ROOT / "benchmarks" / "evaluation-manifests" / "m3-001-v1-evaluation-manifest.json"
        approval_path = ROOT / "validation" / "evidence" / "m3-001-v1-approval-2026-07-21.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
        manifest_digest = "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()

        self.assertIn("**Status:** Approved — execution not yet initiated.", study)
        self.assertIn("**Version:** `1.0`.", study)
        self.assertIn("`EE-M3-001-v1`", study)
        self.assertIn("Microsoft Windows 10.0.26200", study)
        self.assertIn("Deterministic retrieval", study)
        self.assertIn("three independent Python process invocations", study)
        self.assertIn("Score tolerance: `0.0`", study)
        self.assertIn("6183145f8fd6018431c55fd2e4ee7e1001e5fc87", study)
        self.assertIn("sha256:332b9b0ae251547a0db50deb717d2c778a3e2e5be40644255598aef783b18765", study)
        self.assertIn("apply this exact comparison algorithm", study)
        self.assertIn("Compute SHA-256 over the canonical bytes", study)
        self.assertIn("**INCONCLUSIVE:**", study)
        self.assertIn("**ABORTED:**", study)
        self.assertIn("No inferential statistics, confidence intervals, p-values", study)
        self.assertIn("hardware portability, or cross-platform", study)
        self.assertIn(manifest_digest, study)
        self.assertEqual(manifest_digest, approval["evaluation_manifest_digest"])
        self.assertEqual("M3-001", approval["subject_id"])
        self.assertEqual("1.0", approval["subject_version"])
        self.assertEqual("EE-M3-001-v1", manifest["execution_environment"]["id"])
        self.assertEqual("6183145f8fd6018431c55fd2e4ee7e1001e5fc87", manifest["implementation"]["required_commit"])
        self.assertEqual(3, manifest["replicate_plan"]["count"])
        self.assertEqual("canonical-json-sha256-first-v1", manifest["comparison"]["equality_algorithm"])
        self.assertEqual(["PASS", "FAIL", "INCONCLUSIVE", "ABORTED"], manifest["outcomes"])
        self.assertIn("M3-001 execution MUST NOT start", study)
        self.assertIn("SHALL NOT evaluate or claim biological", study)
        self.assertIn("Expected record count | 12 canonical GenomeRecordVersions", corpus)
        self.assertIn("No annotations, derived relations, alternate embedding profiles", corpus)


if __name__ == "__main__":
    unittest.main()
