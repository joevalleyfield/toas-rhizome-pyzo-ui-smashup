"""Real Run-menu assignments, broken-target correction and kernel generations."""

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
from spikes.peer_frames.contract import Direction
from spikes.peer_frames.execution_routing import AssignmentMode, RoutingStatus

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


from yoton.channels.channels_reqrep import TimeoutError as EvaluationTimeout
from spikes.peer_frames.probe_evaluation import EvaluationPending, EvaluationPoller

evaluations = EvaluationPoller(EvaluationTimeout)


def value(shell, expression):
    return evaluations.value(shell, expression, state["phase"])


def chooser(editor):
    select(editor)
    host = pyzo.editors._group_for_editor(editor)
    runtime = window._peerRuntimeForEditorHost(host)
    frame_id = runtime.model.resolve_active_context().frame_id
    assert frame_id is not None
    frame = runtime.frame_windows[frame_id]
    # Windows/Linux project a menu into each frame; use the invoking editor's
    # frame. Cocoa's menu_bar_for resolves to its shared application menu.
    run = window._peerCommandProjector.menu_bar_for(frame)._menumap["run"]
    from pyzo.core.workspaceContext import context_for

    assert context_for(run).editors.getCurrentEditor() is editor
    run._updateExecutionTarget()
    assert not run._executionTargetAction.isVisible()
    menu = run._selectionTargetMenu
    menu.refresh()
    return menu


def assign(editor, shell):
    service = pyzo.application.workspace_execution
    menu = chooser(editor)
    choices = service.selection_targets(editor).choices
    index = next(index for index, target in enumerate(choices) if target.shell is shell)
    menu.actions()[index + 2].trigger()
    snapshot = service.selection_targets(editor)
    assert snapshot.assignment.mode is AssignmentMode.EXPLICIT
    assert snapshot.assignment.shell_id == service._shells[shell].identity
    menu.refresh()
    assert menu.actions()[index + 2].isChecked()


