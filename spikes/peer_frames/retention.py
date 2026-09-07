"""Deterministic scheduling and durability barriers for retained documents."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol


class RetentionStatus(str, Enum):
    DURABLE = "durable"
    PENDING = "pending"
    WRITING = "writing"
    FAILED = "failed"


class RetentionWriter(Protocol):
    def __call__(self, snapshot: object, complete: Callable[[int, Exception | None], None]) -> None: ...


@dataclass(frozen=True)
class RetentionState:
    status: RetentionStatus
    revision: int | None
    durable_revision: int | None
    error: Exception | None = None


@dataclass(frozen=True)
class _Pending:
    revision: int
    snapshot: object
    due_at: float


class RetentionCoordinator:
    """Coalesce edits and publish immutable snapshots in revision order.

    ``capture`` and ``writer`` are deliberately injected. Capture is called by
    ``edit`` on the owning thread; the writer receives an immutable snapshot
    and must call ``complete`` when its durable write has finished.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], float],
        capture: Callable[[], object],
        writer: RetentionWriter,
        schedule: Callable[[float, Callable[[], None]], None],
        due_after: float = 1.0,
    ) -> None:
        if due_after < 0:
            raise ValueError("due_after must be non-negative")
        self._clock = clock
        self._capture = capture
        self._writer = writer
        self._schedule = schedule
        self._due_after = due_after
        self._next_revision = 0
        self._durable_revision: int | None = None
        self._durable_snapshot: object | None = None
        self._pending: _Pending | None = None
        self._in_flight: tuple[int, object] | None = None
        self._error: Exception | None = None
        self._scheduled = False

    @property
    def state(self) -> RetentionState:
        if self._in_flight is not None:
            status = RetentionStatus.WRITING
            revision = self._in_flight[0]
        elif self._error is not None:
            status = RetentionStatus.FAILED
            revision = self._pending.revision if self._pending else self._durable_revision
        elif self._pending is not None:
            status = RetentionStatus.PENDING
            revision = self._pending.revision
        else:
            status = RetentionStatus.DURABLE
            revision = self._durable_revision
        return RetentionState(status, revision, self._durable_revision, self._error)

    def edit(self, revision: int | None = None) -> int:
        """Capture the newest owner-thread state and retain its generation."""
        if revision is None:
            self._next_revision += 1
            revision = self._next_revision
        elif revision <= self._next_revision:
            raise ValueError("edit revisions must increase")
        else:
            self._next_revision = revision
        snapshot = self._capture()
        if self._in_flight is None and self._pending is None and snapshot == self._durable_snapshot:
            return revision
        now = self._clock()
        due_at = self._pending.due_at if self._pending is not None else now + self._due_after
        self._pending = _Pending(revision, snapshot, due_at)
        self._error = None
        self._ensure_scheduled(due_at)
        return revision

    def retry(self) -> bool:
        if self._pending is None or self._in_flight is not None:
            return False
        self._error = None
        self._begin_write()
        return True

    def flush(self) -> bool:
        """Start or observe the barrier for all edits known at call time."""
        if self._in_flight is not None:
            return False
        if self._pending is None:
            return self._error is None
        self._begin_write()
        return self._in_flight is None and self._error is None

    def run_due(self) -> bool:
        """Run a due callback; useful for fake clocks and scheduler adapters."""
        if self._pending is None or self._in_flight is not None:
            return False
        if self._clock() < self._pending.due_at:
            return False
        self._scheduled = False
        self._begin_write()
        return True

    def complete(self, revision: int, error: Exception | None = None) -> bool:
        """Publish one writer completion, rejecting stale completions."""
        if self._in_flight is None or self._in_flight[0] != revision:
            return False
        _revision, snapshot = self._in_flight
        self._in_flight = None
        if error is not None:
            if self._pending is None or self._pending.revision < revision:
                self._pending = _Pending(revision, snapshot, self._clock())
            self._error = error
            self._scheduled = False
            return True
        self._durable_revision = revision
        self._durable_snapshot = snapshot
        self._error = None
        if self._pending is not None and self._pending.revision <= revision:
            self._pending = None
        if self._pending is not None:
            self._ensure_scheduled(self._pending.due_at)
        return True

    def _begin_write(self) -> None:
        if self._pending is None or self._in_flight is not None:
            return
        pending = self._pending
        self._pending = None
        self._in_flight = (pending.revision, pending.snapshot)
        try:
            self._writer(pending.snapshot, self.complete)
        except Exception as error:
            self.complete(pending.revision, error)

    def _ensure_scheduled(self, due_at: float) -> None:
        if self._scheduled or self._in_flight is not None:
            return
        self._scheduled = True
        self._schedule(max(0.0, due_at - self._clock()), self.run_due)
