from __future__ import annotations

import unittest


class QtDocumentRetentionProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import pyzo
            from pyzo.util._locale import translate

            pyzo.translate = translate
            from pyzo.qt import QtWidgets

            cls.QtWidgets = QtWidgets
            cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        except Exception as error:  # pragma: no cover - host capability gate
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
        from spikes.peer_frames.qt_document_retention_probe import make_probe
        from spikes.peer_frames.document_resources import DocumentResourceRegistry

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


if __name__ == "__main__":
    unittest.main()
