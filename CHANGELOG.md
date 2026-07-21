# Changelog

All notable repository changes are recorded here. This changelog describes
software and governed evidence; it does not make biological, scalability, or
retrieval-quality claims.

## Unreleased

### Governance

- M2 is accepted as an internal completion checkpoint. The M2.1-M2.6 evidence,
  fresh 86-test contract suite, and 7-test cross-adapter/Explorer conformance
  suite are recorded in `validation/evidence/m2-evidence-report-2026-07-21.md`.
  Query contracts, exact cosine reference behavior, cursors, provenance, and
  Core/SDK/REST/Explorer semantic boundaries are frozen except through
  controlled governance revision. This is not a public release or a scientific
  performance, usefulness, or biological claim.
- OQ-05 is accepted as an M3 evidence-threshold policy. It defines the
  preregistered evidence required before a claim category may be supported; it
  makes no scientific or method-quality claim and selects no method. ADR-009
  and ADR-014 are reconciled as EDS-proposed, absent historical entries rather
  than retroactively created decisions.

### Changed

- M2.6 adds a framework-neutral provenance-first Explorer presentation client.
  It consumes injected Core/SDK QueryResult data, labels canonical rows, and
  preserves typed errors, provenance, evidence labels, ordering, and cursors.
  It explicitly marks unavailable annotations, relations, and projections;
  no desktop/web UI, graph, projection, or independent query behavior is added.
- M2.5 adds a typed local Python SDK and a dependency-free local `/v1/query`
  WSGI transport adapter. Both are thin delegates over an injected Query Core;
  a shared corpus verifies identical success, typed-error, provenance, warning,
  ordering, and cursor behavior. Authentication, remote deployment, and an
  HTTP SDK client are not included.
- M2.4 adds Core-owned canonical-field filters, explicit state semantics,
  opaque cursor continuation, and bounded traversal-selector validation. The
  corrected M1 Draft has no annotation, unit-range, or relation artifacts, so
  those forms return typed unsupported errors and are never silently ignored.
  No SDK, REST, Explorer, ANN, benchmark, or public-release capability is
  included.
- The controlled M2.1 QueryResult defect correction preserves the historical
  `query-result/0.1.0` contract and makes `query-result/0.1.1` normative for
  subsequent M2 work. Exact results now bind metric direction, vector-shard
  digest, and the corrected M1 successor profile version/digest; QueryRequest
  semantics and query behavior are unchanged.
- M2.3 adds only the ADR-011 exact cosine reference path over an already
  verified, profile-scoped M1 Draft successor snapshot. It uses deterministic
  float32 inner products and score-descending/stable-record-ID ordering, and
  returns provenance-complete QueryResult envelopes. No ANN, filter, cursor,
  SDK, REST, Explorer, performance, recall, or biological capability is added.
- The M2.1 Query Contract Gate is approved. The normative QueryRequest,
  QueryResult, Filter, Cursor, and Error/Warning contracts have complete
  positive and negative conformance evidence; M2.2 verified local release
  adapter work is authorized. No M2 release, search, SDK, REST, or Explorer
  implementation is included in this change.
- M2.2 adds the local verified-release adapter. It delegates verification to
  the established M1 reader and exposes only immutable, manifest-addressed
  snapshots with typed trust failures. It includes no query execution or
  cosine-search behavior.
- A controlled M1 Draft successor package correction adds a schema-valid,
  manifest-addressed declaration for the existing frozen GENERanno profile.
  It preserves v2 as historical evidence and designates v3 as the authoritative
  Draft input for M2; embeddings, vectors, canonicalization, and execution
  provenance are unchanged.

## m1.0.0-draft - 2026-07-21

### Added

- A reproducible M1 Builder reference path for the fixed 12-record NCBI RefSeq
  prokaryotic internal-validation scope.
- Canonicalization, embedding-stage, packaging, and package-reader contract
  tests, including integrity and failure-path checks.
- A pinned GENERanno profile and the approved deterministic T4 execution
  environment for release generation.
- Draft-package integrity evidence, a clean-room reader validation bundle, ERS
  traceability, and a single-maintainer M1 evidence-gate approval record.

### Changed

- EDS v2.1.1 applies the accepted, narrow M1 execution-environment amendment:
  release eligibility depends on deterministic reproduction and complete
  provenance rather than CPU processor type.

### Release boundary

- `m1.0.0-draft` identifies the repository state supporting the approved M1
  evidence gate. The associated Atlas package remains an internal `Draft`, is
  not citable, and has not entered Candidate or Published state.
- The source-derived Draft package is intentionally retained outside Git; its
  identity is recorded in the M1 evidence index.
