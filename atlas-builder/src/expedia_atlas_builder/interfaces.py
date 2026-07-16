"""EDS section 9 interface placeholders.

These protocols intentionally declare boundaries only. Implementations must
persist the stage-envelope contract rather than infer stage success from files.
"""

from collections.abc import Mapping, Sequence
from typing import Protocol


Artifact = Mapping[str, object]
StageEnvelope = Mapping[str, object]


class Stage(Protocol):
    """A typed Builder stage with declared inputs, outputs, and outcome."""

    @property
    def stage_id(self) -> str: ...

    def run(self, inputs: Sequence[Artifact], configuration: Mapping[str, object]) -> StageEnvelope: ...


class PluginResolver(Protocol):
    """Resolves only compatible, digest-pinned PluginDescriptors."""

    def resolve(self, descriptor: Mapping[str, object]) -> object: ...


class AtlasBuilder(Protocol):
    """Builds one declared BuildRun from a manifest."""

    def build(self, manifest: Mapping[str, object]) -> Mapping[str, object]: ...
