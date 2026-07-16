from __future__ import annotations

import unittest

from spikes.peer_frames.contract import (
    OperationStatus,
    PaneDescriptor,
    PaneKind,
    WorkspaceModel,
)
from spikes.peer_frames.fake_backend import FakeBackend
from spikes.peer_frames.lifecycle import DocumentViewRegistry


class RecordingDocument:
    def __init__(self, *, dirty: bool = False):
        self.dirty = dirty
        self.close_count = 0

    def is_dirty(self) -> bool:
        return self.dirty

    def close_document(self) -> None:
        self.close_count += 1


class DocumentViewLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = WorkspaceModel(FakeBackend())
        self.registry = DocumentViewRegistry()

    def add_view(
        self,
        pane_id: str,
        document_id: str,
        document: RecordingDocument,
        frame_id: str,
        *,
        pinned: bool = False,
    ) -> None:
        policy = self.registry.register_view(
            pane_id,
            document_id,
            document,
            is_pinned=lambda: pinned,
        )
        self.assertTrue(
            self.model.register_pane(
                PaneDescriptor(pane_id, PaneKind.EDITOR, pane_id), policy
            ).applied
        )
        self.assertTrue(self.model.create_frame(pane_id, frame_id).applied)

    def test_closing_non_final_view_preserves_document(self) -> None:
        document = RecordingDocument()
        self.add_view("view-a", "document", document, "frame-a")
        self.add_view("view-b", "document", document, "frame-b")

        result = self.model.request_close_pane("view-a")

        self.assertTrue(result.applied)
        self.assertNotIn("view-a", self.model.panes)
        self.assertEqual(self.registry.view_ids("document"), {"view-b"})
        self.assertEqual(document.close_count, 0)
        self.assertFalse(self.model.shutdown_requested)

    def test_closing_final_clean_view_closes_document_once_not_application(self) -> None:
        document = RecordingDocument()
        self.add_view("only-view", "document", document, "only-frame")

        result = self.model.request_close_pane("only-view")

        self.assertTrue(result.applied)
        self.assertEqual(self.model.frames, {})
        self.assertEqual(self.registry.document_ids, frozenset())
        self.assertEqual(document.close_count, 1)
        self.assertFalse(self.model.shutdown_requested)
        self.assertEqual(
            self.model.request_close_pane("only-view").status,
            OperationStatus.INVALID,
        )
        self.assertEqual(document.close_count, 1)

    def test_transaction_closing_all_views_closes_document_once(self) -> None:
        document = RecordingDocument()
        self.add_view("view-a", "document", document, "workspace")
        self.add_view("view-b", "document", document, "temporary")
        self.assertTrue(self.model.tab("view-b", "view-a").applied)

        result = self.model.request_close_frame("workspace")

        self.assertTrue(result.applied)
        self.assertEqual(document.close_count, 1)
        self.assertEqual(self.registry.document_ids, frozenset())

    def test_transaction_closing_subset_of_views_preserves_document(self) -> None:
        document = RecordingDocument()
        self.add_view("view-a", "document", document, "workspace")
        self.add_view("view-b", "document", document, "temporary")
        self.add_view("survivor", "document", document, "survivor-frame")
        self.assertTrue(self.model.tab("view-b", "view-a").applied)

        result = self.model.request_close_frame("workspace")

        self.assertTrue(result.applied)
        self.assertEqual(self.registry.view_ids("document"), {"survivor"})
        self.assertEqual(document.close_count, 0)

    def test_dirty_non_final_view_can_close_but_final_view_is_protected(self) -> None:
        document = RecordingDocument(dirty=True)
        self.add_view("view-a", "document", document, "frame-a")
        self.add_view("view-b", "document", document, "frame-b")

        self.assertTrue(self.model.request_close_pane("view-a").applied)
        before = self.model.serialize_layout()
        result = self.model.request_close_pane("view-b")

        self.assertEqual(result.status, OperationStatus.REFUSED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(document.close_count, 0)

    def test_dirty_all_views_transaction_is_protected_before_mutation(self) -> None:
        document = RecordingDocument(dirty=True)
        self.add_view("view-a", "document", document, "workspace")
        self.add_view("view-b", "document", document, "temporary")
        self.assertTrue(self.model.tab("view-b", "view-a").applied)
        before = self.model.serialize_layout()

        result = self.model.request_close_frame("workspace")

        self.assertEqual(result.status, OperationStatus.REFUSED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(document.close_count, 0)

    def test_pinned_view_is_protected_before_mutation(self) -> None:
        document = RecordingDocument()
        self.add_view("pinned", "document", document, "frame", pinned=True)
        before = self.model.serialize_layout()

        result = self.model.request_close_pane("pinned")

        self.assertEqual(result.status, OperationStatus.REFUSED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(document.close_count, 0)

    def test_move_operations_do_not_touch_document_lifecycle(self) -> None:
        first = RecordingDocument()
        second = RecordingDocument()
        self.add_view("first", "first-document", first, "first-frame")
        self.add_view("second", "second-document", second, "second-frame")

        self.assertTrue(self.model.tab("second", "first").applied)
        self.assertTrue(self.model.float("second", "floated").applied)

        self.assertEqual(first.close_count, 0)
        self.assertEqual(second.close_count, 0)
        self.assertEqual(self.registry.view_ids("first-document"), {"first"})
        self.assertEqual(self.registry.view_ids("second-document"), {"second"})

    def test_binding_rollback_is_idempotent_and_does_not_close_document(self) -> None:
        document = RecordingDocument()
        self.registry.register_view("view", "document", document)

        self.registry.forget_view("view")
        self.registry.forget_view("view")

        self.assertIsNone(self.registry.document_id_for_view("view"))
        self.assertEqual(self.registry.document_ids, frozenset())
        self.assertEqual(document.close_count, 0)


if __name__ == "__main__":
    unittest.main()
