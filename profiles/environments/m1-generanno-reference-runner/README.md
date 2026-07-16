# M1 GENERanno reference runner

This is the M1 CPU/float32 reference environment for
`m1-generanno-prokaryote-0.5b-assembly-v1`. Its `uv.lock` must be used without
dependency upgrades. It deliberately excludes FlashAttention and GPU execution
from the reference profile.

The lock captures packages only; it does not download model weights. M1.5 must
record the resolved wheel artifacts, runtime SBOM, model snapshot digest, and
determinism evidence with its StageOutcome before emitting any embedding.
