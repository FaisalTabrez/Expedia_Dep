# Lessons learned

**Status:** M1 implementation evidence. These observations guide future work;
they are not performance or biological claims.

## Reproducibility and execution

- Determinism must be treated as a release input. The model revision, weight
  digest, tokenizer identity, runtime versions, numeric policy, and execution
  environment all need durable provenance.
- CUDA deterministic execution required `CUBLAS_WORKSPACE_CONFIG` to be set
  before the Python process performed the model operation. Capturing only a
  framework seed is insufficient.
- The frozen profile is computationally expensive on CPU. The observed CPU
  reference run was approximately 39.6 CPU-hours for the smallest assembly, so
  the approved deterministic T4 path was necessary for practical M1 release
  generation. This is an operational observation, not a throughput benchmark.

## Artifact and release engineering

- Content digests, exact row mappings, and package inventory checks exposed
  integrity failures early and made the reader independent from the Builder
  workspace.
- An external ValidationBundle avoids a self-referential digest cycle: placing a
  bundle that binds a ReleaseManifest digest inside the same manifest-addressed
  package would require circular hashes.
- A clean-room reader should be exercised before governance approval, not only
  after packaging succeeds in the Builder environment.

## Governance and scope control

- Explicitly recording scope-bounded and not-exercised requirements prevents an
  M1 Draft from being represented as a public release or a complete Query Core.
- Small, stage-scoped commits made evidence review and rollback reasoning
  tractable. The same discipline should apply to M2 contract and conformance
  work.
- Execution-environment approval can preserve model-independent architecture
  when it changes only operational eligibility and provenance, not profile
  semantics.
