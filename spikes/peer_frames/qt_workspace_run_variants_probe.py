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
from spikes.peer_frames.execution_routing import (
    AssignmentMode,
    ExecutionCommand,
)

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


def assert_receipt(receipt, command, runtime, shell):
    service = pyzo.application.workspace_execution
    assert receipt.command is command and receipt.workspace_id == runtime.identity
    assert receipt.shell_id == service._shells[shell].identity
    assert receipt.process_workspace_id == runtime.identity
    assert (
        receipt.kernel_generation_id
        == service.router.shell_state(receipt.shell_id).kernel_generation_id
    )
    return receipt


def assert_startup_receipt(shell, original, successor):
    from pyzo.core.nativeRequests import wire_receipt

    results = [result for result in shell._workspaceResults
               if result["phase"] == "startup" and result["receipt"] == wire_receipt(original)]
    assert results, shell._workspaceResults
    assert all(result["successor_generation_id"] == str(successor.kernel_generation_id)
               and result["epoch"] == shell._nativeTransportEpoch for result in results)


def designate(editor):
    from pyzo.core.menu import EditorTabContextMenu

    select(editor)
    menu = EditorTabContextMenu(name="Source")
    menu.setIndex(0)
    menu._fileAction("main")
    assert pyzo.editors._tabs.isMainItem(pyzo.editors._tabs.currentItem())
    menu.deleteLater()


