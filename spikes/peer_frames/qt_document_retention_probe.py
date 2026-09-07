"""Isolated real-Pyzo-editor retention probe.

This module is intentionally not imported by Pyzo production code. It proves
the adapter boundary using the public editor/document APIs and the existing
technology-neutral document registry; it does not inspect Qt's private undo
stack.
"""

from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
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
        probe_view = ProbeView(self._PyzoEditor(self.parent), view_id)
        probe_view.editor.setPlainText(self.registry.resource(self.document_id).text)
        probe_view.editor.document().setModified(True)
        self.registry.open_view(
            self.document_id,
            self.workspace_id,
            identity=view_id,
            state=deepcopy(state or DocumentViewState()),
            notify=lambda _origin, _text, revision: self.notifications.append(
                (view_id, revision)
            ),
        )
        probe_view.editor.textChanged.connect(
            lambda: self._editor_changed(probe_view)
        )
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
            state = value["state"]
            if not isinstance(state, dict):
                raise TypeError("probe snapshot view state is invalid")
            normalized = dict(state)
            normalized["selection"] = tuple(normalized.get("selection", (0, 0)))
            highlight = normalized.get("run_highlight")
            normalized["run_highlight"] = tuple(highlight) if highlight else None
            self.add_view(
                DocumentViewState(**normalized),
                ApplicationIdentity(IdentityKind.VIEW, view_value),
            )
        if old_views and any(view.editor in old_views for view in self.views):
            raise AssertionError("recreate reused an old editor widget")

    def _editor_changed(self, probe_view: ProbeView) -> None:
        if probe_view.syncing or self.document_id is None:
            return
        self.registry.replace_text(
            probe_view.view_id, probe_view.editor.toPlainText()
        )
        self._project_text(probe_view)

    def _project_text(self, source: ProbeView) -> None:
        assert self.document_id is not None
        text = self.registry.resource(self.document_id).text
        for target in self.views:
            if target is source:
                continue
            target.syncing = True
            try:
                cursor = target.editor.textCursor()
                target.editor.setPlainText(text)
                target.editor.setTextCursor(cursor)
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

        QtWidgets.QApplication.clipboard().setText(text)
        self.views[index].editor.paste()

    def delete_selection(self, index: int) -> None:
        cursor = self.views[index].editor.textCursor()
        cursor.removeSelectedText()
        self.views[index].editor.setTextCursor(cursor)

    def indent_selection(self, index: int, start: int, end: int) -> None:
        self.set_selection(index, start, end)
        self.views[index].editor.indentSelection()

    def undo(self, index: int) -> None:
        self.views[index].editor.undo()

    def redo(self, index: int) -> None:
        self.views[index].editor.redo()

    def set_selection(self, index: int, start: int, end: int) -> None:
        probe_view = self.views[index]
        cursor = probe_view.editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, cursor.MoveMode.KeepAnchor)
        probe_view.editor.setTextCursor(cursor)
        self.registry.view(probe_view.view_id).state.selection = (start, end)

    def serialize(self) -> dict[str, object]:
        for probe_view in self.views:
            cursor = probe_view.editor.textCursor()
            state = self.registry.view(probe_view.view_id).state
            state.cursor = cursor.position()
            state.selection = (cursor.selectionStart(), cursor.selectionEnd())
        return deepcopy(dict(self.registry.persistence_snapshot()))

    def destroy(self) -> None:
        for probe_view in self.views:
            probe_view.editor.deleteLater()
        self.views.clear()


def make_probe(parent=None) -> QtDocumentRetentionProbe:
    """Create a probe after the caller has created a QApplication."""
    probe = QtDocumentRetentionProbe(parent)
    probe.create()
    return probe
