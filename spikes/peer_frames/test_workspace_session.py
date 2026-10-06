from __future__ import annotations

import unittest

from spikes.peer_frames.contract import OperationResult, OperationStatus
from spikes.peer_frames.workspace_session import (
    WorkspaceSessionService,
    retained_pane_layout,
)
from spikes.peer_frames.contract import PaneDescriptor, PaneKind, WorkspaceModel
from spikes.peer_frames.fake_backend import FakeBackend
from copy import deepcopy


class Geometry:
    def __init__(self, values):
        self.values = values

    def x(self):
        return self.values[0]

    def y(self):
        return self.values[1]

    def width(self):
        return self.values[2]

    def height(self):
        return self.values[3]


class Window:
    def __init__(self, geometry):
        self.values = list(geometry)

    def geometry(self):
        return Geometry(self.values)

    def setGeometry(self, *geometry):
        self.values = list(geometry)


class Workspace:
    def __init__(self, layout):
        self.layout = layout

    def serialize_layout(self):
        return self.layout

    def restore_layout(self, layout):
        if layout.get("schema") != 2:
            return OperationResult(OperationStatus.INVALID, "unsupported layout")
        self.layout = layout
        return OperationResult(OperationStatus.APPLIED)


class WorkspaceSessionTests(unittest.TestCase):
    def test_retained_placement_prunes_absent_groups_frames_and_splits(self):
        def group(identity, panes):
            return {
                "id": identity,
                "panes": panes,
                "active_pane_id": panes[-1],
                "tab_side": "top",
            }

        def leaf(identity):
            return {"type": "group", "group_id": identity}

        saved = {
            "schema": WorkspaceModel.SCHEMA_VERSION,
            "active_pane_id": "shell",
            "frames": [
                {
                    "id": "primary",
                    "groups": [
                        group("editors", ["a", "b"]),
                        group("shells", ["shell"]),
                    ],
                    "root": {
                        "type": "split",
                        "orientation": "horizontal",
                        "children": [leaf("editors"), leaf("shells")],
                    },
                },
                {
                    "id": "floating",
                    "groups": [group("other", ["c"])],
                    "root": leaf("other"),
                },
            ],
        }
        before = deepcopy(saved)
        for keys, expected_frames, expected_groups in (
            (("a", "b", "shell", "c"), 2, 3),
            (("a", "b", "c"), 2, 2),
            (("b",), 1, 1),
            (("shell",), 1, 1),
            (("c",), 1, 1),
            ((), 0, 0),
        ):
            with self.subTest(retained=keys):
                mapping = {key: "fresh-" + key for key in keys}
                layout = retained_pane_layout(saved, mapping)
                model = WorkspaceModel(FakeBackend())
                for pane_id in mapping.values():
                    self.assertTrue(
                        model.register_pane(
                            PaneDescriptor(pane_id, PaneKind.EDITOR, pane_id)
                        ).applied
                    )
                self.assertTrue(model.restore_layout(layout).applied)
                self.assertEqual(len(layout["frames"]), expected_frames)
                self.assertEqual(
                    sum(len(frame["groups"]) for frame in layout["frames"]),
                    expected_groups,
                )
                self.assertEqual(
                    {
                        pane
                        for frame in layout["frames"]
                        for group in frame["groups"]
                        for pane in group["panes"]
                    },
                    set(mapping.values()),
                )
                self.assertEqual(layout["active_pane_id"], mapping.get("shell"))
                if keys == ("b",):
                    self.assertEqual(layout["frames"][0]["root"], leaf("editors"))
                    self.assertEqual(
                        layout["frames"][0]["groups"][0]["active_pane_id"], "fresh-b"
                    )
                self.assertEqual(saved, before)

    def make_service(self):
        layout = {
            "schema": 2,
            "active_pane_id": "editor",
            "frames": [{"id": "frame", "root": {}, "groups": []}],
        }
        workspace = Workspace(layout)
        windows = {"frame": Window((10, 20, 640, 480))}
        tools = ["files"]

        def restore_tools(value):
            tools[:] = value

        service = WorkspaceSessionService(
            workspace,
            lambda: windows,
            lambda: tools,
            restore_tools,
        )
        return service, workspace, windows, tools

    def test_complete_session_round_trip_restores_layout_geometry_and_tools(self):
        service, _workspace, _windows, _tools = self.make_service()
        saved = service.capture()
        workspace = Workspace({"schema": 2, "active_pane_id": None, "frames": []})
        windows = {"frame": Window((1, 2, 300, 200))}
        tools = ["outline"]

        def restore_tools(value):
            tools[:] = value

        restarted_service = WorkspaceSessionService(
            workspace,
            lambda: windows,
            lambda: tools,
            restore_tools,
        )

        result = restarted_service.restore(saved)

        self.assertTrue(result.applied, result.detail)
        self.assertEqual(workspace.layout, saved["layout"])
        self.assertEqual(windows["frame"].values, [10, 20, 640, 480])
        self.assertEqual(tools, ["files"])

    def test_invalid_snapshot_is_rejected_without_mutation(self):
        service, workspace, windows, tools = self.make_service()
        before = service.capture()
        invalid = dict(before)
        invalid["layout"] = {"schema": 999, "frames": []}

        result = service.restore(invalid)

        self.assertFalse(result.applied)
        self.assertEqual(service.capture(), before)
        self.assertEqual(tools, ["files"])


if __name__ == "__main__":
    unittest.main()
