"""Workspace-owned built-in tools and durable contextual state in real kernels."""

from __future__ import annotations

import os
import sys
import time
import traceback
import types
from pathlib import Path

from pyzo.util import paths

directory = Path(os.environ["PYZO_WORKSPACE_SET_PROBE_DIR"])
directory.mkdir(parents=True, exist_ok=True)
(directory / "tools").mkdir(exist_ok=True)
os.chdir(directory)
paths.prepare_appdata_appconfig_dirs = lambda: (str(directory), str(directory))
os.environ["PYZO_WORKSPACE_DIR"] = str(directory / "workspaces")
os.environ["PYZO_RECOVERY_DIR"] = str(directory / "recovery")
os.environ["PYZO_LOG"] = str(directory / "application.log")
commandline = types.ModuleType("pyzo.core.commandline")
commandline.is_our_server_running = lambda: False
commandline.handle_cmd_args = lambda: None
commandline.stop_our_server = lambda: None
sys.modules["pyzo.core.commandline"] = commandline
sys.argv = ["pyzolauncher.py"]

import pyzo._start
from pyzo.core.main import MainWindow
from pyzo.qt import QtCore, QtWidgets

import gc
import json
import psutil
from copy import deepcopy
from dataclasses import replace
from shiboken6 import isValid
from pyzo.core.workspaceContext import plain
from pyzo.core.workspaceRuntime import WorkspaceRuntimeCatalog
from spikes.peer_frames.identity import ApplicationIdentity, IdentityKind

phase = os.environ["PYZO_WORKSPACE_SET_PHASE"]
count = int(os.environ["PYZO_SCALE_WORKSPACES"])
started = time.monotonic()
state = {"phase": "initial", "cycle": 0, "samples": []}
window = None
TOOLS = (
    "pyzohistoryviewer",
    "pyzosourcestructure",
    "pyzosnippets",
    "pyzointeractivehelp",
)
UNAVAILABLE = "scale-unavailable"
original_create = WorkspaceRuntimeCatalog.create


def create_with_failure(self, **kwargs):
    if str(kwargs["identity"]) == UNAVAILABLE:
        raise RuntimeError("test-owned unavailable scale workspace")
    return original_create(self, **kwargs)


WorkspaceRuntimeCatalog.create = create_with_failure


def flush():
    QtWidgets.QApplication.processEvents()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    gc.collect()


def context(owner):
    return pyzo.workspaceContext.context(owner)


def metrics():
    owners = pyzo.application.workspaces.identities
    runtimes = [window._peerRuntimeCatalog.runtime(owner) for owner in owners]
    widgets = QtWidgets.QApplication.allWidgets()
    timers = {}
    for parent in [QtWidgets.qApp, *widgets]:
        for timer in parent.findChildren(QtCore.QTimer):
            if isValid(timer):
                timers[id(timer)] = timer
    for value in vars(window).values():
        if isinstance(value, QtCore.QTimer) and isValid(value):
            timers[id(value)] = value
    delivered = {str(owner): 0 for owner in owners}
    observed = []
    for owner in owners:
        local = context(owner).editors

        def callback(owner=owner):
            delivered[str(owner)] += 1

        local.currentChanged.connect(callback)
        observed.append((local, callback))
    pyzo.editors.currentChanged.emit()
    for local, callback in observed:
        local.currentChanged.disconnect(callback)
    assert list(delivered.values()) == [1] * len(owners), delivered
    assert all(runtime.backend.manager.dockAreaCount() == 0 for runtime in runtimes)
    assert not any(isinstance(widget, QtWidgets.QMainWindow) for widget in widgets)
    return dict(
        workspaces=len(owners),
        widgets=len(widgets),
        timers=len(timers),
        panes=sum(len(runtime.backend.docks) for runtime in runtimes),
        frames=sum(len(runtime.frame_windows) for runtime in runtimes),
        documents=len(window._peerDocumentResources.document_ids),
        views=len(window._peerDocumentResources.view_ids),
        retained_views=len(window._peerDocumentResources.retained_view_ids),
        modules=sum(name.startswith("pyzo.tools._workspace_") for name in sys.modules),
        signal_receivers=pyzo.editors.receivers("2currentChanged()"),
        callbacks=sum(delivered.values()),
        rss_kib=psutil.Process().memory_info().rss // 1024,
        startup_seconds=round(time.monotonic() - started, 4),
    )


