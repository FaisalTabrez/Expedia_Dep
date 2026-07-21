# Known limitations

**Status:** Current after the M1 internal Draft evidence-gate approval.

These are explicit scope boundaries, not defects silently omitted from the
record.

## Release and licensing

- The M1 package is an internal `Draft`, not a Candidate or Published Atlas
  Release. It has no persistent identifier, archive receipt, public
  distribution authorization, or citation status.
- M1 is limited to twelve versioned NCBI RefSeq prokaryotic assemblies. It is
  not a population atlas or coverage claim.
- The retained source notice permits internal reproducibility validation only.
  A public-release licensing matrix remains deferred.

## Representation and execution

- M1 contains exactly one profile:
  `m1-generanno-prokaryote-0.5b-assembly-v1`. It does not establish that this
  profile is preferred, biologically useful, or comparable to another profile.
- Canonical release generation is approved only for the declared deterministic
  T4 environment. CPU execution reached the validated execution boundary but is
  operationally impractical for the smallest assemblies under the frozen
  profile.
- The implementation supports one pinned descriptor rather than a general
  plugin host or plugin trust-root policy.

## Query and presentation

- M2 now has a local Query Core API, canonical filtering, exact ranking,
  pagination, and thin local SDK/REST adapters. Caching, remote deployment,
  HTTP-client configuration, and Explorer behavior remain deferred.
- No ANN adapter, recall target, default index, BridgeProfile, graph traversal,
  annotation workflow, or derived-relation workflow is implemented.

## Evidence and operations

- M1 validates release integrity and deterministic execution provenance. It
  does not provide benchmark results, biological interpretation, throughput
  claims, scalability claims, availability guarantees, access control, or a
  remote service deployment.
- The M1 single-maintainer governance delegation is expressly limited to M1 and
  expires on entry to M4.

## M2 entry blockers

- ADR-010, ADR-011, and ADR-016 require explicit acceptance before M2 adapters
  or query behavior are implemented.
- OQ-11 must define the v1 filter grammar and query-cost limits before Query
  Core contract acceptance. OQ-04 remains deferred, so M2 must use an exact
  reference path unless a later decision authorizes an evaluated ANN adapter.
