"""Round-trip and invalid-payload tests for initial canonical contracts."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "schemas" / "python"))

from expedia_contracts import (  # noqa: E402
    ArtifactDescriptor,
    ContractValidationError,
    EmbeddingInstance,
    EmbeddingProfile,
    GenomeRecordVersion,
    ReleaseManifest,
    ReleaseState,
)


def sample_profile() -> EmbeddingProfile:
    return EmbeddingProfile(
        profile_id="m1-generanno-prokaryote-0.5b-assembly-v1",
        version="0.1.0",
        input_contract={"canonicalization_profile": "m1-assembly-canonical-v1"},
        model={"artifact": "GenerTeam/GENERanno-prokaryote-0.5b-base", "revision": "abc", "content_digest": "sha256:model"},
        tokenization={"bos_prefix": "<s>", "maximum_positions": 8192},
        pooling={"window": "final-layer-bos", "assembly": "arithmetic-mean"},
        preprocessing={},
        output={"dimension": 1280, "dtype": "float32"},
        metric={"name": "cosine", "direction": "higher-is-more-similar"},
        compatibility={"class": "m1-generanno"},
        provenance={"plugin_descriptor": "sha256:plugin", "runner_environment": "sha256:env", "determinism": "declared"},
        lifecycle="Draft",
        validation_links=("validation/m1-release-integrity-v1",),
    )


class CoreContractRoundTripTests(unittest.TestCase):
    def test_release_manifest_round_trips_with_canonical_json(self) -> None:
        manifest = ReleaseManifest(
            release_id="expedia-m1-draft",
            schema_version="0.1.0",
            state=ReleaseState.DRAFT,
            scope={"population": "prokaryotic-genomes", "count": 12},
            artifacts=(ArtifactDescriptor("records.parquet", "application/x-parquet", "sha256:records", 42, "0.1.0"),),
            validation={"bundle_digest": "sha256:validation", "review_status": "pending"},
            created_at="2026-07-16T00:00:00Z",
            licenses=({"notice": "internal-m1"},),
        )
        encoded = manifest.to_json()
        self.assertEqual(encoded, json.dumps(manifest.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        self.assertEqual(ReleaseManifest.from_json(encoded).to_dict(), manifest.to_dict())

    def test_release_timestamp_is_normalized_to_utc(self) -> None:
        manifest = ReleaseManifest(
            release_id="expedia-m1-draft", schema_version="0.1.0", state=ReleaseState.DRAFT,
            scope={"population": "prokaryotic-genomes"},
            artifacts=(ArtifactDescriptor("records.parquet", "application/x-parquet", "sha256:records", 42, "0.1.0"),),
            validation={"review_status": "pending"}, created_at="2026-07-16T05:30:00+05:30",
        )
        self.assertEqual(manifest.created_at, "2026-07-16T00:00:00Z")

    def test_genome_record_round_trips(self) -> None:
        record = GenomeRecordVersion(
            record_id="ncbi-assembly:GCF_000001.1:m1-assembly-canonical-v1",
            entity_id="ncbi-assembly:GCF_000001",
            sequence_digest="sha256:sequence",
            canonicalization_id="m1-assembly-canonical-v1",
            source_provenance_id="source:ncbi-refseq",
            lifecycle_state="Eligible",
        )
        self.assertEqual(GenomeRecordVersion.from_json(record.to_json()).to_dict(), record.to_dict())

    def test_embedding_profile_round_trips(self) -> None:
        profile = sample_profile()
        self.assertEqual(EmbeddingProfile.from_json(profile.to_json()).to_dict(), profile.to_dict())

    def test_embedding_instance_round_trips(self) -> None:
        instance = EmbeddingInstance(
            instance_id="instance:1",
            record_id="record:1",
            profile_id="profile:1",
            vector_reference={"shard_id": "vectors-000", "row": 0, "shard_digest": "sha256:shard"},
            created_in="build:m1",
            runner_provenance={"environment": "sha256:env"},
            eligibility_status="Eligible",
        )
        self.assertEqual(EmbeddingInstance.from_json(instance.to_json()).to_dict(), instance.to_dict())


class CoreContractValidationTests(unittest.TestCase):
    def test_manifest_rejects_unsafe_or_duplicate_artifacts(self) -> None:
        with self.assertRaisesRegex(ContractValidationError, "safe relative"):
            ArtifactDescriptor("../records.parquet", "application/x-parquet", "sha256:records", 1, "0.1.0")
        artifact = ArtifactDescriptor("records.parquet", "application/x-parquet", "sha256:records", 1, "0.1.0")
        with self.assertRaisesRegex(ContractValidationError, "duplicate"):
            ReleaseManifest(
                release_id="draft", schema_version="0.1.0", state=ReleaseState.DRAFT,
                scope={"population": "test"}, artifacts=(artifact, artifact), validation={"status": "pending"},
            )

    def test_deserialization_rejects_unknown_or_missing_fields(self) -> None:
        payload = {"record_id": "r"}
        with self.assertRaisesRegex(ContractValidationError, "missing required"):
            GenomeRecordVersion.from_dict(payload)
        payload = sample_profile().to_dict()
        payload["undocumented"] = True
        with self.assertRaisesRegex(ContractValidationError, "undeclared"):
            EmbeddingProfile.from_dict(payload)

    def test_profile_rejects_invalid_dimension_and_missing_model_pin(self) -> None:
        payload = sample_profile().to_dict()
        payload["output"]["dimension"] = 0
        with self.assertRaisesRegex(ContractValidationError, "dimension"):
            EmbeddingProfile.from_dict(payload)
        payload = sample_profile().to_dict()
        del payload["model"]["content_digest"]
        with self.assertRaisesRegex(ContractValidationError, "model.content_digest"):
            EmbeddingProfile.from_dict(payload)

    def test_instance_rejects_invalid_row_and_non_json_provenance(self) -> None:
        payload = {
            "instance_id": "instance:1", "record_id": "record:1", "profile_id": "profile:1",
            "vector_reference": {"shard_id": "s", "row": -1, "shard_digest": "sha256:s"},
            "created_in": "build:m1", "runner_provenance": {"environment": "sha256:env"},
            "eligibility_status": "Eligible",
        }
        with self.assertRaisesRegex(ContractValidationError, "row"):
            EmbeddingInstance.from_dict(payload)
        with self.assertRaisesRegex(ContractValidationError, "not JSON-serializable"):
            EmbeddingInstance(
                instance_id="instance:1", record_id="record:1", profile_id="profile:1",
                vector_reference={"shard_id": "s", "row": 0, "shard_digest": "sha256:s"},
                created_in="build:m1", runner_provenance={"bad": object()}, eligibility_status="Eligible",
            )
