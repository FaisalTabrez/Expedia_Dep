# ADR-016: Query Core as the single semantic authority

**Status:** Accepted — Faisal Tabrez, Project Maintainer, 2026-07-21.
**EDS register decision:** Query Core owns query semantics.

## Decision

Query Core SHALL be the sole implementation of release selection, trusted-read
resolution, profile compatibility, request validation, filtering, traversal,
ranking, exactness mode, cursor construction, warnings, errors, and result
provenance.

The Python SDK SHALL be a typed in-process wrapper over Query Core. REST SHALL
be a versioned transport adapter over Query Core. Explorer SHALL consume
provenance-complete QueryResult data and SHALL NOT execute independent query
logic. All adapters SHALL preserve the Core’s logical result semantics; they
may change only language binding, serialization, transport, or presentation.

## Rationale

The EDS identifies Query Core as the semantic center between immutable releases
and all clients. Duplicating filtering, ordering, cursor, or evidence behavior
in adapters would create conflicting interpretations of the same scientific
release.

## Consequences

- Contract changes are made in Query Core first and verified through a shared
  conformance corpus before SDK, REST, or Explorer behavior is added.
- REST cannot weaken errors, filter behavior, exactness, ordering, or cursors
  because of transport convenience.
- Explorer can render evidence labels and derived-artifact distinctions without
  becoming a retrieval engine.
- Caching and optimization remain implementation details that must preserve the
  Core result contract and provenance.

## Acceptance criteria

1. The same canonical request corpus through Core, SDK, and REST returns
   equivalent logical rows, release/profile/metric context, provenance,
   warnings, errors, ordering, and cursor behavior.
2. Explorer receives QueryResult data from Query Core and contains no local
   filter, similarity, cursor, or release-trust implementation.
3. Any unsupported request is rejected or reported by Query Core; no adapter
   silently removes a filter, changes exactness, or substitutes a profile.
4. Cursor reuse after a changed release, profile, filter, ordering version, or
   request digest is rejected by Query Core consistently through every adapter.

## EDS clauses affected

- EDS 5 architecture and dependency direction
- EDS 10 Explorer evidence presentation
- EDS 11 SDK and REST API
- EDS 12.1–12.7 Query Core
- ERS REQ-011, REQ-012, REQ-023, and REQ-024

## Non-goals

This decision does not prescribe a UI framework, REST server deployment, remote
authorization, language SDK beyond the planned Python wrapper, or an alternate
query execution engine.
