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
sys.path.insert(0, str(ROOT / "validation" / "src"))

from expedia_atlas_builder.release_packaging import (  # noqa: E402
    ADEE_ID,
    PROFILE_ID,
    PackageInputs,
    assemble_draft_package,
)
from expedia_validation.release_reader import (  # noqa: E402
    ReleaseReaderError,
    read_release,
    write_validation_evidence,
)


def sha256(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


class ReleaseReaderTests(unittest.TestCase):
    def _json(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")

    def _package(self, root: Path) -> Path:
        canonical = root / "canonical"
        canonical.mkdir()
        records: list[dict[str, object]] = []
        entities: list[dict[str, object]] = []
        instances: list[dict[str, object]] = []
        vectors: list[float] = []
        for row in range(12):
            accession = f"GCF_{row:09d}.1"
            record_id = f"ncbi-assembly:{accession}:m1-assembly-canonical-v1"
            payload = f"CONTIG_{row}.1\tACGT\n".encode("ascii")
            (canonical / f"{accession}.txt").write_bytes(payload)
            records.append({"record_id": record_id, "entity_id": f"ncbi-assembly:{accession}", "sequence_digest": sha256(payload), "canonicalization_id": "m1-assembly-canonical-v1", "source_provenance_id": "test-source", "lifecycle_state": "eligible"})
            entities.append({"entity_id": f"ncbi-assembly:{accession}", "entity_type": "assembly", "record_versions": [record_id]})
            vectors.extend(1.0 if component == row else 0.0 for component in range(1280))
            instances.append({"instance_id": f"embedding:{record_id}:{PROFILE_ID}", "record_id": record_id, "profile_id": PROFILE_ID, "vector_reference": {"shard_id": "test-shard", "row": row, "shard_digest": "pending"}, "created_in": "test-build", "runner_provenance": {}, "eligibility_status": "eligible"})
        records_path = root / "records.jsonl"
        entities_path = root / "entities.jsonl"
        quarantines_path = root / "quarantines.jsonl"
        records_path.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
        entities_path.write_text("".join(json.dumps(row) + "\n" for row in entities), encoding="utf-8")
        quarantines_path.write_text("", encoding="utf-8")
        vectors_bytes = struct.pack(f"<{12 * 1280}f", *vectors)
        provenance = {"execution_environment_id": ADEE_ID, "execution_environment_declaration_digest": "sha256:test", "accelerator": "Tesla T4"}
        for instance in instances:
            instance["vector_reference"]["shard_digest"] = sha256(vectors_bytes)
            instance["runner_provenance"] = provenance
        embedding_zip = root / "embedding.zip"
        with zipfile.ZipFile(embedding_zip, "w") as archive:
            archive.writestr("vectors.float32le", vectors_bytes)
            archive.writestr("vector-shard-manifest.json", json.dumps({"profile_id": PROFILE_ID, "shard_id": "test-shard", "dimension": 1280, "dtype": "float32", "row_mapping": {str(row): instances[row]["instance_id"] for row in range(12)}, "digest": sha256(vectors_bytes), "build_provenance": {"runner_provenance": provenance}}))
            archive.writestr("embedding-instances.jsonl", "".join(json.dumps(item) + "\n" for item in instances))
            archive.writestr("embedding-stage-envelope.json", json.dumps({"stage_id": "embed", "input_artifacts": [], "output_artifacts": [], "outcome": "succeeded", "verification": {"runner_provenance": provenance}}))
        source = root / "source.json"
        acquisition = root / "acquisition.json"
        canonicalization = root / "canonicalization.json"
        self._json(source, {"source_provenance_id": "test-source", "source": "test", "source_version": "test", "acquired_at": "2026-07-21T00:00:00Z", "license_notice": {"scope": "internal M1 reproducibility validation only"}})
        for path, stage_id in ((acquisition, "acquire"), (canonicalization, "register-canonicalize")):
            self._json(path, {"stage_id": stage_id, "input_artifacts": [], "output_artifacts": [], "outcome": "succeeded", "verification": {}})
        inventory = root / "inventory.json"
        self._json(inventory, {"assemblies": []})
        inputs = PackageInputs(
            embedding_zip,
            records_path,
            entities_path,
            quarantines_path,
            canonical,
            source,
            inventory,
            acquisition,
            canonicalization,
            ROOT / "atlas-builder" / "manifests" / "m1" / "m1-build-manifest.t4-release.json",
            ROOT / "profiles" / "embedding" / "m1-generanno-prokaryote-0.5b-assembly-v1.yaml",
            ROOT / "profiles" / "plugins" / "m1-generanno-huggingface-adapter-input-v1.json",
            ROOT / "profiles" / "environments" / f"{ADEE_ID}.json",
            ROOT / "profiles" / "licenses" / "generanno-prokaryote-0.5b-base-MIT-notice.md",
            ROOT / "validation" / "colab" / "evidence" / "m1-t4-accelerator-implementation-validation-2026-07-19.md",
            ROOT / "schemas" / "json",
        )
        package = root / "draft"
        assemble_draft_package(inputs=inputs, release_directory=package, release_id="expedia-m1-draft-reader-test-v1", created_at="2026-07-21T00:00:00Z")
        return package

    def test_reader_opens_package_and_writes_external_validation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self._package(root)
            result = read_release(package)
            bundle = root / "validation-bundle.json"
            run_record = root / "clean-room-run.json"
            write_validation_evidence(result=result, validation_bundle_path=bundle, run_record_path=run_record, bundle_id="m1-reader-test", environment_label="test-clean-room")
            validation_schema = json.loads((ROOT / "schemas" / "json" / "validation-bundle.schema.json").read_text())

            Draft202012Validator(validation_schema).validate(json.loads(bundle.read_text()))
            self.assertEqual(12, result["record_count"])
            self.assertEqual(6, len(result["checks"]))
            self.assertRegex(result["logical_release_digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual("package directory and embedded schemas only", json.loads(run_record.read_text())["reader_inputs"])

    def test_reader_rejects_changed_vector_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self._package(Path(directory))
            vector = package / "embeddings" / "vectors.float32le"
            payload = bytearray(vector.read_bytes())
            payload[0] ^= 0x01
            vector.write_bytes(payload)
            with self.assertRaisesRegex(ReleaseReaderError, "digest mismatch"):
                read_release(package)

    def test_reader_rejects_path_traversal_and_non_draft_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self._package(Path(directory))
            manifest_path = package / "release-manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["artifacts"][0]["path"] = "../outside"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(ReleaseReaderError):
                read_release(package)
        with tempfile.TemporaryDirectory() as directory:
            package = self._package(Path(directory))
            manifest_path = package / "release-manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["state"] = "Candidate"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ReleaseReaderError, "only the declared Draft"):
                read_release(package)


if __name__ == "__main__":
    unittest.main()
