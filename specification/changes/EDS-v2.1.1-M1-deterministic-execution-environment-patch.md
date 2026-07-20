# EDS v2.1.1 proposed normative patch: M1 deterministic execution environments

**Status:** Proposed controlled amendment; not effective until accepted by the
M1 Release Owner under EDS document control.  
**Target:** `EXPEDIA_Design_Specification_EDS_v2.1.docx`  
**Scope:** M1 embedding execution policy only.  
**Non-goals:** No change to the M1 architecture, milestones, contracts,
schemas, canonicalization, embedding-profile representation semantics, model,
tokenizer, windowing, pooling, normalization, vector format, or governance
model.

## Decision

M1 release eligibility MUST be determined by embedding-profile conformance,
pinned model and tokenizer identities, an Approved Deterministic Execution
Environment (ADEE), complete provenance, and successful contract validation.
Processor type alone MUST NOT determine release eligibility or embedding-profile
identity.

An ADEE is a versioned, digest-pinned execution declaration selected by one
BuildManifest. It MAY use CPU or validated accelerator hardware. It MUST record
the processor/accelerator identity, operating-system and Python versions,
numeric-library versions, precision policy, deterministic controls, batching
policy, model and tokenizer pins, and validation evidence. A BuildRun MUST use
one ADEE for a given embedding shard and MUST NOT silently fall back or mix
environments.

The following environment is approved for M1 release generation once this
amendment is accepted:

```text
execution_environment_id: m1-generanno-t4-cuda12.1-fp32-deterministic-v1
accelerator: Tesla T4
cuda: 12.1
python: 3.12.13
torch: 2.4.1+cu121
transformers: 4.44.0
precision: float32
deterministic_algorithms: true
tf32: false
cublas_workspace_config: :4096:8
```

This is an execution-environment approval, not a new EmbeddingProfile or a
GPU-specific profile. The profile remains
`m1-generanno-prokaryote-0.5b-assembly-v1`.

## Exact EDS v2.1 clauses amended

| EDS v2.1 locator | Replacement or addition | Why required |
|---|---|---|
| §5.1, paragraph beginning “The host MUST reject a plugin…” | Append: “Processor type is an execution-environment property, not an EmbeddingProfile identity. A BuildRun MAY select CPU or accelerator execution only through an ADEE declared in the BuildManifest and runner provenance. It MUST reject an undeclared, incompatible, or unverifiable ADEE and MUST NOT silently mix or fall back between environments.” | Retains the existing no-fallback rule while allowing an explicitly selected validated accelerator. |
| §8.2, required-profile-declaration table, `provenance` row | Replace the Requirement cell with: “Runner/plugin version, ADEE identifier and declaration digest, environment lock, license, creator, and created time.” | Makes the execution choice reproducible without making processor type a profile identifier. |
| §9.2, Builder manifest paragraph | Insert “selected ADEE identifier and declaration digest” after “plugin versions/configuration digests”. | Ensures the execution environment is an explicit, content-addressed build input. |
| §9.3, content-addressed execution paragraph | Replace the reuse condition with: “A stage MAY reuse an existing artifact only when its input digests, plugin identity, configuration digest, ADEE declaration digest, and schema compatibility match.” | Prevents cross-environment reuse from becoming an undocumented provenance shortcut. |
| §9.4, non-deterministic-steps bullet | Replace with: “Embedding output submitted as deterministic MUST record its ADEE, deterministic controls, seeds where applicable, and expected tolerance. An ADEE is release-eligible only when deterministic reproduction is demonstrated under its declared configuration. If reproducibility cannot be demonstrated, the output remains Experimental.” | Defines the environment-neutral acceptance gate requested for M1. |
| §9.1 reference-pipeline table, `4. Embed` quality gate | Replace with: “Profile and ADEE match; pinned model/tokenizer verification; expected dimension; numeric sanity; deterministic-reproduction evidence; shard checksum. Failure: record-level failure ledger.” | Keeps the same stage, artifacts, and gate while removing the implicit CPU constraint. |
| Appendix C, OQ-03 question | Replace with: “Which embedding profile, record unit, and ADEE define M1?” | Makes the M1 execution-policy disposition explicit without creating another open question. |
| Appendix D terminology table | Add: “Approved Deterministic Execution Environment (ADEE): a versioned, provenance-recorded CPU or accelerator execution declaration approved for a BuildRun after deterministic reproduction and contract validation. It is not an EmbeddingProfile.” | Establishes the requested term and prevents a CPU/GPU profile split. |

## M1 acceptance interpretation after adoption

The M1.5 embedding acceptance criterion remains unchanged except for processor
type. Every eligible record MUST map to exactly one instance under the one
profile; vector dimensions, dtype, normalization, row mapping, and shard
digests MUST verify. The selected ADEE MUST additionally be recorded in runner
provenance and the StageOutcome.

Release artifacts are defined by profile conformance, pinned model and tokenizer
revisions, the declared deterministic configuration, complete provenance, and
successful contract validation. A CPU implementation and an accelerator
implementation are both permitted only when they satisfy the selected ADEE
requirements. Their processor type is provenance, not profile identity.

## Evidence motivating this amendment

1. CPU reference instrumentation established that the smallest M1 assembly
   requires approximately 39.6 CPU-hours under the pinned, sequential,
   float32 policy. The CPU implementation itself passed contract, pinning,
   weight-verification, deterministic-policy, and inference-pipeline checks.
2. The validated Tesla T4 execution completed all 12 canonical records without
   changing model revision, tokenizer, preprocessing, windowing, pooling,
   normalization, or vector format.
3. The T4 evidence verified the pinned revision and weight digest, deterministic
   settings, finite normalized vectors, per-record digests, complete provenance,
   and exact 12-record coverage. Its final evidence digest is
   `sha256:f7b4ba4a6f45eb69120f799a520b297d497705e5380e82ebb109afb7e3f69cff`.
4. The committed evidence record is
   `validation/colab/evidence/m1-t4-accelerator-implementation-validation-2026-07-19.md`.

## Consequences and bounded implementation follow-up

No JSON Schema, Python contract binding, canonicalization profile, vector
format, pooling rule, normalization rule, model pin, tokenizer pin, release
state machine, or governance role changes.

After acceptance, the M1 plugin descriptor and runner provenance declaration
MUST be changed only to replace their CPU-only execution-policy fields with the
approved ADEE declaration. The profile ID remains unchanged; no GPU-specific
profile is created. The existing T4 output must be regenerated through the
release embedding stage so that its vector shard, EmbeddingInstance table, and
StageOutcome are canonical release artifacts with ADEE provenance.
