"""Minimal Qt ADS layout spike.

Run with PySide6-QtAds installed. With ``--test`` the demo builds its initial
layout, saves/restores it, and exits without requiring mouse interaction.
Without ``--test`` it stays open for manual drag, float, and re-dock testing.
"""

from __future__ import annotations

import sys

from PySide6 import QtCore, QtWidgets
import PySide6QtAds as QtAds


class LayoutDemo(QtWidgets.QMainWindow):
    def __init__(self, test_mode: bool = False) -> None:
        super().__init__()
        self.setWindowTitle("QtADS editor layout spike")
        self.resize(1200, 800)
        self.test_mode = test_mode

        self.dock_manager = QtAds.CDockManager(self)
        self._docks: dict[str, QtAds.CDockWidget] = {}

        self._add_editor("editor-left", "Editor Left", QtAds.LeftDockWidgetArea)
        self._add_editor("editor-right", "Editor Right", QtAds.RightDockWidgetArea)
        self._add_editor("editor-bottom", "Editor Bottom", QtAds.BottomDockWidgetArea)
        self._add_tool("shell", "Shell", QtAds.BottomDockWidgetArea)
        self._add_tool("file-browser", "File Browser", QtAds.LeftDockWidgetArea)

        self._add_tabbed_editor()

        if self.test_mode:
            QtCore.QTimer.singleShot(250, self._run_smoke_assertions)

    def _add_editor(self, key: str, title: str, area: object) -> None:
        editor = QtWidgets.QPlainTextEdit()
        editor.setPlainText(f"# {title}\n\nprint('hello from {title}')\n")
        dock = QtAds.CDockWidget(self.dock_manager, title)
        dock.setWidget(editor)
        self.dock_manager.addDockWidget(area, dock)
        self._docks[key] = dock

    def _add_tool(self, key: str, title: str, area: object) -> None:
        tool = QtWidgets.QPlainTextEdit()
        tool.setPlainText(f"{title} output\n")
        dock = QtAds.CDockWidget(self.dock_manager, title)
        dock.setWidget(tool)
        self.dock_manager.addDockWidget(area, dock)
        self._docks[key] = dock

    def _add_tabbed_editor(self) -> None:
        editor = QtWidgets.QPlainTextEdit()
        editor.setPlainText("# Tabbed editor\n")
        dock = QtAds.CDockWidget(self.dock_manager, "Editor Tab")
        dock.setWidget(editor)
        self.dock_manager.addDockWidgetTab(QtAds.CenterDockWidgetArea, dock)
        self._docks["editor-tab"] = dock

    def _run_smoke_assertions(self) -> None:
        assert len(self.dock_manager.dockWidgets()) == 6
        assert self.dock_manager.visibleDockAreaCount() >= 2
        floating_dock = self._docks["editor-bottom"]
        floating_dock.setFloating()
        assert floating_dock.isFloating()
        self.dock_manager.addDockWidget(
            QtAds.RightDockWidgetArea,
            floating_dock,
            self._docks["editor-left"].dockAreaWidget(),
        )
        assert not floating_dock.isFloating()
        state = self.dock_manager.saveState()
        assert state
        assert self.dock_manager.restoreState(state)
        print("QtADS layout smoke test passed")
        print(f"dock_widgets={len(self.dock_manager.dockWidgets())}")
        print(f"dock_areas={self.dock_manager.visibleDockAreaCount()}")
        QtWidgets.QApplication.quit()


def main() -> int:
    test_mode = "--test" in sys.argv
    app = QtWidgets.QApplication(sys.argv)
    window = LayoutDemo(test_mode=test_mode)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
