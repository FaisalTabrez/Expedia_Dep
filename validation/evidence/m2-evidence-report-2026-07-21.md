# M2 completion evidence report

**Status:** Evidence accepted by the M2 completion decision.
**Governing specification:** EDS v2.1.1 sections 5.1, 8, 10-12, and 15.3; ERS
v1.0 REQ-006, REQ-011, REQ-015, and REQ-021-024.
**Implementation commit:** `f5e1e21b6450e95a9a9f55b637a1b029068c9275`.
**Authoritative release fixture:** M1 Draft successor
`expedia-m1-draft-20260721-v3`; it remains internal and non-public.

## M2.1 through M2.6 summary

| Work package | Completion evidence |
|---|---|
| M2.1 contracts | Accepted QueryRequest, QueryResult, FilterExpression, Cursor, and Error/Warning contracts; five-pass positive/negative fixture matrix; controlled QueryResult and FilterExpression corrections preserved the historical schemas. |
| M2.2 verified release adapter | Only the existing Release Reader verification boundary produces immutable manifest-addressed snapshots; verification failures are typed. |
| M2.3 exact cosine | Profile-scoped normalized vectors are ranked by deterministic float32 inner product with score-descending, stable-record-ID ordering and required provenance. |
| M2.4 filters and cursors | Query Core owns canonical request normalization, supported canonical filters, typed unsupported artifact-dependent forms, bounded traversal selection, and release/request/order/last-key cursor binding. |
| M2.5 SDK and REST | The local Python SDK and `/v1/query` REST transport are thin delegates; the shared corpus preserves success, typed error, and cursor semantics. |
| M2.6 Explorer | The framework-neutral presentation boundary consumes Core/SDK results, preserves provenance/evidence/typed errors, and performs no independent query or release-trust behavior. |

## Verification runs

The following commands were run from the repository root on 2026-07-21 against
the implementation commit above:

```text
uv run --group test --python <bundled-python> python -m unittest discover -s tests\\contract -p "test_*.py" -v
Ran 86 tests — OK

uv run --group test --python <bundled-python> python -m unittest discover -s tests\\conformance -p "test_*.py" -v
Ran 7 tests in 2.799s — OK
```

The contract suite covers the M2 governance decisions, M2.1 schemas and
fixtures, verified-release failures, exact cosine behavior, canonical filters,
cursors, profile compatibility, result provenance, and the M1 fixture boundary.
The separate conformance suite proves the M2.5 Core/SDK/REST corpus and M2.6
Explorer preservation behavior.

## Architecture invariants preserved

- Immutable release data is trusted only through the local Reader verification
  boundary (ADR-010).
- Exact cosine remains the sole M2 reference search implementation (ADR-011).
- Query Core is the only semantic authority; SDK, REST, and Explorer cannot
  reinterpret filtering, ranking, cursors, trust, or provenance (ADR-016).
- Equivalent JSON formatting and member ordering have one canonical request
  interpretation under OQ-11.
- The M1 Draft fixture has not been altered, and M2 adds no embedding profile,
  index artifact, model behavior, or release-state change.

## Deferred items

OQ-04, OQ-05, OQ-08, OQ-09, and OQ-10 remain outside M2. In particular, the
evidence does not establish ANN recall, retrieval usefulness, biological
interpretation, a preferred profile, remote-service behavior, public-release
licensing, archival policy, or public-distribution trust roots.

## Acceptance conclusion

The M2 exit criteria are satisfied: the shared adapter corpus is equivalent,
cursors are bound and invalidated by Core, Explorer is a provenance-first
consumer, and no unsupported claim has been added. The governing approval and
frozen-boundary statement are recorded in
[`m2-completion-decision-2026-07-21.md`](m2-completion-decision-2026-07-21.md).
