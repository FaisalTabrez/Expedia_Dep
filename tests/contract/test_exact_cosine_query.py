"""M2.3 ADR-011 exact-cosine reference conformance."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "contract"))
sys.path.insert(0, str(ROOT / "atlas-builder" / "src"))
sys.path.insert(0, str(ROOT / "schemas" / "python"))
sys.path.insert(0, str(ROOT / "validation" / "src"))
sys.path.insert(0, str(ROOT / "query-core" / "src"))

from expedia_atlas_builder.release_successor import create_m1_profile_successor  # noqa: E402
from expedia_query_core.exact_cosine import ExactCosineQueryCore  # noqa: E402
from expedia_query_core.verified_release import open_verified_release  # noqa: E402
from m1_draft_fixture import build_m1_draft_package  # noqa: E402


PROFILE_ID = "m1-generanno-prokaryote-0.5b-assembly-v1"
PROFILE_VERSION = "1.0.0"


def _registry() -> Registry:
    registry = Registry()
    for schema_path in (ROOT / "schemas" / "json").glob("*.schema.json"):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry


class ExactCosineQueryTests(unittest.TestCase):
    def _core(self, root: Path) -> ExactCosineQueryCore:
        predecessor = build_m1_draft_package(root / "predecessor")
        successor = root / "successor"
        create_m1_profile_successor(
            predecessor_package=predecessor,
            profile_record=ROOT / "profiles" / "embedding" / f"{PROFILE_ID}.json",
            successor_package=successor,
            successor_release_id="expedia-m1-draft-m2-3-test-v3",
            created_at="2026-07-21T08:00:00Z",
        )
        return ExactCosineQueryCore(open_verified_release(successor))

    @staticmethod
    def _request(core: ExactCosineQueryCore, *, record_id: str, **overrides: object) -> str:
        release = core._release  # Test-only access to the immutable, verified fixture snapshot.
        request: dict[str, object] = {
            "schema_version": "query-request/0.1.0",
            "release_selector": {"release_id": release.release_id, "release_digest": release.release_digest},
            "operation": "similarity",
            "profile_selector": {"profile_id": PROFILE_ID, "profile_version": PROFILE_VERSION},
            "similarity": {"query_record_id": record_id, "metric": "cosine", "mode": "exact"},
        }
        request.update(overrides)
        return json.dumps(request)

    def test_exact_cosine_uses_v3_profile_and_returns_contract_valid_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core = self._core(Path(directory))
            records = core._release.read_table("records/genome-record-versions.jsonl")
            query_id = records[3]["record_id"]
            assert isinstance(query_id, str)
            result = core.execute(self._request(core, record_id=query_id))

            Draft202012Validator(
                json.loads((ROOT / "schemas" / "json" / "query-result.schema.json").read_text()),
                registry=_registry(),
            ).validate(result)
            self.assertEqual("success", result["outcome"])
            self.assertEqual("exact", result["context"]["mode"])  # type: ignore[index]
            self.assertEqual("higher-is-more-similar", result["context"]["metric_direction"])  # type: ignore[index]
            self.assertEqual(PROFILE_VERSION, result["provenance"]["profile_version"])  # type: ignore[index]
            self.assertEqual(core._release.embedding_profile(PROFILE_ID).digest, result["provenance"]["profile_digest"])  # type: ignore[index]
            self.assertEqual(core._release.vector_shard(PROFILE_ID).digest, result["provenance"]["vector_shard_digest"])  # type: ignore[index]
            self.assertEqual(query_id, result["rows"][0]["record_id"])  # type: ignore[index]
            self.assertEqual(1.0, result["rows"][0]["score"])  # type: ignore[index]
            self.assertEqual(
                sorted(row["record_id"] for row in records if row["record_id"] != query_id),
                [row["record_id"] for row in result["rows"][1:]],  # type: ignore[index]
            )

    def test_equivalent_request_serializations_have_identical_exact_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core = self._core(Path(directory))
            record_id = core._release.read_table("records/genome-record-versions.jsonl")[6]["record_id"]
            assert isinstance(record_id, str)
            first = core.execute(self._request(core, record_id=record_id))
            second = core.execute(json.dumps(json.loads(self._request(core, record_id=record_id)), indent=2, sort_keys=True))
            self.assertEqual(first, second)

    def test_m2_3_rejects_unimplemented_filter_cursor_and_profile_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core = self._core(Path(directory))
            record_id = core._release.read_table("records/genome-record-versions.jsonl")[0]["record_id"]
            assert isinstance(record_id, str)
            cases = (
                ({"filter": {"state": "eligible"}}, "unsupported_filter"),
                ({"pagination": {"limit": 12, "cursor": "opaque", "ordering_version": "score-desc-record-id-asc-v1"}}, "invalid_cursor"),
                ({"profile_selector": {"profile_id": PROFILE_ID, "profile_version": "9.0.0"}}, "profile_incompatible"),
                ({"release_selector": {"release_id": "different", "release_digest": core._release.release_digest}}, "release_not_found"),
            )
            for overrides, expected_code in cases:
                with self.subTest(expected_code=expected_code):
                    result = core.execute(self._request(core, record_id=record_id, **overrides))
                    self.assertEqual("error", result["outcome"])
                    self.assertEqual(expected_code, result["error"]["code"])  # type: ignore[index]

    def test_reference_executor_contains_no_ann_or_faiss_path(self) -> None:
        source = (ROOT / "query-core" / "src" / "expedia_query_core" / "exact_cosine.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("import faiss", source)
        self.assertNotIn("import hnsw", source)
        self.assertNotIn("index_factory", source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
