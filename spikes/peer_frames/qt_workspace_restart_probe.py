"""Real two-process restart with secondary owner foreground and live shell seed."""

import json
import os
from pathlib import Path
import sys
import types
import traceback
from pyzo.util import paths

directory = Path(os.environ["PYZO_WORKSPACE_SET_PROBE_DIR"])
directory.mkdir(parents=True, exist_ok=True)
(directory / "tools").mkdir(exist_ok=True)
os.chdir(directory)
paths.prepare_appdata_appconfig_dirs = lambda: (str(directory), str(directory))
os.environ.update(
    PYZO_WORKSPACE_DIR=str(directory / "workspaces"),
    PYZO_RECOVERY_DIR=str(directory / "recovery"),
    PYZO_LOG=str(directory / "application.log"),
)
commandline = types.ModuleType("pyzo.core.commandline")
commandline.is_our_server_running = lambda: False
commandline.handle_cmd_args = lambda: None
commandline.stop_our_server = lambda: None
sys.modules["pyzo.core.commandline"] = commandline
sys.argv = ["pyzolauncher.py"]
import pyzo._start
from pyzo.core.main import MainWindow
from pyzo.qt import QtCore, QtWidgets
from spikes.peer_frames.contract import Direction
from spikes.peer_frames.workspace_session import retained_pane_layout

window = None
state = {"phase": "initial"}
phase = os.environ["PYZO_WORKSPACE_SET_PHASE"]


def ready(shell):
    return (
        shell._version and shell._state == "Ready" and shell._context.connection_count
    )


def finish():
    state["phase"] = "done"
    window._peerShellCloseChooser = lambda *_: "terminate"
    pyzo.application.lifecycle.quit()


def semantic(runtime):
    keys = {
        runtime.backend._pane_id_from_dock(dock): "view:"
        + str(host._tabs.currentItem().editor._peerViewIdentity)
        for host, dock in runtime.editor_hosts.items()
        if host._tabs.currentItem() is not None
    }
    keys.update(
        {
            runtime.backend._pane_id_from_dock(dock): "tool:" + dock._toolId
            for dock in runtime.backend.docks.values()
            if hasattr(dock, "_toolId")
        }
    )
    result = retained_pane_layout(runtime.model.serialize_layout(), keys)
    # A selected old shell is ephemeral; startup may focus an eligible retained
    # pane or its fresh default shell. Group selection/placement stays exact.
    result["active_pane_id"] = None
    return result


