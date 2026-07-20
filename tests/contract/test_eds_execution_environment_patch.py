from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class EDSExecutionEnvironmentPatchTests(unittest.TestCase):
    def test_patch_is_limited_to_execution_policy_and_identifies_every_clause(self) -> None:
        patch = (ROOT / "specification" / "changes" / "EDS-v2.1.1-M1-deterministic-execution-environment-patch.md").read_text(encoding="utf-8")
        for locator in (
            "§5.1",
            "§8.2",
            "§9.1",
            "§9.2",
            "§9.3",
            "§9.4",
            "Appendix C, OQ-03",
            "Appendix D",
        ):
            self.assertIn(locator, patch)
        self.assertIn("m1-generanno-t4-cuda12.1-fp32-deterministic-v1", patch)
        self.assertIn("not a new EmbeddingProfile", patch)
        self.assertIn("No JSON Schema, Python contract binding, canonicalization profile", patch)
        self.assertIn("sha256:f7b4ba4a6f45eb69120f799a520b297d497705e5380e82ebb109afb7e3f69cff", patch)

    def test_accepted_successor_is_present(self) -> None:
        patch = (ROOT / "specification" / "changes" / "EDS-v2.1.1-M1-deterministic-execution-environment-patch.md").read_text(encoding="utf-8")
        self.assertIn("**Status:** Accepted controlled amendment, effective 20 July 2026.", patch)
        self.assertTrue((ROOT / "EXPEDIA_Design_Specification_EDS_v2.1.1.docx").is_file())


if __name__ == "__main__":
    unittest.main()
