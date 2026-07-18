"""Application workspace-session snapshots and transactional restoration."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Mapping


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
