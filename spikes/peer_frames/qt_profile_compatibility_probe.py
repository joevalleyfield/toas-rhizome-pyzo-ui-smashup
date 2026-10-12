"""Real startup/exec-restart/quit against pristine, legacy and peer profiles.

The parent harness chooses the source tree via PYTHONPATH. All app data and
servers are isolated; no production classes are replaced except the guarded
post-startup probe and explicit Cancel response.
"""

from __future__ import annotations

import faulthandler
import json
import os
import sys
import traceback
import types
from pathlib import Path

from pyzo.util import paths

directory = Path(os.environ["PYZO_COMPAT_DIRECTORY"])
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
sys.argv = [str(Path(__file__).resolve())]

import pyzo._start
from pyzo._start import ssdf
from pyzo.core.main import MainWindow
from pyzo.qt import QtCore, QtWidgets

mode = os.environ["PYZO_COMPAT_MODE"]
phase = os.environ["PYZO_COMPAT_PHASE"]
faulthandler.dump_traceback_later(12)
peer = mode == "peer"
window = None
done = False
failure = False
seeded = False
execution_marker = None
expected_path = directory / "expected.json"
source_names = ("main.py", "second.py")

# Start a real kernel using the same isolated runtime as the GUI. This also
# avoids interpreter discovery or configuration UI in the fresh controls.
if not pyzo.config.shellConfigs2:
    pyzo.config.shellConfigs2 = [ssdf.new()]
pyzo.config.shellConfigs2[0].exe = sys.executable
pyzo.config.shellConfigs2[0].name = "Compatibility kernel"
pyzo.config.advanced.alwaysAskWhenClosingPyzo = 0


def group_for(editor):
    if hasattr(pyzo.editors, "_group_for_editor"):
        return pyzo.editors._group_for_editor(editor)
    return pyzo.editors


def named_editors():
    return {
        Path(editor.filename).name: editor
        for editor in pyzo.editors
        if editor.filename
    }


def quit_app():
    global done
    done = True
    if peer:
        window._peerShellCloseChooser = lambda *_: "terminate"
        assert pyzo.application.lifecycle.quit().value == "completed"
    else:
        assert window.close()


def verify():
    expected = json.loads(expected_path.read_text())
    editors = named_editors()
    assert set(editors) == set(source_names), set(editors)
    assert sum(bool(editor.filename) for editor in pyzo.editors) == 2
    assert Path(pyzo.editors.getMainEditor().filename).name == "main.py"
    for name, editor in editors.items():
        entry = expected["files"][name]
        assert editor.toPlainText() == entry["text"], name
        assert editor.textCursor().position() == entry["cursor"], (
            name, editor.textCursor().position(), entry["cursor"]
        )
        host = group_for(editor)
        item = host._findEditorOfFile(editor.filename)
        assert item.pinned == (name == "main.py"), name
        assert Path(editor.filename).read_bytes().hex() == entry["bytes"], name
        assert Path(editor.filename).stat().st_mtime_ns == entry["mtime_ns"], name
    config = pyzo.config
    if peer:
        config = pyzo.workspaceContext.context(
            pyzo.application.workspaces.active_identity
        ).config
    assert config.settings.defaultIndentWidth == 3
    assert config.tools.pyzointeractivehelp.noNewlines == 0
    assert config.tools.futureextension["nested"] == ["preserve", 39]
    tools = set(pyzo.toolManager.getLoadedTools())
    assert {"pyzofilebrowser", "pyzointeractivehelp"} <= tools, tools
    for tool_id in ("pyzofilebrowser", "pyzointeractivehelp"):
        tool = pyzo.toolManager.getTool(tool_id)
        assert tool is not None and not isinstance(tool, QtWidgets.QLabel), tool_id
    if phase == "restarted":
        assert os.environ["PYZO_COMPAT_RESTART_TOKEN"] == expected["restart_token"]
        if os.name == "nt":
            assert os.getpid() != expected["restart_pid"], "Restart did not launch a successor"
        else:
            assert os.getpid() == expected["restart_pid"], "Restart did not exec"
    if peer and os.environ.get("PYZO_COMPAT_ORIGIN") != "peer":
        archived = window._peerWorkspaceStore.load().state.application_state
        assert archived["legacy_config"]["tools"]["futureextension"]["nested"] == [
            "preserve", 39
        ]
    print(f"PROFILE {mode} {phase} STATE VERIFIED", flush=True)


