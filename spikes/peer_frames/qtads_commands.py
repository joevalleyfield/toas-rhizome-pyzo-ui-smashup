"""Qt menu projection for application-owned commands on QtADS peer frames."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum

from PySide6 import QtCore, QtGui, QtWidgets

from .commands import CommandRegistry


COMMAND_ID_PROPERTY = "applicationCommandId"


@dataclass
class _MenuProjection:
    menu_bar: QtWidgets.QMenuBar
    menu: QtWidgets.QMenu
    actions: dict[str, QtGui.QAction]


class MenuProjectionMode(str, Enum):
    SHARED_NATIVE = "shared-native"
    PER_FRAME = "per-frame"


class QtAdsCommandProjector:
    """Project selected application commands into every QtADS peer frame."""

    def __init__(
        self,
        registry: CommandRegistry,
        dock_manager: QtCore.QObject,
        command_ids: tuple[str, ...],
        *,
        native_menus: bool | None = None,
        projection_mode: MenuProjectionMode | None = None,
        menu_title: str = "File",
    ):
        self.registry = registry
        self.dock_manager = dock_manager
        self.command_ids = command_ids
        if native_menus is not None and projection_mode is not None:
            raise ValueError("specify native_menus or projection_mode, not both")
        if projection_mode is None:
            use_native = sys.platform == "darwin" if native_menus is None else native_menus
            projection_mode = (
                MenuProjectionMode.SHARED_NATIVE
                if use_native
                else MenuProjectionMode.PER_FRAME
            )
        self.projection_mode = MenuProjectionMode(projection_mode)
        self.menu_title = menu_title
        self._windows: dict[int, QtWidgets.QWidget] = {}
        self._frame_projections: dict[int, _MenuProjection] = {}
        self._application_projection = (
            self._create_projection(None)
            if self.projection_mode is MenuProjectionMode.SHARED_NATIVE
            else None
        )

        for command_id in command_ids:
            registry.state(command_id)
        dock_manager.floatingWidgetCreated.connect(self._on_floating_widget_created)
        for window in dock_manager.floatingWidgets():
            self.project(window)

    @property
    def projected_window_ids(self) -> frozenset[int]:
        return frozenset(self._windows)

    @property
    def native_menus(self) -> bool:
        return self.projection_mode is MenuProjectionMode.SHARED_NATIVE

    @property
    def application_menu_bar(self) -> QtWidgets.QMenuBar | None:
        if self._application_projection is None:
            return None
        return self._application_projection.menu_bar

    def project(self, window: QtWidgets.QWidget) -> None:
        key = id(window)
        if self._windows.get(key) is window:
            return

        if self._application_projection is not None:
            self._track_window(key, window)
            return
        layout = window.layout()
        if layout is None or not hasattr(layout, "insertWidget"):
            raise RuntimeError("peer frame must provide an insertable layout")
        projection = self._create_projection(window)
        layout.insertWidget(0, projection.menu_bar)
        self._frame_projections[key] = projection
        self._track_window(key, window)

    def _create_projection(
        self, parent: QtWidgets.QWidget | None
    ) -> _MenuProjection:
        shared = parent is None
        menu_bar = QtWidgets.QMenuBar(parent)
        menu_bar.setObjectName(
            "applicationCommandMenuBar" if shared else "peerCommandMenuBar"
        )
        menu_bar.setNativeMenuBar(shared)
        menu = menu_bar.addMenu(self.menu_title)
        menu.setObjectName(
            "applicationCommandMenu" if shared else "peerCommandMenu"
        )
        actions: dict[str, QtGui.QAction] = {}
        for command_id in self.command_ids:
            state = self.registry.state(command_id)
            action = menu.addAction(state.label)
            action.setObjectName(f"peer-command:{command_id}")
            action.setProperty(COMMAND_ID_PROPERTY, command_id)
            action.setEnabled(state.enabled)
            action.setShortcutContext(
                QtCore.Qt.ShortcutContext.ApplicationShortcut
                if shared
                else QtCore.Qt.ShortcutContext.WindowShortcut
            )
            if state.shortcuts:
                action.setShortcuts(
                    [QtGui.QKeySequence(shortcut) for shortcut in state.shortcuts]
                )
            if command_id == "application.quit":
                action.setMenuRole(QtGui.QAction.MenuRole.QuitRole)
            action.triggered.connect(
                lambda _checked=False, command_id=command_id: self.registry.invoke(
                    command_id
                )
            )
            actions[command_id] = action
        return _MenuProjection(menu_bar, menu, actions)

    def menu_bar_for(self, window: QtWidgets.QWidget) -> QtWidgets.QMenuBar:
        return self._projection(window).menu_bar

    def action_for(
        self, window: QtWidgets.QWidget, command_id: str
    ) -> QtGui.QAction:
        return self._projection(window).actions[command_id]

    def _projection(self, window: QtWidgets.QWidget) -> _MenuProjection:
        key = id(window)
        if self._windows.get(key) is not window:
            raise KeyError("window has no command projection")
        if self._application_projection is not None:
            return self._application_projection
        return self._frame_projections[key]

    def _forget_window(self, key: int) -> None:
        self._windows.pop(key, None)
        self._frame_projections.pop(key, None)

    def _track_window(self, key: int, window: QtWidgets.QWidget) -> None:
        self._windows[key] = window
        window.destroyed.connect(lambda _object=None, key=key: self._forget_window(key))

    def _on_floating_widget_created(self, *args: object) -> None:
        for value in args:
            if isinstance(value, QtWidgets.QWidget):
                self.project(value)
