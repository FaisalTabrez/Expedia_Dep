# Study M3-001: Deterministic Exact Query Reproducibility

**Status:** Approved — execution not yet initiated.
**Version:** `1.0`.
**Owner:** Faisal Tabrez, Project Maintainer.
**Prepared:** 2026-07-21.
**Governing sources:** EDS v2.1.1 section 13; accepted OQ-05; M2 completion
checkpoint `m2.0.0-complete`.

**Execution Environment:** `EE-M3-001-v1.1` (controlled execution-environment
successor).
**Approval records:** [`original approval`](../../validation/evidence/m3-001-v1-approval-2026-07-21.json)
and [`execution-environment amendment approval`](../../validation/evidence/m3-001-v1.0-environment-amendment-approval-2026-07-21.json).

## 0. Frozen implementation and serialization binding

| Binding | Value |
|---|---|
| Repository tag | `m2.0.0-complete` |
| Peeled immutable commit | `6183145f8fd6018431c55fd2e4ee7e1001e5fc87` |
| Required working-tree state | Clean before every replicate; the observed state is recorded. |
| Dependency manifest | `pyproject.toml` — `sha256:e0dcfffdf2d2ca71abcffcb69503f66d03a0ca2ff5f32280bf7ed2d080b0a813` |
| Dependency lock | `uv.lock` — `sha256:332b9b0ae251547a0db50deb717d2c778a3e2e5be40644255598aef783b18765` |
| Effective Python executable | Lock-resolved `.venv/Scripts/python.exe` — `sha256:5912d0884b23c0343983a864c6064242391e2265536f50b88624857e353882c9` |
| Atlas Release digest | `sha256:fb18e65424f9b1f8978b6460917f799f39137659ae83d3074d2b01a491eca37b` |
| EmbeddingProfile digest | `sha256:5679461d5a4482b48b90e97615d9661e84c2ac7c3b01253e7be4d7909a294294` |
| Vector-shard digest | `sha256:69204de55e57d8f3b088bba7dd63a8207c6bf55337d28b4bedc4769f1d8cf0c3` |
| Effective evaluation manifest | [`m3-001-v1.1-evaluation-manifest.json`](../evaluation-manifests/m3-001-v1.1-evaluation-manifest.json) — `sha256:6786d1a1e01b2509f7888d1a697461f9b16d2c24b6fffb8b9a049d7d26c87aab` |
| Historical manifest | [`m3-001-v1-evaluation-manifest.json`](../evaluation-manifests/m3-001-v1-evaluation-manifest.json) — `sha256:9750d6fdd0dbb7716110b24ec2e0f25ee206db6c27cee530e7b36ec6be0b93ec` |

`EE-M3-001-v1.1` is the sole active execution-environment identifier for this study. It
declares the following required environment property in addition to the bound
inputs above:

| Environment property | Required value |
|---|---|
| Operating system | `Microsoft Windows 10.0.26200`, `X64` (runtime-reported identity) |

Each replicate MUST also record its actual executable path and SHA-256. A
different environment may be recorded for diagnostic purposes, but its output
does not replace a failed required replicate.

For request hashing and output comparison, canonical JSON means: UTF-8 encoded
bytes; lexicographically sorted object keys; no insignificant whitespace; the
normalized finite numeric representation defined by OQ-11; and SHA-256 over
those canonical bytes. Canonical JSON has no line separators; any textual
fixture or report line ending MUST be LF. Whitespace, source formatting, and
object-member order SHALL NOT affect a canonical request digest.

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

The following approved values MUST NOT be changed without a controlled
governance amendment:

- Replicates: three independent Python process invocations in
  `EE-M3-001-v1.1` against the same verified package and committed M2
  implementation checkpoint.
- Environment capture: Python version, operating system, architecture, package
  dependency lock/revision, repository commit, and release/profile/shard
  digests for every invocation, all verified against `EE-M3-001-v1.1`.
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

For each identically addressed request in each replicate pair, the runner SHALL
apply this exact comparison algorithm:

1. Construct the complete logical outcome object: the `QueryResult` for a
   success, or the typed Query Core error outcome for a failure.
2. Canonicalize that object using the canonical JSON rules in section 0.
3. Compute SHA-256 over the canonical bytes and compare the resulting digests.
4. If the digests are equal, record the outcomes as identical.
5. If the digests differ, retain both canonical objects and diagnose the first
   difference in this fixed order: outcome type; typed error code and stage;
   ordered record IDs; decoded scores (equality tolerance `0.0`); provenance;
   warnings in returned order; opaque cursor payloads and their continuation
   reconstruction. The differing canonical-object digests remain the
   authoritative comparison result.

**PASS:** every request in every replicate matches in every recorded field.

**FAIL:** all required execution and environment checks complete, but any
comparison digest differs or any required result is missing.

**INCONCLUSIVE:** all planned executions complete, but the retained evidence
cannot support the hypothesis because of an evidence-integrity condition such
as package mismatch, corrupted output, or provenance mismatch.

**ABORTED:** the study is terminated before completion, whether by maintainer
decision or an unavoidable external interruption such as power loss, storage
failure, or repository corruption. An aborted replicate SHALL NOT be silently
replaced. It may be rerun only after a recorded incident; the rerun MUST
reference that incident and MUST NOT erase the aborted attempt.

No aggregate performance metric, latency statistic, biological benchmark, or
comparative score is collected.

No inferential statistics, confidence intervals, p-values, or hypothesis tests
other than deterministic equality under the algorithm above are performed.

No nonzero numerical-tolerance, hardware portability, or cross-platform
reproducibility claim is made. The `0.0` equality rule is an intra-study
comparison rule for the frozen reference implementation, not a portability
claim.

## 6. Evidence and analysis plan

The following required pre-execution evidence is bound:

- the immutable evaluation-manifest path and digest above;
- the approval record naming this exact preregistration version;
- an output directory containing per-replicate canonical requests, results,
  environment records, and SHA-256 digests;
- a deviation/incident record; and
- an analysis record that reports only the preregistered reproducibility
  comparison, including failures and unsupported status where relevant.

Raw outputs are internal M3 evidence. They do not alter the M1 Draft package or
authorize a Candidate, Published, public, or citable Atlas Release.

## 7. Pre-execution acceptance checklist

- [x] The maintainer accepts this exact Version `1.0` preregistration.
- [x] The immutable evaluation manifest and output/retention locations are
      fixed.
- [x] The approval record and evaluation-manifest digest are bound above.
- [ ] Immediately before execution, the local M1 v3 package and all referenced
      profile/shard digests verify through the Release Reader.
- [ ] Immediately before execution, the workspace is at commit
      `6183145f8fd6018431c55fd2e4ee7e1001e5fc87` and clean.
- [ ] `EE-M3-001-v1.1` is verified and recorded for all three processes.
- [x] No biological, comparative, performance, scalability, or generalization
      claim has been added.

M3-001 execution MUST NOT start until every unchecked pre-execution item is
completed and retained. After execution begins, no preregistration change is
permitted except through controlled governance.
