from __future__ import annotations

import unittest

from PySide6 import QtCore, QtGui, QtWidgets
import PySide6QtAds as QtAds

from spikes.peer_frames.commands import CommandDescriptor, CommandRegistry
from spikes.peer_frames.contract import PaneDescriptor, PaneKind, WorkspaceModel
from spikes.peer_frames.qtads_backend import QtAdsPeerFrameBackend
from spikes.peer_frames.qtads_commands import (
    COMMAND_ID_PROPERTY,
    QtAdsCommandProjector,
)


class QtAdsCommandProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self) -> None:
        self.backend = QtAdsPeerFrameBackend()
        self.model = WorkspaceModel(self.backend)
        self.backend.bind_model(self.model)
        self.invocations: list[object] = []
        self.registry = CommandRegistry(self.model.resolve_active_context)
        self.registry.register(
            CommandDescriptor(
                "application.quit",
                "Quit Test Application",
                lambda context: self.invocations.append(context) or False,
                shortcuts=("Ctrl+Q",),
            )
        )
        self.projector = QtAdsCommandProjector(
            self.registry,
            self.backend.manager,
            ("application.quit",),
            native_menus=False,
        )

    def tearDown(self) -> None:
        self.backend.close()
        self.app.processEvents()

    def add_frame(self, pane_id: str) -> QtWidgets.QWidget:
        self.assertTrue(
            self.model.register_pane(
                PaneDescriptor(pane_id, PaneKind.EDITOR, pane_id.title())
            ).applied
        )
        self.assertTrue(self.model.create_frame(pane_id, pane_id).applied)
        self.app.processEvents()
        return self.backend.frame_windows[pane_id]

    def test_existing_and_future_frames_receive_one_quit_projection(self) -> None:
        self.assertEqual(self.projector.projected_window_ids, frozenset())
        first = self.add_frame("first")
        second = self.add_frame("second")

        for window in (first, second):
            menu_bars = window.findChildren(
                QtWidgets.QMenuBar,
                options=QtCore.Qt.FindChildOption.FindDirectChildrenOnly,
            )
            self.assertEqual(len(menu_bars), 1)
            self.assertIs(menu_bars[0], self.projector.menu_bar_for(window))
            self.assertFalse(menu_bars[0].isNativeMenuBar())
            self.assertEqual(window.layout().count(), 2)
            action = self.projector.action_for(window, "application.quit")
            self.assertEqual(
                action.property(COMMAND_ID_PROPERTY), "application.quit"
            )
            self.assertEqual(action.text(), "Quit Test Application")
            self.assertTrue(action.isEnabled())
            self.assertEqual(action.menuRole(), QtGui.QAction.MenuRole.QuitRole)
            self.assertEqual(
                [
                    shortcut.toString(QtGui.QKeySequence.SequenceFormat.PortableText)
                    for shortcut in action.shortcuts()
                ],
                ["Ctrl+Q"],
            )

        self.assertEqual(
            self.projector.projected_window_ids,
            frozenset((id(first), id(second))),
        )

    def test_native_projection_leaves_qtads_frame_layout_untouched(self) -> None:
        backend = QtAdsPeerFrameBackend()
        model = WorkspaceModel(backend)
        backend.bind_model(model)
        registry = CommandRegistry(model.resolve_active_context)
        registry.register(
            CommandDescriptor("application.quit", "Quit", lambda _context: None)
        )
        projector = QtAdsCommandProjector(
            registry,
            backend.manager,
            ("application.quit",),
            native_menus=True,
        )
        model.register_pane(PaneDescriptor("native", PaneKind.EDITOR, "Native"))
        model.create_frame("native", "native")
        self.app.processEvents()
        window = backend.frame_windows["native"]

        self.assertTrue(projector.native_menus)
        self.assertEqual(window.layout().count(), 1)
        self.assertIsNotNone(projector.menu_bar_for(window))
        backend.close()
        self.app.processEvents()

    def test_projection_is_idempotent_and_does_not_bypass_quit_handler(self) -> None:
        first = self.add_frame("first")
        before = self.model.serialize_layout()
        windows_before = dict(self.backend.frame_windows)
        self.projector.project(first)
        self.projector.project(first)

        self.assertEqual(
            len(first.findChildren(QtWidgets.QMenuBar)),
            1,
        )
        action = self.projector.action_for(first, "application.quit")
        action.trigger()
        self.assertEqual(len(self.invocations), 1)
        self.assertFalse(self.invocations[0].pane is None)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(self.backend.frame_windows, windows_before)
        self.assertTrue(first.isVisible())

    def test_destroyed_frame_removes_projector_tracking(self) -> None:
        window = self.add_frame("first")
        key = id(window)
        self.assertIn(key, self.projector.projected_window_ids)

        window.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(
            None, QtCore.QEvent.Type.DeferredDelete
        )
        self.app.processEvents()

        self.assertNotIn(key, self.projector.projected_window_ids)

    def test_detach_preserves_one_application_pane_outside_hidden_root(self) -> None:
        self.add_frame("first")
        original_frame_id = next(iter(self.model.frames))
        area = self.backend.docks["first"].dockAreaWidget()

        area.titleBar().button(QtAds.TitleBarButtonUndock).click()
        event_loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(100, event_loop.quit)
        event_loop.exec()

        layout = self.model.serialize_layout()
        self.assertEqual(len(layout["frames"]), 1)
        self.assertEqual(
            [
                pane_id
                for frame in layout["frames"]
                for group in frame["groups"]
                for pane_id in group["panes"]
            ],
            ["first"],
        )
        self.assertNotEqual(layout["frames"][0]["id"], original_frame_id)
        self.assertEqual(self.backend.manager.dockAreaCount(), 0)
        self.assertTrue(self.backend.docks["first"].isInFloatingContainer())


if __name__ == "__main__":
    unittest.main()
