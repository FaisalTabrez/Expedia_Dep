"""M3-002 oracle verification without executing a Query Core comparison."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
from types import MappingProxyType
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "contract"))
sys.path.insert(0, str(ROOT / "atlas-builder" / "src"))
sys.path.insert(0, str(ROOT / "schemas" / "python"))
sys.path.insert(0, str(ROOT / "validation" / "src"))
sys.path.insert(0, str(ROOT / "validation" / "reference"))

from expedia_atlas_builder.release_successor import create_m1_profile_successor  # noqa: E402
from m1_draft_fixture import build_m1_draft_package  # noqa: E402
from m3_002_float32_cosine import (  # noqa: E402
    ReferenceBinding,
    ReferenceInputError,
    IndependentReferenceRelease,
    _float32_inner_product,
    _round_float32,
    load_reference_release,
)


PROFILE_ID = "m1-generanno-prokaryote-0.5b-assembly-v1"


def _digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _binding(package: Path) -> ReferenceBinding:
    manifest = json.loads((package / "release-manifest.json").read_text(encoding="utf-8"))
    profile = json.loads((package / "profiles" / f"{PROFILE_ID}.json").read_text(encoding="utf-8"))
    return ReferenceBinding(
        release_id=manifest["release_id"],
        release_digest=_digest(package / "release-manifest.json"),
        profile_id=profile["profile_id"],
        profile_version=profile["version"],
        profile_digest=_digest(package / "profiles" / f"{PROFILE_ID}.json"),
        vector_shard_digest=_digest(package / "embeddings" / "vectors.float32le"),
        expected_record_count=12,
    )


class M3002ReferenceOracleTests(unittest.TestCase):
    def _package(self, root: Path) -> Path:
        predecessor = build_m1_draft_package(root / "predecessor")
        successor = root / "successor"
        create_m1_profile_successor(
            predecessor_package=predecessor,
            profile_record=ROOT / "profiles" / "embedding" / f"{PROFILE_ID}.json",
            successor_package=successor,
            successor_release_id="expedia-m3-002-reference-oracle-test-v3",
            created_at="2026-07-21T08:00:00Z",
        )
        return successor

    def test_oracle_loads_verified_inputs_and_emits_only_reference_projection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self._package(Path(directory))
            reference = load_reference_release(package, binding=_binding(package))
            query_record_id = reference.record_ids[0]
            result = reference.comparison_object(
                query_record_id=query_record_id,
                canonical_request_digest="sha256:" + "a" * 64,
            )

            self.assertEqual(
                {
                    "canonical_request_digest",
                    "ordered_record_ids",
                    "decoded_float32_scores",
                    "provenance",
                },
                set(result),
            )
            self.assertEqual(12, len(result["ordered_record_ids"]))
            self.assertEqual(12, len(result["decoded_float32_scores"]))
            self.assertEqual(query_record_id, result["ordered_record_ids"][0])
            self.assertEqual(1.0, result["decoded_float32_scores"][0])
            self.assertEqual("score-desc-record-id-asc-v1", result["provenance"]["ordering_version"])

    def test_oracle_rejects_a_binding_that_differs_from_the_verified_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self._package(Path(directory))
            binding = _binding(package)
            invalid = ReferenceBinding(
                release_id=binding.release_id,
                release_digest=binding.release_digest,
                profile_id=binding.profile_id,
                profile_version="9.0.0",
                profile_digest=binding.profile_digest,
                vector_shard_digest=binding.vector_shard_digest,
                expected_record_count=binding.expected_record_count,
            )
            with self.assertRaises(ReferenceInputError):
                load_reference_release(package, binding=invalid)

    def test_local_binary32_primitive_rounds_every_product_and_accumulation(self) -> None:
        left = (_round_float32(0.1), _round_float32(0.2), _round_float32(0.3))
        right = (_round_float32(0.4), _round_float32(0.5), _round_float32(0.6))
        expected = 0.0
        for left_value, right_value in zip(left, right, strict=True):
            expected = _round_float32(expected + _round_float32(left_value * right_value))
        self.assertEqual(expected, _float32_inner_product(left, right))

    def test_oracle_orders_equal_scores_by_ascending_record_id(self) -> None:
        binding = ReferenceBinding(
            release_id="fixture-release",
            release_digest="sha256:" + "b" * 64,
            profile_id="fixture-profile",
            profile_version="1.0.0",
            profile_digest="sha256:" + "c" * 64,
            vector_shard_digest="sha256:" + "d" * 64,
            expected_record_count=3,
        )
        reference = IndependentReferenceRelease(
            binding=binding,
            record_ids=("record:b", "record:a", "record:c"),
            vectors_by_record_id=MappingProxyType(
                {
                    "record:a": (1.0, 0.0),
                    "record:b": (1.0, 0.0),
                    "record:c": (0.0, 1.0),
                }
            ),
        )
        result = reference.comparison_object(
            query_record_id="record:b",
            canonical_request_digest="sha256:" + "e" * 64,
        )
        self.assertEqual(["record:a", "record:b", "record:c"], result["ordered_record_ids"])
        self.assertEqual([1.0, 1.0, 0.0], result["decoded_float32_scores"])

    def test_oracle_source_does_not_import_query_core(self) -> None:
        source = (ROOT / "validation" / "reference" / "m3_002_float32_cosine.py").read_text(encoding="utf-8")
        self.assertNotIn("expedia_query_core", source)
        self.assertNotIn("ExactCosineQueryCore", source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
