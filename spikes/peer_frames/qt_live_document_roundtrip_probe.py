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
import time
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
from pyzo.qt import QtCore, QtGui, QtWidgets

phase = os.environ["PYZO_019_PHASE"]
saved_path = os.path.join(app_dir, "saved.py")
main_window = None
checkpoint_started = None


def finish_after_forced_crash():
    item = pyzo.editors.newFile()
    editor = item.editor
    editor.setPlainText("crash\n")
    editor.document().setModified(True)
    assert pyzo.editors.saveFile(editor, saved_path)
    editor.insertPlainText("!")
    manifest = os.path.join(app_dir, "workspaces", "manifest.json")
    before_checkpoint = os.stat(manifest).st_mtime_ns

    def crash_after_checkpoint():
        assert os.stat(manifest).st_mtime_ns > before_checkpoint
        print("CRASH DURABLE", flush=True)
        os._exit(42)

    QtCore.QTimer.singleShot(1500, crash_after_checkpoint)


def inspect_after_forced_crash():
    snapshot = pyzo.application.documents.registry.persistence_snapshot()
    record = next(
        value for value in snapshot["documents"].values()
        if value.get("path") == saved_path
    )
    assert record["text"] == "!crash\n", record
    assert record["clean_text"] == "crash\n", record
    editor = next(
        editor for editor in pyzo.editors if editor.filename == saved_path
    )
    assert editor.toPlainText() == "!crash\n"
    assert editor.document().isModified()
    assert editor.undo()
    assert editor.toPlainText() == "crash\n"
    assert editor.redo()
    assert editor.toPlainText() == "!crash\n"
    print("CRASH RESTORED", flush=True)
    main_window._peerDirtyCloseChooser = (
        lambda _document_id, _lifecycle: "discard"
    )
    main_window._peerShellCloseChooser = (
        lambda _pane_id, _lifecycle: "terminate"
    )
    pyzo.application.lifecycle.quit()


def finish_external_first():
    item = pyzo.editors.newFile()
    editor = item.editor
    editor.setPlainText("disk\n")
    editor.document().setModified(True)
    assert pyzo.editors.saveFile(editor, saved_path)
    editor.setPlainText("retained\n")
    editor.document().setModified(True)
    manifest = os.path.join(app_dir, "workspaces", "manifest.json")
    before_checkpoint = os.stat(manifest).st_mtime_ns

    def finish_after_checkpoint():
        assert os.stat(manifest).st_mtime_ns > before_checkpoint
        print("EXTERNAL DURABLE", flush=True)
        main_window._peerDirtyCloseChooser = (
            lambda _document_id, _lifecycle: "discard"
        )
        main_window._peerShellCloseChooser = (
            lambda _pane_id, _lifecycle: "terminate"
        )
        pyzo.application.lifecycle.quit()

    QtCore.QTimer.singleShot(1500, finish_after_checkpoint)


def inspect_external_second():
    external_text = "# coding: latin-1\nexternal é\n"
    assert open(saved_path, "rb").read() == external_text.encode("latin-1")
    editors = [
        editor for editor in pyzo.editors if editor.filename == saved_path
    ]
    assert len(editors) == 1, editors
    editor = editors[0]
    assert editor.toPlainText() == "retained\n"
    assert editor.document().isModified()
    assert getattr(editor, "_peerExternalConflict", False)
    assert editor._peerExternalText == external_text
    assert editor._peerExternalSignature == main_window._peerFileSignature(saved_path)
    assert editor._peerExternalEncoding.lower() in {"iso-8859-1", "latin-1"}
    conflict_host = pyzo.editors._group_for_editor(editor)
    assert "⚠" in main_window._editorHosts[conflict_host].windowTitle()
    record = next(
        value
        for value in pyzo.application.documents.registry.persistence_snapshot()[
            "documents"
        ].values()
        if value.get("path") == saved_path
    )
    assert record["clean_text"] == "disk\n", record
    assert record["external_conflict"] is True, record
    assert record["external_text"] == external_text, record
    assert record["external_signature"] == editor._peerExternalSignature, record
    assert record["external_encoding"].lower() in {"iso-8859-1", "latin-1"}, record
    assert open(saved_path, "rb").read() == external_text.encode("latin-1")
    print("EXTERNAL CONFLICT", flush=True)
    assert main_window._savePeerWorkspacePersistence()
    main_window._peerDirtyCloseChooser = (
        lambda _document_id, _lifecycle: "discard"
    )
    main_window._peerShellCloseChooser = (
        lambda _pane_id, _lifecycle: "terminate"
    )
    pyzo.application.lifecycle.quit()


