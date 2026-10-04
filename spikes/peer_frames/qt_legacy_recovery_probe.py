"""Separate-process proof of explicit recovery choice and retained reopening."""

import os
from pathlib import Path
import sys
import types

from pyzo.util import paths
from spikes.peer_frames.workspace_persistence import WorkspacePersistenceStore

directory = Path(os.environ["PYZO_WORKSPACE_SET_PROBE_DIR"])
directory.mkdir(parents=True, exist_ok=True)
(directory / "tools").mkdir(exist_ok=True)
os.chdir(directory)
paths.prepare_appdata_appconfig_dirs = lambda: (str(directory), str(directory))
os.environ["PYZO_WORKSPACE_DIR"] = str(directory / "workspaces")
os.environ["PYZO_RECOVERY_DIR"] = str(directory / "recovery")
phase = os.environ["PYZO_WORKSPACE_SET_PHASE"]
source = directory / "saved.py"
store = WorkspacePersistenceStore(directory / "workspaces")
if not store.manifest.exists():
    source.write_text("disk\n")
    (directory / "malformed.py").write_text("untouched\n")
    store.migrate_legacy(
        {
            "workspaceRecovery": {
                "a": {
                    "snapshots": [
                        {
                            "document_id": "legacy-named",
                            "filename": str(source),
                            "text": "first\n",
                            "history": ["before first\n"],
                        },
                        {
                            "document_id": "legacy-named",
                            "filename": str(source),
                            "text": "selected\n",
                            "clean_text": "baseline\n",
                            "history": ["before selected\n"],
                            "use_bom": True,
                            "line_endings": "CRLF",
                        },
                        {"document_id": "legacy-untitled", "text": "untitled first\n"},
                        {"document_id": "legacy-untitled", "text": "untitled second\n"},
                        {
                            "document_id": "malformed",
                            "filename": str(directory / "malformed.py"),
                            "text": 123,
                        },
                    ]
                }
            }
        },
        default_workspace_id="a",
    )

commandline = types.ModuleType("pyzo.core.commandline")
commandline.is_our_server_running = lambda: False
commandline.handle_cmd_args = lambda: None
commandline.stop_our_server = lambda: None
sys.modules["pyzo.core.commandline"] = commandline
sys.argv = ["pyzolauncher.py"]

import pyzo._start
from pyzo.core.main import MainWindow
from pyzo.qt import QtWidgets
from spikes.peer_frames.identity import ApplicationIdentity, IdentityKind


original_init = MainWindow.__init__