def tick():
    phase = state["phase"]
    if phase == "initial":
        sa = pyzo.shells.getCurrentShell()
        if sa is None or not ready(sa):
            return
        a = window._peerActiveRuntime()
        ea = pyzo.editors.getCurrentEditor()
        ma = pyzo.editors.newFile().editor
        b_id = pyzo.application.workspaces.create("Run B")
        b = window._peerRuntimeCatalog.runtime(b_id)
        eb = pyzo.editors.getCurrentEditor()
        sb = pyzo.shells.addShell()
        state.update(phase="ready", a=a, b=b, ea=ea, eb=eb, ma=ma, sa=sa, sb=sb)
        return

    service = pyzo.application.workspace_execution
    a, b = state["a"], state["b"]
    ea, eb, ma, sa, sb = [state[name] for name in ("ea", "eb", "ma", "sa", "sb")]
    if phase == "ready":
        if not all(ready(shell) for shell in (sa, sb)):
            return
        state["counts"] = {shell: count_sends(shell) for shell in (sa, sb)}
        for name, editor in (("a", ea), ("b", eb), ("main-a", ma)):
            editor.setPlainText("# disk baseline\n")
            editor.document().setModified(True)
            assert pyzo.editors.saveFile(editor, str(directory / f"{name}.py"))
        state["bytes"] = [
            (directory / f"{name}.py").read_bytes() for name in ("a", "b", "main-a")
        ]
        ma.useBom = True
        ma.lineEndings = "CRLF"
        ma.setPlainText("# main baseline\n")
        ma.document().setModified(True)
        assert pyzo.editors.saveFile(ma)
        state["bytes"][2] = (directory / "main-a.py").read_bytes()
        ea.setParser("python")
        ea.setPlainText("## first\ncell_value = 101\n## next\nnever_run = 99\n")
        focus_shell(sa)
        focus_shell(sb)
        pyzo.shells.setExecutionShell(sb)
        state["phase"] = "cell"
        return

    if phase == "cell":
        from pyzo.codeeditor.parsers.python_parser import CellCommentToken

        ea.setIndentUsingSpaces(ea.indentUsingSpaces())
        first = ea.document().firstBlock().userData()
        if not state.get("parser_reported"):
            print(
                "CELL PARSER",
                ea.parser().name(),
                None if first is None else [type(t).__name__ for t in first.tokens],
                flush=True,
            )
            state["parser_reported"] = True
        if first is None or not any(
            isinstance(t, CellCommentToken) for t in first.tokens
        ):
            return
        select(ea)
        cursor = ea.textCursor()
        cursor.setPosition(0)
        ea.setTextCursor(cursor)
        receipt = pyzo.runCommands.run_cell(advance=True)
        assert_receipt(receipt, ExecutionCommand.EXECUTE_CELL, a, sa)
        assert ea.textCursor().blockNumber() == 2
        assert not state["counts"][sb]
        state["phase"] = "cell-value"
        return

    if phase == "cell-value":
        if value(sa, "cell_value") != 101:
            return
        assert value(sa, "'never_run' in globals()") is False
        ea.setPlainText("file_value = 102\n")
        eb.setPlainText("file_value = 202\n")
        select(ea)
        assert_receipt(
            pyzo.runCommands.run_file((False, False)),
            ExecutionCommand.EXECUTE_FILE,
            a,
            sa,
        )
        select(eb)
        pyzo.shells.setExecutionShell(sa)
        assert_receipt(
            pyzo.runCommands.run_file((False, False)),
            ExecutionCommand.EXECUTE_FILE,
            b,
            sb,
        )
        state["phase"] = "file-values"
        return

    if phase == "file-values":
        if value(sa, "file_value") != 102 or value(sb, "file_value") != 202:
            return
        ma.setPlainText("main_value = 301\n")
        eb.setPlainText("main_value = 401\n")
        designate(ma)
        designate(eb)
        docs = pyzo.application.documents.registry
        state["main_id"] = ma._peerDocumentIdentity
        assert docs.main(a.identity).document_id == state["main_id"]
        assert docs.main(b.identity).document_id == eb._peerDocumentIdentity
        assert pyzo.editors.closeFile(ma)
        assert not pyzo.application.documents.is_bound(ma)
        count = len(tuple(pyzo.editors))
        select(ea)
        assert_receipt(
            pyzo.runCommands.run_file((False, True)),
            ExecutionCommand.EXECUTE_MAIN,
            a,
            sa,
        )
        assert (
            len(tuple(pyzo.editors)) == count
        )  # Execute retained main does not reopen a view.
        select(eb)
        assert_receipt(
            pyzo.runCommands.run_file((False, True)),
            ExecutionCommand.EXECUTE_MAIN,
            b,
            sb,
        )
        state["phase"] = "main-values"
        return

    if phase == "main-values":
        if value(sa, "main_value") != 301 or value(sb, "main_value") != 401:
            return
        assert [
            (directory / f"{name}.py").read_bytes() for name in ("a", "b", "main-a")
        ] == state["bytes"]
        window._savePeerWorkspacePersistence()
        docs = pyzo.application.documents.registry
        persisted = pyzo.application.documents.persistence_snapshot()
        assert persisted["mains"][str(a.identity)] == str(state["main_id"])
        assert persisted["mains"][str(b.identity)] == str(eb._peerDocumentIdentity)
        # A stale persisted main cannot reassert itself when its native view binds.
        docs.clear_main(a.identity)
        reopened = window._peerMainEditor(state["main_id"], a.identity)
        assert docs.main(a.identity) is None
        docs.set_main(a.identity, state["main_id"])
        assert pyzo.editors.closeFile(reopened)
        # Unavailable main refuses without reading another workspace's main.
        docs.mark_unavailable(state["main_id"])
        select(ea)
        before = [len(state["counts"][s]) for s in (sa, sb)]
        assert pyzo.runCommands.run_file((False, True)) is None
        assert "main" in window._peerStatusState.snapshot.message
        assert before == [len(state["counts"][s]) for s in (sa, sb)]
        # Explicitly relocate the same retained main identity after unavailability.
        (directory / "main-a.py").rename(directory / "main-relocated.py")
        assert docs.rename_document(
            state["main_id"], str(directory / "main-relocated.py")
        ).applied
        # Real File as Script autosaves B and restarts only B.
        eb.setPlainText("script_value = 502\n")
        eb.document().setModified(True)
        select(eb)
        receipt = pyzo.runCommands.run_file((True, False))
        assert receipt.command is ExecutionCommand.RUN_FILE_AS_SCRIPT
        assert (
            receipt.workspace_id == b.identity
            and receipt.shell_id == service._shells[sb].identity
        )
        assert receipt.policy.autosave and receipt.policy.recycle
        assert (directory / "b.py").read_text() == "script_value = 502\n"
        assert not service.provenance_is_current(receipt)
        state.update(phase="file-script", pb=receipt, context_a=sa._context)
        return

    if phase == "file-script":
        if not ready(sb) or value(sb, "script_value") != 502:
            return
        fresh = service.resolve_editor(eb, ExecutionCommand.EXECUTE_FILE).provenance
        assert fresh.shell_id == state["pb"].shell_id
        assert fresh.kernel_generation_id != state["pb"].kernel_generation_id
        assert_startup_receipt(sb, state["pb"], fresh)
        assert sa._context is state["context_a"] and value(sa, "main_value") == 301
        assert value(sb, "'main_value' in globals()") is False
        assert sb._startup_info.get("ipython") != "yes"
        state["phase"] = "main-script"
        return

    if phase == "main-script":
        if not ready(sb):
            return
        select(ea)
        assert service.assign_selection(ea, sa).applied
        receipt = pyzo.runCommands.run_file((True, True))
        assert receipt is not None, (
            window._peerStatusState.snapshot.message,
            service.selection_targets(ea),
            pyzo.application.documents.registry.main(a.identity),
        )
        assert receipt.command is ExecutionCommand.RUN_MAIN_AS_SCRIPT
        assert receipt.assignment_mode is AssignmentMode.EXPLICIT
        assert (
            receipt.shell_id == service._shells[sa].identity
            and receipt.workspace_id == a.identity
        )
        assert receipt.policy.autosave and receipt.policy.recycle
        assert (
            directory / "main-relocated.py"
        ).read_bytes() == b"\xef\xbb\xbfmain_value = 301\r\n"
        assert not service.provenance_is_current(receipt)
        main_editor = window._peerMainEditor(state["main_id"], a.identity, reopen=False)
        assert (
            main_editor is not None
            and main_editor.useBom
            and main_editor.lineEndings == "\r\n"
        )
        assert main_editor.toPlainText() == "main_value = 301\n"
        state.update(phase="main-script-value", pa=receipt)
        return

    if phase == "main-script-value":
        if not ready(sa) or value(sa, "main_value") != 301:
            return
        fresh = service.resolve_editor(ea, ExecutionCommand.EXECUTE_MAIN).provenance
        assert (
            fresh.shell_id == state["pa"].shell_id
            and fresh.kernel_generation_id != state["pa"].kernel_generation_id
        )
        assert fresh.assignment_mode is AssignmentMode.EXPLICIT
        assert_startup_receipt(sa, state["pa"], fresh)
        assert value(sa, "'file_value' in globals()") is False
        assert not service.accept_result(
            state["pa"],
            999,
            lambda _: (_ for _ in ()).throw(AssertionError("stale result")),
        )
        assert (directory / "a.py").read_bytes() == state["bytes"][0]
        assert not any(d.name.endswith("<tmp>") for d in directory.iterdir())
        # Actual native external-change prompt cancellation cannot adopt/save/restart.
        main_editor = window._peerMainEditor(state["main_id"], a.identity, reopen=False)
        docs = pyzo.application.documents.registry
        baseline = docs.resource(state["main_id"])._clean_text
        external = b"# externally replaced main\n"
        (directory / "main-relocated.py").write_bytes(external)
        select(ea)
        original_exec = QtWidgets.QMessageBox.exec
        dialogs = []

        def cancel(dialog):
            dialogs.append(dialog.text())
            return 0

        QtWidgets.QMessageBox.exec = cancel
        try:
            before = service.resolve_editor(
                ea, ExecutionCommand.EXECUTE_MAIN
            ).provenance
            assert pyzo.runCommands.run_file((True, True)) is None
        finally:
            QtWidgets.QMessageBox.exec = original_exec
        assert any("modified outside" in text for text in dialogs), dialogs
        assert any("Could not save the file" in text for text in dialogs), dialogs
        assert service.provenance_is_current(before)
        assert docs.resource(state["main_id"])._clean_text == baseline
        assert (directory / "main-relocated.py").read_bytes() == external
        assert main_editor.document().isModified()
        sb._info.ipython = "yes"
        sb.restart()
        state["phase"] = "ipython-start"
        return

    if phase == "ipython-start":
        if not ready(sb):
            return
        assert sb._startup_info.get("ipython") == "yes"
        sb.executeCommand("kept_value = 502\n")
        state["phase"] = "ipython-file"
        return

    if phase == "ipython-file":
        if value(sb, "kept_value") != 502 or not ready(sb):
            return
        eb.setPlainText("ipython_value = kept_value + 1\n")
        select(eb)
        receipt = pyzo.runCommands.run_file((True, False))
        assert receipt.command is ExecutionCommand.RUN_FILE_AS_SCRIPT
        assert receipt.policy.autosave and not receipt.policy.recycle
        state.update(phase="ipython-main", ipython=receipt)
        return

    if phase == "ipython-main":
        if value(sb, "ipython_value") != 503 or not ready(sb):
            return
        assert service.provenance_is_current(state["ipython"])
        eb.setPlainText("ipython_main_value = ipython_value + 1\n")
        select(eb)
        receipt = pyzo.runCommands.run_file((True, True))
        assert receipt.command is ExecutionCommand.RUN_MAIN_AS_SCRIPT
        assert receipt.policy.autosave and not receipt.policy.recycle
        assert receipt.kernel_generation_id == state["ipython"].kernel_generation_id
        state["phase"] = "ipython-value"
        return

    if phase == "ipython-value":
        if value(sb, "ipython_main_value") != 504 or not ready(sb):
            return
        assert value(sb, "kept_value") == 502
        assert service.provenance_is_current(state["ipython"])
        print(
            "WORKSPACE RUN VARIANTS COMPLETE: real cell/File/retained Main and both script routes; owner/generation/save/restart/IPython/BOM/CRLF/source controls passed",
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
            print("RUN VARIANTS PHASE", phase, flush=True)
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
