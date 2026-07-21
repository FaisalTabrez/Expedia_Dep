# M3 study preregistration template

**Template status:** Draft template only. It is not a study, approval, dataset
manifest, benchmark result, or claim.
**Authority:** EDS v2.1.1 section 13, accepted OQ-05, and the M3 evaluation
plan.

Copy this file to `m3-<study-id>-preregistration.md`. Replace every
`[REQUIRED]` placeholder, obtain maintainer approval, and record the approval
before executing a study. An incomplete or unapproved copy MUST NOT be run.

## 1. Study identity and approval

- Study ID: `[REQUIRED]`
- Version: `[REQUIRED]`
- Status: `Draft | Accepted | Superseded | Rejected`
- Owner: `[REQUIRED]`
- Created at (UTC): `[REQUIRED]`
- Governing EDS/ERS versions: `EDS v2.1.1; ERS v1.0`
- M1 release identity/digest: `[REQUIRED]`
- M2 implementation checkpoint: `m2.0.0-complete` or a declared successor
- Maintainer approval record: `[REQUIRED before execution]`

## 2. Scope and claim boundary

- Research question: `[REQUIRED]`
- Hypothesis: `[REQUIRED]`
- Claim category or categories from `M3-CLAIM-BOUNDARY-REGISTER.md`:
  `[REQUIRED]`
- Allowed result wording if evidence supports the preregistered decision rule:
  `[REQUIRED]`
- Explicitly prohibited wording: `[REQUIRED]`
- Decision rule and task-specific acceptance criteria, including rationale:
  `[REQUIRED]`

State whether the study is claim-seeking or evidence-only. No result-dependent
change to this section is permitted without a versioned, approved amendment.

## 3. Cohort, sources, and ground truth

- Cohort identity and version: `[REQUIRED]`
- Source and license evidence: `[REQUIRED]`
- Inclusion criteria: `[REQUIRED]`
- Exclusion criteria and handling: `[REQUIRED]`
- Train/validation/test or independent hold-out split: `[REQUIRED]`
- Ground-truth definition, curator, and provenance: `[REQUIRED or explain why not applicable]`
- Missing, ambiguous, or conflicting ground-truth handling: `[REQUIRED]`

The M1 twelve-record internal Draft fixture is not an implied evaluation cohort.

## 4. Frozen methods and baselines

- Profile(s): `[REQUIRED]`
- Canonicalization compatibility requirement: `[REQUIRED]`
- Reference retrieval method: `M2 Query Core exact float32 cosine`
- Reference ordering/provenance policy: `M2 accepted behavior`
- Comparator baselines: `[REQUIRED; use “none” only for an evidence-only study]`
- Preprocessing and representation details: `[REQUIRED]`
- Hardware/runtime and reproducibility configuration: `[REQUIRED]`

ANN, quantization, an alternate profile/model, cross-profile comparison,
BridgeProfile, UMAP/clustering, GAT transformation, annotation provider, and
derived relation are out of scope unless separately authorized before this
preregistration is accepted.

## 5. Metrics, uncertainty, and analysis

- Primary metric or metrics and definitions: `[REQUIRED]`
- Secondary metrics: `[REQUIRED or none]`
- Statistical/uncertainty method: `[REQUIRED]`
- Multiple-comparison handling: `[REQUIRED or not applicable]`
- Failure-case analysis: `[REQUIRED]`
- Negative-result handling: `[REQUIRED]`
- Resource observations, if any, and their interpretation limit: `[REQUIRED or none]`

No metric, threshold, transformation, or aggregation may be added after
observing results without a versioned, approved amendment.

## 6. Evidence and reproducibility plan

- Evaluation manifest path and digest policy: `[REQUIRED]`
- Versioned raw-result artifact location and retention policy: `[REQUIRED]`
- Dataset manifest path and digest: `[REQUIRED]`
- Code/environment revision and dependency lock: `[REQUIRED]`
- Expected outputs and checksums: `[REQUIRED]`
- Deviation and incident record location: `[REQUIRED]`
- Analysis artifact location: `[REQUIRED]`

## 7. Pre-execution checklist

- [ ] Every required field is completed.
- [ ] Claim categories map to the M3 claim-boundary register.
- [ ] Dataset licensing and cohort provenance are recorded.
- [ ] Baselines, metrics, uncertainty treatment, and failure analysis are
      frozen.
- [ ] Raw evidence and negative-result retention are defined.
- [ ] The maintainer approval record is linked.
- [ ] No result, outcome, or unsupported claim has been inserted.

## 8. Amendments

| Amendment ID | Date (UTC) | Reason | Changed section | Approval record | Effect on claim interpretation |
|---|---|---|---|---|---|
| `[none at initial acceptance]` |  |  |  |  |  |
