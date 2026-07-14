"""Stock-QtADS projection of the application-owned peer-frame topology."""

from __future__ import annotations

from copy import deepcopy
from typing import Callable, Mapping

from PySide6 import QtCore, QtWidgets
import PySide6QtAds as QtAds

from .contract import Capability, Direction


PaneWidgetFactory = Callable[[str], QtWidgets.QWidget]


class QtAdsPeerFrameBackend:
    """Render every application frame as the same QtADS floating-container type.

    QtADS still requires one ``CDockManager``.  This adapter keeps that manager
    hidden and empty, using it only as the library registry and coordinator.
    Every application-visible frame is a ``CFloatingDockContainer``.
    """

    capabilities = frozenset(Capability)

    def __init__(self, pane_factory: PaneWidgetFactory | None = None):
        self.manager = QtAds.CDockManager()
        self.manager.hide()
        self._pane_factory = pane_factory or self._default_pane_factory
        self.docks: dict[str, QtAds.CDockWidget] = {}
        self.frame_windows: dict[str, QtAds.CFloatingDockContainer] = {}
        self._snapshot: dict[str, object] | None = None
        self._next_origin = QtCore.QPoint(80, 80)

    @property
    def current(self) -> dict[str, object] | None:
        return deepcopy(self._snapshot)

    def render(self, snapshot: Mapping[str, object]) -> None:
        desired = deepcopy(dict(snapshot))
        frames = desired.get("frames", [])
        if not isinstance(frames, list):
            raise ValueError("frames must be a list")

        desired_panes = {
            pane_id
            for frame in frames
            for group in frame["groups"]
            for pane_id in group["panes"]
        }
        for pane_id in desired_panes:
            self._ensure_dock(pane_id)

        for frame in frames:
            self._ensure_frame(frame)
        for frame in frames:
            self._realize_frame(frame)

        desired_frame_ids = {frame["id"] for frame in frames}
        for frame_id in set(self.frame_windows).difference(desired_frame_ids):
            window = self.frame_windows.pop(frame_id)
            if not window.dockWidgets():
                window.hide()

        for pane_id in set(self.docks).difference(desired_panes):
            dock = self.docks.pop(pane_id)
            self.manager.removeDockWidget(dock)
            dock.hide()
            dock.deleteLater()

        self._snapshot = desired

    def close(self) -> None:
        for window in tuple(self.frame_windows.values()):
            window.hide()
            window.deleteLater()
        self.frame_windows.clear()
        self.manager.hide()
        self.manager.deleteLater()

    def container_for_frame(self, frame_id: str) -> QtAds.CDockContainerWidget:
        return self.frame_windows[frame_id].dockContainer()

    def _ensure_dock(self, pane_id: str) -> QtAds.CDockWidget:
        dock = self.docks.get(pane_id)
        if dock is not None:
            return dock
        dock = QtAds.CDockWidget(self.manager, pane_id)
        dock.setObjectName(f"peer-pane:{pane_id}")
        dock.setWidget(self._pane_factory(pane_id))
        self.docks[pane_id] = dock
        return dock

    def _ensure_frame(self, frame: Mapping[str, object]) -> None:
        frame_id = frame["id"]
        if frame_id in self.frame_windows:
            return
        first_pane = self._first_pane(frame)
        dock = self.docks[first_pane]
        window = self.manager.addDockWidgetFloating(dock)
        window.setObjectName(f"peer-frame:{frame_id}")
        window.setWindowTitle(str(frame_id))
        window.resize(640, 420)
        window.move(self._next_origin)
        self._next_origin += QtCore.QPoint(36, 36)
        window.show()
        self.frame_windows[str(frame_id)] = window

    def _realize_frame(self, frame: Mapping[str, object]) -> None:
        frame_id = str(frame["id"])
        container = self.container_for_frame(frame_id)
        groups = {group["id"]: group for group in frame["groups"]}
        root = frame["root"]

        first_group_id = self._first_group_id(root)
        first_group = groups[first_group_id]
        first_dock = self.docks[first_group["panes"][0]]
        if first_dock.dockAreaWidget().dockContainer() is not container:
            self.manager.addDockWidgetToContainer(
                QtAds.CenterDockWidgetArea, first_dock, container
            )

        self._realize_node(root, groups, container, is_root=True)
        for group in groups.values():
            anchor = self.docks[group["panes"][0]]
            area = anchor.dockAreaWidget()
            for pane_id in group["panes"][1:]:
                dock = self.docks[pane_id]
                if dock.dockAreaWidget() is not area:
                    self.manager.addDockWidgetTabToArea(dock, area)
            active = self.docks[group["active_pane_id"]]
            area.setCurrentDockWidget(active)

    def _realize_node(
        self,
        node: Mapping[str, object],
        groups: Mapping[str, Mapping[str, object]],
        container: QtAds.CDockContainerWidget,
        *,
        is_root: bool,
    ) -> None:
        if node["type"] == "group":
            return
        children = node["children"]
        self._realize_node(children[0], groups, container, is_root=False)
        reference_group_id = self._first_group_id(children[0])
        reference_area = self.docks[
            groups[reference_group_id]["panes"][0]
        ].dockAreaWidget()
        orientation = node["orientation"]
        area = (
            QtAds.RightDockWidgetArea
            if orientation == "horizontal"
            else QtAds.BottomDockWidgetArea
        )
        for child in children[1:]:
            child_group_id = self._first_group_id(child)
            child_dock = self.docks[groups[child_group_id]["panes"][0]]
            child_area = child_dock.dockAreaWidget()
            child_container = child_area.dockContainer() if child_area else None
            if child_container is not container:
                target_area = None if is_root else reference_area
                container.addDockWidget(area, child_dock, target_area)
            self._realize_node(child, groups, container, is_root=False)

    @staticmethod
    def _first_group_id(node: Mapping[str, object]) -> str:
        while node["type"] == "split":
            node = node["children"][0]
        return str(node["group_id"])

    @classmethod
    def _first_pane(cls, frame: Mapping[str, object]) -> str:
        group_id = cls._first_group_id(frame["root"])
        groups = {group["id"]: group for group in frame["groups"]}
        return str(groups[group_id]["panes"][0])

    @staticmethod
    def _default_pane_factory(pane_id: str) -> QtWidgets.QWidget:
        editor = QtWidgets.QPlainTextEdit()
        editor.setPlainText(f"Peer pane: {pane_id}\n")
        return editor
