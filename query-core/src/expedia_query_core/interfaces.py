"""EDS section 12 interfaces and the ADR-010 trusted-release boundary."""

from collections.abc import Mapping
from typing import Protocol

from .verified_release import VerifiedRelease


class ReleaseReader(Protocol):
    """Opens only immutable, verified local packages for trusted operation."""

    def open(self, release_location: str) -> VerifiedRelease: ...


class QueryCore(Protocol):
    """Executes a versioned QueryRequest and returns a QueryResult envelope."""

    def execute(self, request: Mapping[str, object]) -> Mapping[str, object]: ...
