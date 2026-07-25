from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from spikes.peer_frames.workspace_lifecycle import (
    WorkspaceLifecycleCancelled,
    WorkspaceLifecycleCoordinator,
)
from spikes.peer_frames.workspace_persistence import (
    RESOURCE_SCHEMA_VERSION,
    WorkspacePersistenceError,
    WorkspacePersistenceState,
    WorkspacePersistenceStore,
)


class Runtime:
    def __init__(self, identity: str):
        self.identity = identity
        self.attached = True
        self.topology = {"frames": [f"{identity}-frame"]}
        self.dirty = [f"dirty-{identity}"]


class WorkspaceLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.user_file = Path(self.temporary.name) / "shared.py"
        self.user_file.write_text("user-owned\n", encoding="utf-8")
        self.store = WorkspacePersistenceStore(
            Path(self.temporary.name) / "workspaces"
        )
        resources = {
            "schema": RESOURCE_SCHEMA_VERSION,
            "documents": {
                "shared": {"path": str(self.user_file)},
                "a-document": {"path": str(Path(self.temporary.name) / "a.py")},
            },
            "views": {
                "a-view": {"workspace_id": "a", "document_id": "shared"},
                "b-view": {"workspace_id": "b", "document_id": "shared"},
                "a-only": {"workspace_id": "a", "document_id": "a-document"},
            },
        }
        initial = WorkspacePersistenceState(
            ("a", "b"),
            "a",
            {
                "a": {"schema": 1, "identity": "a", "name": "A"},
                "b": {"schema": 1, "identity": "b", "name": "B"},
            },
            resources,
            {},
            {},
        )
        loaded = self.store.commit(initial)
        self.runtimes = {"a": Runtime("a"), "b": Runtime("b")}
        self.events = []
        self.external_writes = []

        def capture_workspace(identity, runtime):
            self.events.append(("capture", identity))
            return {
                "schema": 1,
                "identity": identity,
                "name": identity.upper(),
                "session": deepcopy(runtime.topology),
            }

        def capture_recovery(identity, runtime):
            self.events.append(("recovery", identity))
            return {
                "schema": 1,
                "workspace_id": identity,
                "snapshots": [
                    {
                        "document_id": f"{identity}-document",
                        "text": runtime.dirty[0],
                    }
                ],
            }

        def detach(identity, runtime, shared):
            self.events.append(("detach", identity, shared))
            token = deepcopy(runtime.topology)
            runtime.attached = False
            runtime.topology = {}
            return token

        def restore_detached(identity, runtime, token):
            self.events.append(("rollback", identity))
            runtime.topology = token
            runtime.attached = True

        def construct(identity, record, recovery):
            self.events.append(("construct", identity))
            runtime = Runtime(identity)
            runtime.topology = deepcopy(record["session"])
            runtime.dirty = [
                recovery["snapshots"][0]["text"]
            ] if recovery.get("snapshots") else []
            return runtime

        def dispose(identity, runtime):
            self.events.append(("dispose", identity))
            runtime.attached = False

        self.lifecycle = WorkspaceLifecycleCoordinator(
            self.store,
            loaded,
            self.runtimes,
            capture_workspace=capture_workspace,
            capture_recovery=capture_recovery,
            detach_workspace=detach,
            restore_detached=restore_detached,
            construct_workspace=construct,
            dispose_constructed=dispose,
            capture_token=lambda _identity, runtime: (
                deepcopy(runtime.topology),
                tuple(runtime.dirty),
            ),
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_unload_freezes_recovery_keeps_catalog_and_shared_document(self):
        user_bytes = self.user_file.read_bytes()
        user_mtime = self.user_file.stat().st_mtime_ns
        result = self.lifecycle.unload("a")

        self.assertTrue(result.applied, result.detail)
        self.assertEqual(self.lifecycle.loaded_workspace_ids, ("b",))
        self.assertNotIn("a", self.lifecycle.runtimes)
        self.assertIn("a", self.lifecycle.state.workspaces)
        self.assertEqual(
            self.lifecycle.state.recovery["a"]["snapshots"][0]["text"],
            "dirty-a",
        )
        self.assertEqual(self.user_file.read_bytes(), user_bytes)
        self.assertEqual(self.user_file.stat().st_mtime_ns, user_mtime)
        self.assertIn(("detach", "a", frozenset({"shared"})), self.events)
        self.assertEqual(self.external_writes, [])

        self.runtimes["b"].dirty[0] = "later-b"
        self.assertEqual(
            self.lifecycle.state.recovery["a"]["snapshots"][0]["text"],
            "dirty-a",
        )

    def test_cancelled_capture_leaves_live_topology_and_generation_exact(self):
        generation = self.store.load().generation
        topology = deepcopy(self.runtimes["a"].topology)
        self.lifecycle._capture_recovery = lambda _identity, _runtime: (
            _ for _ in ()
        ).throw(WorkspaceLifecycleCancelled("cancelled"))

        result = self.lifecycle.unload("a")

        self.assertFalse(result.applied)
        self.assertEqual(self.store.load().generation, generation)
        self.assertEqual(self.runtimes["a"].topology, topology)
        self.assertTrue(self.runtimes["a"].attached)
        self.assertNotIn(("detach", "a", frozenset({"shared"})), self.events)

    def test_state_change_during_capture_rejects_stale_snapshot_before_detach(self):
        generation = self.store.load().generation
        original_capture = self.lifecycle._capture_recovery

        def mutate_during_capture(identity, runtime):
            captured = original_capture(identity, runtime)
            runtime.dirty[0] = "changed-during-capture"
            return captured

        self.lifecycle._capture_recovery = mutate_during_capture

        result = self.lifecycle.unload("a")

        self.assertFalse(result.applied)
        self.assertIn("changed while persistence was captured", result.detail)
        self.assertEqual(self.store.load().generation, generation)
        self.assertTrue(self.runtimes["a"].attached)
        self.assertNotIn(("detach", "a", frozenset({"shared"})), self.events)

    def test_failed_durable_commit_rolls_back_detached_topology(self):
        generation = self.store.load().generation
        topology = deepcopy(self.runtimes["a"].topology)
        original_commit = self.store.commit
        self.store.commit = lambda _state: (_ for _ in ()).throw(
            WorkspacePersistenceError("disk full")
        )
        try:
            result = self.lifecycle.unload("a")
        finally:
            self.store.commit = original_commit

        self.assertFalse(result.applied)
        self.assertEqual(self.store.load().generation, generation)
        self.assertEqual(self.lifecycle.loaded_workspace_ids, ("a", "b"))
        self.assertEqual(self.runtimes["a"].topology, topology)
        self.assertTrue(self.runtimes["a"].attached)
        self.assertIn(("rollback", "a"), self.events)

    def test_unload_then_reload_restores_identity_topology_and_recovery(self):
        user_bytes = self.user_file.read_bytes()
        user_mtime = self.user_file.stat().st_mtime_ns
        before = deepcopy(self.runtimes["a"].topology)
        self.assertTrue(self.lifecycle.unload("a").applied)

        result = self.lifecycle.reload("a")

        self.assertTrue(result.applied, result.detail)
        self.assertEqual(self.lifecycle.loaded_workspace_ids, ("b", "a"))
        self.assertEqual(self.lifecycle.runtimes["a"].identity, "a")
        self.assertEqual(self.lifecycle.runtimes["a"].topology, before)
        self.assertEqual(self.lifecycle.runtimes["a"].dirty, ["dirty-a"])
        self.assertEqual(self.external_writes, [])
        self.assertEqual(self.user_file.read_bytes(), user_bytes)
        self.assertEqual(self.user_file.stat().st_mtime_ns, user_mtime)

    def test_reload_commit_failure_disposes_constructed_runtime(self):
        self.assertTrue(self.lifecycle.unload("a").applied)
        before = self.store.load().generation
        original_commit = self.store.commit
        self.store.commit = lambda _state: (_ for _ in ()).throw(
            WorkspacePersistenceError("full")
        )
        try:
            result = self.lifecycle.reload("a")
        finally:
            self.store.commit = original_commit

        self.assertFalse(result.applied)
        self.assertNotIn("a", self.lifecycle.runtimes)
        self.assertEqual(self.store.load().generation, before)
        self.assertIn(("dispose", "a"), self.events)

    def test_quit_style_multi_unload_is_one_transaction_and_rolls_back_all(self):
        before = {
            identity: deepcopy(runtime.topology)
            for identity, runtime in self.runtimes.items()
        }
        original_commit = self.store.commit
        self.store.commit = lambda _state: (_ for _ in ()).throw(
            WorkspacePersistenceError("injected")
        )
        try:
            result = self.lifecycle.unload_many(("a", "b"))
        finally:
            self.store.commit = original_commit

        self.assertFalse(result.applied)
        self.assertEqual(set(self.lifecycle.runtimes), {"a", "b"})
        self.assertEqual(
            {identity: runtime.topology for identity, runtime in self.runtimes.items()},
            before,
        )
        self.assertTrue(all(runtime.attached for runtime in self.runtimes.values()))

    def test_final_view_close_is_not_implemented_as_workspace_unload(self):
        before = self.lifecycle.loaded_workspace_ids
        # Final-view Save/Discard/Cancel remains owned by DocumentViewRegistry;
        # this coordinator has no view-close entry point.
        self.assertFalse(hasattr(self.lifecycle, "close_view"))
        self.assertEqual(self.lifecycle.loaded_workspace_ids, before)


if __name__ == "__main__":
    unittest.main()