def init_and_probe(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    self._peerShellCloseChooser = lambda *_args: "terminate"

    def inspect():
        registry = pyzo.application.documents.registry
        named = ApplicationIdentity(IdentityKind.DOCUMENT, "legacy-named")
        untitled = ApplicationIdentity(IdentityKind.DOCUMENT, "legacy-untitled")
        if phase == "select":
            healthy = pyzo.editors.newFile().editor
            healthy.insertPlainText("healthy\n")
            healthy_id = pyzo.application.documents.identity(healthy)
            self._peerLegacyRecoveryChooser = lambda *_args: None
            before = store.load()
            assert (
                pyzo.editors.loadFile(
                    str(directory / ".." / directory.name / "saved.py")
                )
                is None
            )
            assert named not in registry.document_ids
            assert store.load().generation == before.generation
            assert pyzo.editors.loadFile(str(directory / "malformed.py")) is None
            assert (directory / "malformed.py").read_text() == "untouched\n"
            print("LEGACY CANCEL PRESERVED", flush=True)

            file_menu = self._peerCommandProjector.primary_menu_bar()._menumap["file"]
            assert any(
                "Recover legacy buffer" in action.text()
                for action in file_menu.actions()
            )
            execute_dialog = QtWidgets.QDialog.exec

            def choose_preview(dialog):
                preview = dialog.findChild(
                    QtWidgets.QPlainTextEdit, "legacy-recovery-working-preview"
                )
                versions = dialog.findChild(
                    QtWidgets.QComboBox, "legacy-recovery-versions"
                )
                assert preview.toPlainText() == "first\n"
                versions.setCurrentIndex(1)
                assert preview.toPlainText() == "selected\n"
                return QtWidgets.QDialog.DialogCode.Accepted

            try:
                QtWidgets.QDialog.exec = choose_preview
                assert self._choosePeerLegacyRecovery(
                    self.legacyPeerRecoveryChoices(), "legacy-named"
                ) == ("legacy-named", 1)
            finally:
                QtWidgets.QDialog.exec = execute_dialog
            print("LEGACY CHOICE PREVIEW VERIFIED", flush=True)

            self._peerLegacyRecoveryChooser = lambda *_args: ("legacy-named", 1)
            select = self._peerWorkspaceStore.select_legacy_recovery

            def fail_selection(*_args, **_kwargs):
                raise OSError("injected selection publication failure")

            self._peerWorkspaceStore.select_legacy_recovery = fail_selection
            assert pyzo.editors.loadFile(str(source)) is None
            assert named not in registry.document_ids
            assert "Legacy recovery failed" in self._peerStatusService.currentMessage()
            assert "legacy-named" in self.legacyPeerRecoveryChoices()
            self._peerWorkspaceStore.select_legacy_recovery = select
            print("LEGACY FAILURE PRESERVED", flush=True)

            item = pyzo.editors.loadFile(str(source))
            assert item is not None
            editor = item.editor
            assert pyzo.application.documents.identity(editor) == named
            assert editor.toPlainText() == "selected\n"
            assert editor.useBom
            assert editor.lineEndingsHumanReadable == "CRLF"
            assert editor.undo()
            assert editor.toPlainText() == "before selected\n"
            assert editor.redo()
            assert editor.toPlainText() == "selected\n"
            healthy.insertPlainText("still bound\n")
            assert registry.resource(healthy_id).text == healthy.toPlainText()
            secondary = pyzo.application.workspaces.create("Recovery workspace")
            assert pyzo.application.workspaces.activate(secondary).applied
            assert self.resolvePeerLegacyRecovery("legacy-untitled", 0)
            assert registry.resource(untitled).text == "untitled first\n"
            recovered = next(
                e
                for e in pyzo.editors
                if pyzo.application.documents.identity(e) == untitled
            )
            assert (
                registry.view(
                    pyzo.application.documents.view_identity(recovered)
                ).workspace_id
                == secondary
            )
            assert (
                self._peerRuntimeForEditorHost(
                    pyzo.editors._group_for_editor(recovered)
                ).identity
                == secondary
            )
            assert self._peerRetentionCoordinator.flush()
            assert pyzo.editors.closeFile(recovered) == 1
            assert not registry.views_for_document(untitled)
            assert pyzo.editors.closeFile(editor) == 1
            assert not registry.views_for_document(named)
            assert self._peerRetentionCoordinator.flush()
            print("LEGACY SELECTED CLOSED", flush=True)
        elif phase == "restart":
            assert self.legacyPeerRecoveryChoices() == {"malformed": []}
            assert not registry.views_for_document(named)
            item = pyzo.editors.loadFile(
                str(directory / ".." / directory.name / "saved.py")
            )
            assert item.editor.toPlainText() == "selected\n"
            assert item.editor.useBom
            assert item.editor.lineEndingsHumanReadable == "CRLF"
            assert pyzo.application.documents.identity(item.editor) == named
            assert item.editor.undo()
            assert item.editor.toPlainText() == "before selected\n"
            assert item.editor.redo()
            assert item.editor.toPlainText() == "selected\n"
            assert registry.resource(untitled).text == "untitled first\n"
            preserved = store.load().state.application_state["legacy_recovery"][
                "candidates"
            ]
            assert len(preserved["legacy-named"]) == 2
            assert len(preserved["legacy-untitled"]) == 2
            print("LEGACY RESTART RETAINED", flush=True)
        else:
            raise ValueError(phase)
        assert source.read_text() == "disk\n"
        pyzo.application.lifecycle.quit()

    pyzo.callLater(inspect)


MainWindow.__init__ = init_and_probe
pyzo._start.start()
