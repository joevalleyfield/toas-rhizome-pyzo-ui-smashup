"""Real-kernel workspace Cancel, failed publication, termination and resume."""

from __future__ import annotations

from copy import deepcopy
import os
import json
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
from spikes.peer_frames.execution_routing import ExecutionCommand

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
    assert records["extensions"]["workspace_breakpoints"] == state["overlays"]
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


def foreground(shell):
    host = next(host for host in pyzo.shells.hosts if shell in host.getShells())
    host._stack.setCurrentWidget(shell)
    window._onFocusedDockWidgetChanged(
        window._peerRuntimeForShellHost(host).shell_hosts[host]
    )
    assert pyzo.shells.getCurrentShell() is shell
    pyzo.application.workspace_execution.foreground_shell(shell)
    host.onShellDebugStateChange(shell)
    return host


def mode(shell):
    return (shell._debugState or {}).get("debugmode", 0)


def command(shell, name):
    foreground(shell)
    assert pyzo.shellCommands.invoke("shell.debug.control." + name)


def dialog_cancel(shell):
    foreground(shell)
    timer.stop()
    seen = []

    def answer():
        dialog = next(
            widget
            for widget in QtWidgets.QApplication.topLevelWidgets()
            if isinstance(widget, QtWidgets.QMessageBox) and widget.isVisible()
        )
        seen.append(dialog.informativeText())
        assert "interpreter" in seen[-1] and "stack" in seen[-1], seen
        if mode(shell) == 1:
            assert "Postmortem" in seen[-1], seen
        dialog.button(QtWidgets.QMessageBox.StandardButton.Cancel).click()

    QtCore.QTimer.singleShot(50, answer)
    result = window._askPeerShellClose(
        window._peerShellLifecycles._shells[
            pyzo.application.workspace_execution._shells[shell].pane_id
        ].lifecycle
    )
    timer.start(100)
    assert result == "cancel" and seen
    print("VISIBLE STACK LOSS WARNING", seen, flush=True)


class Held:
    def __init__(self, future, receipt, epoch):
        self.future, self.receipt, self.epoch, self.callbacks = (
            future,
            receipt,
            epoch,
            [],
        )

    def add_done_callback(self, callback):
        self.callbacks.append(callback)

    def __getattr__(self, name):
        return getattr(self.future, name)

    def release(self):
        assert self.future.done() and not self.future.exception()
        for callback in self.callbacks:
            callback(self)


def held_query(shell):
    from pyzo.core.nativeRequests import request

    original = shell._request.requestWithProvenance
    captured, writes = [], []

    def hold(receipt, epoch, method, args):
        future = Held(original(receipt, epoch, method, args), receipt, epoch)
        captured.append(future)
        return future

    shell._request.requestWithProvenance = hold
    consumer = types.SimpleNamespace()
    try:
        request(
            shell,
            ExecutionCommand.TOOL,
            consumer,
            "evalMultiple",
            [["local_owner"]],
            lambda reply: writes.append(reply.result()),
        )
    finally:
        shell._request.requestWithProvenance = original
    assert len(captured) == 1
    return captured[0], writes, original, consumer


SOURCE = "def stage5_function():\n    local_owner = owner_marker\n    first = 1\n    second = 2\n    return local_owner + str(first + second)\n\nstage5_result = stage5_function()\n"
ERROR = "def stage5_failure():\n    local_owner = owner_marker\n    raise RuntimeError(local_owner)\n\nstage5_failure()\n"


