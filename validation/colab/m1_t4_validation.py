"""Non-release T4 validation harness for the frozen M1 embedding algorithm."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "atlas-builder" / "src"))

from expedia_atlas_builder.embedding import (  # noqa: E402
    BOS_PREFIX,
    VECTOR_DIMENSION,
    pool_and_normalize,
    profile_windows,
    read_canonical_contigs,
)

MODEL_ID = "GenerTeam/GENERanno-prokaryote-0.5b-base"
REVISION = "d02db0f24f2c62fa1efde760217cdf75771b0228"
WEIGHT_DIGEST = "sha256:ed1cfcc64fe890a6a72017d24c02ad6af3b15c9cfa6950e850908cca92882d51"
PROFILE_ID = "m1-generanno-prokaryote-0.5b-assembly-v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def configure_t4_determinism(torch: object) -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("a CUDA T4 runtime is required for this validation harness")
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def run(canonical_path: Path, output_dir: Path) -> None:
    import torch
    import transformers
    from huggingface_hub import snapshot_download
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    configure_t4_determinism(torch)
    snapshot = Path(snapshot_download(MODEL_ID, revision=REVISION, local_dir=output_dir / "snapshot"))
    if sha256(snapshot / "model.safetensors") != WEIGHT_DIGEST:
        raise RuntimeError("pinned model weight digest mismatch")
    tokenizer = AutoTokenizer.from_pretrained(snapshot, trust_remote_code=True, local_files_only=True)
    model = AutoModelForMaskedLM.from_pretrained(snapshot, trust_remote_code=True, torch_dtype=torch.float32, local_files_only=True).to("cuda").eval()
    windows = profile_windows(read_canonical_contigs(canonical_path))
    vectors = []
    started = time.perf_counter()
    for window in windows:
        encoded = tokenizer(window, add_special_tokens=False, return_tensors="pt").to("cuda")
        with torch.inference_mode():
            hidden = model(**encoded, output_hidden_states=True).hidden_states[-1][0, 0, :]
        vectors.append(tuple(float(value) for value in hidden.to("cpu", dtype=torch.float32).tolist()))
    vector = pool_and_normalize(tuple(vectors))
    if len(vector) != VECTOR_DIMENSION:
        raise RuntimeError("unexpected embedding dimension")
    output_dir.mkdir(parents=True, exist_ok=True)
    vector_path = output_dir / "vector.float32le"
    torch.tensor(vector, dtype=torch.float32).numpy().tofile(vector_path)
    metadata = {
        "validation_only": True,
        "profile_id": PROFILE_ID,
        "model": {"id": MODEL_ID, "revision": REVISION, "weight_digest": WEIGHT_DIGEST},
        "algorithm": {"bos_prefix": BOS_PREFIX, "window_bases": 8191, "window_count": len(windows), "pooling": "arithmetic-mean-of-window-vectors", "normalization": "l2", "dtype": "float32"},
        "runtime": {"python": platform.python_version(), "torch": torch.__version__, "transformers": transformers.__version__, "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0), "deterministic_algorithms": True, "tf32": False},
        "timing": {"forward_pipeline_seconds": time.perf_counter() - started},
        "vector_digest": sha256(vector_path),
    }
    (output_dir / "validation-metadata.json").write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.canonical, args.output_dir)
