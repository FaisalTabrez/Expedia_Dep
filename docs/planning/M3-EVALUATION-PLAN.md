# M3 evaluation plan: evidence before method claims

**Status:** M3.1 evaluation governance is complete. M3-001 is a Draft
preregistration; no experiment, benchmark result, or scientific claim has been
accepted.
**Governing specification:** EDS v2.1.1 sections 8, 12.4-12.7, 13, 14, and
15.4; ERS v1.0; the accepted M2 checkpoint `m2.0.0-complete`.
**Purpose:** Define the smallest controlled path from deterministic retrieval to
scientific method evidence. This plan creates no result, benchmark, biological,
performance, recall, scalability, or usefulness claim.

## 1. Boundary

M1 established a deterministic internal Draft package. M2 established one
deterministic local read and retrieval interpretation. M3 evaluates hypotheses
against that fixed target; it does not extend Query Core, change the M1
EmbeddingProfile, select a default profile or index, or prepare a public
release.

The M2 frozen boundary is the study reference:

- the authoritative M1 Draft successor remains
  `expedia-m1-draft-20260721-v3`;
- `m1-generanno-prokaryote-0.5b-assembly-v1` remains the sole profile;
- Query Core exact float32 cosine remains the reference retrieval method;
- M2 request, filtering, ordering, cursor, provenance, SDK, REST, and Explorer
  semantics remain unchanged; and
- any study result is external evidence, not a mutation of an Atlas Release.

## 2. Entry gate and blockers

M3 work begins only after the following planning gate is accepted. Drafting
this plan does not satisfy the gate.

| Gate | Required disposition | Status |
|---|---|---|
| M2 closure | M2 completion decision and immutable repository checkpoint | Satisfied: `m2.0.0-complete`. |
| OQ-05 | Accepted claim-evidence requirements and permitted claim boundaries | Satisfied by the accepted OQ-05 disposition; every study must apply it. |
| Study preregistration | Freeze question, cohort, inclusion/exclusion, ground truth, baselines, metrics, uncertainty treatment, failure analysis, raw-artifact plan, and claim limits before execution | **Blocking; not yet authored.** |
| OQ-04 | Resolve only if an ANN method is proposed for evaluation | Deferred; no ANN study is planned by this baseline. |
| OQ-08 | Resolve only if a cross-profile comparison or BridgeProfile is proposed | Deferred; no cross-profile study is planned by this baseline. |

OQ-09 and OQ-10 remain M4/M5 publication and distribution concerns. They do
not block a non-public M3 preregistration, but neither may be treated as
resolved by evaluation work.

## 3. Phased M3 work

| ID | Phase | Dependencies | Deliverables | Acceptance criteria | Complexity |
|---|---|---|---|---|---|
| M3.1 | Evaluation governance | M2 closure; accepted OQ-05 | Claim-boundary register and preregistration template | **Complete:** reusable templates require claim categories, prohibited wording, task-specific decision rules, cohort/source provenance, baselines, metrics, uncertainty, failure analysis, raw evidence, and maintainer approval before execution. | M |
| M3.2 | Preregister reference study | M3.1 | Versioned preregistration; cohort/source/license record; frozen baseline definition; evaluation manifest | **In progress:** M3-001 Draft binds the internal M1 v3 fixture, exact cosine baseline, request families, repeat design, and prohibited claims. Maintainer acceptance and evaluation-manifest binding remain required before execution. | L |
| M3.3 | Execute reference experiments | M3.2 | Immutable run manifests, raw outputs, environment/provenance records, integrity digests | Every run is reproducible from its manifest and bounded by the preregistration. Deviations are recorded as deviations, not silently folded into results. | XL |
| M3.4 | Analyze evidence | M3.3 | Analysis notebook/script, uncertainty and failure analysis, evidence-status assessment | Analysis uses only preregistered methods or labels an approved amendment. It distinguishes method evidence from exploratory observations. | L |
| M3.5 | Review and decision | M3.4 | Evidence report, raw-artifact index, supported/unsupported claim register, controlled decision record | Each conclusion is limited to the preregistered evidence. Unsupported hypotheses remain unsupported. Any proposal to select a default method or extend M2 requires a separate controlled decision. | M |

## 4. Reference-study policy

The default M3 baseline is not a claim that exact cosine or GENERanno is useful.
It is an auditable comparison point:

1. The study invokes the accepted M2 Query Core exact cosine path without
   changing its profile, metric, filtering, ordering, or provenance.
2. Ground truth, where retrieval quality is evaluated, is computed or curated
   under the preregistered protocol and retained with versioned provenance.
3. A method is compared only against baselines named before execution. The
   exact-reference result is retained even if a future evaluated method differs.
4. Failure cases, exclusions, uncertainty, and missing/ambiguous ground truth
   are first-class outputs; they are not discarded to improve a summary metric.
5. Resource observations may be recorded only when the preregistration defines
   their collection and interpretation. They do not become throughput or
   scalability claims by default.

No ANN configuration, FAISS index, quantization, alternate model, cross-profile
comparison, UMAP/clustering result, GAT transformation, annotation provider, or
derived relation is included in this baseline. Each would require the specific
deferred decision and a revised preregistration before study execution.

## 5. Evidence and acceptance model

Each M3 study SHALL retain:

- a versioned preregistration and its acceptance record;
- source/cohort, license, inclusion/exclusion, and split provenance;
- M1 release, profile, vector-shard, and M2 implementation identifiers;
- exact query inputs and canonical request digests where query behavior is
  evaluated;
- raw result artifacts, checksums, runtime environment, and analysis inputs;
- uncertainty treatment, failure cases, deviations, and negative results; and
- an explicit mapping from each proposed claim to its supporting evidence or an
  explicit unsupported status.

A study passes M3 only when it meets its own preregistered acceptance criteria.
The EDS deliberately supplies no universal numerical threshold; none is added
by this plan.

## 6. Critical path

`accepted OQ-05 disposition -> accepted preregistration -> exact-reference
execution -> raw evidence and analysis ->
claim review -> controlled decision`

This order minimizes rework: experimental data cannot be interpreted or used to
promote a method before the question, baseline, and claim boundary are fixed.

## 7. Risks and controls

| Risk | Control |
|---|---|
| A deterministic retrieval implementation is mistaken for scientific validation | Keep M1/M2 evidence separate from M3 method evidence and prohibit claim promotion before preregistered review. |
| Metric selection follows observed results | Freeze metrics, treatment of uncertainty, and claim language before execution. |
| The small M1 fixture is represented as a representative population | Describe its twelve-record internal scope exactly; select any evaluation cohort under an explicit source/license and inclusion policy. |
| ANN or another optimization is selected by convenience | Leave OQ-04 deferred unless an ANN study is proposed; retain exact cosine as the reference path. |
| Cross-profile comparison is implied by equal vector dimensions | Keep OQ-08 deferred and reject cross-profile interpretation without an approved BridgeProfile evaluation. |
| EDS-proposed ADRs are mistaken for accepted history | Preserve their Proposed status through the ADR register reconciliation note; require a future ADR only for public/default-method promotion. |

## 8. M3 exit criteria

M3 is complete only when each executed study has an accepted preregistration,
reproducible raw evidence, documented uncertainty and failure analysis, and a
reviewed claim register. It may recommend a later architectural or method
decision only where the evidence supports that narrowly scoped decision. It
does not itself authorize M4 publication.
