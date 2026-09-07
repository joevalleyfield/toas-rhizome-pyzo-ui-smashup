from __future__ import annotations

import json
import os
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from spikes.peer_frames.workspace_persistence import (
    RECOVERY_SCHEMA_VERSION,
    RESOURCE_SCHEMA_VERSION,
    WORKSPACE_SCHEMA_VERSION,
    WorkspacePersistenceError,
    WorkspacePersistenceState,
    WorkspacePersistenceStore,
)


def workspace(identity: str, name: str) -> dict[str, object]:
    return {
        "schema": WORKSPACE_SCHEMA_VERSION,
        "identity": identity,
        "name": name,
        "session": {"layout": {"frames": [{"id": f"{identity}-frame"}]}},
        "profile": {"main": "document", "unknown-tool": {"future": [1, 2]}},
        "extensions": {"deprecated": True},
    }


def state() -> WorkspacePersistenceState:
    recovery = {
        identity: {
            "schema": RECOVERY_SCHEMA_VERSION,
            "workspace_id": identity,
            "snapshots": [
                {
                    "snapshot_id": f"{identity}-snapshot",
                    "document_id": "document",
                    "text": f"dirty-{identity}",
                }
            ],
        }
        for identity in ("a", "b")
    }
    return WorkspacePersistenceState(
        ("a", "b"),
        "b",
        {"a": workspace("a", "A"), "b": workspace("b", "B")},
        {
            "schema": RESOURCE_SCHEMA_VERSION,
            "documents": {"document": {"path": "/project/shared.py"}},
            "views": {
                "view-a": {"workspace_id": "a", "document_id": "document", "pinned": True},
                "view-b": {"workspace_id": "b", "document_id": "document", "pinned": False},
            },
            "mains": {"a": "document", "b": "document"},
        },
        recovery,
        {"unknown-application": {"keep": "exactly"}},
    )


class WorkspacePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "workspaces"
        self.store = WorkspacePersistenceStore(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def test_two_workspace_restart_round_trip_preserves_references_and_unknown_fields(self):
        expected = state()
        committed = self.store.commit(expected)
        restarted = WorkspacePersistenceStore(self.root).load()

        self.assertEqual(committed.state, expected)
        self.assertEqual(restarted.state, expected)
        self.assertEqual(restarted.unavailable_workspace_ids, ())
        self.assertEqual(restarted.issues, ())
        self.assertIsNot(
            restarted.state.workspaces["a"]["profile"],
            expected.workspaces["a"]["profile"],
        )

    def test_one_corrupt_workspace_is_unavailable_while_peer_remains_usable(self):
        self.store.commit(state())
        manifest = json.loads(self.store.manifest.read_text(encoding="utf-8"))
        generation = self.store.generations / manifest["generation"]
        entry = next(item for item in manifest["workspaces"] if item["id"] == "b")
        record = generation / entry["file"]
        recoverable_bytes = record.read_bytes()
        record.write_text("not json", encoding="utf-8")

        loaded = self.store.load()

        self.assertEqual(loaded.state.loaded_workspace_ids, ("a", "b"))
        self.assertEqual(set(loaded.state.workspaces), {"a"})
        self.assertEqual(loaded.unavailable_workspace_ids, ("b",))
        self.assertEqual(loaded.state.active_workspace_id, "a")
        self.assertEqual(loaded.state.workspaces["a"]["name"], "A")
        self.assertEqual([(issue.kind, issue.identity) for issue in loaded.issues], [("workspace", "b")])

        record.write_bytes(recoverable_bytes)
        retried = self.store.load()
        self.assertEqual(set(retried.state.workspaces), {"a", "b"})
        self.assertEqual(retried.unavailable_workspace_ids, ())
        self.assertEqual(retried.issues, ())

    def test_corrupt_workspace_does_not_block_healthy_workspace_commit_or_retry(self):
        self.store.commit(state())
        manifest = json.loads(self.store.manifest.read_text(encoding="utf-8"))
        generation = self.store.generations / manifest["generation"]
        entry = next(item for item in manifest["workspaces"] if item["id"] == "b")
        record = generation / entry["file"]
        recoverable_bytes = record.read_bytes()
        record.write_text("not json", encoding="utf-8")
        partial = self.store.load()
        healthy_state = partial.state.detached_copy()
        healthy_state.workspaces["a"]["name"] = "A changed"

        committed = self.store.commit(healthy_state)

        self.assertEqual(committed.state.workspaces["a"]["name"], "A changed")
        self.assertEqual(committed.unavailable_workspace_ids, ("b",))
        self.assertEqual(committed.state.loaded_workspace_ids, ("a", "b"))

        record.write_bytes(recoverable_bytes)
        retried = self.store.load()
        self.assertEqual(retried.state.workspaces["b"]["name"], "B")
        self.assertEqual(retried.unavailable_workspace_ids, ())

    def test_corrupt_recovery_isolated_from_workspace_and_other_snapshots(self):
        self.store.commit(state())
        manifest = json.loads(self.store.manifest.read_text(encoding="utf-8"))
        generation = self.store.generations / manifest["generation"]
        entry = next(item for item in manifest["workspaces"] if item["id"] == "a")
        (generation / entry["recovery"]["file"]).write_text("bad", encoding="utf-8")

        loaded = self.store.load()

        self.assertEqual(set(loaded.state.workspaces), {"a", "b"})
        self.assertNotIn("a", loaded.state.recovery)
        self.assertIn("b", loaded.state.recovery)
        self.assertEqual([(issue.kind, issue.identity) for issue in loaded.issues], [("recovery", "a")])

    def test_failure_at_every_publish_boundary_keeps_previous_manifest_authoritative(self):
        for failure_point in (
            "record-write",
            "record-fsync",
            "generation-replace",
            "manifest-write",
            "manifest-replace",
        ):
            with self.subTest(failure_point=failure_point):
                case_root = Path(self.temporary.name) / failure_point
                store = WorkspacePersistenceStore(case_root)
                original = state()
                store.commit(original)
                changed = state().detached_copy()
                changed.workspaces["a"]["name"] = "Changed"
                original_record = store._write_record
                original_fsync = store._fsync_directory
                original_write_json = store._write_json
                original_replace = os.replace

                def fail_record(*args, **kwargs):
                    raise OSError("injected record write")

                def fail_fsync(path):
                    if Path(path).name.startswith(".tmp-"):
                        raise OSError("injected record fsync")
                    return original_fsync(path)

                def fail_json(path, value):
                    if Path(path).name.startswith(".manifest-"):
                        raise OSError("injected manifest write")
                    return original_write_json(path, value)

                def fail_replace(source, destination):
                    destination = Path(destination)
                    if (
                        failure_point == "generation-replace"
                        and destination.parent == store.generations
                        and not destination.name.startswith(".tmp-")
                    ):
                        raise OSError("injected generation replace")
                    if (
                        failure_point == "manifest-replace"
                        and destination == store.manifest
                    ):
                        raise OSError("injected manifest replace")
                    return original_replace(source, destination)

                if failure_point == "record-write":
                    store._write_record = fail_record
                elif failure_point == "record-fsync":
                    store._fsync_directory = fail_fsync
                elif failure_point == "manifest-write":
                    store._write_json = fail_json
                os.replace = fail_replace
                try:
                    with self.assertRaisesRegex(WorkspacePersistenceError, "injected"):
                        store.commit(changed)
                finally:
                    os.replace = original_replace
                    store._write_record = original_record
                    store._fsync_directory = original_fsync
                    store._write_json = original_write_json

                self.assertEqual(store.load().state, original)

    def test_invalid_reference_set_is_rejected_before_any_manifest_exists(self):
        invalid = state().detached_copy()
        invalid.workspaces.pop("b")

        with self.assertRaisesRegex(ValueError, "loaded workspace"):
            self.store.commit(invalid)

        self.assertFalse(self.store.manifest.exists())

    def test_unloaded_workspace_remains_in_catalog_with_frozen_recovery(self):
        durable = state().detached_copy()
        durable = WorkspacePersistenceState(
            ("b",),
            "b",
            durable.workspaces,
            durable.shared_resources,
            durable.recovery,
            durable.application_state,
        )

        loaded = self.store.commit(durable).state

        self.assertEqual(loaded.loaded_workspace_ids, ("b",))
        self.assertEqual(set(loaded.workspaces), {"a", "b"})
        self.assertEqual(
            loaded.recovery["a"]["snapshots"][0]["text"], "dirty-a"
        )

    def test_copy_payload_can_be_persisted_without_mutable_aliases(self):
        original = state().detached_copy()
        copied = deepcopy(original.workspaces["a"])
        copied["identity"] = "copy"
        copied["name"] = "A copy"
        durable = WorkspacePersistenceState(
            ("a", "b", "copy"),
            "copy",
            {**original.workspaces, "copy": copied},
            original.shared_resources,
            {**original.recovery, "copy": {"schema": 1, "workspace_id": "copy", "snapshots": []}},
            original.application_state,
        )

        loaded = self.store.commit(durable).state
        loaded.workspaces["copy"]["profile"]["unknown-tool"]["future"].append(3)

        self.assertEqual(
            loaded.workspaces["a"]["profile"]["unknown-tool"]["future"], [1, 2]
        )

    def test_legacy_migration_is_single_workspace_lossless_backed_up_and_idempotent(self):
        legacy = {
            "state": {
                "peerWorkspaceSession": {"schema": 1, "layout": {"frames": []}},
                "views": [
                    {"name": "[NORMAL]"},
                    {"name": "Presentation", "workspaceSession": {"layout": "snapshot"}},
                ],
            },
            "tools": {"thirdparty": {"unknown": {"nested": 42}}},
            "deprecated": {"old": True},
        }
        original = deepcopy(legacy)

        first = self.store.migrate_legacy(legacy, default_workspace_id="default")
        second = self.store.migrate_legacy(legacy, default_workspace_id="different")

        self.assertTrue(first.migrated)
        self.assertFalse(second.migrated)
        self.assertEqual(first.load.state.loaded_workspace_ids, ("default",))
        self.assertEqual(second.load.state, first.load.state)
        self.assertEqual(first.load.state.application_state["legacy_config"], original)
        self.assertEqual(legacy, original)
        self.assertEqual(
            json.loads(Path(first.backup_path).read_text(encoding="utf-8")), original
        )
        self.assertEqual(
            first.load.state.application_state["legacy_config"]["state"]["views"],
            original["state"]["views"],
        )

    def test_interrupted_migration_retains_backup_and_retry_publishes_once(self):
        legacy = {
            "state": {"peerWorkspaceSession": {"schema": 1}, "views": []},
            "tools": {"unknown": {"value": 7}},
        }
        original_commit = self.store.commit
        self.store.commit = lambda _state: (_ for _ in ()).throw(
            WorkspacePersistenceError("injected migration commit")
        )
        try:
            with self.assertRaisesRegex(
                WorkspacePersistenceError, "injected migration"
            ):
                self.store.migrate_legacy(
                    legacy, default_workspace_id="default"
                )
        finally:
            self.store.commit = original_commit

        self.assertFalse(self.store.manifest.exists())
        backups = tuple(self.store.backups.glob("*.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(
            json.loads(backups[0].read_text(encoding="utf-8")), legacy
        )

        retried = self.store.migrate_legacy(
            legacy, default_workspace_id="default"
        )
        repeated = self.store.migrate_legacy(
            legacy, default_workspace_id="other"
        )
        self.assertTrue(retried.migrated)
        self.assertFalse(repeated.migrated)
        self.assertEqual(repeated.load.state.loaded_workspace_ids, ("default",))

    def test_legacy_recovery_equal_candidates_coalesce_without_losing_provenance(self):
        legacy = {
            "state": {"peerWorkspaceSession": {"schema": 1}},
            "workspaceRecovery": {
                "default": {
                    "snapshots": [
                        {
                            "snapshot_id": "old-a",
                            "workspace_id": "default",
                            "document_id": "doc",
                            "text": "same",
                            "clean_text": "base",
                            "history": ["edit"],
                        },
                        {
                            "snapshot_id": "old-b",
                            "workspace_id": "default",
                            "document_id": "doc",
                            "text": "same",
                            "clean_text": "base",
                            "history": ["edit"],
                        },
                    ]
                }
            },
        }

        result = self.store.migrate_legacy(legacy, default_workspace_id="default")

        self.assertEqual(result.load.issues, ())
        retained = result.load.state.shared_resources["retained_documents"]["doc"]
        self.assertEqual(retained["candidate"]["text"], "same")
        self.assertEqual(retained["workspace_ids"], ["default"])
        self.assertEqual(
            len(result.load.state.application_state["legacy_recovery"]["candidates"]["doc"]),
            2,
        )
        self.assertEqual(
            len(result.load.state.recovery["default"]["snapshots"]), 2
        )

    def test_legacy_recovery_divergence_and_malformed_records_are_visible(self):
        legacy = {
            "state": {"peerWorkspaceSession": {"schema": 1}},
            "workspaceRecovery": {
                "default": {
                    "snapshots": [
                        {"snapshot_id": "one", "document_id": "doc", "text": "one"},
                        {"snapshot_id": "two", "document_id": "doc", "text": "two"},
                        "malformed",
                    ]
                }
            },
        }

        result = self.store.migrate_legacy(legacy, default_workspace_id="default")

        self.assertEqual(result.load.state.shared_resources["retained_documents"], {})
        self.assertIn("doc", result.load.state.application_state["legacy_recovery"]["candidates"])
        self.assertTrue(any(issue.kind == "ambiguous-recovery" for issue in result.load.issues))


if __name__ == "__main__":
    unittest.main()
