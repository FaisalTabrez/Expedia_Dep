# M3-001 Maintainer Claim Decision

**Decision:** Supported.  
**Claim category:** Deterministic retrieval (engineering-conformance).  
**Study:** M3-001 Deterministic Exact Query Reproducibility.  
**Decision date:** 2026-07-21.  
**Maintainer:** Faisal Tabrez, Project Maintainer.

## Basis

M3-001 asked only whether the frozen M2 exact cosine Query Core reproduced
identical logical QueryResults under the recorded execution conditions. The
retained evidence records that the approved execution environment was verified
after the controlled `EE-M3-001-v1.1` correction, the M1 v3 Draft package
passed pre-execution verification, three independent Python-process replicates
were retained, and the preregistered comparison produced the observed `PASS`
outcome. No execution deviation was recorded after the amendment. The original
failed pre-execution check remains retained as historical incident evidence.

## Supported claim

Under the preregistered M3-001 study conditions, the frozen M2 exact cosine
Query Core reproduced deterministic QueryResults for the declared request
corpus using the verified M1 v3 Draft package and the recorded execution
environment.

## Explicit non-support

This decision does not support or establish biological validity, biological
usefulness, embedding quality, annotation quality, comparative superiority,
ANN quality or equivalence, latency, throughput, scalability, generalization
beyond the preregistered corpus, cross-platform reproducibility, portability to
different execution environments, or suitability as a default scientific
method.

## Governance effect

M3-001 is accepted as completed engineering-conformance evidence. The accepted
OQ-05 evidence requirements are satisfied for the deterministic retrieval claim
category by this specific study only. No M1 Draft package, M2 implementation,
or release-state change is authorized. Every future claim outside this scope
requires its own preregistered study and applicable evidence review.

## Evidence binding

- [M3-001 Draft analysis](M3-001-analysis.md)
- [M3.3 raw evidence bundle](execution-v1/)
- [M3-001 Version 1.0 preregistration](../../../benchmarks/preregistrations/m3-001-deterministic-exact-query-reproducibility.md)
- [M3-001 execution-environment amendment](../../../benchmarks/preregistrations/m3-001-v1.0-execution-environment-amendment.md)
