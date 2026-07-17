# M1 GENERanno T4 validation harness

This harness validates the frozen M1 embedding algorithm on a Google Colab T4.
It is **not** an Atlas Builder stage and its vectors are **validation evidence
only**. Do not place its outputs in an M1 release, register them as
`EmbeddingInstance` records, or compare them across accelerator classes as if
they were the CPU reference profile.

## Colab procedure

1. In Colab, choose **Runtime → Change runtime type → T4 GPU**.
2. Clone this repository and install the pinned runtime packages with a clean
   reinstall. Colab can otherwise retain incompatible files from a previously
   installed Transformers version:

   ```bash
   pip uninstall -y transformers tokenizers huggingface_hub
   pip install --no-cache-dir --force-reinstall --no-deps \
     torch==2.4.1 transformers==4.44.0 tokenizers==0.19.1 huggingface_hub==0.36.2
   ```

   Restart the Colab runtime immediately after this installation, then clone
   or pull the repository again before running the harness.
   The harness sets `CUBLAS_WORKSPACE_CONFIG=:4096:8` before importing PyTorch;
   do not override or remove it.
3. Make the acquired canonical record available in the notebook workspace; do
   not re-canonicalize source FASTA in Colab.
4. Run `m1_t4_validation.py` with the canonical record, output directory, and
   frozen model revision. It downloads the exact snapshot, verifies the
   `model.safetensors` SHA-256, enables deterministic CUDA settings, and emits
   a vector plus runtime metadata.
5. Restart the Colab runtime and repeat the same command. Compare the two
   `vector.float32le` files byte-for-byte. Stop if they differ.
6. Retain the two metadata files, vector digests, and comparison result as
   validation evidence. The 12-record mode below is permitted only after this
   gate passes, and its outputs must remain outside the canonical M1 release.

The harness preserves the M1 model revision, tokenizer, BOS/window policy,
pooling, and L2 normalization. CUDA runtime details are recorded separately so
they cannot be mistaken for CPU-profile provenance.

## Full M1.5 implementation validation (12 records)

This mode validates the complete frozen implementation on the already-verified
T4 runtime. It does **not** change the CPU-only release profile and never emits
release vectors, vector shards, or `EmbeddingInstance` records.

Before uploading anything to Colab, prepare an input folder from the existing
M1.4 outputs. It must contain exactly these two items:

```text
m1-canonical-inputs/
  genome-record-versions.jsonl
  canonical/
    GCF_*.txt   # exactly the 12 M1 canonical files
```

The harness verifies the uploaded record table against the committed M1.4
record-table digest, verifies all 12 expected record identities, and verifies
every canonical file against its declared sequence digest. It refuses missing,
extra, duplicate, or changed inputs.

In Colab, upload and unpack that folder, then use a persistent output location
(for example, mounted Google Drive) if the run may outlast a Colab session:

```python
from google.colab import files
files.upload()  # Upload m1-canonical-inputs.zip
```

```bash
!unzip -q /content/m1-canonical-inputs.zip -d /content
!python validation/colab/m1_t4_validation.py \
  --canonical-directory /content/m1-canonical-inputs/canonical \
  --record-versions /content/m1-canonical-inputs/genome-record-versions.jsonl \
  --output-dir /content/drive/MyDrive/expedia-m1-t4-validation
```

The command loads and verifies the model once, then records each completed
assembly independently under `records/`. If a Colab session stops, reconnect
the same T4 runtime and rerun the **identical** command with the same output
directory. The harness verifies the frozen run identity and completed vector
evidence before reusing any record; it refuses a mixed configuration.

When complete, `validation-metadata.json` must report exactly 12 records, no
missing or duplicate records, finite L2-normalized vectors, complete
provenance, per-record digests, and stage-level timing. Archive this directory
as accelerator validation evidence only. It must not be copied into an M1
release workspace.
