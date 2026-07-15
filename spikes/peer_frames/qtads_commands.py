"""Qt menu projection for application-owned commands on QtADS peer frames."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from PySide6 import QtCore, QtGui, QtWidgets

from .commands import CommandRegistry


COMMAND_ID_PROPERTY = "applicationCommandId"


@dataclass
class _FrameProjection:
    window: QtWidgets.QWidget
    menu_bar: QtWidgets.QMenuBar
    menu: QtWidgets.QMenu
    actions: dict[str, QtGui.QAction]


class QtAdsCommandProjector:
    """Project selected application commands into every QtADS peer frame."""

    def __init__(
        self,
        registry: CommandRegistry,
        dock_manager: QtCore.QObject,
        command_ids: tuple[str, ...],
        *,
        native_menus: bool | None = None,
        menu_title: str = "File",
    ):
        self.registry = registry
        self.dock_manager = dock_manager
        self.command_ids = command_ids
        self.native_menus = (
            sys.platform == "darwin" if native_menus is None else native_menus
        )
        self.menu_title = menu_title
        self._projections: dict[int, _FrameProjection] = {}

        for command_id in command_ids:
            registry.state(command_id)
        dock_manager.floatingWidgetCreated.connect(self._on_floating_widget_created)
        for window in dock_manager.floatingWidgets():
            self.project(window)

    @property
    def projected_window_ids(self) -> frozenset[int]:
        return frozenset(self._projections)

    def project(self, window: QtWidgets.QWidget) -> None:
        key = id(window)
        existing = self._projections.get(key)
        if existing is not None and existing.window is window:
            return
        layout = window.layout()
        if layout is None or not hasattr(layout, "insertWidget"):
            raise RuntimeError("peer frame must provide an insertable layout")

        menu_bar = QtWidgets.QMenuBar(window)
        menu_bar.setObjectName("peerCommandMenuBar")
        menu_bar.setNativeMenuBar(self.native_menus)
        menu = menu_bar.addMenu(self.menu_title)
        menu.setObjectName("peerCommandMenu")
        actions: dict[str, QtGui.QAction] = {}
        for command_id in self.command_ids:
            state = self.registry.state(command_id)
            action = menu.addAction(state.label)
            action.setObjectName(f"peer-command:{command_id}")
            action.setProperty(COMMAND_ID_PROPERTY, command_id)
            action.setEnabled(state.enabled)
            action.setShortcutContext(QtCore.Qt.ShortcutContext.WindowShortcut)
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

        if not self.native_menus:
            layout.insertWidget(0, menu_bar)
        self._projections[key] = _FrameProjection(window, menu_bar, menu, actions)
        window.destroyed.connect(
            lambda _object=None, key=key: self._projections.pop(key, None)
        )

    def menu_bar_for(self, window: QtWidgets.QWidget) -> QtWidgets.QMenuBar:
        return self._projection(window).menu_bar

    def action_for(
        self, window: QtWidgets.QWidget, command_id: str
    ) -> QtGui.QAction:
        return self._projection(window).actions[command_id]

    def _projection(self, window: QtWidgets.QWidget) -> _FrameProjection:
        projection = self._projections.get(id(window))
        if projection is None or projection.window is not window:
            raise KeyError("window has no command projection")
        return projection

    def _on_floating_widget_created(self, *args: object) -> None:
        for value in args:
            if isinstance(value, QtWidgets.QWidget):
                self.project(value)
