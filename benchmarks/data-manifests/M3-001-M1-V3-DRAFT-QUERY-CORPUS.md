# M3-001 controlled query-corpus manifest

**Status:** Draft study input manifest. Not an Atlas Release, benchmark result,
or biological cohort.
**Study:** M3-001 Deterministic Exact Query Reproducibility.

## Immutable input identity

| Input | Bound value |
|---|---|
| Atlas package | `expedia-m1-draft-20260721-v3` (internal Draft only) |
| ReleaseManifest digest | `sha256:fb18e65424f9b1f8978b6460917f799f39137659ae83d3074d2b01a491eca37b` |
| Record table | Manifest-addressed `records/genome-record-versions.jsonl` |
| Expected record count | 12 canonical GenomeRecordVersions |
| Profile | `m1-generanno-prokaryote-0.5b-assembly-v1` version `1.0.0` |
| Profile digest | `sha256:5679461d5a4482b48b90e97615d9661e84c2ac7c3b01253e7be4d7909a294294` |
| Vector shard digest | `sha256:69204de55e57d8f3b088bba7dd63a8207c6bf55337d28b4bedc4769f1d8cf0c3` |
| Query implementation checkpoint | Repository tag `m2.0.0-complete` |

## Cohort rule

After the Verified Release Adapter verifies the package, the corpus consists of
every row in the manifest-addressed record table, in its declared stable table
order. Each row's `record_id` is used once as `similarity.query_record_id`.
The runner MUST reject execution unless there are exactly 12 unique record IDs
and every requested ID is present in the verified table.

## Source and license boundary

This study reuses the internal M1 Draft package solely as a controlled software
and retrieval reproducibility fixture. The retained M1 source notice permits
internal reproducibility validation only. This manifest does not establish an
evaluation population, biological ground truth, public benchmark dataset, or
public-release license.

## Exclusions

No annotations, derived relations, alternate embedding profiles, BridgeProfiles,
ANN indexes, external genomes, biological labels, or downstream tasks are part
of this corpus.
