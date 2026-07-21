# Query Core

Query Core is the sole owner of release query semantics under EDS section 12
and ADR-016. It opens verified immutable releases and returns provenance-complete
results. Explorer, SDK, and REST adapters must not reimplement its semantics.

M2.2 provides the ADR-010 local trust boundary: it uses the established M1
Release Reader, snapshots only manifest-addressed artifacts into an immutable
`VerifiedRelease`, and reports typed verification failures. Query execution,
filtering, ranking, pagination, caching, SDK, REST, and Explorer adapters are
not implemented here.
