# M3-002 Analysis Report

**Status:** Draft observational analysis — no maintainer claim decision.
**Study:** M3-002 Exact Float32 Cosine Correctness.
**Preregistration:** Version 1.0, approved.
**Evaluation manifest:** `m3-002-evaluation-manifest-v1` / `sha256:1ca19ce393c2c475c59922e708401833a49334bea46e508cec574d034353c060`.
**Execution environment:** `EE-M3-001-v1.1`.
**Frozen M2 implementation commit:** `6183145f8fd6018431c55fd2e4ee7e1001e5fc87`.

## 1. Scope

This report indexes only observations retained by the approved M3-002
preregistration and immutable evaluation manifest. It does not evaluate
biological meaning, biological usefulness, embedding quality, annotation
quality, comparative superiority, ANN quality, recall, latency, throughput,
scalability, portability, cross-platform reproducibility, downstream ML
utility, default-method selection, or generalization.

## 2. Verified input identities

| Input | Retained identity |
|---|---|
| Approved preregistration | Version `1.0`; `sha256:23d537e522200b635d3c68e81913a187283a3ecd257a9d9e08bc16496b7be25c` |
| Evaluation manifest | `sha256:1ca19ce393c2c475c59922e708401833a49334bea46e508cec574d034353c060` |
| M2 implementation | `m2.0.0-complete` / `6183145f8fd6018431c55fd2e4ee7e1001e5fc87` |
| M1 v3 Draft release | `expedia-m1-draft-20260721-v3`; `sha256:fb18e65424f9b1f8978b6460917f799f39137659ae83d3074d2b01a491eca37b` |
| EmbeddingProfile | `m1-generanno-prokaryote-0.5b-assembly-v1` version `1.0.0`; `sha256:5679461d5a4482b48b90e97615d9661e84c2ac7c3b01253e7be4d7909a294294` |
| Vector shard | `sha256:69204de55e57d8f3b088bba7dd63a8207c6bf55337d28b4bedc4769f1d8cf0c3` |
| Query Core identity | Frozen M2 workspace at the commit above |
| Oracle identity | `validation/reference/m3_002_float32_cosine.py`; source identity bound by the evaluation manifest |
| Execution environment | `EE-M3-001-v1.1`; command-scoped Git trust; `git version 2.53.0.windows.3` |
| Runner identity | `sha256:8533f9007fb8c6db7b42f16f6b9a28cb69f2194e2bb96ac5059616e52af0cb24` |

## 3. Execution observations

The retained evidence records the following counts:

| Observation | Recorded count |
|---|---:|
| Canonical requests | 12 |
| Unique canonical request digests | 12 |
| Raw Query Core outputs | 12 |
| Independent oracle projections | 12 |
| Comparison observations | 12 |
| Digest-inventory entries | 10 |
| Historical pre-execution incidents | 2 |

The evidence inventory is located at
[`execution-v1`](execution-v1/). Its `digests.json` records the SHA-256 values
for the retained environment, release, request, output, comparison, incident,
and analysis-location artifacts.

## 4. Comparison observations

For each preregistered request, the retained comparison artifact records a
canonical comparison-object digest for the Query Core projection and a
canonical comparison-object digest for the independent oracle projection. The
artifact records no differing canonical-object digest and no diagnostic-field
entry for all 12 retained observations.

The canonical request records, raw Query Core outputs, canonical Query Core
projections, canonical oracle projections, and comparison observations are
retained in [`execution-v1`](execution-v1/). This is an observation of the
retained artifacts only; this report does not assign an outcome or a claim.

## 5. Incident history

Two incidents are retained in
[`incident-log.json`](execution-v1/incident-log.json):

- The initial runner could not resolve the Git executable.
- The first Git-resolution restart encountered Git safe-directory ownership
  protection for the detached frozen workspace.

Both incidents occurred before Release Reader verification. The controlled
runner amendments, environment record, release-verification record, and later
execution artifacts remain separately retained. No incident record is removed
or replaced.

## 6. Deviations

The retained bundle contains the two historical pre-execution incidents above.
It contains no separately retained deviation record after the approved
command-scoped Git trust amendment and successful restart.

## 7. Claim boundary reminder

This document reports only preregistered observations from retained evidence.
It does not classify the study as PASS or FAIL and does not support or reject
the exact-query-correctness claim. Those determinations are reserved for the
M3-002.8 maintainer claim decision.