def verify(expected):
    docs = window._peerDocumentResources
    assert {str(owner) for owner in pyzo.application.workspaces.identities} == set(
        expected["owners"]
    )
    shared = ApplicationIdentity(IdentityKind.DOCUMENT, expected["shared"])
    assert docs.resource(shared).text == expected["shared_text"]
    for index, text in enumerate(expected["owners"]):
        owner = ApplicationIdentity(IdentityKind.WORKSPACE, text)
        local = context(owner)
        assert local.requested.view.zoom == index % 2
        assert "scale_" + str(index) in local.command_history.get_commands()
        assert plain(local.config.tools.future_scale) == {"owner": text}
        manager = pyzo.toolManager.for_workspace(owner)
        assert set(manager.getLoadedTools()) == set(expected["tools"][text])
        main = docs.main(owner)
        assert str(main.document_id) == expected["mains"][text]
        for editor in local.editors:
            view = docs.view(editor._peerViewIdentity)
            assert view.workspace_id == owner
            assert str(view.document_id) in expected["documents"]
            assert editor.toPlainText() == expected["documents"][str(view.document_id)]
        runtime = window._peerRuntimeCatalog.runtime(owner)
        for tool_id, dock in manager._activeTools.items():
            assert isValid(dock) and isValid(dock.widget()), (text, tool_id)
            pane_id = runtime.backend._pane_id_from_dock(dock)
            assert runtime.backend.docks.get(pane_id) is dock
            assert runtime.model.is_pane_placed(pane_id), (text, tool_id, pane_id)
        for dock in runtime.backend.docks.values():
            assert (
                window._peerWorkspaces.descriptor(owner).name in dock.accessibleName()
            )
        local_doc = ApplicationIdentity(
            IdentityKind.DOCUMENT, expected["locals"][index]
        )
        assert docs.resource(local_doc).text == expected["documents"][str(local_doc)]
    assert (directory / "shared.py").read_text() == "external disk\n"
    assert not (directory / "missing.py").exists()
    missing = ApplicationIdentity(IdentityKind.DOCUMENT, expected["missing"])
    if phase == "scale-restore":
        assert docs.resource(shared).external_conflict
        assert not pyzo.application.workspace_execution._main_path_is_available(
            docs.resource(missing).path
        )
        assert UNAVAILABLE in window._peerWorkspaceRestoreFailures
        loaded = window._peerWorkspaceStore.load()
        assert loaded.state.workspaces[UNAVAILABLE] == expected["unavailable"]
        assert UNAVAILABLE in loaded.state.loaded_workspace_ids
    return shared


def finish():
    window._peerShellCloseChooser = lambda *_: "terminate"
    result = pyzo.application.lifecycle.quit()
    assert getattr(result, "value", None) == "completed", result
    assert not window._peerApplicationExitErrors, window._peerApplicationExitErrors


