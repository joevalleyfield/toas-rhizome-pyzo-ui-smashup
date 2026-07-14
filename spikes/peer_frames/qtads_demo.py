"""Interactive stock-QtADS peer-frame and reverse-synchronization demo."""

from __future__ import annotations

import json
import sys

from PySide6 import QtCore, QtWidgets

from spikes.peer_frames.contract import PaneDescriptor, PaneKind, WorkspaceModel
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
