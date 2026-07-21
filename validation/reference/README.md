# Independent validation references

This namespace contains validation-only, independently implemented reference
oracles. It is not part of Query Core and does not change Atlas, query, SDK,
REST, or Explorer semantics.

## M3-002 float32 cosine oracle

`m3_002_float32_cosine.py` implements the approved M3-002 oracle specification.
It may use the M1 Release Reader and manifest-addressed package artifacts, but
it must not import, call, copy, or reuse Query Core computation, ranking,
ordering, search, cursor, or result-construction code.

It accepts an explicit release/profile/vector binding, re-verifies the local
Draft package, decodes little-endian float32 vector bytes, verifies declared L2
normalization, and produces the preregistered comparison projection. It does
not parse QueryRequest JSON or construct QueryResult data.

This oracle is verified as software infrastructure before M3-002 execution. A
successful unit test verifies only its conformance to the oracle specification;
it is not an M3-002 Query Core comparison result or an exact-query-correctness
claim.
