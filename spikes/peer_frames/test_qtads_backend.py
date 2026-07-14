from __future__ import annotations

import unittest

from PySide6 import QtWidgets
import PySide6QtAds as QtAds

from spikes.peer_frames.contract import Direction, PaneDescriptor, PaneKind, WorkspaceModel
from spikes.peer_frames.qtads_backend import QtAdsPeerFrameBackend


class QtAdsPeerFrameBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self) -> None:
        self.backend = QtAdsPeerFrameBackend()
        self.model = WorkspaceModel(self.backend)

    def tearDown(self) -> None:
        self.backend.close()
        self.app.processEvents()

    def register(self, pane_id: str, kind: PaneKind = PaneKind.CUSTOM) -> None:
        self.assertTrue(
            self.model.register_pane(PaneDescriptor(pane_id, kind, pane_id)).applied
        )

    def test_hidden_manager_is_not_an_application_frame(self) -> None:
        for pane_id, kind in (
            ("editor", PaneKind.EDITOR),
            ("shell", PaneKind.SHELL),
            ("files", PaneKind.TOOL),
            ("debug", PaneKind.RUN_DEBUG),
        ):
            self.register(pane_id, kind)
            self.assertTrue(self.model.create_frame(pane_id, pane_id).applied)
        self.app.processEvents()

        self.assertTrue(self.backend.manager.isHidden())
        self.assertEqual(self.backend.manager.dockAreaCount(), 0)
        self.assertEqual(set(self.backend.frame_windows), set(self.model.frames))
        self.assertTrue(
            all(
                isinstance(window, QtAds.CFloatingDockContainer)
                for window in self.backend.frame_windows.values()
            )
        )
        self.assertTrue(
            all(
                self.backend.container_for_frame(frame_id) is not self.backend.manager
                for frame_id in self.backend.frame_windows
            )
        )

    def test_contract_layout_operations_stay_in_peer_containers(self) -> None:
        for pane_id in ("one", "two", "three", "four"):
            self.register(pane_id)
            self.model.create_frame(pane_id, pane_id)

        self.assertTrue(self.model.tab("two", "one").applied)
        self.assertTrue(self.model.split("three", "one", Direction.RIGHT).applied)
        self.assertTrue(
            self.model.split("four", "three", Direction.BELOW, outer=True).applied
        )
        self.app.processEvents()

        self.assertEqual(set(self.backend.frame_windows), {"one"})
        container = self.backend.container_for_frame("one")
        self.assertEqual(container.visibleDockAreaCount(), 3)
        self.assertIs(
            self.backend.docks["one"].dockAreaWidget(),
            self.backend.docks["two"].dockAreaWidget(),
        )
        self.assertTrue(
            all(
                dock.dockAreaWidget().dockContainer() is container
                for dock in self.backend.docks.values()
            )
        )

    def test_floating_and_closing_first_created_frame_are_not_special(self) -> None:
        for pane_id in ("one", "two"):
            self.register(pane_id)
            self.model.create_frame(pane_id, pane_id)
        self.model.tab("two", "one")
        self.assertTrue(self.model.float("two", "floated").applied)
        self.app.processEvents()

        self.assertEqual(set(self.backend.frame_windows), {"one", "floated"})
        first_window = self.backend.frame_windows["one"]
        self.assertTrue(self.model.request_close_frame("one").applied)
        self.app.processEvents()
        self.assertFalse(self.model.shutdown_requested)
        self.assertEqual(set(self.backend.frame_windows), {"floated"})
        self.assertFalse(first_window.isVisible())
        self.assertIsNot(
            self.backend.container_for_frame("floated"), self.backend.manager
        )

    def test_application_layout_restores_as_peer_floating_frames(self) -> None:
        for pane_id in ("one", "two", "three"):
            self.register(pane_id)
            self.model.create_frame(pane_id, pane_id)
        self.model.tab("two", "one")
        self.model.split("three", "one", Direction.RIGHT)
        saved = self.model.serialize_layout()

        restored_backend = QtAdsPeerFrameBackend()
        restored = WorkspaceModel(restored_backend)
        try:
            for pane_id in ("one", "two", "three"):
                restored.register_pane(
                    PaneDescriptor(pane_id, PaneKind.CUSTOM, pane_id)
                )
            self.assertTrue(restored.restore_layout(saved).applied)
            self.app.processEvents()

            self.assertEqual(restored.serialize_layout(), saved)
            self.assertTrue(restored_backend.manager.isHidden())
            self.assertEqual(restored_backend.manager.dockAreaCount(), 0)
            self.assertEqual(set(restored_backend.frame_windows), {"one"})
            self.assertEqual(
                restored_backend.container_for_frame("one").visibleDockAreaCount(), 2
            )
        finally:
            restored_backend.close()


if __name__ == "__main__":
    unittest.main()
