# M1.7 clean-room validation evidence

**Status:** Passed M1.7; M1.8 approved the retained Draft package on
2026-07-21.
**Release ID:** `expedia-m1-draft-20260721-v2`
**State:** `Draft`
**Scope:** Internal M1 reproducibility validation only. This record does not
approve, publish, or assign a citation identifier to the release.

## Validation boundary

The reader ran in `C:\\tmp\\expedia-m1-clean-room-20260721-v1` with only a copy
of the frozen Draft package and a copy of the committed M1.7 reader source.
It read the package directory and its embedded schemas only. It did not use
Builder workspaces, model snapshots, acquisition inputs, or release-generation
code.

The ValidationBundle is external evidence. Adding it to the frozen Draft
package would require adding its digest to the ReleaseManifest, while the
bundle itself must bind that manifest digest; that creates a circular integrity
dependency. The immutable package therefore remains unchanged.

## Package and run identities

- ReleaseManifest digest:
  `sha256:66a0ff36d1a15c05de74fb8f66bbc02030172bf8b9d8324a0c919bd964c3f583`
- Reconstructed logical release digest:
  `sha256:125df7442ff77c06b21d36abb7733cc20f10609bd295d05133801e323418ab08`
- Vector-shard digest:
  `sha256:69204de55e57d8f3b088bba7dd63a8207c6bf55337d28b4bedc4769f1d8cf0c3`
- ValidationBundle ID:
  `expedia-m1-draft-20260721-v2-clean-room-v2`
- ValidationBundle digest:
  `sha256:9e4c5264aa0be5b77a4984fef5e0d6de00d1af4467b664dba0f2c92589b7b891`
- Clean-room run record digest:
  `sha256:9fb44fa97d48e21a6d7946209e059067286e011f2014e943ecf93e2f21b8723b`

The generated external evidence is retained locally outside Git at
`workspaces/m1/validation/expedia-m1-draft-20260721-v2-clean-room-v2/` because
it is bound to source-derived internal M1 package artifacts.

## Passed clean-room checks

1. The package-embedded `ReleaseManifest` schema, exact 50-payload inventory,
   file sizes, and SHA-256 digests passed.
2. Twelve canonical GenomeRecordVersions and twelve AtlasEntities passed schema,
   eligibility, digest, and referential-integrity checks.
3. Twelve EmbeddingInstances and the 12 × 1280 float32 vector shard passed
   schema, row-mapping, finite-value, L2-normalization, and digest checks.
4. The reader reconstructed the logical release graph deterministically from
   records, entities, embedding instances, and the vector-shard digest.
5. Packaged source provenance, license restriction, profile, plugin,
   Approved Deterministic Execution Environment
   (`m1-generanno-t4-cuda12.1-fp32-deterministic-v1`), BuildManifest selection,
   and successful upstream stage envelopes passed.
6. The package contained no forbidden credential filenames or credential
   markers.

The external ValidationBundle also passed
`validation-bundle/0.1.0` JSON Schema validation.

## Failure-path evidence

The contract suite exercises a changed vector payload, an unsafe manifest path,
and a non-Draft state. In addition, a temporary copy of this Draft package had
one vector byte changed. The independent reader rejected it at the manifest
artifact-digest gate:

```text
ReleaseReaderError: manifest-addressed artifact digest mismatch:
embeddings/vectors.float32le
```

The canonical Draft package was not modified.

## M1.7 acceptance result

The Draft package opens offline after its packaged inputs are present, validates
all required schemas and digests, reads the canonical tables and vectors,
reconstructs a deterministic logical release digest, and rejects a material
payload change. M1.7 is complete. M1.8 approved retention of the package as a
Draft; no Candidate or Published release has been created.
