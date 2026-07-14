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
        self.backend.bind_model(self.model)

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
        restored_backend.bind_model(restored)
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

    def test_application_render_does_not_reverse_adopt(self) -> None:
        self.register("one")
        self.register("two")
        self.model.create_frame("one", "one")
        self.model.create_frame("two", "two")
        self.model.split("two", "one", Direction.RIGHT)
        self.app.processEvents()

        self.assertEqual(self.backend.adoption_count, 0)
        self.assertEqual(self.backend.capture_layout(), self.model.serialize_layout())

    def test_direct_cross_frame_split_is_adopted_once_after_signal_burst(self) -> None:
        self.register("one")
        self.register("two")
        self.model.create_frame("one", "one")
        self.model.create_frame("two", "two")
        target = self.backend.container_for_frame("one")

        target.addDockWidget(
            QtAds.RightDockWidgetArea,
            self.backend.docks["two"],
            self.backend.docks["one"].dockAreaWidget(),
        )
        self.app.processEvents()

        self.assertEqual(self.backend.adoption_count, 1)
        self.assertTrue(self.backend.last_sync_result.applied)
        self.assertEqual(set(self.model.frames), {"one"})
        self.assertEqual(target.visibleDockAreaCount(), 2)
        self.assertEqual(self.backend.capture_layout(), self.model.serialize_layout())

    def test_direct_cross_frame_tab_is_adopted(self) -> None:
        self.register("one")
        self.register("two")
        self.model.create_frame("one", "one")
        self.model.create_frame("two", "two")
        target_area = self.backend.docks["one"].dockAreaWidget()

        self.backend.manager.addDockWidgetTabToArea(
            self.backend.docks["two"], target_area
        )
        self.app.processEvents()

        self.assertEqual(self.backend.adoption_count, 1)
        self.assertEqual(set(self.model.frames), {"one"})
        self.assertIs(
            self.backend.docks["one"].dockAreaWidget(),
            self.backend.docks["two"].dockAreaWidget(),
        )
        self.assertEqual(self.backend.capture_layout(), self.model.serialize_layout())

    def test_direct_outer_split_is_adopted_as_frame_root(self) -> None:
        for pane_id in ("one", "two", "three"):
            self.register(pane_id)
            self.model.create_frame(pane_id, pane_id)
        target = self.backend.container_for_frame("one")
        target.addDockWidget(
            QtAds.RightDockWidgetArea,
            self.backend.docks["two"],
            self.backend.docks["one"].dockAreaWidget(),
        )
        self.app.processEvents()
        before = self.backend.adoption_count

        target.addDockWidget(
            QtAds.BottomDockWidgetArea, self.backend.docks["three"], None
        )
        self.app.processEvents()

        self.assertEqual(self.backend.adoption_count, before + 1)
        root = self.model.serialize_layout()["frames"][0]["root"]
        self.assertEqual(root["orientation"], "vertical")
        self.assertEqual(len(root["children"]), 2)
        self.assertEqual(self.backend.capture_layout(), self.model.serialize_layout())

    def test_multi_area_frame_merge_preserves_target_and_group_identities(self) -> None:
        for pane_id in ("target", "source-one", "source-two"):
            self.register(pane_id)
            self.model.create_frame(pane_id, pane_id)
        self.model.split("source-two", "source-one", Direction.RIGHT)
        source_layout = next(
            frame
            for frame in self.model.serialize_layout()["frames"]
            if frame["id"] == "source-one"
        )
        source_group_ids = {group["id"] for group in source_layout["groups"]}
        source = self.backend.container_for_frame("source-one")
        target = self.backend.container_for_frame("target")
        source_areas = [source.dockArea(index) for index in range(source.dockAreaCount())]
        target_area = self.backend.docks["target"].dockAreaWidget()

        target.dropWidget(source_areas[0], QtAds.RightDockWidgetArea, target_area)
        target.dropWidget(source_areas[1], QtAds.BottomDockWidgetArea, None)
        self.app.processEvents()

        self.assertEqual(self.backend.adoption_count, 1)
        self.assertEqual(set(self.model.frames), {"target"})
        merged = self.model.serialize_layout()["frames"][0]
        self.assertTrue(
            source_group_ids.issubset({group["id"] for group in merged["groups"]})
        )
        self.assertEqual(target.visibleDockAreaCount(), 3)
        self.assertEqual(self.backend.capture_layout(), self.model.serialize_layout())

    def test_direct_float_receives_a_new_peer_frame_identity(self) -> None:
        self.register("one")
        self.register("two")
        self.model.create_frame("one", "one")
        self.model.create_frame("two", "two")
        self.model.tab("two", "one")

        self.backend.docks["two"].setFloating()
        self.app.processEvents()

        self.assertEqual(self.backend.adoption_count, 1)
        self.assertEqual(len(self.model.frames), 2)
        new_frames = set(self.model.frames).difference({"one"})
        self.assertEqual(len(new_frames), 1)
        self.assertTrue(next(iter(new_frames)).startswith("frame-user-"))
        self.assertEqual(self.backend.capture_layout(), self.model.serialize_layout())

    def test_direct_tab_activation_updates_application_context(self) -> None:
        self.register("one")
        self.register("two")
        self.model.create_frame("one", "one")
        self.model.create_frame("two", "two")
        self.model.tab("two", "one")
        area = self.backend.docks["one"].dockAreaWidget()

        area.setCurrentDockWidget(self.backend.docks["one"])
        self.app.processEvents()

        self.assertEqual(self.backend.adoption_count, 1)
        self.assertEqual(self.model.active_pane_id, "one")

    def test_root_contamination_is_rejected_and_authoritative_layout_returns(self) -> None:
        self.register("one")
        self.model.create_frame("one", "one")

        self.backend.manager.addDockWidget(
            QtAds.CenterDockWidgetArea, self.backend.docks["one"]
        )
        self.app.processEvents()

        self.assertEqual(self.backend.adoption_count, 0)
        self.assertEqual(self.backend.last_sync_result.status.value, "invalid")
        self.assertEqual(self.backend.manager.dockAreaCount(), 0)
        self.assertIs(
            self.backend.docks["one"].dockAreaWidget().dockContainer(),
            self.backend.container_for_frame("one"),
        )

    def test_physical_pane_removal_cannot_bypass_application_close(self) -> None:
        self.register("one")
        self.model.create_frame("one", "one")
        before = self.model.serialize_layout()

        self.backend.manager.removeDockWidget(self.backend.docks["one"])
        self.app.processEvents()

        self.assertEqual(self.backend.adoption_count, 0)
        self.assertEqual(self.backend.last_sync_result.status.value, "invalid")
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertIs(
            self.backend.docks["one"].dockAreaWidget().dockContainer(),
            self.backend.container_for_frame("one"),
        )


if __name__ == "__main__":
    unittest.main()
