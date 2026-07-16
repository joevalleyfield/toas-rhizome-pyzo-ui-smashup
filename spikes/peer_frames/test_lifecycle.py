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
from spikes.peer_frames.lifecycle import (
    DirtyCloseChoice,
    DocumentCloseDisposition,
)


class RecordingDocument:
    def __init__(
        self,
        *,
        dirty: bool = False,
        save_result: bool = True,
        save_clears_dirty: bool = True,
        save_raises: bool = False,
    ):
        self.dirty = dirty
        self.save_result = save_result
        self.save_clears_dirty = save_clears_dirty
        self.save_raises = save_raises
        self.save_count = 0
        self.close_count = 0
        self.close_dispositions: list[DocumentCloseDisposition] = []

    def is_dirty(self) -> bool:
        return self.dirty

    def save_document(self) -> bool:
        self.save_count += 1
        if self.save_raises:
            raise OSError("save failed")
        if self.save_result and self.save_clears_dirty:
            self.dirty = False
        return self.save_result

    def close_document(self, disposition: DocumentCloseDisposition) -> None:
        self.close_count += 1
        self.close_dispositions.append(disposition)


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
        self.assertEqual(
            document.close_dispositions, [DocumentCloseDisposition.CLEAN]
        )
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

    def test_dirty_non_final_view_can_close_but_final_view_requires_choice(self) -> None:
        document = RecordingDocument(dirty=True)
        self.add_view("view-a", "document", document, "frame-a")
        self.add_view("view-b", "document", document, "frame-b")

        self.assertTrue(self.model.request_close_pane("view-a").applied)
        before = self.model.serialize_layout()
        result = self.model.request_close_pane("view-b")

        self.assertEqual(result.status, OperationStatus.CONFIRMATION_REQUIRED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(document.close_count, 0)

    def test_cancel_preserves_dirty_document_and_topology_without_save(self) -> None:
        document = RecordingDocument(dirty=True)
        self.add_view("view-a", "document", document, "workspace")
        self.add_view("view-b", "document", document, "temporary")
        self.assertTrue(self.model.tab("view-b", "view-a").applied)
        before = self.model.serialize_layout()

        result = self.model.request_close_frame(
            "workspace",
            lambda votes: self.registry.resolve_confirmations(
                votes, lambda _document_id, _document: DirtyCloseChoice.CANCEL
            ),
        )

        self.assertEqual(result.status, OperationStatus.CANCELLED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertTrue(document.dirty)
        self.assertEqual(document.save_count, 0)
        self.assertEqual(document.close_count, 0)

    def test_discard_is_deferred_until_transaction_commit(self) -> None:
        document = RecordingDocument(dirty=True)
        self.add_view("view", "document", document, "frame")

        result = self.model.request_close_pane(
            "view",
            lambda votes: self.registry.resolve_confirmations(
                votes, lambda _document_id, _document: DirtyCloseChoice.DISCARD
            ),
        )

        self.assertTrue(result.applied)
        self.assertEqual(document.save_count, 0)
        self.assertEqual(
            document.close_dispositions, [DocumentCloseDisposition.DISCARDED]
        )

    def test_save_must_succeed_and_clear_dirty_before_commit(self) -> None:
        for document in (
            RecordingDocument(dirty=True, save_result=False),
            RecordingDocument(dirty=True, save_clears_dirty=False),
            RecordingDocument(dirty=True, save_raises=True),
        ):
            with self.subTest(document=document):
                model = WorkspaceModel(FakeBackend())
                registry = DocumentViewRegistry()
                policy = registry.register_view("view", "document", document)
                model.register_pane(
                    PaneDescriptor("view", PaneKind.EDITOR, "View"), policy
                )
                model.create_frame("view", "frame")
                before = model.serialize_layout()

                result = model.request_close_pane(
                    "view",
                    lambda votes, registry=registry: registry.resolve_confirmations(
                        votes,
                        lambda _document_id, _document: DirtyCloseChoice.SAVE,
                    ),
                )

                self.assertEqual(result.status, OperationStatus.CANCELLED)
                self.assertEqual(model.serialize_layout(), before)
                self.assertEqual(document.close_count, 0)

    def test_successful_save_commits_with_saved_disposition(self) -> None:
        document = RecordingDocument(dirty=True)
        self.add_view("view", "document", document, "frame")

        result = self.model.request_close_pane(
            "view",
            lambda votes: self.registry.resolve_confirmations(
                votes, lambda _document_id, _document: DirtyCloseChoice.SAVE
            ),
        )

        self.assertTrue(result.applied)
        self.assertEqual(document.save_count, 1)
        self.assertFalse(document.dirty)
        self.assertEqual(
            document.close_dispositions, [DocumentCloseDisposition.SAVED]
        )

    def test_multi_document_choices_are_collected_before_first_save(self) -> None:
        first = RecordingDocument(dirty=True)
        second = RecordingDocument(dirty=True)
        self.add_view("first", "first-document", first, "workspace")
        self.add_view("second", "second-document", second, "temporary")
        self.assertTrue(self.model.tab("second", "first").applied)
        choices_seen: list[str] = []

        def choose(document_id, _document):
            self.assertEqual(first.save_count + second.save_count, 0)
            choices_seen.append(document_id)
            return (
                DirtyCloseChoice.SAVE
                if document_id == "first-document"
                else DirtyCloseChoice.DISCARD
            )

        result = self.model.request_close_frame(
            "workspace",
            lambda votes: self.registry.resolve_confirmations(votes, choose),
        )

        self.assertTrue(result.applied)
        self.assertEqual(choices_seen, ["first-document", "second-document"])
        self.assertEqual(first.save_count, 1)
        self.assertEqual(second.save_count, 0)
        self.assertEqual(
            first.close_dispositions, [DocumentCloseDisposition.SAVED]
        )
        self.assertEqual(
            second.close_dispositions, [DocumentCloseDisposition.DISCARDED]
        )

    def test_cancel_in_multi_document_choice_phase_performs_no_saves(self) -> None:
        first = RecordingDocument(dirty=True)
        second = RecordingDocument(dirty=True)
        self.add_view("first", "first-document", first, "workspace")
        self.add_view("second", "second-document", second, "temporary")
        self.assertTrue(self.model.tab("second", "first").applied)
        before = self.model.serialize_layout()

        result = self.model.request_close_frame(
            "workspace",
            lambda votes: self.registry.resolve_confirmations(
                votes,
                lambda document_id, _document: (
                    DirtyCloseChoice.SAVE
                    if document_id == "first-document"
                    else DirtyCloseChoice.CANCEL
                ),
            ),
        )

        self.assertEqual(result.status, OperationStatus.CANCELLED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(first.save_count + second.save_count, 0)

    def test_later_save_failure_keeps_topology_after_earlier_save(self) -> None:
        first = RecordingDocument(dirty=True)
        second = RecordingDocument(dirty=True, save_result=False)
        self.add_view("first", "first-document", first, "workspace")
        self.add_view("second", "second-document", second, "temporary")
        self.assertTrue(self.model.tab("second", "first").applied)
        before = self.model.serialize_layout()

        result = self.model.request_close_frame(
            "workspace",
            lambda votes: self.registry.resolve_confirmations(
                votes, lambda _document_id, _document: DirtyCloseChoice.SAVE
            ),
        )

        self.assertEqual(result.status, OperationStatus.CANCELLED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertFalse(first.dirty)
        self.assertTrue(second.dirty)
        self.assertEqual(first.save_count, 1)
        self.assertEqual(second.save_count, 1)
        self.assertEqual(first.close_count + second.close_count, 0)

    def test_all_views_of_one_dirty_document_prompt_once(self) -> None:
        document = RecordingDocument(dirty=True)
        self.add_view("view-a", "document", document, "workspace")
        self.add_view("view-b", "document", document, "temporary")
        self.assertTrue(self.model.tab("view-b", "view-a").applied)
        prompts = []

        result = self.model.request_close_frame(
            "workspace",
            lambda votes: self.registry.resolve_confirmations(
                votes,
                lambda document_id, _document: prompts.append(document_id)
                or DirtyCloseChoice.DISCARD,
            ),
        )

        self.assertTrue(result.applied)
        self.assertEqual(prompts, ["document"])
        self.assertEqual(document.close_count, 1)

    def test_truthy_generic_confirmation_cannot_bypass_resolution(self) -> None:
        document = RecordingDocument(dirty=True)
        self.add_view("view", "document", document, "frame")
        before = self.model.serialize_layout()

        result = self.model.request_close_pane("view", lambda _votes: True)

        self.assertEqual(result.status, OperationStatus.REFUSED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(document.close_count, 0)

    def test_reentrant_close_is_refused_while_choice_dialog_is_active(self) -> None:
        document = RecordingDocument(dirty=True)
        self.add_view("view", "document", document, "frame")
        nested_results = []

        def choose(_document_id, _document):
            nested_results.append(self.model.request_close_pane("view"))
            return DirtyCloseChoice.CANCEL

        result = self.model.request_close_pane(
            "view",
            lambda votes: self.registry.resolve_confirmations(votes, choose),
        )

        self.assertEqual(result.status, OperationStatus.CANCELLED)
        self.assertEqual(nested_results[0].status, OperationStatus.REFUSED)
        self.assertIn("already in progress", nested_results[0].detail)

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