def tick():
    phase = state["phase"]
    if phase == "initial":
        sa = pyzo.shells.getCurrentShell()
        if sa is None or not ready(sa):
            return
        a = window._peerActiveRuntime()
        ea = pyzo.editors.getCurrentEditor()
        alternate = pyzo.shells.addShell()
        b_id = pyzo.application.workspaces.create("Assignment B")
        b = window._peerRuntimeCatalog.runtime(b_id)
        eb = pyzo.editors.getCurrentEditor()
        sb = pyzo.shells.addShell()
        state.update(
            phase="ready", a=a, b=b, ea=ea, eb=eb, sa=sa, sb=sb, alternate=alternate
        )
        return

    service = pyzo.application.workspace_execution
    a, b = state["a"], state["b"]
    ea, eb, sa, sb, alternate = [
        state[name] for name in ("ea", "eb", "sa", "sb", "alternate")
    ]
    if phase == "ready":
        if not all(ready(shell) for shell in (sa, sb, alternate)):
            return
        for name, editor in (("a", ea), ("b", eb)):
            editor.setPlainText("# saved source\n")
            editor.document().setModified(True)
            assert pyzo.editors.saveFile(editor, str(directory / f"{name}.py"))
        state["bytes"] = [
            (directory / f"{name}.py").read_bytes() for name in ("a", "b")
        ]
        state["counts"] = {shell: count_sends(shell) for shell in (sa, sb, alternate)}
        ea.setPlainText("assigned_value = 11")
        eb.setPlainText("assigned_value = 22")
        assign(ea, sa)
        assign(eb, sb)
        focus_shell(alternate)
        focus_shell(sb)
        pyzo.shells.setExecutionShell(sb)
        select(ea)
        pa = pyzo.runCommands.run_selected()
        assert pa.assignment_mode is AssignmentMode.EXPLICIT
        assert pa.workspace_id == a.identity
        assert (
            len(state["counts"][sa]) == 1
            and not state["counts"][alternate]
            and not state["counts"][sb]
        )
        focus_shell(sb)
        focus_shell(alternate)
        pyzo.shells.setExecutionShell(alternate)
        select(eb)
        pb = pyzo.runCommands.run_selected()
        assert (
            pb.assignment_mode is AssignmentMode.EXPLICIT
            and pb.workspace_id == b.identity
        )
        assert len(state["counts"][sa]) == len(state["counts"][sb]) == 1
        assert not state["counts"][alternate]
        state.update(phase="values", pa=pa, pb=pb)
        return

    if phase == "values":
        if value(sa, "assigned_value") != 11 or value(sb, "assigned_value") != 22:
            return
        assert value(alternate, "'assigned_value' in globals()") is False
        if not state.get("layout_moved"):
            pane = a.backend._pane_id_from_dock(shell_dock(sa))
            editor_pane = a.backend._pane_id_from_dock(
                a.editor_hosts[pyzo.editors._group_for_editor(ea)]
            )
            context = sa._context
            assert a.model.float(pane).applied
            assert a.model.split(pane, editor_pane, Direction.RIGHT).applied
            assert sa._context is context and service.provenance_is_current(state["pa"])
            state["layout_moved"] = True
        state["response"] = evaluations.value(
            sa, "assigned_value", phase, label="after-pane-move"
        )
        assert state["response"] == 11
        sa.restart()
        assert not service.provenance_is_current(state["pa"])
        assert service.resolve_selection(ea).status is RoutingStatus.BROKEN_TARGET
        assert "Execution target" in window._peerStatusState.snapshot.message
        menu = chooser(ea)
        assert "unavailable" in menu.title()
        assert menu.actions()[-1].isChecked() and not menu.actions()[-1].isEnabled()
        before = len(state["counts"][sa])
        assert pyzo.runCommands.run_selected() is None
        assert len(state["counts"][sa]) == before
        state["phase"] = "restart"
        return

    if phase == "restart":
        if not ready(sa):
            return
        fresh = service.resolve_selection(ea).provenance
        assert fresh.assignment_mode is AssignmentMode.EXPLICIT
        assert fresh.shell_id == state["pa"].shell_id
        assert fresh.kernel_generation_id != state["pa"].kernel_generation_id
        accepted = []
        assert not service.accept_result(
            state["pa"], state["response"], accepted.append
        )
        assert service.accept_result(fresh, value(sa, "40 + 2"), accepted.append)
        assert accepted == [42]
        focus_shell(alternate)
        sa._context.close()
        assert service.resolve_selection(ea).status is RoutingStatus.BROKEN_TARGET
        assert not service.dispatch(
            fresh, lambda _: (_ for _ in ()).throw(AssertionError("lost send"))
        )
        assert ready(alternate) and ready(sb)
        assert not pyzo.runCommands.run_selected()
        assert not state["counts"][alternate]
        # Exercise the actual connection lifecycle without changing shell view.
        sa.resetVariables()
        sa.connectToKernel(sa._info)
        state.update(phase="reconnect", old=fresh)
        return

    if phase == "reconnect":
        if not ready(sa):
            return
        reconnected = service.resolve_selection(ea).provenance
        assert reconnected.assignment_mode is AssignmentMode.EXPLICIT
        assert reconnected.shell_id == state["old"].shell_id
        assert reconnected.kernel_generation_id != state["old"].kernel_generation_id
        assert not service.provenance_is_current(state["old"])
        # A second real transport loss is corrected through the actual chooser.
        sa._context.close()
        assert service.resolve_selection(ea).status is RoutingStatus.BROKEN_TARGET
        assert "unavailable" in chooser(ea).title()
        assign(ea, alternate)
        ea.setPlainText("assigned_value = 33")
        select(ea)
        assert (
            pyzo.runCommands.run_selected().assignment_mode is AssignmentMode.EXPLICIT
        )
        state["phase"] = "corrected"
        return

    if phase == "corrected":
        if value(alternate, "assigned_value") != 33 or not ready(alternate):
            return
        menu = chooser(ea)
        menu.actions()[0].trigger()
        assert service.selection_targets(ea).assignment.mode is AssignmentMode.IMPLICIT
        ea.setPlainText("assigned_value = 34")
        select(ea)
        assert (
            pyzo.runCommands.run_selected().assignment_mode is AssignmentMode.IMPLICIT
        )
        state["phase"] = "clear"
        return

    if phase == "clear":
        if value(alternate, "assigned_value") != 34 or not ready(alternate):
            return
        assign(ea, alternate)
        captured = service.resolve_selection(ea).provenance
        focus_shell(sa)  # Ineligible implicit foreground must not block explicit.
        window._peerShellCloseChooser = lambda *_: "cancel"
        assert not alternate.closeShell()
        assert service.provenance_is_current(captured)
        assert service.selection_targets(ea).assignment.mode is AssignmentMode.EXPLICIT
        window._peerShellCloseChooser = lambda *_: "terminate"
        assert alternate.closeShell()
        assert service.selection_targets(ea).assignment.mode is AssignmentMode.IMPLICIT
        assert not service.provenance_is_current(captured)
        assert not service.resolve_selection(ea).resolved
        # B remains independently assigned and receives a later invocation.
        eb.setPlainText("assigned_value = 23")
        select(eb)
        assert (
            pyzo.runCommands.run_selected().assignment_mode is AssignmentMode.EXPLICIT
        )
        state["phase"] = "retire"
        return

    if phase == "retire":
        if value(sb, "assigned_value") != 23 or not ready(sb):
            return
        captured = service.resolve_selection(eb).provenance
        view_id = eb._peerViewIdentity
        window._peerDirtyCloseChooser = lambda *_: "discard"
        assert pyzo.editors.closeFile(eb)
        reopened = window._reopenPeerRetainedView(view_id, workspace_id=b.identity)
        assert reopened is not eb and reopened._peerViewIdentity == view_id
        assert (
            service.selection_targets(reopened).assignment.mode
            is AssignmentMode.IMPLICIT
        )
        assert not service.provenance_is_current(captured)
        assert not service.assign_selection(eb, sb).applied
        assert [
            (directory / f"{name}.py").read_bytes() for name in ("a", "b")
        ] == state["bytes"]
        print(
            "SELECTION ASSIGNMENT COMPLETE: actual namespaces 11/22; menu/sticky/restart/reconnect/broken/correction/clear/close/movement/retire/source controls passed",
            flush=True,
        )
        state["phase"] = "done"
        pyzo.application.lifecycle.quit()


def guarded_tick():
    try:
        phase = state["phase"]
        if phase != state.get("observed_phase"):
            state["observed_phase"] = phase
            state["phase_started"] = time.monotonic()
            print("ASSIGNMENT PHASE", phase, flush=True)
        if time.monotonic() - state["phase_started"] > 12:
            shells = [
                state[name] for name in ("sa", "sb", "alternate") if name in state
            ]
            raise AssertionError(
                (
                    phase,
                    [
                        (shell._state, shell._version, shell._context.connection_count)
                        for shell in shells
                    ],
                )
            )
        tick()
    except EvaluationPending:
        return
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
