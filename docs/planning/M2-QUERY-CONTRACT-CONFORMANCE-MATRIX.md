# M2 Query Contract Conformance Matrix

**Status:** Approved M2.1 query-contract gate, with controlled QueryResult and
FilterExpression contract-defect corrections.
**Original approval record:** [`m2-query-contract-gate-approval-2026-07-21.json`](../../validation/evidence/m2-query-contract-gate-approval-2026-07-21.json)
**Correction approval:** [`m2-query-result-contract-defect-correction-approval-2026-07-21.json`](../../validation/evidence/m2-query-result-contract-defect-correction-approval-2026-07-21.json)
**Filter correction approval:** [`m2-filter-expression-contract-defect-correction-approval-2026-07-21.json`](../../validation/evidence/m2-filter-expression-contract-defect-correction-approval-2026-07-21.json)
**Gate:** Satisfied. M2.2 verified-release-adapter work is authorized; all
subsequent implementation SHALL preserve these contracts unless a verified
defect receives a controlled governance revision.

This matrix applies the M1 contract-first discipline to Query Core. A `Pass`
requires both positive and negative fixtures, executable tests, and an evidence
link. It is not satisfied by schema shape alone.

| Contract | Positive fixtures | Negative fixtures | Required evidence | Status |
|---|---|---|---|---|
| QueryRequest | [`m2-query-contract-pack.json`](../../fixtures/valid/m2-query-contract-pack.json) | [`m2-query-contract-pack.json`](../../fixtures/invalid/m2-query-contract-pack.json) | `test_json_schema_conformance.py`; `test_query_contracts.py` canonical digest/default tests | **Pass** |
| QueryResult | [`m2-query-contract-pack.json`](../../fixtures/valid/m2-query-contract-pack.json) | [`m2-query-contract-pack.json`](../../fixtures/invalid/m2-query-contract-pack.json) | `test_json_schema_conformance.py` validates success/error exclusivity; controlled `query-result/0.1.1` correction requires metric direction, vector-shard digest, profile version, and profile digest | **Pass** |
| Filter | [`m2-query-contract-pack.json`](../../fixtures/valid/m2-query-contract-pack.json) | [`m2-query-contract-pack.json`](../../fixtures/invalid/m2-query-contract-pack.json) | `test_json_schema_conformance.py`; `test_query_contracts.py`; `test_m2_4_query_core.py` validate controlled `filter-expression/0.1.1`, canonical evaluation, explicit false, and typed unsupported forms | **Pass** |
| Cursor | [`m2-query-contract-pack.json`](../../fixtures/valid/m2-query-contract-pack.json) | [`m2-query-contract-pack.json`](../../fixtures/invalid/m2-query-contract-pack.json) | `test_json_schema_conformance.py`; `test_query_contracts.py`; `test_m2_4_query_core.py` validate opaque encode/decode, release/request/order/last-key binding, continuation, and changed-filter invalidation | **Pass** |
| Errors and warnings | [`m2-query-contract-pack.json`](../../fixtures/valid/m2-query-contract-pack.json) | [`m2-query-contract-pack.json`](../../fixtures/invalid/m2-query-contract-pack.json) | `test_json_schema_conformance.py` validates the closed typed-code sets and rejects unknown codes | **Pass** |

## Pass criteria

Each row may be changed to `Pass` only when all of the following are recorded:

1. A positive fixture validates the accepted contract semantics.
2. Negative fixtures demonstrate each mandatory rejection or typed error path.
3. The locked contract suite executes the fixtures and names the test module.
4. The fixture and test locations are linked in this matrix.
5. The M2.1 review confirms the result does not introduce ANN, public-release,
   biological, performance, or scalability claims.

## M2.2 release condition

M2.2 is authorized because this matrix has five `Pass` rows and the M2.1
approval record above references the completed matrix. The controlled QueryResult
correction retains the historical `query-result/0.1.0` schema and makes
`query-result/0.1.1` normative for subsequent M2 work. A failed or incomplete
row would block the verified release adapter rather than being waived
implicitly.

The controlled FilterExpression correction retains historical
`filter-expression/0.1.0` and makes `filter-expression/0.1.1` normative for
subsequent M2 work. QueryRequest retains its existing semantics and schema
version; its filter reference is updated only to bind the corrected normative
filter contract.
