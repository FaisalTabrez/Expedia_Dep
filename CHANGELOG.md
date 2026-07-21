# Changelog

All notable repository changes are recorded here. This changelog describes
software and governed evidence; it does not make biological, scalability, or
retrieval-quality claims.

## Unreleased

### Changed

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
