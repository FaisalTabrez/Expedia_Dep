# OQ-11: M2 v1 filter grammar and query-cost limits

**Status:** Proposed disposition — pending maintainer acceptance for M2.
**Question:** What filter grammar and cost limits are supported in v1 Query
Core?

## Decision

M2 SHALL use the following deterministic JSON filter grammar. A filter is a
single object with exactly one operator key:

```text
Filter ::= {"all": [Filter, ...]}              # one or more operands
         | {"any": [Filter, ...]}              # one or more operands
         | {"not": Filter}
         | {"eq": {"field": FieldRef, "value": Scalar}}
         | {"in": {"field": FieldRef, "values": [Scalar, ...]}}
         | {"range": {"field": FieldRef, "gte"|"gt": Number,
                       "lte"|"lt": Number, "unit": String}}
         | {"state": {"field": FieldRef,
                       "is": "present"|"missing"|"unavailable"|"false"}}
         | {"relation": {"relation_type": String,
                           "direction": "outbound"|"inbound",
                           "artifact_id": String?}}

FieldRef ::= {"kind": "canonical",
              "name": "record_id"|"entity_id"|"canonicalization_id"|
                      "source_provenance_id"|"lifecycle_state"}
           | {"kind": "annotation", "source": String, "predicate": String}
Scalar ::= String | Number | Boolean
```

`range` SHALL include one lower bound and one upper bound, both numeric, and a
unit. It is valid only for a field whose contract declares numeric values in
that unit; otherwise Query Core returns `unsupported_filter`. Annotation and
relation forms are part of the v1 grammar but return `unsupported_filter` or
`unsupported_relation` when the verified release lacks the required declared
assertion or relation artifact. They MUST NOT be ignored.

The `state` values are distinct:

- `missing`: no value for the FieldRef occurs in the selected record.
- `unavailable`: the field/assertion is declared but has no evaluable value or
  lacks comparable source-defined semantics.
- `false`: a Boolean false value or an explicit negative assertion occurs.
- `present`: an evaluable non-null value occurs.

If multiple matching relation derivations exist and `artifact_id` is absent,
Query Core SHALL return `ambiguous_relation` rather than choose by recency.
Free-form SQL, arbitrary field paths, implicit coercion, and client-side filter
interpretation are prohibited.

For M2’s local M1 fixture, the explicit limits are:

| Limit | Value | Required behavior on excess |
|---|---:|---|
| Canonical UTF-8 request size | 16 KiB | `query_cost_exceeded` |
| Filter predicate nodes | 32 | `query_cost_exceeded` |
| Boolean nesting depth | 8 | `query_cost_exceeded` |
| `in` values | 100 | `query_cost_exceeded` |
| Relation depth | default 1; maximum 2 when explicitly requested | `query_cost_exceeded` |
| Traversed edges | 1,000 | `query_cost_exceeded` |
| Page size | default 12; minimum 1; maximum 12 | `query_cost_exceeded` |
| Exact similarity candidates | one profile, one verified shard, at most 12 rows | `query_cost_exceeded` |

Offset pagination is prohibited. Pagination uses only the EDS cursor contract.
These limits are an M2 local-fixture safety boundary, not a scalability claim or
a future public-service policy.

## Rationale

EDS 12.3 requires a minimum v1 surface that distinguishes missing,
unavailable, and explicitly false/negative values, while prohibiting free-form
SQL and silent filter loss. M2 needs a small canonical grammar and bounded
resource behavior before implementation so Core, SDK, REST, and Explorer cannot
invent conflicting filter semantics. The limits match the verified twelve-row
M1 fixture and intentionally do not imply a production capacity target.

## Consequences

- QueryRequest and QueryResult contracts can be completed without guessing
  filter semantics.
- Unsupported annotation or relation predicates are visible, typed outcomes;
  they are not treated as false or silently discarded.
- M2 exact search remains bounded to the one M1 profile/shard fixture. Larger
  release, ANN, remote-service, or public cost policies require later evidence
  and governance decisions.
- SDK, REST, and Explorer must pass Filter objects to Query Core unchanged.

## Acceptance criteria

1. Contract fixtures validate every grammar form and reject multiple operator
   keys, unknown canonical fields, arbitrary paths, malformed ranges, missing
   units, empty Boolean arrays, and unsupported scalar types.
2. Tests distinguish `missing`, `unavailable`, and `false` without coercion.
3. A filter an adapter cannot evaluate is enforced by Query Core or returns the
   declared typed unsupported error; it is never ignored.
4. Every cost limit has a deterministic `query_cost_exceeded` failure test.
5. Cursor tests prove that release, canonical request digest, ordering, and
   last-emitted key remain bound as required by EDS 12.4.

## EDS clauses affected

- EDS 12.2 request/result interfaces
- EDS 12.3 filtering and traversal
- EDS 12.4 ranking, exactness, and pagination
- EDS 12.5 caching keys and invalidation
- EDS 12.6 extension behavior
- EDS Table 40 OQ-11 and ERS REQ-023–024

## Non-goals

This draft does not add annotation providers, relation derivation, full-text
search, SQL, ANN filtering, remote rate limiting, or a public-service capacity
policy.
