"""Explorer boundary contracts."""

from collections.abc import Mapping
from typing import Protocol


class ExplorerClient(Protocol):
    """Consumes provenance-complete Query Core results for presentation."""

    def present_release(self, release_context: Mapping[str, object]) -> Mapping[str, object]: ...

    def present_result(self, result: Mapping[str, object]) -> Mapping[str, object]: ...