def tick():
    if state["phase"] == "done":
        return
    if phase == "restart-restore":
        expected = json.loads((directory / "restart-expected.json").read_text())
        shells = tuple(pyzo.shells)
        if not shells or not all(ready(shell) for shell in shells):
            return
        assert str(window._peerRuntime.identity) == expected["active"]
        actual = {
            str(owner): window._peerRuntimeCatalog.runtime(owner)
            for owner in pyzo.application.workspaces.identities
        }
        assert set(actual) == set(expected["owners"])
        for owner, runtime in actual.items():
            local = pyzo.workspaceContext.context(runtime.identity)
            name = window._peerWorkspaces.descriptor(runtime.identity).name
            assert all(
                name in frame.windowTitle() for frame in runtime.frame_windows.values()
            ), "Restored frame caption lost its owner"
            assert all(
                host._tabs.currentItem() is not None for host in runtime.editor_hosts
            ), "Empty startup editor survived restore"
            assert {
                str(editor._peerViewIdentity): editor.toPlainText()
                for editor in local.editors
            } == expected["views"][owner]
            assert semantic(runtime) == expected["layouts"][owner], (
                owner,
                semantic(runtime),
                expected["layouts"][owner],
            )
            for frame_id, geometry in expected["geometries"][owner].items():
                frame = runtime.frame_windows[frame_id]
                rect = frame.geometry()
                assert [rect.x(), rect.y(), rect.width(), rect.height()] == geometry
        assert not set(expected["epochs"]).intersection(
            shell._nativeTransportEpoch for shell in shells
        )
        assert not window._peerWorkspaceRestoreFailures, (
            window._peerWorkspaceRestoreFailures
        )
        print("WORKSPACE RESTART RESTORE COMPLETE", flush=True)
        finish()
        return
    if state["phase"] == "initial":
        shell = pyzo.shells.getCurrentShell()
        if shell is None or not ready(shell):
            return
        a = pyzo.application.workspaces.active_identity
        b = pyzo.application.workspaces.create("Restart B")
        pyzo.workspaceContext.context(b).shells.addShell()
        state.update(phase="seed", owners=[a, b])
        return
    if state["phase"] == "seed":
        if not all(ready(shell) for shell in pyzo.shells):
            return
        owners = state["owners"]
        shared = directory / "shared.py"
        shared.write_text("shared_value = 10\n")
        for index, owner in enumerate(owners):
            local = pyzo.workspaceContext.context(owner)
            editor = local.editors.getCurrentEditor()
            editor.setPlainText("local_owner = " + str(index) + "\n")
            pyzo.application.documents.flush(editor)
            second = local.editors.loadFile(str(shared)).editor
            manager = pyzo.toolManager.for_workspace(owner)
            manager.loadTool("pyzofilebrowser")
            runtime = local.runtime
            anchor = runtime.backend._pane_id_from_dock(
                runtime.editor_hosts[pyzo.editors._group_for_editor(editor)]
            )
            peer = runtime.backend._pane_id_from_dock(
                runtime.editor_hosts[pyzo.editors._group_for_editor(second)]
            )
            assert runtime.model.tab(peer, anchor).applied
            for pane_id, pane in tuple(runtime.model.panes.items()):
                if pane_id not in {anchor, peer}:
                    assert runtime.model.split(
                        pane_id,
                        anchor,
                        Direction.BELOW
                        if pane.kind.value == "shell"
                        else Direction.RIGHT,
                    ).applied
        window._activatePeerWorkspace(owners[-1])
        for index, owner in enumerate(owners):
            runtime = window._peerRuntimeCatalog.runtime(owner)
            for frame in runtime.frame_windows.values():
                frame.setGeometry(30 + index * 100, 50 + index * 100, 800, 600)
        expected = dict(
            active=str(owners[-1]),
            owners=[str(owner) for owner in owners],
            views={
                str(owner): {
                    str(editor._peerViewIdentity): editor.toPlainText()
                    for editor in pyzo.workspaceContext.context(owner).editors
                }
                for owner in owners
            },
            layouts={
                str(owner): semantic(window._peerRuntimeCatalog.runtime(owner))
                for owner in owners
            },
            geometries={
                str(owner): {
                    key: [
                        frame.geometry().x(),
                        frame.geometry().y(),
                        frame.width(),
                        frame.height(),
                    ]
                    for key, frame in window._peerRuntimeCatalog.runtime(
                        owner
                    ).frame_windows.items()
                    if key
                    in {
                        item["id"]
                        for item in semantic(window._peerRuntimeCatalog.runtime(owner))[
                            "frames"
                        ]
                    }
                }
                for owner in owners
            },
            epochs=[shell._nativeTransportEpoch for shell in pyzo.shells],
        )
        (directory / "restart-expected.json").write_text(json.dumps(expected))
        print("WORKSPACE RESTART SEED COMPLETE", flush=True)
        finish()


original_init = MainWindow.__init__


def init(self, *args, **kwargs):
    global window
    original_init(self, *args, **kwargs)
    window = self
    self._restartProbe = QtCore.QTimer(self)

    def guarded():
        try:
            tick()
        except Exception:
            traceback.print_exc()
            self._restartProbe.stop()
            self._abortPeerTestRun()
            QtWidgets.qApp.exit(1)

    self._restartProbe.timeout.connect(guarded)
    self._restartProbe.start(60)
    QtCore.QTimer.singleShot(
        20000, lambda: self._abortPeerTestRun() if state["phase"] != "done" else None
    )


MainWindow.__init__ = init
pyzo._start.start()
