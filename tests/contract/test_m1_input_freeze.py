"""M1.1 tests for frozen external-input declarations; no Builder stages run here."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
M1_MANIFESTS = ROOT / "atlas-builder" / "manifests" / "m1"


class M1InputFreezeTests(unittest.TestCase):
    def test_inventory_is_exactly_twelve_versioned_refseq_accessions(self) -> None:
        inventory = json.loads((M1_MANIFESTS / "m1-refseq-accessions.json").read_text())
        assemblies = inventory["assemblies"]

        self.assertEqual(12, len(assemblies))
        accessions = [assembly["accession"] for assembly in assemblies]
        self.assertEqual(len(accessions), len(set(accessions)))
        self.assertTrue(all(re.fullmatch(r"GCF_\d{9}\.\d+", accession) for accession in accessions))
        self.assertEqual({"Bacteria", "Archaea"}, {assembly["domain"] for assembly in assemblies})
        self.assertEqual("Complete Genome", inventory["selection_rules"]["assembly_level"])

    def test_build_freeze_refers_only_to_committed_m1_inputs(self) -> None:
        manifest = json.loads((M1_MANIFESTS / "m1-build-manifest.input-freeze.json").read_text())
        acquisition = manifest["source_inventory"][0]["acquisition"]

        self.assertEqual("18.33.1", acquisition["version"])
        self.assertRegex(acquisition["package_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertIn("not-executed", acquisition["status"])
        self.assertEqual(["m1-generanno-prokaryote-0.5b-assembly-v1"], manifest["embedding_profiles"])

        provenance = json.loads((M1_MANIFESTS / "m1-source-provenance.json").read_text())
        self.assertEqual("internal M1 reproducibility validation only", provenance["license_notice"]["scope"])
        self.assertIn("does not grant redistribution rights", provenance["license_notice"]["notice"])

    def test_profile_has_no_unresolved_implementation_placeholders(self) -> None:
        profile = (ROOT / "profiles" / "embedding" / "m1-generanno-prokaryote-0.5b-assembly-v1.yaml").read_text()

        self.assertNotIn("REQUIRED_", profile)
        self.assertIn("d02db0f24f2c62fa1efde760217cdf75771b0228", profile)
        self.assertIn("sha256:ed1cfcc64fe890a6a72017d24c02ad6af3b15c9cfa6950e850908cca92882d51", profile)

    def test_plugin_descriptor_captures_pinned_custom_code_identity(self) -> None:
        descriptor_path = ROOT / "profiles" / "plugins" / "m1-generanno-huggingface-adapter-input-v1.json"
        descriptor = json.loads(descriptor_path.read_text())

        self.assertEqual("hf-git-revision:d02db0f24f2c62fa1efde760217cdf75771b0228", descriptor["identity_digest"])
        self.assertEqual("4.44.0", descriptor["compatibility"]["required_transformers_version"])
        self.assertEqual("Tesla T4", descriptor["determinism"]["accelerator"])
        self.assertEqual(
            "m1-generanno-t4-cuda12.1-fp32-deterministic-v1",
            descriptor["determinism"]["declaration_id"],
        )
        declaration = ROOT / descriptor["determinism"]["declaration_path"]
        self.assertTrue(declaration.is_file())
        self.assertIn("modeling_generanno.py", descriptor["compatibility"]["custom_model_code"])
        notice = ROOT / descriptor["compatibility"]["license_evidence"]["notice_path"]
        self.assertIn("MIT license text", notice.read_text())

    def test_runner_lock_contains_the_pinned_direct_dependencies(self) -> None:
        lock = (ROOT / "profiles" / "environments" / "m1-generanno-reference-runner" / "uv.lock").read_text()

        self.assertIn('requires-python = "==3.12.13"', lock)
        self.assertIn('name = "torch"', lock)
        self.assertIn('version = "2.4.1"', lock)
        self.assertIn('name = "transformers"', lock)
        self.assertIn('version = "4.44.0"', lock)


if __name__ == "__main__":
    unittest.main()
