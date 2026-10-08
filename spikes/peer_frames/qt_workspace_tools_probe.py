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


import json
from copy import deepcopy
from spikes.peer_frames import workspace_persistence
from pyzo.core.workspaceTools import BUILTINS
from pyzo.core.workspaceContext import config_for, plain, struct


def affiliation():
    for owner in pyzo.application.workspaces.identities:
        runtime = window._peerRuntimeCatalog.runtime(owner)
        name = window._peerWorkspaces.descriptor(owner).name
        for pane_id, dock in runtime.backend.docks.items():
            assert name in dock.windowTitle(), (name, pane_id, dock.windowTitle())
            assert name in dock.accessibleName()
            assert name in dock.widget().accessibleName()
            assert dock._workspaceContextOwner == owner


def verify_tools(owner):
    manager = pyzo.toolManager.for_workspace(owner)
    context = pyzo.workspaceContext.context(owner)
    for tool_id in BUILTINS:
        tool = manager.getTool(tool_id)
        assert tool is not None, (owner, tool_id)
        assert not isinstance(tool, QtWidgets.QLabel), (
            tool_id,
            tool.text() if isinstance(tool, QtWidgets.QLabel) else "",
        )
        module = sys.modules[type(tool).__module__]
        assert module.pyzo.owner == owner
        assert all(
            window._peerDocumentResources.view(e._peerViewIdentity).workspace_id
            == owner
            for e in module.pyzo.editors
        )
        selected = module.pyzo.shells.getCurrentShell()
        if selected is not None:
            assert (
                pyzo.application.workspace_execution._shells[selected].workspace_id
                == owner
            )
    return manager, context


