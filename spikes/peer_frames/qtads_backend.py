"""Stock-QtADS projection of the application-owned peer-frame topology."""

from __future__ import annotations

from copy import deepcopy
import sys
from typing import TYPE_CHECKING, Callable, Mapping
from weakref import ReferenceType, ref

from PySide6 import QtCore, QtGui, QtWidgets
import PySide6QtAds as QtAds
from shiboken6 import isValid

from .contract import (
    Capability,
    OperationResult,
    OperationStatus,
    TabSide,
)

if TYPE_CHECKING:
    from .contract import WorkspaceModel


PaneWidgetFactory = Callable[[str], QtWidgets.QWidget]
FrameCloseRequest = Callable[[str], OperationResult]
PaneCloseRequest = Callable[[str], OperationResult]

_HAS_FOUR_TAB_SIDES = all(
    hasattr(QtAds.CDockAreaWidget, name)
    for name in ("TabPositionLeft", "TabPositionRight", "setTabPosition")
)


class _TabSideMenuFilter(QtCore.QObject):
    """Add the application-owned group command to native QtADS menus."""

    def __init__(self, backend: QtAdsPeerFrameBackend):
        super().__init__()
        self._backend = backend

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if event.type() != QtCore.QEvent.Type.ContextMenu:
            return False
        if Capability.TAB_SIDE not in self._backend.capabilities:
            return False
        area_getter = getattr(watched, "dockAreaWidget", None)
        menu_builder = getattr(watched, "buildContextMenu", None)
        if not callable(area_getter) or not callable(menu_builder):
            return False
        area = area_getter()
        if area is None or self._backend._group_id_from_area(area) is None:
            return False

        menu = menu_builder(None)
        self._backend.append_tab_side_menu(area, menu)
        menu.exec(event.globalPos())
        menu.deleteLater()
        return True


class _ProjectionLifecycleFilter(QtCore.QObject):
    """Keep native widget lifecycle subordinate to application lifecycle."""

    def __init__(self, backend: QtAdsPeerFrameBackend):
        super().__init__()
        self._backend = backend

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        event_type = event.type()
        if event_type == QtCore.QEvent.Type.Close:
            if isinstance(watched, QtAds.CFloatingDockContainer):
                return self._backend._handle_native_frame_close(watched, event)
            if isinstance(watched, QtAds.CDockWidget):
                return self._backend._handle_native_dock_close(watched, event)
        elif event_type == QtCore.QEvent.Type.Hide:
            self._backend._projection_hidden(watched)
        elif event_type == QtCore.QEvent.Type.DeferredDelete:
            return self._backend._intercept_projection_delete(watched)
        return False


