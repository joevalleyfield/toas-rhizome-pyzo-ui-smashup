from __future__ import annotations

import unittest
from copy import deepcopy

from spikes.peer_frames.contract import PaneDescriptor, PaneKind, WorkspaceModel
from spikes.peer_frames.document_resources import (
    DocumentOperationStatus,
    DocumentResourceRegistry,
    DocumentViewState,
)
from spikes.peer_frames.fake_backend import FakeBackend
from spikes.peer_frames.identity import IdentityKind, new_identity
from spikes.peer_frames.lifecycle import (
    DirtyCloseChoice,
    DocumentCloseDisposition,
    DocumentViewRegistry,
)


class DocumentResourceStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = DocumentResourceRegistry()
        self.workspace_a = new_identity(IdentityKind.WORKSPACE)
        self.workspace_b = new_identity(IdentityKind.WORKSPACE)

    def create(self, text="initial", *, path="/project/example.py", dirty=False):
        return self.registry.create_document(text, path=path, dirty=dirty)

    def open(self, document_id, workspace_id=None, **kwargs):
        return self.registry.open_view(
            document_id, workspace_id or self.workspace_a, **kwargs
        )

    def test_pathless_and_named_documents_have_durable_path_independent_identity(self):
        pathless = self.registry.create_document()
        named = self.create()

        self.assertIs(pathless.kind, IdentityKind.DOCUMENT)
        self.assertIs(named.kind, IdentityKind.DOCUMENT)
        before = named
        self.assertTrue(
            self.registry.rename_document(named, "/renamed/example.py").applied
        )
        self.assertEqual(named, before)
        self.assertEqual(self.registry.resource(named).path, "/renamed/example.py")

    def test_shared_edits_dirty_and_undo_with_independent_workspace_view_state(self):
        document_id = self.create()
        events: dict[str, list[tuple[object, str, int]]] = {"a": [], "b": []}
        view_a = self.open(
            document_id,
            self.workspace_a,
            state=DocumentViewState(cursor=2, pinned=True, affiliation="project-a"),
            notify=lambda *event: events["a"].append(event),
        )
        view_b = self.open(
            document_id,
            self.workspace_b,
            state=DocumentViewState(cursor=8, scroll=40, affiliation="project-b"),
            notify=lambda *event: events["b"].append(event),
        )

        revision = self.registry.resource(document_id).revision
        self.registry.replace_text(view_a, "changed")
        resource = self.registry.resource(document_id)

        self.assertEqual(resource.revision, revision + 1)
        self.assertEqual(resource.text, "changed")
        self.assertTrue(resource.is_dirty())
        self.assertEqual(resource.undo_depth, 1)
        self.assertEqual(len(events["a"]), 1)
        self.assertEqual(len(events["b"]), 1)
        self.assertEqual(self.registry.view(view_a).state.cursor, 2)
        self.assertEqual(self.registry.view(view_b).state.cursor, 8)
        self.assertTrue(self.registry.view(view_a).state.pinned)
        self.assertFalse(self.registry.view(view_b).state.pinned)
        self.assertIsNot(
            self.registry.view(view_a).state,
            self.registry.view(view_b).state,
        )

        self.assertTrue(self.registry.undo(view_b))
        self.assertEqual(resource.text, "initial")
        self.assertFalse(resource.is_dirty())
        self.assertTrue(self.registry.redo(view_a))
        self.assertEqual(resource.text, "changed")

    def test_persistence_round_trip_restores_durable_identity_links_without_saving(self):
        writes = []
        document_id = self.registry.create_document(
            "initial",
            path="/project/shared.py",
            save=lambda path, text: writes.append((path, text)) or True,
        )
        view_a = self.open(
            document_id,
            self.workspace_a,
            state=DocumentViewState(cursor=3, pinned=True),
        )
        view_b = self.open(
            document_id,
            self.workspace_b,
            state=DocumentViewState(scroll=8, affiliation="b"),
        )
        self.registry.replace_text(view_a, "dirty")
        self.registry.set_main(self.workspace_b, document_id)
        snapshot = self.registry.persistence_snapshot()
        restored = DocumentResourceRegistry()

        restored.restore_persistence_snapshot(snapshot)

        self.assertEqual(restored.persistence_snapshot(), snapshot)
        self.assertEqual(restored.view(view_a).document_id, document_id)
        self.assertEqual(restored.view(view_b).document_id, document_id)
        self.assertEqual(restored.view(view_a).workspace_id, self.workspace_a)
        self.assertEqual(restored.view(view_b).workspace_id, self.workspace_b)
        self.assertTrue(restored.view(view_a).state.pinned)
        self.assertEqual(restored.main(self.workspace_b).document_id, document_id)
        self.assertTrue(restored.resource(document_id).is_dirty())
        self.assertEqual(writes, [])

    def test_invalid_persistence_restore_is_transactional(self):
        document_id = self.create()
        self.open(document_id)
        before = self.registry.persistence_snapshot()
        invalid = deepcopy(before)
        invalid["views"][next(iter(invalid["views"]))]["document_id"] = "missing"

        with self.assertRaises(KeyError):
            self.registry.restore_persistence_snapshot(invalid)

        self.assertEqual(self.registry.persistence_snapshot(), before)

    def test_noop_and_reentrant_edit_do_not_duplicate_mutations(self):
        document_id = self.create()
        recursive_results = []
        view_id = None

        def notify(_origin, _text, _revision):
            try:
                self.registry.replace_text(view_id, "recursive")
            except RuntimeError as error:
                recursive_results.append(str(error))

        view_id = self.open(document_id, notify=notify)
        before = self.registry.resource(document_id).revision

        self.assertEqual(self.registry.replace_text(view_id, "initial"), before)
        self.registry.replace_text(view_id, "once")

        resource = self.registry.resource(document_id)
        self.assertEqual(resource.text, "once")
        self.assertEqual(resource.revision, before + 1)
        self.assertEqual(resource.undo_depth, 1)
        self.assertEqual(recursive_results, ["recursive document mutation"])

    def test_move_changes_only_workspace_and_view_epoch(self):
        document_id = self.create(dirty=True)
        view_id = self.open(
            document_id,
            state=DocumentViewState(
                cursor=4,
                selection=(2, 4),
                scroll=9,
                focused=True,
                presentation={"zoom": 2},
                pinned=True,
                run_highlight=(1, 3),
                affiliation="project",
            ),
        )
        token = self.registry.view_token(view_id)
        resource_before = deepcopy(self.registry.snapshot()["documents"])
        state_before = deepcopy(self.registry.view(view_id).state)

        result = self.registry.move_view(view_id, self.workspace_b)

        self.assertTrue(result.applied)
        self.assertEqual(self.registry.view(view_id).workspace_id, self.workspace_b)
        self.assertEqual(self.registry.view(view_id).state, state_before)
        self.assertEqual(self.registry.snapshot()["documents"], resource_before)
        self.assertFalse(self.registry.token_is_current(token))
        self.assertTrue(
            self.registry.token_is_current(self.registry.view_token(view_id))
        )
        self.assertEqual(
            self.registry.move_view(view_id, self.workspace_b).status,
            DocumentOperationStatus.INVALID,
        )

    def test_atomic_save_as_preserves_identity_views_main_and_undo(self):
        saves = []
        document_id = self.create(dirty=True)
        view_a = self.open(document_id)
        view_b = self.open(document_id, self.workspace_b)
        self.registry.replace_text(view_a, "dirty text")
        self.registry.set_main(self.workspace_a, document_id)
        token = self.registry.resource_token(document_id)
        undo_depth = self.registry.resource(document_id).undo_depth

        result = self.registry.save_as(
            document_id,
            "/new/location.py",
            lambda path, text: saves.append((path, text)) or True,
        )

        resource = self.registry.resource(document_id)
        self.assertTrue(result.applied)
        self.assertEqual(result.document_id, document_id)
        self.assertEqual(resource.path, "/new/location.py")
        self.assertFalse(resource.is_dirty())
        self.assertEqual(resource.undo_depth, undo_depth)
        self.assertEqual(
            self.registry.views_for_document(document_id), (view_a, view_b)
        )
        self.assertEqual(self.registry.main(self.workspace_a).document_id, document_id)
        self.assertEqual(self.registry.main(self.workspace_a).path, "/new/location.py")
        self.assertEqual(saves, [("/new/location.py", "dirty text")])
        self.assertFalse(self.registry.token_is_current(token))

    def test_cancel_failure_and_path_collision_are_snapshot_atomic(self):
        first = self.create(path="/first.py", dirty=True)
        second = self.registry.create_document("second", path="/second.py")
        self.open(first)

        for operation in (
            lambda: self.registry.save_as(first, None, lambda _p, _t: True),
            lambda: self.registry.save_as(first, "/failed.py", lambda _p, _t: False),
            lambda: self.registry.save_as(
                first,
                "/raises.py",
                lambda _p, _t: (_ for _ in ()).throw(OSError("disk full")),
            ),
            lambda: self.registry.save_as(first, "/second.py", lambda _p, _t: True),
            lambda: self.registry.rename_document(first, "/second.py"),
        ):
            with self.subTest(operation=operation):
                before = deepcopy(self.registry.snapshot())
                result = operation()
                self.assertFalse(result.applied)
                self.assertEqual(self.registry.snapshot(), before)
                self.assertEqual(self.registry.resource(second).path, "/second.py")

    def test_adopted_foreground_save_does_not_write_twice(self):
        document_id = self.create(dirty=True)
        view_id = self.open(document_id)
        self.registry.replace_text(view_id, "saved by Pyzo")
        before_identity = document_id

        result = self.registry.adopt_saved(
            document_id, "/adopted.py", "saved by Pyzo"
        )

        resource = self.registry.resource(document_id)
        self.assertTrue(result.applied)
        self.assertEqual(document_id, before_identity)
        self.assertEqual(resource.path, "/adopted.py")
        self.assertEqual(resource.text, "saved by Pyzo")
        self.assertFalse(resource.is_dirty())
        self.assertEqual(resource.save_count, 0)

    def test_branch_creates_independent_identity_content_and_copied_view_state(self):
        document_id = self.create(dirty=True)
        source_view = self.open(
            document_id,
            self.workspace_b,
            state=DocumentViewState(
                cursor=7,
                selection=(3, 7),
                scroll=11,
                presentation={"theme": "blue"},
                pinned=True,
                affiliation="project-b",
            ),
        )
        self.registry.replace_text(source_view, "source current")

        result = self.registry.branch_view(source_view)

        self.assertTrue(result.applied)
        self.assertNotEqual(result.document_id, document_id)
        self.assertNotEqual(result.view_id, source_view)
        branch = self.registry.resource(result.document_id)
        source = self.registry.resource(document_id)
        self.assertEqual(branch.text, source.text)
        self.assertTrue(branch.is_dirty())
        self.assertEqual(branch.undo_depth, 0)
        self.assertEqual(
            self.registry.view(result.view_id).state,
            self.registry.view(source_view).state,
        )
        self.assertIsNot(
            self.registry.view(result.view_id).state,
            self.registry.view(source_view).state,
        )
        self.assertEqual(
            self.registry.view(result.view_id).workspace_id, self.workspace_b
        )

        self.registry.replace_text(result.view_id, "branch only")
        self.assertEqual(branch.text, "branch only")
        self.assertEqual(source.text, "source current")

    def test_branch_failure_leaves_original_snapshot_unchanged(self):
        document_id = self.create()
        source_view = self.open(document_id)
        existing_view = self.open(document_id, self.workspace_b)
        before = deepcopy(self.registry.snapshot())

        with self.assertRaisesRegex(ValueError, "already registered"):
            self.registry.branch_view(source_view, branch_view_id=existing_view)

        self.assertEqual(self.registry.snapshot(), before)

    def test_main_survives_zero_views_follows_rename_and_can_be_broken(self):
        document_id = self.create()
        view_id = self.open(document_id)
        main = self.registry.set_main(self.workspace_a, document_id)
        self.assertTrue(main.available)

        self.assertTrue(self.registry.close_view(view_id))
        self.assertEqual(self.registry.views_for_document(document_id), ())
        self.assertEqual(self.registry.main(self.workspace_a).document_id, document_id)
        self.assertTrue(self.registry.main(self.workspace_a).available)

        self.registry.rename_document(document_id, "/relocated.py")
        self.assertEqual(self.registry.main(self.workspace_a).path, "/relocated.py")
        self.registry.mark_unavailable(document_id)
        broken = self.registry.main(self.workspace_a)
        self.assertEqual(broken.document_id, document_id)
        self.assertFalse(broken.available)

        pathless = self.registry.create_document()
        with self.assertRaisesRegex(ValueError, "must be saved"):
            self.registry.set_main(self.workspace_b, pathless)
        self.registry.clear_main(self.workspace_a)
        self.assertIsNone(self.registry.main(self.workspace_a))

    def test_cache_tokens_reject_edit_move_rename_close_and_wrong_branch(self):
        document_id = self.create()
        view_id = self.open(document_id)

        resource_token = self.registry.resource_token(document_id)
        view_token = self.registry.view_token(view_id)
        applied = []
        self.assertTrue(
            self.registry.apply_if_current(view_token, lambda: applied.append("fresh"))
        )
        self.registry.replace_text(view_id, "edited")
        self.assertFalse(self.registry.apply_if_current(resource_token, lambda: None))
        self.assertFalse(self.registry.apply_if_current(view_token, lambda: None))

        view_token = self.registry.view_token(view_id)
        self.registry.move_view(view_id, self.workspace_b)
        self.assertFalse(self.registry.token_is_current(view_token))

        resource_token = self.registry.resource_token(document_id)
        self.registry.rename_document(document_id, "/renamed.py")
        self.assertFalse(self.registry.token_is_current(resource_token))

        branch = self.registry.branch_view(view_id)
        branch_token = self.registry.view_token(branch.view_id)
        self.assertNotEqual(branch_token.document_id, document_id)
        self.assertTrue(self.registry.token_is_current(branch_token))

        original_token = self.registry.view_token(view_id)
        self.registry.close_view(view_id)
        self.assertFalse(self.registry.token_is_current(original_token))
        self.assertEqual(applied, ["fresh"])

    def test_close_and_reopen_retains_identity_history_and_view_state(self):
        document_id = self.create(dirty=True)
        view_id = self.open(
            document_id,
            self.workspace_b,
            state=DocumentViewState(
                cursor=7, selection=(2, 7), scroll=13, presentation={"zoom": 2}
            ),
        )
        self.registry.replace_text(view_id, "edited")
        token = self.registry.view_token(view_id)
        before = deepcopy(self.registry.resource(document_id))

        self.assertTrue(self.registry.close_view(view_id))
        self.assertFalse(self.registry.token_is_current(token))
        self.assertEqual(self.registry.retained_view_ids, (view_id,))
        self.assertEqual(self.registry.resource(document_id).text, "edited")
        self.assertEqual(self.registry.resource(document_id).undo_depth, 1)
        self.assertFalse(self.registry.resource(document_id).live)

        reopened = self.registry.reopen_view(document_id)

        self.assertEqual(reopened, view_id)
        self.assertFalse(self.registry.token_is_current(token))
        self.assertEqual(self.registry.view(view_id).workspace_id, self.workspace_b)
        self.assertEqual(
            self.registry.view(view_id).state,
            DocumentViewState(
                cursor=7, selection=(2, 7), scroll=13, presentation={"zoom": 2}
            ),
        )
        self.assertEqual(self.registry.resource(document_id).text, before.text)
        self.assertEqual(self.registry.resource(document_id).undo_depth, before.undo_depth)
        self.assertTrue(self.registry.resource(document_id).live)

    def test_failed_reopen_preserves_named_and_untitled_retained_buffers(self):
        named = self.create("named")
        untitled = self.registry.create_document("untitled", dirty=True)
        named_view = self.open(named)
        untitled_view = self.open(untitled, self.workspace_b)
        self.registry.close_view(named_view)
        self.registry.close_view(untitled_view)
        before = deepcopy(self.registry.snapshot())

        with self.assertRaisesRegex(ValueError, "does not belong"):
            self.registry.reopen_view(named, view_id=untitled_view)

        self.assertEqual(self.registry.snapshot(), before)
        self.assertEqual(
            {self.registry.resource(document_id).path for document_id in (named, untitled)},
            {"/project/example.py", None},
        )
        self.assertEqual(
            self.registry.retained_views_for_document(untitled),
            (self.registry.retained_view(untitled_view),),
        )

    def test_current_content_and_identity_are_stable_run_and_recovery_provenance(self):
        document_id = self.create(dirty=True)
        view_id = self.open(document_id)
        self.registry.replace_text(view_id, "current unsaved buffer")

        resource = self.registry.resource(document_id)
        run_payload = (resource.identity, resource.text)
        recovery_payload = (resource.identity, resource.text, resource.path)

        self.assertEqual(run_payload, (document_id, "current unsaved buffer"))
        self.assertEqual(
            recovery_payload,
            (document_id, "current unsaved buffer", "/project/example.py"),
        )
        self.assertEqual(resource.save_count, 0)


class SharedDocumentCloseIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.resources = DocumentResourceRegistry()
        self.closes = DocumentViewRegistry()
        self.workspace_a = new_identity(IdentityKind.WORKSPACE)
        self.workspace_b = new_identity(IdentityKind.WORKSPACE)
        self.document_id = self.resources.create_document(
            "dirty", path="/shared.py", dirty=True, save=lambda _p, _t: True
        )
        self.model_a = WorkspaceModel(FakeBackend(), self.workspace_a)
        self.model_b = WorkspaceModel(FakeBackend(), self.workspace_b)

    def add_view(self, pane_id, workspace_id, model, *, pinned=False):
        view_id = new_identity(IdentityKind.VIEW)
        self.resources.open_view(
            self.document_id,
            workspace_id,
            identity=view_id,
            state=DocumentViewState(pinned=pinned),
        )
        resource = self.resources.resource(self.document_id)
        policy = self.closes.register_view(
            pane_id,
            self.document_id,
            resource,
            is_pinned=lambda view_id=view_id: self.resources.view(view_id).state.pinned,
            workspace_id=workspace_id,
            close_view=lambda view_id=view_id: self.resources.close_view(view_id),
        )
        self.assertTrue(
            model.register_pane(
                PaneDescriptor(pane_id, PaneKind.EDITOR, pane_id), policy
            ).applied
        )
        self.assertTrue(model.create_frame(pane_id, pane_id + "-frame").applied)
        return view_id

    def test_cross_workspace_non_final_close_never_saves_then_final_saves_once(self):
        self.add_view("view-a", self.workspace_a, self.model_a)
        self.add_view("view-b", self.workspace_b, self.model_b)
        resource = self.resources.resource(self.document_id)

        self.assertTrue(self.model_a.request_close_pane("view-a").applied)
        self.assertEqual(resource.save_count, 0)
        self.assertEqual(resource.close_count, 0)
        self.assertTrue(resource.live)

        result = self.model_b.request_close_pane(
            "view-b",
            lambda votes: self.closes.resolve_confirmations(
                votes, lambda _document_id, _resource: DirtyCloseChoice.SAVE
            ),
        )

        self.assertTrue(result.applied)
        self.assertEqual(resource.save_count, 1)
        self.assertEqual(resource.close_count, 1)
        self.assertEqual(
            resource.close_dispositions, [DocumentCloseDisposition.SAVED]
        )
        self.assertFalse(resource.live)

    def test_pinned_view_must_be_unpinned_before_close(self):
        view_id = self.add_view(
            "pinned", self.workspace_a, self.model_a, pinned=True
        )

        result = self.model_a.request_close_pane("pinned")
        self.assertFalse(result.applied)
        self.assertIn("pinned", result.detail)

        self.resources.update_view_state(view_id, pinned=False)
        result = self.model_a.request_close_pane(
            "pinned",
            lambda votes: self.closes.resolve_confirmations(
                votes, lambda _document_id, _resource: DirtyCloseChoice.DISCARD
            ),
        )
        self.assertTrue(result.applied)

    def test_close_registry_tracks_workspace_move_and_invalidates_epoch(self):
        self.add_view("view", self.workspace_a, self.model_a)
        before = self.closes.view_epoch("view")

        self.assertTrue(self.closes.move_view("view", self.workspace_b))
        self.assertEqual(
            self.closes.workspace_id_for_view("view"), self.workspace_b
        )
        self.assertEqual(self.closes.view_epoch("view"), before + 1)
        self.assertFalse(self.closes.move_view("view", self.workspace_b))


if __name__ == "__main__":
    unittest.main()
