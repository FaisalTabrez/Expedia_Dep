# M1 GENERanno reference runner

This is the M1 CPU/float32 reference environment for
`m1-generanno-prokaryote-0.5b-assembly-v1`. Its `uv.lock` must be used without
dependency upgrades. It deliberately excludes FlashAttention and GPU execution
from the reference profile.

The lock captures packages only; it does not download model weights. M1.5 must
record the resolved wheel artifacts, runtime SBOM, model snapshot digest, and
determinism evidence with its StageOutcome before emitting any embedding.

## M1.5 execution order

This environment is the only release-qualified execution path. It is CPU-only
and intentionally evaluates one window at a time. The T4 harness under
`validation/colab/` is validation evidence only and must not create a release
vector shard or `EmbeddingInstance` records.

1. Run the one-record gate twice in separate Python processes using
   `expedia_atlas_builder.embedding`. Compare the resulting vector files
   byte-for-byte. Retain the timing files as evidence.
2. Only after that comparison passes, run the complete 12-record stage below.
3. If the process stops before completion, rerun the exact command with the
   same workspace. The explicit resume state verifies the same record table,
   profile, model-weight digest, build identifier, and runner provenance before
   it skips already written rows. A changed input requires a new workspace.

From this directory, create the locked environment and make the Builder source
available without installing an alternate package:

```powershell
uv sync --frozen
$env:PYTHONPATH = (Resolve-Path "..\\..\\..\\atlas-builder\\src")
```

The one-record gate should use the smallest canonical record,
`GCF_000023265.1`, and a fresh output directory for each run:

```powershell
uv run --frozen python -m expedia_atlas_builder.embedding `
  --canonical ..\\..\\..\\workspaces\\m1\\canonicalize\\run-20260716\\canonical\\GCF_000023265.1.txt `
  --snapshot ..\\..\\..\\workspaces\\m1\\models\\generanno-prokaryote-0.5b-base-d02db0f `
  --weight-digest sha256:ed1cfcc64fe890a6a72017d24c02ad6af3b15c9cfa6950e850908cca92882d51 `
  --output ..\\..\\..\\workspaces\\m1\\embedding\\cpu-gate-run-1\\vector.json `
  --timing-output ..\\..\\..\\workspaces\\m1\\embedding\\cpu-gate-run-1\\timings.json
```

For the second run, change both `cpu-gate-run-1` paths to `cpu-gate-run-2` and
compare `vector.json` using `Get-FileHash -Algorithm SHA256`. The hashes must
match exactly. Do not compare these CPU vectors to T4 validation vectors.

After the gate passes, run the complete stage in a new workspace:

```powershell
uv run --frozen python -m expedia_atlas_builder.embedding_stage `
  --record-versions ..\\..\\..\\workspaces\\m1\\canonicalize\\run-20260716\\genome-record-versions.jsonl `
  --canonical-directory ..\\..\\..\\workspaces\\m1\\canonicalize\\run-20260716\\canonical `
  --snapshot ..\\..\\..\\workspaces\\m1\\models\\generanno-prokaryote-0.5b-base-d02db0f `
  --weight-digest sha256:ed1cfcc64fe890a6a72017d24c02ad6af3b15c9cfa6950e850908cca92882d51 `
  --workspace ..\\..\\..\\workspaces\\m1\\embedding\\cpu-release-run-1 `
  --build-id m1-cpu-release-run-1
```

The final stage emits the float32 vector shard, vector-shard manifest,
EmbeddingInstance JSONL, and a successful stage envelope. These artifacts are
still inputs to M1.6 Draft packaging; they are not an Atlas Release by
themselves.
