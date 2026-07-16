"""Profile-bound pre/post-processing for the M1 GENERanno embedding stage."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import time
from typing import Any

from .acquisition import sha256_file


WINDOW_BASES = 8191
VECTOR_DIMENSION = 1280
BOS_PREFIX = "<s>"


class EmbeddingError(ValueError):
    """Raised when M1 profile inputs or vectors violate the declared contract."""


def configure_reproducible_cpu(torch_module: object) -> None:
    """Apply the frozen M1 CPU policy before loading or evaluating the model.

    This intentionally trades throughput for a narrowly controlled numerical
    environment. The caller supplies the module to keep this contract layer
    testable without importing the optional runtime dependency.
    """

    if bool(torch_module.cuda.is_available()):
        raise EmbeddingError("M1 profile forbids GPU execution")
    torch_module.manual_seed(0)
    torch_module.set_num_threads(1)
    torch_module.set_num_interop_threads(1)
    torch_module.use_deterministic_algorithms(True)
    torch_module.backends.mkldnn.enabled = False


def read_canonical_contigs(path: Path) -> tuple[tuple[str, str], ...]:
    """Read only the canonical `accession<TAB>sequence<LF>` representation."""

    records: list[tuple[str, str]] = []
    for line in path.read_text(encoding="ascii").splitlines():
        try:
            accession, sequence = line.split("\t", 1)
        except ValueError as error:
            raise EmbeddingError("canonical record must contain one tab separator") from error
        if not accession or not sequence:
            raise EmbeddingError("canonical record contains an empty accession or sequence")
        records.append((accession, sequence))
    if not records:
        raise EmbeddingError("canonical record contains no contigs")
    return tuple(records)


def profile_windows(contigs: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    """Partition contigs without crossing boundaries and add the declared BOS token."""

    windows: list[str] = []
    for _, sequence in contigs:
        windows.extend(BOS_PREFIX + sequence[start : start + WINDOW_BASES] for start in range(0, len(sequence), WINDOW_BASES))
    return tuple(windows)


def pool_and_normalize(window_vectors: tuple[tuple[float, ...], ...]) -> tuple[float, ...]:
    """Arithmetic-mean window vectors, then L2 normalize the assembly vector."""

    if not window_vectors:
        raise EmbeddingError("model returned no window vectors")
    if any(len(vector) != VECTOR_DIMENSION for vector in window_vectors):
        raise EmbeddingError("window vector dimension does not match the profile")
    mean = tuple(sum(vector[index] for vector in window_vectors) / len(window_vectors) for index in range(VECTOR_DIMENSION))
    norm = math.sqrt(sum(value * value for value in mean))
    if not math.isfinite(norm) or norm == 0.0:
        raise EmbeddingError("assembly vector has zero or non-finite norm")
    normalized = tuple(value / norm for value in mean)
    if not all(math.isfinite(value) for value in normalized):
        raise EmbeddingError("assembly vector contains non-finite values")
    return normalized


def embed_assembly_from_local_snapshot(
    canonical_path: Path, snapshot_path: Path, expected_weight_digest: str, timings: dict[str, float] | None = None
) -> tuple[float, ...]:
    """Embed one canonical assembly using only the exact local GENERanno snapshot.

    Windows are deliberately evaluated one at a time. This is slower than
    batching but prevents an undeclared throughput optimization from changing
    the M1 reference execution path.
    """

    timings = timings if timings is not None else {}
    started = time.perf_counter()
    weight_path = snapshot_path / "model.safetensors"
    if sha256_file(weight_path) != expected_weight_digest:
        raise EmbeddingError("pinned model weight digest mismatch")
    timings["weight_verification_seconds"] = time.perf_counter() - started
    try:
        import torch
        from transformers import AutoModelForMaskedLM, AutoTokenizer
    except ImportError as error:
        raise EmbeddingError("pinned M1 runner is not available") from error
    started = time.perf_counter()
    configure_reproducible_cpu(torch)
    tokenizer = AutoTokenizer.from_pretrained(snapshot_path, trust_remote_code=True, local_files_only=True)
    model = AutoModelForMaskedLM.from_pretrained(
        snapshot_path, trust_remote_code=True, local_files_only=True, torch_dtype=torch.float32
    ).to("cpu").eval()
    timings["model_load_seconds"] = time.perf_counter() - started
    started = time.perf_counter()
    windows = profile_windows(read_canonical_contigs(canonical_path))
    timings["window_generation_seconds"] = time.perf_counter() - started
    timings["window_count"] = float(len(windows))
    vectors: list[tuple[float, ...]] = []
    tokenization_seconds = 0.0
    forward_seconds = 0.0
    for window in windows:
        started = time.perf_counter()
        encoded: Any = tokenizer(window, add_special_tokens=False, return_tensors="pt")
        tokenization_seconds += time.perf_counter() - started
        started = time.perf_counter()
        with torch.inference_mode():
            outputs = model(**encoded, output_hidden_states=True)
        forward_seconds += time.perf_counter() - started
        hidden = outputs.hidden_states[-1][0, 0, :].to(dtype=torch.float32, device="cpu")
        vector = tuple(float(value) for value in hidden.tolist())
        if len(vector) != VECTOR_DIMENSION:
            raise EmbeddingError("model output dimension does not match the profile")
        vectors.append(vector)
    timings["tokenization_seconds"] = tokenization_seconds
    timings["forward_seconds"] = forward_seconds
    started = time.perf_counter()
    result = pool_and_normalize(tuple(vectors))
    timings["pooling_and_normalization_seconds"] = time.perf_counter() - started
    return result


def main(argv: list[str] | None = None) -> int:
    """Run one reproducibility-gated assembly embedding from explicit paths."""

    parser = argparse.ArgumentParser(description="Run one M1 GENERanno reference embedding.")
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--weight-digest", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timing-output", type=Path)
    args = parser.parse_args(argv)
    timings: dict[str, float] = {}
    vector = embed_assembly_from_local_snapshot(args.canonical, args.snapshot, args.weight_digest, timings)
    started = time.perf_counter()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(vector, separators=(",", ":")), encoding="utf-8")
    timings["serialization_seconds"] = time.perf_counter() - started
    if args.timing_output:
        args.timing_output.parent.mkdir(parents=True, exist_ok=True)
        args.timing_output.write_text(json.dumps(timings, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
