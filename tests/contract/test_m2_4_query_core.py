"""M2.4 Core conformance: corrected filters, cursors, and traversal refusal."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "contract"))
sys.path.insert(0, str(ROOT / "atlas-builder" / "src"))
sys.path.insert(0, str(ROOT / "schemas" / "python"))
sys.path.insert(0, str(ROOT / "validation" / "src"))
sys.path.insert(0, str(ROOT / "query-core" / "src"))

from expedia_atlas_builder.release_successor import create_m1_profile_successor  # noqa: E402
from expedia_query_core.exact_cosine import ExactCosineQueryCore  # noqa: E402
from expedia_query_core.filters import selected_record_ids  # noqa: E402
from expedia_query_core.verified_release import open_verified_release  # noqa: E402
from m1_draft_fixture import build_m1_draft_package  # noqa: E402


PROFILE_ID = "m1-generanno-prokaryote-0.5b-assembly-v1"


class M24QueryCoreTests(unittest.TestCase):
    def _core(self, root: Path) -> ExactCosineQueryCore:
        predecessor = build_m1_draft_package(root / "predecessor")
        successor = root / "successor"
        create_m1_profile_successor(
            predecessor_package=predecessor,
            profile_record=ROOT / "profiles" / "embedding" / f"{PROFILE_ID}.json",
            successor_package=successor,
            successor_release_id="expedia-m1-draft-m2-4-test-v3",
            created_at="2026-07-21T10:00:00Z",
        )
        return ExactCosineQueryCore(open_verified_release(successor))

    @staticmethod
    def _similarity_request(core: ExactCosineQueryCore, *, record_id: str, **changes: object) -> str:
        release = core._release  # Test-only immutable M2.2 snapshot access.
        request: dict[str, object] = {
            "schema_version": "query-request/0.1.0",
            "release_selector": {"release_id": release.release_id, "release_digest": release.release_digest},
            "operation": "similarity",
            "profile_selector": {"profile_id": PROFILE_ID, "profile_version": "1.0.0"},
            "similarity": {"query_record_id": record_id, "metric": "cosine", "mode": "exact"},
        }
        request.update(changes)
        return json.dumps(request)

    def test_canonical_filter_is_evaluated_before_exact_ranking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core = self._core(Path(directory))
            record_id = core._release.read_table("records/genome-record-versions.jsonl")[4]["record_id"]
            assert isinstance(record_id, str)
            filter_expression = {
                "all": [
                    {"eq": {"field": {"kind": "canonical", "name": "record_id"}, "value": record_id}},
                    {"state": {"field": {"kind": "canonical", "name": "lifecycle_state"}, "is": "present"}},
                ]
            }
            result = core.execute(self._similarity_request(core, record_id=record_id, filter=filter_expression))
            self.assertEqual("success", result["outcome"])
            self.assertEqual([record_id], [row["record_id"] for row in result["rows"]])  # type: ignore[index]
            self.assertEqual("method_not_evaluated", result["warnings"][0]["code"])  # type: ignore[index]

    def test_false_state_is_distinct_from_present_for_core_evaluation(self) -> None:
        records = {"record": {"record_id": "record", "lifecycle_state": False}}
        field = {"kind": "canonical", "name": "lifecycle_state"}
        self.assertEqual(frozenset({"record"}), selected_record_ids({"state": {"field": field, "is": "false"}}, records))
        self.assertEqual(frozenset(), selected_record_ids({"state": {"field": field, "is": "present"}}, records))

    def test_unsupported_filter_forms_are_typed_and_never_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core = self._core(Path(directory))
            record_id = core._release.read_table("records/genome-record-versions.jsonl")[0]["record_id"]
            assert isinstance(record_id, str)
            cases = (
                ({"range": {"field": {"kind": "canonical", "name": "record_id"}, "gte": 1, "lte": 2, "unit": "ordinal"}}, "unsupported_filter"),
                ({"eq": {"field": {"kind": "annotation", "source": "test", "predicate": "flag"}, "value": True}}, "unsupported_filter"),
                ({"relation": {"relation_type": "derived_from", "direction": "outbound"}}, "unsupported_relation"),
            )
            for filter_expression, code in cases:
                with self.subTest(code=code):
                    result = core.execute(self._similarity_request(core, record_id=record_id, filter=filter_expression))
                    self.assertEqual("error", result["outcome"])
                    self.assertEqual(code, result["error"]["code"])  # type: ignore[index]

    def test_cursor_binds_release_and_canonical_selection_and_resumes_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core = self._core(Path(directory))
            record_id = core._release.read_table("records/genome-record-versions.jsonl")[5]["record_id"]
            assert isinstance(record_id, str)
            first = core.execute(self._similarity_request(core, record_id=record_id, pagination={"limit": 2, "cursor": None, "ordering_version": "score-desc-record-id-asc-v1"}))
            cursor = first["next_cursor"]
            assert isinstance(cursor, str)
            second = core.execute(self._similarity_request(core, record_id=record_id, pagination={"limit": 2, "cursor": cursor, "ordering_version": "score-desc-record-id-asc-v1"}))
            self.assertEqual("success", second["outcome"])
            self.assertEqual(first["context"]["canonical_request_digest"], second["context"]["canonical_request_digest"])  # type: ignore[index]
            self.assertTrue(set(row["record_id"] for row in first["rows"]).isdisjoint(row["record_id"] for row in second["rows"]))  # type: ignore[index]

            changed_filter = {"eq": {"field": {"kind": "canonical", "name": "lifecycle_state"}, "value": "eligible"}}
            invalidated = core.execute(self._similarity_request(core, record_id=record_id, filter=changed_filter, pagination={"limit": 2, "cursor": cursor, "ordering_version": "score-desc-record-id-asc-v1"}))
            self.assertEqual("invalid_cursor", invalidated["error"]["code"])  # type: ignore[index]

    def test_valid_traversal_selector_returns_typed_unsupported_relation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core = self._core(Path(directory))
            record_id = core._release.read_table("records/genome-record-versions.jsonl")[0]["record_id"]
            assert isinstance(record_id, str)
            request = {
                "schema_version": "query-request/0.1.0",
                "release_selector": {"release_id": core._release.release_id, "release_digest": core._release.release_digest},
                "operation": "traversal",
                "profile_selector": None,
                "similarity": None,
                "traversal": {"start_record_ids": [record_id], "relation_type": "derived_from", "direction": "outgoing", "depth": 1},
            }
            result = core.execute(json.dumps(request))
            self.assertEqual("error", result["outcome"])
            self.assertEqual("unsupported_relation", result["error"]["code"])  # type: ignore[index]


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
