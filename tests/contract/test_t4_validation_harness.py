from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "validation" / "colab"))
from m1_t4_validation import PROFILE_ID, REVISION, WEIGHT_DIGEST  # noqa: E402


class T4ValidationHarnessTests(unittest.TestCase):
    def test_harness_is_validation_only_and_pins_the_frozen_model(self) -> None:
        self.assertEqual("m1-generanno-prokaryote-0.5b-assembly-v1", PROFILE_ID)
        self.assertEqual("d02db0f24f2c62fa1efde760217cdf75771b0228", REVISION)
        self.assertRegex(WEIGHT_DIGEST, r"^sha256:[0-9a-f]{64}$")
        instructions = (ROOT / "validation" / "colab" / "README.md").read_text()
        self.assertIn("validation evidence only", " ".join(instructions.replace("**", "").split()))
        self.assertIn("byte-for-byte", instructions)
        self.assertIn("CUBLAS_WORKSPACE_CONFIG", instructions)


if __name__ == "__main__":
    unittest.main()
