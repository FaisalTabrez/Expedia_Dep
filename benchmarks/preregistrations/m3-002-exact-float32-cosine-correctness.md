# Study M3-002: Exact Float32 Cosine Correctness

**Status:** Approved — execution remains prohibited pending later M3-002 gates.
**Version:** `1.0`.
**Owner:** Faisal Tabrez, Project Maintainer.  
**Prepared:** 2026-07-21.  
**Governing sources:** EDS v2.1.1 section 13; accepted OQ-05; M2 completion
checkpoint `m2.0.0-complete` at
`6183145f8fd6018431c55fd2e4ee7e1001e5fc87`; completed M3-001 evidence.
**Review record:** [`m3-002-preregistration-review-2026-07-21.md`](../../validation/evidence/m3-002/m3-002-preregistration-review-2026-07-21.md).
**Approval record:** [`m3-002-preregistration-approval-2026-07-21.json`](../../validation/evidence/m3-002/m3-002-preregistration-approval-2026-07-21.json).

## 1. Research question and claim boundary

**Research question.** Does the frozen M2 exact cosine Query Core produce
identical logical similarity results to an independently implemented float32
cosine reference using the same verified release and profile?

**Claim category.** Exact query correctness. This is the OQ-05
engineering-conformance category requiring exact-reference fixtures.

**Primary hypothesis.** For every preregistered request, the independent
reference and M2 Query Core produce identical ordered record IDs, decoded
float32 scores, deterministic tie ordering, and declared provenance fields.

**Null hypothesis.** At least one preregistered request produces a difference
outside the declared comparison rule.

**Permitted result wording if accepted and supported.** “Under the
preregistered corpus and recorded execution conditions, the frozen M2 exact
cosine implementation produced outputs identical to an independently
implemented float32 cosine reference.”

**Explicit non-goals.** This study SHALL NOT evaluate or claim biological
meaning, biological usefulness, embedding quality, annotation quality,
comparative superiority, ANN quality, recall, latency, throughput,
scalability, portability, cross-platform reproducibility, downstream ML
utility, default-method selection, or generalization.

## 2. Controlled inputs and cohort

The controlled corpus is
[`M3-002-M1-V3-EXACT-COSINE-CORPUS.md`](../data-manifests/M3-002-M1-V3-EXACT-COSINE-CORPUS.md).
It binds the internal M1 v3 Draft package, the sole declared profile, its
vector shard, the frozen M2 commit, and `EE-M3-001-v1.1`.

The cohort is every one of the twelve manifest-addressed canonical
GenomeRecordVersions. It is a software-correctness fixture, not a biological
cohort, external benchmark, population sample, or ground-truth dataset. No
biological ground truth applies to this algorithm-correctness question.

## 3. Independence requirement

The independent reference SHALL be specified and later implemented only under
`validation/reference/`. It SHALL NOT import, call, copy, or reuse Query Core
cosine computation, ranking, ordering, search-executor, cursor, or result
construction logic. It MAY reuse immutable schemas, the M1 Release Reader,
verified package artifacts, verified vector bytes, and profile declarations
only. The detailed boundary is in
[`M3-002-INDEPENDENT-REFERENCE-SPECIFICATION.md`](../reference/M3-002-INDEPENDENT-REFERENCE-SPECIFICATION.md).

## 4. Proposed execution design

After approval, a runner SHALL first verify the release through the M1 Release
Reader and reject every mismatch in the bound release, profile, shard,
repository commit, dependency lock, or execution-environment identity. It
shall then run each corpus request once through the frozen M2 Query Core and
once through the independent reference. It SHALL retain both raw outputs and
their canonical JSON SHA-256 digests before comparison.

No benchmark repetition, ANN, alternate profile, alternate model, annotation,
filter, traversal, cursor continuation, or error-behavior evaluation is in
scope. This study tests only complete exact-similarity rankings over the fixed
verified vectors.

## 5. Preregistered comparison and outcomes

For each request, canonicalize the M2 and independent-reference comparison
objects as UTF-8 JSON with lexicographically sorted keys, no insignificant
whitespace, finite normalized numeric representation, and SHA-256 over the
canonical bytes. Compare canonical-object digests first. If they differ,
diagnose fields in this fixed order: ordered record IDs; decoded float32
scores; score-desc-record-id-asc-v1 ordering and tie handling; release/profile/
vector-shard provenance.

Score equality tolerance is `0.0`. Rationale: both paths are required to use
the identical declared float32 arithmetic and fixed environment; a tolerance
would weaken this exact-correctness test.

**PASS:** every preregistered comparison object is identical.

**FAIL:** a verified execution completes and any comparison object differs.

**INCONCLUSIVE:** all planned execution completes but evidence integrity cannot
support the comparison, such as a package, provenance, or retained-output
mismatch.

**ABORTED:** execution is terminated before completion. The event and its cause
are retained; no failed or aborted run is silently replaced.

No additional metrics, aggregate statistics, confidence intervals, p-values,
or hypothesis tests are permitted.

## 6. Evidence and retention plan

Before execution, M3-002 MUST add and bind an approved immutable evaluation
manifest, maintainer approval record, environment record, Release Reader
verification record, independent-reference source digest, per-request raw M2
and reference outputs, comparison artifact, digest inventory, incident log,
and analysis location. Negative outcomes and all deviations are retained.

## 7. Pre-execution checklist

- [x] The preregistration review and maintainer approval are retained without
      scope expansion.
- [x] The controlled corpus and independent-reference specification are
      accepted as complete planning artifacts; implementation independence is
      still subject to later verification.
- [ ] An immutable evaluation manifest and approval record are bound.
- [ ] The verified M1 v3 Draft package and all declared digests are checked.
- [ ] No result, outcome, claim decision, production cosine code, or Query Core
      change has been inserted.

Until every remaining unchecked item is complete, M3-002 MUST NOT execute.
