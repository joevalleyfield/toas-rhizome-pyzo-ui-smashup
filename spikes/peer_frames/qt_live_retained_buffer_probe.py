"""Real peer-editor close/reopen acceptance probe for task 020.

Run with the configured ``uvt`` launcher, ``PYZO_PEER_FRAMES=1``, and a fresh
``PYZO_020_APP_DIR``.  The probe deliberately calls the identity-based reopen
operation used by the retained-buffer command rather than reopening by path.
"""

from __future__ import annotations

import os
import sys
import types

from pyzo.util import paths

app_dir = os.environ["PYZO_020_APP_DIR"]
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


def _close_and_reopen(editor, expected_text):
    application = pyzo.application
    documents = application.documents
    document_id = documents.identity(editor)
    view_id = documents.view_identity(editor)
    assert document_id is not None
    assert view_id is not None
    resource = documents.resource(editor)
    cursor = editor.textCursor()
    cursor.setPosition(len(expected_text))
    editor.setTextCursor(cursor)
    editor.insertPlainText("!")
    expected_text += "!"
    expected_cursor = editor.textCursor().position()
    assert resource.text == expected_text
    assert resource.is_dirty()

    def unexpected_prompt(*_args):
        raise AssertionError("final retained close requested Save/Discard")

    application._peerDirtyCloseChooser = unexpected_prompt
    assert pyzo.editors.closeFile(editor)
    assert not any(candidate is editor for candidate in pyzo.editors)
    assert view_id in documents.registry.retained_view_ids
    retained = documents.registry.retained_view(view_id)
    assert retained.document_id == document_id
    assert documents.registry.resource(document_id).text == expected_text

    reopened = pyzo.main.reopen_retained_view(view_id)
    assert reopened is not editor
    assert documents.identity(reopened) == document_id
    assert documents.view_identity(reopened) == view_id
    assert reopened.toPlainText() == expected_text
    assert reopened.document().isModified()
    assert reopened.textCursor().position() == expected_cursor
    assert reopened.undo()
    assert reopened.toPlainText() == expected_text[:-1]
    assert reopened.redo()
    assert reopened.toPlainText() == expected_text
    return reopened


def run_probe():
    named_path = os.path.join(app_dir, "named.py")
    named = pyzo.editors.newFile().editor
    named.setPlainText("named\n")
    named.document().setModified(True)
    assert pyzo.editors.saveFile(named, named_path)
    named = _close_and_reopen(named, "named\n")

    untitled = pyzo.editors.newFile().editor
    untitled.setPlainText("untitled\n")
    untitled.document().setModified(True)
    _close_and_reopen(untitled, "untitled\n")

    print(
        "SECOND",
        named.filename,
        len(pyzo.application.documents.registry.retained_view_ids),
        flush=True,
    )
    pyzo.application.lifecycle.quit()


original_init = MainWindow.__init__


def init_and_probe(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    pyzo.callLater(run_probe)


MainWindow.__init__ = init_and_probe
pyzo._start.start()
