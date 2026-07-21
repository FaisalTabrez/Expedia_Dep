from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "atlas-builder" / "src"))
sys.path.insert(0, str(ROOT / "schemas" / "python"))

from expedia_atlas_builder.embedding import VECTOR_DIMENSION  # noqa: E402
from expedia_atlas_builder.release_packaging import (  # noqa: E402
    ADEE_ID,
    PACKAGE_ENVELOPE_PATH,
    PROFILE_ID,
    PackageInputs,
    ReleasePackagingError,
    assemble_draft_package,
    verify_draft_package,
)
from expedia_contracts import ReleaseManifest  # noqa: E402


def sha256(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


class ReleasePackagingTests(unittest.TestCase):
    def _write_json(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")

    def _inputs(self, root: Path) -> PackageInputs:
        canonical = root / "canonical"
        canonical.mkdir()
        record_rows = []
        entity_rows = []
        instances = []
        vectors: list[float] = []
        for row in range(12):
            accession = f"GCF_{row:09d}.1"
            record_id = f"ncbi-assembly:{accession}:m1-assembly-canonical-v1"
            payload = f"CONTIG_{row}.1\tACGT\n".encode("ascii")
            (canonical / f"{accession}.txt").write_bytes(payload)
            record_rows.append({"record_id": record_id, "sequence_digest": sha256(payload), "canonicalization_id": "m1-assembly-canonical-v1", "lifecycle_state": "eligible"})
            entity_rows.append({"entity_id": f"ncbi-assembly:{accession}", "entity_type": "assembly", "record_versions": [record_id]})
            vectors.extend(1.0 if component == row else 0.0 for component in range(VECTOR_DIMENSION))
            instances.append({"instance_id": f"embedding:{record_id}:{PROFILE_ID}", "record_id": record_id, "profile_id": PROFILE_ID, "vector_reference": {"shard_id": "test-shard", "row": row, "shard_digest": "pending"}, "created_in": "test-build", "runner_provenance": {}, "eligibility_status": "eligible"})
        records = root / "genome-record-versions.jsonl"
        records.write_text("".join(json.dumps(row) + "\n" for row in record_rows), encoding="utf-8")
        entities = root / "atlas-entities.jsonl"
        entities.write_text("".join(json.dumps(row) + "\n" for row in entity_rows), encoding="utf-8")
        quarantines = root / "quarantines.jsonl"
        quarantines.write_text("", encoding="utf-8")
        vector_payload = struct.pack(f"<{12 * VECTOR_DIMENSION}f", *vectors)
        provenance = {
            "execution_environment_id": ADEE_ID,
            "execution_environment_declaration_digest": "sha256:test",
            "accelerator": "Tesla T4",
        }
        for instance in instances:
            instance["vector_reference"]["shard_digest"] = sha256(vector_payload)
            instance["runner_provenance"] = provenance
        bundle = root / "embedding.zip"
        with zipfile.ZipFile(bundle, "w") as archive:
            archive.writestr("vectors.float32le", vector_payload)
            archive.writestr("vector-shard-manifest.json", json.dumps({"profile_id": PROFILE_ID, "dimension": VECTOR_DIMENSION, "dtype": "float32", "digest": sha256(vector_payload), "build_provenance": {"runner_provenance": provenance}}))
            archive.writestr("embedding-instances.jsonl", "".join(json.dumps(item) + "\n" for item in instances))
            archive.writestr("embedding-stage-envelope.json", json.dumps({"stage_id": "embed", "outcome": "succeeded", "verification": {"runner_provenance": provenance}}))
        source = root / "source-provenance.json"
        inventory = root / "inventory.json"
        acquisition = root / "acquisition.json"
        canonicalization = root / "canonicalization.json"
        build = root / "build.json"
        profile = root / "profile.yaml"
        plugin = root / "plugin.json"
        environment = root / "environment.json"
        license_notice = root / "license.md"
        evidence = root / "evidence.md"
        for path in (source, inventory, acquisition, canonicalization, build, plugin, environment):
            self._write_json(path, {"id": path.stem})
        profile.write_text("profile_id: test\n", encoding="utf-8")
        license_notice.write_text("MIT\n", encoding="utf-8")
        evidence.write_text("validation evidence\n", encoding="utf-8")
        schemas = root / "schemas"
        schemas.mkdir()
        (schemas / "release-manifest.schema.json").write_text("{}", encoding="utf-8")
        (schemas / "CONTRACT-CATALOGUE.md").write_text("catalogue\n", encoding="utf-8")
        return PackageInputs(bundle, records, entities, quarantines, canonical, source, inventory, acquisition, canonicalization, build, profile, plugin, environment, license_notice, evidence, schemas)

    def test_assembles_a_complete_draft_package_and_contract_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "draft"
            manifest_path = assemble_draft_package(
                inputs=self._inputs(root),
                release_directory=package,
                release_id="expedia-m1-draft-test-v1",
                created_at="2026-07-21T00:00:00Z",
            )
            manifest = verify_draft_package(package)
            schema = json.loads((ROOT / "schemas" / "json" / "release-manifest.schema.json").read_text())

            Draft202012Validator(schema).validate(manifest)
            self.assertEqual("Draft", manifest["state"])
            self.assertEqual("not assigned", manifest["citation"]["status"])
            self.assertTrue(manifest_path.is_file())
            self.assertIn(PACKAGE_ENVELOPE_PATH, {item["path"] for item in manifest["artifacts"]})
            self.assertNotIn("release-manifest.json", {item["path"] for item in manifest["artifacts"]})
            self.assertEqual(ReleaseManifest.from_json(manifest_path.read_text()).to_dict(), manifest)

    def test_rejects_a_changed_payload_after_assembly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "draft"
            assemble_draft_package(
                inputs=self._inputs(root),
                release_directory=package,
                release_id="expedia-m1-draft-test-v1",
                created_at="2026-07-21T00:00:00Z",
            )
            vector_path = package / "embeddings" / "vectors.float32le"
            payload = bytearray(vector_path.read_bytes())
            payload[0] ^= 0x01
            vector_path.write_bytes(payload)
            with self.assertRaisesRegex(ReleasePackagingError, "integrity mismatch"):
                verify_draft_package(package)

    def test_rejects_an_embedding_bundle_missing_a_required_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = self._inputs(root)
            with zipfile.ZipFile(inputs.embedding_artifacts_zip, "w") as archive:
                archive.writestr("vectors.float32le", b"")
            with self.assertRaisesRegex(ReleasePackagingError, "unexpected file inventory"):
                assemble_draft_package(
                    inputs=inputs,
                    release_directory=root / "draft",
                    release_id="expedia-m1-draft-test-v1",
                    created_at="2026-07-21T00:00:00Z",
                )


if __name__ == "__main__":
    unittest.main()
