"""Application workspace-session snapshots and transactional restoration."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Mapping


def retained_pane_layout(layout, pane_ids, *, current_layout=None):
    """Keep captured placement for surviving panes with fresh native IDs."""
    result = deepcopy(layout)
    frames = []
    for frame in result["frames"]:
        groups = []
        for group in frame["groups"]:
            panes = [pane_ids[pane] for pane in group["panes"] if pane in pane_ids]
            if panes:
                groups.append(
                    {
                        **group,
                        "panes": panes,
                        "active_pane_id": pane_ids.get(
                            group["active_pane_id"], panes[0]
                        ),
                    }
                )
        kept = {group["id"] for group in groups}

        def prune(node):
            if node["type"] == "group":
                return node if node["group_id"] in kept else None
            children = [
                child
                for child in (prune(child) for child in node["children"])
                if child is not None
            ]
            if not children:
                return None
            if len(children) == 1:
                return children[0]
            return {**node, "children": children}

        root = prune(frame["root"])
        if root is not None:
            frames.append({**frame, "root": root, "groups": groups})
    result["frames"] = frames
    result["active_pane_id"] = pane_ids.get(layout.get("active_pane_id"))
    if current_layout is not None:
        # Fresh runtime panes (e.g. the default interpreter) are not retained
        # resources. Keep their current placement without reviving old shells.
        fresh = {
            pane: pane
            for frame in current_layout["frames"]
            for group in frame["groups"]
            for pane in group["panes"]
            if pane not in pane_ids.values()
        }
        extra = retained_pane_layout(current_layout, fresh)
        frame_ids = {frame["id"] for frame in frames}
        group_ids = {group["id"] for frame in frames for group in frame["groups"]}

        def reserve(identity, used):
            candidate, suffix = identity, 0
            while candidate in used:
                suffix += 1
                candidate = f"{identity}-fresh-{suffix}"
            used.add(candidate)
            return candidate

        for frame in extra["frames"]:
            frame["id"] = reserve(frame["id"], frame_ids)
            renamed = {
                group["id"]: reserve(group["id"], group_ids)
                for group in frame["groups"]
            }
            for group in frame["groups"]:
                group["id"] = renamed[group["id"]]

            def rename_node(node):
                if node["type"] == "group":
                    node["group_id"] = renamed[node["group_id"]]
                else:
                    for child in node["children"]:
                        rename_node(child)

            rename_node(frame["root"])
            frames.append(frame)
    return result


@dataclass(frozen=True)
class SessionRestoreResult:
    applied: bool
    detail: str = ""


class WorkspaceSessionService:
    """Persist complete peer topology without window-manager state blobs."""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        workspace,
        frame_windows: Callable[[], Mapping[str, object]],
        loaded_tools: Callable[[], object],
        restore_tools: Callable[[object], None],
    ):
        self._workspace = workspace
        self._frameWindows = frame_windows
        self._loadedTools = loaded_tools
        self._restoreTools = restore_tools

    def capture(self) -> dict[str, object]:
        return {
            "schema": self.SCHEMA_VERSION,
            "layout": deepcopy(self._workspace.serialize_layout()),
            "frame_geometries": {
                frame_id: self._geometry(window)
                for frame_id, window in self._frameWindows().items()
            },
            "loaded_tools": list(self._loadedTools()),
        }

    def restore(self, snapshot: object) -> SessionRestoreResult:
        try:
            layout, geometries, tools = self._validate(snapshot)
        except (KeyError, TypeError, ValueError) as error:
            return SessionRestoreResult(False, f"invalid workspace session: {error}")

        before = self.capture()
        try:
            self._restoreTools(tools)
            result = self._workspace.restore_layout(layout)
            if not result.applied:
                raise ValueError(result.detail)
            self._apply_geometries(geometries)
        except Exception as error:
            self._rollback(before)
            return SessionRestoreResult(
                False, f"workspace session restore failed: {error}"
            )
        return SessionRestoreResult(True)

    def _rollback(self, snapshot: Mapping[str, object]) -> None:
        try:
            self._restoreTools(snapshot["loaded_tools"])
            self._workspace.restore_layout(snapshot["layout"])
            self._apply_geometries(snapshot["frame_geometries"])
        except Exception:
            pass

    def _validate(self, snapshot):
        if not isinstance(snapshot, Mapping):
            raise TypeError("snapshot must be an object")
        if snapshot["schema"] != self.SCHEMA_VERSION:
            raise ValueError("unsupported schema")
        layout = snapshot["layout"]
        geometries = snapshot["frame_geometries"]
        tools = snapshot["loaded_tools"]
        if not isinstance(layout, Mapping):
            raise TypeError("layout must be an object")
        if not isinstance(geometries, Mapping):
            raise TypeError("frame geometries must be an object")
        if not isinstance(tools, list) or not all(
            isinstance(tool, str) for tool in tools
        ):
            raise TypeError("loaded tools must be a list of strings")
        frame_ids = {
            frame["id"]
            for frame in layout.get("frames", ())
            if isinstance(frame, Mapping) and isinstance(frame.get("id"), str)
        }
        if set(geometries).difference(frame_ids):
            raise ValueError("geometry refers to an unknown frame")
        normalized = {}
        for frame_id, geometry in geometries.items():
            if (
                not isinstance(frame_id, str)
                or not isinstance(geometry, (list, tuple))
                or len(geometry) != 4
                or not all(isinstance(value, int) for value in geometry)
                or geometry[2] <= 0
                or geometry[3] <= 0
            ):
                raise ValueError("invalid frame geometry")
            normalized[frame_id] = list(geometry)
        return deepcopy(layout), normalized, list(tools)

    def _apply_geometries(self, geometries: Mapping[str, object]) -> None:
        windows = self._frameWindows()
        for frame_id, geometry in geometries.items():
            window = windows.get(frame_id)
            if window is not None:
                window.setGeometry(*geometry)

    @staticmethod
    def _geometry(window) -> list[int]:
        geometry = window.geometry()
        return [geometry.x(), geometry.y(), geometry.width(), geometry.height()]
