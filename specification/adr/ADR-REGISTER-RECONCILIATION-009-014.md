# ADR register reconciliation note: ADR-009 and ADR-014

**Status:** Reconciled register metadata; this note is not an ADR and does not
accept, recreate, supersede, or supply missing historical decision content.
**Recorded:** 2026-07-21.
**Scope:** Repository traceability only.

## Finding

EDS v2.1 and EDS v2.1.1 Appendix B list the following proposed ADR entries:

| EDS identifier | EDS register title | EDS register status |
|---|---|---|
| ADR-009 | Experimental methods off default scientific path | Proposed |
| ADR-014 | Preregistered method-evaluation governance | Proposed |

ERS v1.0 references ADR-009 from REQ-014 and ADR-014 from REQ-013; both
requirements are Planned. Neither controlled source identifies a successor,
renamed identifier, or accepted decision record.

## Repository audit evidence

- The initial repository commit `0c4730621f5645cf68474741bc734c943ed0c94b`
  contains `specification/adr/.gitkeep` and `specification/adr/README.md`, but
  no ADR-009 or ADR-014 record.
- A search of all reachable refs, commits, tags, and current files finds only
  roadmap references to the identifiers; it finds no decision text or renamed
  record.
- `git fsck --full --no-reflogs --unreachable` found no dangling object from
  which either record can be recovered.

Accordingly, ADR-009 and ADR-014 are **not recoverable repository artifacts**.
They are EDS-proposed register entries, not accepted historical ADRs.

## Controlled correction

Repository planning documents SHALL describe ADR-009 and ADR-014 as
**Proposed**. They are relevant before a public method claim or a proposal to
promote an experimental method onto a default scientific path. They are not
retroactively accepted and do not supply an M3 execution rule beyond the
accepted OQ-05 evidence policy and an accepted study preregistration.

If a future public/default-method proposal needs either decision, the project
MUST create and review a new ADR from then-current evidence. It MUST NOT claim
to reconstruct an absent historical decision.
