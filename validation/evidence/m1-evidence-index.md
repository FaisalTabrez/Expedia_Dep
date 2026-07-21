# M1 evidence index

**Status:** M1.8 approved; M1 complete as an internal reproducibility
validation milestone.
**Release ID:** `expedia-m1-draft-20260721-v2`
**Release state:** `Draft`
**Scope:** Internal M1 reproducibility validation only.

## Integrity anchors

- ReleaseManifest digest:
  `sha256:66a0ff36d1a15c05de74fb8f66bbc02030172bf8b9d8324a0c919bd964c3f583`
- Vector-shard digest:
  `sha256:69204de55e57d8f3b088bba7dd63a8207c6bf55337d28b4bedc4769f1d8cf0c3`
- Clean-room ValidationBundle digest:
  `sha256:9e4c5264aa0be5b77a4984fef5e0d6de00d1af4467b664dba0f2c92589b7b891`
- Clean-room run-record digest:
  `sha256:9fb44fa97d48e21a6d7946209e059067286e011f2014e943ecf93e2f21b8723b`

## Reviewed evidence

1. The M1 BuildManifest, source-provenance notice, acquisition and
   canonicalization stage outcomes are retained under
   `atlas-builder/manifests/m1/`.
2. The sole profile, plugin descriptor, and Approved Deterministic Execution
   Environment declaration are retained under `profiles/`.
3. M1.6 package assembly is recorded in
   [`m1-draft-package-2026-07-21.md`](m1-draft-package-2026-07-21.md).
4. M1.7 independent read, reconstruction, and failure-path evidence is recorded
   in [`m1-clean-room-validation-2026-07-21.md`](m1-clean-room-validation-2026-07-21.md).
5. The ERS mapping and its explicit M1 boundaries are machine-readable in
   [`specification/requirements/m1-traceability.json`](../../specification/requirements/m1-traceability.json).

## Claim and lifecycle review

The package remains a Draft with no persistent identifier and no public
distribution. This index makes no biological, scalability, retrieval-quality,
or performance claim. It does not authorize Candidate, Published, archive, or
citation status.

## Decision record

The sole M1 Release Owner/Approver approved this evidence gate on
`2026-07-21T04:57:24Z`. The schema-valid durable record is
[`m1-maintainer-decision-2026-07-21.json`](m1-maintainer-decision-2026-07-21.json).
It names the maintainer, decision, Draft release identifier, timestamp, and
rationale. It is external governance evidence bound by this index to the
ReleaseManifest digest; it does not mutate the Draft package.

- Approval-record digest:
  `sha256:780f82c39a8c93debcf9f6d6f6ebed7c3f494b2b981f3cdab50f4aedc66376e7`

M1 is complete. This decision does not authorize Candidate, Published, archive,
citation, or public-distribution status.
