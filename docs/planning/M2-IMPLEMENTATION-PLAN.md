# M2 implementation plan: one semantic read path

**Status:** The M2.1 Query Contract Gate is approved. M2.2
Verified Release Adapter work is authorized; no M2 release-adapter or query
execution implementation is present yet.
**Governing specification:** EDS v2.1.1 sections 5.1, 8, 11, 12, 14, 15.3, and
16; ERS REQ-006, REQ-011, REQ-015, REQ-021–024.
**Prerequisite release evidence:** M1 internal Draft evidence gate approved at
repository tag `m1.0.0-draft`.

## 1. Objective and boundary

M2 establishes Query Core as the sole owner of read-only release query
semantics. Explorer, the typed SDK, and REST are adapters over that Core; none
may define an alternate interpretation of filtering, ranking, provenance,
errors, or cursors.

M2 operates against a verified local release fixture. The M1 package remains a
non-public Draft and is development evidence only; M2 does not change its
state, licensing, citation, or publication status.

Included after the entry gates pass:

- Versioned QueryRequest, QueryResult, filter, traversal, provenance, warning,
  error, and cursor contracts.
- A local verified-release adapter and exact cosine reference search over the
  declared profile vectors.
- Query Core conformance tests, then a thin typed SDK and REST adapter that
  delegate to the same Core.
- A provenance-first Explorer view that consumes QueryResult without local
  query semantics.

Excluded:

- ANN as a default or unevaluated optimization; OQ-04 remains deferred.
- Cross-profile similarity, BridgeProfiles, annotations, derived relations,
  method benchmarks, biological claims, public release work, remote deployment,
  or access-control design.

## 2. Accepted governance gates and remaining contract gate

The following governance dispositions and the M2.1 Query Contract Gate are
accepted. M2.2 may now implement the verified local release adapter. M2.3 and
later work remain dependent on their declared predecessor milestones.

The proposed dispositions are available for review in
[`ADR-010`](../../specification/adr/ADR-010-trusted-local-release-boundary.md),
[`ADR-011`](../../specification/adr/ADR-011-exact-cosine-m2-reference-search.md),
[`ADR-016`](../../specification/adr/ADR-016-query-core-semantic-authority.md),
and [OQ-11](../../specification/open-questions/OQ-11-M2-filter-grammar-and-cost-limits.md).
All four dispositions are accepted. They remain narrow M2 constraints and do
not authorize ANN, a public release, remote deployment, or changed Atlas
semantics.

| Gate | Required disposition | Why it blocks M2 |
|---|---|---|
| ADR-010 | Accepted trusted local read boundary | Defines the supported local release access boundary. |
| ADR-011 | Accepted exact-cosine reference search | Defines the initial exact reference adapter and prohibits ANN selection in M2. |
| ADR-016 | Accepted Query Core semantic authority | Establishes the single semantic authority for Core, SDK, REST, and Explorer. |
| OQ-11 | Accepted v1 filter grammar and local-fixture cost limits | Prevents silent filter weakening and undefined request cost behavior. |
| M2 contract review | Query schemas replace their M1 placeholders with accepted semantics | Approved; authorizes M2.2 only. |

OQ-04 remains deferred. Therefore the initial M2 search path must be exact
cosine over normalized vectors; it must report exact mode and the verified
vector-shard digest. It must not present an ANN result as exact.

## 3. Work breakdown and acceptance criteria

| ID | Work | Dependencies | Deliverables | Acceptance criteria | Complexity |
|---|---|---|---|---|---|
| M2.1 | Accept the entry-gate decisions and replace M1 query-schema placeholders with reviewed contracts. | ADR-010/011/016; OQ-11 | Contract revisions, fixtures, compatibility rules, errors/warnings/cursor definitions, and the Query Contract Conformance Matrix | Positive and negative fixtures validate; every matrix row is `Pass` with linked test evidence before M2.2 starts. | L |
| M2.2 | Build a verified local release adapter. | M2.1; M1 reader | Immutable-release handle, table/vector readers, trust boundary | Adapter refuses unverified artifacts and exposes only manifest-addressed data. | M |
| M2.3 | Implement exact profile-scoped cosine search. | M2.1–M2.2 | Query Core reference executor, exact result fixtures | Normalized vectors, declared profile, metric direction, deterministic score-plus-record ordering, and provenance are returned. | L |
| M2.4 | Implement filters, traversal selectors, warnings, errors, and stable cursors. | M2.1–M2.3 | Canonical request normalization, cursor binding, conformance matrix | Core rejects unsupported cross-profile, filter, traversal, or exactness combinations; cursors bind release/request/order/last key. | XL |
| M2.5 | Add SDK and REST transport adapters. | M2.4 | Typed SDK wrapper, OpenAPI/REST adapter, shared conformance fixtures | Equivalent logical requests through Core, SDK, and REST yield equivalent results, provenance, warnings, errors, and cursor behavior. | L |
| M2.6 | Add a provenance-first Explorer client. | M2.5 | Local Explorer read view and presentation tests | Explorer labels canonical records, assertions, and derived artifacts distinctly and never executes independent query logic. | M |

## 4. Critical path

`ADR/OQ disposition -> accepted contracts -> verified reader adapter -> exact
reference search -> filters/cursors -> SDK/REST conformance -> Explorer`

M2.5 and M2.6 must not start before Core conformance in M2.4. Explorer is a
consumer of QueryResult, never a parallel query implementation.

M2.2 was gated by the
[`M2 Query Contract Conformance Matrix`](M2-QUERY-CONTRACT-CONFORMANCE-MATRIX.md).
Its five Pass rows and recorded maintainer approval now satisfy that gate.

## 5. Test and evidence strategy

- Start with contract fixtures before Core behavior. Test absent, unavailable,
  false, malformed, and unsupported filter conditions distinctly once OQ-11 is
  resolved.
- Bind every result and cursor to release digest, schema version, profile,
  metric, mode, request digest, ordering version, and relevant artifact digest.
- Use the M1 Draft fixture only for local conformance. Do not infer biological
  quality, recall, latency, or scalability from it.
- Run the same request corpus through Core, SDK, and REST. Compare logical
  result content, not transport-specific serialization details.
- Retain negative tests for changed release digest, profile mismatch,
  cross-profile query, unsupported traversal, cursor reuse after changed input,
  and any attempt to weaken exact mode silently.

## 6. Risks and controls

| Risk | Control |
|---|---|
| Query clients diverge semantically | Make Core the only executor and use shared conformance fixtures. |
| Filter grammar is guessed in code | Block M2.1 until OQ-11 is resolved. |
| ANN convenience is treated as evidence | Keep exact search as the sole M2 reference path while OQ-04 is deferred. |
| Draft fixture is mistaken for a public atlas | Keep Draft scope, license, and citation warnings in release context and documentation. |
| Large result sets create unbounded work | Define OQ-11 cost limits and cursor semantics before behavior is implemented. |

## 7. Exit criteria

M2 is complete only when an identical conformance corpus through Query Core, SDK,
and REST produces equivalent logical results and context; cursors are stable and
invalidated correctly; Explorer presents only Core results with evidence labels;
and no public, biological, benchmark, recall, latency, or scalability claim has
been added without its required later evidence.