def seed():
    for index, name in enumerate(source_names):
        path = directory / name
        text = f"compatibility_value = {index + 39}\nprint(compatibility_value)\n"
        raw = text.replace("\n", "\r\n").encode("utf-8")
        if index == 0:
            raw = b"\xef\xbb\xbf" + raw
        path.write_bytes(raw)
        item = pyzo.editors.loadFile(str(path))
        assert item is not None
        editor = item.editor
        cursor = editor.textCursor()
        cursor.setPosition(5 + index)
        editor.setTextCursor(cursor)
        if index == 0:
            if peer:
                registry = pyzo.application.documents.registry
                registry.set_main(
                    pyzo.application.workspaces.active_identity,
                    pyzo.application.documents.identity(editor),
                )
            else:
                group_for(editor)._tabs._mainFile = item.id
            host = group_for(editor)
            host._menu.setIndex(host._tabs.items().index(item))
            host._menu._fileAction("pin")
            assert item.pinned
    config = pyzo.config
    if peer:
        config = pyzo.workspaceContext.context(
            pyzo.application.workspaces.active_identity
        ).config
    config.settings.defaultIndentWidth = 3
    config.tools.pyzointeractivehelp.noNewlines = 0
    config.tools.futureextension = {"nested": ["preserve", 39]}
    pyzo.toolManager.loadTool("pyzofilebrowser")
    pyzo.toolManager.loadTool("pyzointeractivehelp")
    editor = named_editors()["second.py"]
    baseline = editor.toPlainText()
    cursor = editor.textCursor().position()
    editor.insertPlainText("cancel_me")
    shell = pyzo.shells.getCurrentShell()
    if peer:
        window._peerShellCloseChooser = lambda *_: "cancel"
        assert pyzo.application.lifecycle.quit().value == "cancelled"
    else:
        host = group_for(editor)
        original = host.askToSaveFileIfDirty
        host.askToSaveFileIfDirty = lambda *_: False
        try:
            assert not window.close()
        finally:
            host.askToSaveFileIfDirty = original
    assert "cancel_me" in editor.toPlainText()
    assert shell._context.connection_count
    assert (directory / "second.py").read_bytes().decode("utf-8").replace(
        "\r\n", "\n"
    ) == baseline
    assert editor.undo() is not False
    assert editor.toPlainText() == baseline
    restored_cursor = editor.textCursor()
    restored_cursor.setPosition(cursor)
    editor.setTextCursor(restored_cursor)
    editor.document().setModified(False)
    print(f"PROFILE {mode} CANCEL PRESERVED", flush=True)
    expected = {
        "restart_pid": os.getpid(),
        "files": {
            name: {
                "text": ed.toPlainText(),
                "cursor": ed.textCursor().position(),
                "bytes": (directory / name).read_bytes().hex(),
                "mtime_ns": (directory / name).stat().st_mtime_ns,
            }
            for name, ed in named_editors().items()
        },
    }
    expected_path.write_text(json.dumps(expected))


def tick():
    global done, seeded, execution_marker
    if done:
        return
    if os.environ.get("PYZO_COMPAT_INJECT_FAILURE") == "1":
        raise AssertionError("injected compatibility callback failure")
    shells = tuple(pyzo.shells)
    if not shells or not all(
        shell._version and shell._state == "Ready" and shell._context.connection_count
        for shell in shells
    ):
        return
    windows = [
        widget for widget in QtWidgets.QApplication.topLevelWidgets()
        if isinstance(widget, QtWidgets.QMainWindow)
    ]
    assert (not windows) if peer else (window in windows), windows
    assert Path(pyzo.__file__).resolve().is_relative_to(
        Path(os.environ["PYZO_COMPAT_SOURCE"]).resolve()
    )
    assert hasattr(window, "_dockManager") == (mode != "vanilla")
    if phase in {"seed", "seed-quit"} and not seeded:
        seed()
        seeded = True
    if execution_marker is None:
        if phase != "seed":
            verify()
        execution_marker = directory / f"kernel-{mode}-{phase}-{os.getpid()}.txt"
        editor = named_editors()["main.py"]
        shells[0].executeCode(
            editor.toPlainText()
            + f"\nwith open({str(execution_marker)!r}, 'w') as compatibility_report:\n"
            + "    compatibility_report.write(str(compatibility_value))\n",
            editor.filename, 0,
        )
        return
    if not execution_marker.exists():
        return
    assert execution_marker.read_text() == "39"
    print(f"PROFILE {mode} {phase} KERNEL EXECUTION VERIFIED", flush=True)
    if phase in {"seed", "migrate"}:
        expected = json.loads(expected_path.read_text())
        expected["restart_pid"] = os.getpid()
        expected["restart_token"] = os.urandom(16).hex()
        os.environ["PYZO_COMPAT_RESTART_TOKEN"] = expected["restart_token"]
        expected_path.write_text(json.dumps(expected))
        os.environ["PYZO_COMPAT_PHASE"] = "restarted"
        print(f"PROFILE {mode} RESTART REQUESTED", flush=True)
        done = True
        if peer:
            window._peerShellCloseChooser = lambda *_: "terminate"
            pyzo.application.lifecycle.restart()
        else:
            window.restart()
        if os.name == "nt" and hasattr(window, "_restartProcess"):
            assert window._restartProcess.pid != os.getpid()
            assert window._restartProcess.poll() is None
            print(f"PROFILE {mode} RESTART HANDED OFF", flush=True)
            return
        raise AssertionError("Restart returned without replacing the process")
    quit_app()


def abort(error):
    global failure, done
    failure = done = True
    print(f"PROFILE FAILURE {mode} {phase}: {error}", flush=True)
    pyzo.localKernelManager.terminateAll()
    for shell in tuple(pyzo.shells):
        shell._context.close()
    pyzo.parser.stop(timeout=0.5)
    QtWidgets.qApp.exit(1)


original_init = MainWindow.__init__


def init(self, *args, **kwargs):
    global window
    original_init(self, *args, **kwargs)
    window = self
    self._compatTimer = QtCore.QTimer(self)

    def guarded():
        try:
            tick()
        except Exception as error:
            traceback.print_exc()
            abort(error)

    self._compatTimer.timeout.connect(guarded)
    self._compatTimer.start(60)
    QtCore.QTimer.singleShot(
        20000, lambda: abort("internal deadline") if not done else None
    )


MainWindow.__init__ = init
pyzo._start.start()
if failure or not done:
    sys.exit(1)
print(f"PROFILE {mode} {phase} QUIT COMPLETE", flush=True)
