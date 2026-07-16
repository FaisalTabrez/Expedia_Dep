"""SDK boundary contracts."""

from collections.abc import Mapping
from typing import Protocol


class ExpediaClient(Protocol):
    """Delegates all query semantics to Query Core or the versioned REST adapter."""

    def query(self, request: Mapping[str, object]) -> Mapping[str, object]: ...