def inspect_external_third():
    external_text = "# coding: latin-1\nexternal é\n"
    assert open(saved_path, encoding="utf-8").read() == "disk\n"
    editor = next(editor for editor in pyzo.editors if editor.filename == saved_path)
    resource = pyzo.application.documents.resource(editor)
    assert resource.external_conflict
    assert resource.external_text == external_text
    assert resource.external_latest_text == "disk\n"
    assert resource.external_latest_signature == main_window._peerFileSignature(saved_path)
    assert pyzo.application.documents.resolve_external(
        editor, "retained\n", clean=False
    )
    assert resource.text == "retained\n"
    assert not resource.external_conflict
    assert resource.external_text is None
    assert editor.toPlainText() == "retained\n"
    assert not getattr(editor, "_peerExternalConflict", False)
    print("EXTERNAL RESOLVED", flush=True)
    main_window._peerDirtyCloseChooser = (
        lambda _document_id, _lifecycle: "discard"
    )
    main_window._peerShellCloseChooser = (
        lambda _pane_id, _lifecycle: "terminate"
    )
    pyzo.application.lifecycle.quit()


def finish_failed_checkpoint():
    item = pyzo.editors.newFile()
    editor = item.editor
    editor.setPlainText("source\n")
    editor.document().setModified(True)
    assert pyzo.editors.saveFile(editor, saved_path)
    editor.setPlainText("unsaved\n")
    editor.document().setModified(True)
    manifest = os.path.join(app_dir, "workspaces", "manifest.json")
    before_checkpoint = os.stat(manifest).st_mtime_ns

    original_save = main_window._savePeerWorkspacePersistence

    def fail_save(*_args, **_kwargs):
        raise OSError("injected persistence failure")

    main_window._savePeerWorkspacePersistence = fail_save

    def inspect_failed_checkpoint():
        state = main_window._peerRetentionCoordinator.state
        assert state.status.value == "failed", state
        assert os.stat(manifest).st_mtime_ns == before_checkpoint
        assert open(saved_path, encoding="utf-8").read() == "source\n"
        failure_message = main_window._peerStatusService.currentMessage().lower()
        assert "checkpoint failed" in failure_message, failure_message
        result = main_window._requestPeerApplicationExit(
            main_window._ApplicationExitDisposition.QUIT
        )
        assert result.value == "cancelled", result
        assert any(candidate is editor for candidate in pyzo.editors)
        assert main_window._peerWorkspace.panes
        print("CHECKPOINT FAILURE VISIBLE CLOSE REFUSED", flush=True)
        main_window._savePeerWorkspacePersistence = original_save
        main_window._peerApplicationExitRequested = False
        assert main_window._peerRetentionCoordinator.retry()
        assert main_window._peerRetentionCoordinator.state.status.value == "durable"
        print("CHECKPOINT RETRY COMPLETED", flush=True)
        QtWidgets.qApp.exit(0)

    QtCore.QTimer.singleShot(1500, inspect_failed_checkpoint)


def finish_first():
    global checkpoint_started
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
    editor.document().setModified(False)
    assert not editor.document().isModified()
    resource = pyzo.application.documents.resource(editor)
    assert resource.text == "abc\n"
    assert resource.undo_depth == 1

    def finish_after_automatic_checkpoint():
        assert os.stat(manifest).st_mtime_ns > before_checkpoint
        latency = time.monotonic() - checkpoint_started
        print(
            "FIRST",
            resource.text.strip(),
            resource.undo_depth,
            "CHECKPOINT_LATENCY",
            f"{latency:.3f}",
            "HISTORY",
            resource.undo_depth,
            flush=True,
        )
        main_window._peerDirtyCloseChooser = (
            lambda _document_id, _lifecycle: "discard"
        )
        main_window._peerShellCloseChooser = (
            lambda _pane_id, _lifecycle: "terminate"
        )
        pyzo.application.lifecycle.quit()

    checkpoint_started = time.monotonic()
    QtCore.QTimer.singleShot(1500, finish_after_automatic_checkpoint)


