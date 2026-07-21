# Study M3-001: Deterministic Exact Query Reproducibility

**Status:** Draft — not accepted; execution is prohibited.
**Version:** `0.1.0-draft`.
**Owner:** Faisal Tabrez, Project Maintainer.
**Prepared:** 2026-07-21.
**Governing sources:** EDS v2.1.1 section 13; accepted OQ-05; M2 completion
checkpoint `m2.0.0-complete`.

## 1. Research question and claim boundary

**Research question.** Does the frozen M1 Draft package produce deterministic,
profile-scoped exact cosine QueryResults across repeated executions using the
M2 Query Core?

**Claim category.** Deterministic retrieval. This is an engineering-conformance
category under OQ-05. It does not evaluate biological meaning, retrieval
usefulness, or method superiority.

**Primary hypothesis.** Repeated executions of identical canonical
QueryRequests against the same verified release produce logically identical
QueryResults: returned records, ranking, decoded scores, provenance, warnings,
and cursor behavior are identical.

**Null hypothesis.** Repeated executions produce an observable difference
outside the preregistered comparison rule.

**Permitted conclusion if accepted and supported.** “The declared M3-001
request corpus reproduced deterministic exact QueryResults under the recorded
execution conditions.”

**Prohibited conclusions.** This study SHALL NOT evaluate or claim biological
usefulness, embedding quality, annotation quality, comparative superiority,
scalability, latency, ANN performance, generalization, downstream ML utility,
or a preferred model/profile/index.

## 2. Inputs and scope

The controlled query corpus is
[`M3-001-M1-V3-DRAFT-QUERY-CORPUS.md`](../data-manifests/M3-001-M1-V3-DRAFT-QUERY-CORPUS.md).
The runner SHALL first open the M1 v3 Draft only through the Verified Release
Adapter. It SHALL reject a missing, changed, unverified, profile-incompatible,
or wrong-digest package.

The sole profile is `m1-generanno-prokaryote-0.5b-assembly-v1` version `1.0.0`.
The sole retrieval baseline is the frozen M2 exact float32 cosine reference
implementation at `m2.0.0-complete`. No ANN, FAISS, HNSW, quantization,
BridgeProfile, annotation, derived relation, external cohort, or comparative
method is in scope.

## 3. Preregistered request corpus

For each of the 12 verified record IDs, the runner SHALL execute the following
request families using `query-request/0.1.0`, exact cosine, the declared
profile, and `score-desc-record-id-asc-v1` ordering:

| Family | Request construction | Purpose |
|---|---|---|
| Full result | `limit: 12`, `cursor: null`, no filter | Stable release/profile/provenance, rows, ordering, scores, warnings, and no-page cursor behavior. |
| Paginated result | `limit: 2`, `cursor: null`, then every returned continuation cursor | Stable cursor creation, continuation rows, and complete ordered reconstruction. |
| Invalid cursor | Same exact request with a deliberately malformed opaque cursor | Stable typed `invalid_cursor` failure. |
| Profile mismatch | Same query record with an undeclared profile version | Stable typed `profile_incompatible` failure. |

The corpus contains no annotations or derived relations. Any request that does
not validate through Query Core is recorded as its declared typed error; it is
not silently repaired.

## 4. Proposed execution design

The following values are proposed for maintainer approval and MUST NOT be
changed after acceptance without an approved amendment:

- Replicates: three independent Python process invocations against the same
  verified package and committed M2 implementation checkpoint.
- Environment capture: Python version, operating system, architecture, package
  dependency lock/revision, repository commit, and release/profile/shard
  digests for every invocation.
- Input representation: each request is written as canonical UTF-8 JSON after
  Query Core normalization; its `canonical_request_digest` is recorded.
- Output representation: each QueryResult is retained as canonical UTF-8 JSON
  and as a parsed logical object; no output is rounded before comparison.
- Score tolerance: `0.0` for decoded score equality. Rationale: the study is
  limited to the frozen deterministic M2 exact float32 reference executor and
  asks whether its identical inputs reproduce identical logical results, not
  whether different hardware implementations are numerically close.

## 5. Metrics and decision rule

For every request family and every replicate, record:

- canonical request digest;
- release, profile, profile-declaration, and vector-shard digests;
- result outcome, ordered record IDs, decoded scores, warnings, and provenance;
- cursor values, continuation reconstruction, and typed error code/stage where
  applicable; and
- runtime provenance listed in section 4.

The study passes only when all three replicates have identical values for every
recorded metric and every request family, with decoded-score tolerance `0.0`.
A missing result, changed digest, changed row/order/score/provenance/warning,
changed cursor behavior, or changed typed error is a failure. The failure,
inputs, and raw outputs SHALL be retained without retry-based replacement.

No aggregate performance metric, latency statistic, biological benchmark, or
comparative score is collected.

## 6. Evidence and analysis plan

Before execution, the study MUST add and bind:

- an immutable evaluation-manifest path and digest;
- an approval record naming this exact preregistration version;
- an output directory containing per-replicate canonical requests, results,
  environment records, and SHA-256 digests;
- a deviation/incident record; and
- an analysis record that reports only the preregistered reproducibility
  comparison, including failures and unsupported status where relevant.

Raw outputs are internal M3 evidence. They do not alter the M1 Draft package or
authorize a Candidate, Published, public, or citable Atlas Release.

## 7. Pre-execution acceptance checklist

- [ ] The maintainer accepts this exact `0.1.0-draft` preregistration or an
      approved successor.
- [ ] The local M1 v3 package digest and all referenced profile/shard digests
      verify through the Release Reader.
- [ ] The evaluation manifest and output/retention locations are fixed.
- [ ] The three-process execution environment is recorded.
- [ ] No biological, comparative, performance, scalability, or generalization
      claim has been added.

Until every item is complete, M3-001 MUST NOT execute.
