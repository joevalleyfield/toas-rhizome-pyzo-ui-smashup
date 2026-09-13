"""Two-process live Pyzo document persistence probe.

Run this module twice with the same ``PYZO_019_APP_DIR`` and temporary
``PYZO_RECOVERY_DIR``. Set ``PYZO_019_PHASE=first`` for the writer process and
``PYZO_019_PHASE=second`` for the restoring process. The launcher must provide
the pinned PySide6-QtAds wheel and set ``PYZO_PEER_FRAMES=1``.

The probe patches only the process-local application-data resolver and the
command-server module before Pyzo startup. It never changes HOME or the user's
Pyzo configuration.
"""

from __future__ import annotations

import json
import os
import sys
import types

from pyzo.util import paths

app_dir = os.environ["PYZO_019_APP_DIR"]
os.makedirs(os.path.join(app_dir, "tools"), exist_ok=True)
os.chdir(app_dir)
paths.prepare_appdata_appconfig_dirs = lambda: (app_dir, app_dir)

commandline = types.ModuleType("pyzo.core.commandline")
commandline.is_our_server_running = lambda: False
commandline.handle_cmd_args = lambda: None
commandline.stop_our_server = lambda: None
sys.modules["pyzo.core.commandline"] = commandline

sys.argv = ["pyzolauncher.py"]
import pyzo._start
from pyzo.core.main import MainWindow
from pyzo.qt import QtCore

phase = os.environ["PYZO_019_PHASE"]
saved_path = os.path.join(app_dir, "saved.py")


def finish_first():
    item = pyzo.editors.newFile()
    editor = item.editor
    editor.setPlainText("abc\n")
    editor.document().setModified(True)
    manifest = os.path.join(app_dir, "workspaces", "manifest.json")
    before_checkpoint = os.stat(manifest).st_mtime_ns

    assert pyzo.editors.saveFile(editor, saved_path)
    assert not editor.document().isModified()

    editor.setPlainText("abcd\n")
    editor.document().setModified(True)
    editor.undo()
    assert editor.toPlainText() == "abc\n"
    resource = pyzo.application.documents.resource(editor)
    assert resource.text == "abc\n"
    assert resource.undo_depth == 1

    def finish_after_automatic_checkpoint():
        assert os.stat(manifest).st_mtime_ns > before_checkpoint
        print("FIRST", resource.text.strip(), resource.undo_depth, flush=True)
        pyzo.application._peerDirtyCloseChooser = (
            lambda _document_id, _lifecycle: "discard"
        )
        pyzo.application.lifecycle.quit()

    QtCore.QTimer.singleShot(1500, finish_after_automatic_checkpoint)


def inspect_second():
    snapshot = pyzo.application.documents.registry.persistence_snapshot()
    documents = snapshot["documents"]
    record = next(
        value for value in documents.values() if value.get("path") == saved_path
    )
    assert record["text"] == "abc\n", record
    assert record["undo"] == [""], record
    assert record["redo"] == ["abcd\n"], record
    assert record["revision"] >= 2, record
    saved_document_id = next(
        document_id
        for document_id, value in documents.items()
        if value.get("path") == saved_path
    )
    saved_views = [
        value
        for value in snapshot["views"].values()
        if value.get("document_id") == saved_document_id
    ]
    assert len(saved_views) == 1, snapshot
    editors = [editor for editor in pyzo.editors if editor.filename == saved_path]
    assert len(editors) == 1, editors
    editor = editors[0]
    assert editor.toPlainText() == "abc\n"
    assert not editor.document().isModified()
    view_id = pyzo.application.documents.view_identity(editor)
    assert view_id is not None
    view_state = pyzo.application.documents.registry.view(view_id).state
    cursor = editor.textCursor()
    assert (cursor.position(), cursor.anchor()) == (
        view_state.cursor,
        view_state.selection[0],
    )
    assert editor.undo()
    assert editor.toPlainText() == ""
    assert editor.redo()
    assert editor.toPlainText() == "abc\n"
    original_document_id = pyzo.application.documents.identity(editor)
    original_view_id = pyzo.application.documents.view_identity(editor)
    original_undo = tuple(
        pyzo.application.documents.resource(editor)._undo
    )
    for reopened in (saved_path, "./saved.py", saved_path):
        reopened_item = pyzo.editors.loadFile(reopened)
        assert reopened_item is not None
        assert reopened_item.editor is editor
        assert pyzo.application.documents.identity(reopened_item.editor) == (
            original_document_id
        )
        assert pyzo.application.documents.view_identity(reopened_item.editor) == (
            original_view_id
        )
        assert tuple(
            pyzo.application.documents.resource(reopened_item.editor)._undo
        ) == original_undo
    print("SECOND", json.dumps(record, sort_keys=True), flush=True)
    pyzo.application.lifecycle.quit()


original_init = MainWindow.__init__


def init_and_probe(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    pyzo.callLater(finish_first if phase == "first" else inspect_second)


MainWindow.__init__ = init_and_probe
pyzo._start.start()
