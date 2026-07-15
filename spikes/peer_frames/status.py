"""Application-owned status state for peer-frame projections."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable


@dataclass(frozen=True)
class StatusSnapshot:
    """Status that is safe to project identically into every peer frame.

    Execution-target identity is deliberately absent.  Kernel affinity is
    contextual state and must not be inferred from focus or presented as an
    application-global status value.
    """

    message: str = ""
    cursor_text: str = ""
    visible: bool = True


StatusSubscriber = Callable[[StatusSnapshot], None]


class StatusState:
    """Observable status state with no frame, widget, or backend ownership."""

    def __init__(self, snapshot: StatusSnapshot | None = None):
        self._snapshot = snapshot or StatusSnapshot()
        self._subscribers: list[StatusSubscriber] = []

    @property
    def snapshot(self) -> StatusSnapshot:
        return self._snapshot

    def subscribe(self, subscriber: StatusSubscriber) -> Callable[[], None]:
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)
        subscriber(self._snapshot)

        def unsubscribe() -> None:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)

        return unsubscribe

    def set_message(self, message: str) -> None:
        self._replace(message=str(message))

    def set_cursor_text(self, cursor_text: str) -> None:
        self._replace(cursor_text=str(cursor_text))

    def set_visible(self, visible: bool) -> None:
        self._replace(visible=bool(visible))

    def _replace(self, **changes: object) -> None:
        snapshot = replace(self._snapshot, **changes)
        if snapshot == self._snapshot:
            return
        self._snapshot = snapshot
        for subscriber in tuple(self._subscribers):
            subscriber(snapshot)
