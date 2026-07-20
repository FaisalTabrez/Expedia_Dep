# Atlas Builder

Atlas Builder is the manifest-driven, content-addressed release compiler defined
by EDS section 9. It produces Draft/Candidate release artifacts; it does not
define query semantics or mutate Published releases.

The reference stage order is Acquire -> Register/Canonicalize -> Quality
validate -> Embed -> Annotate -> Derive -> Validate -> Package -> Publish ->
Archive.

## M1.5 approved T4 release generation

EDS v2.1.1 approves
`m1-generanno-t4-cuda12.1-fp32-deterministic-v1` for M1 release generation.
The frozen profile remains `m1-generanno-prokaryote-0.5b-assembly-v1`; the
ADEE is selected by `manifests/m1/m1-build-manifest.t4-release.json` and is
recorded in every generated `EmbeddingInstance` and the stage envelope.

On a Google Colab Tesla T4 runtime, first make the exact M1.4 canonical input
folder available at `/content/m1-canonical-inputs`. It must contain the
committed `genome-record-versions.jsonl` and all twelve canonical files. Then
install the approved runtime exactly, restart the Colab runtime, and run the
release stage into an initially empty, persistent workspace:

```bash
pip uninstall -y transformers tokenizers huggingface_hub
pip install --no-cache-dir --force-reinstall --no-deps \
  torch==2.4.1 transformers==4.44.0 tokenizers==0.19.1 huggingface_hub==0.36.2
```

After the restart, clone or pull the commit containing this runner before
using:

```bash
export PYTHONPATH=/content/Expedia_Dep/atlas-builder/src
export CUBLAS_WORKSPACE_CONFIG=:4096:8
python -m expedia_atlas_builder.t4_release \
  --record-versions /content/m1-canonical-inputs/genome-record-versions.jsonl \
  --canonical-directory /content/m1-canonical-inputs/canonical \
  --workspace /content/drive/MyDrive/expedia-m1-t4-release-build-v1 \
  --build-manifest atlas-builder/manifests/m1/m1-build-manifest.t4-release.json \
  --execution-environment profiles/environments/m1-generanno-t4-cuda12.1-fp32-deterministic-v1.json
```

The runner rejects a changed record table, changed canonical input, changed
ADEE declaration, model-weight mismatch, non-T4 device, unpinned runtime, or
non-deterministic runtime setting. A completed run emits only these canonical
M1.5 artifacts: `vectors.float32le`, `vector-shard-manifest.json`,
`embedding-instances.jsonl`, and `embedding-stage-envelope.json`. The model
snapshot and any partial resume state are execution workspace state, not
release artifacts. The successful M1.5 output still requires M1.6 Draft
packaging before it is an Atlas Release.
