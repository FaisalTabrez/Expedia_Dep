"""Controlled M1 Draft successor correction conformance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "contract"))
sys.path.insert(0, str(ROOT / "atlas-builder" / "src"))
sys.path.insert(0, str(ROOT / "validation" / "src"))

from expedia_atlas_builder.release_packaging import PACKAGE_ENVELOPE_PATH  # noqa: E402
from expedia_atlas_builder.release_successor import (  # noqa: E402
    PROFILE_RECORD_PATH,
    create_m1_profile_successor,
)
from expedia_validation.release_reader import ReleaseReaderError, read_release  # noqa: E402
from m1_draft_fixture import build_m1_draft_package  # noqa: E402


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class M1ProfileSuccessorTests(unittest.TestCase):
    def test_successor_preserves_predecessor_payloads_and_binds_profile_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            predecessor = build_m1_draft_package(root / "predecessor")
            successor = root / "successor"
            profile = ROOT / "profiles" / "embedding" / "m1-generanno-prokaryote-0.5b-assembly-v1.json"

            result = create_m1_profile_successor(
                predecessor_package=predecessor,
                profile_record=profile,
                successor_package=successor,
                successor_release_id="expedia-m1-draft-successor-test-v1",
                created_at="2026-07-21T06:00:00Z",
            )

            self.assertEqual("expedia-m1-draft-reader-test-v1", result.predecessor_release_id)
            self.assertEqual("expedia-m1-draft-successor-test-v1", result.successor_release_id)
            self.assertEqual(result.preserved_artifact_count + 2, result.successor_artifact_count)
            self.assertEqual(sha256_file(profile), result.profile_record_digest)

            predecessor_manifest = json.loads((predecessor / "release-manifest.json").read_text())
            successor_manifest = json.loads((successor / "release-manifest.json").read_text())
            self.assertEqual("expedia-m1-draft-reader-test-v1", successor_manifest["base_release"])
            predecessor_descriptors = {item["path"]: item for item in predecessor_manifest["artifacts"]}
            successor_descriptors = {item["path"]: item for item in successor_manifest["artifacts"]}
            self.assertEqual(len(predecessor_descriptors) - 1, result.preserved_artifact_count)
            self.assertEqual(len(predecessor_descriptors) + 1, result.successor_artifact_count)
            for path, descriptor in predecessor_descriptors.items():
                if path != PACKAGE_ENVELOPE_PATH:
                    self.assertEqual(descriptor, successor_descriptors[path])
            self.assertIn(PROFILE_RECORD_PATH, successor_descriptors)
            self.assertEqual(result.profile_record_digest, successor_descriptors[PROFILE_RECORD_PATH]["digest"])

            profile_schema = json.loads((ROOT / "schemas" / "json" / "embedding-profile.schema.json").read_text())
            Draft202012Validator(profile_schema).validate(json.loads((successor / PROFILE_RECORD_PATH).read_text()))
            reader_result = read_release(successor)
            self.assertEqual(result.successor_manifest_digest, reader_result["release_manifest_digest"])

    def test_reader_rejects_a_successor_profile_that_does_not_match_the_frozen_representation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            predecessor = build_m1_draft_package(root / "predecessor")
            bad_profile = root / "bad-profile.json"
            source = json.loads((ROOT / "profiles" / "embedding" / "m1-generanno-prokaryote-0.5b-assembly-v1.json").read_text())
            source["version"] = "2.0.0"
            bad_profile.write_text(json.dumps(source), encoding="utf-8")
            successor = root / "successor"
            create_m1_profile_successor(
                predecessor_package=predecessor,
                profile_record=bad_profile,
                successor_package=successor,
                successor_release_id="expedia-m1-draft-successor-invalid-profile-v1",
                created_at="2026-07-21T06:00:00Z",
            )
            with self.assertRaisesRegex(ReleaseReaderError, "EmbeddingProfile declaration does not match"):
                read_release(successor)

    def test_committed_correction_evidence_binds_the_authoritative_successor(self) -> None:
        profile = ROOT / "profiles" / "embedding" / "m1-generanno-prokaryote-0.5b-assembly-v1.json"
        profile_schema = json.loads((ROOT / "schemas" / "json" / "embedding-profile.schema.json").read_text())
        Draft202012Validator(profile_schema).validate(json.loads(profile.read_text()))
        self.assertEqual(
            "sha256:5679461d5a4482b48b90e97615d9661e84c2ac7c3b01253e7be4d7909a294294",
            sha256_file(profile),
        )

        approval = json.loads((ROOT / "validation" / "evidence" / "m1-profile-successor-correction-approval-2026-07-21.json").read_text())
        approval_schema = json.loads((ROOT / "schemas" / "json" / "approval-record.schema.json").read_text())
        Draft202012Validator(approval_schema).validate(approval)
        self.assertEqual("expedia-m1-draft-20260721-v3", approval["subject_id"])

        index = (ROOT / "validation" / "evidence" / "m1-evidence-index.md").read_text()
        self.assertIn("**Release ID:** `expedia-m1-draft-20260721-v3`", index)
        self.assertIn("v2 as historical evidence", index)
        self.assertIn("authoritative M1 Draft input for\nsubsequent M2", index)


if __name__ == "__main__":
    unittest.main()
