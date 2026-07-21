# M1 Draft successor correction evidence

**Status:** Controlled correction approved; authoritative M1 Draft input for
subsequent M2 milestones.
**Successor release ID:** `expedia-m1-draft-20260721-v3`
**State:** `Draft`
**Scope:** Internal reproducibility validation only; not public or citable.

## Purpose and immutable history

This successor repairs one implementation omission in the historical M1 Draft
package: the absence of a manifest-addressed, schema-valid EmbeddingProfile
record with an explicit profile version. It does not repair or reinterpret any
scientific artifact.

`expedia-m1-draft-20260721-v2` remains immutable historical evidence. The
successor becomes the authoritative M1 Draft package for M2 because it permits
Query Core to bind the existing vector shard to the requested profile identity,
version, and artifact digest.

## Integrity anchors

| Anchor | Digest / value |
|---|---|
| Predecessor ReleaseManifest | `sha256:66a0ff36d1a15c05de74fb8f66bbc02030172bf8b9d8324a0c919bd964c3f583` |
| Successor ReleaseManifest | `sha256:fb18e65424f9b1f8978b6460917f799f39137659ae83d3074d2b01a491eca37b` |
| Added EmbeddingProfile record | `sha256:5679461d5a4482b48b90e97615d9661e84c2ac7c3b01253e7be4d7909a294294` |
| Profile identity / version | `m1-generanno-prokaryote-0.5b-assembly-v1` / `1.0.0` |
| Unchanged vector shard | `sha256:69204de55e57d8f3b088bba7dd63a8207c6bf55337d28b4bedc4769f1d8cf0c3` |
| Isolated-reader ValidationBundle | `sha256:8577e18b71a19e89e4b197a0be940393897971262aca9674e1e219573f6e5f78` |
| Isolated-reader run record | `sha256:3aff57bdb784ee97b4badd2b9e1da87bc6c38a3ace9525921d24a4e89bdf4e7` |

## Controlled change set

- Added `profiles/m1-generanno-prokaryote-0.5b-assembly-v1.json`, a
  schema-valid EmbeddingProfile declaration with explicit `version: 1.0.0`.
- Regenerated only the package-stage envelope and ReleaseManifest to bind the
  added record and successor relationship.
- Set `base_release` to `expedia-m1-draft-20260721-v2`.
- Preserved all 49 predecessor payloads other than the regenerated package
  stage envelope byte-for-byte. The successor contains 51 manifest-addressed
  payload artifacts: the 50 predecessor paths, with the package-stage envelope
  regenerated, plus the profile record.

No canonical record, entity, embedding instance, vector byte, source
provenance, model revision, tokenizer, pooling rule, normalization rule, ADEE,
or governance model was altered.

## Independent package-reader evidence

The package was opened from an isolated working directory using the locked
JSON-Schema verifier dependency. The reader consumed only the successor package
and its embedded schemas. It passed manifest inventory, canonical-record/entity
integrity, vector/embedding integrity, logical reconstruction, provenance and
license policy, and credential scanning.

The generated evidence files remain outside Git with the source-derived Draft
package at:

`workspaces/m1/validation/expedia-m1-draft-20260721-v3-isolated-reader-v1/`

## Approval boundary

The schema-valid approval record is
[`m1-profile-successor-correction-approval-2026-07-21.json`](m1-profile-successor-correction-approval-2026-07-21.json).
It authorizes this controlled correction only. It does not authorize Candidate,
Published, archive, citation, public distribution, biological claims,
retrieval-quality claims, or performance claims.
