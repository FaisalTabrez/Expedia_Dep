"""EDS section 12 interface placeholders."""

from collections.abc import Mapping, Sequence
from typing import Protocol


class ReleaseReader(Protocol):
    """Opens only verified release packages for trusted operation."""

    def open(self, release_location: str) -> Mapping[str, object]: ...

    def read_table(self, table_name: str) -> Sequence[Mapping[str, object]]: ...


class QueryCore(Protocol):
    """Executes a versioned QueryRequest and returns a QueryResult envelope."""

    def execute(self, request: Mapping[str, object]) -> Mapping[str, object]: ...
