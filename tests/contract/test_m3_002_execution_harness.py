"""M3-002 runner tests that do not execute the approved study corpus."""

from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks" / "execution"))

from m3_002_runner import (  # noqa: E402
    _diagnostic_fields,
    _initialize_incident_log,
    canonical_json,
    query_core_projection,
    resolve_git_executable,
)


class M3002ExecutionHarnessTests(unittest.TestCase):
    def _result(self) -> dict[str, object]:
        return {
            "outcome": "success",
            "rows": [
                {"record_id": "record:a", "score": 1.0},
                {"record_id": "record:b", "score": 0.5},
            ],
            "context": {"profile_id": "profile", "ordering_version": "score-desc-record-id-asc-v1"},
            "provenance": {
                "release_digest": "sha256:release",
                "profile_version": "1.0.0",
                "profile_digest": "sha256:profile",
                "vector_shard_digest": "sha256:shard",
            },
        }

    def test_query_core_projection_contains_only_preregistered_comparison_fields(self) -> None:
        projection = query_core_projection(
            result=self._result(),
            canonical_request_digest="sha256:" + "a" * 64,
        )
        self.assertEqual(
            {"canonical_request_digest", "ordered_record_ids", "decoded_float32_scores", "provenance"},
            set(projection),
        )
        self.assertEqual(["record:a", "record:b"], projection["ordered_record_ids"])
        self.assertEqual([1.0, 0.5], projection["decoded_float32_scores"])
        self.assertEqual("profile", projection["provenance"]["profile_id"])

    def test_canonical_comparison_json_is_key_sorted_and_whitespace_free(self) -> None:
        self.assertEqual('{"a":[0.5,1],"z":"value"}', canonical_json({"z": "value", "a": [0.5, 1]}))

    def test_diagnostics_are_limited_to_the_preregistered_field_order(self) -> None:
        left = {
            "ordered_record_ids": ["record:a"],
            "decoded_float32_scores": [1.0],
            "provenance": {"release_digest": "sha256:one"},
        }
        right = {
            "ordered_record_ids": ["record:b"],
            "decoded_float32_scores": [0.5],
            "provenance": {"release_digest": "sha256:two"},
        }
        self.assertEqual(
            ["ordered_record_ids", "decoded_float32_scores", "provenance"],
            _diagnostic_fields(left, right),
        )

    def test_runner_contains_no_study_outcome_classifier(self) -> None:
        source = (ROOT / "benchmarks" / "execution" / "m3_002_runner.py").read_text(encoding="utf-8")
        self.assertNotIn('"PASS"', source)
        self.assertNotIn('"FAIL"', source)
        self.assertNotIn("claim decision", source.lower())

    def test_runner_resolves_an_explicit_git_executable_without_path_lookup(self) -> None:
        with patch.dict("os.environ", {"EXPEDIA_GIT_EXECUTABLE": sys.executable}, clear=True):
            with patch("m3_002_runner.shutil.which", side_effect=AssertionError("PATH lookup must not occur")):
                self.assertEqual(Path(sys.executable).resolve(), resolve_git_executable())

    def test_preexisting_incident_log_is_retained_when_verification_restarts(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "incident-log.json"
            original = '{"incidents":[{"type":"prior"}],"study_id":"M3-002"}'
            log.write_text(original, encoding="utf-8")
            _initialize_incident_log(root)
            self.assertEqual(original, log.read_text(encoding="utf-8"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
