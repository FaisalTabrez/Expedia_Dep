# M3-002 controlled exact-cosine corpus manifest

**Status:** Draft study input manifest. Not an Atlas Release, benchmark result,
biological cohort, or approved evaluation manifest.  
**Study:** M3-002 Exact Float32 Cosine Correctness.

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
| M2 implementation | `m2.0.0-complete` / `6183145f8fd6018431c55fd2e4ee7e1001e5fc87` |
| Proposed execution environment | `EE-M3-001-v1.1` |

## Request rule

After independent release verification, every row in the manifest-addressed
record table is used once as `similarity.query_record_id`, in stable declared
table order. Each request is an exact cosine similarity request with the bound
profile, `limit: 12`, `cursor: null`, no filter, no traversal, and ordering
`score-desc-record-id-asc-v1`.

The runner MUST reject execution unless there are exactly twelve unique record
IDs, each is present in the verified table, and each request returns a complete
ranking subject to the frozen exact-cosine contract.

## Inclusion and exclusion

Included: the twelve canonical records and their sole manifest-addressed
float32 vector shard under the declared profile.

Excluded: pagination continuation behavior, malformed requests, typed errors,
filters, traversal, annotations, derived relations, alternate profiles,
BridgeProfiles, ANN indexes, external genomes, biological labels, and
downstream tasks.

## Source and license boundary

This corpus reuses the internal M1 Draft package only as a controlled
algorithm-correctness fixture. It creates no external evaluation cohort,
biological ground truth, public benchmark dataset, or public-release license.