def tick():
    phase = state["phase"]
    if phase == "initial" and os.environ["PYZO_WORKSPACE_SET_PHASE"] == "tools-restore":
        expected = json.loads((directory / "tools-expected.json").read_text())
        from spikes.peer_frames.identity import ApplicationIdentity, IdentityKind

        for owner_text, entry in expected.items():
            owner = ApplicationIdentity(IdentityKind.WORKSPACE, owner_text)
            manager, context = verify_tools(owner)
            assert context.requested.view.zoom == entry["zoom"]
            assert context.requested.settings.language == entry["language"]
            assert "owned_" + entry["tag"] in context.command_history.get_commands()
            assert context.config.tools.futuretool["nested"] == entry["tag"]
            assert set(manager.getLoadedTools()) >= BUILTINS
            assert manager.getTool("pyzoexpressionviewer")._em.getExpressions()[
                "owner_marker"
            ][0]
            assert manager.getTool("pyzosnippets")._searchText.text() == entry["tag"]
            for tool_id, retained in entry["tool_states"].items():
                assert manager.capture_states()[tool_id] == retained, (owner, tool_id)
            assert plain(context.config.shellConfigs2) == entry["shell_profiles"]
            assert (
                plain(context.config.tools.pyzofilebrowser2.starredDirs)
                == entry["projects"]
            )
        affiliation()
        print(
            "WORKSPACE TOOLS RESTART COMPLETE: both owners, all built-ins, configuration/history/requests/tool states and affiliation",
            flush=True,
        )
        state["phase"] = "done"
        window._peerShellCloseChooser = lambda *_: "terminate"
        pyzo.application.lifecycle.quit()
        return
    if phase == "initial":
        sa = pyzo.shells.getCurrentShell()
        if sa is None or not ready(sa):
            return
        a = window._peerActiveRuntime().identity
        ea = pyzo.editors.getCurrentEditor()
        ea.setPlainText('def owner_A():\n    return "A"\n')
        b = pyzo.application.workspaces.create("Tools peer B")
        eb = pyzo.editors.getCurrentEditor()
        eb.setPlainText('def owner_B():\n    return "B"\n')
        sb = pyzo.shells.addShell()
        state.update(a=a, b=b, ea=ea, eb=eb, sa=sa, sb=sb, phase="seed")
        return
    a, b, sa, sb = (state[key] for key in ("a", "b", "sa", "sb"))
    if phase == "seed":
        if not ready(sb):
            return
        if not state.get("seeded"):
            sa.executeCommand('owner_marker="A"\n')
            sb.executeCommand('owner_marker="B"\n')
            state["seeded"] = True
            return
        if value(sa, "owner_marker") != "A" or value(sb, "owner_marker") != "B":
            return
        for owner, tag, zoom in ((a, "A", 2), (b, "B", -1)):
            manager = pyzo.toolManager.for_workspace(owner)
            for tool_id in sorted(BUILTINS):
                manager.loadTool(tool_id)
            manager, context = verify_tools(owner)
            context.requested.view.zoom = zoom
            context.requested.settings.language = tag + " requested language"
            context.requested.view.showStatusbar = tag == "A"
            context.config.tools.futuretool = {"nested": tag}
            context.command_history.append("owned_" + tag)
            manager.getTool("pyzoexpressionviewer").addExpression("owner_marker")
            manager.getTool("pyzosnippets")._searchText.setText(tag)
            manager.getTool("pyzoworkspace")._tree._proxy.setName("owner_marker")
            help_tool = manager.getTool("pyzointeractivehelp")
            help_tool._pauseBut.setChecked(True)
            help_tool._history = ["help_" + tag]
            help_tool._histindex = 0
            help_tool._text.setText("help_" + tag)
            browser = manager.getTool("pyzowebbrowser")._view
            browser._url = "https://example.invalid/" + tag
            browser._history = ["prior_" + tag]
            browser._history2 = ["next_" + tag]
            context.config.shellConfigs2.append(
                struct({"name": "owned_" + tag, "exe": sys.executable})
            )
            context.config.tools.pyzofilebrowser2.starredDirs = [
                struct(
                    {
                        "path": str(directory),
                        "name": "project_" + tag,
                        "addToPythonpath": False,
                    }
                )
            ]
        state["before_B"] = pyzo.workspaceContext.snapshot(b)
        assert (
            pyzo.workspaceContext.profiles[a] is not pyzo.workspaceContext.profiles[b]
        )
        focus_shell(sa)
        state["automatic_started"] = time.monotonic()
        state["phase"] = "automatic"
        return
    if phase == "automatic":
        durable = window._peerWorkspaceStore.load()
        for owner, tag, zoom in ((a, "A", 2), (b, "B", -1)):
            contextual = (
                durable.state.workspaces.get(str(owner), {})
                .get("profile", {})
                .get("contextual", {})
            )
            if contextual.get("config", {}).get("view", {}).get("zoom") != zoom:
                return
            if "owned_" + tag not in contextual.get("history", []):
                return
        elapsed = time.monotonic() - state["automatic_started"]
        assert elapsed < 4, elapsed
        base_size = pyzo.codeeditor.Manager.defaultFont().pointSize()
        # An existing document checkpoint may publish the profile before the
        # next context census projects it onto live controls. Observe both.
        if (
            state["ea"].font().pointSize() != base_size + 2
            or state["eb"].font().pointSize() != base_size - 1
        ):
            return
        assert (
            pyzo.workspaceContext.capabilities(a)["settings.debuggerSelection"][
                "effective"
            ]
            == "independent"
        )
        assert window._workspaceStatusVisible(a) and not window._workspaceStatusVisible(
            b
        )
        print(
            f"CONTEXT AUTOMATIC CHECKPOINT {elapsed:.3f}s: independent preferences/history without further document edits; live owner-only zoom/status update",
            flush=True,
        )
        state["phase"] = "tools"
        return
    if phase == "tools":
        ma, ca = verify_tools(a)
        mb, cb = verify_tools(b)
        if not state.get("refreshed"):
            ma.getTool("pyzoexpressionviewer").manualRefresh()
            mb.getTool("pyzoexpressionviewer").manualRefresh()
            state["refreshed"] = True
        ar = ma.getTool("pyzoexpressionviewer")._em.getExpressions().get("owner_marker")
        br = mb.getTool("pyzoexpressionviewer")._em.getExpressions().get("owner_marker")
        if not ar or not br or ar[1] != "A" or br[1] != "B":
            return
        assert ma.getTool("pyzosourcestructure")._getCurEditorFromRef() is state["ea"]
        assert mb.getTool("pyzosourcestructure")._getCurEditorFromRef() is state["eb"]
        assert all(ma.getTool(t) is not mb.getTool(t) for t in BUILTINS)
        assert config_for(state["ea"]).view.zoom == 2
        assert config_for(state["eb"]).view.zoom == -1
        assert (
            pyzo.workspaceContext.capabilities(a)["settings.language"]["requested"]
            == "A requested language"
        )
        assert (
            pyzo.workspaceContext.capabilities(a)["settings.language"]["effective"]
            == pyzo.config.settings.language
        )
        print("shared diagnostic marker", flush=True)
        assert all(
            "shared diagnostic marker"
            in manager.getTool("pyzologger")._logger_shell.toPlainText()
            for manager in (ma, mb)
        )
        # A captured A launcher remains local when B is foreground.
        description = next(
            item for item in ma.getToolInfo() if item.id == "pyzosnippets"
        )
        old_b = mb.getTool("pyzosnippets")
        focus_shell(sb)
        description.menuLauncher(True)
        assert mb.getTool("pyzosnippets") is old_b
        # A third-party tool can opt in through its explicit context constructor.
        (directory / "tools" / "contextTool.py").write_text(
            'workspace_api=1\ntool_name="Context tool"\nfrom pyzo.qt import QtWidgets\nclass ContextTool(QtWidgets.QLabel):\n    def __init__(self,parent,*,context):\n        super().__init__("owned",parent)\n        self.context=context\n'
        )
        ma.loadToolInfo()
        mb.loadToolInfo()
        ma.loadTool("contexttool")
        mb.loadTool("contexttool")
        assert ma.getTool("contexttool").context.owner == a
        assert mb.getTool("contexttool").context.owner == b
        # An undeclared tool is rejected before its import side effect.
        (directory / "tools" / "futureTool.py").write_text(
            'tool_name="Future"\nimport pathlib\npathlib.Path("must-not-execute").write_text("bad")\n'
        )
        ma.loadToolInfo()
        ma.loadTool("futuretool")
        refused = ma.getTool("futuretool")
        assert (
            isinstance(refused, QtWidgets.QLabel) and "workspace_api" in refused.text()
        )
        assert not (directory / "must-not-execute").exists()
        assert cb.config.tools.futuretool["nested"] == "B"
        (directory / "tools" / "badMetadata.py").write_text(
            'tool_name=__import__("pathlib").Path("metadata-must-not-execute").write_text("bad")\n'
        )
        ma.loadToolInfo()
        assert not (directory / "metadata-must-not-execute").exists()
        # Capture a genuine in-flight A query, then reload A's tool. B remains live.
        old = ma.getTool("pyzoexpressionviewer")
        held, original = hold(sa)
        old.manualRefresh()
        assert held
        state.update(held=held, original=original, old=old, phase="held")
        return
    if phase == "held":
        if not all(reply.future.done() for reply in state["held"]):
            return
        ma = pyzo.toolManager.for_workspace(a)
        before = deepcopy(state["old"]._proxy._response)
        ma.loadTool("pyzoexpressionviewer")
        sa._request.requestWithProvenance = state["original"]
        for reply in state["held"]:
            reply.release()
        assert state["old"]._proxy._response == before
        assert ma.getTool("pyzoexpressionviewer") is not state["old"]
        assert (
            pyzo.toolManager.for_workspace(b)
            .getTool("pyzoexpressionviewer")
            ._em.getExpressions()["owner_marker"][1]
            == "B"
        )
        # Float/move tools within their owner and rename that owner.
        runtime = window._peerRuntimeCatalog.runtime(a)
        dock = ma._activeTools["pyzosnippets"]
        pane = runtime.backend._pane_id_from_dock(dock)
        runtime.model.create_frame(pane, "tools-affiliation-frame")
        window._peerWorkspaces.rename_workspace(a, "Tools renamed A")
        window._refreshWorkspaceAffiliation()
        affiliation()
        print(
            "WORKSPACE TOOLS LOCAL FOLLOWING: ten independent built-ins, real A/B namespace values, source structures, histories, profiles, stale reload reply and third-party refusal",
            flush=True,
        )
        state["phase"] = "close"
        return
    if phase == "close":
        ma = pyzo.toolManager.for_workspace(a)
        old_tools = {key: ma.getTool(key) for key in BUILTINS}
        before = pyzo.workspaceContext.snapshot(a)
        window._peerShellCloseChooser = lambda *_: "cancel"
        assert not pyzo.application.workspaces.close(a).applied
        assert all(ma.getTool(key) is obj for key, obj in old_tools.items())
        window._peerShellCloseChooser = lambda *_: "terminate"
        original = workspace_persistence.os.replace

        def fail_manifest(source, destination):
            if str(destination).endswith("manifest.json"):
                raise OSError("owned Stage 6 publication failure")
            return original(source, destination)

        workspace_persistence.os.replace = fail_manifest
        try:
            result = pyzo.application.workspaces.close(a)
        finally:
            workspace_persistence.os.replace = original
        assert not result.applied and "persistence preflight failed" in result.detail
        assert all(ma.getTool(key) is obj for key, obj in old_tools.items())
        assert pyzo.application.workspaces.close(a).applied
        prefix = "pyzo.tools._workspace_" + str(a).replace("-", "_")
        assert not any(
            key == prefix or key.startswith(prefix + ".") for key in sys.modules
        )
        durable = window._peerWorkspaceStore.load().state.workspaces[str(a)]["profile"][
            "contextual"
        ]
        assert durable == before
        assert pyzo.workspaceContext.context(b).shells.getCurrentShell() is sb
        query = sb._request.eval("owner_marker")
        query.set_auto_cancel_timeout(2.0)
        state.update(
            phase="survivor", survivor_query=query,
            survivor_started=time.monotonic(), old_tools=old_tools, before=before,
        )
        return
    if phase == "survivor":
        query = state["survivor_query"]
        if not query.done():
            return
        assert not query.cancelled() and query.exception() is None
        assert query.result() == "B"
        assert pyzo.workspaceContext.context(b).shells.getCurrentShell() is sb
        print(
            f"SURVIVING B RESPONSE {time.monotonic() - state['survivor_started']:.3f}s",
            flush=True,
        )
        old_tools, before = state["old_tools"], state["before"]
        assert pyzo.application.workspaces.reopen(a).applied
        ma, ca = verify_tools(a)
        assert all(ma.getTool(key) is not old_tools[key] for key in BUILTINS)
        assert ca.shells.getCurrentShell() is None
        assert (
            pyzo.workspaceContext.capabilities(a)["settings.debuggerSelection"][
                "effective"
            ]
            == "unavailable"
        )
        assert ma.getTool("pyzoexpressionviewer")._proxy._response == []
        ma.getTool("pyzoexpressionviewer").manualRefresh()
        assert ca.command_history.get_commands() == before["history"]
        assert ma.capture_states() == before["tool_states"]
        assert ma.getTool("pyzosnippets")._searchText.text() == "A"
        assert "owner_marker" in ma.getTool("pyzoexpressionviewer")._em.getExpressions()
        window._refreshWorkspaceAffiliation()
        affiliation()
        expected = {}
        for owner, tag in ((a, "A"), (b, "B")):
            context = pyzo.workspaceContext.context(owner)
            expected[str(owner)] = {
                "tag": tag,
                "zoom": context.requested.view.zoom,
                "language": context.requested.settings.language,
                "tool_states": context.toolManager.capture_states(),
                "shell_profiles": plain(context.config.shellConfigs2),
                "projects": plain(context.config.tools.pyzofilebrowser2.starredDirs),
            }
        (directory / "tools-expected.json").write_text(json.dumps(expected))
        window._savePeerWorkspacePersistence()
        print(
            "WORKSPACE TOOLS COMPLETE: Cancel/failure keep instances, durable A teardown/resume, local-empty A and surviving B kernel, requested/effective settings, visible/accessibility affiliation",
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
            print("TOOLS PHASE", phase, flush=True)
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
