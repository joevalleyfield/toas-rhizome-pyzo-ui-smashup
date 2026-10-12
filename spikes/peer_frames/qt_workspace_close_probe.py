"""Real-kernel workspace Cancel, failed publication, termination and resume."""

from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys
import time
import traceback
import types

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
from spikes.peer_frames import workspace_persistence
from spikes.peer_frames.owned_process import process_for_pid
from spikes.peer_frames.execution_routing import AssignmentMode, ExecutionCommand

state = {"phase": "initial", "events": [], "choices": []}
window = None


def ready(shell):
    return (
        shell._version and shell._state == "Ready" and shell._context.connection_count
    )


def value(shell, expression):
    return shell._request.eval(expression).result_or_cancel(0.2)


def activate(editor):
    host = pyzo.editors._group_for_editor(editor)
    runtime = window._peerRuntimeForEditorHost(host)
    window._onFocusedDockWidgetChanged(runtime.editor_hosts[host])
    host._tabs.setCurrentItem(
        next(item for item in host._tabs.items() if item.editor is editor)
    )


def write(editor, text):
    editor.setPlainText(text)
    pyzo.application.documents.flush(editor)


def placement(editor):
    host = pyzo.editors._group_for_editor(editor)
    runtime = window._peerRuntimeForEditorHost(host)
    pane_id = runtime.backend._pane_id_from_dock(runtime.editor_hosts[host])
    return runtime.model.resolve_pane_context(pane_id)


def choose(choice):
    def answer(pane_id, lifecycle):
        state["choices"].append((state["phase"], pane_id, choice))
        return choice

    window._peerShellCloseChooser = answer


def live_snapshot():
    docs, service = pyzo.application.documents, pyzo.application.workspace_execution
    return {
        "owners": tuple(pyzo.application.workspaces.identities),
        "active": pyzo.application.workspaces.active_identity,
        "layouts": [
            deepcopy(state[key].model.serialize_layout()) for key in ("a", "b")
        ],
        "resources": deepcopy(docs.registry.snapshot()),
        "views": [
            service.selection_targets(state[key])
            for key in ("ea", "eb", "ua", "shared")
        ],
        "shells": [
            (
                shell._context,
                service.router.shell_state(service._shells[shell].identity),
            )
            for shell in (state["sa"], state["sb"])
        ],
        "bindings": tuple(docs._editors),
    }


def durable_before_teardown(event, owner):
    if state["phase"] != "accept":
        state["events"].append((event, str(owner)))
        return
    assert owner == state["a"].identity, (event, owner)
    persisted = window._peerWorkspaceStore.load()
    assert not persisted.issues, persisted.issues
    records = persisted.state.shared_resources
    for document_id, expected in state["durable_documents"].items():
        actual = records["documents"][document_id]
        for field in ("text", "clean_text", "undo", "redo"):
            assert actual[field] == expected[field], (event, document_id, field)
    assert set(state["a_views"]) <= set(records["views"])
    assert str(state["b"].identity) in persisted.state.loaded_workspace_ids
    state["events"].append((event, str(owner), persisted.generation))


def install_observers():
    original_close = window._closeCommittedPeerShell

    def close(pane_id, shell, **kwargs):
        durable_before_teardown("shell-close", state["shell_owners"][shell])
        return original_close(pane_id, shell, **kwargs)

    window._closeCommittedPeerShell = close
    for shell in (state["sa"], state["sb"]):
        original = shell.terminate

        def terminate(_shell=shell, _original=original):
            durable_before_teardown("terminate", state["shell_owners"][_shell])
            return _original()

        shell.terminate = terminate
    documents = pyzo.application.documents
    editor_owners = {
        editor: documents.registry.view(documents.view_identity(editor)).workspace_id
        for editor in documents._editors
    }
    original_unbind = documents.unbind

    def unbind(editor):
        durable_before_teardown("editor-unbind", editor_owners.get(editor))
        return original_unbind(editor)

    documents.unbind = unbind