class QtAdsPeerFrameBackend:
    """Render every application frame as the same QtADS floating-container type.

    QtADS still requires one ``CDockManager``.  This adapter keeps that manager
    hidden and empty, using it only as the library registry and coordinator.
    Every application-visible frame is a ``CFloatingDockContainer``.
    """

    capabilities = (
        frozenset(Capability)
        if _HAS_FOUR_TAB_SIDES
        else frozenset(
            capability
            for capability in Capability
            if capability is not Capability.TAB_SIDE
        )
    )
    FRAME_PREFIX = "peer-frame:"
    GROUP_PREFIX = "peer-group:"
    PANE_PREFIX = "peer-pane:"

    def __init__(self, pane_factory: PaneWidgetFactory | None = None):
        self.manager = QtAds.CDockManager()
        self.manager.hide()
        self._pane_factory = pane_factory or self._default_pane_factory
        self.docks: dict[str, QtAds.CDockWidget] = {}
        self.frame_windows: dict[str, QtAds.CFloatingDockContainer] = {}
        self._snapshot: dict[str, object] | None = None
        self._next_origin = QtCore.QPoint(80, 80)
        self._next_user_frame = 1
        self._next_user_group = 1
        self._model: WorkspaceModel | None = None
        self._frame_close_request: FrameCloseRequest | None = None
        self._pane_close_request: PaneCloseRequest | None = None
        self._rendering = False
        self._closing = False
        self._frame_close_in_progress: set[str] = set()
        self._pane_close_in_progress: set[str] = set()
        self._sync_pending = False
        self._visibility_repair_pending = False
        self._repairing_visibility = False
        self._hidden_projection_candidates: set[tuple[str, str]] = set()
        self._active_pane_hint: str | None = None
        self._projected_active_pane: str | None = None
        self._settled_callbacks: list[Callable[[tuple[object, ...]], None]] = []
        self._settled_notification_pending = False
        self.adoption_count = 0
        self.last_sync_result: OperationResult | None = None
        self.last_frame_close_result: OperationResult | None = None
        self.last_pane_close_result: OperationResult | None = None
        self.fatal_backend_error: RuntimeError | None = None
        self._tab_side_menu_filter = _TabSideMenuFilter(self)
        self._projection_lifecycle_filter = _ProjectionLifecycleFilter(self)

        self.manager.floatingWidgetCreated.connect(self._floating_widget_created)
        self.manager.dockAreasAdded.connect(self._schedule_sync)
        self.manager.dockAreasRemoved.connect(self._schedule_sync)
        self.manager.dockWidgetRemoved.connect(self._schedule_sync)
        self.manager.focusedDockWidgetChanged.connect(
            self._focused_dock_widget_changed
        )
        self.manager.focusedDockWidgetChanged.connect(self._schedule_sync)

    @property
    def current(self) -> dict[str, object] | None:
        return deepcopy(self._snapshot)

    def bind_model(
        self,
        model: WorkspaceModel,
        frame_close_request: FrameCloseRequest | None = None,
        pane_close_request: PaneCloseRequest | None = None,
    ) -> None:
        self._model = model
        self._frame_close_request = frame_close_request or model.request_close_frame
        self._pane_close_request = pane_close_request or model.request_close_pane
        for pane_id, dock in self.docks.items():
            self._watch_dock(pane_id, dock)
        for window in self.manager.floatingWidgets():
            self._watch_window(window)

    def add_settled_callback(
        self, callback: Callable[[tuple[object, ...]], None]
    ) -> None:
        """Observe committed layout synchronization at its settled point."""

        self._settled_callbacks.append(callback)

    def register_dock(self, pane_id: str, dock: QtAds.CDockWidget) -> None:
        """Register an application-constructed dock before model placement."""

        if pane_id in self.docks:
            raise ValueError(f"dock already registered: {pane_id}")
        if dock.dockAreaWidget() is not None:
            raise ValueError("a registered dock must not already be placed")
        dock.setObjectName(f"{self.PANE_PREFIX}{pane_id}")
        self.docks[pane_id] = dock
        self._watch_dock(pane_id, dock)

    def render(self, snapshot: Mapping[str, object]) -> None:
        self._rendering = True
        try:
            desired = deepcopy(dict(snapshot))
            frames = desired.get("frames", [])
            if not isinstance(frames, list):
                raise ValueError("frames must be a list")
            self._refresh_live_frame_windows()

            desired_panes = {
                pane_id
                for frame in frames
                for group in frame["groups"]
                for pane_id in group["panes"]
            }
            for pane_id in desired_panes:
                self._ensure_dock(pane_id)

            for frame in frames:
                self._ensure_frame(frame)
            for frame in frames:
                self._realize_frame(frame)

            desired_frame_ids = {frame["id"] for frame in frames}
            for frame_id in set(self.frame_windows).difference(desired_frame_ids):
                window = self.frame_windows.pop(frame_id)
                try:
                    if not window.dockWidgets():
                        window.hide()
                except RuntimeError:
                    pass

            for pane_id in set(self.docks).difference(desired_panes):
                dock = self.docks.pop(pane_id)
                self.manager.removeDockWidget(dock)
                dock.hide()
                dock.deleteLater()

            self._snapshot = desired
            if self._projected_active_pane in self.docks:
                active_dock = self.docks[self._projected_active_pane]
                window = active_dock.floatingDockContainer()
                if window is not None:
                    window.activateWindow()
                content = active_dock.widget()
                if content is not None:
                    content.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
        finally:
            self._rendering = False
        if self._projected_active_pane is not None:
            self._schedule_sync()

    def capture_layout(self) -> dict[str, object]:
        """Capture a settled QtADS layout in application contract form."""

        if self.manager.dockAreaCount() != 0:
            raise ValueError("the private manager/root contains dock areas")

        windows = [
            window
            for window in self.manager.floatingWidgets()
            if isValid(window) and window.dockWidgets()
        ]
        preferred = []
        if self._model is not None:
            preferred = [
                frame["id"] for frame in self._model.serialize_layout()["frames"]
            ]
        rank = {frame_id: index for index, frame_id in enumerate(preferred)}
        windows.sort(
            key=lambda window: rank.get(self._frame_id_from_window(window), len(rank))
        )

        used_frames: set[str] = set()
        used_groups: set[str] = set()
        frames: list[dict[str, object]] = []
        current_windows: dict[str, QtAds.CFloatingDockContainer] = {}
        captured_panes: list[str] = []
        for window in windows:
            frame_id = self._frame_id_from_window(window)
            if frame_id is None or frame_id in used_frames:
                frame_id = self._new_user_frame_id(used_frames)
                window.setObjectName(f"{self.FRAME_PREFIX}{frame_id}")
            used_frames.add(frame_id)
            current_windows[frame_id] = window
            self._watch_window(window)

            groups: list[dict[str, object]] = []
            root = self._capture_node(
                window.dockContainer().rootSplitter(), groups, used_groups
            )
            if root is None:
                raise ValueError(f"frame has docks but no layout tree: {frame_id}")
            frame_panes = [pane for group in groups for pane in group["panes"]]
            if len(frame_panes) != len(set(frame_panes)):
                raise ValueError(f"duplicate pane in frame: {frame_id}")
            captured_panes.extend(frame_panes)
            frames.append({"id": frame_id, "root": root, "groups": groups})

        if len(captured_panes) != len(set(captured_panes)):
            raise ValueError("a pane appears in more than one frame")
        self.frame_windows = current_windows
        active = self._captured_active_pane(captured_panes, frames)
        schema = self._model.SCHEMA_VERSION if self._model is not None else 2
        return {"schema": schema, "active_pane_id": active, "frames": frames}

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        for window in tuple(self.frame_windows.values()):
            try:
                window.hide()
                window.deleteLater()
            except RuntimeError:
                pass
        self.frame_windows.clear()
        self.manager.hide()
        self.manager.deleteLater()

    def _floating_widget_created(self, *args: object) -> None:
        for value in args:
            if isinstance(value, QtAds.CFloatingDockContainer):
                self._watch_window(value)
        self._schedule_sync()

    def _watch_window(self, window: QtAds.CFloatingDockContainer) -> None:
        if (
            sys.platform == "win32"
            and QtWidgets.QApplication.platformName() == "windows"
            and not window.property("peer-native-independent")
        ):
            # The hidden manager cannot remain the native owner of a Windows
            # application frame. QtADS keeps its manager pointer and registry.
            stylesheet = self.manager.styleSheet()
            window.setParent(
                None, window.windowFlags() | QtCore.Qt.WindowType.WindowMinimizeButtonHint
            )
            if stylesheet:
                window.setStyleSheet(stylesheet)
            window.setProperty("peer-native-independent", True)
        if not window.property("peer-frame-close-watched"):
            window.setProperty("peer-frame-close-watched", True)
            window.installEventFilter(self._projection_lifecycle_filter)
            frame_id = self._frame_id_from_window(window)
            window.destroyed.connect(
                lambda _object=None, frame_id=frame_id, reference=ref(window): (
                    self._projection_destroyed("frame", frame_id, reference)
                )
            )
        container = window.dockContainer()
        if not container.property("peer-sync-watched"):
            container.setProperty("peer-sync-watched", True)
            container.dockAreasAdded.connect(self._schedule_sync)
            container.dockAreasRemoved.connect(self._schedule_sync)
        for index in range(container.dockAreaCount()):
            self._watch_area(container.dockArea(index))

    def _watch_dock(self, pane_id: str, dock: QtAds.CDockWidget) -> None:
        custom_close = QtAds.CDockWidget.DockWidgetFeature.CustomCloseHandling
        if not dock.features() & custom_close:
            dock.setFeatures(dock.features() | custom_close)
        if dock.property("peer-pane-lifecycle-watched"):
            return
        dock.setProperty("peer-pane-lifecycle-watched", True)
        dock.installEventFilter(self._projection_lifecycle_filter)
        dock.closeRequested.connect(
            lambda pane_id=pane_id: self._request_native_pane_close(pane_id)
        )
        dock.destroyed.connect(
            lambda _object=None, pane_id=pane_id, reference=ref(dock): (
                self._projection_destroyed("pane", pane_id, reference)
            )
        )

    def _handle_native_dock_close(
        self, dock: QtAds.CDockWidget, event: QtCore.QEvent
    ) -> bool:
        if self._rendering or self._closing or self._model is None:
            return False
        try:
            pane_id = self._pane_id_from_dock(dock)
        except ValueError:
            return False
        if pane_id not in self._model.panes:
            return False
        event.ignore()
        self._request_native_pane_close(pane_id)
        return True

    def _request_native_pane_close(self, pane_id: str) -> None:
        if (
            self._rendering
            or self._closing
            or self._model is None
            or pane_id not in self._model.panes
            or pane_id in self._pane_close_in_progress
        ):
            return
        request = self._pane_close_request
        if request is None:
            return
        self._pane_close_in_progress.add(pane_id)
        try:
            self.last_pane_close_result = request(pane_id)
        finally:
            self._pane_close_in_progress.discard(pane_id)
        if (
            not self.last_pane_close_result.applied
            and pane_id in self._model.panes
        ):
            self._queue_visibility_repair("pane", pane_id)

    def _projection_hidden(self, watched: QtCore.QObject) -> None:
        if self._rendering or self._closing or self._repairing_visibility:
            return
        if isinstance(watched, QtAds.CDockWidget):
            try:
                self._queue_visibility_repair(
                    "pane", self._pane_id_from_dock(watched)
                )
            except ValueError:
                pass
        elif isinstance(watched, QtAds.CFloatingDockContainer):
            frame_id = self._frame_id_from_window(watched)
            if frame_id is not None and watched.dockWidgets():
                self._queue_visibility_repair("frame", frame_id)

    def _queue_visibility_repair(self, kind: str, identity: str) -> None:
        self._hidden_projection_candidates.add((kind, identity))
        if self._visibility_repair_pending:
            return
        self._visibility_repair_pending = True
        QtCore.QTimer.singleShot(0, self._repair_projection_visibility)

    def _repair_projection_visibility(self) -> None:
        self._visibility_repair_pending = False
        candidates = self._hidden_projection_candidates
        self._hidden_projection_candidates = set()
        if self._rendering or self._closing or self._model is None:
            return

        repairs: list[str] = []
        self._repairing_visibility = True
        try:
            for kind, identity in candidates:
                if kind == "pane" and identity in self._model.panes:
                    dock = self.docks.get(identity)
                    if dock is None:
                        continue
                    try:
                        area = dock.dockAreaWidget()
                        if dock.isClosed():
                            dock.toggleView(True)
                            repairs.append(f"closed pane {identity}")
                        elif (
                            area is not None
                            and area.currentDockWidget() is dock
                            and not dock.isVisible()
                        ):
                            dock.show()
                            repairs.append(f"hidden active pane {identity}")
                    except RuntimeError:
                        continue
                elif kind == "frame" and identity in self._model.frames:
                    window = self.frame_windows.get(identity)
                    if window is None:
                        continue
                    try:
                        if window.dockWidgets() and not window.isVisible():
                            window.show()
                            repairs.append(f"hidden populated frame {identity}")
                    except RuntimeError:
                        continue
        finally:
            self._repairing_visibility = False
        if repairs:
            self.last_sync_result = OperationResult(
                OperationStatus.INVALID,
                "backend projection drift repaired: " + ", ".join(repairs),
            )

    def _intercept_projection_delete(self, watched: QtCore.QObject) -> bool:
        if self._rendering or self._closing or self._model is None:
            return False
        identity: str | None = None
        if isinstance(watched, QtAds.CDockWidget):
            try:
                identity = self._pane_id_from_dock(watched)
            except ValueError:
                return False
            live = identity in self._model.panes
            kind = "pane"
        elif isinstance(watched, QtAds.CFloatingDockContainer):
            identity = self._frame_id_from_window(watched)
            live = identity in self._model.frames and bool(watched.dockWidgets())
            kind = "frame"
        else:
            return False
        if not live or identity is None:
            return False
        self.last_sync_result = OperationResult(
            OperationStatus.INVALID,
            f"rejected deferred deletion of live {kind}: {identity}",
        )
        self._queue_visibility_repair(kind, identity)
        return True

    def _projection_destroyed(
        self, kind: str, identity: str | None, reference: ReferenceType[QtCore.QObject]
    ) -> None:
        if self._closing or self._model is None:
            return
        # A numeric Python id can be reused after its wrapper is collected,
        # while the old native object's destroyed callback is still pending.
        projection = reference()
        if projection is None:
            return
        objects = self.docks if kind == "pane" else self.frame_windows
        if identity is None:
            identity = next(
                (key for key, value in objects.items() if value is projection),
                None,
            )
        if identity is None:
            return
        current = objects.get(identity)
        if current is not projection:
            return
        objects.pop(identity, None)
        live = (
            identity in self._model.panes
            if kind == "pane"
            else identity in self._model.frames
        )
        if not live:
            return
        self.fatal_backend_error = RuntimeError(
            f"live {kind} was destroyed outside application lifecycle: {identity}"
        )
        self.last_sync_result = OperationResult(
            OperationStatus.INVALID, str(self.fatal_backend_error)
        )

    def _handle_native_frame_close(
        self, watched: QtCore.QObject, event: QtCore.QEvent
    ) -> bool:
        if self._rendering or self._closing or self._model is None:
            return False
        if not isinstance(watched, QtAds.CFloatingDockContainer):
            return False
        frame_id = self._frame_id_from_window(watched)
        if frame_id is None or frame_id not in self._model.frames:
            return False
        live_docks = [dock for dock in watched.dockWidgets() if not dock.isClosed()]
        if not live_docks:
            return False

        event.ignore()
        if frame_id in self._frame_close_in_progress:
            return True
        request = self._frame_close_request
        if request is None:
            return True
        self._frame_close_in_progress.add(frame_id)
        try:
            self.last_frame_close_result = request(frame_id)
        finally:
            self._frame_close_in_progress.discard(frame_id)
        if (
            not self.last_frame_close_result.applied
            and frame_id in self._model.frames
        ):
            watched.show()
        return True

    def _watch_area(self, area: QtAds.CDockAreaWidget) -> None:
        if Capability.TAB_SIDE in self.capabilities:
            targets = [area.titleBar()]
            targets.extend(dock.tabWidget() for dock in area.dockWidgets())
            for target in targets:
                if not target.property("peer-tab-side-menu"):
                    target.setProperty("peer-tab-side-menu", True)
                    target.installEventFilter(self._tab_side_menu_filter)
        if area.property("peer-sync-watched"):
            return
        area.setProperty("peer-sync-watched", True)
        area.currentChanged.connect(
            lambda index, watched_area=area: self._area_current_changed(
                watched_area, index
            )
        )

    def append_tab_side_menu(
        self, area: QtAds.CDockAreaWidget, menu: QtWidgets.QMenu
    ) -> QtWidgets.QMenu | None:
        """Append a checked, group-local four-side command to ``menu``."""

        if Capability.TAB_SIDE not in self.capabilities or self._model is None:
            return None
        group_id = self._group_id_from_area(area)
        if group_id is None:
            return None
        side = self._tab_side_for_group(group_id)
        if side is None:
            return None

        menu.addSeparator()
        submenu = menu.addMenu("Tab position")
        action_group = QtGui.QActionGroup(submenu)
        action_group.setExclusive(True)
        submenu._peer_tab_side_action_group = action_group
        for candidate in TabSide:
            action = submenu.addAction(candidate.value.title())
            action.setCheckable(True)
            action.setData(candidate.value)
            action.setChecked(candidate is side)
            action_group.addAction(action)
            action.triggered.connect(
                lambda checked=False, group_id=group_id, candidate=candidate: (
                    self._set_group_tab_side(group_id, candidate)
                )
            )
        return submenu

    def _tab_side_for_group(self, group_id: str) -> TabSide | None:
        if self._model is None:
            return None
        for frame in self._model.serialize_layout()["frames"]:
            for group in frame["groups"]:
                if group["id"] == group_id:
                    return TabSide(group["tab_side"])
        return None

    def _set_group_tab_side(self, group_id: str, side: TabSide) -> None:
        if self._model is None:
            return
        result = self._model.set_group_tab_side(group_id, side)
        if not result.applied:
            raise RuntimeError(result.detail)

    def _area_current_changed(
        self, area: QtAds.CDockAreaWidget, index: int
    ) -> None:
        if self._rendering or self._closing:
            return
        dock = area.currentDockWidget()
        if dock is not None:
            try:
                self._active_pane_hint = self._pane_id_from_dock(dock)
            except ValueError:
                self._active_pane_hint = None
        self._schedule_sync()

    def _focused_dock_widget_changed(self, dock: QtAds.CDockWidget | None) -> None:
        if self._rendering or self._closing or self._model is None or dock is None:
            return
        if self._projected_active_pane is not None:
            try:
                pane_id = self._pane_id_from_dock(dock)
            except ValueError:
                return
            if pane_id == self._projected_active_pane:
                return
            self._projected_active_pane = None
        if any(window.isDraggingActive() for window in self.manager.floatingWidgets()):
            return
        try:
            pane_id = self._pane_id_from_dock(dock)
        except ValueError:
            return
        self._active_pane_hint = pane_id
        self._model.adopt_backend_activation(pane_id)

    def preserve_projected_activation(self, pane_id: str | None) -> None:
        """Ignore stale native focus notifications during layout restoration."""

        self._projected_active_pane = pane_id
        self._active_pane_hint = pane_id

    def _schedule_sync(self, *args: object) -> None:
        if (
            self._rendering
            or self._closing
            or self._model is None
            or self._sync_pending
        ):
            return
        self._sync_pending = True
        QtCore.QTimer.singleShot(0, self._synchronize_settled_layout)

    def _synchronize_settled_layout(self) -> None:
        self._sync_pending = False
        if self._rendering or self._closing or self._model is None:
            return
        if any(window.isDraggingActive() for window in self.manager.floatingWidgets()):
            self._sync_pending = True
            QtCore.QTimer.singleShot(16, self._synchronize_settled_layout)
            return

        authoritative = self._model.serialize_layout()
        try:
            captured = self.capture_layout()
            result = self._model.adopt_backend_layout(captured)
        except (RuntimeError, ValueError) as error:
            result = OperationResult(OperationStatus.INVALID, str(error))
        self.last_sync_result = result
        if result.applied:
            self.adoption_count += 1
            self._snapshot = self._model.serialize_layout()
        else:
            self.render(authoritative)
        self._active_pane_hint = None
        self._refresh_live_frame_windows()
        if not self._settled_notification_pending:
            self._settled_notification_pending = True
            QtCore.QTimer.singleShot(0, self._notify_settled)

    def _notify_settled(self) -> None:
        self._settled_notification_pending = False
        if self._closing:
            return
        # The projection is interactive before observers inspect the settled
        # frame set.  Leaving this hint live during notification causes a
        # genuine focus change in an observer turn to be mistaken for stale
        # restoration focus and discarded.
        self._projected_active_pane = None
        settled_windows = tuple(self.frame_windows.values())
        for callback in tuple(self._settled_callbacks):
            callback(settled_windows)

    def container_for_frame(self, frame_id: str) -> QtAds.CDockContainerWidget:
        return self.frame_windows[frame_id].dockContainer()

    def _refresh_live_frame_windows(self) -> None:
        live: dict[str, QtAds.CFloatingDockContainer] = {}
        for window in self.manager.floatingWidgets():
            if not isValid(window):
                continue
            frame_id = self._frame_id_from_window(window)
            if frame_id is not None and frame_id not in live:
                live[frame_id] = window
        self.frame_windows = live

    def _ensure_dock(self, pane_id: str) -> QtAds.CDockWidget:
        dock = self.docks.get(pane_id)
        if dock is not None:
            self._watch_dock(pane_id, dock)
            return dock
        dock = QtAds.CDockWidget(self.manager, pane_id)
        dock.setObjectName(f"{self.PANE_PREFIX}{pane_id}")
        dock.setWidget(self._pane_factory(pane_id))
        self.docks[pane_id] = dock
        self._watch_dock(pane_id, dock)
        return dock

    @staticmethod
    def restore_frame_geometry(window, geometry) -> None:
        """Recover an inaccessible title bar after monitor/DPI layout changes."""
        rect = QtCore.QRect(*geometry)
        available = [screen.availableGeometry() for screen in QtGui.QGuiApplication.screens()]
        title = QtCore.QRect(rect.x(), rect.y(), min(rect.width(), 120), min(rect.height(), 32))
        if available and not any(
            title.intersected(screen).width() >= min(60, title.width())
            and title.intersected(screen).height() >= min(24, title.height())
            for screen in available
        ):
            center = rect.center()
            target = min(available, key=lambda screen:
                (screen.center().x() - center.x()) ** 2 + (screen.center().y() - center.y()) ** 2)
            width, height = min(rect.width(), target.width()), min(rect.height(), target.height())
            x = max(target.left(), min(rect.x(), target.right() - width + 1))
            y = max(target.top(), min(rect.y(), target.bottom() - height + 1))
            rect = QtCore.QRect(x, y, width, height)
        window.setGeometry(rect.x(), rect.y(), rect.width(), rect.height())

    def _ensure_frame(self, frame: Mapping[str, object]) -> None:
        frame_id = frame["id"]
        window = self.frame_windows.get(frame_id)
        if (
            window is not None
            and isValid(window)
            and window.dockContainer().dockManager() is self.manager
        ):
            return
        self.frame_windows.pop(frame_id, None)
        first_pane = self._first_pane(frame)
        dock = self.docks[first_pane]
        window = self.manager.addDockWidgetFloating(dock)
        window.setObjectName(f"{self.FRAME_PREFIX}{frame_id}")
        window.setWindowTitle(str(frame_id))
        window.resize(640, 420)
        window.move(self._next_origin)
        self._next_origin += QtCore.QPoint(36, 36)
        window.show()
        self.frame_windows[str(frame_id)] = window
        self._watch_window(window)

    def _realize_frame(self, frame: Mapping[str, object]) -> None:
        # Moving a last pane detaches its old floating container immediately,
        # before deferred deletion invalidates the Python wrapper. Earlier
        # placements may have retired this target since the initial ensure pass.
        self._ensure_frame(frame)
        frame_id = str(frame["id"])
        container = self.container_for_frame(frame_id)
        groups = {group["id"]: group for group in frame["groups"]}
        root = frame["root"]

        first_group_id = self._first_group_id(root)
        first_group = groups[first_group_id]
        first_dock = self.docks[first_group["panes"][0]]
        first_area = first_dock.dockAreaWidget()
        if first_area is None or first_area.dockContainer() is not container:
            self.manager.addDockWidgetToContainer(
                QtAds.CenterDockWidgetArea, first_dock, container
            )

        self._realize_node(root, groups, container, is_root=True)
        for group in groups.values():
            anchor = self.docks[group["panes"][0]]
            area = anchor.dockAreaWidget()
            for pane_id in group["panes"][1:]:
                dock = self.docks[pane_id]
                if dock.dockAreaWidget() is not area:
                    self.manager.addDockWidgetTabToArea(dock, area)
            active = self.docks[group["active_pane_id"]]
            area.setCurrentDockWidget(active)
            area.setObjectName(f"{self.GROUP_PREFIX}{group['id']}")
            area.setProperty("peer-tab-side", group["tab_side"])
            self._render_native_tab_side(area, TabSide(group["tab_side"]))
            self._watch_area(area)

    def _realize_node(
        self,
        node: Mapping[str, object],
        groups: Mapping[str, Mapping[str, object]],
        container: QtAds.CDockContainerWidget,
        *,
        is_root: bool,
    ) -> None:
        if node["type"] == "group":
            return
        children = node["children"]
        self._realize_node(children[0], groups, container, is_root=False)
        reference_group_id = self._first_group_id(children[0])
        reference_area = self.docks[
            groups[reference_group_id]["panes"][0]
        ].dockAreaWidget()
        orientation = node["orientation"]
        area = (
            QtAds.RightDockWidgetArea
            if orientation == "horizontal"
            else QtAds.BottomDockWidgetArea
        )
        for child in children[1:]:
            child_group_id = self._first_group_id(child)
            child_dock = self.docks[groups[child_group_id]["panes"][0]]
            child_area = child_dock.dockAreaWidget()
            child_container = child_area.dockContainer() if child_area else None
            if child_container is not container:
                target_area = None if is_root else reference_area
                container.addDockWidget(area, child_dock, target_area)
            self._realize_node(child, groups, container, is_root=False)

    @staticmethod
    def _first_group_id(node: Mapping[str, object]) -> str:
        while node["type"] == "split":
            node = node["children"][0]
        return str(node["group_id"])

    def _capture_node(
        self,
        widget: QtWidgets.QWidget,
        groups: list[dict[str, object]],
        used_groups: set[str],
    ) -> dict[str, object] | None:
        if isinstance(widget, QtAds.CDockAreaWidget):
            docks = [dock for dock in widget.dockWidgets() if not dock.isClosed()]
            if not docks:
                return None
            panes = [self._pane_id_from_dock(dock) for dock in docks]
            group_id = self._group_id_from_area(widget)
            if group_id is None or group_id in used_groups:
                group_id = self._new_user_group_id(used_groups)
                widget.setObjectName(f"{self.GROUP_PREFIX}{group_id}")
            used_groups.add(group_id)
            current = widget.currentDockWidget()
            active = self._pane_id_from_dock(current) if current in docks else panes[0]
            tab_side = widget.property("peer-tab-side")
            try:
                tab_side = TabSide(tab_side).value
            except ValueError:
                tab_side = self._inherited_tab_side(panes)
                widget.setProperty("peer-tab-side", tab_side)
            self._render_native_tab_side(widget, TabSide(tab_side))
            groups.append(
                {
                    "id": group_id,
                    "panes": panes,
                    "active_pane_id": active,
                    "tab_side": tab_side,
                }
            )
            self._watch_area(widget)
            return {"type": "group", "group_id": group_id}

        if isinstance(widget, QtWidgets.QSplitter):
            children = [
                self._capture_node(widget.widget(index), groups, used_groups)
                for index in range(widget.count())
            ]
            children = [child for child in children if child is not None]
            if not children:
                return None
            if len(children) == 1:
                return children[0]
            orientation = (
                "horizontal"
                if widget.orientation() == QtCore.Qt.Orientation.Horizontal
                else "vertical"
            )
            return {
                "type": "split",
                "orientation": orientation,
                "children": children,
            }
        raise ValueError(f"unsupported layout widget: {type(widget).__name__}")

    def _captured_active_pane(
        self,
        captured_panes: list[str],
        frames: list[dict[str, object]],
    ) -> str | None:
        if self._active_pane_hint in captured_panes:
            return self._active_pane_hint
        focused = self.manager.focusedDockWidget()
        if focused is not None:
            pane_id = self._pane_id_from_dock(focused)
            if pane_id in captured_panes:
                return pane_id
        if self._model is not None and self._model.active_pane_id in captured_panes:
            return self._model.active_pane_id
        for frame in frames:
            for group in frame["groups"]:
                return str(group["active_pane_id"])
        return None

    def _new_user_frame_id(self, used: set[str]) -> str:
        existing = set(self.frame_windows).union(used)
        while f"frame-user-{self._next_user_frame}" in existing:
            self._next_user_frame += 1
        value = f"frame-user-{self._next_user_frame}"
        self._next_user_frame += 1
        return value

    def _new_user_group_id(self, used: set[str]) -> str:
        while f"group-user-{self._next_user_group}" in used:
            self._next_user_group += 1
        value = f"group-user-{self._next_user_group}"
        self._next_user_group += 1
        return value

    def _inherited_tab_side(self, pane_ids: list[str]) -> str:
        if self._model is not None:
            for frame in self._model.serialize_layout()["frames"]:
                for group in frame["groups"]:
                    if any(pane_id in group["panes"] for pane_id in pane_ids):
                        return str(group["tab_side"])
        return TabSide.TOP.value

    @staticmethod
    def _render_native_tab_side(
        area: QtAds.CDockAreaWidget, side: TabSide
    ) -> None:
        """Render the subset implemented by our QtADS experiment fork.

        Published stock bindings remain metadata-only. The experiment fork
        advertises ``TAB_SIDE`` only when all four native enum values exist.
        """

        if not hasattr(area, "setTabPosition"):
            return
        positions = {
            TabSide.TOP: QtAds.CDockAreaWidget.TabPositionTop,
            TabSide.BOTTOM: QtAds.CDockAreaWidget.TabPositionBottom,
        }
        if _HAS_FOUR_TAB_SIDES:
            positions.update(
                {
                    TabSide.LEFT: QtAds.CDockAreaWidget.TabPositionLeft,
                    TabSide.RIGHT: QtAds.CDockAreaWidget.TabPositionRight,
                }
            )
        position = positions.get(side)
        if position is not None:
            area.setTabPosition(position)

    @classmethod
    def _pane_id_from_dock(cls, dock: QtAds.CDockWidget) -> str:
        name = dock.objectName()
        if not name.startswith(cls.PANE_PREFIX):
            raise ValueError(f"unknown dock widget identity: {name!r}")
        return name[len(cls.PANE_PREFIX) :]

    @classmethod
    def _frame_id_from_window(
        cls, window: QtAds.CFloatingDockContainer
    ) -> str | None:
        name = window.objectName()
        return name[len(cls.FRAME_PREFIX) :] if name.startswith(cls.FRAME_PREFIX) else None

    @classmethod
    def _group_id_from_area(cls, area: QtAds.CDockAreaWidget) -> str | None:
        name = area.objectName()
        return name[len(cls.GROUP_PREFIX) :] if name.startswith(cls.GROUP_PREFIX) else None

    @classmethod
    def _first_pane(cls, frame: Mapping[str, object]) -> str:
        group_id = cls._first_group_id(frame["root"])
        groups = {group["id"]: group for group in frame["groups"]}
        return str(groups[group_id]["panes"][0])

    @staticmethod
    def _default_pane_factory(pane_id: str) -> QtWidgets.QWidget:
        editor = QtWidgets.QPlainTextEdit()
        editor.setPlainText(f"Peer pane: {pane_id}\n")
        return editor
