# M2 completion decision record

**Decision:** Approved internal M2 completion gate.
**Maintainer:** Faisal Tabrez, Project Maintainer.
**Completion date:** 2026-07-21.
**Implementation commit reviewed:** `f5e1e21b6450e95a9a9f55b637a1b029068c9275` (`feat(explorer): complete M2.6 provenance presentation`).
**Governing specification:** EDS v2.1.1; ERS v1.0.
**Repository checkpoint:** `m2.0.0-complete`.

## Decision

The maintainer accepts M2 as complete at the repository checkpoint above. The
schema-valid approval record is
[`m2-completion-approval-2026-07-21.json`](m2-completion-approval-2026-07-21.json).

The reviewed implementation commit is the final M2 implementation commit.
The checkpoint tag is created after this decision record and its evidence are
committed; this avoids claiming that an uncommitted document is already bound
to a repository object.

## Frozen M2 retrieval boundary

At this accepted M2 boundary, the following are frozen except through a
controlled governance revision:

- QueryRequest, QueryResult, FilterExpression, Cursor, and Error/Warning
  contract semantics;
- canonical request interpretation, filter evaluation, ordering, and cursor
  binding;
- exact float32 cosine as the sole M2 reference search path;
- required result provenance and evidence fields;
- SDK and REST semantic delegation to Query Core; and
- the Explorer boundary as a presentation consumer of Core-owned results.

This is a governance freeze of the accepted M2 behavior, not a new embedding
profile, index, release format, or scientific claim. ADR-016 remains the
semantic-authority rule for any future controlled revision.

## Disposition register

| Item | M2 completion status |
|---|---|
| ADR-010 | Accepted; implemented by the verified local release boundary. |
| ADR-011 | Accepted; implemented by the exact cosine reference path. |
| ADR-016 | Accepted; implemented by Core-owned semantics and adapter conformance. |
| OQ-11 | Resolved for M2; implemented by the accepted filter grammar, canonical request interpretation, and local-fixture cost limits. |
| OQ-04 | Deferred; no ANN adapter, recall target, or default index is selected. |
| OQ-05 | Unresolved; M3 must define evidence required for usefulness claims. |
| OQ-08 | Deferred; no cross-profile comparison or BridgeProfile is introduced. |
| OQ-09 | Unresolved for M4/M5 archival policy. |
| OQ-10 | Unresolved for trusted public distribution and plugin trust policy. |

## Boundary

This completion decision does not convert the authoritative M1 package from
Draft to Candidate or Published, authorize public distribution or citation,
or support a biological, recall, latency, throughput, scalability, or
usefulness claim. M3 remains planning and evidence work only until a separate
evaluation-governance gate is accepted.
