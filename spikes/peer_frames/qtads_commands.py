"""Qt menu projection for application-owned commands on QtADS peer frames."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from collections.abc import Callable, Iterable
from enum import Enum
from typing import Callable
from weakref import ref

from PySide6 import QtCore, QtGui, QtWidgets
from shiboken6 import isValid

from .commands import CommandRegistry, CommandState
from .contract import ActiveContext
from .qtads_chrome import frame_chrome_base_margins, reserve_frame_chrome


COMMAND_ID_PROPERTY = "applicationCommandId"
CommandMenuProvider = Callable[[ActiveContext], tuple[str, ...]]
MenuBarBuilder = Callable[[QtWidgets.QMenuBar], object]


def _assign_menu_mnemonics(menus: Iterable[QtWidgets.QMenu]) -> None:
    """Give translated menu titles distinct access keys without changing IDs."""
    preferred = {
        "file": "f", "edit": "e", "view": "v", "settings": "s",
        "shell": "l", "run": "r", "tools": "t", "help": "h",
    }
    menus = tuple(menus)
    used = set()
    for menu in menus:
        sequence = QtGui.QKeySequence.mnemonic(menu.title())
        if not sequence.isEmpty():
            used.add(sequence.toString().rsplit("+", 1)[-1].casefold())
    for menu in menus:
        title = menu.title()
        if not QtGui.QKeySequence.mnemonic(title).isEmpty():
            continue
        candidates = preferred.get(title.casefold(), "") + title
        for candidate in candidates:
            key = candidate.casefold()
            if candidate.isalnum() and key not in used:
                index = title.casefold().find(key)
                if index >= 0:
                    menu.setTitle(title[:index] + "&" + title[index:])
                    used.add(key)
                    break


class _FrameMenuKeyFilter(QtCore.QObject):
    def __init__(self, menu_bar):
        super().__init__(menu_bar)
        self._menu_bar = menu_bar

    def eventFilter(self, watched, event):
        if not isValid(self._menu_bar):
            return False
        return self._menu_bar._filter_event(watched, event)


class _MenuKeyDispatcher(QtCore.QObject):
    """One application filter, with routing limited to registered peer frames."""

    def __init__(self, application):
        super().__init__(application)
        self._bars = {}
        application.installEventFilter(self)

    def register(self, menu_bar):
        key = id(menu_bar.parentWidget())
        reference = ref(menu_bar)
        self._bars[key] = reference
        menu_bar.destroyed.connect(lambda: self._forget(key, reference))

    def _forget(self, key, reference):
        if self._bars.get(key) is reference:
            self._bars.pop(key, None)

    def eventFilter(self, watched, event):
        if event.type() not in (
            QtCore.QEvent.Type.ShortcutOverride, QtCore.QEvent.Type.KeyPress,
            QtCore.QEvent.Type.KeyRelease, QtCore.QEvent.Type.ActionAdded,
            QtCore.QEvent.Type.ActionRemoved, QtCore.QEvent.Type.MouseMove,
            QtCore.QEvent.Type.MouseButtonPress, QtCore.QEvent.Type.MouseButtonRelease,
        ):
            return False
        owner = watched
        if isinstance(owner, QtGui.QWindow):
            owner = QtWidgets.QWidget.find(owner.winId())
        if not isinstance(owner, QtWidgets.QWidget):
            return False
        recipient = owner
        while owner is not None:
            reference = self._bars.get(id(owner))
            if reference is not None:
                bar = reference()
                return bool(bar is not None and isValid(bar)
                            and bar._filter_event(recipient, event))
            owner = owner.parentWidget()
        return False


class _FrameMenuBar(QtWidgets.QMenuBar):
    """Size overlay chrome to its frame without entering the QtADS layout."""

    def __init__(self, frame):
        super().__init__(frame)
        self._root_menus = ()
        self._pending_access_menu = None
        self._shown_menu = None
        self._popup_sync_pending = False
        # Switching sibling native popups loses the keyboard grab under
        # Wayland. Reuse one surface; source menus retain action ownership,
        # command routing, and their dynamic aboutToShow/aboutToHide hooks.
        self._popup_widget = (
            QtWidgets.QMenu(self)
            if QtWidgets.QApplication.platformName() == "wayland" else None
        )
        if self._popup_widget is not None:
            self._popup_widget.aboutToHide.connect(self._popup_hidden)
        # QMenuBar manages its own application event-filter registration.
        # Keep our routing separate so Qt cannot unregister it during popup
        # transitions or style changes.
        self._key_filter = _FrameMenuKeyFilter(self)
        frame.installEventFilter(self._key_filter)
        application = QtWidgets.QApplication.instance()
        dispatcher = getattr(application, "_peer_menu_key_dispatcher", None)
        if dispatcher is None:
            dispatcher = application._peer_menu_key_dispatcher = _MenuKeyDispatcher(application)
        self._key_dispatcher = dispatcher
        dispatcher.register(self)
        self.fit_frame()

    def fit_frame(self):
        frame = self.parentWidget()
        margins = frame_chrome_base_margins(frame)
        self.setGeometry(
            margins.left(), margins.top(),
            max(0, frame.width() - margins.left() - margins.right()),
            self.sizeHint().height(),
        )

    def enable_keyboard_navigation(self, menus):
        self._root_menus = tuple(menus)

    def _popup_hidden(self):
        menu, self._shown_menu = self._shown_menu, None
        if menu is not None and isValid(menu):
            menu.aboutToHide.emit()
        if isValid(self):
            self.setActiveAction(None)
            # The Wayland highlight is painted from _shown_menu, while Qt's
            # active action may already be None. Clearing it then schedules
            # no repaint, so explicitly erase our previous selected title.
            self.update()

    def _sync_popup_actions(self):
        if not isValid(self):
            return
        self._popup_sync_pending = False
        if self._shown_menu is None or not isValid(self._shown_menu):
            return
        popup = self._popup_widget
        selected = popup.activeAction()
        desired = self._shown_menu.actions()
        if popup.actions() == desired:
            return
        # Never empty a mapped popup while refreshing it: Wayland dismisses
        # the popup and its keyboard grab when its last action is removed.
        for action in desired:
            if action not in popup.actions():
                popup.addAction(action)
        for action in popup.actions():
            if action not in desired:
                popup.removeAction(action)
        before = None
        for action in reversed(desired):
            popup.insertAction(before, action)
            before = action
        if selected not in popup.actions():
            selected = None
        popup.setActiveAction(selected)
        popup.adjustSize()

    def mousePressEvent(self, event):
        if self._popup_widget is not None and event.button() == QtCore.Qt.MouseButton.LeftButton:
            action = self.actionAt(event.position().toPoint())
            menu = next((menu for menu in self._root_menus
                         if menu.menuAction() == action), None)
            if menu is not None and action.isEnabled():
                if self._shown_menu is menu and self._popup_widget.isVisible():
                    self._popup_widget.hide()
                else:
                    self._open_menu(menu)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._popup_widget is not None and event.button() == QtCore.Qt.MouseButton.LeftButton:
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        if self._popup_widget is None or not self._popup_widget.isVisible() or self._shown_menu is None:
            return super().paintEvent(event)
        painter = QtWidgets.QStylePainter(self)
        option = QtWidgets.QStyleOptionMenuItem()
        option.initFrom(self)
        option.rect = self.rect()
        painter.drawControl(QtWidgets.QStyle.ControlElement.CE_MenuBarEmptyArea, option)
        selected = QtWidgets.QStyle.StateFlag.State_Selected | QtWidgets.QStyle.StateFlag.State_Sunken
        for action in self.actions():
            if not action.isVisible():
                continue
            self.initStyleOption(option, action)
            option.rect = self.actionGeometry(action)
            option.state &= ~selected
            if action == self._shown_menu.menuAction():
                option.state |= selected
            painter.drawControl(QtWidgets.QStyle.ControlElement.CE_MenuBarItem, option)

    def _cycle_menu(self, menu, key):
        menus = [
            candidate for candidate in self._root_menus
            if isValid(candidate) and candidate.menuAction().isEnabled()
            and candidate.menuAction().isVisible()
        ]
        if menu not in menus:
            return False
        forward = QtCore.Qt.Key.Key_Right
        if self.layoutDirection() == QtCore.Qt.LayoutDirection.RightToLeft:
            forward = QtCore.Qt.Key.Key_Left
        display = self._popup_widget if self._popup_widget is not None else menu
        selected = display.activeAction()
        # Right still enters an item's submenu; its Left key returns normally.
        if key == forward and selected is not None:
            if any(child.menuAction() == selected
                   for child in self.findChildren(QtWidgets.QMenu)):
                return False
        step = 1 if key == forward else -1
        target_menu = menus[(menus.index(menu) + step) % len(menus)]
        self._open_menu(target_menu)
        return True

    def _open_menu(self, target_menu):
        if self._popup_widget is not None:
            if self._shown_menu is not target_menu:
                if self._shown_menu is not None:
                    self._shown_menu.aboutToHide.emit()
                self._shown_menu = target_menu
                self._popup_widget.setTitle(target_menu.title())
                self._popup_widget.setAccessibleName(target_menu.title().replace("&", ""))
                target_menu.aboutToShow.emit()
                self._sync_popup_actions()
                # Selecting a submenu before mapping can open it without a
                # valid Wayland input serial and dismiss the whole menu chain.
                self._popup_widget.setActiveAction(None)
            self.update()
            position = self.mapToGlobal(self.actionGeometry(target_menu.menuAction()).bottomLeft())
            if self._popup_widget.isVisible():
                self._popup_widget.move(position)
            else:
                self._popup_widget.popup(position)
            return
        for menu in self._root_menus:
            menu.hide()
        self.setActiveAction(None)

        def open_neighbor():
            if not isValid(self) or not isValid(target_menu) or not self.isVisible():
                return
            target = target_menu.menuAction()
            if not target.isEnabled() or not target.isVisible():
                return
            target_menu.popup(self.mapToGlobal(self.actionGeometry(target).bottomLeft()))
            first = next((action for action in target_menu.actions()
                          if action.isEnabled() and action.isVisible()
                          and not action.isSeparator()), None)
            target_menu.setActiveAction(first)

        open_neighbor()

    def _access_key_menu(self, watched, event):
        if not isinstance(watched, QtWidgets.QWidget) or not self.isVisible():
            return None
        owner = watched
        while owner is not None and owner is not self.parentWidget():
            owner = owner.parentWidget()
        if owner is None or QtWidgets.QApplication.activeModalWidget() is not None:
            return None
        if event.modifiers() != QtCore.Qt.KeyboardModifier.AltModifier:
            return None
        for menu in self._root_menus:
            key = QtGui.QKeySequence.mnemonic(menu.title())
            if (not key.isEmpty() and key[0].key() == event.key()
                    and menu.menuAction().isEnabled() and menu.menuAction().isVisible()):
                return menu
        return None

    def _filter_event(self, watched, event):
        if (self._popup_widget is not None and watched is self._shown_menu
                and event.type() in (QtCore.QEvent.Type.ActionAdded, QtCore.QEvent.Type.ActionRemoved)
                and not self._popup_sync_pending):
            self._popup_sync_pending = True
            QtCore.QTimer.singleShot(0, self._sync_popup_actions)
        if (self._popup_widget is not None
                and event.type() in (QtCore.QEvent.Type.MouseMove,
                                     QtCore.QEvent.Type.MouseButtonPress,
                                     QtCore.QEvent.Type.MouseButtonRelease)):
            position = self.mapFromGlobal(event.globalPosition().toPoint())
            if self.rect().contains(position):
                action = self.actionAt(position)
                menu = next((menu for menu in self._root_menus
                             if menu.menuAction() == action), None)
                if menu is not None and action.isEnabled():
                    if (event.type() == QtCore.QEvent.Type.MouseButtonPress
                            and menu is self._shown_menu):
                        self._popup_widget.hide()
                    elif (event.type() == QtCore.QEvent.Type.MouseButtonPress
                          or (event.type() == QtCore.QEvent.Type.MouseMove
                              and self._popup_widget.isVisible()
                              and menu is not self._shown_menu)):
                        self._open_menu(menu)
                return True
        if (event.type() == QtCore.QEvent.Type.KeyRelease
                and event.key() == QtCore.Qt.Key.Key_Alt
                and self._pending_access_menu is not None):
            self._pending_access_menu = None
            # This access key owns Alt release. QMenuBar's separate Alt-only
            # keyboard-mode transition otherwise dismisses the new popup.
            return True
        if event.type() in (QtCore.QEvent.Type.ShortcutOverride, QtCore.QEvent.Type.KeyPress):
            menu = self._access_key_menu(watched, event)
            if menu is not None:
                event.accept()
                if event.type() == QtCore.QEvent.Type.KeyPress:
                    if event.modifiers() == QtCore.Qt.KeyboardModifier.AltModifier:
                        self._pending_access_menu = menu
                        QtWidgets.QApplication.instance().installEventFilter(self._key_dispatcher)
                        self._open_menu(menu)
                return True
        if (isinstance(watched, QtWidgets.QMenu)
                and event.type() == QtCore.QEvent.Type.KeyPress
                and event.key() in (QtCore.Qt.Key.Key_Left, QtCore.Qt.Key.Key_Right)
                and (watched in self._root_menus or watched is self._popup_widget)
                and watched.isVisible()):
            source = self._shown_menu if watched is self._popup_widget else watched
            if self._cycle_menu(source, event.key()):
                event.accept()
                return True
        if (watched is self.parentWidget()
                and event.type() in (QtCore.QEvent.Type.DeferredDelete, QtCore.QEvent.Type.Destroy)):
            # Retire subscriptions before QWidget destroys its child actions.
            # The frame's destroyed signal is too late for this ordering.
            dispose = getattr(self, "_disposeMenus", None)
            if self._popup_widget is not None:
                self._popup_widget.hide()
            if dispose is not None:
                dispose()
        if (watched is self.parentWidget()
                and event.type() in (QtCore.QEvent.Type.Resize, QtCore.QEvent.Type.Show)):
            self.fit_frame()
        return False


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
        frame_provider: Callable[[], Iterable[QtWidgets.QWidget]] | None = None,
    ):
        self.registry = registry
        self.dock_manager = dock_manager
        self._frame_provider = frame_provider
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
            self.reconcile()
            if self._application_projection is None and not self._frame_projections:
                # Quit/restart can retire every owner before its action returns.
                # No per-frame menu remains to evaluate a retired context for.
                return
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
            self.reconcile()
        finally:
            self._refreshing = False

    def reconcile(
        self, windows: Iterable[QtWidgets.QWidget] | None = None
    ) -> frozenset[int]:
        """Reconcile at a settled owner snapshot and return its window IDs."""

        source = (
            windows
            if windows is not None
            else (
                self._frame_provider()
                if self._frame_provider is not None
                else self.dock_manager.floatingWidgets()
            )
        )
        live_windows = {
            id(window): window
            for window in source
            if isValid(window)
        }
        for key, window in tuple(self._windows.items()):
            if key in self._projecting_window_ids:
                continue
            if key not in live_windows or live_windows[key] is not window:
                self._forget_window(key)
        for key, projection in tuple(self._frame_projections.items()):
            if not isValid(projection.menu_bar) or not isValid(projection.menu):
                self._forget_window(key)
        for window in live_windows.values():
            self.project(window)
        return frozenset(live_windows)

    def _create_projection(
        self, parent: QtWidgets.QWidget | None
    ) -> _MenuProjection:
        shared = parent is None
        menu_bar = QtWidgets.QMenuBar() if shared else _FrameMenuBar(parent)
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
        _assign_menu_mnemonics(menus.values())
        if isinstance(menu_bar, _FrameMenuBar):
            menu_bar.enable_keyboard_navigation(menus.values())
            if menu_bar._popup_widget is not None:
                # Legacy actions can create frames while their menu is open.
                # Reconcile after the command returns and its layout settles.
                menu_bar._popup_widget.triggered.connect(
                    lambda _action: QtCore.QTimer.singleShot(0, self.refresh)
                )
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
        projection = self._frame_projections.pop(key, None)
        if projection is not None and isValid(projection.menu_bar):
            dispose = getattr(projection.menu_bar, "_disposeMenus", None)
            if dispose is not None:
                dispose()
            projection.menu_bar.hide()
            projection.menu_bar.deleteLater()

    def retire_workspace(self, owner):
        for key, projection in tuple(self._frame_projections.items()):
            if getattr(projection.menu_bar, "_workspaceContextOwner", None) == owner:
                self._forget_window(key)

    @staticmethod
    def _reserve_menu_height(projection: _MenuProjection) -> None:
        if projection.window is None or not isValid(projection.window):
            return
        projection.menu_bar.fit_frame()
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
