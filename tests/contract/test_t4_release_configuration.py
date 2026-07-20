from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "atlas-builder" / "src"))

from expedia_atlas_builder.t4_release import (  # noqa: E402
    ADEE_ID,
    T4ReleaseError,
    load_approved_t4_environment,
    validate_release_build_manifest,
)


class T4ReleaseConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.declaration_path = ROOT / "profiles" / "environments" / f"{ADEE_ID}.json"
        self.manifest_path = ROOT / "atlas-builder" / "manifests" / "m1" / "m1-build-manifest.t4-release.json"

    def test_approved_environment_is_explicitly_selected_by_a_schema_valid_manifest(self) -> None:
        environment = load_approved_t4_environment(self.declaration_path)
        build_id, record_table_digest = validate_release_build_manifest(self.manifest_path, environment)
        manifest = json.loads(self.manifest_path.read_text())
        schema = json.loads((ROOT / "schemas" / "json" / "build-manifest.schema.json").read_text())

        Draft202012Validator(schema).validate(manifest)
        self.assertEqual("m1-t4-release-build-v1", build_id)
        self.assertEqual("sha256:1d711c8d67b88ce4da9907933d67208eac3c2d0487cd49ceab2443c17f0beb48", record_table_digest)
        self.assertEqual(ADEE_ID, manifest["plugins"][0]["execution_environment"]["id"])
        self.assertEqual(environment.declaration_digest, manifest["plugins"][0]["execution_environment"]["declaration_digest"])

    def test_manifest_rejects_an_unpinned_or_different_execution_environment(self) -> None:
        environment = load_approved_t4_environment(self.declaration_path)
        payload = json.loads(self.manifest_path.read_text())
        payload["plugins"][0]["execution_environment"]["declaration_digest"] = "sha256:" + "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(T4ReleaseError, "does not match"):
                validate_release_build_manifest(path, environment)

    def test_release_adapter_uses_the_builder_stage_not_the_validation_harness(self) -> None:
        source = (ROOT / "atlas-builder" / "src" / "expedia_atlas_builder" / "t4_release.py").read_text()
        self.assertIn("execute_embedding_stage(", source)
        self.assertNotIn("m1_t4_validation", source)
        self.assertIn('"execution_environment_declaration_digest"', source)


if __name__ == "__main__":
    unittest.main()