def tick():
    docs, service = pyzo.application.documents, pyzo.application.workspace_execution
    debugging = pyzo.application.workspace_debugging
    phase = state["phase"]
    if os.environ.get("PYZO_WORKSPACE_SET_PHASE") == "debugger-restore":
        expected = json.loads((directory / "debugger-expected.json").read_text())
        editors = [
            editor
            for editor in docs._editors
            if str(docs.identity(editor)) == expected["document"]
        ]
        actual = {
            str(docs.registry.view(docs.view_identity(editor)).workspace_id): sorted(
                editor.breakPoints(True)
            )
            for editor in editors
        }
        assert actual == {
            owner: [tuple(entry) for entry in entries]
            for owner, entries in expected["entries"].items()
        }, actual
        assert all(
            editor.toPlainText() == expected["text"] and editor.document().isModified()
            for editor in editors
        )
        assert all(
            not mode(shell) and not getattr(shell, "_workspaceBreakpointSnapshot", None)
            for shell in service._shells
        )
        assert (
            docs.persistence_snapshot()["extensions"]["workspace_breakpoints"]
            == expected["overlays"]
        )
        print(
            "WORKSPACE DEBUGGER RESTART COMPLETE: durable independent enabled/disabled overlays, dirty shared identity; no interpreter or captured stack revival",
            flush=True,
        )
        state["phase"] = "done"
        choose("terminate")
        pyzo.application.lifecycle.quit()
        return
    if phase == "initial":
        sa = pyzo.shells.getCurrentShell()
        if sa is None or not ready(sa):
            return
        a, ea = window._peerActiveRuntime(), pyzo.editors.getCurrentEditor()
        write(ea, SOURCE)
        ea.document().setModified(True)
        assert pyzo.editors.saveFile(ea, str(directory / "source.py"))
        ua = pyzo.editors.newFile().editor
        write(ua, "retained while debugging\n")
        b_id = pyzo.application.workspaces.create("Debugger peer B")
        b = window._peerRuntimeCatalog.runtime(b_id)
        sb = pyzo.shells.addShell()
        shared = window._peerMainEditor(docs.identity(ea), b.identity)
        ea.toggleBreakpoint(3)
        shared.toggleBreakpoint(4)
        assert ea.breakPoints() == [3] and shared.breakPoints() == [4]
        state.update(
            a=a,
            b=b,
            ea=ea,
            eb=shared,
            shared=shared,
            ua=ua,
            sa=sa,
            sb=sb,
            path=ea.filename,
            baseline=(directory / "source.py").read_bytes(),
            phase="seed",
        )
        return
    a, b, sa, sb, ea, eb = (state[key] for key in ("a", "b", "sa", "sb", "ea", "eb"))
    if phase == "seed":
        if not ready(sb):
            return
        if not state.get("seeded"):
            sa.executeCommand("owner_marker = 'A'\n")
            sb.executeCommand("owner_marker = 'B'\n")
            state["seeded"] = True
            return
        if value(sa, "owner_marker") != "A" or value(sb, "owner_marker") != "B":
            return
        pids = [value(shell, "__import__('os').getpid()") for shell in (sa, sb)]
        assert len(set(pids)) == 2
        state.update(
            pids=pids,
            processes=[
                next(
                    kernel._process
                    for kernel in pyzo.localKernelManager._kernels
                    if getattr(kernel._process, "pid", None) == pid
                )
                for pid in pids
            ],
            shell_owners={sa: a.identity, sb: b.identity},
        )
        for editor, shell in ((ea, sa), (eb, sb)):
            foreground(shell)
            assert service.assign_selection(editor, shell).applied
            pyzo.runCommands.run_file((False, False), editor)
        state["phase"] = "both-live"
        return
    if phase == "both-live":
        if mode(sa) != 2 or mode(sb) != 2:
            return
        assert sa._debugState["frames"][-1][1] == 3, sa._debugState
        assert sb._debugState["frames"][-1][1] == 4, sb._debugState
        assert value(sa, "local_owner") == "A" and value(sb, "local_owner") == "B"
        assert sa._debugState["session_id"] != sb._debugState["session_id"]
        state["a_live"] = deepcopy(sa._debugState)
        ea.toggleBreakpoint(5)
        assert sa._workspaceBreakpointSnapshot == {state["path"]: [3]}
        assert debugging.overlays.project(a.identity) == {state["path"]: [3, 5]}
        assert eb.breakPoints() == [4]
        cursor = ea.textCursor()
        cursor.setPosition(0)
        cursor.insertText("# shifted shared source\n")
        docs.flush(ea)
        assert sorted(ea.breakPoints()) == [4, 6] and eb.breakPoints() == [5], (
            ea.breakPoints(),
            eb.breakPoints(),
        )
        assert sa._workspaceBreakpointSnapshot == {state["path"]: [3]}
        assert sb._workspaceBreakpointSnapshot == {state["path"]: [4]}
        assert ea.undo()
        docs.flush(ea)
        assert sorted(ea.breakPoints()) == [3, 5] and eb.breakPoints() == [4], (
            ea.breakPoints(),
            eb.breakPoints(),
        )
        foreground(sa)
        host = next(host for host in pyzo.shells.hosts if sa in host.getShells())
        state["held_action"] = host._dbs.menu().actions()[0]
        foreground(sb)
        host._dbs.onTriggered(state["held_action"])
        assert sa._debugState == state["a_live"]
        state["query"] = held_query(sb)
        state["b_action"] = (
            next(host for host in pyzo.shells.hosts if sb in host.getShells())
            ._dbs.menu()
            .actions()[0]
        )
        state["phase"] = "held-query-ready"
        print(
            "INDEPENDENT LIVE BREAKPOINTS; FIXED ACTIVE SNAPSHOT; STALE FOREIGN STACK ACTION REJECTED",
            state["pids"],
            flush=True,
        )
        return
    if phase == "held-query-ready":
        if not state["query"][0].done():
            return
        assert not state["query"][0].exception()
        command(sb, "next")
        state["phase"] = "b-next"
        return
    if phase == "b-next":
        if sb._debugState["frames"][-1][1] != 5:
            return
        assert sa._debugState == state["a_live"]
        held, writes, original, _consumer = state["query"]
        held.release()
        assert not writes
        host = foreground(sb)
        sent, execute = [], sb.executeCommand
        sb.executeCommand = sent.append
        try:
            host._dbs.onTriggered(state["b_action"])
        finally:
            sb.executeCommand = execute
        assert not sent
        state["stale_query"] = original(
            held.receipt,
            held.epoch,
            "evalMultiple",
            [
                [
                    "__import__('sys')._pyzoInterpreter._main_locals.__setitem__('stale_side_effect', True)"
                ]
            ],
        )
        state["phase"] = "stale-kernel-query"
        return
    if phase == "stale-kernel-query":
        if not state["stale_query"].done():
            return
        assert state["stale_query"].exception()
        assert (
            value(
                sb,
                "'stale_side_effect' in __import__('sys')._pyzoInterpreter._main_locals",
            )
            is False
        )
        print(
            "STALE FRAME ACTION/HELD RESULT REJECTED; KERNEL REJECTED STALE QUERY BEFORE EVALUATION",
            flush=True,
        )
        command(sb, "stop")
        state["phase"] = "b-idle"
        return
    if phase == "b-idle":
        if mode(sb) or not ready(sb):
            return
        foreground(sb)
        assert not pyzo.shellCommands.invoke("shell.debug.control.next")
        assert sa._debugState == state["a_live"]
        command(sa, "stop")
        state["phase"] = "fail-both"
        return
    if phase == "fail-both":
        if mode(sa) or not ready(sa):
            return
        debugging.clear(a.identity)
        debugging.clear(b.identity)
        write(ea, ERROR)
        for editor, shell in ((ea, sa), (eb, sb)):
            if shell is sb:
                logged = (
                    ERROR.rsplit("stage5_failure()", 1)[0]
                    + "try:\n    stage5_failure()\nexcept RuntimeError:\n    import logging\n    logging.getLogger('owned-stage5').error('captured exception', exc_info=True)\n"
                )
                write(ea, logged)
            foreground(shell)
            pyzo.runCommands.run_file((False, False), editor)
        state["phase"] = "tracebacks"
        return
    if phase == "tracebacks":
        if not all(
            getattr(shell, "_workspaceTracebackReceipt", None) and ready(shell)
            for shell in (sa, sb)
        ):
            return
        for shell in (sa, sb):
            foreground(shell)
            assert pyzo.shellCommands.invoke("shell.debug.start")
        state["phase"] = "both-postmortem"
        return
    if phase == "both-postmortem":
        if mode(sa) != 1 or mode(sb) != 1:
            return
        assert value(sa, "local_owner") == "A" and value(sb, "local_owner") == "B"
        for shell in (sa, sb):
            foreground(shell)
            for name in ("next", "step", "return", "jump", "continue"):
                assert not pyzo.shellCommands.invoke("shell.debug.control." + name)
            shell.executeCommand("frame_mutation = local_owner + '-PM'\n")
        state["phase"] = "pm-executable"
        return
    if phase == "pm-executable":
        if (
            value(sa, "frame_mutation") != "A-PM"
            or value(sb, "frame_mutation") != "B-PM"
        ):
            return
        dialog_cancel(sb)
        state["b_pm"] = deepcopy(sb._debugState)
        state["b_context"] = sb._context
        state["b_assignment"] = service.selection_targets(eb)
        command(sa, "stop")
        state["phase"] = "live-and-pm"
        print("TWO EXECUTABLE POSTMORTEM CONTEXTS; CONTINUE/STEP DISABLED", flush=True)
        return
    if phase == "live-and-pm":
        if mode(sa) or not ready(sa):
            return
        write(ea, SOURCE)
        ea.toggleBreakpoint(3)
        ea.toggleBreakpoint(5)
        eb.toggleBreakpoint(4)
        foreground(sa)
        pyzo.runCommands.run_file((False, False), ea)
        state["phase"] = "cancel-debug"
        return
    if phase == "cancel-debug":
        if mode(sa) != 2:
            return
        assert sa._debugState["frames"][-1][1] == 3
        assert sa._workspaceBreakpointSnapshot == {state["path"]: [3, 5]}
        assert sb._debugState == state["b_pm"]
        write(ea, SOURCE + "# retained dirty shared source\n")
        ea.toggleBreakpoint(2)
        ea.toggleBreakpoint(2)
        assert sorted(ea.breakPoints(True)) == [(2, False), (3, True), (5, True)]
        dialog_cancel(sa)
        state["debug_at_close"] = deepcopy(sa._debugState)
        window._peerRetentionCoordinator.edit()
        assert window._peerRetentionCoordinator.flush()
        install_observers()
        state["phase"] = "cancel"
        return
    if phase in {"cancel", "cancel-after-failure", "fail-publication"}:
        before = live_snapshot()
        debug_before = [deepcopy(shell._debugState) for shell in (sa, sb)]
        manifest = (
            window._peerWorkspaceStore.manifest.read_bytes()
            if window._peerWorkspaceStore.manifest.exists()
            else None
        )
        original = workspace_persistence.os.replace

        def fail(source, destination):
            if Path(destination) == window._peerWorkspaceStore.manifest:
                raise OSError("owned debugger retention failure")
            return original(source, destination)

        choose("terminate" if phase == "fail-publication" else "cancel")
        if phase == "fail-publication":
            workspace_persistence.os.replace = fail
        try:
            result = pyzo.application.workspaces.close(a.identity)
        finally:
            workspace_persistence.os.replace = original
        assert not result.applied, result
        if manifest is not None:
            assert window._peerWorkspaceStore.manifest.read_bytes() == manifest
        assert_preserved(before)
        assert [shell._debugState for shell in (sa, sb)] == debug_before
        assert value(sa, "local_owner") == "A" and value(sb, "frame_mutation") == "B-PM"
        print("DEBUG CLOSE PRESERVED", phase, "zero teardown", flush=True)
        state["phase"] = {
            "cancel": "fail-publication",
            "fail-publication": "cancel-after-failure",
            "cancel-after-failure": "accept",
        }[phase]
        return
    if phase == "accept":
        before = docs.persistence_snapshot()
        state["durable_documents"] = before["documents"]
        state["a_views"] = {
            identity: record
            for identity, record in before["views"].items()
            if record["workspace_id"] == str(a.identity)
        }
        state["overlays"] = deepcopy(before["extensions"]["workspace_breakpoints"])
        choose("terminate")
        result = pyzo.application.workspaces.close(a.identity)
        assert result.applied and not result.cleanup_errors, result
        persisted = window._peerWorkspaceStore.load().state.shared_resources
        assert persisted["extensions"]["workspace_breakpoints"] == state["overlays"]
        assert sum(event[0] == "terminate" for event in state["events"]) == 1
        assert sb._debugState == state["b_pm"] and sb._context is state["b_context"]
        print(
            "DEBUG OVERLAYS/TEXT/UNDO/VIEWS DURABLE BEFORE A-ONLY TEARDOWN",
            state["events"],
            flush=True,
        )
        sb.executeCommand("after_close = frame_mutation + '-survived'\n")
        state["phase"] = "process-exit"
        return
    if phase == "process-exit":
        if (
            state["processes"][0].poll() is None
            or value(sb, "after_close") != "B-PM-survived"
        ):
            return
        assert state["processes"][1].poll() is None
        assert value(sb, "__import__('os').getpid()") == state["pids"][1]
        assert sb._debugState == state["b_pm"]
        assert service.selection_targets(eb) == state["b_assignment"]
        result = pyzo.application.workspaces.reopen(a.identity)
        assert result.applied, result
        state["phase"] = "resumed"
        return
    if phase == "resumed":
        views = {
            str(docs.view_identity(editor)): editor
            for editor in docs._editors
            if docs.registry.view(docs.view_identity(editor)).workspace_id == a.identity
        }
        assert set(views) == set(state["a_views"])
        resumed = next(
            editor
            for editor in views.values()
            if docs.identity(editor) == docs.identity(eb)
        )
        assert resumed.breakPoints() == [3, 5] and eb.breakPoints() == [4]
        assert not any(
            binding.workspace_id == a.identity for binding in service._shells.values()
        )
        assert sb._debugState == state["b_pm"]
        assert (directory / "source.py").read_bytes() == state["baseline"]
        assert window._savePeerWorkspacePersistence()
        expected = dict(
            document=str(docs.identity(eb)),
            text=eb.toPlainText(),
            entries={
                str(a.identity): sorted(resumed.breakPoints(True)),
                str(b.identity): sorted(eb.breakPoints(True)),
            },
            overlays=docs.persistence_snapshot()["extensions"]["workspace_breakpoints"],
        )
        (directory / "debugger-expected.json").write_text(json.dumps(expected))
        print(
            "WORKSPACE DEBUGGER COMPLETE: independent overlays; two live and two executable PM contexts; frozen session; foreground controls; cancel/failure/retry; retained A-only termination; B same live PM PID; resume overlays",
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
            print("WORKSPACE DEBUGGER PHASE", phase, flush=True)
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
