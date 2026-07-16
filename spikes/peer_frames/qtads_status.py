"""Qt status projection for application-owned peer-frame status."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6 import QtCore, QtWidgets
from shiboken6 import isValid

from .qtads_chrome import frame_chrome_base_margins, reserve_frame_chrome
from .status import StatusSnapshot, StatusState


STATUS_CHROME_OWNER = "application-status"


class _PeerStatusBar(QtWidgets.QFrame):
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.setObjectName("peerStatusBar")
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6, 1, 6, 1)
        layout.setSpacing(8)
        self.message_label = QtWidgets.QLabel(self)
        self.message_label.setObjectName("peerStatusMessage")
        self.cursor_label = QtWidgets.QLabel(self)
        self.cursor_label.setObjectName("peerStatusCursor")
        layout.addWidget(self.message_label, 1)
        layout.addWidget(self.cursor_label, 0)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.message_label.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.cursor_label.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)


@dataclass
class _StatusProjection:
    window: QtWidgets.QWidget
    status_bar: _PeerStatusBar


class QtAdsStatusProjector(QtCore.QObject):
    """Mirror globally safe status state into every existing and future frame."""

    def __init__(self, state: StatusState, dock_manager: QtCore.QObject):
        super().__init__()
        self.state = state
        self.dock_manager = dock_manager
        self._closed = False
        self._projecting_window_ids: set[int] = set()
        self._projections: dict[int, _StatusProjection] = {}
        self._unsubscribe = lambda: None
        self._unsubscribe = state.subscribe(self.refresh)
        dock_manager.floatingWidgetCreated.connect(self._on_floating_widget_created)
        dock_manager.destroyed.connect(self.close)
        for window in dock_manager.floatingWidgets():
            self.project(window)

    @property
    def projected_window_ids(self) -> frozenset[int]:
        return frozenset(self._projections)

    def project(self, window: QtWidgets.QWidget) -> None:
        if self._closed:
            return
        key = id(window)
        projection = self._projections.get(key)
        if projection is not None and projection.window is window:
            return
        self._projecting_window_ids.add(key)
        try:
            status_bar = _PeerStatusBar(window)
            projection = _StatusProjection(window, status_bar)
            self._projections[key] = projection
            window.installEventFilter(self)
            window.destroyed.connect(
                lambda _object=None, key=key: self._forget_window(key)
            )
            self._apply(projection, self.state.snapshot)
        finally:
            self._projecting_window_ids.discard(key)

    def status_bar_for(self, window: QtWidgets.QWidget) -> QtWidgets.QWidget:
        projection = self._projections.get(id(window))
        if projection is None or projection.window is not window:
            raise KeyError("window has no status projection")
        return projection.status_bar

    def refresh(self, snapshot: StatusSnapshot | None = None) -> None:
        if self._closed:
            return
        if not isValid(self.dock_manager):
            self.close()
            return
        snapshot = snapshot or self.state.snapshot
        self._reconcile_windows()
        for key, projection in tuple(self._projections.items()):
            if not isValid(projection.window) or not isValid(projection.status_bar):
                self._forget_window(key)
                continue
            self._apply(projection, snapshot)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if event.type() in (
            QtCore.QEvent.Type.Resize,
            QtCore.QEvent.Type.Show,
            QtCore.QEvent.Type.LayoutRequest,
        ):
            projection = self._projections.get(id(watched))
            if projection is not None and projection.window is watched:
                self._position(projection)
        return False

    def _apply(
        self, projection: _StatusProjection, snapshot: StatusSnapshot
    ) -> None:
        projection.status_bar.message_label.setText(snapshot.message)
        projection.status_bar.cursor_label.setText(snapshot.cursor_text)
        height = projection.status_bar.sizeHint().height() if snapshot.visible else 0
        reserve_frame_chrome(
            projection.window,
            STATUS_CHROME_OWNER,
            bottom=height,
        )
        projection.status_bar.setVisible(snapshot.visible)
        self._position(projection)

    def _position(self, projection: _StatusProjection) -> None:
        if not isValid(projection.window) or not isValid(projection.status_bar):
            return
        base = frame_chrome_base_margins(projection.window)
        height = (
            projection.status_bar.sizeHint().height()
            if projection.status_bar.isVisible()
            else 0
        )
        projection.status_bar.setGeometry(
            base.left(),
            projection.window.height() - base.bottom() - height,
            max(0, projection.window.width() - base.left() - base.right()),
            height,
        )
        projection.status_bar.raise_()

    def _reconcile_windows(self) -> None:
        for key, projection in tuple(self._projections.items()):
            if key in self._projecting_window_ids:
                continue
            if (
                not isValid(projection.window)
                or not projection.window.dockWidgets()
            ):
                self._forget_window(key)
        for window in self.dock_manager.floatingWidgets():
            if isValid(window) and window.dockWidgets():
                self.project(window)

    def _forget_window(self, key: int) -> None:
        self._projections.pop(key, None)

    def _on_floating_widget_created(self, *args: object) -> None:
        if self._closed:
            return
        for value in args:
            if isinstance(value, QtWidgets.QWidget):
                self.project(value)

    def close(self, *_args: object) -> None:
        if self._closed:
            return
        self._closed = True
        self._unsubscribe()
        self._unsubscribe = lambda: None
        for projection in tuple(self._projections.values()):
            if isValid(projection.window):
                projection.window.removeEventFilter(self)
            if isValid(projection.status_bar):
                projection.status_bar.hide()
                projection.status_bar.deleteLater()
        self._projections.clear()
