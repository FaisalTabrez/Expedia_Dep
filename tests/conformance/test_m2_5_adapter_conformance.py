"""M2.5 proof that Core, SDK, and REST retain one query interpretation."""

from __future__ import annotations

from io import BytesIO
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
sys.path.insert(0, str(ROOT / "api" / "src"))

from expedia_api import V1QueryApplication  # noqa: E402
from expedia_atlas_builder.release_successor import create_m1_profile_successor  # noqa: E402
from expedia_query_core.exact_cosine import ExactCosineQueryCore  # noqa: E402
from expedia_query_core.verified_release import open_verified_release  # noqa: E402
from expedia_sdk import LocalExpediaClient  # noqa: E402
from m1_draft_fixture import build_m1_draft_package  # noqa: E402


PROFILE_ID = "m1-generanno-prokaryote-0.5b-assembly-v1"


def _rest_query(app: V1QueryApplication, request: dict[str, object]) -> tuple[str, dict[str, object]]:
    body = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    observed: dict[str, object] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        observed["status"] = status
        observed["headers"] = headers

    response = b"".join(
        app(
            {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/v1/query",
                "CONTENT_LENGTH": str(len(body)),
                "wsgi.input": BytesIO(body),
            },
            start_response,
        )
    )
    return str(observed["status"]), json.loads(response.decode("utf-8"))


class M25AdapterConformanceTests(unittest.TestCase):
    def _adapters(self, root: Path) -> tuple[ExactCosineQueryCore, LocalExpediaClient, V1QueryApplication]:
        predecessor = build_m1_draft_package(root / "predecessor")
        successor = root / "successor"
        create_m1_profile_successor(
            predecessor_package=predecessor,
            profile_record=ROOT / "profiles" / "embedding" / f"{PROFILE_ID}.json",
            successor_package=successor,
            successor_release_id="expedia-m1-draft-m2-5-test-v3",
            created_at="2026-07-21T11:00:00Z",
        )
        core = ExactCosineQueryCore(open_verified_release(successor))
        return core, LocalExpediaClient(core), V1QueryApplication(core)

    @staticmethod
    def _request(core: ExactCosineQueryCore, *, record_id: str, **changes: object) -> dict[str, object]:
        release = core._release  # Test-only immutable trusted snapshot access.
        request: dict[str, object] = {
            "schema_version": "query-request/0.1.0",
            "release_selector": {"release_id": release.release_id, "release_digest": release.release_digest},
            "operation": "similarity",
            "profile_selector": {"profile_id": PROFILE_ID, "profile_version": "1.0.0"},
            "similarity": {"query_record_id": record_id, "metric": "cosine", "mode": "exact"},
            "filter": {"eq": {"field": {"kind": "canonical", "name": "lifecycle_state"}, "value": "eligible"}},
            "pagination": {"limit": 2, "cursor": None, "ordering_version": "score-desc-record-id-asc-v1"},
        }
        request.update(changes)
        return request

    @staticmethod
    def _core_query(core: ExactCosineQueryCore, request: dict[str, object]) -> dict[str, object]:
        return dict(core.execute(json.dumps(request, ensure_ascii=False, separators=(",", ":"))))

    def _assert_equivalent(self, core: ExactCosineQueryCore, sdk: LocalExpediaClient, rest: V1QueryApplication, request: dict[str, object]) -> dict[str, object]:
        core_result = self._core_query(core, request)
        sdk_result = dict(sdk.query(request))
        status, rest_result = _rest_query(rest, request)
        self.assertEqual("200 OK", status)
        self.assertEqual(core_result, sdk_result)
        self.assertEqual(core_result, rest_result)
        return core_result

    def test_success_error_and_cursor_corpus_is_identical_across_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core, sdk, rest = self._adapters(Path(directory))
            record_id = core._release.read_table("records/genome-record-versions.jsonl")[7]["record_id"]
            assert isinstance(record_id, str)

            first = self._assert_equivalent(core, sdk, rest, self._request(core, record_id=record_id))
            cursor = first["next_cursor"]
            assert isinstance(cursor, str)
            self._assert_equivalent(
                core,
                sdk,
                rest,
                self._request(core, record_id=record_id, pagination={"limit": 2, "cursor": cursor, "ordering_version": "score-desc-record-id-asc-v1"}),
            )
            unsupported = self._assert_equivalent(
                core,
                sdk,
                rest,
                self._request(core, record_id=record_id, filter={"eq": {"field": {"kind": "annotation", "source": "test", "predicate": "flag"}, "value": True}}),
            )
            self.assertEqual("unsupported_filter", unsupported["error"]["code"])  # type: ignore[index]

    def test_adapters_do_not_implement_release_or_query_semantics(self) -> None:
        sdk_source = (ROOT / "sdk" / "src" / "expedia_sdk" / "client.py").read_text(encoding="utf-8")
        rest_source = (ROOT / "api" / "src" / "expedia_api" / "v1.py").read_text(encoding="utf-8")
        for source in (sdk_source, rest_source):
            self.assertIn(".execute(", source)
            self.assertNotIn("open_verified_release", source)
            self.assertNotIn("evaluate_filter", source)
            self.assertNotIn("encode_cursor", source)

    def test_openapi_declares_only_the_versioned_query_transport(self) -> None:
        openapi = (ROOT / "api" / "openapi" / "v1" / "openapi.yaml").read_text(encoding="utf-8")
        self.assertIn("/v1/query:", openapi)
        self.assertIn("query-request.schema.json", openapi)
        self.assertIn("query-result.schema.json", openapi)
        self.assertNotIn("placeholder", openapi)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
