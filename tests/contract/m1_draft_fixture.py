"""Shared complete M1 Draft-package fixture for reader-boundary tests."""

from __future__ import annotations

from pathlib import Path

from test_release_reader import ReleaseReaderTests as _ReleaseReaderTests


def build_m1_draft_package(root: Path) -> Path:
    """Build the same complete, integrity-valid M1 Draft fixture as reader tests."""

    return _ReleaseReaderTests()._package(root)
