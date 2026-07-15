"""Interactive stock-QtADS peer-frame and reverse-synchronization demo."""

from __future__ import annotations

import json
import sys

from PySide6 import QtCore, QtWidgets

from spikes.peer_frames.contract import (
    Capability,
    PaneDescriptor,
    PaneKind,
    TabSide,
    WorkspaceModel,
)
from spikes.peer_frames.qtads_backend import QtAdsPeerFrameBackend


PANE_SPECS = (
    ("editor-one", PaneKind.EDITOR, "Editor One"),
    ("editor-two", PaneKind.EDITOR, "Editor Two"),
    ("shell", PaneKind.SHELL, "Shell"),
    ("files", PaneKind.TOOL, "File Browser"),
    ("debug", PaneKind.RUN_DEBUG, "Run / Debug"),
)


def pane_factory(pane_id: str) -> QtWidgets.QWidget:
    editor = QtWidgets.QPlainTextEdit()
    editor.setReadOnly(True)
    editor.setPlainText(
        f"{pane_id}\n\n"
        "Drag this tab or its frame. After each settled drop, QtADS topology "
        "is captured into the application-owned peer-frame model.\n\n"
        "There is no visible main window."
    )
    return editor


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Peer-frame QtADS adapter spike")
    app.setQuitOnLastWindowClosed(False)
    backend = QtAdsPeerFrameBackend(pane_factory)
    model = WorkspaceModel(backend)
    backend.bind_model(model)

    for pane_id, kind, title in PANE_SPECS:
        model.register_pane(PaneDescriptor(pane_id, kind, title))
        model.create_frame(pane_id, f"workspace-{pane_id}")

    model.tab("editor-two", "editor-one")
    if Capability.TAB_SIDE in backend.capabilities:
        requested_sides = {
            "editor-one": TabSide.LEFT,
            "shell": TabSide.RIGHT,
            "files": TabSide.BOTTOM,
            "debug": TabSide.TOP,
        }
        for pane_id, side in requested_sides.items():
            frame = next(
                frame
                for frame in model.serialize_layout()["frames"]
                if any(
                    pane_id in group["panes"] for group in frame["groups"]
                )
            )
            group = next(
                group for group in frame["groups"] if pane_id in group["panes"]
            )
            model.set_group_tab_side(group["id"], side)
    for index, window in enumerate(backend.frame_windows.values()):
        window.move(90 + index * 150, 90 + index * 95)
        window.resize(620, 410)

    previous_count = -1

    def report_adoption() -> None:
        nonlocal previous_count
        if backend.adoption_count == previous_count:
            return
        previous_count = backend.adoption_count
        print(f"adoptions={backend.adoption_count}")
        print(json.dumps(model.serialize_layout(), indent=2))

    timer = QtCore.QTimer()
    timer.setInterval(150)
    timer.timeout.connect(report_adoption)
    timer.start()
    app.aboutToQuit.connect(backend.close)
    report_adoption()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
