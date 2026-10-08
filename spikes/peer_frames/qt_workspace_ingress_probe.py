"""Real Qt external opens, shared views, close reentrancy and empty startup.

Uses the actual command parser and macOS QFileOpenEvent handler with a
non-listening test-owned server. It never addresses the user's Pyzo server.
"""

from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys
import threading
import time
import traceback

from pyzo.util import paths

directory = Path(os.environ["PYZO_WORKSPACE_SET_PROBE_DIR"])
directory.mkdir(parents=True, exist_ok=True)
(directory / "tools").mkdir(exist_ok=True)
os.chdir(directory)
paths.prepare_appdata_appconfig_dirs = lambda: (str(directory), str(directory))
os.environ["PYZO_WORKSPACE_DIR"] = str(directory / "workspaces")
os.environ["PYZO_RECOVERY_DIR"] = str(directory / "recovery")
os.environ["PYZO_LOG"] = str(directory / "application.log")
phase = os.environ["PYZO_WORKSPACE_SET_PHASE"]

if phase == "ingress-empty":
    from spikes.peer_frames.document_resources import DocumentResourceRegistry
    from spikes.peer_frames.workspace_persistence import (
        WorkspacePersistenceState,
        WorkspacePersistenceStore,
    )

    store = WorkspacePersistenceStore(directory / "workspaces")
    store.commit(
        WorkspacePersistenceState(
            (),
            None,
            {
                "unavailable": {
                    "schema": 1,
                    "identity": "unavailable",
                    "name": "Unavailable",
                    "persistence_location": None,
                    "session": {},
                    "profile": {},
                    "extensions": {"future": ["opaque", 7]},
                },
            },
            DocumentResourceRegistry().persistence_snapshot(),
            {},
            {},
        )
    )

# _start imports yoton from the Pyzo package's bundled module directory.
sys.path.insert(0, str(Path(paths.__file__).parents[1]))
import yoton.clientserver


class OwnedServer:
    def __init__(self, *args):
        pass

    def start(self):
        pass

    def is_alive(self):
        return True

    def stop(self):
        pass


yoton.clientserver.RequestServer = OwnedServer
sys.argv = ["pyzolauncher.py"]
import pyzo._start
from pyzo.core import commandline
from pyzo.core.main import MainWindow
from pyzo.qt import QtCore, QtGui, QtWidgets

# Exercise handle_cmd_args and QFileOpenEvent without binding a process port.
commandline.do_request = lambda address, request, timeout: (
    commandline.server.handle_request(request)
)


def file_item(owner, path):
    items = [
        group._findEditorOfFile(str(path))
        for group in pyzo.workspaceContext.context(owner).editors.groups
    ]
    return next((item for item in items if item is not None), None)


def owner_of(item):
    return window._peerDocumentResources.view(
        item.editor._peerViewIdentity
    ).workspace_id


def flush():
    QtWidgets.QApplication.sendPostedEvents()
    QtWidgets.QApplication.processEvents()


def request(path, *, bare=False, worker=False):
    request_text = str(path) if bare else "open " + str(path)
    if worker:
        thread = threading.Thread(
            target=lambda: commandline.server.handle_request(request_text)
        )
        thread.start()
        thread.join(1)
        assert not thread.is_alive()
    else:
        commandline.server.handle_request(request_text)


def finish():
    window._peerShellCloseChooser = lambda *args: "terminate"
    window._peerShutdownCoordinator._confirm_exit = lambda disposition: True

    def timeout():
        print("PROBE TEARDOWN TIMEOUT", file=sys.stderr, flush=True)
        os._exit(2)

    deadline = threading.Timer(3, timeout)
    deadline.daemon = True
    deadline.start()
    result = pyzo.application.lifecycle.quit()
    assert getattr(result, "value", None) == "completed", result
    assert not window._peerApplicationExitErrors, window._peerApplicationExitErrors


