# REST API

REST is a versioned `/v1` transport adapter over an injected Query Core. It is
not an independent query implementation and never mutates a release.

M2.5 exposes only `POST /v1/query` through a dependency-free local WSGI
adapter. It passes UTF-8 QueryRequest JSON to Core and serializes the resulting
QueryResult envelope; it does not open packages, select a profile, evaluate a
filter, rank vectors, construct cursors, or translate typed query errors.

Remote deployment, authentication, authorization, and access-control policy
remain deferred. The OpenAPI contract is [openapi/v1/openapi.yaml](openapi/v1/openapi.yaml).
