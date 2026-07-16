# Query Core

Query Core is the sole owner of release query semantics under EDS section 12
and ADR-016. It opens verified immutable releases and returns provenance-complete
results. Explorer, SDK, and REST adapters must not reimplement its semantics.

The skeleton exposes interfaces only. Query execution, filtering, ranking,
pagination, caching, and adapters are M2 work.
