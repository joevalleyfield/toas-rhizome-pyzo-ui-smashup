"""Qt menu projection for application-owned commands on QtADS peer frames."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from PySide6 import QtCore, QtGui, QtWidgets
from shiboken6 import isValid

from .commands import CommandRegistry, CommandState
from .contract import ActiveContext
from .qtads_chrome import reserve_frame_chrome


COMMAND_ID_PROPERTY = "applicationCommandId"
CommandMenuProvider = Callable[[ActiveContext], tuple[str, ...]]
MenuBarBuilder = Callable[[QtWidgets.QMenuBar], object]


@dataclass
class _MenuProjection:
    menu_bar: QtWidgets.QMenuBar
    menu: QtWidgets.QMenu
    menus: dict[str, QtWidgets.QMenu]
    actions: dict[str, QtGui.QAction]
    window: QtWidgets.QWidget | None


class MenuProjectionMode(str, Enum):
    SHARED_NATIVE = "shared-native"
    PER_FRAME = "per-frame"


class QtAdsCommandProjector:
    """Project selected application commands into every QtADS peer frame."""

    def __init__(
        self,
        registry: CommandRegistry,
        dock_manager: QtCore.QObject,
        command_ids: tuple[str, ...] | CommandMenuProvider,
        *,
        native_menus: bool | None = None,
        projection_mode: MenuProjectionMode | None = None,
        menu_title: str = "File",
        menu_bar_builder: MenuBarBuilder | None = None,
        command_menu_titles: dict[str, str] | None = None,
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
        self.menu_bar_builder = menu_bar_builder
        self.command_menu_titles = dict(command_menu_titles or {})
        self._refreshing = False
        self._projecting_window_ids: set[int] = set()
        self._windows: dict[int, QtWidgets.QWidget] = {}
        self._frame_projections: dict[int, _MenuProjection] = {}
        self._application_projection = (
            self._create_projection(None)
            if self.projection_mode is MenuProjectionMode.SHARED_NATIVE
            else None
        )

        self._command_states()
        self.refresh()
        dock_manager.floatingWidgetCreated.connect(self._on_floating_widget_created)
        dock_manager.focusedDockWidgetChanged.connect(self.refresh)
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
        self._projecting_window_ids.add(key)
        try:
            if self._application_projection is not None:
                self._track_window(key, window)
                self.refresh()
                return
            projection = self._create_projection(window)
            self._frame_projections[key] = projection
            projection.menu.destroyed.connect(
                lambda _object=None, key=key: self._forget_window(key)
            )
            self._track_window(key, window)
            projection.menu_bar.show()
            self.refresh()
        finally:
            self._projecting_window_ids.discard(key)

    def refresh(self, *_args: object) -> None:
        if self._refreshing:
            return
        self._refreshing = True
        try:
            self._reconcile_windows()
            states = self._command_states()
            if self._application_projection is not None:
                if not isValid(self._application_projection.menu):
                    return
                self._sync_projection(
                    self._application_projection, states, shared=True
                )
                return
            for key, projection in tuple(self._frame_projections.items()):
                if not isValid(projection.menu):
                    self._forget_window(key)
                    continue
                self._sync_projection(projection, states, shared=False)
                self._reserve_menu_height(projection)
        finally:
            self._refreshing = False

    def _reconcile_windows(self) -> None:
        for key, window in tuple(self._windows.items()):
            if key in self._projecting_window_ids:
                continue
            if not isValid(window) or not window.dockWidgets():
                self._forget_window(key)
        for key, projection in tuple(self._frame_projections.items()):
            if not isValid(projection.menu_bar) or not isValid(projection.menu):
                self._forget_window(key)
        for window in self.dock_manager.floatingWidgets():
            if not isValid(window) or not window.dockWidgets():
                continue
            self.project(window)

    def _create_projection(
        self, parent: QtWidgets.QWidget | None
    ) -> _MenuProjection:
        shared = parent is None
        menu_bar = QtWidgets.QMenuBar(parent)
        menu_bar.setObjectName(
            "applicationCommandMenuBar" if shared else "peerCommandMenuBar"
        )
        menu_bar.setNativeMenuBar(shared)
        menu_bar.setProperty("applicationCommandProjection", True)
        built_menus = None
        if self.menu_bar_builder is not None:
            built_menus = self.menu_bar_builder(menu_bar)
        if built_menus is None:
            built_menus = getattr(menu_bar, "_menus", ())
        menus = {menu.title().replace("&", ""): menu for menu in built_menus}
        menu = menus.get(self.menu_title)
        if menu is None:
            menu = menu_bar.addMenu(self.menu_title)
            menus[self.menu_title] = menu
        menu.setObjectName(
            "applicationCommandMenu" if shared else "peerCommandMenu"
        )
        menu.aboutToShow.connect(self.refresh)
        return _MenuProjection(
            menu_bar,
            menu,
            menus,
            {},
            parent,
        )

    def _command_states(self) -> tuple[CommandState, ...]:
        context = self.registry.resolve_context()
        command_ids = (
            self.command_ids(context)
            if callable(self.command_ids)
            else self.command_ids
        )
        if len(command_ids) != len(set(command_ids)):
            raise ValueError("a projected menu cannot contain duplicate commands")
        return self.registry.states_for(command_ids, context)

    def _sync_projection(
        self,
        projection: _MenuProjection,
        states: tuple[CommandState, ...],
        *,
        shared: bool,
    ) -> None:
        desired_ids = {state.id for state in states}
        for command_id in set(projection.actions).difference(desired_ids):
            action = projection.actions.pop(command_id)
            projection.menu.removeAction(action)
            action.deleteLater()

        for action in projection.actions.values():
            for menu in projection.menus.values():
                menu.removeAction(action)
        for state in states:
            action = projection.actions.get(state.id)
            if action is None:
                action = self._create_action(projection.menu, state.id, shared)
                projection.actions[state.id] = action
            self._apply_state(action, state)
            menu_title = self.command_menu_titles.get(state.id, self.menu_title)
            projection.menus[menu_title].addAction(action)

    def _create_action(
        self,
        menu: QtWidgets.QMenu,
        command_id: str,
        shared: bool,
    ) -> QtGui.QAction:
        action = QtGui.QAction(menu)
        action.setObjectName(f"peer-command:{command_id}")
        action.setProperty(COMMAND_ID_PROPERTY, command_id)
        action.setShortcutContext(
            QtCore.Qt.ShortcutContext.ApplicationShortcut
            if shared
            else QtCore.Qt.ShortcutContext.WindowShortcut
        )
        if command_id == "application.quit":
            action.setMenuRole(QtGui.QAction.MenuRole.QuitRole)
        action.triggered.connect(
            lambda _checked=False, command_id=command_id: self._invoke(command_id)
        )
        return action

    def _invoke(self, command_id: str) -> None:
        self.registry.invoke(command_id)
        self.refresh()

    @staticmethod
    def _apply_state(action: QtGui.QAction, state: CommandState) -> None:
        action.setText(state.label)
        action.setEnabled(state.enabled)
        action.setCheckable(state.checkable)
        action.setChecked(state.checked if state.checkable else False)
        action.setShortcuts(
            [QtGui.QKeySequence(shortcut) for shortcut in state.shortcuts]
        )

    def menu_bar_for(self, window: QtWidgets.QWidget) -> QtWidgets.QMenuBar:
        return self._projection(window).menu_bar

    def menu_for(
        self, window: QtWidgets.QWidget, title: str | None = None
    ) -> QtWidgets.QMenu:
        projection = self._projection(window)
        return projection.menu if title is None else projection.menus[title]

    def primary_menu_bar(self) -> QtWidgets.QMenuBar:
        if self._application_projection is not None:
            return self._application_projection.menu_bar
        try:
            return next(iter(self._frame_projections.values())).menu_bar
        except StopIteration:
            raise RuntimeError("no peer menu bar is available") from None

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

    @staticmethod
    def _reserve_menu_height(projection: _MenuProjection) -> None:
        if projection.window is None or not isValid(projection.window):
            return
        reserve_frame_chrome(
            projection.window,
            "application-menu",
            top=projection.menu_bar.sizeHint().height(),
        )

    def _track_window(self, key: int, window: QtWidgets.QWidget) -> None:
        self._windows[key] = window
        window.destroyed.connect(lambda _object=None, key=key: self._forget_window(key))

    def _on_floating_widget_created(self, *args: object) -> None:
        for value in args:
            if isinstance(value, QtWidgets.QWidget):
                self.project(value)
