"""M2 Query Core contracts, trusted release boundary, and exact reference path."""

from typing import Any

__all__ = ["ExactCosineQueryCore", "VerifiedRelease", "open_verified_release"]


def __getattr__(name: str) -> Any:
    """Avoid forcing release-reader dependencies on contract-only consumers."""

    if name == "ExactCosineQueryCore":
        from .exact_cosine import ExactCosineQueryCore

        return ExactCosineQueryCore
    if name in {"VerifiedRelease", "open_verified_release"}:
        from .verified_release import VerifiedRelease, open_verified_release

        return {"VerifiedRelease": VerifiedRelease, "open_verified_release": open_verified_release}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
