"""M2.2 ADR-010 verified local release adapter conformance."""

from __future__ import annotations

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

from expedia_atlas_builder.release_packaging import PROFILE_ID  # noqa: E402
from expedia_query_core.verified_release import (  # noqa: E402
    ReleaseVerificationFailure,
    open_verified_release,
)
from m1_draft_fixture import build_m1_draft_package  # noqa: E402


class VerifiedReleaseAdapterTests(unittest.TestCase):
    def _package(self, root: Path) -> Path:
        """Reuse the complete M1 Draft package fixture from reader conformance."""

        return build_m1_draft_package(root)

    def test_open_returns_an_immutable_manifest_addressed_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self._package(Path(directory))
            release = open_verified_release(package)

            self.assertEqual("Draft", release.state)
            self.assertEqual(12, len(release.read_table("records/genome-record-versions.jsonl")))
            self.assertGreater(release.artifact_count, 0)
            self.assertTrue(release.release_manifest_digest.startswith("sha256:"))
            self.assertEqual(release.release_manifest_digest, release.release_digest)
            self.assertEqual((PROFILE_ID,), release.vector_profiles)

            records = release.read_table("records/genome-record-versions.jsonl")
            with self.assertRaises(TypeError):
                records[0]["record_id"] = "changed"  # type: ignore[index]
            with self.assertRaises(TypeError):
                release.artifacts["records/genome-record-versions.jsonl"] = None  # type: ignore[index]
            with self.assertRaises(TypeError):
                release.vector_shard(PROFILE_ID).row_mapping["0"] = "changed"  # type: ignore[index]

    def test_snapshot_is_not_affected_by_later_package_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self._package(Path(directory))
            release = open_verified_release(package)
            original = release.vector_shard(PROFILE_ID).payload

            vector_path = package / "embeddings" / "vectors.float32le"
            changed = bytearray(vector_path.read_bytes())
            changed[0] ^= 0x01
            vector_path.write_bytes(changed)

            self.assertEqual(original, release.vector_shard(PROFILE_ID).payload)

    def test_changed_manifest_addressed_artifact_returns_typed_untrusted_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self._package(Path(directory))
            vector_path = package / "embeddings" / "vectors.float32le"
            changed = bytearray(vector_path.read_bytes())
            changed[0] ^= 0x01
            vector_path.write_bytes(changed)

            with self.assertRaises(ReleaseVerificationFailure) as raised:
                open_verified_release(package)
            self.assertEqual("release_untrusted", raised.exception.code)
            self.assertEqual("local release reader verification failed", raised.exception.message)

    def test_missing_package_returns_typed_not_found_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ReleaseVerificationFailure) as raised:
                open_verified_release(Path(directory) / "missing")
            self.assertEqual("release_not_found", raised.exception.code)

    def test_handle_only_reads_manifest_addressed_jsonl_tables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            release = open_verified_release(self._package(Path(directory)))
            with self.assertRaises(KeyError):
                release.read_table("not-in-manifest.jsonl")
            with self.assertRaises(ValueError):
                release.read_table("embeddings/vectors.float32le")


if __name__ == "__main__":
    unittest.main()
