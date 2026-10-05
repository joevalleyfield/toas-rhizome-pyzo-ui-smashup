from __future__ import annotations

import unittest

from spikes.peer_frames.execution_routing import (
    COMMAND_POLICIES,
    AssignmentMode,
    ExecutionCommand,
    ExecutionRouter,
    RoutingStatus,
)
from spikes.peer_frames.identity import (
    IDENTITY_LIFETIMES,
    IdentityKind,
    IdentityLifetime,
    new_identity,
)


class ExecutionRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = ExecutionRouter()
        self.a = new_identity(IdentityKind.WORKSPACE)
        self.b = new_identity(IdentityKind.WORKSPACE)
        self.c = new_identity(IdentityKind.WORKSPACE)
        for workspace_id in (self.a, self.b, self.c):
            self.router.register_workspace(workspace_id)
        self.view_a = self.add_view(self.a)
        self.view_b = self.add_view(self.b)
        self.shell_a1 = self.add_shell(self.a)
        self.shell_a2 = self.add_shell(self.a)
        self.shell_b = self.add_shell(self.b)

    def add_view(self, workspace_id):
        view_id = new_identity(IdentityKind.VIEW)
        self.router.register_view(view_id, workspace_id)
        return view_id

    def add_shell(self, workspace_id):
        shell_id = new_identity(IdentityKind.SHELL)
        self.router.register_shell(
            shell_id,
            workspace_id,
            new_identity(IdentityKind.KERNEL_GENERATION),
        )
        return shell_id

    def foreground(self, workspace_id, shell_id):
        self.assertTrue(
            self.router.foreground_shell(workspace_id, shell_id).applied
        )

    def resolve(self, view_id, command=ExecutionCommand.EXECUTE_SELECTION):
        return self.router.resolve(command, view_id=view_id)

    def test_operation_identity_has_an_explicit_live_session_lifetime(self):
        self.assertEqual(
            IDENTITY_LIFETIMES[IdentityKind.OPERATION],
            IdentityLifetime.LIVE_SESSION,
        )

    def test_reopened_view_uses_resource_epoch_and_rejects_old_operation(self):
        self.foreground(self.a, self.shell_a1)
        old = self.resolve(self.view_a).provenance
        self.router.close_view(self.view_a)
        self.router.register_view(self.view_a, self.a, epoch=2)
        self.assertFalse(self.router.provenance_is_current(old))
        self.assertEqual(self.resolve(self.view_a).provenance.view_epoch, 2)

    def test_implicit_routing_is_workspace_local_and_has_no_recency_queue(self):
        self.foreground(self.a, self.shell_a1)
        self.foreground(self.a, self.shell_a2)
        self.foreground(self.b, self.shell_b)

        resolved_a = self.resolve(self.view_a)
        resolved_b = self.resolve(self.view_b)

        self.assertEqual(resolved_a.provenance.shell_id, self.shell_a2)
        self.assertEqual(resolved_b.provenance.shell_id, self.shell_b)
        self.router.unexpected_shell_loss(self.shell_a2)
        missing = self.resolve(self.view_a)
        self.assertEqual(missing.status, RoutingStatus.NO_TARGET)
        self.assertIsNone(missing.provenance)
        self.assertEqual(self.resolve(self.view_b).provenance.shell_id, self.shell_b)

    def test_explicit_assignment_is_sticky_across_focus_and_kernel_recycle(self):
        self.foreground(self.a, self.shell_a2)
        self.assertTrue(self.router.assign_view(self.view_a, self.shell_a1).applied)
        before = self.resolve(self.view_a)
        self.foreground(self.a, self.shell_a2)

        after_focus = self.resolve(self.view_a)

        self.assertEqual(before.provenance.shell_id, self.shell_a1)
        self.assertEqual(after_focus.provenance.shell_id, self.shell_a1)
        self.assertTrue(self.router.provenance_is_current(before.provenance))

        generation = new_identity(IdentityKind.KERNEL_GENERATION)
        self.assertTrue(
            self.router.recycle_shell(
                self.shell_a1, generation, succeeded=True
            ).applied
        )
        after_recycle = self.resolve(self.view_a)
        self.assertEqual(after_recycle.provenance.shell_id, self.shell_a1)
        self.assertEqual(after_recycle.provenance.kernel_generation_id, generation)
        self.assertFalse(self.router.provenance_is_current(before.provenance))

    def test_unexpected_loss_stays_broken_until_reconnect_or_clear(self):
        self.foreground(self.a, self.shell_a2)
        self.router.assign_view(self.view_a, self.shell_a1)
        self.router.unexpected_shell_loss(self.shell_a1)

        broken = self.resolve(self.view_a)
        self.assertEqual(broken.status, RoutingStatus.BROKEN_TARGET)
        self.assertEqual(
            self.router.view_state(self.view_a).assignment.mode,
            AssignmentMode.BROKEN,
        )
        self.foreground(self.a, self.shell_a2)
        self.assertEqual(self.resolve(self.view_a).status, RoutingStatus.BROKEN_TARGET)

        generation = new_identity(IdentityKind.KERNEL_GENERATION)
        self.assertTrue(
            self.router.reconnect_shell(self.shell_a1, generation).applied
        )
        self.assertEqual(self.resolve(self.view_a).provenance.shell_id, self.shell_a1)

        self.router.unexpected_shell_loss(self.shell_a1)
        self.assertTrue(self.router.clear_assignment(self.view_a).applied)
        self.assertEqual(self.resolve(self.view_a).provenance.shell_id, self.shell_a2)

    def test_confirmed_close_clears_assignment_without_older_fallback(self):
        self.foreground(self.a, self.shell_a1)
        self.router.assign_view(self.view_a, self.shell_a1)

        self.assertTrue(self.router.confirmed_shell_close(self.shell_a1).applied)

        self.assertEqual(
            self.router.view_state(self.view_a).assignment.mode,
            AssignmentMode.IMPLICIT,
        )
        self.assertEqual(self.resolve(self.view_a).status, RoutingStatus.NO_TARGET)
        self.foreground(self.a, self.shell_a2)
        self.assertEqual(self.resolve(self.view_a).provenance.shell_id, self.shell_a2)

    def test_view_assignment_cannot_cross_workspaces_and_breaks_on_view_move(self):
        self.assertEqual(
            self.router.assign_view(self.view_a, self.shell_b).status,
            RoutingStatus.INVALID,
        )
        self.router.assign_view(self.view_a, self.shell_a1)
        before = self.resolve(self.view_a).provenance

        self.assertTrue(self.router.move_view(self.view_a, self.b).applied)

        self.assertEqual(self.resolve(self.view_a).status, RoutingStatus.BROKEN_TARGET)
        self.assertFalse(self.router.provenance_is_current(before))
        self.router.clear_assignment(self.view_a)
        self.foreground(self.b, self.shell_b)
        self.assertEqual(self.resolve(self.view_a).provenance.shell_id, self.shell_b)

    def test_shell_move_is_transitional_until_successful_recycle(self):
        self.foreground(self.a, self.shell_a1)
        before = self.router.resolve(
            ExecutionCommand.HELP,
            workspace_id=self.a,
        ).provenance

        self.assertTrue(self.router.move_shell(self.shell_a1, self.b).applied)
        moved = self.router.shell_state(self.shell_a1)
        self.assertTrue(moved.transitional)
        self.assertEqual(moved.workspace_id, self.b)
        self.assertEqual(moved.process_workspace_id, self.a)
        self.assertFalse(self.router.provenance_is_current(before))
        self.assertEqual(
            self.router.resolve(
                ExecutionCommand.HELP, workspace_id=self.a
            ).status,
            RoutingStatus.NO_TARGET,
        )

        self.foreground(self.b, self.shell_a1)
        destination = self.router.resolve(
            ExecutionCommand.EXECUTE_LINE,
            workspace_id=self.b,
        ).provenance
        self.assertEqual(destination.workspace_id, self.b)
        self.assertEqual(destination.process_workspace_id, self.a)

        self.assertTrue(self.router.move_shell(self.shell_a1, self.c).applied)
        repeated = self.router.shell_state(self.shell_a1)
        self.assertEqual(repeated.workspace_id, self.c)
        self.assertEqual(repeated.process_workspace_id, self.a)
        failed_generation = new_identity(IdentityKind.KERNEL_GENERATION)
        self.assertEqual(
            self.router.recycle_shell(
                self.shell_a1, failed_generation, succeeded=False
            ).status,
            RoutingStatus.FAILED,
        )
        self.assertEqual(self.router.shell_state(self.shell_a1), repeated)

        generation = new_identity(IdentityKind.KERNEL_GENERATION)
        self.assertTrue(
            self.router.recycle_shell(
                self.shell_a1, generation, succeeded=True
            ).applied
        )
        recycled = self.router.shell_state(self.shell_a1)
        self.assertFalse(recycled.transitional)
        self.assertEqual(recycled.process_workspace_id, self.c)
        self.assertEqual(recycled.kernel_generation_id, generation)

    def test_delayed_result_validation_rejects_changed_implicit_target(self):
        self.foreground(self.a, self.shell_a1)
        implicit = self.resolve(self.view_a).provenance
        direct = self.router.resolve(
            ExecutionCommand.DEBUGGER,
            workspace_id=self.a,
            shell_id=self.shell_a1,
        ).provenance

        self.foreground(self.a, self.shell_a2)

        self.assertFalse(self.router.provenance_is_current(implicit))
        self.assertTrue(self.router.provenance_is_current(direct))
        self.router.unexpected_shell_loss(self.shell_a1)
        self.assertFalse(self.router.provenance_is_current(direct))

    def test_execute_and_script_variants_share_resolution_but_keep_policy(self):
        self.foreground(self.a, self.shell_a1)
        execute_commands = (
            ExecutionCommand.EXECUTE_SELECTION,
            ExecutionCommand.EXECUTE_LINE,
            ExecutionCommand.EXECUTE_CELL,
            ExecutionCommand.EXECUTE_FILE,
            ExecutionCommand.EXECUTE_MAIN,
        )
        script_commands = (
            ExecutionCommand.RUN_FILE_AS_SCRIPT,
            ExecutionCommand.RUN_MAIN_AS_SCRIPT,
        )

        for command in execute_commands + script_commands:
            with self.subTest(command=command):
                resolution = self.resolve(self.view_a, command)
                self.assertTrue(resolution.resolved)
                self.assertEqual(resolution.provenance.shell_id, self.shell_a1)
                self.assertEqual(
                    resolution.provenance.policy, COMMAND_POLICIES[command]
                )
        for command in execute_commands:
            policy = COMMAND_POLICIES[command]
            self.assertTrue(policy.uses_buffer)
            self.assertFalse(policy.autosave)
            self.assertFalse(policy.recycle)
        for command in script_commands:
            policy = COMMAND_POLICIES[command]
            self.assertFalse(policy.uses_buffer)
            self.assertTrue(policy.autosave)
            self.assertTrue(policy.recycle)


if __name__ == "__main__":
    unittest.main()
