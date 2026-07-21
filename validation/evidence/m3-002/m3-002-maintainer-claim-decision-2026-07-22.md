# M3-002 Maintainer Claim Decision

**Decision:** Supported.
**Claim category:** Exact query correctness (engineering-conformance).
**Study:** M3-002 Exact Float32 Cosine Correctness.
**Decision date:** 2026-07-22.

## Basis

The approved M3-002 Version 1.0 preregistration asked whether the frozen M2
exact cosine Query Core produced identical logical similarity results to an
independently implemented float32 cosine reference over the declared verified
release and profile.

The retained evidence records that:

- the immutable evaluation manifest bound the M2 commit, M1 v3 Draft package,
  profile, vector shard, environment, oracle source, and oracle verification;
- the restarted environment and Release Reader verification completed under
  the retained command-scoped Git trust amendment;
- all 12 preregistered requests produced retained Query Core and oracle
  comparison projections;
- every retained canonical comparison-object digest pair is identical; and
- no retained comparison observation contains a diagnostic-field entry.

The two historical incidents occurred before Release Reader verification and
remain retained. They are not omitted or replaced.

## Supported claim

Under the preregistered M3-002 corpus and recorded execution conditions, the
frozen M2 exact cosine implementation produced outputs identical to an
independently implemented float32 cosine reference.

## Explicit non-support

This decision does not support or establish biological meaning, biological
usefulness, embedding quality, annotation quality, comparative superiority,
ANN quality, recall, latency, throughput, scalability, portability,
cross-platform reproducibility, downstream ML utility, default-method
selection, or generalization.

## Governance effect

M3-002 is accepted as completed exact-query-correctness engineering-conformance
evidence for this preregistered corpus and recorded execution environment only.
No Atlas artifact, embedding profile, M2 contract, Query Core behavior, Release
Reader behavior, oracle, or release state is changed. Claims outside this scope
remain subject to separate preregistered studies and maintainer decisions under
OQ-05.
