from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from spikes.peer_frames.document_resources import DocumentResourceRegistry
from spikes.peer_frames.identity import ApplicationIdentity, IdentityKind
from spikes.peer_frames.workspace_persistence import WorkspacePersistenceStore


class LegacyRecoverySelectionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="legacy-selection-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "saved.py"
        self.source.write_text("disk\n")
        self.store = WorkspacePersistenceStore(self.root / "workspaces")
        self.legacy = {
            "workspaceRecovery": {
                "a": {
                    "snapshots": [
                        {
                            "document_id": "doc",
                            "filename": str(self.source),
                            "text": "one",
                            "clean_text": "baseline",
                            "history": ["before"],
                            "use_bom": True,
                            "encoding": "utf-8",
                            "unknown": {"x": 1},
                        },
                        {
                            "document_id": "doc",
                            "filename": str(self.source),
                            "text": "two",
                            "clean_text": "baseline",
                            "history": ["start"],
                            "redo": ["after"],
                            "line_endings": "CRLF",
                        },
                        {"document_id": "untitled", "text": "u1"},
                        {"document_id": "untitled", "text": "u2"},
                    ]
                }
            },
        }
        self.store.migrate_legacy(self.legacy, default_workspace_id="a")

    def test_selection_preserves_alternatives_identity_history_metadata_and_restart(
        self,
    ):
        before = self.store.load()
        chosen = self.store.select_legacy_recovery("doc", 1, workspace_id="a")
        restarted = WorkspacePersistenceStore(self.store.root).load()
        self.assertEqual(chosen.state, restarted.state)
        record = restarted.state.shared_resources["documents"]["doc"]
        self.assertEqual((record["text"], record["clean_text"]), ("two", "baseline"))
        self.assertEqual(record["undo"], ["start"])
        self.assertEqual(record["redo"], ["after"])
        migration = restarted.state.application_state["legacy_recovery"]
        self.assertEqual(
            migration["candidates"],
            before.state.application_state["legacy_recovery"]["candidates"],
        )
        self.assertEqual(
            restarted.state.application_state["legacy_config"], self.legacy
        )
        self.assertEqual(migration["selections"]["doc"]["candidate_index"], 1)
        self.assertNotIn("doc", migration["blocked_documents"])
        self.assertIn("untitled", migration["blocked_documents"])
        self.assertFalse(any(issue.identity == "doc" for issue in restarted.issues))
        self.assertTrue(any(issue.identity == "untitled" for issue in restarted.issues))
        registry = DocumentResourceRegistry()
        registry.restore_persistence_snapshot(restarted.state.shared_resources)
        document = ApplicationIdentity(IdentityKind.DOCUMENT, "doc")
        view = registry.retained_views_for_document(document)[0]
        registry.reopen_view(
            document, view_id=view.view_id, workspace_id=view.workspace_id
        )
        self.assertTrue(registry.undo(view.view_id))
        self.assertEqual(registry.resource(document).text, "start")
        self.assertTrue(registry.redo(view.view_id))
        self.assertEqual(registry.resource(document).text, "two")
        self.assertEqual(self.source.read_text(), "disk\n")

    def test_untitled_selection_is_retained_without_views(self):
        chosen = self.store.select_legacy_recovery("untitled", 0, workspace_id="a")
        record = chosen.state.shared_resources["documents"]["untitled"]
        self.assertIsNone(record["path"])
        self.assertEqual(record["text"], "u1")
        self.assertIsNone(record["clean_text"])
        self.assertEqual(chosen.state.shared_resources["views"], {})

    def test_invalid_inputs_and_failed_publication_leave_generation_unchanged(self):
        before = self.store.load()
        for document, index, owner in (
            ("missing", 0, "a"),
            ("doc", -1, "a"),
            ("doc", 2, "a"),
            ("doc", True, "a"),
            ("doc", "0", "a"),
            ("doc", 0, "missing"),
        ):
            with self.subTest(document=document, index=index, owner=owner):
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    self.store.select_legacy_recovery(
                        document, index, workspace_id=owner
                    )
                self.assertEqual(self.store.load(), before)
        with patch.object(
            self.store, "commit", side_effect=OSError("injected publication")
        ):
            with self.assertRaisesRegex(OSError, "publication"):
                self.store.select_legacy_recovery("doc", 0, workspace_id="a")
        self.assertEqual(self.store.load(), before)
        self.assertEqual(self.source.read_text(), "disk\n")

    def test_existing_document_and_path_collision_cannot_be_overwritten(self):
        before = self.store.load()
        registry = DocumentResourceRegistry()
        registry.create_document("healthy", path=str(self.source))
        resources = dict(registry.persistence_snapshot())
        self.store.commit(
            type(before.state)(
                before.state.loaded_workspace_ids,
                before.state.active_workspace_id,
                before.state.workspaces,
                resources,
                before.state.recovery,
                before.state.application_state,
            )
        )
        colliding = self.store.load()
        with self.assertRaises(ValueError):
            self.store.select_legacy_recovery("doc", 0, workspace_id="a")
        self.assertEqual(self.store.load(), colliding)
        registry = DocumentResourceRegistry()
        registry.create_document(
            "authoritative", identity=ApplicationIdentity(IdentityKind.DOCUMENT, "doc")
        )
        self.store.commit(
            type(before.state)(
                before.state.loaded_workspace_ids,
                before.state.active_workspace_id,
                before.state.workspaces,
                registry.persistence_snapshot(),
                before.state.recovery,
                before.state.application_state,
            )
        )
        existing = self.store.load()
        with self.assertRaises(ValueError):
            self.store.select_legacy_recovery("doc", 0, workspace_id="a")
        self.assertEqual(self.store.load(), existing)

    def test_live_adoption_keeps_existing_notifications_and_rejects_duplicate(self):
        chosen = self.store.select_legacy_recovery("doc", 0, workspace_id="a")
        registry = DocumentResourceRegistry()
        healthy = registry.create_document("healthy")
        notifications = []
        view = registry.open_view(
            healthy,
            ApplicationIdentity(IdentityKind.WORKSPACE, "a"),
            notify=lambda *args: notifications.append(args),
        )
        registry.adopt_retained_document(chosen.state.shared_resources, "doc")
        registry.replace_text(view, "changed")
        self.assertEqual(len(notifications), 1)
        self.assertEqual(registry.resource(healthy).text, "changed")
        original = deepcopy(dict(registry.persistence_snapshot()))
        with self.assertRaises(ValueError):
            registry.adopt_retained_document(chosen.state.shared_resources, "doc")
        self.assertEqual(registry.persistence_snapshot(), original)

    def test_malformed_only_and_invalid_history_remain_preserved_and_blocked(self):
        before = self.store.load()
        application = deepcopy(dict(before.state.application_state))
        migration = application["legacy_recovery"]
        migration["blocked_documents"].append("malformed-only")
        migration["candidates"]["doc"][0]["redo"] = [123]
        self.store.commit(
            type(before.state)(
                before.state.loaded_workspace_ids,
                before.state.active_workspace_id,
                before.state.workspaces,
                before.state.shared_resources,
                before.state.recovery,
                application,
            )
        )
        before = self.store.load()
        for document in ("malformed-only", "doc"):
            with self.assertRaises((ValueError, TypeError)):
                self.store.select_legacy_recovery(document, 0, workspace_id="a")
            self.assertEqual(self.store.load(), before)
