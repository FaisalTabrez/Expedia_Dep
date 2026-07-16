# Storage adapters

Storage provides portable release-table, blob, vector-shard, and optional index
adapters. The baseline defined by EDS section 14 is Parquet, Arrow, DuckDB,
content-addressed blobs, and profile-scoped derived vector indexes.

Storage does not define Atlas identity, profile semantics, or query behavior.
No adapter implementation is present in this skeleton.
