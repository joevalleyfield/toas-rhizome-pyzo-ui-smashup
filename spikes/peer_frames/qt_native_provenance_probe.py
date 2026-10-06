"""Native callbacks and operation envelopes in two workspace-owned kernels."""

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


def value(shell, expression):
    return shell._request.eval(expression).result_or_cancel(0.2)


class Held:
    def __init__(self, future):
        self.future, self.callbacks = future, []

    def add_done_callback(self, callback):
        self.callbacks.append(callback)

    def __getattr__(self, name):
        return getattr(self.future, name)

    def release(self):
        assert self.future.done() and not self.future.exception()
        for callback in self.callbacks:
            callback(self)


def hold(shell):
    original = shell._request.requestWithProvenance
    held = []

    def send(*args):
        future = Held(original(*args))
        held.append(future)
        return future

    shell._request.requestWithProvenance = send
    return held, original


def source(editor, text):
    editor.setPlainText(text)
    cursor = editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    editor.setTextCursor(cursor)


def auto(editor, names):
    from pyzo.core.baseTextCtrl import AutoCompObject

    aco = AutoCompObject(editor, "owned_obj", "")

    original_buffer = aco.setBuffer

    def set_buffer(*args, **kwargs):
        result = original_buffer(*args, **kwargs)
        if "append" in result:
            names.append(result)
        return result

    aco.setBuffer = set_buffer
    aco.finish = lambda: (
        state.setdefault("popups", []).append("completion"),
        aco.setBuffer(),
    )
    editor._autoCompBuffer_time = 0
    editor.processAutoComp(aco)
    return aco


