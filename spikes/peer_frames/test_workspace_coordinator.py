from __future__ import annotations

import unittest
from copy import deepcopy

from spikes.peer_frames.commands import CommandDescriptor, CommandRegistry
from spikes.peer_frames.contract import (
    ActiveContext,
    CloseDecision,
    CloseRequest,
    CloseVote,
    OperationResult,
    OperationStatus,
    PaneDescriptor,
    PaneKind,
    WorkspaceModel,
)
from spikes.peer_frames.fake_backend import FakeBackend
from spikes.peer_frames.identity import (
    IDENTITY_LIFETIMES,
    ApplicationIdentity,
    IdentityKind,
    IdentityLifetime,
    new_identity,
)
from spikes.peer_frames.workspace_coordinator import WorkspaceCoordinator


class RecordingPolicy:
    def __init__(self) -> None:
        self.closed: list[str] = []

    def prepare_close(self, pane, request: CloseRequest) -> CloseVote:
        return CloseVote(pane.id, CloseDecision.ALLOW)

    def validate_close(self, pane, request: CloseRequest) -> CloseVote:
        return CloseVote(pane.id, CloseDecision.ALLOW)

    def did_close(self, pane, request: CloseRequest) -> None:
        self.closed.append(pane.id)


class FailingBackend(FakeBackend):
    def __init__(self) -> None:
        super().__init__()
        self.fail_next_render = False

    def render(self, snapshot) -> None:
        if self.fail_next_render:
            self.fail_next_render = False
            raise RuntimeError("render failed")
        super().render(snapshot)


class WorkspaceCoordinatorStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.coordinator = WorkspaceCoordinator()
        self.a_model = WorkspaceModel(FakeBackend())
        self.b_model = WorkspaceModel(FakeBackend())
        self.a_id = self.coordinator.add_workspace(
            self.a_model,
            name="A",
            state={"nested": {"value": 1}},
        )
        self.b_id = self.coordinator.add_workspace(self.b_model, name="B")

    def add_pane(
        self,
        workspace_id,
        pane_id: str,
        policy=None,
        *,
        place: bool = True,
    ) -> PaneDescriptor:
        pane = PaneDescriptor(pane_id, PaneKind.EDITOR, pane_id.title())
        result = self.coordinator.register_pane(workspace_id, pane, policy)
        self.assertTrue(result.applied)
        if place:
            model = self.coordinator.model(workspace_id)
            self.assertTrue(model.create_frame(pane_id, f"{pane_id}-frame").applied)
        return pane

    def test_identity_kinds_have_explicit_lifetimes(self) -> None:
        self.assertEqual(set(IDENTITY_LIFETIMES), set(IdentityKind))
        for kind in (
            IdentityKind.WORKSPACE,
            IdentityKind.DOCUMENT,
            IdentityKind.VIEW,
            IdentityKind.RECOVERY_SNAPSHOT,
        ):
            self.assertEqual(IDENTITY_LIFETIMES[kind], IdentityLifetime.DURABLE)
        self.assertEqual(
            IDENTITY_LIFETIMES[IdentityKind.SHELL], IdentityLifetime.LIVE_SESSION
        )
        self.assertEqual(
            IDENTITY_LIFETIMES[IdentityKind.KERNEL_GENERATION],
            IdentityLifetime.GENERATION,
        )
        self.assertEqual(
            IDENTITY_LIFETIMES[IdentityKind.DEBUG_SESSION],
            IdentityLifetime.LIVE_SESSION,
        )
        with self.assertRaisesRegex(ValueError, "non-empty"):
            ApplicationIdentity(IdentityKind.DOCUMENT, "")

    def test_no_workspace_and_empty_workspace_contexts_are_distinct(self) -> None:
        empty = WorkspaceCoordinator()
        self.assertEqual(empty.resolve_active_context(), ActiveContext())

        context = self.coordinator.resolve_active_context()
        self.assertEqual(context.workspace_id, self.a_id)
        self.assertIsNone(context.pane)
        self.assertTrue(self.coordinator.context_is_current(context))

    def test_multiple_roots_have_one_owner_per_pane(self) -> None:
        self.add_pane(self.a_id, "a-pane")
        self.add_pane(self.b_id, "b-pane")

        self.assertTrue(self.coordinator.assert_invariants())
        self.assertEqual(self.coordinator.pane_owner("a-pane"), self.a_id)
        self.assertEqual(self.coordinator.pane_owner("b-pane"), self.b_id)
        self.assertIn("a-pane", self.a_model.panes)
        self.assertNotIn("a-pane", self.b_model.panes)
        self.assertNotEqual(
            self.a_model.serialize_layout(), self.b_model.serialize_layout()
        )

    def test_command_invocation_keeps_captured_context_after_focus_changes(self) -> None:
        self.add_pane(self.a_id, "a-pane")
        self.add_pane(self.b_id, "b-pane")
        self.coordinator.activate_pane(self.a_id, "a-pane")
        seen: list[ActiveContext] = []

        def invoke(context: ActiveContext):
            seen.append(context)
            self.coordinator.activate_pane(self.b_id, "b-pane")
            return context

        commands = CommandRegistry(self.coordinator.resolve_active_context)
        commands.register(CommandDescriptor("capture", "Capture", invoke))

        invocation = commands.invoke("capture")

        self.assertEqual(invocation.value.workspace_id, self.a_id)
        self.assertEqual(invocation.value.pane.id, "a-pane")
        self.assertEqual(seen, [invocation.value])
        self.assertEqual(
            self.coordinator.resolve_active_context().workspace_id, self.b_id
        )
        self.assertTrue(self.coordinator.context_is_current(invocation.value))

    def test_missing_or_mismatched_explicit_context_never_falls_back(self) -> None:
        self.add_pane(self.a_id, "a-pane")
        self.coordinator.activate_pane(self.a_id, "a-pane")
        unknown = new_identity(IdentityKind.WORKSPACE)

        self.assertIsNone(
            self.coordinator.resolve_workspace_context(unknown, "a-pane")
        )
        self.assertIsNone(
            self.coordinator.resolve_workspace_context(self.b_id, "a-pane")
        )
        self.assertEqual(
            self.coordinator.resolve_active_context().workspace_id, self.a_id
        )

    def test_captured_context_becomes_stale_after_transfer_and_repeated_move(self) -> None:
        self.add_pane(self.a_id, "pane")
        self.coordinator.activate_pane(self.a_id, "pane")
        original = self.coordinator.resolve_active_context()

        self.assertTrue(self.coordinator.transfer_pane("pane", self.b_id).applied)
        moved = self.coordinator.resolve_workspace_context(self.b_id, "pane")
        self.assertFalse(self.coordinator.context_is_current(original))
        self.assertIsNotNone(moved)
        self.assertTrue(self.coordinator.context_is_current(moved))

        self.assertTrue(self.coordinator.transfer_pane("pane", self.a_id).applied)
        self.assertFalse(self.coordinator.context_is_current(original))
        returned = self.coordinator.resolve_workspace_context(self.a_id, "pane")
        self.assertTrue(self.coordinator.context_is_current(returned))

    def test_context_becomes_stale_after_pane_close_and_workspace_removal(self) -> None:
        self.add_pane(self.a_id, "pane")
        pane_context = self.coordinator.resolve_workspace_context(self.a_id, "pane")
        self.assertTrue(self.a_model.request_close_pane("pane").applied)
        self.assertFalse(self.coordinator.context_is_current(pane_context))

        empty_context = self.coordinator.resolve_workspace_context(self.a_id)
        self.assertTrue(self.coordinator.remove_workspace(self.a_id).applied)
        self.assertFalse(self.coordinator.context_is_current(empty_context))
        self.assertIsNone(self.coordinator.active_workspace_id)
        self.assertEqual(self.coordinator.resolve_active_context(), ActiveContext())

    def test_duplicate_pane_registration_is_rejected_without_mutation(self) -> None:
        self.add_pane(self.a_id, "pane", place=False)
        before_a = dict(self.a_model.panes)
        before_b = dict(self.b_model.panes)

        result = self.coordinator.register_pane(
            self.b_id, PaneDescriptor("pane", PaneKind.EDITOR, "Duplicate")
        )

        self.assertEqual(result.status, OperationStatus.INVALID)
        self.assertEqual(self.a_model.panes, before_a)
        self.assertEqual(self.b_model.panes, before_b)
        self.assertEqual(self.coordinator.pane_owner("pane"), self.a_id)

        unknown = new_identity(IdentityKind.WORKSPACE)
        self.assertEqual(
            self.coordinator.register_pane(
                unknown, PaneDescriptor("other", PaneKind.EDITOR, "Other")
            ).status,
            OperationStatus.INVALID,
        )
        self.assertIsNone(self.coordinator.pane_owner("other"))

    def test_direct_cross_root_duplicate_is_detected_by_invariant(self) -> None:
        pane = PaneDescriptor("pane", PaneKind.EDITOR, "Pane")
        self.assertTrue(self.a_model.register_pane(pane).applied)
        self.assertTrue(self.b_model.register_pane(pane).applied)

        with self.assertRaisesRegex(AssertionError, "belongs to both"):
            self.coordinator.assert_invariants()
        with self.assertRaisesRegex(RuntimeError, "several workspaces"):
            self.coordinator.pane_owner("pane")

    def test_transfer_preserves_descriptor_and_policy_without_closing(self) -> None:
        policy = RecordingPolicy()
        pane = self.add_pane(self.a_id, "pane", policy)

        result = self.coordinator.transfer_pane("pane", self.b_id)

        self.assertTrue(result.applied)
        self.assertNotIn("pane", self.a_model.panes)
        self.assertEqual(self.b_model.panes["pane"], pane)
        self.assertEqual(policy.closed, [])
        self.assertEqual(self.coordinator.pane_owner("pane"), self.b_id)
        self.assertIsNone(self.b_model.resolve_pane_context("pane").frame_id)

    def test_target_rejection_rolls_transfer_back_atomically(self) -> None:
        policy = RecordingPolicy()
        self.add_pane(self.a_id, "pane", policy)
        before_source = deepcopy(self.a_model.serialize_layout())
        before_target = deepcopy(self.b_model.serialize_layout())
        original_accept = self.b_model.accept_pane
        def mutate_then_reject(transfer):
            self.assertTrue(original_accept(transfer).applied)
            self.assertTrue(self.b_model.create_frame("pane", "target-frame").applied)
            return OperationResult(OperationStatus.INVALID, "injected rejection")

        self.b_model.accept_pane = mutate_then_reject
        try:
            result = self.coordinator.transfer_pane("pane", self.b_id)
        finally:
            self.b_model.accept_pane = original_accept

        self.assertEqual(result.status, OperationStatus.INVALID)
        self.assertEqual(self.a_model.serialize_layout(), before_source)
        self.assertEqual(self.b_model.serialize_layout(), before_target)
        self.assertEqual(self.coordinator.pane_owner("pane"), self.a_id)
        self.assertEqual(policy.closed, [])
        self.assertTrue(self.coordinator.assert_invariants())

    def test_source_projection_failure_rolls_transfer_back_atomically(self) -> None:
        coordinator = WorkspaceCoordinator()
        source_backend = FailingBackend()
        source = WorkspaceModel(source_backend)
        target = WorkspaceModel(FakeBackend())
        source_id = coordinator.add_workspace(source, name="Source")
        target_id = coordinator.add_workspace(target, name="Target")
        pane = PaneDescriptor("pane", PaneKind.EDITOR, "Pane")
        coordinator.register_pane(source_id, pane)
        source.create_frame("pane", "frame")
        before = deepcopy(source.serialize_layout())
        source_backend.fail_next_render = True

        result = coordinator.transfer_pane("pane", target_id)

        self.assertEqual(result.status, OperationStatus.INVALID)
        self.assertEqual(source.serialize_layout(), before)
        self.assertEqual(coordinator.pane_owner("pane"), source_id)
        self.assertNotIn("pane", target.panes)
        self.assertTrue(coordinator.assert_invariants())

    def test_stale_backend_activation_after_transfer_is_rejected(self) -> None:
        self.add_pane(self.a_id, "pane")
        self.coordinator.transfer_pane("pane", self.b_id)
        active_before = self.coordinator.active_workspace_id

        result = self.coordinator.adopt_backend_activation(self.a_id, "pane")

        self.assertEqual(result.status, OperationStatus.INVALID)
        self.assertEqual(self.coordinator.active_workspace_id, active_before)

    def test_workspace_rename_relocate_and_copy_identity_contract(self) -> None:
        original_identity = self.a_id
        renamed = self.coordinator.rename_workspace(self.a_id, "Renamed")
        relocated = self.coordinator.relocate_workspace(self.a_id, "/new/location")
        copied_model = WorkspaceModel(FakeBackend())

        copied_id = self.coordinator.copy_workspace(
            self.a_id, copied_model, name="Copied"
        )

        self.assertEqual(renamed.identity, original_identity)
        self.assertEqual(relocated.identity, original_identity)
        self.assertEqual(relocated.persistence_location, "/new/location")
        self.assertNotEqual(copied_id, original_identity)
        self.assertEqual(
            self.coordinator.state(copied_id), self.coordinator.state(self.a_id)
        )
        self.coordinator.state(copied_id)["nested"]["value"] = 2
        self.assertEqual(self.coordinator.state(self.a_id)["nested"]["value"], 1)

    def test_invalid_workspace_operations_do_not_select_a_fallback(self) -> None:
        self.add_pane(self.a_id, "pane")
        self.coordinator.activate_pane(self.a_id, "pane")
        before = self.coordinator.resolve_active_context()
        unknown = new_identity(IdentityKind.WORKSPACE)

        self.assertEqual(
            self.coordinator.activate_workspace(unknown).status,
            OperationStatus.INVALID,
        )
        self.assertEqual(
            self.coordinator.activate_pane(self.b_id, "pane").status,
            OperationStatus.INVALID,
        )
        self.assertEqual(self.coordinator.resolve_active_context(), before)


if __name__ == "__main__":
    unittest.main()
