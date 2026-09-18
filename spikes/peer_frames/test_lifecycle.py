from __future__ import annotations

import unittest

from spikes.peer_frames.contract import (
    Capability,
    Direction,
    OperationStatus,
    PaneDescriptor,
    PaneKind,
    WorkspaceModel,
)
from spikes.peer_frames.fake_backend import FakeBackend
from spikes.peer_frames.identity import IdentityKind, new_identity
from spikes.peer_frames.lifecycle import DocumentViewRegistry
from spikes.peer_frames.lifecycle import (
    DirtyCloseChoice,
    DocumentCloseDisposition,
    ShellCloseChoice,
    ShellCloseDisposition,
    ShellLifecycleRegistry,
    ShellState,
)


class RecordingDocument:
    def __init__(
        self,
        *,
        dirty: bool = False,
        save_result: bool = True,
        save_clears_dirty: bool = True,
        save_raises: bool = False,
        retain_result: bool = True,
    ):
        self.dirty = dirty
        self.save_result = save_result
        self.save_clears_dirty = save_clears_dirty
        self.save_raises = save_raises
        self.retain_result = retain_result
        self.retain_results: list[bool] = []
        self.retain_count = 0
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

    def retain_document(self) -> bool:
        self.retain_count += 1
        if self.retain_results:
            return self.retain_results.pop(0)
        return self.retain_result


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

    def test_opt_in_retention_keeps_closed_view_descriptor_without_disposition(self) -> None:
        document = RecordingDocument(dirty=True)
        policy = self.registry.register_view(
            "view",
            "document",
            document,
            workspace_id=new_identity(IdentityKind.WORKSPACE),
            retain_on_final_close=True,
        )
        self.assertTrue(
            self.model.register_pane(
                PaneDescriptor("view", PaneKind.EDITOR, "view"), policy
            ).applied
        )
        self.assertTrue(self.model.create_frame("view", "frame").applied)

        result = self.model.request_close_pane("view")

        self.assertTrue(result.applied)
        self.assertEqual(document.close_count, 0)
        self.assertEqual(self.registry.retained_view_ids, {"view"})
        retained = self.registry.retained_view("view")
        self.assertEqual(retained.document_id, "document")
        self.assertEqual(retained.epoch, 2)

    def test_failed_retention_barrier_preserves_final_view(self) -> None:
        document = RecordingDocument(dirty=True, retain_result=False)
        policy = self.registry.register_view(
            "view",
            "document",
            document,
            workspace_id=new_identity(IdentityKind.WORKSPACE),
            retain_on_final_close=True,
        )
        self.assertTrue(
            self.model.register_pane(
                PaneDescriptor("view", PaneKind.EDITOR, "view"), policy
            ).applied
        )
        self.assertTrue(self.model.create_frame("view", "frame").applied)

        result = self.model.request_close_pane("view")

        self.assertEqual(result.status, OperationStatus.REFUSED)
        self.assertEqual(document.retain_count, 1)
        self.assertEqual(document.close_count, 0)
        self.assertEqual(self.registry.retained_view_ids, set())
        self.assertIn("view", self.model.panes)

    def test_retention_retry_commits_once_after_initial_failure(self) -> None:
        document = RecordingDocument(dirty=True)
        document.retain_results = [False, True]
        policy = self.registry.register_view(
            "view",
            "document",
            document,
            workspace_id=new_identity(IdentityKind.WORKSPACE),
            retain_on_final_close=True,
        )
        self.assertTrue(
            self.model.register_pane(
                PaneDescriptor("view", PaneKind.EDITOR, "view"), policy
            ).applied
        )
        self.assertTrue(self.model.create_frame("view", "frame").applied)

        first = self.model.request_close_pane("view")
        second = self.model.request_close_pane("view")

        self.assertEqual(first.status, OperationStatus.REFUSED)
        self.assertTrue(second.applied)
        self.assertEqual(document.retain_count, 2)
        self.assertEqual(document.close_count, 0)
        self.assertNotIn("view", self.model.panes)
        self.assertEqual(self.registry.retained_view_ids, {"view"})

    def test_two_views_close_non_final_then_retain_final_once(self) -> None:
        document = RecordingDocument(dirty=True)
        workspace = new_identity(IdentityKind.WORKSPACE)
        first = self.registry.register_view(
            "first",
            "document",
            document,
            workspace_id=workspace,
            retain_on_final_close=True,
        )
        second = self.registry.register_view(
            "second",
            "document",
            document,
            workspace_id=workspace,
            retain_on_final_close=True,
        )
        self.assertTrue(
            self.model.register_pane(
                PaneDescriptor("first", PaneKind.EDITOR, "first"), first
            ).applied
        )
        self.assertTrue(
            self.model.register_pane(
                PaneDescriptor("second", PaneKind.EDITOR, "second"), second
            ).applied
        )
        self.assertTrue(self.model.create_frame("first", "first-frame").applied)
        self.assertTrue(
            self.model.create_frame("second", "second-frame").applied
        )

        close_first = self.model.request_close_pane("first")
        self.assertTrue(close_first.applied)
        self.assertEqual(document.retain_count, 0)
        self.assertEqual(self.registry.view_ids("document"), {"second"})
        self.assertEqual(self.registry.retained_view_ids, set())

        close_second = self.model.request_close_pane("second")
        self.assertTrue(close_second.applied)
        self.assertEqual(document.retain_count, 1)
        self.assertEqual(document.close_count, 0)
        self.assertEqual(self.registry.retained_view_ids, {"second"})


