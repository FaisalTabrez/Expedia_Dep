"""M2.6 proof that Explorer consumes, rather than recreates, QueryResult data."""

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
sys.path.insert(0, str(ROOT / "sdk" / "src"))
sys.path.insert(0, str(ROOT / "explorer" / "src"))

from expedia_atlas_builder.release_successor import create_m1_profile_successor  # noqa: E402
from expedia_explorer import ProvenanceExplorer  # noqa: E402
from expedia_query_core.exact_cosine import ExactCosineQueryCore  # noqa: E402
from expedia_query_core.verified_release import open_verified_release  # noqa: E402
from expedia_sdk import LocalExpediaClient  # noqa: E402
from m1_draft_fixture import build_m1_draft_package  # noqa: E402


PROFILE_ID = "m1-generanno-prokaryote-0.5b-assembly-v1"


class M26ExplorerConformanceTests(unittest.TestCase):
    def _components(self, root: Path) -> tuple[ExactCosineQueryCore, LocalExpediaClient, ProvenanceExplorer]:
        predecessor = build_m1_draft_package(root / "predecessor")
        successor = root / "successor"
        create_m1_profile_successor(
            predecessor_package=predecessor,
            profile_record=ROOT / "profiles" / "embedding" / f"{PROFILE_ID}.json",
            successor_package=successor,
            successor_release_id="expedia-m1-draft-m2-6-test-v3",
            created_at="2026-07-21T12:00:00Z",
        )
        core = ExactCosineQueryCore(open_verified_release(successor))
        sdk = LocalExpediaClient(core)
        return core, sdk, ProvenanceExplorer(sdk.query)

    @staticmethod
    def _request(core: ExactCosineQueryCore, record_id: str, **changes: object) -> dict[str, object]:
        release = core._release  # Test-only snapshot access.
        request: dict[str, object] = {
            "schema_version": "query-request/0.1.0",
            "release_selector": {"release_id": release.release_id, "release_digest": release.release_digest},
            "operation": "similarity",
            "profile_selector": {"profile_id": PROFILE_ID, "profile_version": "1.0.0"},
            "similarity": {"query_record_id": record_id, "metric": "cosine", "mode": "exact"},
        }
        request.update(changes)
        return request

    def test_explorer_preserves_core_rows_context_and_evidence_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core, sdk, explorer = self._components(Path(directory))
            record_id = core._release.read_table("records/genome-record-versions.jsonl")[2]["record_id"]
            assert isinstance(record_id, str)
            request = self._request(core, record_id, pagination={"limit": 2, "cursor": None, "ordering_version": "score-desc-record-id-asc-v1"})
            core_result = sdk.query(request)
            presented = explorer.query_and_present(request)
            direct_presentation = explorer.present_result(core_result)
            self.assertEqual(direct_presentation, presented)
            self.assertEqual("query-result", presented["presentation_kind"])
            self.assertEqual(core_result["context"]["release_digest"], presented["release"]["release_digest"])  # type: ignore[index]
            self.assertEqual(core_result["context"]["profile_id"], presented["query_context"]["profile_id"])  # type: ignore[index]
            self.assertEqual([row["record_id"] for row in core_result["rows"]], [row["record_id"] for row in presented["rows"]])  # type: ignore[index]
            self.assertTrue(all(row["kind"] == "canonical-record" for row in presented["rows"]))  # type: ignore[index]
            self.assertEqual("not-returned-by-query-result", presented["annotation_assertions"])
            self.assertEqual("not-returned-by-query-result", presented["relation_lineage"])
            self.assertEqual("method_not_evaluated", presented["warnings"][0]["code"])  # type: ignore[index]

    def test_explorer_preserves_typed_core_errors_without_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core, sdk, explorer = self._components(Path(directory))
            record_id = core._release.read_table("records/genome-record-versions.jsonl")[0]["record_id"]
            assert isinstance(record_id, str)
            request = self._request(core, record_id, filter={"eq": {"field": {"kind": "annotation", "source": "test", "predicate": "flag"}, "value": True}})
            result = sdk.query(request)
            presented = explorer.present_result(result)
            self.assertEqual("typed-query-error", presented["presentation_kind"])
            self.assertEqual(result["error"], presented["error"])
            self.assertIn("did not alter", presented["evidence_note"])

    def test_release_context_is_displayed_only_when_supplied_by_a_trusted_caller(self) -> None:
        explorer = ProvenanceExplorer()
        view = explorer.present_release(
            {
                "release_id": "draft",
                "release_digest": "sha256:" + "a" * 64,
                "scope": "internal Draft",
                "citation": "not citable",
                "compatibility": "profile-declared",
                "integrity": "verified",
            }
        )
        self.assertEqual("release-context", view["presentation_kind"])
        self.assertEqual("verified", view["release"]["integrity"])  # type: ignore[index]

    def test_explorer_source_contains_no_query_core_semantics(self) -> None:
        source = (ROOT / "explorer" / "src" / "expedia_explorer" / "presenter.py").read_text(encoding="utf-8")
        for forbidden in ("open_verified_release", "ExactCosineQueryCore", "evaluate_filter", "encode_cursor", ".execute("):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
