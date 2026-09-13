"""Two-process acceptance probe for retained closed-buffer restart behavior."""

from __future__ import annotations

import os
import sys
import types

from pyzo.util import paths

app_dir = os.environ["PYZO_020_APP_DIR"]
phase = os.environ["PYZO_020_PHASE"]
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

saved_path = os.path.join(app_dir, "closed.py")
main_window = None


def first():
    editor = pyzo.editors.newFile().editor
    editor.setPlainText("closed\n")
    editor.document().setModified(True)
    assert pyzo.editors.saveFile(editor, saved_path)
    editor.insertPlainText("!")
    assert editor.document().isModified()
    document_id = pyzo.application.documents.identity(editor)
    view_id = pyzo.application.documents.view_identity(editor)
    assert document_id is not None and view_id is not None

    assert pyzo.editors.closeFile(editor)
    assert not any(candidate.filename == saved_path for candidate in pyzo.editors)
    assert view_id in pyzo.application.documents.registry.retained_view_ids
    assert pyzo.workspacePersistence.save()
    print("FIRST", document_id, view_id, flush=True)
    pyzo.application.lifecycle.quit()


def second():
    registry = pyzo.application.documents.registry
    retained = registry.retained_view_ids
    assert len(retained) == 1, retained
    view_id = retained[0]
    descriptor = registry.retained_view(view_id)
    resource = registry.resource(descriptor.document_id)
    assert resource.path == saved_path
    assert resource.text == "!closed\n"
    assert not any(candidate.filename == saved_path for candidate in pyzo.editors)
    choices = main_window.retainedPeerBufferChoices()
    assert [entry["view_id"] for entry in choices] == [view_id]

    reopened = pyzo.main.reopen_retained_view(view_id)
    assert reopened is not None
    assert pyzo.application.documents.identity(reopened) == descriptor.document_id
    assert pyzo.application.documents.view_identity(reopened) == view_id
    assert reopened.toPlainText() == "!closed\n"
    assert reopened.document().isModified()
    print("SECOND", descriptor.document_id, view_id, flush=True)
    pyzo.application.lifecycle.quit()


original_init = MainWindow.__init__


def init_and_probe(self, *args, **kwargs):
    global main_window
    main_window = self
    original_init(self, *args, **kwargs)
    pyzo.callLater(first if phase == "first" else second)


MainWindow.__init__ = init_and_probe
pyzo._start.start()
