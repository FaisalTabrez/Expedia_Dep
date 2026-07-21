# M3-002 independent float32 cosine reference specification

**Status:** Draft specification only. No reference implementation is created or
authorized by this document.  
**Study:** M3-002 Exact Float32 Cosine Correctness.

## 1. Isolation boundary

The future implementation SHALL reside under `validation/reference/` and SHALL
NOT import, call, copy, or reuse any Query Core cosine calculation, ranking,
ordering, search execution, cursor handling, or result construction. It SHALL
not import any `expedia_query_core` module. Source review and an import-boundary
test are required before execution.

Permitted reusable components are immutable schemas, the M1 Release Reader,
verified package artifacts, verified vector bytes, and profile declarations.
The reference reads its verified inputs directly; it does not accept a Query
Core `VerifiedRelease` object.

## 2. Inputs and preconditions

The reference accepts only the M3-002 corpus binding: verified release digest,
profile identifier/version/digest, vector-shard digest, record table, embedding
instances, vector-shard row mapping, and float32 vector bytes. It SHALL reject
missing, changed, duplicate, non-finite, dimension-incompatible, or
non-normalized vectors. Profile-declared `l2` normalization is verified, not
reapplied or changed.

## 3. Independent float32 calculation

For each selected query row and each candidate row, the reference SHALL:

1. decode the little-endian float32 vector values independently from the shard;
2. multiply corresponding components, rounding every product to IEEE-754
   binary32;
3. accumulate the score in sequence order, rounding every accumulation to
   IEEE-754 binary32; and
4. retain the decoded float32 score without rounding, formatting, quantization,
   or tolerance adjustment.

The reference SHALL use a separately written local float32-rounding primitive
and SHALL NOT call or copy Query Core's float32 helpers.

## 4. Ranking and tie handling

The reference SHALL construct one candidate row per verified record and order
them by descending decoded float32 score, then ascending canonical `record_id`.
This independently realizes the declared `score-desc-record-id-asc-v1` rule.
No ANN index, cache, filter, traversal, pagination continuation, or alternate
ranking policy is permitted.

## 5. Reference output contract

For each corpus request, the reference emits one canonical comparison object
containing only:

- canonical request digest;
- ordered record IDs;
- decoded float32 scores;
- release digest;
- profile identifier, version, and digest; and
- vector-shard digest and ordering version.

The comparison runner independently projects the same fields from the M2
QueryResult. It canonicalizes each object as defined by the M3-002
preregistration and compares SHA-256 digests before field diagnostics. This
specification defines no result, acceptance outcome, claim, or implementation.
