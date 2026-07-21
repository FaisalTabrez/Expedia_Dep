# Python SDK

The Python SDK is a typed, in-process wrapper over an injected Query Core. It
does not own release opening, filtering, ranking, profile compatibility,
pagination, cursors, warnings, errors, or provenance semantics.

`LocalExpediaClient.query()` serializes a mapping as JSON and delegates it to
Core. The returned QueryResult mapping is the Core result. HTTP-client behavior
and remote configuration are intentionally deferred with the service model.
