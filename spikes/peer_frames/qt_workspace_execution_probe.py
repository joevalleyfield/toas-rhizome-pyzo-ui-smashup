"""Test-owned Qt application and real-kernel Execute Selection proof."""

from __future__ import annotations

import os
import sys
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
from spikes.peer_frames.contract import Direction

state = {"phase": "initial"}
window = None


def ready(shell):
    return (
        shell._version and shell._state == "Ready" and shell._context.connection_count
    )


def shell_host(shell):
    return next(host for host in pyzo.shells.hosts if shell in host.getShells())


def shell_dock(shell):
    host = shell_host(shell)
    return window._peerRuntimeForShellHost(host).shell_hosts[host]


def focus_shell(shell):
    window._onFocusedDockWidgetChanged(shell_dock(shell))


def select(editor):
    host = pyzo.editors._group_for_editor(editor)
    runtime = window._peerRuntimeForEditorHost(host)
    window._onFocusedDockWidgetChanged(runtime.editor_hosts[host])
    assert pyzo.editors.getCurrentEditor() is editor
    cursor = editor.textCursor()
    cursor.select(cursor.SelectionType.Document)
    editor.setTextCursor(cursor)


def count_sends(shell):
    calls = []
    for method in ("executeCode", "executeCommand"):
        original = getattr(shell, method)

        def send(*args, _original=original, _method=method, **kwargs):
            calls.append((_method, args, kwargs))
            return _original(*args, **kwargs)

        setattr(shell, method, send)
    return calls


def value(shell, expression):
    return shell._request.eval(expression).result_or_cancel(0.2)


