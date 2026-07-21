# ADR-011: exact cosine M2 reference search

**Status:** Proposed — pending maintainer acceptance for M2.
**EDS register decision:** Columnar local baseline; evaluate FAISS first.

## Decision

M2 SHALL use exact cosine similarity as its sole reference similarity-search
implementation. It SHALL operate only on verified, profile-scoped vectors that
the selected EmbeddingProfile declares as L2-normalized. The exact score SHALL
be the float32 inner product of those normalized vectors.

Every similarity result SHALL report the release digest, profile identifier,
metric name and direction, `exact` adapter mode, vector-shard artifact digest,
and deterministic ordering policy. Equal scores SHALL be ordered by stable
record identifier after score.

No ANN adapter, FAISS index, quantized transform, or index-specific artifact is
authorized for M2. The EDS instruction to evaluate FAISS remains a later
evaluation activity; it is not a selection, default, or implementation
authorization while OQ-04 is deferred.

## Rationale

M1 supplies one verified, normalized profile vector representation but no
recall/resource evidence for approximate retrieval. Exact cosine is the
profile-declared metric and provides an inspectable reference implementation
against which any future optimization can be evaluated without changing Query
Core semantics.

## Consequences

- M2 has one auditable similarity path with no index-recall claim.
- A request with a mismatched or undeclared profile is rejected; matching vector
  dimension alone does not establish compatibility.
- Indexes remain derived artifacts rather than Atlas data-model fields.
- Future ANN work requires OQ-04 disposition, evaluation evidence, an adapter
  declaration, and conformance against this exact reference path.

## Acceptance criteria

1. Exact results equal a direct float32 inner-product calculation over the
   verified normalized vectors within the declared numeric tolerance.
2. Result envelopes identify the selected profile, cosine metric, higher-score
   direction, `exact` mode, and vector-shard digest.
3. Ranking is deterministic by descending score and then stable record ID.
4. A cross-profile, non-normalized, missing, or unverified vector request fails
   rather than falling back to an undeclared representation or adapter.
5. No M2 code path imports, selects, or reports an ANN/FAISS configuration.

## EDS clauses affected

- EDS 8.2–8.4 profile identity, metric, and profile-scoped storage
- EDS 12.4 ranking, exactness, and deterministic ordering
- EDS 12.6 query extensions
- EDS 12.7 local exact reference implementation strategy
- EDS Appendix C OQ-04
- ERS REQ-004, REQ-006, and REQ-011

## Non-goals

This draft does not declare a default ANN, establish recall or resource targets,
or change the Atlas data model to include an index.
