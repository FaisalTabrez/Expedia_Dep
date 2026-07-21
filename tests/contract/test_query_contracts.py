"""M2.1 canonical QueryRequest and OQ-11 cost-limit conformance."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "query-core" / "src"))

from expedia_query_core.query_contracts import QueryContractError, canonicalize_query_request_json


def _request(filter_expression: object | None = None) -> dict[str, object]:
    request: dict[str, object] = {
        "schema_version": "query-request/0.1.0",
        "release_selector": {
            "release_id": "expedia-m1-draft-20260721-v2",
            "release_digest": "sha256:66a0ff36d1a15c05de74fb8f66bbc02030172bf8b9d8324a0c919bd964c3f583",
        },
        "operation": "similarity",
        "profile_selector": {"profile_id": "generanno-reference", "profile_version": "1.0.0"},
        "similarity": {"query_record_id": "GCF_000005845.2", "metric": "cosine", "mode": "exact"},
    }
    if filter_expression is not None:
        request["filter"] = filter_expression
    return request


class QueryContractTests(unittest.TestCase):
    def test_formatting_member_order_and_default_pagination_do_not_change_digest(self) -> None:
        field = {"kind": "canonical", "name": "record_id"}
        request = _request({"in": {"field": field, "values": ["b", "a"]}})
        left = canonicalize_query_request_json(json.dumps(request, indent=2))
        reordered = {
            "similarity": request["similarity"],
            "operation": request["operation"],
            "filter": {"in": {"values": ["a", "b"], "field": field}},
            "release_selector": request["release_selector"],
            "profile_selector": request["profile_selector"],
            "schema_version": request["schema_version"],
            "pagination": {"ordering_version": "score-desc-record-id-asc-v1", "cursor": None, "limit": 12},
        }
        right = canonicalize_query_request_json(json.dumps(reordered, separators=(",", ":")))
        self.assertEqual(left.canonical_json, right.canonical_json)
        self.assertEqual(left.digest, right.digest)

    def test_boolean_filter_order_is_semantic_order_independent(self) -> None:
        record = {"kind": "canonical", "name": "record_id"}
        lifecycle = {"kind": "canonical", "name": "lifecycle_state"}
        left = canonicalize_query_request_json(json.dumps(_request({"all": [{"eq": {"field": record, "value": "a"}}, {"eq": {"field": lifecycle, "value": "active"}}]})))
        right = canonicalize_query_request_json(json.dumps(_request({"all": [{"eq": {"value": "active", "field": lifecycle}}, {"eq": {"value": "a", "field": record}}]})))
        self.assertEqual(left.digest, right.digest)

    def test_equivalent_numeric_spellings_have_one_canonical_interpretation(self) -> None:
        field = {"kind": "canonical", "name": "record_id"}
        left = canonicalize_query_request_json(json.dumps(_request({"range": {"field": field, "gte": 1.0, "lte": 2.00, "unit": "ordinal"}})))
        right = canonicalize_query_request_json(json.dumps(_request({"range": {"field": field, "gte": 1, "lte": 2, "unit": "ordinal"}})))
        self.assertEqual(left.digest, right.digest)

    def test_duplicate_json_member_is_rejected(self) -> None:
        with self.assertRaisesRegex(QueryContractError, "duplicate JSON object member"):
            canonicalize_query_request_json('{"schema_version":"query-request/0.1.0","schema_version":"query-request/0.1.0"}')

    def test_duplicate_semantic_filter_values_are_deduplicated(self) -> None:
        field = {"kind": "canonical", "name": "record_id"}
        duplicated = canonicalize_query_request_json(json.dumps(_request({"in": {"field": field, "values": ["a", "a"]}})))
        unique = canonicalize_query_request_json(json.dumps(_request({"in": {"field": field, "values": ["a"]}})))
        self.assertEqual(duplicated.digest, unique.digest)

    def test_filter_cost_limits_are_enforced(self) -> None:
        field = {"kind": "canonical", "name": "record_id"}
        too_many = {"all": [{"eq": {"field": field, "value": str(index)}} for index in range(33)]}
        with self.assertRaisesRegex(QueryContractError, "32 predicate"):
            canonicalize_query_request_json(json.dumps(_request(too_many)))

        nested: object = {"eq": {"field": field, "value": "a"}}
        for _ in range(8):
            nested = {"not": nested}
        with self.assertRaisesRegex(QueryContractError, "depth 8"):
            canonicalize_query_request_json(json.dumps(_request(nested)))

        with self.assertRaisesRegex(QueryContractError, "membership exceeds 100"):
            canonicalize_query_request_json(json.dumps(_request({"in": {"field": field, "values": list(map(str, range(101)))}})))

        with self.assertRaisesRegex(QueryContractError, "exceeds 16 KiB"):
            canonicalize_query_request_json(json.dumps(_request({"eq": {"field": field, "value": "x" * 17_000}})))

    def test_false_state_is_preserved_in_the_canonical_interpretation(self) -> None:
        state = {"state": {"field": {"kind": "canonical", "name": "lifecycle_state"}, "is": "false"}}
        canonical = canonicalize_query_request_json(json.dumps(_request(state)))
        self.assertIn('"is":"false"', canonical.canonical_json)


if __name__ == "__main__":
    unittest.main()
