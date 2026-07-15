"""Technology-neutral peer-frame workspace contract."""

from .contract import (
    BackendEvent,
    BackendEventKind,
    Capability,
    CloseDecision,
    CloseReason,
    CloseVote,
    Direction,
    OperationResult,
    OperationStatus,
    Orientation,
    PaneDescriptor,
    PaneKind,
    TabSide,
    WorkspaceModel,
)
from .fake_backend import FakeBackend

__all__ = [
    "BackendEvent",
    "BackendEventKind",
    "Capability",
    "CloseDecision",
    "CloseReason",
    "CloseVote",
    "Direction",
    "FakeBackend",
    "OperationResult",
    "OperationStatus",
    "Orientation",
    "PaneDescriptor",
    "PaneKind",
    "TabSide",
    "WorkspaceModel",
]
