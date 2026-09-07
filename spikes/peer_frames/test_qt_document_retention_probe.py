from __future__ import annotations

import tempfile
import unittest
from types import SimpleNamespace


class QtDocumentRetentionProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import pyzo

            # Importing _start establishes the normal Pyzo config object before
            # importing PyzoEditor, whose module-level code reads it.
            import pyzo._start
            from pyzo.util._locale import translate

            cls.config_dir = tempfile.TemporaryDirectory(prefix="pyzo-qt-probe-")
            pyzo.appConfigDir = cls.config_dir.name
            pyzo.appDataDir = cls.config_dir.name
            pyzo._saveConfigFile = False
            pyzo._start.loadConfig(defaultsOnly=True)
            pyzo.translate = translate
            from pyzo.qt import QtWidgets

            cls.QtWidgets = QtWidgets
            cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
            from pyzo.core import menu
            from pyzo.core.main import loadIcons

            loadIcons()
            pyzo.keyMapper = menu.KeyMapper()
            pyzo.editors = SimpleNamespace(
                _findReplace=SimpleNamespace(
                    startFind=lambda: None,
                    findSelection=lambda: None,
                    findSelectionBw=lambda: None,
                ),
                getCurrentEditor=lambda: None,
            )
            pyzo.parser = SimpleNamespace(parseThis=lambda _editor: None)
            pyzo.metadata = SimpleNamespace(cursor=lambda _editor: None)
            pyzo.runCommands = SimpleNamespace(run_selected=lambda: None)
            pyzo.toolManager = SimpleNamespace(getTool=lambda _name: None)
        except Exception as error:  # noqa: BLE001  # pragma: no cover - capability gate
            raise unittest.SkipTest(f"real Qt editor unavailable: {error}")

    def test_shared_real_edit_and_independent_selections(self):
        from spikes.peer_frames.qt_document_retention_probe import make_probe

        probe = make_probe()
        try:
            first, second = probe.views
            probe.set_selection(0, 0, 4)
            first.editor.insertPlainText("é")
            self.assertEqual(first.editor.toPlainText(), second.editor.toPlainText())
            self.assertEqual(second.editor.textCursor().selectionStart(), 1)
            self.assertEqual(second.editor.textCursor().selectionEnd(), 4)
            self.assertGreaterEqual(len(probe.notifications), 1)
        finally:
            probe.destroy()

    def test_serialized_registry_restores_document_and_view_state(self):
        from spikes.peer_frames.document_resources import DocumentResourceRegistry
        from spikes.peer_frames.qt_document_retention_probe import make_probe

        probe = make_probe()
        try:
            probe.set_selection(1, 1, 5)
            snapshot = probe.serialize()
            restored = DocumentResourceRegistry()
            restored.restore_persistence_snapshot(snapshot)
            self.assertEqual(
                restored.resource(probe.document_id).text,
                probe.registry.resource(probe.document_id).text,
            )
            self.assertEqual(len(restored.view_ids), 2)
            self.assertEqual(
                restored.view(probe.views[1].view_id).state.selection,
                (1, 5),
            )
            old_editors = tuple(view.editor for view in probe.views)
            probe.recreate(snapshot)
            self.assertTrue(all(view.editor not in old_editors for view in probe.views))
            self.assertEqual(probe.views[1].editor.toPlainText(), "café\nsecond\n")
            self.assertEqual(
                probe.registry.view(probe.views[1].view_id).state.selection,
                (1, 5),
            )
        finally:
            probe.destroy()

    def test_native_edit_transactions_and_redo_invalidation(self):
        from spikes.peer_frames.qt_document_retention_probe import make_probe

        probe = make_probe()
        try:
            editor = probe.views[0].editor
            cursor = editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            editor.setTextCursor(cursor)
            editor.insertPlainText(" + edit")
            self.assertIn("+ edit", editor.toPlainText())
            self.assertGreaterEqual(probe.registry.resource(probe.document_id).undo_depth, 1)
            probe.undo(0)
            self.assertNotIn("+ edit", editor.toPlainText())
            probe.redo(0)
            self.assertIn("+ edit", editor.toPlainText())
            probe.undo(0)
            probe.paste(0, "pasted")
            self.assertIn("pasted", editor.toPlainText())
            probe.indent_selection(0, 0, len(editor.toPlainText()))
            self.assertTrue(editor.toPlainText().startswith("    ") or "\t" in editor.toPlainText())
        finally:
            probe.destroy()

    def test_authoritative_history_survives_widget_recreation(self):
        from spikes.peer_frames.qt_document_retention_probe import make_probe

        probe = make_probe()
        try:
            editor = probe.views[0].editor
            cursor = editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            editor.setTextCursor(cursor)
            editor.insertPlainText(" + edit")
            snapshot = probe.serialize()
            probe.recreate(snapshot)

            probe.undo(1)
            self.assertEqual(probe.views[0].editor.toPlainText(), "café\nsecond\n")
            self.assertEqual(probe.views[1].editor.toPlainText(), "café\nsecond\n")
            probe.redo(1)
            self.assertTrue(probe.views[0].editor.toPlainText().endswith(" + edit"))
            self.assertEqual(
                probe.views[0].editor.toPlainText(),
                probe.views[1].editor.toPlainText(),
            )
        finally:
            probe.destroy()


if __name__ == "__main__":
    unittest.main()