def finish_sustained_latency():
    item = pyzo.editors.newFile()
    editor = item.editor
    editor.setPlainText("base\n")
    editor.document().setModified(True)
    assert pyzo.editors.saveFile(editor, saved_path)
    resource = pyzo.application.documents.resource(editor)
    coordinator = main_window._peerRetentionCoordinator
    original_writer = coordinator._writer
    completion_times = {}
    edit_times = {}
    completed_revisions = []
    completion_latencies = []
    coalesced_batch_sizes = []

    def timed_writer(snapshot, complete):
        def timed_complete(revision, error=None):
            completed_at = time.monotonic()
            completion_times[revision] = completed_at
            previous_revision = completed_revisions[-1] if completed_revisions else 0
            batch_edits = [
                edit_revision
                for edit_revision in edit_times
                if previous_revision < edit_revision <= revision
            ]
            if batch_edits:
                completion_latencies.append(
                    completed_at - min(edit_times[edit_revision] for edit_revision in batch_edits)
                )
                coalesced_batch_sizes.append(len(batch_edits))
            completed_revisions.append(revision)
            complete(revision, error)

        original_writer(snapshot, timed_complete)

    coordinator._writer = timed_writer
    groups = iter(range(8))
    final_edit_time = None

    def continue_editing():
        nonlocal final_edit_time
        try:
            group = next(groups)
        except StopIteration:
            final_edit_time = time.monotonic()
            target_revision = coordinator._next_revision

            def wait_for_completion():
                state = coordinator.state
                if (
                    target_revision is not None
                    and state.durable_revision is not None
                    and state.durable_revision >= target_revision
                ):
                    assert completion_latencies, (completion_times, edit_times)
                    coalesced_batches = sum(size > 1 for size in coalesced_batch_sizes)
                    writes_during_edit = sum(
                        completion_times[revision] <= final_edit_time
                        for revision in completion_times
                    )
                    workspace_root = os.path.join(app_dir, "workspaces")
                    storage_bytes = sum(
                        os.path.getsize(os.path.join(root, filename))
                        for root, _directories, filenames in os.walk(workspace_root)
                        for filename in filenames
                    )
                    history_entries = len(resource._undo) + len(resource._redo)
                    print(
                        "SUSTAINED CHECKPOINT",
                        "MAX_LATENCY",
                        f"{max(completion_latencies):.3f}",
                        "WRITES_DURING_EDIT",
                        writes_during_edit,
                        "COALESCED_BATCHES",
                        coalesced_batches,
                        "HISTORY_ENTRIES",
                        history_entries,
                        "STORAGE_BYTES",
                        storage_bytes,
                        flush=True,
                    )
                    main_window._peerDirtyCloseChooser = (
                        lambda _document_id, _lifecycle: "discard"
                    )
                    main_window._peerShellCloseChooser = (
                        lambda _pane_id, _lifecycle: "terminate"
                    )
                    pyzo.application.lifecycle.quit()
                    return
                QtCore.QTimer.singleShot(25, wait_for_completion)

            wait_for_completion()
            return
        for index in range(3):
            editor.insertPlainText(f"group-{group:02d}-{index}\n")
            editor.document().setModified(True)
            edit_times[coordinator._next_revision] = time.monotonic()
        if group < 7:
            editor.moveCursor(QtGui.QTextCursor.MoveOperation.Start)
            editor.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        QtCore.QTimer.singleShot(180, continue_editing)

    continue_editing()


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
        for view_group in (snapshot["views"], snapshot["retained_views"])
        for value in view_group.values()
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
    main_window._peerDirtyCloseChooser = (
        lambda _document_id, _lifecycle: "discard"
    )
    main_window._peerShellCloseChooser = (
        lambda _pane_id, _lifecycle: "terminate"
    )
    pyzo.application.lifecycle.quit()


original_init = MainWindow.__init__


def init_and_probe(self, *args, **kwargs):
    global main_window
    original_init(self, *args, **kwargs)
    main_window = self
    callbacks = {
        "first": finish_first,
        "second": inspect_second,
        "crash": finish_after_forced_crash,
        "crash-second": inspect_after_forced_crash,
        "external-first": finish_external_first,
        "external-second": inspect_external_second,
        "external-third": inspect_external_third,
        "failed-checkpoint": finish_failed_checkpoint,
        "latency": finish_sustained_latency,
    }
    pyzo.callLater(callbacks[phase])


MainWindow.__init__ = init_and_probe
pyzo._start.start()
