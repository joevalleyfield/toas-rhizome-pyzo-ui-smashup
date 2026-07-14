"""Deterministic backend used to exercise the workspace contract."""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping

from .contract import Capability


class FakeBackend:
    def __init__(self, capabilities: frozenset[Capability] | None = None):
        self.capabilities = capabilities or frozenset(Capability)
        self.snapshots: list[dict[str, object]] = []

    @property
    def current(self) -> dict[str, object] | None:
        return self.snapshots[-1] if self.snapshots else None

    def render(self, snapshot: Mapping[str, object]) -> None:
        self.snapshots.append(deepcopy(dict(snapshot)))