def tick():
    from pyzo.core.baseTextCtrl import CallTipObject
    from pyzo.core.nativeRequests import wire_receipt
    from pyzo.tools.pyzoWorkspace import WorkspaceProxy
    from pyzo.tools.pyzoExpressionViewer import ExpressionProxy

    phase = state["phase"]
    if phase == "initial":
        sa = pyzo.shells.getCurrentShell()
        if sa is None or not ready(sa):
            return
        a, ea = window._peerActiveRuntime(), pyzo.editors.getCurrentEditor()
        b_id = pyzo.application.workspaces.create("Provenance B")
        b = window._peerRuntimeCatalog.runtime(b_id)
        eb, sb = pyzo.editors.getCurrentEditor(), pyzo.shells.addShell()
        state.update(phase="ready", sa=sa, sb=sb, a=a, b=b, ea=ea, eb=eb)
        return
    sa, sb, ea, eb = (state[name] for name in ("sa", "sb", "ea", "eb"))
    service = pyzo.application.workspace_execution
    if phase == "ready":
        if not ready(sb):
            return
        for label, editor in (("a", ea), ("b", eb)):
            source(editor, "# saved baseline\n")
            editor.document().setModified(True)
            assert pyzo.editors.saveFile(editor, str(directory / (label + ".py")))
        source(
            ea,
            'owned_obj = []\ndef owned_function(a_only):\n    """A documentation."""\n    return a_only\n',
        )
        source(
            eb,
            'owned_obj = {"b": 2}\ndef owned_function(b_only, another):\n    """B documentation."""\n    return b_only\n',
        )
        focus_shell(sa)
        focus_shell(sb)
        state["pa"] = pyzo.runCommands.run_file((False, False), ea)
        state["pb"] = pyzo.runCommands.run_file((False, False), eb)
        state["phase"] = "queries"
        return
    if phase == "queries":
        if (
            value(sa, "type(owned_obj).__name__") != "list"
            or value(sb, "type(owned_obj).__name__") != "dict"
        ):
            return
        for shell, token in ((sa, state["pa"]), (sb, state["pb"])):
            if not any(
                item["receipt"] == wire_receipt(token) and item["phase"] == "complete"
                for item in shell._workspaceResults
            ):
                return
        source(ea, "owned_obj.")
        state["names"], state["tips"], state["docs"] = [], [], []
        auto(ea, state["names"])
        cto = CallTipObject(ea, "owned_function", 0)

        original_buffer = cto.setBuffer

        def set_buffer(text, *args, **kwargs):
            original_buffer(text, *args, **kwargs)
            if "a_only" in text:
                state["tips"].append(text)

        cto.setBuffer = set_buffer
        cto.finish = lambda text: (
            state.setdefault("popups", []).append("calltip"),
            cto.setBuffer(text),
        )
        sa.processCallTip(cto)
        pyzo.toolManager.loadTool("pyzointeractivehelp")
        hw = pyzo.toolManager.getTool("pyzointeractivehelp")
        assert hw is not None
        hw.displayResponse = state["docs"].append
        hw.setObjectName("owned_function", requestSource=ea)
        state["hw"] = hw
        parent = QtWidgets.QWidget()
        proxy = WorkspaceProxy(parent)
        expression = ExpressionProxy(parent)
        expression.setExpressions(["len(owned_obj)"])
        expression.evaluateExpressions()
        state.update(
            phase="first-results", proxy=proxy, expression=expression, parent=parent
        )
        return
    if phase == "first-results":
        if (
            not state["names"]
            or not state["tips"]
            or not state["docs"]
            or not state["expression"]._response
        ):
            return
        assert "append" in state["names"][0] and "keys" not in state["names"][0]
        assert "a_only" in state["tips"][0] and "b_only" not in state["tips"][0]
        assert (
            "A documentation." in state["docs"][0]
            and "B documentation." not in state["docs"][0]
        )
        assert any(item[0] == "owned_obj" for item in state["proxy"]._variables)
        assert state["expression"]._response[0] == ("len(owned_obj)", True, "1")
        assert not state.get("popups"), state.get("popups")
        held, original = hold(sb)
        state["proxy"].setName("owned_obj")
        state["proxy"].setName("")
        state.update(phase="tool-order", held_b=held, original_b=original)
        return
    if phase == "tool-order":
        if len(state["held_b"]) < 2 or not all(
            future.done() for future in state["held_b"]
        ):
            return
        state["held_b"][-1].release()
        variables = list(state["proxy"]._variables)
        assert any(item[0] == "owned_obj" for item in variables)
        state["held_b"][-2].release()
        assert state["proxy"]._variables == variables
        sb._request.requestWithProvenance = state["original_b"]
        held, original = hold(sa)
        auto(ea, state["names"])
        state.update(phase="hold-edit", held=held, original=original)
        return
    if phase == "hold-edit":
        if not state["held"] or not state["held"][-1].done():
            return
        before = len(state["names"])
        cached = list(ea._autoCompBuffer_result)
        source(ea, "owned_obj.changed")
        state["held"][-1].release()
        assert len(state["names"]) == before and ea._autoCompBuffer_result == cached
        source(ea, "owned_obj.")
        auto(ea, state["names"])
        state["phase"] = "hold-restart"
        return
    if phase == "hold-restart":
        if not state["held"][-1].done():
            return
        state["stale"] = state["held"][-1]
        state["old_result"] = dict(sa._workspaceResults[-1])
        state["old_token"] = service.resolve_selection(ea).provenance
        sa.restart()
        state["phase"] = "recycled"
        return
    if phase == "recycled":
        if not ready(sa):
            return
        fresh = service.resolve_selection(ea).provenance
        assert fresh.kernel_generation_id != state["old_token"].kernel_generation_id
        before = len(state["names"])
        state["stale"].release()
        assert len(state["names"]) == before
        assert not sa._consumeWorkspaceResult(state["old_result"])
        sa._request.requestWithProvenance = state["original"]
        # New-generation direct command and debugger command both echo receipts.
        sa._ctrl_operation.send(
            {
                "kind": "command",
                "payload": "retired_transport_executed = True\n",
                "epoch": state["old_result"]["epoch"],
                "receipt": state["old_result"]["receipt"],
            }
        )
        state["retired_query"] = sa._request.requestWithProvenance(
            state["old_result"]["receipt"],
            state["old_result"]["epoch"],
            "dir",
            ["owned_obj"],
        )
        sa.executeCommand("owned_obj = [42]\n")
        sa.executeCommand("DB STOP\n")
        state["phase"] = "new-generation"
        return
    if phase == "new-generation":
        if value(sa, "owned_obj") != [42] or not state["retired_query"].done():
            return
        assert state["retired_query"].exception()
        assert value(sa, "'retired_transport_executed' in globals()") is False
        if not any(
            item["receipt"]["command"] == "debugger" and item["phase"] == "complete"
            for item in sa._workspaceResults
        ):
            return
        held, original = hold(sa)
        source(ea, "owned_obj.")
        auto(ea, state["names"])
        state.update(phase="hold-close", held=held, original=original)
        return
    if phase == "hold-close":
        if not state["held"][-1].done():
            return
        before = len(state["names"])
        window._peerDirtyCloseChooser = lambda *_: "discard"
        assert pyzo.editors.closeFile(ea)
        state["held"][-1].release()
        assert len(state["names"]) == before
        assert (directory / "a.py").read_text() == "# saved baseline\n"
        assert (directory / "b.py").read_text() == "# saved baseline\n"
        print(
            "NATIVE PROVENANCE COMPLETE: actual two-kernel completion/signature/help/tool requests, Run/debugger wire receipts, held source-edit/recycle/closed-view results rejected; source bytes preserved",
            flush=True,
        )
        state["phase"] = "done"
        window._peerShellCloseChooser = lambda *_: "terminate"
        pyzo.application.lifecycle.quit()


def guarded_tick():
    try:
        phase = state["phase"]
        if phase != state.get("observed_phase"):
            state["observed_phase"] = phase
            state["phase_started"] = time.monotonic()
            print("PROVENANCE PHASE", phase, flush=True)
        if time.monotonic() - state["phase_started"] > 12:
            shells = [state[name] for name in ("sa", "sb") if name in state]
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
