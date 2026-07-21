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
        self.assertIn("**Status:** M3.1–M3.5 are complete for M3-001.", plan)
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
        manifest_path = ROOT / "benchmarks" / "evaluation-manifests" / "m3-001-v1.1-evaluation-manifest.json"
        approval_path = ROOT / "validation" / "evidence" / "m3-001-v1.0-environment-amendment-approval-2026-07-21.json"
        amendment_path = ROOT / "benchmarks" / "preregistrations" / "m3-001-v1.0-execution-environment-amendment.md"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
        manifest_digest = "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()

        self.assertIn("**Status:** Approved — execution not yet initiated.", study)
        self.assertIn("**Version:** `1.0`.", study)
        self.assertIn("`EE-M3-001-v1.1`", study)
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
        self.assertEqual(manifest_digest, approval["effective_evaluation_manifest_digest"])
        self.assertEqual("M3-001", approval["subject_id"])
        self.assertEqual("1.0", approval["subject_version"])
        self.assertEqual("EE-M3-001-v1.1", manifest["execution_environment"]["id"])
        self.assertEqual("sha256:5912d0884b23c0343983a864c6064242391e2265536f50b88624857e353882c9", manifest["execution_environment"]["python_executable_digest"])
        self.assertIn("No scientific question, methodology, analysis, claim boundary", amendment_path.read_text(encoding="utf-8"))
        self.assertEqual("6183145f8fd6018431c55fd2e4ee7e1001e5fc87", manifest["implementation"]["required_commit"])
        self.assertEqual(3, manifest["replicate_plan"]["count"])
        self.assertEqual("canonical-json-sha256-first-v1", manifest["comparison"]["equality_algorithm"])
        self.assertEqual(["PASS", "FAIL", "INCONCLUSIVE", "ABORTED"], manifest["outcomes"])
        self.assertIn("M3-001 execution MUST NOT start", study)
        self.assertIn("SHALL NOT evaluate or claim biological", study)
        self.assertIn("Expected record count | 12 canonical GenomeRecordVersions", corpus)
        self.assertIn("No annotations, derived relations, alternate embedding profiles", corpus)

    def test_m3002_has_an_approved_preregistration_and_immutable_oracle_bound_manifest(self) -> None:
        study = (ROOT / "benchmarks" / "preregistrations" / "m3-002-exact-float32-cosine-correctness.md").read_text(encoding="utf-8")
        corpus = (ROOT / "benchmarks" / "data-manifests" / "M3-002-M1-V3-EXACT-COSINE-CORPUS.md").read_text(encoding="utf-8")
        reference = (ROOT / "benchmarks" / "reference" / "M3-002-INDEPENDENT-REFERENCE-SPECIFICATION.md").read_text(encoding="utf-8")
        claim_check = (ROOT / "benchmarks" / "preregistrations" / "M3-002-CLAIM-BOUNDARY-VERIFICATION.md").read_text(encoding="utf-8")
        template = json.loads((ROOT / "benchmarks" / "evaluation-manifests" / "M3-002-EVALUATION-MANIFEST-TEMPLATE.json").read_text(encoding="utf-8"))
        manifest_path = ROOT / "benchmarks" / "evaluation-manifests" / "m3-002-v1-evaluation-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        approval = json.loads((ROOT / "validation" / "evidence" / "m3-002" / "m3-002-preregistration-approval-2026-07-21.json").read_text(encoding="utf-8"))
        manifest_approval_path = ROOT / "validation" / "evidence" / "m3-002" / "m3-002-evaluation-manifest-approval-2026-07-21.json"
        manifest_approval = json.loads(manifest_approval_path.read_text(encoding="utf-8"))
        oracle_verification_path = ROOT / "validation" / "evidence" / "m3-002" / "m3-002-oracle-verification-2026-07-21.json"
        oracle_verification = json.loads(oracle_verification_path.read_text(encoding="utf-8"))
        review = (ROOT / "validation" / "evidence" / "m3-002" / "m3-002-preregistration-review-2026-07-21.md").read_text(encoding="utf-8")
        self.assertIn("**Status:** Approved — execution remains prohibited pending later M3-002 gates.", study)
        self.assertIn("**Version:** `1.0`.", study)
        self.assertIn("**Claim category.** Exact query correctness.", study)
        self.assertIn(
            "Until every remaining unchecked item is complete, M3-002 MUST NOT execute.",
            study,
        )
        self.assertIn("SHALL NOT import,\ncall, copy, or reuse any Query Core", reference)
        self.assertIn("score-desc-record-id-asc-v1", reference)
        self.assertIn("Expected record count | 12 canonical GenomeRecordVersions", corpus)
        self.assertIn("`EE-M3-001-v1.1`", corpus)
        self.assertIn("Therefore it satisfies only that evidence requirement.", claim_check)
        self.assertEqual("unapproved-template", template["approval_status"])
        self.assertEqual("M3-002", approval["subject_id"])
        self.assertEqual("1.0", approval["subject_version"])
        self.assertEqual("sha256:" + hashlib.sha256((ROOT / "benchmarks" / "preregistrations" / "m3-002-exact-float32-cosine-correctness.md").read_bytes()).hexdigest(), approval["preregistration_digest"])
        self.assertIn("**Status:** Passed maintainer review.", review)
        self.assertIn("**Status:** Implemented validation-only oracle.", reference)
        self.assertEqual("accepted-immutable", manifest["approval_status"])
        self.assertEqual("M3-002", manifest["study_id"])
        self.assertEqual("exact query correctness", manifest["claim_category"])
        self.assertEqual("6183145f8fd6018431c55fd2e4ee7e1001e5fc87", manifest["implementation"]["required_commit"])
        self.assertEqual("EE-M3-001-v1.1", manifest["execution_environment"]["id"])
        self.assertEqual(0.0, manifest["comparison"]["score_equality_tolerance"])
        self.assertEqual(["PASS", "FAIL", "INCONCLUSIVE", "ABORTED"], manifest["outcomes"])
        self.assertEqual(
            "sha256:" + hashlib.sha256((ROOT / manifest["preregistration"]["path"]).read_bytes()).hexdigest(),
            manifest["preregistration"]["digest"],
        )
        self.assertEqual(
            "sha256:" + hashlib.sha256((ROOT / manifest["reference_implementation"]["source_path"]).read_bytes()).hexdigest(),
            manifest["reference_implementation"]["source_digest"],
        )
        self.assertEqual(
            "sha256:" + hashlib.sha256((ROOT / manifest["reference_implementation"]["specification_path"]).read_bytes()).hexdigest(),
            manifest["reference_implementation"]["specification_digest"],
        )
        self.assertEqual(
            "sha256:" + hashlib.sha256(oracle_verification_path.read_bytes()).hexdigest(),
            manifest["reference_implementation"]["oracle_verification_digest"],
        )
        self.assertEqual("passed", oracle_verification["outcome"])
        self.assertEqual(
            "software verification only; no M3-002 Query Core/reference comparison was executed",
            oracle_verification["evidence_scope"],
        )
        self.assertEqual(
            "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            manifest_approval["evaluation_manifest_digest"],
        )
        self.assertEqual("M3-002", manifest_approval["subject_id"])
        self.assertEqual("1.0", manifest_approval["subject_version"])
        self.assertIn(
            "Any subsequent change requires a controlled amendment and a new maintainer approval record.",
            manifest_approval["conditions"],
        )


if __name__ == "__main__":
    unittest.main()
