from __future__ import annotations

import unittest
from unittest.mock import patch

from PySide6 import QtCore, QtWidgets
from shiboken6 import isValid

from spikes.peer_frames.contract import PaneDescriptor, PaneKind, WorkspaceModel
from spikes.peer_frames.qtads_backend import QtAdsPeerFrameBackend
from spikes.peer_frames.qtads_commands import QtAdsCommandProjector
from spikes.peer_frames.qtads_status import QtAdsStatusProjector
from spikes.peer_frames.commands import CommandDescriptor, CommandRegistry
from spikes.peer_frames.status import StatusSnapshot, StatusState


class StatusStateTests(unittest.TestCase):
    def test_state_is_observable_without_frames_and_has_no_kernel_affinity(
        self,
    ) -> None:
        state = StatusState()
        snapshots: list[StatusSnapshot] = []
        unsubscribe = state.subscribe(snapshots.append)

        state.set_message("Ready")
        state.set_cursor_text("Line: 4, Column: 2")
        state.set_visible(False)
        unsubscribe()
        state.set_message("not observed")

        self.assertEqual(
            snapshots,
            [
                StatusSnapshot(),
                StatusSnapshot(message="Ready"),
                StatusSnapshot(message="Ready", cursor_text="Line: 4, Column: 2"),
                StatusSnapshot(
                    message="Ready",
                    cursor_text="Line: 4, Column: 2",
                    visible=False,
                ),
            ],
        )
        self.assertFalse(hasattr(state.snapshot, "execution_target"))
        self.assertFalse(hasattr(state.snapshot, "kernel"))


class QtAdsStatusProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self) -> None:
        self.backend = QtAdsPeerFrameBackend()
        self.model = WorkspaceModel(self.backend)
        self.backend.bind_model(self.model)
        self.state = StatusState()
        self.projector = QtAdsStatusProjector(self.state, self.backend.manager)

    def tearDown(self) -> None:
        self.backend.close()
        self.app.processEvents()

    def add_frame(self, pane_id: str, kind: PaneKind) -> QtWidgets.QWidget:
        self.assertTrue(
            self.model.register_pane(
                PaneDescriptor(pane_id, kind, pane_id.title())
            ).applied
        )
        self.assertTrue(self.model.create_frame(pane_id, pane_id).applied)
        self.app.processEvents()
        return self.backend.frame_windows[pane_id]

    def test_existing_future_and_destroyed_frames_track_shared_status(self) -> None:
        editor = self.add_frame("editor", PaneKind.EDITOR)
        self.state.set_message("Parsed")
        self.state.set_cursor_text("Line: 8, Column: 3, Sel.: 0")
        shell = self.add_frame("shell", PaneKind.SHELL)
        tool = self.add_frame("files", PaneKind.TOOL)
        run_debug = self.add_frame("debug", PaneKind.RUN_DEBUG)

        for window in (editor, shell, tool, run_debug):
            bar = self.projector.status_bar_for(window)
            self.assertEqual(bar.message_label.text(), "Parsed")
            self.assertEqual(
                bar.cursor_label.text(), "Line: 8, Column: 3, Sel.: 0"
            )
            self.assertTrue(bar.isVisible())
            self.assertGreaterEqual(
                window.contentsMargins().bottom(), bar.sizeHint().height()
            )

        key = id(editor)
        self.assertTrue(self.model.request_close_frame("editor").applied)
        editor.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(
            None, QtCore.QEvent.Type.DeferredDelete
        )
        self.app.processEvents()
        self.assertNotIn(key, self.projector.projected_window_ids)
        self.assertEqual(self.state.snapshot.message, "Parsed")

    def test_visibility_releases_only_status_reservation_beside_menu(self) -> None:
        registry = CommandRegistry(self.model.resolve_active_context)
        registry.register(CommandDescriptor("quit", "Quit", lambda _context: None))
        menu_projector = QtAdsCommandProjector(
            registry,
            self.backend.manager,
            ("quit",),
            native_menus=False,
        )
        window = self.add_frame("editor", PaneKind.EDITOR)
        bar = self.projector.status_bar_for(window)
        menu = menu_projector.menu_bar_for(window)
        self.assertGreaterEqual(
            window.contentsMargins().top(), menu.sizeHint().height()
        )
        self.assertGreaterEqual(
            window.contentsMargins().bottom(), bar.sizeHint().height()
        )

        self.state.set_visible(False)
        self.assertFalse(bar.isVisible())
        self.assertGreaterEqual(
            window.contentsMargins().top(), menu.sizeHint().height()
        )
        self.assertEqual(window.contentsMargins().bottom(), 0)

        self.state.set_visible(True)
        self.assertTrue(bar.isVisible())
        self.assertGreaterEqual(
            window.contentsMargins().bottom(), bar.sizeHint().height()
        )

    def test_close_is_idempotent_and_later_status_is_model_only(self) -> None:
        self.add_frame("editor", PaneKind.EDITOR)

        self.projector.close()
        self.projector.close()
        self.state.set_message("after projector close")

        self.assertEqual(self.projector.projected_window_ids, frozenset())
        self.assertEqual(self.state.snapshot.message, "after projector close")

    def test_manager_deletion_unsubscribes_before_late_status(self) -> None:
        self.add_frame("editor", PaneKind.EDITOR)

        self.backend.close()
        QtCore.QCoreApplication.sendPostedEvents(
            None, QtCore.QEvent.Type.DeferredDelete
        )
        self.app.processEvents()
        self.state.set_message("after manager deletion")

        self.assertEqual(self.projector.projected_window_ids, frozenset())
        self.assertEqual(self.state.snapshot.message, "after manager deletion")
        self.backend.close = lambda: None

    def test_refresh_prunes_valid_empty_qtads_frame(self) -> None:
        editor = self.add_frame("editor", PaneKind.EDITOR)
        shell = self.add_frame("shell", PaneKind.SHELL)
        shell_key = id(shell)

        self.assertTrue(self.model.tab("shell", "editor").applied)
        self.assertTrue(isValid(shell))
        self.assertEqual(shell.dockWidgets(), [])
        self.projector.refresh()

        live_ids = {id(window) for window in self.backend.frame_windows.values()}
        self.assertEqual(live_ids, {id(editor)})
        self.assertEqual(self.projector.projected_window_ids, live_ids)
        self.assertNotIn(shell_key, self.projector.projected_window_ids)

    def test_refresh_prunes_valid_window_missing_from_manager(self) -> None:
        editor = self.add_frame("editor", PaneKind.EDITOR)
        shell = self.add_frame("shell", PaneKind.SHELL)
        shell_key = id(shell)

        with patch.object(
            self.backend.manager, "floatingWidgets", return_value=[editor]
        ):
            self.projector.refresh()

        self.assertEqual(self.projector.projected_window_ids, {id(editor)})
        self.assertNotIn(shell_key, self.projector.projected_window_ids)


if __name__ == "__main__":
    unittest.main()
