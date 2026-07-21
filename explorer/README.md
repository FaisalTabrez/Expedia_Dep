# Explorer

Explorer is a release-aware, provenance-first client. It presents release
identity, provenance, profile/metric context, evidence status, and
derived-artifact lineage without becoming an alternate source of query
semantics.

M2.6 supplies `ProvenanceExplorer`, a framework-neutral local presentation
boundary over an injected QueryResult source (normally the local SDK). It
labels similarity rows as canonical records and preserves the Core’s ordering,
warnings, typed errors, provenance, cursor, profile, and metric data. It does
not open releases, select profiles, filter, rank, construct cursors, or infer
missing annotations, relations, scope, citations, compatibility, or projections.

No desktop or web UI, projection, graph, annotation workflow, or remote
Explorer transport is included.