def verify():
    shared = directory / "project-a" / "shared file.py"
    shared.parent.mkdir(exist_ok=True)
    shared.write_text("baseline = 1\n")
    baseline = shared.read_bytes()
    if phase == "ingress-empty":
        assert not pyzo.application.workspaces.identities
        before = deepcopy(
            window._peerWorkspaceStore.load().state.workspaces["unavailable"]
        )
        request(shared)
        flush()
        owners = pyzo.application.workspaces.identities
        assert len(owners) == 1
        assert file_item(owners[0], shared) is not None
        window._savePeerWorkspacePersistence()
        after = window._peerWorkspaceStore.load().state.workspaces["unavailable"]
        assert after == before
        assert shared.read_bytes() == baseline
        print(
            "WORKSPACE INGRESS EMPTY COMPLETE: default created; opaque record preserved",
            flush=True,
        )
        finish()
        return

    a = pyzo.application.workspaces.active_identity
    b = pyzo.application.workspaces.create("B", str(directory / "project-b"))
    context_a = pyzo.workspaceContext.context(a)
    item_a = context_a.editors.loadFile(str(shared))
    assert owner_of(item_a) == a
    item_a.editor.setPlainText("retained = 2\n")
    pyzo.application.documents.sync(item_a.editor)
    window._activatePeerWorkspace(a)
    request(shared, worker=True)
    # Resolve at GUI dispatch, not when the request arrived in the worker.
    window._activatePeerWorkspace(b)
    flush()
    item_b = file_item(b, shared)
    assert item_b is not None and owner_of(item_b) == b
    assert item_a.editor._peerDocumentIdentity == item_b.editor._peerDocumentIdentity
    assert item_b.editor.toPlainText() == "retained = 2\n"
    assert window._peerWorkspaces.active_workspace_id == b
    assert shared.read_bytes() == baseline
    views_before = window._peerDocumentResources.view_ids
    # CLI and alias reopen the existing local view, without foreign activation.
    sys.argv = ["pyzolauncher.py", str(shared)]
    assert commandline.handle_cmd_args()
    sys.argv = ["pyzolauncher.py"]
    flush()
    alias = shared.parent / "alias.py"
    alias.symlink_to(shared)
    request(alias, bare=True)
    flush()
    assert window._peerDocumentResources.view_ids == views_before

    if sys.platform == "darwin":
        event = QtGui.QFileOpenEvent(str(shared))
        QtCore.QCoreApplication.sendEvent(QtWidgets.qApp, event)
        sys.argv = ["pyzolauncher.py"]
        flush()
        assert window._peerDocumentResources.view_ids == views_before
        assert file_item(b, shared) is item_b
        print("NATIVE QFILEOPENEVENT COMPLETE", flush=True)

    # The real close preflight runs the ingress callback in a nested Qt loop.
    extra = directory / "during-close.py"
    extra.write_text("during_close = 3\n")
    shell_b = pyzo.workspaceContext.context(b).shells.addShell()
    ready_deadline = time.monotonic() + 8
    while not (shell_b._version and shell_b._state == "Ready"):
        assert time.monotonic() < ready_deadline, shell_b._state
        flush()
        time.sleep(0.01)
    window._activatePeerWorkspace(a)
    window._activatePeerWorkspace(b)
    original_confirm = window._resolvePeerClose

    def cancel_with_open(votes):
        assert b in window._peerClosingWorkspaceIds
        request(extra)
        flush()
        assert file_item(b, extra) is None
        assert owner_of(file_item(a, extra)) == a
        return False

    window._resolvePeerClose = cancel_with_open
    result = window._closePeerWorkspace(b)
    assert not result.applied
    assert shell_b._state == "Ready"
    assert b in pyzo.application.workspaces.identities
    assert not window._peerClosingWorkspaceIds
    assert not window._peerClosingWorkspace
    window._resolvePeerClose = original_confirm
    window._activatePeerWorkspace(b)
    request(extra)
    flush()
    assert owner_of(file_item(b, extra)) == b

    # Accepted owner retirement and final-owner unload cannot leave a captured
    # global host as the next ingress destination.
    window._peerShellCloseChooser = lambda *args: "terminate"
    assert window._closePeerWorkspace(b).applied
    request(shared)
    flush()
    assert file_item(a, shared) is item_a
    sole = directory / "sole-closing.py"
    sole.write_text("sole = 4\n")

    def cancel_final_with_open(votes):
        assert a in window._peerClosingWorkspaceIds
        request(sole)
        flush()
        assert pyzo.application.workspaces.identities == (a,)
        assert file_item(a, sole) is None
        return False

    window._resolvePeerClose = cancel_final_with_open
    assert not window._closePeerWorkspace(a).applied
    window._resolvePeerClose = original_confirm
    assert window._closePeerWorkspace(a).applied
    assert not pyzo.application.workspaces.identities
    request(extra)
    flush()
    owners = pyzo.application.workspaces.identities
    assert len(owners) == 1 and owners[0] not in (a, b)
    assert owner_of(file_item(owners[0], extra)) == owners[0]
    assert shared.read_bytes() == baseline
    shared.unlink()
    original_exit_confirmation = window._confirmPeerApplicationExit
    window._peerShutdownCoordinator._confirm_exit = lambda disposition: False
    assert pyzo.application.lifecycle.quit().value == "cancelled"
    assert not window._peerApplicationExitRequested
    request(shared)
    flush()
    assert owner_of(file_item(owners[0], shared)) == owners[0]
    assert file_item(owners[0], shared).editor.toPlainText() == "retained = 2\n"
    assert not shared.exists()
    window._peerShutdownCoordinator._confirm_exit = original_exit_confirmation
    assert not shared.exists()
    assert not any(
        isinstance(widget, QtWidgets.QMainWindow)
        for widget in QtWidgets.QApplication.topLevelWidgets()
    )
    print(
        "WORKSPACE INGRESS COMPLETE: worker/CLI/OS, shared local views, aliases, reentrant Cancel, retirement and empty-set default",
        flush=True,
    )
    finish()


def guarded_verify():
    try:
        verify()
    except Exception:
        traceback.print_exc()
        pyzo.localKernelManager.terminateAll()
        window._stopPeerApplicationThreads()
        QtWidgets.qApp.exit(1)


original_init = MainWindow.__init__


def init_and_probe(self, *args, **kwargs):
    global window
    original_init(self, *args, **kwargs)
    window = self
    QtCore.QTimer.singleShot(250, guarded_verify)


MainWindow.__init__ = init_and_probe
pyzo._start.start()
