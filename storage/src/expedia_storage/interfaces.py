"""EDS section 14 adapter boundaries."""

from collections.abc import Mapping, Sequence
from typing import Protocol


class ArtifactStore(Protocol):
    """Addresses immutable artifacts by declared digest and media type."""

    def describe(self, digest: str) -> Mapping[str, object]: ...


class VectorShardReader(Protocol):
    """Reads a profile-scoped immutable vector shard by declared row mapping."""

    def read(self, shard: Mapping[str, object]) -> Sequence[Sequence[float]]: ...