def tick():
    if state["phase"] == "initial":
        if phase == "scale-seed":
            shell = pyzo.shells.getCurrentShell()
            if shell is None or not shell._version or shell._state != "Ready":
                return
            owners = [pyzo.application.workspaces.active_identity]
            owners += [
                pyzo.application.workspaces.create("Scale " + str(i))
                for i in range(1, count)
            ]
            locals_ = []
            for index, owner in enumerate(owners):
                local = context(owner)
                editor = local.editors.getCurrentEditor()
                editor.setPlainText("needle local " + str(index) + "\n")
                pyzo.application.documents.flush(editor)
                locals_.append(editor)
                local.requested.view.zoom = index % 2
                local.config.tools.future_scale = {"owner": str(owner)}
                local.command_history.append("scale_" + str(index))
                for tool in TOOLS:
                    pyzo.toolManager.for_workspace(owner).loadTool(tool)
            shared_path = directory / "shared.py"
            shared_path.write_text("needle disk\n")
            shared_editors = [
                context(owner).editors.loadFile(str(shared_path)).editor
                for owner in owners
            ]
            shared_editors[0].setPlainText("needle shared unsaved\n")
            pyzo.application.documents.flush(shared_editors[0])
            shared = shared_editors[0]._peerDocumentIdentity
            assert all(
                editor._peerDocumentIdentity == shared for editor in shared_editors
            )
            # Invoke A's Replace All and late help completion with another owner foreground.
            window._activatePeerWorkspace(owners[-1])
            host = pyzo.editors._group_for_editor(shared_editors[0])
            find = host._findReplace
            find._findText.setText("needle")
            find._replaceText.setText("changed")
            find._replaceInAllFiles()
            assert locals_[0].toPlainText() == "changed local 0\n"
            assert all(
                editor.toPlainText() == "needle local " + str(i) + "\n"
                for i, editor in enumerate(locals_)
                if i
            )
            assert all(
                editor.toPlainText() == "changed shared unsaved\n"
                for editor in shared_editors
            )
            help_calls = []
            help_tool = pyzo.toolManager.for_workspace(owners[0]).getTool(
                "pyzointeractivehelp"
            )
            original = help_tool.helpFromExtension
            help_tool.helpFromExtension = lambda *args: help_calls.append(args)
            shared_editors[0].restoreHelp("calltip")
            help_tool.helpFromExtension = original
            assert help_calls == [(None, "calltip")]
            from pyzo.core.pdfExport import PdfExport

            dialog = PdfExport(editor=shared_editors[0], parent=shared_editors[0])
            assert dialog._currentEditor is shared_editors[0]
            assert dialog._sliderZoom.value() == context(owners[0]).config.view.zoom
            dialog.close()
            dialog.deleteLater()
            missing_path = directory / "missing.py"
            missing_path.write_text("missing disk\n")
            missing = context(owners[0]).editors.loadFile(str(missing_path)).editor
            missing.setPlainText("missing retained\n")
            pyzo.application.documents.flush(missing)
            for owner in owners:
                window._peerDocumentResources.set_main(owner, shared)
            window._peerDocumentResources.set_main(
                owners[-1], missing._peerDocumentIdentity
            )
            # Retain one closed dirty view without a source-file save.
            assert context(owners[0]).editors.closeFile(locals_[0]) == 1
            flush()
            expected = dict(
                owners=[str(owner) for owner in owners],
                shared=str(shared),
                shared_text=window._peerDocumentResources.resource(shared).text,
                locals=[str(editor._peerDocumentIdentity) for editor in locals_],
                missing=str(missing._peerDocumentIdentity),
                documents={
                    str(identity): window._peerDocumentResources.resource(identity).text
                    for identity in window._peerDocumentResources.document_ids
                },
                active=str(pyzo.application.workspaces.active_identity),
                tools={
                    str(owner): pyzo.toolManager.for_workspace(owner).getLoadedTools()
                    for owner in owners
                },
                mains={
                    str(owner): str(
                        window._peerDocumentResources.main(owner).document_id
                    )
                    for owner in owners
                },
                unavailable=dict(
                    schema=1,
                    identity=UNAVAILABLE,
                    name="Unavailable scale",
                    persistence_location=None,
                    session={},
                    profile={},
                    extensions={"future": ["opaque", 7]},
                ),
            )
            window._savePeerWorkspacePersistence()
            loaded = window._peerWorkspaceStore.load()
            records = deepcopy(dict(loaded.state.workspaces))
            records[UNAVAILABLE] = expected["unavailable"]
            window._peerWorkspaceStore.commit(
                replace(
                    loaded.state,
                    workspaces=records,
                    loaded_workspace_ids=loaded.state.loaded_workspace_ids
                    + (UNAVAILABLE,),
                )
            )
            (directory / "scale-expected.json").write_text(json.dumps(expected))
            state["samples"].append(metrics())
            shared_path.write_text("external disk\n")
            missing_path.unlink()
            print("SCALE SEED", json.dumps(state["samples"][0]), flush=True)
            print(
                "SCALE LOADED RECORDS",
                json.dumps(
                    {
                        key: dict(
                            tools=record.get("session", {}).get("loaded_tools"),
                            panes=[
                                p
                                for f in record.get("session", {})
                                .get("layout", {})
                                .get("frames", [])
                                for g in f["groups"]
                                for p in g["panes"]
                            ],
                        )
                        for key, record in window._peerWorkspaceStore.load().state.workspaces.items()
                    }
                ),
                flush=True,
            )
            print("WORKSPACE SCALE SEED COMPLETE", flush=True)
            state["phase"] = "done"
            finish()
            return
        expected = json.loads((directory / "scale-expected.json").read_text())
        verify(expected)
        assert str(pyzo.application.workspaces.active_identity) == expected["active"]
        state.update(
            expected=expected,
            phase="settle",
            survivors={
                str(editor._peerViewIdentity): editor
                for owner in pyzo.application.workspaces.identities[:-1]
                for editor in context(owner).editors
            },
        )
        return
    if state["phase"] == "settle":
        flush()
        state["samples"].append(metrics())
        if count == 1 or state["cycle"] == 3:
            verify(state["expected"])
            report = dict(workspaces=count, samples=state["samples"])
            (directory / "scale-metrics.json").write_text(json.dumps(report))
            print("SCALE METRICS", json.dumps(report), flush=True)
            print("WORKSPACE SCALE RESTORE COMPLETE", flush=True)
            state["phase"] = "done"
            finish()
            return
        owner = pyzo.application.workspaces.identities[-1]
        old = context(owner).editors
        retired = []
        old.currentChanged.connect(lambda: retired.append("called"))
        result = pyzo.application.workspaces.close(owner)
        assert result.applied, result.detail
        retired.clear()
        pyzo.editors.currentChanged.emit()
        assert retired == []
        flush()
        result = pyzo.application.workspaces.reopen(owner)
        assert result.applied, result.detail
        for key, editor in state["survivors"].items():
            assert isValid(editor) and str(editor._peerViewIdentity) == key
        state["cycle"] += 1
        state["phase"] = "settle"
        return


def guarded_tick():
    try:
        tick()
    except Exception:
        traceback.print_exc()
        timer.stop()
        pyzo.localKernelManager.terminateAll()
        QtWidgets.qApp.exit(1)


original_init = MainWindow.__init__


def init(self, *args, **kwargs):
    global window, timer
    original_init(self, *args, **kwargs)
    window = self
    timer = QtCore.QTimer(self)
    timer.timeout.connect(guarded_tick)
    timer.start(100)


MainWindow.__init__ = init
pyzo._start.start()