class RecordingShell:
    def __init__(self, state: ShellState):
        self.state = state
        self.state_sequence: list[ShellState] = []
        self.close_dispositions: list[ShellCloseDisposition] = []

    def shell_state(self) -> ShellState:
        if self.state_sequence:
            self.state = self.state_sequence.pop(0)
        return self.state

    def close_shell(self, disposition: ShellCloseDisposition) -> None:
        self.close_dispositions.append(disposition)


class CountingClosePolicy:
    def __init__(self, delegate):
        self.delegate = delegate
        self.prepare_count = 0
        self.validate_count = 0
        self.did_close_count = 0

    def prepare_close(self, pane, request):
        self.prepare_count += 1
        return self.delegate.prepare_close(pane, request)

    def validate_close(self, pane, request):
        self.validate_count += 1
        return self.delegate.validate_close(pane, request)

    def did_close(self, pane, request):
        self.did_close_count += 1
        return self.delegate.did_close(pane, request)


class ShellLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = WorkspaceModel(FakeBackend())
        self.registry = ShellLifecycleRegistry()

    def add_shell(
        self, pane_id: str, shell: RecordingShell, frame_id: str
    ) -> None:
        policy = self.registry.register_shell(pane_id, shell)
        self.assertTrue(
            self.model.register_pane(
                PaneDescriptor(pane_id, PaneKind.SHELL, pane_id), policy
            ).applied
        )
        self.assertTrue(self.model.create_frame(pane_id, frame_id).applied)

    def resolve(self, votes, choice=ShellCloseChoice.TERMINATE):
        return self.registry.resolve_confirmations(
            votes, lambda _pane_id, _shell: choice
        )

    def test_dead_shell_closes_without_confirmation(self) -> None:
        shell = RecordingShell(ShellState.DEAD)
        self.add_shell("shell", shell, "frame")

        result = self.model.request_close_pane("shell")

        self.assertTrue(result.applied)
        self.assertEqual(shell.close_dispositions, [ShellCloseDisposition.DEAD])
        self.assertEqual(self.registry.pane_ids, frozenset())
        self.assertFalse(self.model.shutdown_requested)

    def test_every_live_shell_state_requires_confirmation(self) -> None:
        for state in (
            ShellState.IDLE,
            ShellState.RUNNING,
            ShellState.DEBUGGING,
            ShellState.STARTING_OR_UNKNOWN,
        ):
            with self.subTest(state=state):
                model = WorkspaceModel(FakeBackend())
                registry = ShellLifecycleRegistry()
                shell = RecordingShell(state)
                policy = registry.register_shell("shell", shell)
                model.register_pane(
                    PaneDescriptor("shell", PaneKind.SHELL, "Shell"), policy
                )
                model.create_frame("shell", "frame")
                before = model.serialize_layout()

                result = model.request_close_pane("shell")

                self.assertEqual(
                    result.status, OperationStatus.CONFIRMATION_REQUIRED
                )
                self.assertEqual(model.serialize_layout(), before)
                self.assertEqual(shell.close_dispositions, [])

    def test_terminate_confirmation_commits_before_shell_close(self) -> None:
        shell = RecordingShell(ShellState.RUNNING)
        self.add_shell("shell", shell, "frame")

        def close_shell(disposition):
            self.assertNotIn("shell", self.model.panes)
            shell.close_dispositions.append(disposition)

        shell.close_shell = close_shell
        result = self.model.request_close_pane("shell", self.resolve)

        self.assertTrue(result.applied)
        self.assertEqual(
            shell.close_dispositions, [ShellCloseDisposition.TERMINATED]
        )

    def test_cancel_preserves_live_shell_and_topology(self) -> None:
        shell = RecordingShell(ShellState.IDLE)
        self.add_shell("shell", shell, "frame")
        before = self.model.serialize_layout()

        result = self.model.request_close_pane(
            "shell",
            lambda votes: self.resolve(votes, ShellCloseChoice.CANCEL),
        )

        self.assertEqual(result.status, OperationStatus.CANCELLED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(shell.close_dispositions, [])

    def test_multi_shell_choices_are_collected_before_any_close(self) -> None:
        first = RecordingShell(ShellState.IDLE)
        second = RecordingShell(ShellState.DEBUGGING)
        self.add_shell("first", first, "workspace")
        self.add_shell("second", second, "temporary")
        self.assertTrue(self.model.tab("second", "first").applied)
        seen: list[str] = []

        def choose(pane_id, _shell):
            self.assertEqual(first.close_dispositions + second.close_dispositions, [])
            seen.append(pane_id)
            return ShellCloseChoice.TERMINATE

        result = self.model.request_close_frame(
            "workspace",
            lambda votes: self.registry.resolve_confirmations(votes, choose),
        )

        self.assertTrue(result.applied)
        self.assertEqual(seen, ["first", "second"])
        self.assertEqual(
            first.close_dispositions, [ShellCloseDisposition.TERMINATED]
        )
        self.assertEqual(
            second.close_dispositions, [ShellCloseDisposition.TERMINATED]
        )

    def test_multi_shell_cancel_closes_nothing(self) -> None:
        first = RecordingShell(ShellState.IDLE)
        second = RecordingShell(ShellState.RUNNING)
        self.add_shell("first", first, "workspace")
        self.add_shell("second", second, "temporary")
        self.assertTrue(self.model.tab("second", "first").applied)
        before = self.model.serialize_layout()

        result = self.model.request_close_frame(
            "workspace",
            lambda votes: self.registry.resolve_confirmations(
                votes,
                lambda pane_id, _shell: (
                    ShellCloseChoice.TERMINATE
                    if pane_id == "first"
                    else ShellCloseChoice.CANCEL
                ),
            ),
        )

        self.assertEqual(result.status, OperationStatus.CANCELLED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(first.close_dispositions + second.close_dispositions, [])

    def test_dead_to_live_drift_without_confirmation_is_refused(self) -> None:
        shell = RecordingShell(ShellState.DEAD)
        shell.state_sequence = [ShellState.DEAD, ShellState.IDLE]
        self.add_shell("shell", shell, "frame")
        before = self.model.serialize_layout()

        result = self.model.request_close_pane("shell")

        self.assertEqual(result.status, OperationStatus.REFUSED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(shell.close_dispositions, [])

    def test_live_state_drift_remains_covered_by_termination_choice(self) -> None:
        shell = RecordingShell(ShellState.RUNNING)
        shell.state_sequence = [ShellState.RUNNING, ShellState.DEBUGGING]
        self.add_shell("shell", shell, "frame")

        result = self.model.request_close_pane("shell", self.resolve)

        self.assertTrue(result.applied)
        self.assertEqual(
            shell.close_dispositions, [ShellCloseDisposition.TERMINATED]
        )

    def test_live_to_dead_drift_closes_without_termination(self) -> None:
        shell = RecordingShell(ShellState.RUNNING)
        shell.state_sequence = [ShellState.RUNNING, ShellState.DEAD, ShellState.DEAD]
        self.add_shell("shell", shell, "frame")

        result = self.model.request_close_pane("shell", self.resolve)

        self.assertTrue(result.applied)
        self.assertEqual(shell.close_dispositions, [ShellCloseDisposition.DEAD])

    def test_generic_confirmation_cannot_approve_live_termination(self) -> None:
        shell = RecordingShell(ShellState.IDLE)
        self.add_shell("shell", shell, "frame")
        before = self.model.serialize_layout()

        result = self.model.request_close_pane("shell", lambda _votes: True)

        self.assertEqual(result.status, OperationStatus.REFUSED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(shell.close_dispositions, [])

    def test_wider_transaction_veto_can_revoke_pending_termination(self) -> None:
        shell = RecordingShell(ShellState.RUNNING)
        self.add_shell("shell", shell, "frame")
        votes = self.model.request_close_pane("shell").confirmations
        self.assertTrue(self.registry.resolve_confirmations(votes, lambda *_: "terminate"))

        self.registry.cancel_pending(("shell",))
        before = self.model.serialize_layout()
        result = self.model.request_close_pane("shell", lambda _votes: True)

        self.assertEqual(result.status, OperationStatus.REFUSED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertEqual(shell.close_dispositions, [])

    def test_reentrant_close_is_refused_during_shell_choice(self) -> None:
        shell = RecordingShell(ShellState.DEBUGGING)
        self.add_shell("shell", shell, "frame")
        nested_results = []

        def choose(_pane_id, _shell):
            nested_results.append(self.model.request_close_pane("shell"))
            return ShellCloseChoice.CANCEL

        result = self.model.request_close_pane(
            "shell",
            lambda votes: self.registry.resolve_confirmations(votes, choose),
        )

        self.assertEqual(result.status, OperationStatus.CANCELLED)
        self.assertEqual(nested_results[0].status, OperationStatus.REFUSED)
        self.assertIn("already in progress", nested_results[0].detail)

    def test_move_operations_never_close_or_terminate_shell(self) -> None:
        shell = RecordingShell(ShellState.DEBUGGING)
        target = RecordingShell(ShellState.DEAD)
        self.add_shell("shell", shell, "shell-frame")
        self.add_shell("target", target, "target-frame")

        self.assertTrue(self.model.tab("shell", "target").applied)
        self.assertTrue(self.model.float("shell", "floated").applied)

        self.assertEqual(shell.close_dispositions, [])
        self.assertEqual(target.close_dispositions, [])
        self.assertEqual(self.registry.pane_ids, {"shell", "target"})
        self.assertFalse(self.model.shutdown_requested)


class PlacementLifecycleInvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = FakeBackend()
        self.model = WorkspaceModel(self.backend)
        self.documents = DocumentViewRegistry()
        self.document = RecordingDocument(dirty=True)
        self.shells = ShellLifecycleRegistry()
        self.shell_objects: dict[str, RecordingShell] = {}
        self.counting_policies: dict[str, CountingClosePolicy] = {}

        for pane_id, pinned in (("view-a", False), ("view-b", True)):
            policy = self.documents.register_view(
                pane_id,
                "shared-document",
                self.document,
                is_pinned=lambda pinned=pinned: pinned,
            )
            self._register(pane_id, PaneKind.EDITOR, policy)

        for state in ShellState:
            pane_id = f"shell-{state.value}"
            shell = RecordingShell(state)
            self.shell_objects[pane_id] = shell
            self._register(
                pane_id,
                PaneKind.SHELL,
                self.shells.register_shell(pane_id, shell),
            )

        self.assertTrue(
            self.model.register_pane(
                PaneDescriptor("target", PaneKind.TOOL, "target")
            ).applied
        )
        self.assertTrue(self.model.create_frame("target", "frame-target").applied)
        self.pane_ids = frozenset(self.model.panes)
        self.policy_ids = {
            pane_id: id(policy) for pane_id, policy in self.model._policies.items()
        }
        self.shell_states = {
            pane_id: shell.state for pane_id, shell in self.shell_objects.items()
        }

    def _register(self, pane_id, kind, policy) -> None:
        counting = CountingClosePolicy(policy)
        self.counting_policies[pane_id] = counting
        self.assertTrue(
            self.model.register_pane(
                PaneDescriptor(pane_id, kind, pane_id), counting
            ).applied
        )
        self.assertTrue(
            self.model.create_frame(pane_id, f"frame-{pane_id}").applied
        )

    def assert_lifecycle_neutral(self) -> None:
        self.assertEqual(frozenset(self.model.panes), self.pane_ids)
        self.assertEqual(
            {pane_id: id(policy) for pane_id, policy in self.model._policies.items()},
            self.policy_ids,
        )
        self.assertEqual(
            self.documents.view_ids("shared-document"), {"view-a", "view-b"}
        )
        self.assertTrue(self.document.dirty)
        self.assertEqual(self.document.save_count, 0)
        self.assertEqual(self.document.close_count, 0)
        self.assertEqual(self.shells.pane_ids, frozenset(self.shell_objects))
        self.assertEqual(
            {pane_id: shell.state for pane_id, shell in self.shell_objects.items()},
            self.shell_states,
        )
        self.assertTrue(
            all(not shell.close_dispositions for shell in self.shell_objects.values())
        )
        self.assertTrue(
            all(
                (
                    policy.prepare_count,
                    policy.validate_count,
                    policy.did_close_count,
                )
                == (0, 0, 0)
                for policy in self.counting_policies.values()
            )
        )
        self.assertFalse(self.model.shutdown_requested)

    def apply(self, operation) -> None:
        result = operation()
        self.assertTrue(result.applied, result.detail)
        self.assert_lifecycle_neutral()

    def test_all_programmatic_placement_paths_are_lifecycle_neutral(self) -> None:
        self.apply(lambda: self.model.tab("view-b", "view-a"))
        self.apply(lambda: self.model.tab("view-b", "view-a"))
        self.apply(lambda: self.model.float("view-b", "shared-source-remains"))
        self.apply(lambda: self.model.float("view-b", "shared-source-emptied"))
        self.apply(lambda: self.model.tab("view-b", "view-a"))

        shell_ids = tuple(self.shell_objects)
        serial = 0
        for outer in (False, True):
            for index, direction in enumerate(Direction):
                pane_id = shell_ids[index % len(shell_ids)]
                self.apply(
                    lambda pane_id=pane_id, direction=direction, outer=outer: (
                        self.model.split(
                            pane_id, "target", direction, outer=outer
                        )
                    )
                )
                self.apply(
                    lambda pane_id=pane_id: self.model.tab(pane_id, "target")
                )
                self.apply(
                    lambda pane_id=pane_id, direction=direction, outer=outer: (
                        self.model.split(
                            pane_id, "target", direction, outer=outer
                        )
                    )
                )
                serial += 1
                self.apply(
                    lambda pane_id=pane_id, serial=serial: self.model.float(
                        pane_id, f"matrix-float-{serial}"
                    )
                )

    def test_valid_and_invalid_backend_adoption_is_lifecycle_neutral(self) -> None:
        planner = WorkspaceModel(FakeBackend())
        for pane in self.model.panes.values():
            self.assertTrue(planner.register_pane(pane).applied)
        self.assertTrue(planner.restore_layout(self.model.serialize_layout()).applied)
        self.assertTrue(planner.tab("view-b", "view-a").applied)

        self.assertTrue(
            self.model.adopt_backend_layout(planner.serialize_layout()).applied
        )
        self.assert_lifecycle_neutral()

        for malformed in (
            {**self.model.serialize_layout(), "frames": []},
            {
                **self.model.serialize_layout(),
                "frames": self.model.serialize_layout()["frames"] * 2,
            },
        ):
            before = self.model.serialize_layout()
            result = self.model.adopt_backend_layout(malformed)
            self.assertEqual(result.status, OperationStatus.INVALID)
            self.assertEqual(self.model.serialize_layout(), before)
            self.assert_lifecycle_neutral()

    def test_invalid_placement_requests_never_enter_close_policy(self) -> None:
        existing_frame = self.model.resolve_active_context().frame_id
        before = self.model.serialize_layout()
        operations = (
            lambda: self.model.tab("view-a", "view-a"),
            lambda: self.model.tab("missing", "view-a"),
            lambda: self.model.split("view-a", "view-a", Direction.LEFT),
            lambda: self.model.split("missing", "view-a", Direction.RIGHT),
            lambda: self.model.float("view-a", existing_frame),
            lambda: self.model.float("missing", "missing-frame"),
        )
        for operation in operations:
            result = operation()
            self.assertEqual(result.status, OperationStatus.INVALID)
            self.assertEqual(self.model.serialize_layout(), before)
            self.assert_lifecycle_neutral()

    def test_unsupported_placement_never_enters_close_policy(self) -> None:
        backend = FakeBackend(frozenset({Capability.CREATE_FRAME}))
        model = WorkspaceModel(backend)
        registry = DocumentViewRegistry()
        document = RecordingDocument(dirty=True)
        policy = CountingClosePolicy(
            registry.register_view("view", "document", document)
        )
        self.assertTrue(
            model.register_pane(
                PaneDescriptor("view", PaneKind.EDITOR, "view"), policy
            ).applied
        )
        self.assertTrue(
            model.register_pane(
                PaneDescriptor("target", PaneKind.TOOL, "target")
            ).applied
        )
        self.assertTrue(model.create_frame("view", "view-frame").applied)
        self.assertTrue(model.create_frame("target", "target-frame").applied)
        before = model.serialize_layout()

        for operation in (
            lambda: model.tab("view", "target"),
            lambda: model.split("view", "target", Direction.LEFT),
            lambda: model.split("view", "target", Direction.LEFT, outer=True),
            lambda: model.float("view", "floated"),
        ):
            self.assertEqual(operation().status, OperationStatus.UNSUPPORTED)
            self.assertEqual(model.serialize_layout(), before)
            self.assertEqual(
                (policy.prepare_count, policy.validate_count, policy.did_close_count),
                (0, 0, 0),
            )
            self.assertTrue(document.dirty)
            self.assertEqual(document.save_count + document.close_count, 0)

    def test_backend_render_failure_does_not_enter_close_policy(self) -> None:
        class FailingBackend(FakeBackend):
            fail = False

            def render(self, snapshot):
                if self.fail:
                    raise RuntimeError("render failed")
                super().render(snapshot)

        backend = FailingBackend()
        model = WorkspaceModel(backend)
        registry = ShellLifecycleRegistry()
        shell = RecordingShell(ShellState.RUNNING)
        policy = CountingClosePolicy(registry.register_shell("shell", shell))
        model.register_pane(PaneDescriptor("shell", PaneKind.SHELL, "shell"), policy)
        model.register_pane(PaneDescriptor("target", PaneKind.TOOL, "target"))
        model.create_frame("shell", "shell-frame")
        model.create_frame("target", "target-frame")
        backend.fail = True

        with self.assertRaisesRegex(RuntimeError, "render failed"):
            model.tab("shell", "target")

        self.assertEqual(
            (policy.prepare_count, policy.validate_count, policy.did_close_count),
            (0, 0, 0),
        )
        self.assertEqual(shell.close_dispositions, [])
        self.assertEqual(registry.pane_ids, {"shell"})


class DocumentViewLifecycleTestsContinued(unittest.TestCase):
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

    def test_application_shutdown_retains_each_dirty_document_once(self) -> None:
        first = RecordingDocument(dirty=True)
        second = RecordingDocument(dirty=True)
        self.add_view("first-a", "first-document", first, "first-a-frame")
        self.add_view("first-b", "first-document", first, "first-b-frame")
        self.add_view("second", "second-document", second, "second-frame")
        retained = []

        result = self.model.request_shutdown(
            lambda votes: self.registry.resolve_retention(
                votes,
                lambda documents: retained.extend(
                    document_id for document_id, _lifecycle in documents
                )
                or True,
            )
        )

        self.assertTrue(result.applied)
        self.assertEqual(retained, ["first-document", "second-document"])
        self.assertEqual(
            first.close_dispositions, [DocumentCloseDisposition.RETAINED]
        )
        self.assertEqual(
            second.close_dispositions, [DocumentCloseDisposition.RETAINED]
        )

    def test_failed_application_retention_preserves_complete_topology(self) -> None:
        document = RecordingDocument(dirty=True)
        self.add_view("view", "document", document, "frame")
        before = self.model.serialize_layout()

        result = self.model.request_shutdown(
            lambda votes: self.registry.resolve_retention(
                votes, lambda _documents: False
            )
        )

        self.assertEqual(result.status, OperationStatus.CANCELLED)
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertTrue(document.dirty)
        self.assertEqual(document.close_count, 0)
        self.assertFalse(self.model.shutdown_requested)

    def test_pinned_document_only_yields_to_application_shutdown(self) -> None:
        document = RecordingDocument(dirty=True)
        self.add_view("pinned", "document", document, "frame", pinned=True)
        before = self.model.serialize_layout()

        self.assertEqual(
            self.model.request_close_frame("frame").status,
            OperationStatus.REFUSED,
        )
        self.assertEqual(self.model.serialize_layout(), before)
        result = self.model.request_shutdown(
            lambda votes: self.registry.resolve_retention(
                votes, lambda _documents: True
            )
        )

        self.assertTrue(result.applied)
        self.assertEqual(
            document.close_dispositions, [DocumentCloseDisposition.RETAINED]
        )

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
