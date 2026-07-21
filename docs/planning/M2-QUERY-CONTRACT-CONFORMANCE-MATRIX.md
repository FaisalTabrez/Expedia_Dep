# M2 Query Contract Conformance Matrix

**Status:** Required M2.1 verification artifact; not started.
**Gate:** M2.2 verified-release-adapter work MUST NOT begin until every row is
`Pass` with linked fixture and test evidence.

This matrix applies the M1 contract-first discipline to Query Core. A `Pass`
requires both positive and negative fixtures, executable tests, and an evidence
link. It is not satisfied by schema shape alone.

| Contract | Positive fixtures | Negative fixtures | Required evidence | Status |
|---|---|---|---|---|
| QueryRequest | Not started | Not started | Schema validation plus canonical-request-digest tests | Not started |
| QueryResult | Not started | Not started | Schema validation plus required provenance/context tests | Not started |
| Filter | Not started | Not started | OQ-11 grammar, state-distinction, unsupported-filter, and cost-limit tests | Not started |
| Cursor | Not started | Not started | Release/request/order/last-key binding and invalidation tests | Not started |
| Errors and warnings | Not started | Not started | Typed error/warning fixtures; no silent semantic weakening tests | Not started |

## Pass criteria

Each row may be changed to `Pass` only when all of the following are recorded:

1. A positive fixture validates the accepted contract semantics.
2. Negative fixtures demonstrate each mandatory rejection or typed error path.
3. The locked contract suite executes the fixtures and names the test module.
4. The fixture and test locations are linked in this matrix.
5. The M2.1 review confirms the result does not introduce ANN, public-release,
   biological, performance, or scalability claims.

## M2.2 release condition

M2.2 may start only after the matrix has five `Pass` rows and an M2.1 approval
record references the completed matrix. A failed or incomplete row blocks the
verified release adapter rather than being waived implicitly.
