# M1 evidence index

**Status:** M1 remains complete as an internal reproducibility validation
milestone. The controlled v3 successor is the authoritative M1 Draft input for
subsequent M2 milestones.
**Release ID:** `expedia-m1-draft-20260721-v3`
**Release state:** `Draft`
**Scope:** Internal M1 reproducibility validation only.

## Integrity anchors

- ReleaseManifest digest:
  `sha256:fb18e65424f9b1f8978b6460917f799f39137659ae83d3074d2b01a491eca37b`
- Vector-shard digest:
  `sha256:69204de55e57d8f3b088bba7dd63a8207c6bf55337d28b4bedc4769f1d8cf0c3`
- EmbeddingProfile declaration digest:
  `sha256:5679461d5a4482b48b90e97615d9661e84c2ac7c3b01253e7be4d7909a294294`
- Isolated-reader ValidationBundle digest:
  `sha256:8577e18b71a19e89e4b197a0be940393897971262aca9674e1e219573f6e5f78`
- Isolated-reader run-record digest:
  `sha256:3aff57bdb784ee97b4badd2b9e1da87bc6c38a3ace9525921d24a4e89bdf4e7`

## Reviewed evidence

1. The M1 BuildManifest, source-provenance notice, acquisition and
   canonicalization stage outcomes are retained under
   `atlas-builder/manifests/m1/`.
2. The sole profile, plugin descriptor, and Approved Deterministic Execution
   Environment declaration are retained under `profiles/`.
3. The historical v2 M1.6 package assembly is recorded in
   [`m1-draft-package-2026-07-21.md`](m1-draft-package-2026-07-21.md).
4. The historical v2 M1.7 independent read, reconstruction, and failure-path evidence is recorded
   in [`m1-clean-room-validation-2026-07-21.md`](m1-clean-room-validation-2026-07-21.md).
5. The ERS mapping and its explicit M1 boundaries are machine-readable in
   [`specification/requirements/m1-traceability.json`](../../specification/requirements/m1-traceability.json).
6. The v3 successor correction, preservation evidence, and isolated-reader
   verification are recorded in
   [`m1-draft-successor-v3-2026-07-21.md`](m1-draft-successor-v3-2026-07-21.md).

## Claim and lifecycle review

The package remains a Draft with no persistent identifier and no public
distribution. This index makes no biological, scalability, retrieval-quality,
or performance claim. It does not authorize Candidate, Published, archive, or
citation status.

## Decision record

The sole M1 Release Owner/Approver approved the historical v2 evidence gate on
`2026-07-21T04:57:24Z`. The schema-valid durable record is
[`m1-maintainer-decision-2026-07-21.json`](m1-maintainer-decision-2026-07-21.json).
It names the maintainer, decision, Draft release identifier, timestamp, and
rationale. It is external governance evidence bound by this index to the
historical v2 ReleaseManifest digest; it does not mutate the Draft package.

- Approval-record digest:
  `sha256:780f82c39a8c93debcf9f6d6f6ebed7c3f494b2b981f3cdab50f4aedc66376e7`

The controlled v3 successor correction was authorized on `2026-07-21T07:09:50Z`.
Its schema-valid durable record is
[`m1-profile-successor-correction-approval-2026-07-21.json`](m1-profile-successor-correction-approval-2026-07-21.json).
It preserves v2 as historical evidence and designates v3 as the authoritative
Draft input for subsequent M2 work without altering its Draft-only claim and
lifecycle boundary.

M1 is complete. This decision does not authorize Candidate, Published, archive,
citation, or public-distribution status.
