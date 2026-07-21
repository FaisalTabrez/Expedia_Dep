# M2 Query Contract Conformance Matrix

**Status:** M2.1 evidence complete; maintainer approval pending.
**Gate:** M2.2 verified-release-adapter work MUST NOT begin until every row is
`Pass` with linked fixture and test evidence.

This matrix applies the M1 contract-first discipline to Query Core. A `Pass`
requires both positive and negative fixtures, executable tests, and an evidence
link. It is not satisfied by schema shape alone.

| Contract | Positive fixtures | Negative fixtures | Required evidence | Status |
|---|---|---|---|---|
| QueryRequest | [`m2-query-contract-pack.json`](../../fixtures/valid/m2-query-contract-pack.json) | [`m2-query-contract-pack.json`](../../fixtures/invalid/m2-query-contract-pack.json) | `test_json_schema_conformance.py`; `test_query_contracts.py` canonical digest/default tests | Evidence complete; approval pending |
| QueryResult | [`m2-query-contract-pack.json`](../../fixtures/valid/m2-query-contract-pack.json) | [`m2-query-contract-pack.json`](../../fixtures/invalid/m2-query-contract-pack.json) | `test_json_schema_conformance.py` validates success/error exclusivity and required context/provenance | Evidence complete; approval pending |
| Filter | [`m2-query-contract-pack.json`](../../fixtures/valid/m2-query-contract-pack.json) | [`m2-query-contract-pack.json`](../../fixtures/invalid/m2-query-contract-pack.json) | `test_json_schema_conformance.py`; `test_query_contracts.py` validates canonical Boolean/set deduplication, state grammar, typed unsupported-filter capability, and OQ-11 costs | Evidence complete; approval pending |
| Cursor | [`m2-query-contract-pack.json`](../../fixtures/valid/m2-query-contract-pack.json) | [`m2-query-contract-pack.json`](../../fixtures/invalid/m2-query-contract-pack.json) | `test_json_schema_conformance.py` validates release/request/order/last-key payload bindings and rejects incomplete bindings; cursor encode/decode/invalidation behavior remains M2.4 | Evidence complete; approval pending |
| Errors and warnings | [`m2-query-contract-pack.json`](../../fixtures/valid/m2-query-contract-pack.json) | [`m2-query-contract-pack.json`](../../fixtures/invalid/m2-query-contract-pack.json) | `test_json_schema_conformance.py` validates the closed typed-code sets and rejects unknown codes | Evidence complete; approval pending |

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
record references the completed matrix. Evidence-complete rows are not `Pass`
until maintainer acceptance. A failed or incomplete row blocks the verified
release adapter rather than being waived implicitly.
