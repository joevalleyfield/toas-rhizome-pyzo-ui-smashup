"""Live workspace-local execution routing and provenance policy."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .identity import ApplicationIdentity, IdentityKind, new_identity


class ExecutionCommand(str, Enum):
    EXECUTE_SELECTION = "execute-selection"
    EXECUTE_LINE = "execute-line"
    EXECUTE_CELL = "execute-cell"
    EXECUTE_FILE = "execute-file"
    EXECUTE_MAIN = "execute-main"
    RUN_FILE_AS_SCRIPT = "run-file-as-script"
    RUN_MAIN_AS_SCRIPT = "run-main-as-script"
    COMPLETION = "completion"
    HELP = "help"
    TOOL = "tool"
    DEBUGGER = "debugger"


@dataclass(frozen=True)
class ExecutionCommandPolicy:
    uses_buffer: bool
    autosave: bool
    recycle: bool


COMMAND_POLICIES = {
    command: ExecutionCommandPolicy(True, False, False)
    for command in (
        ExecutionCommand.EXECUTE_SELECTION,
        ExecutionCommand.EXECUTE_LINE,
        ExecutionCommand.EXECUTE_CELL,
        ExecutionCommand.EXECUTE_FILE,
        ExecutionCommand.EXECUTE_MAIN,
    )
}
COMMAND_POLICIES.update(
    {
        command: ExecutionCommandPolicy(False, True, True)
        for command in (
            ExecutionCommand.RUN_FILE_AS_SCRIPT,
            ExecutionCommand.RUN_MAIN_AS_SCRIPT,
        )
    }
)
COMMAND_POLICIES.update(
    {
        command: ExecutionCommandPolicy(False, False, False)
        for command in (
            ExecutionCommand.COMPLETION,
            ExecutionCommand.HELP,
            ExecutionCommand.TOOL,
            ExecutionCommand.DEBUGGER,
        )
    }
)


class AssignmentMode(str, Enum):
    IMPLICIT = "implicit"
    EXPLICIT = "explicit"
    BROKEN = "broken"
    DIRECT = "direct"


class RoutingStatus(str, Enum):
    RESOLVED = "resolved"
    NO_TARGET = "no-target"
    BROKEN_TARGET = "broken-target"
    APPLIED = "applied"
    INVALID = "invalid"
    FAILED = "failed"


@dataclass(frozen=True)
class RoutingResult:
    status: RoutingStatus
    detail: str = ""

    @property
    def applied(self) -> bool:
        return self.status is RoutingStatus.APPLIED


@dataclass(frozen=True)
class ExecutionAssignment:
    mode: AssignmentMode = AssignmentMode.IMPLICIT
    shell_id: ApplicationIdentity | None = None


@dataclass(frozen=True)
class ViewRoutingState:
    identity: ApplicationIdentity
    workspace_id: ApplicationIdentity
    epoch: int = 1
    assignment: ExecutionAssignment = ExecutionAssignment()


@dataclass(frozen=True)
class ShellRoutingState:
    identity: ApplicationIdentity
    workspace_id: ApplicationIdentity
    process_workspace_id: ApplicationIdentity
    kernel_generation_id: ApplicationIdentity
    epoch: int = 1
    eligible: bool = True

    @property
    def transitional(self) -> bool:
        return self.workspace_id != self.process_workspace_id


@dataclass(frozen=True)
class ExecutionProvenance:
    operation_id: ApplicationIdentity
    command: ExecutionCommand
    policy: ExecutionCommandPolicy
    assignment_mode: AssignmentMode
    workspace_id: ApplicationIdentity
    view_id: ApplicationIdentity | None
    view_epoch: int | None
    shell_id: ApplicationIdentity
    shell_epoch: int
    kernel_generation_id: ApplicationIdentity
    process_workspace_id: ApplicationIdentity


@dataclass(frozen=True)
class ExecutionResolution:
    status: RoutingStatus
    detail: str = ""
    provenance: ExecutionProvenance | None = None

    @property
    def resolved(self) -> bool:
        return self.status is RoutingStatus.RESOLVED


class ExecutionRouter:
    """Resolve live operations without application-global shell fallback."""

    def __init__(self) -> None:
        self._workspaces: set[ApplicationIdentity] = set()
        self._views: dict[ApplicationIdentity, ViewRoutingState] = {}
        self._shells: dict[ApplicationIdentity, ShellRoutingState] = {}
        self._foreground_shells: dict[
            ApplicationIdentity, ApplicationIdentity
        ] = {}

    def register_workspace(self, workspace_id: ApplicationIdentity) -> None:
        self._validate_identity(workspace_id, IdentityKind.WORKSPACE)
        if workspace_id in self._workspaces:
            raise ValueError(f"workspace is already registered: {workspace_id}")
        self._workspaces.add(workspace_id)

    def register_view(
        self,
        view_id: ApplicationIdentity,
        workspace_id: ApplicationIdentity,
    ) -> None:
        self._validate_identity(view_id, IdentityKind.VIEW)
        self._require_workspace(workspace_id)
        if view_id in self._views:
            raise ValueError(f"view is already registered: {view_id}")
        self._views[view_id] = ViewRoutingState(view_id, workspace_id)
        self.assert_invariants()

    def register_shell(
        self,
        shell_id: ApplicationIdentity,
        workspace_id: ApplicationIdentity,
        kernel_generation_id: ApplicationIdentity,
    ) -> None:
        self._validate_identity(shell_id, IdentityKind.SHELL)
        self._validate_identity(
            kernel_generation_id, IdentityKind.KERNEL_GENERATION
        )
        self._require_workspace(workspace_id)
        if shell_id in self._shells:
            raise ValueError(f"shell is already registered: {shell_id}")
        self._shells[shell_id] = ShellRoutingState(
            shell_id,
            workspace_id,
            workspace_id,
            kernel_generation_id,
        )
        self.assert_invariants()

    def view_state(self, view_id: ApplicationIdentity) -> ViewRoutingState:
        try:
            return self._views[view_id]
        except KeyError:
            raise KeyError(f"unknown view: {view_id}") from None

    def shell_state(self, shell_id: ApplicationIdentity) -> ShellRoutingState:
        try:
            return self._shells[shell_id]
        except KeyError:
            raise KeyError(f"unknown shell: {shell_id}") from None

    def foreground_shell(
        self,
        workspace_id: ApplicationIdentity,
        shell_id: ApplicationIdentity,
    ) -> RoutingResult:
        if workspace_id not in self._workspaces:
            return self._invalid("unknown workspace")
        shell = self._shells.get(shell_id)
        if shell is None or not shell.eligible:
            return self._invalid("shell is not eligible")
        if shell.workspace_id != workspace_id:
            return self._invalid("shell belongs to another workspace")
        self._foreground_shells[workspace_id] = shell_id
        self.assert_invariants()
        return self._applied()

    def assign_view(
        self,
        view_id: ApplicationIdentity,
        shell_id: ApplicationIdentity,
    ) -> RoutingResult:
        view = self._views.get(view_id)
        shell = self._shells.get(shell_id)
        if view is None:
            return self._invalid("unknown view")
        if shell is None or not shell.eligible:
            return self._invalid("shell is not eligible")
        if view.workspace_id != shell.workspace_id:
            return self._invalid("cross-workspace assignment is not supported")
        self._views[view_id] = replace(
            view,
            assignment=ExecutionAssignment(AssignmentMode.EXPLICIT, shell_id),
        )
        self.assert_invariants()
        return self._applied()

    def clear_assignment(self, view_id: ApplicationIdentity) -> RoutingResult:
        view = self._views.get(view_id)
        if view is None:
            return self._invalid("unknown view")
        self._views[view_id] = replace(view, assignment=ExecutionAssignment())
        self.assert_invariants()
        return self._applied()

    def move_view(
        self,
        view_id: ApplicationIdentity,
        workspace_id: ApplicationIdentity,
    ) -> RoutingResult:
        view = self._views.get(view_id)
        if view is None:
            return self._invalid("unknown view")
        if workspace_id not in self._workspaces:
            return self._invalid("unknown workspace")
        if view.workspace_id == workspace_id:
            return self._invalid("view already belongs to the target workspace")
        assignment = view.assignment
        if assignment.mode is AssignmentMode.EXPLICIT:
            shell = self._shells.get(assignment.shell_id)
            if shell is None or shell.workspace_id != workspace_id:
                assignment = replace(assignment, mode=AssignmentMode.BROKEN)
        self._views[view_id] = replace(
            view,
            workspace_id=workspace_id,
            epoch=view.epoch + 1,
            assignment=assignment,
        )
        self.assert_invariants()
        return self._applied()

    def close_view(self, view_id: ApplicationIdentity) -> RoutingResult:
        if self._views.pop(view_id, None) is None:
            return self._invalid("unknown view")
        self.assert_invariants()
        return self._applied()

    def move_shell(
        self,
        shell_id: ApplicationIdentity,
        workspace_id: ApplicationIdentity,
    ) -> RoutingResult:
        shell = self._shells.get(shell_id)
        if shell is None:
            return self._invalid("unknown shell")
        if workspace_id not in self._workspaces:
            return self._invalid("unknown workspace")
        if shell.workspace_id == workspace_id:
            return self._invalid("shell already belongs to the target workspace")
        source_id = shell.workspace_id
        self._shells[shell_id] = replace(
            shell,
            workspace_id=workspace_id,
            epoch=shell.epoch + 1,
        )
        if self._foreground_shells.get(source_id) == shell_id:
            del self._foreground_shells[source_id]
        self._break_assignments_to_mismatched_shell(shell_id)
        self.assert_invariants()
        return self._applied()

    def recycle_shell(
        self,
        shell_id: ApplicationIdentity,
        kernel_generation_id: ApplicationIdentity,
        *,
        succeeded: bool,
    ) -> RoutingResult:
        shell = self._shells.get(shell_id)
        if shell is None:
            return self._invalid("unknown shell")
        self._validate_identity(
            kernel_generation_id, IdentityKind.KERNEL_GENERATION
        )
        if not succeeded:
            return RoutingResult(RoutingStatus.FAILED, "kernel recycle failed")
        if kernel_generation_id == shell.kernel_generation_id:
            return self._invalid("kernel recycle requires a new generation")
        self._shells[shell_id] = replace(
            shell,
            process_workspace_id=shell.workspace_id,
            kernel_generation_id=kernel_generation_id,
            epoch=shell.epoch + 1,
            eligible=True,
        )
        self.assert_invariants()
        return self._applied()

    def unexpected_shell_loss(
        self, shell_id: ApplicationIdentity
    ) -> RoutingResult:
        shell = self._shells.get(shell_id)
        if shell is None:
            return self._invalid("unknown shell")
        self._shells[shell_id] = replace(
            shell,
            eligible=False,
            epoch=shell.epoch + 1,
        )
        for view_id, view in tuple(self._views.items()):
            if (
                view.assignment.mode is AssignmentMode.EXPLICIT
                and view.assignment.shell_id == shell_id
            ):
                self._views[view_id] = replace(
                    view,
                    assignment=replace(
                        view.assignment, mode=AssignmentMode.BROKEN
                    ),
                )
        self.assert_invariants()
        return self._applied()

    def reconnect_shell(
        self,
        shell_id: ApplicationIdentity,
        kernel_generation_id: ApplicationIdentity,
    ) -> RoutingResult:
        shell = self._shells.get(shell_id)
        if shell is None:
            return self._invalid("unknown shell identity")
        if shell.eligible:
            return self._invalid("shell is already connected")
        self._validate_identity(
            kernel_generation_id, IdentityKind.KERNEL_GENERATION
        )
        self._shells[shell_id] = replace(
            shell,
            kernel_generation_id=kernel_generation_id,
            epoch=shell.epoch + 1,
            eligible=True,
        )
        current = self._shells[shell_id]
        for view_id, view in tuple(self._views.items()):
            if (
                view.assignment.mode is AssignmentMode.BROKEN
                and view.assignment.shell_id == shell_id
                and view.workspace_id == current.workspace_id
            ):
                self._views[view_id] = replace(
                    view,
                    assignment=replace(
                        view.assignment, mode=AssignmentMode.EXPLICIT
                    ),
                )
        self.assert_invariants()
        return self._applied()

    def confirmed_shell_close(
        self, shell_id: ApplicationIdentity
    ) -> RoutingResult:
        shell = self._shells.pop(shell_id, None)
        if shell is None:
            return self._invalid("unknown shell")
        for workspace_id, foreground_id in tuple(self._foreground_shells.items()):
            if foreground_id == shell_id:
                del self._foreground_shells[workspace_id]
        for view_id, view in tuple(self._views.items()):
            if view.assignment.shell_id == shell_id:
                self._views[view_id] = replace(
                    view, assignment=ExecutionAssignment()
                )
        self.assert_invariants()
        return self._applied()

    def resolve(
        self,
        command: ExecutionCommand,
        *,
        view_id: ApplicationIdentity | None = None,
        workspace_id: ApplicationIdentity | None = None,
        shell_id: ApplicationIdentity | None = None,
    ) -> ExecutionResolution:
        if not isinstance(command, ExecutionCommand):
            return self._unresolved(RoutingStatus.INVALID, "unknown command")
        selection = self._select_target(
            view_id=view_id,
            workspace_id=workspace_id,
            shell_id=shell_id,
        )
        if isinstance(selection, ExecutionResolution):
            return selection
        selected_workspace, view, shell, assignment_mode = selection
        return ExecutionResolution(
            RoutingStatus.RESOLVED,
            provenance=ExecutionProvenance(
                operation_id=new_identity(IdentityKind.OPERATION),
                command=command,
                policy=COMMAND_POLICIES[command],
                assignment_mode=assignment_mode,
                workspace_id=selected_workspace,
                view_id=view.identity if view is not None else None,
                view_epoch=view.epoch if view is not None else None,
                shell_id=shell.identity,
                shell_epoch=shell.epoch,
                kernel_generation_id=shell.kernel_generation_id,
                process_workspace_id=shell.process_workspace_id,
            ),
        )

    def provenance_is_current(self, provenance: ExecutionProvenance) -> bool:
        if not isinstance(provenance, ExecutionProvenance):
            return False
        shell = self._shells.get(provenance.shell_id)
        if (
            shell is None
            or not shell.eligible
            or shell.workspace_id != provenance.workspace_id
            or shell.process_workspace_id != provenance.process_workspace_id
            or shell.epoch != provenance.shell_epoch
            or shell.kernel_generation_id != provenance.kernel_generation_id
        ):
            return False
        selection = self._select_target(
            view_id=provenance.view_id,
            workspace_id=provenance.workspace_id,
            shell_id=(
                provenance.shell_id
                if provenance.assignment_mode is AssignmentMode.DIRECT
                else None
            ),
        )
        if isinstance(selection, ExecutionResolution):
            return False
        _, view, selected_shell, assignment_mode = selection
        return bool(
            selected_shell.identity == provenance.shell_id
            and assignment_mode is provenance.assignment_mode
            and (
                view is None
                or (
                    view.identity == provenance.view_id
                    and view.epoch == provenance.view_epoch
                )
            )
        )

    def assert_invariants(self) -> bool:
        for workspace_id in self._workspaces:
            assert workspace_id.kind is IdentityKind.WORKSPACE
        for view in self._views.values():
            assert view.identity.kind is IdentityKind.VIEW
            assert view.workspace_id in self._workspaces
            assert view.epoch > 0
            if view.assignment.mode is AssignmentMode.IMPLICIT:
                assert view.assignment.shell_id is None
            else:
                assert view.assignment.shell_id is not None
                assert view.assignment.shell_id.kind is IdentityKind.SHELL
            if view.assignment.mode is AssignmentMode.EXPLICIT:
                shell = self._shells[view.assignment.shell_id]
                assert shell.eligible
                assert shell.workspace_id == view.workspace_id
        for shell in self._shells.values():
            assert shell.identity.kind is IdentityKind.SHELL
            assert shell.workspace_id in self._workspaces
            assert shell.process_workspace_id in self._workspaces
            assert shell.kernel_generation_id.kind is IdentityKind.KERNEL_GENERATION
            assert shell.epoch > 0
        for workspace_id, shell_id in self._foreground_shells.items():
            shell = self._shells[shell_id]
            assert workspace_id in self._workspaces
            assert shell.workspace_id == workspace_id
        return True

    def _select_target(
        self,
        *,
        view_id: ApplicationIdentity | None,
        workspace_id: ApplicationIdentity | None,
        shell_id: ApplicationIdentity | None,
    ) -> (
        tuple[
            ApplicationIdentity,
            ViewRoutingState | None,
            ShellRoutingState,
            AssignmentMode,
        ]
        | ExecutionResolution
    ):
        view = None
        if view_id is not None:
            view = self._views.get(view_id)
            if view is None:
                return self._unresolved(RoutingStatus.INVALID, "unknown view")
            if workspace_id is not None and workspace_id != view.workspace_id:
                return self._unresolved(
                    RoutingStatus.INVALID, "view belongs to another workspace"
                )
            workspace_id = view.workspace_id
        if workspace_id is None or workspace_id not in self._workspaces:
            return self._unresolved(RoutingStatus.INVALID, "unknown workspace")

        if shell_id is not None:
            if view is not None:
                return self._unresolved(
                    RoutingStatus.INVALID,
                    "direct shell routing cannot override a view assignment",
                )
            assignment_mode = AssignmentMode.DIRECT
            target_id = shell_id
        elif view is not None and view.assignment.mode in (
            AssignmentMode.EXPLICIT,
            AssignmentMode.BROKEN,
        ):
            assignment_mode = view.assignment.mode
            target_id = view.assignment.shell_id
            if assignment_mode is AssignmentMode.BROKEN:
                return self._unresolved(
                    RoutingStatus.BROKEN_TARGET,
                    "the view's explicit shell assignment is broken",
                )
        else:
            assignment_mode = AssignmentMode.IMPLICIT
            target_id = self._foreground_shells.get(workspace_id)

        if target_id is None:
            return self._unresolved(
                RoutingStatus.NO_TARGET,
                "the invoking workspace has no foreground shell",
            )
        shell = self._shells.get(target_id)
        if (
            shell is None
            or not shell.eligible
            or shell.workspace_id != workspace_id
        ):
            status = (
                RoutingStatus.BROKEN_TARGET
                if assignment_mode is AssignmentMode.EXPLICIT
                else RoutingStatus.NO_TARGET
            )
            return self._unresolved(status, "the selected shell is unavailable")
        return workspace_id, view, shell, assignment_mode

    def _break_assignments_to_mismatched_shell(
        self, shell_id: ApplicationIdentity
    ) -> None:
        shell = self._shells[shell_id]
        for view_id, view in tuple(self._views.items()):
            if (
                view.assignment.mode is AssignmentMode.EXPLICIT
                and view.assignment.shell_id == shell_id
                and view.workspace_id != shell.workspace_id
            ):
                self._views[view_id] = replace(
                    view,
                    assignment=replace(
                        view.assignment, mode=AssignmentMode.BROKEN
                    ),
                )

    def _require_workspace(self, workspace_id: ApplicationIdentity) -> None:
        self._validate_identity(workspace_id, IdentityKind.WORKSPACE)
        if workspace_id not in self._workspaces:
            raise KeyError(f"unknown workspace: {workspace_id}")

    @staticmethod
    def _validate_identity(
        identity: ApplicationIdentity, kind: IdentityKind
    ) -> None:
        if not isinstance(identity, ApplicationIdentity) or identity.kind is not kind:
            raise ValueError(f"identity must have {kind.value} kind")

    @staticmethod
    def _applied() -> RoutingResult:
        return RoutingResult(RoutingStatus.APPLIED)

    @staticmethod
    def _invalid(detail: str) -> RoutingResult:
        return RoutingResult(RoutingStatus.INVALID, detail)

    @staticmethod
    def _unresolved(status: RoutingStatus, detail: str) -> ExecutionResolution:
        return ExecutionResolution(status, detail)
