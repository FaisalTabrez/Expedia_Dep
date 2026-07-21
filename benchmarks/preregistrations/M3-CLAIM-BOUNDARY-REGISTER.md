# M3 claim-boundary register

**Status:** Active governance template. This register contains evidence
requirements, not results, supported claims, or method recommendations.
**Authority:** EDS v2.1.1 section 13 and accepted OQ-05.

## Use

Every M3 study preregistration SHALL identify each proposed claim category in
this register, its allowed wording, the required evidence, and its study-local
decision rule. A claim is unsupported until its accepted preregistration,
versioned raw evidence, analysis, and maintainer review all exist.

| Claim category | Permitted pre-result wording | Required evidence | Prohibited interpretation before evidence |
|---|---|---|---|
| Deterministic retrieval | “Deterministic retrieval is being verified.” | Contract tests and reproducibility evidence. | Biological utility, retrieval quality, or performance. |
| Exact query correctness | “Exact-reference query behavior is being verified.” | Exact-reference fixtures. | General retrieval usefulness or population-level accuracy. |
| Embedding reproducibility | “Embedding reproducibility is being verified.” | Independent reruns with pinned provenance. | Biological meaning or model superiority. |
| Preservation of biological meaning | “A preregistered biological evaluation is planned.” | Dedicated preregistered biological benchmark. | That the profile preserves biological meaning. |
| Superiority over a baseline | “A controlled comparison is planned.” | Controlled comparative study. | That any model or method outperforms a baseline. |
| ANN quality preservation | “ANN evaluation is not in the M3 reference-study scope.” | Recall/resource evaluation against the exact reference path. | That an ANN is accurate, efficient, selected, or default. |
| Generalization to unseen genomes | “Independent hold-out evaluation is required.” | Independent hold-out evaluation. | That results generalize beyond the evaluated cohort. |

## Study entry rule

Before execution, a study record MUST bind its proposed claim categories to
specific datasets, inclusion/exclusion rules, baseline methods, metrics,
uncertainty treatment, failure analysis, raw-artifact locations, and accepted
claim wording. The record MUST be accepted by the maintainer before it is
executed.

No numerical threshold, biological outcome, model selection, index selection,
or claim outcome is recorded in this register.
