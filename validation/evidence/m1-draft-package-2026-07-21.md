# M1.6 Draft package evidence

**Status:** Passed M1.6 assembly; M1.7 independent validation pending.
**Release ID:** `expedia-m1-draft-20260721-v2`
**State:** `Draft`
**Scope:** Internal M1 reproducibility validation only; not a public or
citable Atlas Release.

## Frozen package identity

The local Draft package directory is intentionally retained outside Git because
it contains source-derived canonical sequence artifacts. It is rooted by this
ReleaseManifest digest:

```text
sha256:66a0ff36d1a15c05de74fb8f66bbc02030172bf8b9d8324a0c919bd964c3f583
```

The package StageOutcome digest is:

```text
sha256:8dc13cc8281b4118844122de085c55da6eff42b1f5e57d9bae2f877d3fb2c996
```

The Draft package contains 50 manifest-addressed payload artifacts (46,126,556
bytes), plus the root `release-manifest.json` integrity anchor. The manifest
deliberately does not include itself: a self-digest would be circular.

## Inputs and retained provenance

- M1.5 artifact-bundle digest:
  `sha256:16a71fbd774b3710ecce35259536b2a5fc58a36cbbbffad68cf582acec122abe`
- M1 vector-shard digest:
  `sha256:69204de55e57d8f3b088bba7dd63a8207c6bf55337d28b4bedc4769f1d8cf0c3`
- Embedding profile:
  `m1-generanno-prokaryote-0.5b-assembly-v1`
- Approved execution environment:
  `m1-generanno-t4-cuda12.1-fp32-deterministic-v1`
- Record count: 12 canonical NCBI RefSeq complete prokaryotic assemblies.

The package retains the source provenance and internal-use restriction, M1.3,
M1.4, M1.5, and M1.6 stage outcomes, profile and plugin declarations, ADEE
declaration, JSON Schema pack, model MIT notice, and accelerator-validation
evidence.

## Passed checks

1. The Packager accepted only the exact four-file M1.5 artifact bundle and
   rechecked vector dimensions, finite values, L2 normalization, row mapping,
   shard digest, successful stage outcome, and ADEE provenance.
2. Every package payload was assigned a relative path, media type, contract
   version, byte size, and SHA-256 digest in the ReleaseManifest.
3. Credential filename and content-marker checks passed.
4. The produced ReleaseManifest passed both the canonical Python binding and
   `release-manifest/0.1.0` JSON Schema validation.
5. Re-verification of all 50 payload digests passed after package assembly.

## Boundary

This record does not authorize Candidate, Published, citation, public
distribution, or M1 completion. M1.7 must verify the Draft package in a clean
environment and exercise its required failure paths.
