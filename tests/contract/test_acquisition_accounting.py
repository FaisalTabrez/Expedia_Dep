"""Unit tests for the M1.3 acquisition/accounting boundary."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "atlas-builder" / "src"))

from expedia_atlas_builder.acquisition import (  # noqa: E402
    AcquisitionError,
    account_dataset_archive,
    dataset_catalogue_digest,
    load_inventory,
    sha256_file,
    acquire_ncbi_datasets,
    write_accession_list,
)


class AcquisitionAccountingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = load_inventory(ROOT / "atlas-builder" / "manifests" / "m1" / "m1-refseq-accessions.json")

    def _archive_with_accessions(self, path: Path, accessions: list[str]) -> None:
        report = "\n".join(json.dumps({"accession": accession}) for accession in accessions) + "\n"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("ncbi_dataset/data/assembly_data_report.jsonl", report)
            archive.writestr("ncbi_dataset/data/dataset_catalog.json", "{}")

    def test_inventory_is_written_as_exact_lf_versioned_accession_list(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "accessions.txt"
            write_accession_list(self.inventory, output)
            self.assertEqual(
                [assembly.accession for assembly in self.inventory],
                output.read_text(encoding="utf-8").splitlines(),
            )

    def test_archive_accounting_requires_every_declared_assembly_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "dataset.zip"
            accessions = [assembly.accession for assembly in self.inventory]
            self._archive_with_accessions(archive, accessions)
            account = account_dataset_archive(archive, self.inventory)
            self.assertTrue(account.is_complete)
            self.assertEqual(tuple(sorted(accessions)), account.registered)
            self.assertRegex(dataset_catalogue_digest(archive), r"^sha256:[0-9a-f]{64}$")

    def test_archive_accounting_preserves_missing_unexpected_and_duplicate_observations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "dataset.zip"
            accessions = [assembly.accession for assembly in self.inventory]
            self._archive_with_accessions(archive, accessions[:-1] + [accessions[0], "GCF_999999999.1"])
            account = account_dataset_archive(archive, self.inventory)
            self.assertFalse(account.is_complete)
            self.assertEqual((accessions[-1],), account.missing)
            self.assertEqual(("GCF_999999999.1",), account.unexpected)
            self.assertEqual((accessions[0],), account.duplicate_observations)

    def test_invalid_archive_cannot_be_silently_accounted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "dataset.zip"
            archive.write_text("not a zip", encoding="utf-8")
            with self.assertRaisesRegex(AcquisitionError, "cannot read"):
                account_dataset_archive(archive, self.inventory)
            with self.assertRaisesRegex(AcquisitionError, "catalogue"):
                dataset_catalogue_digest(archive)

    def test_file_digest_is_content_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "artifact.bin"
            artifact.write_bytes(b"one")
            first = sha256_file(artifact)
            artifact.write_bytes(b"two")
            self.assertNotEqual(first, sha256_file(artifact))

    def test_failed_acquisition_emits_a_failed_stage_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            missing_cli = Path(directory) / "datasets.exe"
            envelope = acquire_ncbi_datasets(
                inventory_path=ROOT / "atlas-builder" / "manifests" / "m1" / "m1-refseq-accessions.json",
                datasets_executable=missing_cli,
                workspace=workspace,
                expected_cli_version="18.33.1",
            )
            self.assertEqual("failed", envelope["outcome"])
            self.assertTrue((workspace / "acquisition-stage-envelope.json").is_file())

    def test_committed_acquisition_evidence_accounts_for_the_complete_inventory(self) -> None:
        manifests = ROOT / "atlas-builder" / "manifests" / "m1"
        stage = json.loads((manifests / "m1-acquisition-stage-outcome.json").read_text())
        acquired = json.loads((manifests / "m1-build-manifest.acquired.json").read_text())

        self.assertEqual("succeeded", stage["outcome"])
        self.assertEqual(12, stage["verification"]["expected_accession_count"])
        self.assertEqual([], stage["verification"]["missing_accessions"])
        self.assertEqual([], stage["verification"]["unexpected_accessions"])
        self.assertEqual([], stage["verification"]["duplicate_observations"])
        self.assertEqual("18.33.1", acquired["source_inventory"][0]["tool"]["version"])
        self.assertEqual(stage["verification"]["archive_digest"], acquired["source_inventory"][0]["package_archive_digest"])


if __name__ == "__main__":
    unittest.main()
