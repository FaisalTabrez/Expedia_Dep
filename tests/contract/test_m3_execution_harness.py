"""M3-001 evidence harness safeguards without executing a study."""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
HARNESS_PATH = ROOT / "benchmarks" / "execution" / "m3_001_runner.py"
SPEC = importlib.util.spec_from_file_location("m3_001_runner", HARNESS_PATH)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


class M3ExecutionHarnessTests(unittest.TestCase):
    def test_canonical_evidence_json_normalizes_finite_numbers(self) -> None:
        self.assertEqual('{"a":1,"b":[0,1.25]}', HARNESS.canonical_json({"b": [-0.0, 1.25], "a": 1.0}))
        with self.assertRaises(HARNESS.EvidenceError):
            HARNESS.canonical_json({"bad": math.nan})

    def test_diagnostic_order_is_preregistered_and_stable(self) -> None:
        first = {"outcome": "success", "rows": [{"record_id": "a", "score": 1.0}], "provenance": {"release_digest": "x"}, "warnings": [], "next_cursor": None}
        second = {"outcome": "error", "error": {"code": "invalid_cursor", "stage": "validate"}, "rows": [], "provenance": {"release_digest": "y"}, "warnings": ["w"], "next_cursor": "cursor"}
        self.assertEqual(
            [
                "outcome_type",
                "typed_error_code_and_stage",
                "ordered_record_ids",
                "decoded_scores",
                "provenance",
                "warnings_in_returned_order",
                "opaque_cursor_payloads_and_continuation_reconstruction",
            ],
            HARNESS._diagnostic(first, second),
        )

    def test_harness_only_imports_core_from_explicit_implementation_workspace(self) -> None:
        source = HARNESS_PATH.read_text(encoding="utf-8")
        self.assertIn("Query Core was not imported from the frozen implementation workspace", source)
        self.assertNotIn("faiss", source.lower())
        self.assertNotIn("hnsw", source.lower())


if __name__ == "__main__":
    unittest.main()
