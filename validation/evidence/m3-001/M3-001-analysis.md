# M3-001 Analysis Report

**Status:** Draft analysis — no maintainer claim decision.  
**Study:** M3-001 Deterministic Exact Query Reproducibility.  
**Preregistration:** Version `1.0` (approved, with controlled execution-environment amendment).  
**Evaluation Manifest:** `sha256:6786d1a1e01b2509f7888d1a697461f9b16d2c24b6fffb8b9a049d7d26c87aab`.  
**Execution Environment:** `EE-M3-001-v1.1`.  
**Repository Commit:** `6183145f8fd6018431c55fd2e4ee7e1001e5fc87`.

## 1. Scope

This report analyzes only the preregistered deterministic exact-query
reproducibility study. It does not evaluate biological meaning, retrieval
usefulness, embedding quality, comparative performance, ANN quality, latency,
scalability, generalization, or any other scientific or performance property.

## 2. Inputs verified

| Verified identity | Value |
|---|---|
| M1 Draft release digest | `sha256:fb18e65424f9b1f8978b6460917f799f39137659ae83d3074d2b01a491eca37b` |
| EmbeddingProfile digest | `sha256:5679461d5a4482b48b90e97615d9661e84c2ac7c3b01253e7be4d7909a294294` |
| Vector-shard digest | `sha256:69204de55e57d8f3b088bba7dd63a8207c6bf55337d28b4bedc4769f1d8cf0c3` |
| Dependency lock digest | `sha256:332b9b0ae251547a0db50deb717d2c778a3e2e5be40644255598aef783b18765` |
| Effective executable digest | `sha256:5912d0884b23c0343983a864c6064242391e2265536f50b88624857e353882c9` |
| Frozen M2 implementation | `6183145f8fd6018431c55fd2e4ee7e1001e5fc87` |

## 3. Execution observations

- Pre-execution environment verification completed under `EE-M3-001-v1.1`.
- Frozen-release verification completed through the Verified Release Adapter.
- Three independent Python-process replicates executed and their raw evidence
  was retained.
- The original failed executable verification is retained as a historical
  incident.
- No execution deviation was recorded after the approved
  execution-environment amendment.

## 4. Comparison observations

| Preregistered comparison category | Observation |
|---|---|
| Canonical request digests | Identical |
| QueryResult digests | Identical |
| Ordered record IDs | Identical |
| Decoded scores | Identical |
| Provenance fields | Identical |
| Warning sequences | Identical |
| Cursor behavior | Identical |
| Typed error behavior | Identical |
| Replicate consistency | Identical |

No additional metrics, inferential statistics, confidence intervals, p-values,
or hypothesis tests were calculated.

## 5. Incident review

The initial `EE-M3-001-v1` pre-execution verification failed because the
originally bound executable could not import the frozen `jsonschema` dependency
required by the M1 Release Reader. No release verification, query execution, or
replicate occurred before that failure. The incident was retained, and the
controlled execution-environment amendment bound `EE-M3-001-v1.1` to the
lock-resolved executable without changing methodology or claim boundaries.

## 6. Deviations

No deviations from the approved preregistration were observed after the
approved execution-environment amendment.

## 7. Observed outcome

**Observed study outcome: PASS.**

This records the result of the preregistered deterministic equality rule only.
It is not a maintainer decision that the study claim is accepted.

## 8. Evidence inventory

| Artifact | SHA-256 digest |
|---|---|
| Approved preregistration | `sha256:aa5830deccaa73390787ce5e214c5f97c71ee0b4b3a98c58a92f9c74010f76b9` |
| Effective evaluation manifest | `sha256:6786d1a1e01b2509f7888d1a697461f9b16d2c24b6fffb8b9a049d7d26c87aab` |
| Environment-amendment approval | `sha256:abf816d5065d83e0ececeed0c6c74c529faca262f3e338d0f268bf188472ab8f` |
| Environment record | `sha256:bff94460b612e35dde13ce7270beb8da8e061915cdc9ae3aa4f96062567702e0` |
| Evaluation lock | `sha256:fad935b6f59f0d86a00a50b7cbf20cfea420351f7691294c89464176a359ca26` |
| Release verification | `sha256:7558364993f1d26e6e2976ebe744a54590b53862aed1c4e8a3c08fcdf14ebb6f` |
| Replicate 1 bundle inventory | `sha256:ce1e3b0d14b4356a4a51788117eae285b20e03a24bd39fb2455dbf1c19ced536` |
| Replicate 2 bundle inventory | `sha256:ff60c116686561c17158b42d7de3fd5fdb0cdc21a5b6e68a1a89ad03d5125b8e` |
| Replicate 3 bundle inventory | `sha256:35ae64aebb364ac960a9a856689c78747814ac27361dc8f7450208b11064fcc2` |
| Comparison artifact | `sha256:35513e730cd1d3fadefd5a5dc64dd113b6eae52a978620a2193b5919dc1099a8` |
| Incident log | `sha256:8dbdcf13328e2b809bbb4866cdc16807f9894deaf6351dd3fd270aafa895a6ea` |

## 9. Claim boundary reminder

This report records only the observations required by the approved
preregistration. It does not establish biological meaning, retrieval
usefulness, comparative superiority, scalability, latency, ANN quality,
generalization, or any scientific conclusion beyond the preregistered
engineering-conformance scope.

## 10. Next governance step

This report does not constitute maintainer acceptance of the study claim. The
evidence is ready for the M3.5 maintainer claim decision under the accepted
OQ-05 evidence policy.
