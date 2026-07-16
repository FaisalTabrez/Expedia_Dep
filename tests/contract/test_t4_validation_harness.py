from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "validation" / "colab"))
from m1_t4_validation import (  # noqa: E402
    EXPECTED_RECORD_COUNT,
    PROFILE_ID,
    REVISION,
    WEIGHT_DIGEST,
    load_batch_records,
    sha256,
)


class T4ValidationHarnessTests(unittest.TestCase):
    def test_harness_is_validation_only_and_pins_the_frozen_model(self) -> None:
        self.assertEqual("m1-generanno-prokaryote-0.5b-assembly-v1", PROFILE_ID)
        self.assertEqual("d02db0f24f2c62fa1efde760217cdf75771b0228", REVISION)
        self.assertRegex(WEIGHT_DIGEST, r"^sha256:[0-9a-f]{64}$")
        instructions = (ROOT / "validation" / "colab" / "README.md").read_text()
        self.assertIn("validation evidence only", " ".join(instructions.replace("**", "").split()))
        self.assertIn("byte-for-byte", instructions)
        self.assertIn("CUBLAS_WORKSPACE_CONFIG", instructions)

    def test_batch_mode_accepts_only_the_complete_digest_verified_m1_input_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            canonical = root / "canonical"
            canonical.mkdir()
            accessions = tuple(f"GCF_{index:09d}.1" for index in range(EXPECTED_RECORD_COUNT))
            rows: list[dict[str, object]] = []
            for index, accession in enumerate(accessions):
                payload = f"CONTIG_{index}.1\tACGT\n".encode("ascii")
                (canonical / f"{accession}.txt").write_bytes(payload)
                rows.append(
                    {
                        "record_id": f"ncbi-assembly:{accession}:m1-assembly-canonical-v1",
                        "sequence_digest": f"sha256:{hashlib.sha256(payload).hexdigest()}",
                        "canonicalization_id": "m1-assembly-canonical-v1",
                        "lifecycle_state": "eligible",
                    }
                )
            table = root / "genome-record-versions.jsonl"
            table.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            records = load_batch_records(canonical, table, accessions, sha256(table))
            self.assertEqual(accessions, tuple(record.accession for record in records))

            with self.assertRaisesRegex(RuntimeError, "digest"):
                load_batch_records(canonical, table, accessions, "sha256:" + "0" * 64)


if __name__ == "__main__":
    unittest.main()
