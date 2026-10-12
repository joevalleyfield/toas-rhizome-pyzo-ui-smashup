"""Visible Cocoa fixture setup and read-only observation; all test UI actions are native.

This intentionally does not automate drag, focus, menu, typing, closing or quit.
Use the companion launcher and the documented checklist/CUA to perform those.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time
import traceback
import types

from pyzo.util import paths

directory = Path(os.environ["PYZO_PHYSICAL_DIR"])
directory.mkdir(parents=True, exist_ok=True)
(directory / "tools").mkdir(exist_ok=True)
os.chdir(directory)
paths.prepare_appdata_appconfig_dirs = lambda: (str(directory), str(directory))
os.environ["PYZO_WORKSPACE_DIR"] = str(directory / "workspaces")
os.environ["PYZO_RECOVERY_DIR"] = str(directory / "recovery")
os.environ["PYZO_LOG"] = str(directory / "application.log")
# Never address or replace the user's command server.
commandline = types.ModuleType("pyzo.core.commandline")
commandline.is_our_server_running = lambda: False
commandline.handle_cmd_args = lambda: None
commandline.stop_our_server = lambda: None
sys.modules["pyzo.core.commandline"] = commandline
# Production Restart must exec this same isolated entry point.
sys.argv = [str(Path(__file__).resolve())]

import pyzo._start
from pyzo.core.main import MainWindow
from pyzo.core.workspaceContext import owner_for
from pyzo.qt import QtCore, QtGui, QtWidgets
from shiboken6 import isValid
from spikes.peer_frames.contract import Direction
from pyzo.core.kernelbroker import KernelInfo

# The app bundle embeds Python; live kernels use the pinned interpreter binary,
# not the GUI launcher. This is fixture configuration, not a production fallback.
if not pyzo.config.shellConfigs2:
    info = KernelInfo()
    info.exe = os.environ.get("PYZO_PHYSICAL_PYTHON", sys.executable)
    pyzo.config.shellConfigs2.append(info)

window = None
sequence = 0
previous = None
seeded = False


def write_event(kind, **values):
    with (directory / "events.jsonl").open("a") as output:
        output.write(
            json.dumps(dict(time=time.time(), pid=os.getpid(), kind=kind, **values))
            + "\n"
        )


class Observer(QtCore.QObject):
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.FileOpen:
            write_event(
                "native-file-open",
                path=event.file(),
                active=str(pyzo.application.workspaces.active_identity),
            )
        elif event.type() == QtCore.QEvent.Type.WindowActivate:
            write_event(
                "window-activate",
                title=obj.windowTitle()
                if hasattr(obj, "windowTitle")
                else type(obj).__name__,
            )
        elif event.type() in (
            QtCore.QEvent.Type.MouseButtonPress,
            QtCore.QEvent.Type.MouseButtonRelease,
        ):
            point = event.globalPosition()
            write_event(
                "native-mouse",
                event=int(event.type()),
                x=point.x(),
                y=point.y(),
                widget=type(obj).__name__,
            )
        return False


def snapshot():
    global previous, sequence
    if not seeded:
        return
    docs = window._peerDocumentResources
    owners = []
    for owner in pyzo.application.workspaces.identities:
        runtime = window._peerRuntimeCatalog.runtime(owner)
        if runtime._disposed:
            continue
        local = pyzo.workspaceContext.context(owner)
        editors = [
            dict(
                view=str(editor._peerViewIdentity),
                document=str(editor._peerDocumentIdentity),
                path=editor._filename,
                text=editor.toPlainText(),
                dirty=editor.document().isModified(),
                cursor=editor.textCursor().position(),
            )
            for editor in local.editors
            if isValid(editor)
        ]
        shells = [
            dict(
                id=id(shell),
                state=shell._state,
                version=shell._version,
                epoch=getattr(shell, "_nativeTransportEpoch", None),
                text=shell.toPlainText()[-3000:],
            )
            for shell in local.shells.getShells()
            if isValid(shell)
        ]
        owners.append(
            dict(
                id=str(owner),
                name=window._peerWorkspaces.descriptor(owner).name,
                editors=editors,
                shells=shells,
                layout=runtime.model.serialize_layout(),
                tools=pyzo.toolManager.for_workspace(owner).getLoadedTools(),
                frames=[
                    dict(
                        id=key,
                        title=frame.windowTitle(),
                        visible=frame.isVisible(),
                        active=frame.isActiveWindow(),
                        screen=frame.screen().name() if frame.screen() else None,
                        device_pixel_ratio=frame.devicePixelRatioF(),
                        geometry=[frame.x(), frame.y(), frame.width(), frame.height()],
                    )
                    for key, frame in runtime.frame_windows.items()
                ],
            )
        )
    focus = QtWidgets.QApplication.focusWidget()
    windows = QtWidgets.QApplication.topLevelWidgets()
    data = dict(
        pid=os.getpid(),
        platform=QtWidgets.QApplication.platformName(),
        active=str(pyzo.application.workspaces.active_identity),
        screens=[dict(
            name=screen.name(),
            geometry=[screen.geometry().x(), screen.geometry().y(), screen.geometry().width(), screen.geometry().height()],
            available_geometry=[screen.availableGeometry().x(), screen.availableGeometry().y(), screen.availableGeometry().width(), screen.availableGeometry().height()],
            logical_dpi=screen.logicalDotsPerInch(),
            device_pixel_ratio=screen.devicePixelRatio(),
        ) for screen in QtGui.QGuiApplication.screens()],
        owners=owners,
        focus=dict(type=type(focus).__name__, owner=str(owner_for(focus)))
        if focus
        else None,
        qmainwindow=sum(isinstance(item, QtWidgets.QMainWindow) for item in windows),
        cursor_position=[QtGui.QCursor.pos().x(), QtGui.QCursor.pos().y()],
        dialogs=[
            dict(
                title=item.windowTitle(),
                class_name=type(item).__name__,
                text=item.text() if isinstance(item, QtWidgets.QMessageBox) else "",
            )
            for item in windows
            if isinstance(item, QtWidgets.QDialog) and item.isVisible()
        ],
        errors=window._peerApplicationExitErrors,
        documents={
            str(identity): dict(
                text=docs.resource(identity).text,
                path=docs.resource(identity).path,
                dirty=docs.resource(identity).is_dirty(),
            )
            for identity in docs.document_ids
        },
    )
    fingerprint = json.dumps(data, sort_keys=True)
    if fingerprint != previous:
        previous = fingerprint
        sequence += 1
        data.update(sequence=sequence, time=time.time())
        pending = directory / "snapshot.pending"
        pending.write_text(json.dumps(data, indent=2))
        pending.replace(directory / "snapshot.json")
        write_event(
            "snapshot",
            sequence=sequence,
            active=data["active"],
            focus=data["focus"],
            view_ids=[entry["view"] for owner in owners for entry in owner["editors"]],
        )


def setup():
    global seeded
    expected = directory / "fixture.json"
    if not expected.exists():
        owners = [pyzo.application.workspaces.active_identity]
        window._peerWorkspaces.rename_workspace(owners[0], "Physical A")
        owners.append(pyzo.application.workspaces.create("Physical B"))
        editors = []
        for index, owner in enumerate(owners):
            local = pyzo.workspaceContext.context(owner)
            editor = local.editors.getCurrentEditor()
            editor.setPlainText(
                f"# Physical {'AB'[index]} local\nvalue_{'ab'[index]} = {index + 1}\n"
            )
            pyzo.application.documents.flush(editor)
            editors.append(editor)
            pyzo.toolManager.for_workspace(owner).loadTool("pyzofilebrowser")
            pyzo.toolManager.for_workspace(owner).getTool("pyzofilebrowser").setPath(
                str(directory)
            )
        (directory / "shared.py").write_text("# Shared fixture\nshared_value = 10\n")
        (directory / "ingress.py").write_text(
            "# Native file-open fixture\ningress_value = 20\n"
        )
        shared = [
            pyzo.workspaceContext.context(owner)
            .editors.loadFile(str(directory / "shared.py"))
            .editor
            for owner in owners
        ]
        pyzo.workspaceContext.context(owners[1]).shells.addShell()
        # Controlled initial two-frame setup; physical reconfiguration is tested
        # only by CUA/manual drag after this setup, never by these API calls.
        for index, owner in enumerate(owners):
            runtime = window._peerRuntimeCatalog.runtime(owner)
            model = runtime.model
            anchor = runtime.backend._pane_id_from_dock(
                runtime.editor_hosts[pyzo.editors._group_for_editor(editors[index])]
            )
            shared_pane = runtime.backend._pane_id_from_dock(
                runtime.editor_hosts[pyzo.editors._group_for_editor(shared[index])]
            )
            assert model.tab(shared_pane, anchor).applied
            for pane_id, pane in tuple(model.panes.items()):
                if pane_id in {anchor, shared_pane}:
                    continue
                assert model.split(
                    pane_id,
                    anchor,
                    Direction.BELOW if pane.kind.value == "shell" else Direction.RIGHT,
                ).applied
            for frame in runtime.frame_windows.values():
                screen = frame.screen().availableGeometry()
                width = min(850, screen.width() // 2 - 30)
                height = min(650, screen.height() - 100)
                frame.setGeometry(
                    screen.x() + 20 + index * (width + 30),
                    screen.y() + 50,
                    width,
                    height,
                )
                frame.show()
            local = pyzo.workspaceContext.context(owner)
            local.editors.setActiveGroup(pyzo.editors._group_for_editor(editors[index]))
            editors[index].setFocus()
        window._refreshWorkspaceAffiliation()
        window._activatePeerWorkspace(owners[0])
        window._savePeerWorkspacePersistence()
        expected.write_text(
            json.dumps(
                dict(
                    owners=[str(owner) for owner in owners],
                    local_views=[str(editor._peerViewIdentity) for editor in editors],
                    shared_views=[str(editor._peerViewIdentity) for editor in shared],
                    shared_document=str(shared[0]._peerDocumentIdentity),
                ),
                indent=2,
            )
        )
        write_event("fixture-created")
    else:
        write_event("fixture-restored")
    seeded = True
    assert QtWidgets.QApplication.platformName() == os.environ.get("PYZO_PHYSICAL_QPA", "cocoa")
    snapshot()
    print("PHYSICAL DESKTOP SESSION READY", QtWidgets.QApplication.platformName(), str(directory), flush=True)


def observe():
    try:
        snapshot()
    except Exception:
        write_event("observation-error", trace=traceback.format_exc())
        print(traceback.format_exc(), flush=True)
        observer_timer.stop()


original_init = MainWindow.__init__


def init(self, *args, **kwargs):
    global window, observer, observer_timer
    original_init(self, *args, **kwargs)
    window = self
    observer = Observer(QtWidgets.qApp)
    QtWidgets.qApp.installEventFilter(observer)
    observer_timer = QtCore.QTimer()
    observer_timer.timeout.connect(observe)
    observer_timer.start(200)
    QtWidgets.qApp.aboutToQuit.connect(
        lambda: write_event(
            "about-to-quit", errors=list(window._peerApplicationExitErrors)
        )
    )
    QtCore.QTimer.singleShot(700, setup)


MainWindow.__init__ = init
pyzo._start.start()
write_event("process-returned", errors=list(window._peerApplicationExitErrors))
