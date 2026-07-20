# M1.5 T4 accelerator implementation-validation evidence

**Status:** Passed  
**Scope:** M1.5 implementation validation only  
**Release eligibility:** Not eligible for an Atlas Release

## Evidence identity

The reviewed external evidence directory is identified by the SHA-256 digest of
its final `validation-metadata.json`:

```text
sha256:f7b4ba4a6f45eb69120f799a520b297d497705e5380e82ebb109afb7e3f69cff
```

Vectors, per-record vector sidecars, model files, and raw canonical inputs are
intentionally not committed to this repository. They remain non-release
validation evidence.

## Frozen representation verified

| Field | Verified value |
|---|---|
| Embedding profile | `m1-generanno-prokaryote-0.5b-assembly-v1` |
| Model | `GenerTeam/GENERanno-prokaryote-0.5b-base` |
| Model revision | `d02db0f24f2c62fa1efde760217cdf75771b0228` |
| Weight digest | `sha256:ed1cfcc64fe890a6a72017d24c02ad6af3b15c9cfa6950e850908cca92882d51` |
| Window policy | 8,191 bases with `<s>` BOS prefix |
| Pooling | Arithmetic mean of final-layer BOS window vectors |
| Output | 1,280-dimensional little-endian float32, L2 normalized |

## Runtime provenance verified

The evidence records a Tesla T4 with CUDA 12.1, Python 3.12.13, PyTorch
2.4.1+cu121, and Transformers 4.44.0. Deterministic algorithms were enabled,
TF32 was disabled, and `CUBLAS_WORKSPACE_CONFIG=:4096:8` was set before
PyTorch/CUDA initialization. Snapshot retrieval used one worker with a retry
limit of five; these transport controls do not change the model or embedding
profile.

## Passed checks

- Exactly 12 expected M1 records; no missing or duplicate record identifiers.
- All 12 vector files were 5,120-byte, 1,280-dimensional float32 vectors.
- Every vector was finite and L2 normalized within the declared float32
  tolerance.
- Every computed vector digest matched its recorded per-record metadata.
- The final metadata and run-identity records agreed on model, profile,
  algorithm, M1.4 record-table digest, and runtime identity.

## Boundary and remaining work

This result validates the frozen embedding implementation on accelerator
hardware. It does not itself create `EmbeddingInstance` records, create a
vector shard, or authorize M1.6 Draft packaging. EDS v2.1.1 later promoted the
documented T4 environment—not these validation outputs—to an approved M1
release-generation environment. A separate Builder execution must generate
its own canonical artifacts with ADEE provenance.
