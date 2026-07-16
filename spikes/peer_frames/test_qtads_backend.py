from __future__ import annotations

import unittest

from PySide6 import QtWidgets
import PySide6QtAds as QtAds
from shiboken6 import isValid

from spikes.peer_frames.contract import (
    Capability,
    CloseDecision,
    CloseReason,
    CloseVote,
    Direction,
    OperationStatus,
    PaneDescriptor,
    PaneKind,
    TabSide,
    WorkspaceModel,
)
from spikes.peer_frames.qtads_backend import QtAdsPeerFrameBackend


class FrameRecordingPolicy:
    def __init__(self, decision=CloseDecision.ALLOW):
        self.decision = decision
        self.prepared = []
        self.validated = []
        self.closed = []

    def prepare_close(self, pane, request):
        self.prepared.append((pane.id, request.reason))
        return CloseVote(pane.id, self.decision)

    def validate_close(self, pane, request):
        self.validated.append((pane.id, request.reason))
        return CloseVote(pane.id, CloseDecision.ALLOW)

    def did_close(self, pane, request):
        self.closed.append((pane.id, request.reason))


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

    def test_application_constructed_dock_can_be_registered_before_placement(self) -> None:
        dock = QtAds.CDockWidget(self.backend.manager, "Real application pane")
        dock.setWidget(QtWidgets.QPlainTextEdit("application-owned widget"))
        self.backend.register_dock("application-pane", dock)
        self.model.register_pane(
            PaneDescriptor("application-pane", PaneKind.CUSTOM, "Application pane")
        )

        self.assertTrue(
            self.model.create_frame("application-pane", "application-frame").applied
        )
        self.app.processEvents()

        self.assertIs(self.backend.docks["application-pane"], dock)
        self.assertIsNot(dock.dockAreaWidget().dockContainer(), self.backend.manager)
        self.assertEqual(self.backend.manager.dockAreaCount(), 0)

    def test_focused_dock_updates_context_without_rebuilding_frames(self) -> None:
        self.register("editor", PaneKind.EDITOR)
        self.register("shell", PaneKind.SHELL)
        self.model.create_frame("editor", "editor")
        self.model.create_frame("shell", "shell")
        windows = dict(self.backend.frame_windows)
        snapshot = self.backend.current

        self.backend._focused_dock_widget_changed(self.backend.docks["editor"])

        self.assertEqual(self.model.resolve_active_context().pane.id, "editor")
        self.assertEqual(self.backend.frame_windows, windows)
        self.assertEqual(self.backend.current, snapshot)

        self.backend._focused_dock_widget_changed(None)
        self.assertEqual(self.model.resolve_active_context().pane.id, "editor")

    def test_stock_backend_reports_group_tab_side_rendering_as_unsupported(self) -> None:
        if Capability.TAB_SIDE in self.backend.capabilities:
            self.skipTest("fork implements all four tab sides")
        self.register("editor", PaneKind.EDITOR)
        self.model.create_frame("editor", "editor")
        group_id = self.model.serialize_layout()["frames"][0]["groups"][0]["id"]
        before = self.model.serialize_layout()

        result = self.model.set_group_tab_side(group_id, TabSide.LEFT)

        self.assertEqual(result.status, OperationStatus.UNSUPPORTED)
        self.assertEqual(self.model.serialize_layout(), before)

    def test_native_fork_renders_independent_top_and_bottom_group_tabs(self) -> None:
        if not hasattr(QtAds.CDockAreaWidget, "setTabPosition"):
            self.skipTest("requires the per-area tab-position QtADS slice")
        self.register("editor", PaneKind.EDITOR)
        self.register("shell", PaneKind.SHELL)

        self.model.create_frame("editor", "editor")
        self.model.create_frame("shell", "shell")
        editor_area = self.backend.docks["editor"].dockAreaWidget()
        shell_area = self.backend.docks["shell"].dockAreaWidget()

        self.assertEqual(
            QtAds.CDockAreaWidget.TabPositionTop, editor_area.tabPosition()
        )
        self.assertEqual(
            QtAds.CDockAreaWidget.TabPositionBottom, shell_area.tabPosition()
        )
        self.assertIs(
            editor_area.titleBar(), editor_area.titleBar().tabBar().parentWidget()
        )
        self.assertEqual(
            "bottomTabBarWidget",
            shell_area.titleBar().tabBar().parentWidget().objectName(),
        )
        self.assertIs(
            shell_area.titleBar().tabBar().parentWidget(),
            shell_area.findChild(QtWidgets.QWidget, "tabsMenuButton").parentWidget(),
        )

    def test_native_fork_applies_all_four_group_tab_side_commands(self) -> None:
        if Capability.TAB_SIDE not in self.backend.capabilities:
            self.skipTest("requires the four-side QtADS slice")

        expected = {
            TabSide.TOP: QtAds.CDockAreaWidget.TabPositionTop,
            TabSide.BOTTOM: QtAds.CDockAreaWidget.TabPositionBottom,
            TabSide.LEFT: QtAds.CDockAreaWidget.TabPositionLeft,
            TabSide.RIGHT: QtAds.CDockAreaWidget.TabPositionRight,
        }
        for index, side in enumerate(expected):
            pane_id = f"pane-{index}"
            self.register(pane_id)
            self.model.create_frame(pane_id, pane_id)
            frame = next(
                frame
                for frame in self.model.serialize_layout()["frames"]
                if frame["id"] == pane_id
            )
            group_id = frame["groups"][0]["id"]

            result = self.model.set_group_tab_side(group_id, side)

            self.assertTrue(result.applied)
            self.assertEqual(
                expected[side],
                self.backend.docks[pane_id].dockAreaWidget().tabPosition(),
            )

    def test_native_group_context_menu_switches_and_checks_tab_side(self) -> None:
        if Capability.TAB_SIDE not in self.backend.capabilities:
            self.skipTest("requires the four-side QtADS slice")
        self.register("editor", PaneKind.EDITOR)
        self.model.create_frame("editor", "editor")
        area = self.backend.docks["editor"].dockAreaWidget()
        menu = QtWidgets.QMenu()

        submenu = self.backend.append_tab_side_menu(area, menu)

        self.assertIsNotNone(submenu)
        actions = {action.data(): action for action in submenu.actions()}
        self.assertEqual(set(actions), {side.value for side in TabSide})
        self.assertTrue(actions[TabSide.TOP.value].isChecked())
        self.assertTrue(area.titleBar().property("peer-tab-side-menu"))
        self.assertTrue(
            self.backend.docks["editor"]
            .tabWidget()
            .property("peer-tab-side-menu")
        )

        actions[TabSide.RIGHT.value].trigger()

        group = self.model.serialize_layout()["frames"][0]["groups"][0]
        self.assertEqual(TabSide.RIGHT.value, group["tab_side"])
        self.assertEqual(
            QtAds.CDockAreaWidget.TabPositionRight, area.tabPosition()
        )
        self.assertTrue(actions[TabSide.RIGHT.value].isChecked())

    def test_direct_split_inherits_source_group_tab_side_metadata(self) -> None:
        self.register("editor", PaneKind.EDITOR)
        self.register("shell", PaneKind.SHELL)
        self.model.create_frame("editor", "editor")
        self.model.create_frame("shell", "shell")
        target = self.backend.container_for_frame("editor")

        target.addDockWidget(
            QtAds.RightDockWidgetArea,
            self.backend.docks["shell"],
            self.backend.docks["editor"].dockAreaWidget(),
        )
        self.app.processEvents()

        groups = self.model.serialize_layout()["frames"][0]["groups"]
        sides = {
            pane_id: group["tab_side"]
            for group in groups
            for pane_id in group["panes"]
        }
        self.assertEqual(sides["editor"], TabSide.TOP.value)
        self.assertEqual(sides["shell"], TabSide.BOTTOM.value)
        if Capability.TAB_SIDE in self.backend.capabilities:
            self.assertEqual(
                QtAds.CDockAreaWidget.TabPositionBottom,
                self.backend.docks["shell"].dockAreaWidget().tabPosition(),
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

    def test_native_close_uses_same_path_for_first_later_and_final_frame(self) -> None:
        requests = []
        self.backend.bind_model(
            self.model,
            lambda frame_id: requests.append(frame_id)
            or self.model.request_close_frame(frame_id),
        )
        policies = {}
        for pane_id in ("first", "later", "final"):
            policy = FrameRecordingPolicy()
            policies[pane_id] = policy
            self.assertTrue(
                self.model.register_pane(
                    PaneDescriptor(pane_id, PaneKind.CUSTOM, pane_id), policy
                ).applied
            )
            self.assertTrue(self.model.create_frame(pane_id, pane_id).applied)
        self.app.processEvents()

        for frame_id in ("first", "later", "final"):
            window = self.backend.frame_windows[frame_id]
            self.assertFalse(window.close())
            self.app.processEvents()
            self.assertNotIn(frame_id, self.model.frames)
            self.assertTrue(not isValid(window) or not window.isVisible())
            self.assertFalse(self.model.shutdown_requested)
            self.assertEqual(
                policies[frame_id].prepared,
                [(frame_id, CloseReason.FRAME)],
            )
            self.assertEqual(
                policies[frame_id].validated,
                [(frame_id, CloseReason.FRAME)],
            )
            self.assertEqual(
                policies[frame_id].closed,
                [(frame_id, CloseReason.FRAME)],
            )

        self.assertEqual(requests, ["first", "later", "final"])
        self.assertEqual(self.model.frames, {})
        self.assertFalse(self.model.shutdown_requested)

    def test_cancelled_native_frame_close_keeps_window_and_topology(self) -> None:
        policy = FrameRecordingPolicy(CloseDecision.CONFIRM)
        self.model.register_pane(
            PaneDescriptor("frame", PaneKind.CUSTOM, "frame"), policy
        )
        self.model.create_frame("frame", "frame")
        self.backend.bind_model(
            self.model,
            lambda frame_id: self.model.request_close_frame(
                frame_id, lambda _votes: False
            ),
        )
        window = self.backend.frame_windows["frame"]
        before = self.model.serialize_layout()

        self.assertFalse(window.close())
        self.app.processEvents()

        self.assertEqual(
            self.backend.last_frame_close_result.status,
            OperationStatus.CANCELLED,
        )
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertTrue(window.isVisible())
        self.assertEqual(policy.closed, [])
        self.assertFalse(self.model.shutdown_requested)

    def test_structural_empty_source_close_does_not_request_frame_close(self) -> None:
        requests = []
        self.backend.bind_model(
            self.model,
            lambda frame_id: requests.append(frame_id)
            or self.model.request_close_frame(frame_id),
        )
        self.register("target")
        self.register("source")
        self.model.create_frame("target", "target")
        self.model.create_frame("source", "source")
        source_window = self.backend.frame_windows["source"]
        target_container = self.backend.container_for_frame("target")

        target_container.addDockWidget(
            QtAds.CenterDockWidgetArea,
            self.backend.docks["source"],
        )
        self.app.processEvents()

        self.assertEqual(requests, [])
        self.assertNotIn("source", self.model.frames)
        self.assertIn("source", self.model.panes)
        self.assertFalse(source_window.isVisible())

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
