# M1 open-question resolutions

**Status:** Resolved implementation baseline  
**Scope:** M1 proof-of-concept only  
**Authority:** EDS v2.1 Appendix C and the maintainer's 2026-07-16 decision

## Purpose

This record resolves only the EDS v2.1 open questions that block M1. It does not
change the architecture, terminology, ADR register, milestones, or any other
open question. The headings retain the EDS identifiers; the earlier supplied
labels for the profile and index decisions are mapped below without changing
the EDS register.

## Resolution: OQ-01 — Minimal M1 scope

**Decision.** M1 is a local, reproducible proof-of-concept atlas, not a
comprehensive or public production release. Its source is NCBI RefSeq genome
packages retrieved through NCBI Datasets.

- **Population:** prokaryotic genomes (Bacteria and Archaea).
- **Source selection:** a committed inventory of exactly 12 versioned `GCF_`
  RefSeq assembly accessions, with at least one assembly from each domain. The
  first BuildManifest is the authoritative inventory; it must not issue a
  dynamic taxonomic query during a build.
- **Acquisition:** NCBI Datasets v2 genome package, limited to RefSeq,
  `complete` assembly level, and genome sequence plus the standard assembly
  data report and dataset catalogue. NCBI documents both the RefSeq `GCF_`
  filter and these package contents.
- **Scale:** 12 assemblies are sufficient to exercise all M1 stages while
  remaining a small reproducibility fixture.
- **Purpose:** validate architecture, contracts, artifact integrity, and
  reproducibility; it does not establish biological performance or coverage.
- **Quality policy:** apply the selected source's stated quality requirements.
  The `complete` assembly-level restriction is the sole M1 technical filter.
  Any other technical exclusion must be explicitly declared and recorded as an
  exclusion or quarantine assertion; it must not silently alter source
  accounting.
- **Licensing:** M1 is limited to internal reproducibility validation. The
  source-provenance record must retain NCBI's molecular-data usage notice and
  a notice that NCBI does not transfer any third-party rights. The M1 release
  must not present source data, metadata, or derived artifacts as
  unrestrictedly licensed for redistribution. A public-release licensing matrix
  remains deferred.

### M1 closure conditions

Before source acquisition, the committed inventory must name each accession and
source version. The BuildManifest must record the NCBI Datasets CLI version,
retrieval timestamp, command/configuration digest, package digest, inventory,
scope, source-quality rule, usage notice, and any technical exclusions.

## OQ-02 — canonicalization, deduplication, merge, and split policy

**Decision.** M1 uses canonicalization profile `m1-assembly-canonical-v1`.

1. The source unit is one NCBI RefSeq assembly accession **with version**.
2. Each assembly's genomic FASTA records are paired with their sequence-report
   accessions, sorted lexicographically by accession/version, and encoded as
   `accession<TAB>sequence<LF>` records in that order.
3. Sequence text is uppercased, ASCII whitespace is removed, FASTA deflines
   are excluded, and only the IUPAC DNA alphabet
   `ACGTRYSWKMBDHVN` is accepted. Empty sequences, missing accessions, duplicate
   sequence-report accessions, or other symbols cause a recorded quarantine.
4. The `sequence_digest` is SHA-256 over those UTF-8 canonical bytes. Contig
   boundaries are preserved; sequences are never concatenated without their
   accession boundary.
5. `entity_id` is the NCBI assembly accession without its version. `record_id`
   includes the versioned assembly accession and canonicalization profile ID.
   A new accession version creates a new GenomeRecordVersion under the same
   AtlasEntity.
6. M1 performs no automatic merge or split. Distinct accession roots remain
   distinct entities even when their canonical digest matches; such matches are
   recorded as an integrity finding, not interpreted as biological identity.

This is an M1 identity and reproducibility policy only. It makes no taxonomy,
strain, or equivalence claim.

## OQ-03 — M1 baseline profile and record unit

**Decision.** M1 supports exactly one profile,
`m1-generanno-prokaryote-0.5b-assembly-v1`, and uses one canonicalized NCBI RefSeq assembly
as the record unit. The architecture remains model-independent and may add
immutable profiles in later releases.

The profile declaration is:

- **Model artifact:** `GenerTeam/GENERanno-prokaryote-0.5b-base`, resolved to
  one immutable model revision and content digest before the first BuildRun.
  The model's accompanying MIT license text is captured in plugin/profile
  provenance.
- **Input:** the contig-preserving canonical representation defined in OQ-02.
  Each contig is partitioned into contiguous 8,191-base windows, prefixed with
  the model's BOS token `<s>`, tokenized with `add_special_tokens=False`, and
  must not exceed the model's 8,192-position limit. Windows are never padded
  across contig boundaries.
- **Pooling:** the final-layer BOS embedding per window; arithmetic mean of
  window vectors per assembly. Empty-token output is a recorded failure, not a
  substitute zero vector.
- **Output:** 1,280-component IEEE 754 float32 vector, L2-normalized after
  assembly pooling.
- **Comparison:** cosine similarity, represented as inner product of the
  normalized vectors.
- **Provenance:** the profile must record the model revision/digest, tokenizer
  digest, runner/plugin digest, numeric library/environment, deterministic
  settings, and this profile declaration digest.

### M1 execution environment

**Decision.** EDS v2.1.1 replaces the former CPU-only implementation
assumption with an Approved Deterministic Execution Environment (ADEE). M1
release generation may use the approved
`m1-generanno-t4-cuda12.1-fp32-deterministic-v1` environment, subject to its
pinned runtime declaration and deterministic-reproduction evidence. This
decision approves an execution environment only: it does not create or alter
the sole M1 embedding profile, record unit, canonicalization policy, vector
format, pooling, normalization, model pin, or tokenizer pin.

The selected ADEE identifier and declaration digest must be recorded in the
BuildManifest, runner provenance, and StageOutcome. Existing T4 validation
outputs remain validation evidence; the release embedding stage must generate
its own canonical vector shard, EmbeddingInstance table, and StageOutcome.

The GENERanno model card identifies the prokaryote base artifact as a
single-nucleotide-resolution model with an 8 kb context; its pinned
configuration declares a 1,280-dimensional hidden representation and an
8,192-position limit. This selection establishes no performance or
biological-usefulness claim.

## OQ-06 — M1 release, correction, withdrawal, and waiver authority

**Decision.** The project maintainer is the sole M1 Release Owner and Release
Approver. The same person may authorize Draft-to-Candidate,
Candidate-to-Published, correction, withdrawal, and waiver actions for M1.

Every authorization must be a durable governance record naming the actor, date,
action, release/build identifier, and, for a waiver, rationale, scope, and
review point. This authority does not permit mutation of a Published release;
correction and withdrawal follow the existing EDS state machine.

This delegation expires on entry to M4. It does not govern a public
collaborative atlas release.

## Deferred matters

The prior single-index preference is implemented in M1 as exact cosine search
over the 12 profile vectors. It is an index adapter/derived retrieval artifact,
not canonical Atlas data. ANN selection, recall/resource targets, BridgeProfiles,
benchmark claims, public licensing, public governance, and every other OQ
remain deferred to their existing later milestones.

## Source references

- [NCBI Datasets genome download reference](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/command-line/datasets/download/genome/)
- [NCBI Datasets genome-package contents](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/reference-docs/data-packages/genome/)
- [NCBI molecular-data usage policy](https://www.ncbi.nlm.nih.gov/home/about/policies/)
- [Official GENERanno repository](https://github.com/GenerTeam/GENERanno)
- [GENERanno prokaryote model artifact](https://huggingface.co/GenerTeam/GENERanno-prokaryote-0.5b-base)
