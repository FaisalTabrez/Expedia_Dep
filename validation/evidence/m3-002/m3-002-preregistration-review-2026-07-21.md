# M3-002 Version 1.0 preregistration review

**Status:** Passed maintainer review.
**Study:** M3-002 Exact Float32 Cosine Correctness.
**Review date:** 2026-07-21.
**Reviewer:** Faisal Tabrez, Project Maintainer.

## Review checklist

| Required frozen item | Review finding |
|---|---|
| Research question | Present; limited to exact Query Core equality against an independent float32 reference. |
| Primary and null hypotheses | Present and mutually exclusive. |
| OQ-05 claim category | Present; exact query correctness only. |
| Comparison algorithm | Present; canonical SHA-256 first, then fixed field diagnostics. |
| PASS / FAIL / INCONCLUSIVE / ABORTED | Present with task-specific definitions. |
| Score rule | Present; exact `0.0` equality with stated rationale. |
| Explicit exclusions | Present; biological, ANN, performance, portability, and generalization claims are excluded. |
| Evidence retention | Present; raw outputs, digests, incidents, and analysis are required. |
| Execution environment | Bound to `EE-M3-001-v1.1`. |
| Repository checkpoint | Bound to `6183145f8fd6018431c55fd2e4ee7e1001e5fc87`. |
| Release/profile/vector-shard identities | Bound in the controlled corpus manifest. |
| Reference independence | Required by a separate specification; no implementation is present or reviewed as correct yet. |

## Disposition

The Draft is internally consistent with EDS v2.1.1 and the accepted OQ-05
exact-query-correctness requirement. It is approved and frozen as Version
`1.0`. This approval authorizes no reference implementation, oracle
verification, immutable evaluation manifest, comparison execution, result,
analysis, or claim decision. Later changes require a controlled amendment.
