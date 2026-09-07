"""Isolated real-Pyzo-editor retention probe.

This module is intentionally not imported by Pyzo production code. It proves
the adapter boundary using the public editor/document APIs and the existing
technology-neutral document registry; it does not inspect Qt's private undo
stack.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .document_resources import DocumentResourceRegistry, DocumentViewState
from .identity import ApplicationIdentity, IdentityKind, new_identity


@dataclass
class ProbeView:
    editor: Any
    view_id: ApplicationIdentity
    syncing: bool = False


class QtDocumentRetentionProbe:
    """Bind two real Pyzo editors to one shared retained document resource."""

    def __init__(self, parent=None):
        from pyzo.core.editor import PyzoEditor

        self._PyzoEditor = PyzoEditor
        self.workspace_id = new_identity(IdentityKind.WORKSPACE)
        self.document_id = None
        self.registry = DocumentResourceRegistry()
        self.views: list[ProbeView] = []
        self.notifications: list[tuple[ApplicationIdentity, int]] = []
        self.parent = parent
        self._pending: tuple[ApplicationIdentity, str] | None = None
        PyzoEditor = self._PyzoEditor
        probe = self

        class BoundRetentionEditor(PyzoEditor):
            def undo(self):
                view = next(view for view in probe.views if view.editor is self)
                probe.undo(probe.views.index(view))

            def redo(self):
                view = next(view for view in probe.views if view.editor is self)
                probe.redo(probe.views.index(view))

        self._RetentionEditor = BoundRetentionEditor

    def create(self, text: str = "café\nsecond\n") -> None:
        self.document_id = self.registry.create_document(text, dirty=True)
        self.add_view(DocumentViewState(cursor=0, selection=(0, 0)))
        self.add_view(DocumentViewState(cursor=2, selection=(1, 4)))

    def add_view(
        self,
        state: DocumentViewState | None = None,
        identity: ApplicationIdentity | None = None,
    ) -> ProbeView:
        if self.document_id is None:
            raise RuntimeError("create the document before adding views")
        view_id = identity or new_identity(IdentityKind.VIEW)
        self.registry.open_view(
            self.document_id,
            self.workspace_id,
            identity=view_id,
            state=deepcopy(state or DocumentViewState()),
            notify=lambda _origin, _text, revision: self.notifications.append(
                (view_id, revision)
            ),
        )
        return self._bind_view(view_id)

    def _bind_view(self, view_id: ApplicationIdentity) -> ProbeView:
        """Create a widget for an already-registered registry view."""

        if self.document_id is None:
            raise RuntimeError("create the document before binding a view")
        if view_id in {view.view_id for view in self.views}:
            raise ValueError(f"view is already bound: {view_id}")
        probe_view = ProbeView(self._RetentionEditor(self.parent), view_id)
        self._set_projected_text(probe_view.editor, self.registry.resource(self.document_id).text)
        probe_view.editor.document().setModified(True)
        probe_view.editor.textChanged.connect(
            lambda: self._editor_changed(probe_view)
        )
        from pyzo.qt import QtGui

        undo_shortcut = QtGui.QShortcut(
            QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Undo),
            probe_view.editor,
        )
        undo_shortcut.activated.connect(
            lambda: self.undo(self.views.index(probe_view))
        )
        redo_shortcut = QtGui.QShortcut(
            QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Redo),
            probe_view.editor,
        )
        redo_shortcut.activated.connect(
            lambda: self.redo(self.views.index(probe_view))
        )
        probe_view.editor._retention_shortcuts = (undo_shortcut, redo_shortcut)
        self._apply_view_state(probe_view)
        self.views.append(probe_view)
        return probe_view

    def recreate(self, snapshot: dict[str, object]) -> None:
        """Destroy widgets and restore fresh real editors from a registry snapshot."""
        old_views = tuple(view.editor for view in self.views)
        self.destroy()
        self.registry = DocumentResourceRegistry()
        self.registry.restore_persistence_snapshot(snapshot)
        document_value = next(iter(snapshot["documents"]))
        self.document_id = ApplicationIdentity(IdentityKind.DOCUMENT, document_value)
        view_records = snapshot["views"]
        if not isinstance(view_records, dict):
            raise TypeError("probe snapshot views must be an object")
        first = next(iter(view_records.values()))
        if not isinstance(first, dict):
            raise TypeError("probe snapshot view must be an object")
        self.workspace_id = ApplicationIdentity(
            IdentityKind.WORKSPACE, first["workspace_id"]
        )
        for view_value, value in view_records.items():
            if not isinstance(view_value, str) or not isinstance(value, dict):
                raise TypeError("probe snapshot view identity is invalid")
            # restore_persistence_snapshot already registered this view. Bind a
            # fresh widget to that record instead of registering its identity a
            # second time.
            self._bind_view(ApplicationIdentity(IdentityKind.VIEW, view_value))
        if old_views and any(view.editor in old_views for view in self.views):
            raise AssertionError("recreate reused an old editor widget")

    def _editor_changed(self, probe_view: ProbeView) -> None:
        if probe_view.syncing or self.document_id is None:
            return
        text = probe_view.editor.toPlainText()
        if self._pending is not None and self._pending[0] != probe_view.view_id:
            self.flush_pending()
        if self._pending is None:
            self._pending = (probe_view.view_id, text)
        else:
            self._pending = (self._pending[0], text)
        self._project_text(probe_view, text=text)

    def flush_pending(self) -> None:
        if self._pending is None:
            return
        view_id, text = self._pending
        self.registry.replace_text(view_id, text)
        self._pending = None

    def _set_projected_text(self, editor: Any, text: str) -> None:
        """Project text without changing selection or creating native history."""

        from pyzo.qt import QtCore

        cursor = editor.textCursor()
        position = cursor.position()
        anchor = cursor.anchor()
        with QtCore.QSignalBlocker(editor):
            editor.setUndoRedoEnabled(False)
            editor.setPlainText(text)
        position = min(position, len(text))
        anchor = min(anchor, len(text))
        cursor = editor.textCursor()
        cursor.setPosition(anchor)
        cursor.setPosition(position, cursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)

    def _project_text(
        self, source: ProbeView | None = None, *, text: str | None = None
    ) -> None:
        assert self.document_id is not None
        text = self.registry.resource(self.document_id).text if text is None else text
        for target in self.views:
            target.syncing = True
            try:
                if target is not source:
                    self._set_projected_text(target.editor, text)
            finally:
                target.syncing = False

    def _apply_view_state(self, probe_view: ProbeView) -> None:
        state = self.registry.view(probe_view.view_id).state
        cursor = probe_view.editor.textCursor()
        cursor.setPosition(state.cursor)
        if state.selection[0] != state.selection[1]:
            cursor.setPosition(state.selection[0])
            cursor.setPosition(state.selection[1], cursor.MoveMode.KeepAnchor)
        probe_view.editor.setTextCursor(cursor)

    def paste(self, index: int, text: str) -> None:
        from pyzo.qt import QtWidgets

        self.flush_pending()
        QtWidgets.QApplication.clipboard().setText(text)
        self.views[index].editor.paste()

    def delete_selection(self, index: int) -> None:
        cursor = self.views[index].editor.textCursor()
        cursor.removeSelectedText()
        self.views[index].editor.setTextCursor(cursor)

    def indent_selection(self, index: int, start: int, end: int) -> None:
        self.flush_pending()
        self.set_selection(index, start, end)
        self.views[index].editor.indentSelection()

    def undo(self, index: int) -> None:
        self.flush_pending()
        view = self.views[index]
        if self.registry.undo(view.view_id):
            self._project_text()
            self._notify_parser()

    def redo(self, index: int) -> None:
        self.flush_pending()
        view = self.views[index]
        if self.registry.redo(view.view_id):
            self._project_text()
            self._notify_parser()

    def _notify_parser(self) -> None:
        import pyzo

        parser = getattr(pyzo, "parser", None)
        if parser is not None:
            for view in self.views:
                parser.parseThis(view.editor)

    def set_selection(self, index: int, start: int, end: int) -> None:
        probe_view = self.views[index]
        cursor = probe_view.editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, cursor.MoveMode.KeepAnchor)
        probe_view.editor.setTextCursor(cursor)
        self.registry.view(probe_view.view_id).state.selection = (start, end)

    def serialize(self) -> dict[str, object]:
        self.flush_pending()
        for probe_view in self.views:
            cursor = probe_view.editor.textCursor()
            state = self.registry.view(probe_view.view_id).state
            state.cursor = cursor.position()
            state.selection = (cursor.selectionStart(), cursor.selectionEnd())
        return deepcopy(dict(self.registry.persistence_snapshot()))

    def destroy(self) -> None:
        from pyzo.qt import QtCore, QtWidgets

        destroyed = []
        for probe_view in self.views:
            probe_view.editor.destroyed.connect(lambda: destroyed.append(True))
            probe_view.editor.deleteLater()
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
            app.processEvents()
        if len(destroyed) != len(self.views):
            raise AssertionError("destroy did not drain all editor widgets")
        self.views.clear()


def make_probe(parent=None) -> QtDocumentRetentionProbe:
    """Create a probe after the caller has created a QApplication."""
    probe = QtDocumentRetentionProbe(parent)
    probe.create()
    return probe