def tick():
    phase = state["phase"]
    if phase == "initial":
        a_shell = pyzo.shells.getCurrentShell()
        if a_shell is None or not ready(a_shell):
            return
        a = window._peerActiveRuntime()
        a_editor = pyzo.editors.getCurrentEditor()
        b_id = pyzo.application.workspaces.create("Execution B")
        b = window._peerRuntimeCatalog.runtime(b_id)
        b_editor = pyzo.editors.getCurrentEditor()
        b_shell = pyzo.shells.addShell()
        assert window._peerRuntimeForShellHost(shell_host(b_shell)) is b, (
            "B shell created in primary owner"
        )
        state.update(
            phase="two-ready",
            a=a,
            b=b,
            a_editor=a_editor,
            b_editor=b_editor,
            a_shell=a_shell,
            b_shell=b_shell,
        )
        return

    a, b = state["a"], state["b"]
    sa, sb = state["a_shell"], state["b_shell"]
    ea, eb = state["a_editor"], state["b_editor"]
    service = pyzo.application.workspace_execution
    if phase == "two-ready":
        if not ready(sb):
            return
        assert sa._context is not sb._context
        b_pane = b.backend._pane_id_from_dock(shell_dock(sb))
        expected_title = (
            b.model.panes[b_pane].title
            + " · "
            + window._peerWorkspaces.descriptor(b.identity).name
        )
        assert expected_title == shell_dock(sb).windowTitle(), (
            "B shell metadata used primary model"
        )
        for name, editor in (("a", ea), ("b", eb)):
            path = directory / f"{name}.py"
            editor.setPlainText("# saved source\n")
            editor.document().setModified(True)
            assert pyzo.editors.saveFile(editor, str(path))
        state["bytes"] = [
            (directory / f"{name}.py").read_bytes() for name in ("a", "b")
        ]
        ea.setPlainText("owner_value = 101\nonly_a = owner_value + 1\n")
        eb.setPlainText("owner_value = 202")
        state["calls_a"], state["calls_b"] = count_sends(sa), count_sends(sb)
        focus_shell(sa)
        focus_shell(sb)
        pyzo.shells.setExecutionShell(sb)  # Intentionally wrong global target.
        select(ea)
        pa = pyzo.runCommands.run_selected()
        assert pa.workspace_id == a.identity
        assert len(state["calls_a"]) == 1 and not state["calls_b"]
        focus_shell(sb)
        focus_shell(sa)
        pyzo.shells.setExecutionShell(sa)
        select(eb)
        pb = pyzo.runCommands.run_selected()
        assert pb.workspace_id == b.identity
        assert len(state["calls_a"]) == len(state["calls_b"]) == 1
        state.update(phase="values", pa=pa, pb=pb)
        return

    if phase == "values":
        if value(sa, "owner_value") != 101 or value(sb, "owner_value") != 202:
            return
        assert value(sa, "only_a") == 102
        assert value(sb, "'only_a' in globals()") is False
        assert [call[0] for call in state["calls_a"]] == ["executeCode"]
        assert [call[0] for call in state["calls_b"]] == ["executeCommand"]
        empty_id = pyzo.application.workspaces.create("Execution without shell")
        empty_editor = pyzo.editors.getCurrentEditor()
        assert not service.resolve_selection(empty_editor).resolved
        assert (
            "no eligible foreground shell" in window._peerStatusState.snapshot.message
        )
        assert empty_id != a.identity and empty_id != b.identity
        before = (a.model.serialize_layout(), b.model.serialize_layout())
        assert not service.transfer_shell(sb, a.identity).applied
        assert "not supported" in window._peerStatusState.snapshot.message
        assert before == (a.model.serialize_layout(), b.model.serialize_layout())
        pane = a.backend._pane_id_from_dock(shell_dock(sa))
        editor_pane = a.backend._pane_id_from_dock(
            a.editor_hosts[pyzo.editors._group_for_editor(ea)]
        )
        context = sa._context
        assert a.model.float(pane).applied
        assert a.model.split(pane, editor_pane, Direction.RIGHT).applied
        assert sa._context is context
        assert service.provenance_is_current(state["pa"])
        state["future"] = sa._request.eval("owner_value")
        state["old_response"] = state["future"].result_or_cancel(0.2)
        assert state["old_response"] == 101
        sa.restart()
        assert not service.provenance_is_current(state["pa"])
        assert not service.resolve_selection(ea).resolved
        state["phase"] = "restart"
        return

    if phase == "restart":
        if not ready(sa):
            return
        fresh = service.resolve_selection(ea).provenance
        assert fresh.shell_id == state["pa"].shell_id
        assert fresh.kernel_generation_id != state["pa"].kernel_generation_id
        sends = len(state["calls_a"])
        assert not service.dispatch(
            state["pa"], lambda shell: shell.executeCommand("wrong = 1\n")
        )
        assert len(state["calls_a"]) == sends
        received = []
        assert not service.accept_result(
            state["pa"], state["old_response"], received.append
        )
        assert service.accept_result(fresh, value(sa, "40 + 2"), received.append)
        assert received == [42]
        select(ea)
        assert pyzo.runCommands.run_selected().shell_id == fresh.shell_id
        window._activatePeerWorkspace(a.identity)
        newest = pyzo.shells.addShell()
        state.update(phase="loss", newest=newest, fresh=fresh)
        return

    if phase == "loss":
        newest = state["newest"]
        if not ready(newest):
            return
        focus_shell(newest)
        lost = service.resolve_selection(ea).provenance
        assert lost.shell_id != state["fresh"].shell_id
        newest._context.close()  # Actual disconnected transport, older A alive.
        sends = (len(state["calls_a"]), len(state["calls_b"]))
        assert not service.dispatch(
            lost, lambda shell: shell.executeCommand("wrong = 1\n")
        )
        assert not service.resolve_selection(ea).resolved
        assert sends == (len(state["calls_a"]), len(state["calls_b"]))
        assert ready(sa) and ready(sb)
        assert value(sb, "owner_value") == 202
        focus_shell(sa)  # Explicit correction, not a recency fallback.
        captured = service.resolve_selection(ea).provenance
        view_id = ea._peerViewIdentity
        window._peerDirtyCloseChooser = lambda *_: "discard"
        assert pyzo.editors.closeFile(ea)
        assert view_id not in service._documents.view_ids
        assert not service.dispatch(
            captured, lambda shell: shell.executeCommand("wrong = 1\n")
        )
        assert not service.resolve_selection(ea).resolved
        before_b_close = service.resolve_selection(eb).provenance
        b_pane = b.backend._pane_id_from_dock(shell_dock(sb))
        window._peerShellCloseChooser = lambda *_: "terminate"
        assert sb.closeShell()
        assert b_pane not in b.model.panes
        assert not service.provenance_is_current(before_b_close)
        assert not service.resolve_selection(eb).resolved
        assert sa in pyzo.shells.getShells()
        assert [
            (directory / f"{name}.py").read_bytes() for name in ("a", "b")
        ] == state["bytes"]
        print(
            "WORKSPACE EXECUTION COMPLETE: local values 101/202; loss/restart/stale/view/movement/transfer/source controls passed",
            flush=True,
        )
        window._peerShellCloseChooser = lambda *_: "terminate"
        state["phase"] = "done"
        pyzo.application.lifecycle.quit()


def guarded_tick():
    try:
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
