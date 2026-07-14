from __future__ import annotations

import unittest

from spikes.peer_frames.contract import (
    BackendEvent,
    BackendEventKind,
    Capability,
    CloseDecision,
    CloseReason,
    CloseVote,
    Direction,
    OperationStatus,
    PaneDescriptor,
    PaneKind,
    WorkspaceModel,
)
from spikes.peer_frames.fake_backend import FakeBackend


class RecordingClosePolicy:
    def __init__(self, decision: CloseDecision, detail: str = ""):
        self.decision = decision
        self.detail = detail
        self.closed: list[tuple[str, CloseReason]] = []

    def prepare_close(self, pane: PaneDescriptor, reason: CloseReason) -> CloseVote:
        return CloseVote(pane.id, self.decision, self.detail)

    def did_close(self, pane: PaneDescriptor, reason: CloseReason) -> None:
        self.closed.append((pane.id, reason))


class PeerFrameContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = FakeBackend()
        self.model = WorkspaceModel(self.backend)

    def register(
        self,
        pane_id: str,
        kind: PaneKind = PaneKind.CUSTOM,
        policy: RecordingClosePolicy | None = None,
    ) -> None:
        result = self.model.register_pane(
            PaneDescriptor(pane_id, kind, pane_id.title()), policy
        )
        self.assertTrue(result.applied)

    def test_any_pane_kind_can_be_first_in_a_peer_frame(self) -> None:
        for index, kind in enumerate(PaneKind, 1):
            pane_id = f"pane-{index}"
            self.register(pane_id, kind)
            self.assertTrue(self.model.create_frame(pane_id, f"frame-{index}").applied)

        frames = self.backend.current["frames"]
        self.assertEqual(len(frames), len(PaneKind))
        self.assertNotIn("main", repr(self.backend.current).lower())

    def test_tabs_local_splits_outer_splits_and_cross_frame_moves(self) -> None:
        for pane_id in ("one", "two", "three", "four"):
            self.register(pane_id)
        self.model.create_frame("one", "alpha")
        self.model.create_frame("two", "beta")
        self.model.create_frame("three", "gamma")
        self.model.create_frame("four", "delta")

        self.assertTrue(self.model.tab("two", "one").applied)
        self.assertTrue(self.model.split("three", "one", Direction.RIGHT).applied)
        self.assertTrue(
            self.model.split("four", "three", Direction.BELOW, outer=True).applied
        )

        self.assertEqual(list(self.model.frames), ["alpha"])
        layout = self.model.serialize_layout()
        root = layout["frames"][0]["root"]
        self.assertEqual(root["orientation"], "vertical")
        self.assertEqual(len(root["children"]), 2)
        self.assertEqual(set(self.model.panes), {"one", "two", "three", "four"})

    def test_floating_and_retabbing_preserve_pane_identity(self) -> None:
        for pane_id in ("editor", "shell"):
            self.register(pane_id)
        self.model.create_frame("editor", "workspace-a")
        self.model.create_frame("shell", "workspace-b")

        self.assertTrue(self.model.tab("shell", "editor").applied)
        self.assertNotIn("workspace-b", self.model.frames)
        self.assertTrue(self.model.float("shell", "workspace-c").applied)
        self.assertIn("workspace-c", self.model.frames)
        self.assertEqual(self.model.panes["shell"].id, "shell")

    def test_backend_events_have_application_level_results(self) -> None:
        self.register("one")
        self.register("two")
        self.model.create_frame("one", "a")
        self.model.create_frame("two", "b")

        result = self.model.handle_backend_event(
            BackendEvent(BackendEventKind.TAB, pane_id="two", target_pane_id="one")
        )
        self.assertTrue(result.applied)
        self.assertEqual(self.model.active_pane_id, "two")

        snapshots = len(self.backend.snapshots)
        result = self.model.handle_backend_event(
            BackendEvent(BackendEventKind.DESTROYED, pane_id="two")
        )
        self.assertEqual(result.status, OperationStatus.INVALID)
        self.assertIn("two", self.model.panes)
        self.assertEqual(len(self.backend.snapshots), snapshots + 1)

    def test_frame_close_is_transactional_when_one_pane_refuses(self) -> None:
        allowed = RecordingClosePolicy(CloseDecision.ALLOW)
        refused = RecordingClosePolicy(CloseDecision.REFUSE, "still running")
        self.register("allowed", policy=allowed)
        self.register("refused", policy=refused)
        self.model.create_frame("allowed", "workspace")
        self.model.create_frame("refused", "temporary")
        self.model.tab("refused", "allowed")
        before = self.model.serialize_layout()

        result = self.model.request_close_frame("workspace")

        self.assertEqual(result.status, OperationStatus.REFUSED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(allowed.closed, [])
        self.assertEqual(refused.closed, [])

    def test_confirmation_can_cancel_without_partial_close(self) -> None:
        confirm = RecordingClosePolicy(CloseDecision.CONFIRM, "unsaved")
        allowed = RecordingClosePolicy(CloseDecision.ALLOW)
        self.register("dirty", policy=confirm)
        self.register("clean", policy=allowed)
        self.model.create_frame("dirty", "workspace")
        self.model.create_frame("clean", "temporary")
        self.model.tab("clean", "dirty")
        before = self.model.serialize_layout()

        result = self.model.request_close_frame("workspace")
        self.assertEqual(result.status, OperationStatus.CONFIRMATION_REQUIRED)
        self.assertEqual(self.model.serialize_layout(), before)

        result = self.model.request_close_frame("workspace", lambda votes: False)
        self.assertEqual(result.status, OperationStatus.CANCELLED)
        self.assertEqual(self.model.serialize_layout(), before)

        result = self.model.request_close_frame("workspace", lambda votes: True)
        self.assertTrue(result.applied)
        self.assertEqual(self.model.frames, {})
        self.assertEqual(confirm.closed, [("dirty", CloseReason.FRAME)])
        self.assertEqual(allowed.closed, [("clean", CloseReason.FRAME)])

    def test_frame_close_and_application_shutdown_are_separate(self) -> None:
        self.register("first")
        self.register("second")
        self.model.create_frame("first", "created-first")
        self.model.create_frame("second", "created-second")

        self.assertTrue(self.model.request_close_frame("created-first").applied)
        self.assertFalse(self.model.shutdown_requested)
        self.assertIn("created-second", self.model.frames)

        self.assertTrue(self.model.request_shutdown().applied)
        self.assertTrue(self.model.shutdown_requested)

    def test_layout_round_trip_does_not_encode_a_privileged_frame(self) -> None:
        for pane_id in ("one", "two", "three"):
            self.register(pane_id)
        self.model.create_frame("one", "red")
        self.model.create_frame("two", "blue")
        self.model.create_frame("three", "green")
        self.model.split("three", "one", Direction.RIGHT)
        saved = self.model.serialize_layout()

        restored_backend = FakeBackend()
        restored = WorkspaceModel(restored_backend)
        for pane_id in ("one", "two", "three"):
            restored.register_pane(PaneDescriptor(pane_id, PaneKind.CUSTOM, pane_id))
        self.assertTrue(restored.restore_layout(saved).applied)
        self.assertEqual(restored.serialize_layout(), saved)

    def test_missing_capability_is_reported_without_mutation(self) -> None:
        backend = FakeBackend(frozenset({Capability.CREATE_FRAME}))
        model = WorkspaceModel(backend)
        model.register_pane(PaneDescriptor("one", PaneKind.EDITOR, "One"))
        model.register_pane(PaneDescriptor("two", PaneKind.EDITOR, "Two"))
        model.create_frame("one", "a")
        model.create_frame("two", "b")
        before = model.serialize_layout()

        result = model.tab("two", "one")

        self.assertEqual(result.status, OperationStatus.UNSUPPORTED)
        self.assertEqual(model.serialize_layout(), before)

    def test_invalid_restore_is_rejected_without_mutation(self) -> None:
        self.register("one")
        self.model.create_frame("one", "stable")
        before = self.model.serialize_layout()
        malformed = {
            "schema": 1,
            "active_pane_id": "one",
            "frames": [before["frames"][0], before["frames"][0]],
        }

        result = self.model.restore_layout(malformed)

        self.assertEqual(result.status, OperationStatus.INVALID)
        self.assertEqual(self.model.serialize_layout(), before)

    def test_backend_can_atomically_adopt_placement_without_publishing(self) -> None:
        self.register("one")
        self.register("two")
        self.model.create_frame("one", "one")
        self.model.create_frame("two", "two")
        proposed = self.model.serialize_layout()
        proposed["frames"].reverse()
        publications = len(self.backend.snapshots)

        result = self.model.adopt_backend_layout(proposed)

        self.assertTrue(result.applied)
        self.assertEqual(self.model.serialize_layout(), proposed)
        self.assertEqual(len(self.backend.snapshots), publications)

    def test_backend_adoption_cannot_create_or_remove_panes(self) -> None:
        self.register("one")
        self.register("two")
        self.model.create_frame("one", "one")
        self.model.create_frame("two", "two")
        before = self.model.serialize_layout()
        missing = self.model.serialize_layout()
        missing["frames"].pop()

        result = self.model.adopt_backend_layout(missing)

        self.assertEqual(result.status, OperationStatus.INVALID)
        self.assertEqual(self.model.serialize_layout(), before)


if __name__ == "__main__":
    unittest.main()