def assert_preserved(before):
    assert live_snapshot() == before
    assert not state["events"], state["events"]
    assert all(process.poll() is None for process in state["processes"])
    assert all(
        entry.pending_disposition is None
        for entry in window._peerShellLifecycles._shells.values()
    ), "failed/cancelled close retained uncommitted termination authority"


def tick():
    phase = state["phase"]
    if phase == "initial":
        sa = pyzo.shells.getCurrentShell()
        if sa is None or not ready(sa):
            return
        a, ea = window._peerActiveRuntime(), pyzo.editors.getCurrentEditor()
        write(ea, "# A saved baseline\n")
        ea.document().setModified(True)
        assert pyzo.editors.saveFile(ea, str(directory / "a.py"))
        ua = pyzo.editors.newFile().editor
        write(ua, "untitled A retained\n")
        b_id = pyzo.application.workspaces.create("Close peer B")
        b = window._peerRuntimeCatalog.runtime(b_id)
        eb, sb = pyzo.editors.getCurrentEditor(), pyzo.shells.addShell()
        write(eb, "# B saved baseline\n")
        eb.document().setModified(True)
        assert pyzo.editors.saveFile(eb, str(directory / "b.py"))
        shared = window._peerMainEditor(
            pyzo.application.documents.identity(ea), b.identity
        )
        write(ea, "# dirty shared A\n")
        write(eb, "# dirty B\n")
        state.update(
            phase="ready", a=a, b=b, ea=ea, eb=eb, ua=ua, shared=shared, sa=sa, sb=sb
        )
        return
    docs, service = pyzo.application.documents, pyzo.application.workspace_execution
    a, b, sa, sb = (state[key] for key in ("a", "b", "sa", "sb"))
    if phase == "ready":
        if not ready(sb):
            return
        if not state.get("seeded"):
            sa.executeCommand("close_marker = 'A'\n")
            sb.executeCommand("close_marker = 'B'\n")
            state["seeded"] = True
            return
        if value(sa, "close_marker") != "A" or value(sb, "close_marker") != "B":
            return
        pids = [value(shell, "__import__('os').getpid()") for shell in (sa, sb)]
        assert len(set(pids)) == 2 and all(isinstance(pid, int) for pid in pids)
        processes = [
            process_for_pid(
                (kernel._process for kernel in pyzo.localKernelManager._kernels), pid
            )
            for pid in pids
        ]
        for editor, shell in ((state["ea"], sa), (state["eb"], sb)):
            assert service.assign_selection(editor, shell).applied
        activate(state["eb"])
        assert docs.identity(state["ea"]) == docs.identity(state["shared"])
        assert state["ea"] is not state["shared"]
        assert (
            docs.registry.view(docs.view_identity(state["shared"])).workspace_id
            == b.identity
        )
        assert state["ea"].toPlainText() == state["shared"].toPlainText()
        assert window._savePeerWorkspacePersistence()
        write(state["ua"], "untitled A latest retained\n")
        state.update(
            processes=processes,
            pids=pids,
            shell_owners={sa: a.identity, sb: b.identity},
            bytes=[(directory / f"{label}.py").read_bytes() for label in ("a", "b")],
            old_a=service.resolve_shell(sa, ExecutionCommand.TOOL).provenance,
            old_b=service.resolve_shell(sb, ExecutionCommand.TOOL).provenance,
            old_workspace=window._peerWorkspaces.resolve_workspace_context(a.identity),
            old_view=service.request_source_token(state["ea"]),
            phase="cancel",
        )
        install_observers()
        print("TWO READY KERNELS", pids, flush=True)
        return
    if phase in {"cancel", "cancel-after-failure"}:
        before = live_snapshot()
        manifest = window._peerWorkspaceStore.manifest.read_bytes()
        choose("cancel")
        count = len(state["choices"])
        result = pyzo.application.workspaces.close(a.identity)
        assert not result.applied, result
        assert len(state["choices"]) == count + 1
        assert window._peerWorkspaceStore.manifest.read_bytes() == manifest
        assert_preserved(before)
        print("CANCEL PRESERVED", phase, "zero irreversible events", flush=True)
        state["phase"] = "fail-publication" if phase == "cancel" else "accept"
        return
    if phase == "fail-publication":
        before = live_snapshot()
        manifest = window._peerWorkspaceStore.manifest.read_bytes()
        original_replace = workspace_persistence.os.replace
        failed = []

        def fail_manifest(source, destination):
            if Path(destination) == window._peerWorkspaceStore.manifest:
                failed.append(str(destination))
                raise OSError("owned acceptance manifest publication failure")
            return original_replace(source, destination)

        choose("terminate")
        workspace_persistence.os.replace = fail_manifest
        try:
            result = pyzo.application.workspaces.close(a.identity)
        finally:
            workspace_persistence.os.replace = original_replace
        assert failed and not result.applied, result
        assert "persistence preflight failed" in result.detail, result
        assert window._peerWorkspaceStore.manifest.read_bytes() == manifest
        assert_preserved(before)
        print(
            "PUBLICATION FAILURE PRESERVED",
            result.detail,
            "zero irreversible events",
            flush=True,
        )
        state["phase"] = "cancel-after-failure"
        return
    if phase == "accept":
        if value(sa, "close_marker") != "A" or value(sb, "close_marker") != "B":
            return
        before = docs.persistence_snapshot()
        state["durable_documents"] = before["documents"]
        state["a_views"] = {
            identity: record
            for identity, record in before["views"].items()
            if record["workspace_id"] == str(a.identity)
        }
        state["a_placements"] = {
            str(docs.view_identity(editor)): placement(editor)
            for editor in (state["ea"], state["ua"])
        }
        state["b_shell_state"] = service.router.shell_state(
            service._shells[sb].identity
        )
        state["b_assignment"] = service.selection_targets(state["eb"])
        state["b_context"] = sb._context
        state["b_layout"] = deepcopy(b.model.serialize_layout())
        choose("terminate")
        count = len(state["choices"])
        result = pyzo.application.workspaces.close(a.identity)
        assert result.applied, result
        assert not result.cleanup_errors, result.cleanup_errors
        assert len(state["choices"]) == count + 1
        assert sum(event[0] == "terminate" for event in state["events"]) == 1
        assert sum(event[0] == "shell-close" for event in state["events"]) == 1
        assert sum(event[0] == "editor-unbind" for event in state["events"]) == len(
            state["a_views"]
        ), state["events"]
        assert a.identity not in pyzo.application.workspaces.identities
        assert sa not in service._shells
        assert not service.provenance_is_current(state["old_a"])
        assert service.provenance_is_current(state["old_b"])
        assert state["ea"] not in docs._editors and state["ua"] not in docs._editors
        assert b.model.serialize_layout() == state["b_layout"]
        print("DURABLE BEFORE TEARDOWN", state["events"], flush=True)
        sb.executeCommand("after_close = close_marker + '-survived'\n")
        state["phase"] = "process-exit"
        return
    if phase == "process-exit":
        if (
            state["processes"][0].poll() is None
            or value(sb, "after_close") != "B-survived"
        ):
            return
        assert state["processes"][1].poll() is None
        assert value(sb, "__import__('os').getpid()") == state["pids"][1]
        assert sb._context is state["b_context"]
        assert (
            service.router.shell_state(service._shells[sb].identity)
            == state["b_shell_state"]
        )
        assert service.selection_targets(state["eb"]) == state["b_assignment"]
        write(state["shared"], "# edited in B while A suspended\n")
        state["shared_record"] = deepcopy(
            docs.persistence_snapshot()["documents"][
                str(docs.identity(state["shared"]))
            ]
        )
        print(
            "A PROCESS EXITED",
            state["pids"][0],
            "B SAME LIVE PID",
            state["pids"][1],
            flush=True,
        )
        result = pyzo.application.workspaces.reopen(a.identity)
        assert result.applied, result
        state["phase"] = "reopened"
        return
    if phase == "reopened":
        assert not window._peerWorkspaces.context_is_current(state["old_workspace"])
        assert not docs.registry.token_is_current(state["old_view"])
        assert str(a.identity) not in window._peerWorkspaceRestoreFailures
        views = {
            str(docs.view_identity(editor)): editor
            for editor in docs._editors
            if docs.registry.view(docs.view_identity(editor)).workspace_id == a.identity
        }
        assert set(views) == set(state["a_views"]), (views, state["a_views"])
        for identity, record in state["a_views"].items():
            editor = views[identity]
            assert str(docs.identity(editor)) == record["document_id"]
            expected = state["durable_documents"][record["document_id"]]
            if expected["path"]:
                expected = state["shared_record"]
            assert editor.toPlainText() == expected["text"]
            assert editor.document().isModified()
            actual = docs.persistence_snapshot()["documents"][record["document_id"]]
            assert (
                actual["undo"] == expected["undo"]
                and actual["clean_text"] == expected["clean_text"]
            )
            current_placement = placement(editor)
            assert current_placement.workspace_id == a.identity
            assert current_placement.frame_id and current_placement.group_id
            old = state["a_placements"][identity]
            assert (current_placement.frame_id, current_placement.group_id) == (
                old.frame_id,
                old.group_id,
            )
            view_state = record["state"]
            assert (
                editor.textCursor().selectionStart(),
                editor.textCursor().selectionEnd(),
            ) == tuple(view_state["selection"])
            assert editor.verticalScrollBar().value() == view_state["scroll"]
            assert (
                service.selection_targets(editor).assignment.mode
                is AssignmentMode.IMPLICIT
            )
            assert actual["undo"] and editor.undo()
            assert editor.toPlainText() == actual["undo"][-1]
            assert editor.redo() and editor.toPlainText() == expected["text"]
        for left, old_left in state["a_placements"].items():
            for right, old_right in state["a_placements"].items():
                new_left, new_right = placement(views[left]), placement(views[right])
                assert (old_left.frame_id == old_right.frame_id) == (
                    new_left.frame_id == new_right.frame_id
                )
                assert (old_left.group_id == old_right.group_id) == (
                    new_left.group_id == new_right.group_id
                )
        assert not any(
            binding.workspace_id == a.identity for binding in service._shells.values()
        )
        assert sa not in service._shells
        assert service.provenance_is_current(state["old_b"])
        assert (
            sb._context is state["b_context"] and state["processes"][1].poll() is None
        )
        assert service.selection_targets(state["eb"]) == state["b_assignment"]
        assert [
            (directory / f"{label}.py").read_bytes() for label in ("a", "b")
        ] == state["bytes"]
        print(
            "WORKSPACE CLOSE COMPLETE: cancel/failure/retry; durable dirty text/undo/views before A-only termination; actual A exit; B same kernel/assignment; retained shared reopen; source bytes preserved",
            flush=True,
        )
        state["phase"] = "done"
        choose("terminate")
        pyzo.application.lifecycle.quit()


def guarded_tick():
    try:
        phase = state["phase"]
        if phase != state.get("observed_phase"):
            state["observed_phase"] = phase
            state["phase_started"] = time.monotonic()
            print("WORKSPACE CLOSE PHASE", phase, flush=True)
        assert time.monotonic() - state["phase_started"] < 12, phase
        tick()
    except Exception:
        traceback.print_exc()
        timer.stop()
        pyzo.localKernelManager.terminateAll()
        QtWidgets.qApp.exit(1)


original_init = MainWindow.__init__


def init_and_probe(self, *args, **kwargs):
    global window, timer
    original_init(self, *args, **kwargs)
    window = self
    timer = QtCore.QTimer(self)
    timer.timeout.connect(guarded_tick)
    timer.start(100)


MainWindow.__init__ = init_and_probe
pyzo._start.start()
