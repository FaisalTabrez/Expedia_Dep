from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "atlas-builder" / "src"))
from expedia_atlas_builder.embedding import EmbeddingError, VECTOR_DIMENSION, configure_reproducible_cpu, pool_and_normalize, profile_windows, read_canonical_contigs  # noqa: E402


class EmbeddingProfileProcessingTests(unittest.TestCase):
    def test_reproducible_cpu_policy_disables_fast_or_implicit_execution_paths(self) -> None:
        class FakeTorch:
            class cuda:
                @staticmethod
                def is_available() -> bool: return False
            class backends:
                class mkldnn: enabled = True
            def __init__(self) -> None: self.calls: list[tuple[str, object]] = []
            def manual_seed(self, value: int) -> None: self.calls.append(("seed", value))
            def set_num_threads(self, value: int) -> None: self.calls.append(("threads", value))
            def set_num_interop_threads(self, value: int) -> None: self.calls.append(("interop", value))
            def use_deterministic_algorithms(self, value: bool) -> None: self.calls.append(("deterministic", value))
        torch = FakeTorch()
        configure_reproducible_cpu(torch)
        self.assertEqual([("seed", 0), ("threads", 1), ("interop", 1), ("deterministic", True)], torch.calls)
        self.assertFalse(torch.backends.mkldnn.enabled)

    def test_windows_preserve_contig_boundaries_and_position_limit(self) -> None:
        contigs = (("A.1", "A" * 8192), ("B.1", "C"))
        windows = profile_windows(contigs)
        self.assertEqual(3, len(windows))
        self.assertEqual(8191, len(windows[0]) - len("<s>"))
        self.assertEqual("<s>A", windows[1])
        self.assertEqual("<s>C", windows[2])

    def test_pooling_is_mean_then_l2_normalization(self) -> None:
        first = (1.0,) + (0.0,) * (VECTOR_DIMENSION - 1)
        second = (0.0, 1.0) + (0.0,) * (VECTOR_DIMENSION - 2)
        vector = pool_and_normalize((first, second))
        self.assertAlmostEqual(2 ** -0.5, vector[0])
        self.assertAlmostEqual(2 ** -0.5, vector[1])
        self.assertAlmostEqual(1.0, sum(value * value for value in vector))

    def test_invalid_canonical_rows_and_vectors_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.txt"
            path.write_text("missing-tab\n", encoding="ascii")
            with self.assertRaisesRegex(EmbeddingError, "tab"):
                read_canonical_contigs(path)
        with self.assertRaisesRegex(EmbeddingError, "dimension"):
            pool_and_normalize(((1.0,),))


if __name__ == "__main__": unittest.main()
