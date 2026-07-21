# Known limitations

**Status:** Current after the M2 internal completion gate.

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
  pagination, thin local SDK/REST adapters, and a framework-neutral
  provenance-first Explorer presentation boundary. Caching, remote deployment,
  HTTP-client configuration, desktop/web UI, projections, and graph display
  remain deferred.
- No ANN adapter, recall target, default index, BridgeProfile, graph traversal,
  annotation workflow, or derived-relation workflow is implemented.
- The accepted M2 retrieval boundary is frozen: contracts, exact cosine
  reference behavior, provenance, cursors, and adapter/Explorer delegation may
  change only through a controlled governance revision.

## Evidence and operations

- M1 validates release integrity and deterministic execution provenance. It
  does not provide benchmark results, biological interpretation, throughput
  claims, scalability claims, availability guarantees, access control, or a
  remote service deployment.
- The M1 single-maintainer governance delegation is expressly limited to M1 and
  expires on entry to M4.

## Deferred governance and publication work

- OQ-04 remains deferred, so M2 retains an exact reference path unless a later
  evaluation and controlled decision authorize an ANN adapter.
- OQ-05 remains unresolved; M3 must define the evidence necessary for any
  retrieval-usefulness or biological claim.
- OQ-08 remains deferred unless a future proposal introduces a justified
  cross-profile comparison.
- OQ-09 and OQ-10 remain unresolved for archival policy and trusted public
  distribution. The M1 single-maintainer delegation expires on entry to M4.
