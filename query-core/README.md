# Query Core

Query Core is the sole owner of release query semantics under EDS section 12
and ADR-016. It opens verified immutable releases and returns provenance-complete
results. Explorer, SDK, and REST adapters must not reimplement its semantics.

M2.2 provides the ADR-010 local trust boundary: it uses the established M1
Release Reader, snapshots only manifest-addressed artifacts into an immutable
`VerifiedRelease`, and reports typed verification failures.

M2.3 adds the sole ADR-011 reference executor: exact float32 inner products
over the declared, L2-normalized vector shard. It accepts only an
`query-request/0.1.0` similarity request for the verified release's declared
profile and returns provenance-complete `query-result/0.1.1` envelopes. Equal
scores are ordered by stable record ID after descending score. This is a local
reference path, not a performance, scalability, recall, biological, or public
release claim.

Filtering, traversal, cursor execution, caching, SDK, REST, and Explorer
adapters are still not implemented. They receive typed, non-fallback errors at
the M2.3 Core boundary.
