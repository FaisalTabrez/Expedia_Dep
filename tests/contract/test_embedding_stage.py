from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "atlas-builder" / "src"))

from expedia_atlas_builder.embedding import VECTOR_DIMENSION  # noqa: E402
from expedia_atlas_builder.embedding_stage import (  # noqa: E402
    CHECKPOINT_NAME,
    EmbeddingStageError,
    execute_embedding_stage,
)


class EmbeddingStageTests(unittest.TestCase):
    def _records(self, directory: Path, accessions: tuple[str, ...]) -> tuple[Path, Path]:
        canonical = directory / "canonical"
        canonical.mkdir()
        rows: list[dict[str, str]] = []
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
        table = directory / "genome-record-versions.jsonl"
        table.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return table, canonical

    @staticmethod
    def _vector(component: int) -> tuple[float, ...]:
        return tuple(1.0 if index == component else 0.0 for index in range(VECTOR_DIMENSION))

    def test_stage_writes_contract_shard_instances_and_success_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records, canonical = self._records(root, ("GCF_000000001.1", "GCF_000000002.1"))
            calls: list[str] = []

            def embed(canonical_path: Path, _snapshot: Path, _digest: str, timings: dict[str, float]) -> tuple[float, ...]:
                calls.append(canonical_path.name)
                timings["forward_seconds"] = 1.0
                return self._vector(len(calls) - 1)

            workspace = root / "embedding"
            envelope = execute_embedding_stage(
                record_versions_path=records,
                canonical_directory=canonical,
                snapshot_path=root / "snapshot",
                expected_weight_digest="sha256:model",
                workspace=workspace,
                build_id="m1-test-build",
                runner_provenance={"environment": "test"},
                embedder=embed,
            )

            self.assertEqual("succeeded", envelope["outcome"])
            self.assertEqual(["GCF_000000001.1.txt", "GCF_000000002.1.txt"], calls)
            vector_path = workspace / "vectors.float32le"
            self.assertEqual(2 * VECTOR_DIMENSION * 4, vector_path.stat().st_size)
            values = struct.unpack(f"<{2 * VECTOR_DIMENSION}f", vector_path.read_bytes())
            self.assertEqual(1.0, values[0])
            self.assertEqual(1.0, values[VECTOR_DIMENSION + 1])
            manifest = json.loads((workspace / "vector-shard-manifest.json").read_text())
            instances = [json.loads(line) for line in (workspace / "embedding-instances.jsonl").read_text().splitlines()]
            vector_schema = json.loads((ROOT / "schemas" / "json" / "vector-shard-manifest.schema.json").read_text())
            instance_schema = json.loads((ROOT / "schemas" / "json" / "embedding-instance.schema.json").read_text())
            Draft202012Validator(vector_schema).validate(manifest)
            for instance in instances:
                Draft202012Validator(instance_schema).validate(instance)
            self.assertEqual(2, len(instances))
            self.assertEqual(manifest["digest"], instances[0]["vector_reference"]["shard_digest"])
            self.assertEqual({"environment": "test"}, envelope["verification"]["runner_provenance"])
            self.assertFalse((workspace / CHECKPOINT_NAME).exists())

    def test_failed_run_resumes_without_recomputing_completed_vectors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records, canonical = self._records(root, ("GCF_000000001.1", "GCF_000000002.1"))
            workspace = root / "embedding"
            first_calls: list[str] = []

            def fail_on_second(canonical_path: Path, _snapshot: Path, _digest: str, _timings: dict[str, float]) -> tuple[float, ...]:
                first_calls.append(canonical_path.name)
                if len(first_calls) == 2:
                    raise RuntimeError("simulated interruption")
                return self._vector(0)

            with self.assertRaisesRegex(EmbeddingStageError, "inference failed"):
                execute_embedding_stage(
                    record_versions_path=records,
                    canonical_directory=canonical,
                    snapshot_path=root / "snapshot",
                    expected_weight_digest="sha256:model",
                    workspace=workspace,
                    build_id="m1-test-build",
                    runner_provenance={"environment": "test"},
                    embedder=fail_on_second,
                )
            checkpoint = json.loads((workspace / CHECKPOINT_NAME).read_text())
            self.assertEqual(1, checkpoint["completed_rows"])
            resumed_calls: list[str] = []

            def resume(canonical_path: Path, _snapshot: Path, _digest: str, _timings: dict[str, float]) -> tuple[float, ...]:
                resumed_calls.append(canonical_path.name)
                return self._vector(1)

            envelope = execute_embedding_stage(
                record_versions_path=records,
                canonical_directory=canonical,
                snapshot_path=root / "snapshot",
                expected_weight_digest="sha256:model",
                workspace=workspace,
                build_id="m1-test-build",
                runner_provenance={"environment": "test"},
                embedder=resume,
            )
            self.assertEqual("succeeded", envelope["outcome"])
            self.assertEqual(["GCF_000000002.1.txt"], resumed_calls)

    def test_stage_rejects_unnormalized_vectors_before_writing_a_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records, canonical = self._records(root, ("GCF_000000001.1",))
            with self.assertRaisesRegex(EmbeddingStageError, "not L2 normalized"):
                execute_embedding_stage(
                    record_versions_path=records,
                    canonical_directory=canonical,
                    snapshot_path=root / "snapshot",
                    expected_weight_digest="sha256:model",
                    workspace=root / "embedding",
                    build_id="m1-test-build",
                    runner_provenance={"environment": "test"},
                    embedder=lambda *_args: (2.0,) + (0.0,) * (VECTOR_DIMENSION - 1),
                )


if __name__ == "__main__":
    unittest.main()
