# OQ-05: M3 claim-evidence requirements

**Status:** Accepted M3 disposition — Faisal Tabrez, Project Maintainer,
2026-07-21.
**Question:** Which benchmarks support allowed scientific-usefulness claims?

## Decision

EXPEDIA SHALL NOT make scientific, biological, performance, scalability,
comparative, generalization, or method-quality claims unless supported by a
preregistered study with declared datasets, inclusion/exclusion criteria,
baselines, metrics, versioned raw evidence, uncertainty and failure analysis,
explicit claim language, and maintainer approval.

M3 defines evidence requirements and claim boundaries; it does not establish
claim outcomes, select a default method, or promote a profile, index, or model.
No numerical threshold is implied by this disposition. Each preregistration
MUST set task-specific acceptance criteria and rationale before execution.

The minimum evidence category for a proposed claim is:

| Proposed claim category | Minimum required evidence |
|---|---|
| Deterministic retrieval | Contract tests and reproducibility evidence. |
| Exact query correctness | Exact-reference fixtures. |
| Embedding reproducibility | Independent reruns with pinned provenance. |
| Preservation of biological meaning | Dedicated preregistered biological benchmark. |
| Superiority over a baseline | Controlled comparative study. |
| ANN quality preservation | Recall/resource evaluation against the exact reference path. |
| Generalization to unseen genomes | Independent hold-out evaluation. |

The first three rows are engineering-conformance categories. They support only
the stated engineering claim and SHALL NOT be represented as biological or
method-usefulness evidence. All other rows require the full preregistered-study
record above.

## Rationale

EDS section 13 separates software verification, release integrity,
retrieval/method evaluation, and scientific interpretation. Deterministic M1
artifacts and deterministic M2 retrieval establish only the first two kinds of
evidence. This disposition makes the evidence burden explicit before M3
generates results, preventing retrospective metric selection or promotion by
demonstration.

## Consequences

- M3 can evaluate the frozen M2 exact-cosine reference path without claiming
  that GENERanno, cosine, or the M1 profile is biologically useful.
- A future ANN, model, profile, or cross-profile proposal needs the applicable
  evidence category and its own preregistration before evaluation; this
  disposition does not authorize any of them.
- Negative results, uncertainty, exclusions, and failure cases are retained as
  evidence, not omitted to improve a summary result.
- Maintainer approval reviews whether evidence supports the declared claim; it
  does not substitute for the required evidence.

## Acceptance criteria

1. Every M3 preregistration identifies each proposed claim and maps it to one
   row of the evidence table or explicitly declares that no claim is sought.
2. Before execution, the preregistration records datasets, inclusion/exclusion,
   baselines, metrics, uncertainty treatment, failure analysis, raw-artifact
   retention, and allowed claim language.
3. Results without the required evidence are labelled unsupported and are not
   promoted into documentation, release material, or default-method decisions.
4. The M2 exact-reference path remains the retained comparator for any future
   ANN recall/resource evaluation.
5. Any future default-method or public method claim receives the separately
   required governance review; this OQ disposition does not silently accept an
   EDS-proposed ADR.

## EDS clauses affected

- EDS 8.3 compatibility and cross-model comparisons
- EDS 12.4-12.7 ranking, exactness, and query extension behavior
- EDS 13 validation and benchmark protocol
- EDS 14 storage and derived ANN artifacts
- EDS 15.1 release/benchmark CI gates
- EDS Appendix C OQ-05
- ERS REQ-013 and REQ-014

## Non-goals

This disposition does not make a biological, performance, scalability,
retrieval-quality, comparative, or generalization claim. It does not set a
benchmark outcome, add a dataset, select an ANN configuration, introduce a
BridgeProfile, alter M1/M2 contracts, or authorize M4 publication.
