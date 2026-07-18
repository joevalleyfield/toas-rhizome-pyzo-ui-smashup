from __future__ import annotations

import unittest

from spikes.peer_frames.contract import OperationResult, OperationStatus
from spikes.peer_frames.workspace_session import WorkspaceSessionService


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
