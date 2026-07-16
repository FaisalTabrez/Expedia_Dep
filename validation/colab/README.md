# M1 GENERanno T4 validation harness

This harness validates the frozen M1 embedding algorithm on a Google Colab T4.
It is **not** an Atlas Builder stage and its vectors are **validation evidence
only**. Do not place its outputs in an M1 release, register them as
`EmbeddingInstance` records, or compare them across accelerator classes as if
they were the CPU reference profile.

## Colab procedure

1. In Colab, choose **Runtime → Change runtime type → T4 GPU**.
2. Clone this repository and run `pip install torch==2.4.1
   transformers==4.44.0 huggingface_hub==0.36.2`.
3. Make the acquired canonical record available in the notebook workspace; do
   not re-canonicalize source FASTA in Colab.
4. Run `m1_t4_validation.py` with the canonical record, output directory, and
   frozen model revision. It downloads the exact snapshot, verifies the
   `model.safetensors` SHA-256, enables deterministic CUDA settings, and emits
   a vector plus runtime metadata.
5. Restart the Colab runtime and repeat the same command. Compare the two
   `vector.float32le` files byte-for-byte. Stop if they differ.
6. Retain the two metadata files, vector digests, and comparison result as
   validation evidence. Do not start a 12-record accelerator run unless this
   gate passes and its outputs remain outside the canonical M1 release.

The harness preserves the M1 model revision, tokenizer, BOS/window policy,
pooling, and L2 normalization. CUDA runtime details are recorded separately so
they cannot be mistaken for CPU-profile provenance.
