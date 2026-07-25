from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

from spikes.peer_frames.workspace_recovery import (
    ExternalVersion,
    WorkspaceRecoveryRegistry,
)


def external(
    text: str | None,
    *,
    exists: bool = True,
    signature: str = "signature",
    modified: int = 20,
) -> ExternalVersion:
    return ExternalVersion(
        exists,
        text,
        signature,
        modified,
        30,
        (("save", "ordinary"),),
    )


class WorkspaceRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.registry = WorkspaceRecoveryRegistry()

    def capture(self, workspace_id="a", text="retained", observed=None):
        return self.registry.capture(
            workspace_id=workspace_id,
            document_id="document",
            path="/project/shared.py",
            text=text,
            observed_external=observed or external("baseline", signature="old", modified=10),
            captured_at_ns=15,
            metadata={"origin": workspace_id},
        )

    def test_workspace_snapshot_is_immutable_after_peer_edits_and_saves(self):
        frozen = self.capture("a", "a-retained")
        before = frozen.digest
        live_text = "edited through b"
        saved_text = live_text

        self.assertEqual(self.registry.snapshot("a", "document"), frozen)
        self.assertEqual(self.registry.snapshot("a", "document").digest, before)
        self.assertNotEqual(self.registry.snapshot("a", "document").text, saved_text)

    def test_same_document_can_have_independent_workspace_snapshots(self):
        a = self.capture("a", "a-retained")
        b = self.capture("b", "b-retained")

        self.assertEqual(a.document_id, b.document_id)
        self.assertNotEqual(a.snapshot_id, b.snapshot_id)
        self.assertEqual(
            {item.text for item in self.registry.snapshots_for_workspace("a")},
            {"a-retained"},
        )
        self.assertEqual(self.registry.snapshot("b", "document").text, "b-retained")

    def test_content_equality_restores_clean_despite_changed_signature_and_timestamp(self):
        self.capture(text="same")

        decision = self.registry.restore(
            "a", "document", external("same", signature="new", modified=999)
        )

        self.assertFalse(decision.dirty)
        self.assertIsNone(decision.conflict)
        self.assertEqual(decision.text, "same")

    def test_divergence_keeps_two_lineages_under_one_identity_with_metadata(self):
        snapshot = self.capture(text="retained")

        decision = self.registry.restore(
            "a", "document", external("external", signature="new", modified=25)
        )

        conflict = decision.conflict
        self.assertTrue(decision.dirty)
        self.assertEqual(conflict.document_id, snapshot.document_id)
        self.assertEqual(conflict.retained.text, "retained")
        self.assertEqual(conflict.external.text, "external")
        self.assertEqual(conflict.retained.timestamp_ns, 15)
        self.assertEqual(conflict.external.timestamp_ns, 25)
        self.assertIn(("origin", "a"), conflict.retained.metadata)
        self.assertIn(("save", "ordinary"), conflict.external.metadata)

    def test_missing_named_file_conflicts_but_pathless_recovery_does_not(self):
        self.capture(text="retained")
        missing = self.registry.restore(
            "a", "document", external(None, exists=False, signature="missing")
        )
        pathless = self.registry.capture(
            workspace_id="b",
            document_id="untitled",
            path=None,
            text="draft",
            observed_external=None,
        )
        draft = self.registry.restore("b", "untitled", None)

        self.assertIsNotNone(missing.conflict)
        self.assertEqual(missing.conflict.external.signature, "missing")
        self.assertEqual(draft.text, pathless.text)
        self.assertTrue(draft.dirty)
        self.assertIsNone(draft.conflict)

    def test_resolution_propagates_only_to_loaded_equivalent_conflicts(self):
        for owner, retained in (
            ("a", "same-retained"),
            ("b", "same-retained"),
            ("c", "same-retained"),
            ("different", "other-retained"),
        ):
            self.capture(owner, retained)
            self.registry.restore(owner, "document", external("external"))
        frozen_a = self.registry.snapshot("a", "document")
        frozen_b = self.registry.snapshot("b", "document")

        resolved = self.registry.resolve_loaded(
            "a",
            "document",
            resolved_text="merged",
            loaded_workspace_ids=("a", "b", "different"),
        )

        self.assertEqual(set(resolved), {"a", "b"})
        self.assertIsNone(self.registry.conflict("a", "document"))
        self.assertIsNone(self.registry.conflict("b", "document"))
        self.assertIs(self.registry.snapshot("a", "document"), frozen_a)
        self.assertIs(self.registry.snapshot("b", "document"), frozen_b)
        self.assertEqual(frozen_a.text, "same-retained")
        self.assertIsNotNone(self.registry.conflict("c", "document"))
        self.assertIsNotNone(self.registry.conflict("different", "document"))
        self.assertEqual(self.registry.snapshot("c", "document").text, "same-retained")

    def test_unloaded_workspace_reassesses_current_external_version_on_reload(self):
        self.capture("a", "same-retained")
        self.capture("unloaded", "same-retained")
        self.registry.restore("a", "document", external("old-external"))
        self.registry.restore("unloaded", "document", external("old-external"))
        self.registry.resolve_loaded(
            "a",
            "document",
            resolved_text="resolved",
            loaded_workspace_ids=("a",),
        )

        reassessed = self.registry.restore(
            "unloaded", "document", external("same-retained", signature="later")
        )

        self.assertIsNone(reassessed.conflict)
        self.assertFalse(reassessed.dirty)
        self.assertEqual(self.registry.snapshot("unloaded", "document").text, "same-retained")

    def test_snapshot_serialization_round_trip_is_exact(self):
        expected = self.capture("a", "retained")

        restored = self.registry.deserialize_snapshot(
            self.registry.serialize_snapshot(expected)
        )

        self.assertEqual(restored, expected)
        self.assertEqual(restored.digest, expected.digest)

    def test_restore_conflict_and_resolution_never_write_the_external_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "user.py"
            path.write_text("external", encoding="utf-8")
            before = path.read_bytes()
            before_mtime = path.stat().st_mtime_ns
            self.registry.capture(
                workspace_id="a",
                document_id="document",
                path=str(path),
                text="retained",
                observed_external=external("baseline"),
            )

            decision = self.registry.restore(
                "a", "document", external("external")
            )
            resolved = self.registry.resolve_loaded(
                "a",
                "document",
                resolved_text="merged",
                loaded_workspace_ids=("a",),
            )

            self.assertIsNotNone(decision.conflict)
            self.assertEqual(resolved, ("a",))
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(path.stat().st_mtime_ns, before_mtime)


if __name__ == "__main__":
    unittest.main()
