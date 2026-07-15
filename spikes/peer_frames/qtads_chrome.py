"""Shared edge reservation for application chrome on QtADS peer frames."""

from __future__ import annotations

from dataclasses import dataclass, field

from PySide6 import QtCore, QtWidgets
from shiboken6 import isValid


@dataclass
class _ChromeState:
    base_margins: QtCore.QMargins
    reservations: dict[str, tuple[int, int, int, int]] = field(
        default_factory=dict
    )


_STATE_ATTRIBUTE = "_application_peer_chrome_state"


def reserve_frame_chrome(
    window: QtWidgets.QWidget,
    owner: str,
    *,
    left: int = 0,
    top: int = 0,
    right: int = 0,
    bottom: int = 0,
) -> QtCore.QMargins:
    """Reserve frame edges without one projector erasing another's space."""

    state = _state(window)
    state.reservations[owner] = (
        max(0, int(left)),
        max(0, int(top)),
        max(0, int(right)),
        max(0, int(bottom)),
    )
    totals = [
        sum(values[index] for values in state.reservations.values())
        for index in range(4)
    ]
    base = state.base_margins
    window.setContentsMargins(
        base.left() + totals[0],
        base.top() + totals[1],
        base.right() + totals[2],
        base.bottom() + totals[3],
    )
    return QtCore.QMargins(base)


def frame_chrome_base_margins(window: QtWidgets.QWidget) -> QtCore.QMargins:
    return QtCore.QMargins(_state(window).base_margins)


def _state(window: QtWidgets.QWidget) -> _ChromeState:
    state = getattr(window, _STATE_ATTRIBUTE, None)
    if state is None:
        if not isValid(window):
            raise RuntimeError("cannot reserve chrome on a deleted frame")
        state = _ChromeState(QtCore.QMargins(window.contentsMargins()))
        setattr(window, _STATE_ATTRIBUTE, state)
    return state
