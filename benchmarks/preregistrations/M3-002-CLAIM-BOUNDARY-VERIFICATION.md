# M3-002 claim-boundary verification

**Status:** Draft planning verification. Not study approval, execution evidence,
analysis, or claim decision.  
**Study:** M3-002 Exact Float32 Cosine Correctness.

## OQ-05 mapping

| Item | Verified disposition |
|---|---|
| Proposed claim category | Exact query correctness |
| Required OQ-05 evidence | Exact-reference fixtures |
| Study baseline | Frozen M2 exact float32 cosine Query Core at `6183145f8fd6018431c55fd2e4ee7e1001e5fc87` |
| Independent comparator | Separately specified float32 reference outside Query Core |
| Allowed claim if supported | Equality of outputs under the preregistered corpus and recorded conditions only |
| Execution state | Prohibited pending approval, immutable manifest, and independent implementation review |

## Boundary check

M3-002 does not seek deterministic-retrieval reproducibility evidence already
addressed by M3-001. It does not seek biological, comparative, ANN, resource,
portability, or generalization evidence. Its independent reference is an
exact-reference fixture required by the single OQ-05 exact-query-correctness
row. Therefore it satisfies only that evidence requirement.

No claim outcome, model selection, method recommendation, or architecture
change is introduced by this verification.
