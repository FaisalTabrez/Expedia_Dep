"""SDK boundary contracts."""

from collections.abc import Mapping
from typing import Protocol


class ExpediaClient(Protocol):
    """Delegates all query semantics to an injected Query Core instance."""

    def query(self, request: Mapping[str, object]) -> Mapping[str, object]: ...
