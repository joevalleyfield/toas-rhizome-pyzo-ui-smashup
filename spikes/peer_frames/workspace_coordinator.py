"""Application coordinator for explicit concurrent workspace ownership."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Mapping

from .contract import (
    ActiveContext,
    Capability,
    OperationResult,
    OperationStatus,
    PaneClosePolicy,
    PaneDescriptor,
    PaneKind,
    WorkspaceModel,
)
from .identity import ApplicationIdentity, IdentityKind, new_identity


@dataclass(frozen=True)
class WorkspaceDescriptor:
    identity: ApplicationIdentity
    name: str
    persistence_location: str | None = None


@dataclass
class WorkspaceRuntime:
    descriptor: WorkspaceDescriptor
    model: WorkspaceModel
    state: dict[str, object]


class WorkspaceCoordinator:
    """Own several topology roots and their process-wide pane relations."""

    def __init__(self) -> None:
        self._workspaces: dict[ApplicationIdentity, WorkspaceRuntime] = {}
        self._retired: set[ApplicationIdentity] = set()
        self._active_workspace_id: ApplicationIdentity | None = None
        self._ownership_epochs: dict[str, int] = {}

    @property
    def workspace_ids(self) -> tuple[ApplicationIdentity, ...]:
        return tuple(self._workspaces)

    @property
    def active_workspace_id(self) -> ApplicationIdentity | None:
        return self._active_workspace_id

    def add_workspace(
        self,
        model: WorkspaceModel,
        *,
        name: str,
        identity: ApplicationIdentity | None = None,
        persistence_location: str | None = None,
        state: Mapping[str, object] | None = None,
    ) -> ApplicationIdentity:
        identity = identity or new_identity(IdentityKind.WORKSPACE)
        self._validate_workspace_identity(identity)
        self._validate_name(name)
        if identity in self._workspaces or identity in self._retired:
            raise ValueError(f"workspace identity is already known: {identity}")
        if model.workspace_id is not None and model.workspace_id != identity:
            raise ValueError("workspace model is already bound to another identity")
        for pane_id in model.panes:
            if self.pane_owner(pane_id) is not None:
                raise ValueError(f"pane already belongs to a workspace: {pane_id}")

        model.bind_workspace(identity)
        descriptor = WorkspaceDescriptor(identity, name, persistence_location)
        self._workspaces[identity] = WorkspaceRuntime(
            descriptor,
            model,
            deepcopy(dict(state or {})),
        )
        for pane_id in model.panes:
            self._ownership_epochs.setdefault(pane_id, 1)
        if self._active_workspace_id is None:
            self._active_workspace_id = identity
        self.assert_invariants()
        return identity

    def remove_workspace(self, workspace_id: ApplicationIdentity) -> OperationResult:
        runtime = self._workspaces.get(workspace_id)
        if runtime is None:
            return self._invalid(f"unknown workspace: {workspace_id}")
        if runtime.model.panes:
            return self._invalid("workspace must be empty before it is removed")
        del self._workspaces[workspace_id]
        self._retired.add(workspace_id)
        if self._active_workspace_id == workspace_id:
            self._active_workspace_id = None
        self.assert_invariants()
        return self._applied()

    def descriptor(self, workspace_id: ApplicationIdentity) -> WorkspaceDescriptor:
        return self._runtime(workspace_id).descriptor

    def model(self, workspace_id: ApplicationIdentity) -> WorkspaceModel:
        return self._runtime(workspace_id).model

    def state(self, workspace_id: ApplicationIdentity) -> dict[str, object]:
        return self._runtime(workspace_id).state

    def rename_workspace(
        self, workspace_id: ApplicationIdentity, name: str
    ) -> WorkspaceDescriptor:
        self._validate_name(name)
        runtime = self._runtime(workspace_id)
        runtime.descriptor = replace(runtime.descriptor, name=name)
        return runtime.descriptor

    def relocate_workspace(
        self,
        workspace_id: ApplicationIdentity,
        persistence_location: str | None,
    ) -> WorkspaceDescriptor:
        runtime = self._runtime(workspace_id)
        runtime.descriptor = replace(
            runtime.descriptor,
            persistence_location=persistence_location,
        )
        return runtime.descriptor

    def copy_workspace(
        self,
        source_id: ApplicationIdentity,
        model: WorkspaceModel,
        *,
        name: str | None = None,
        persistence_location: str | None = None,
    ) -> ApplicationIdentity:
        source = self._runtime(source_id)
        return self.add_workspace(
            model,
            name=name or f"{source.descriptor.name} copy",
            persistence_location=persistence_location,
            state=source.state,
        )

    def register_pane(
        self,
        workspace_id: ApplicationIdentity,
        pane: PaneDescriptor,
        close_policy: PaneClosePolicy | None = None,
    ) -> OperationResult:
        if workspace_id not in self._workspaces:
            return self._invalid(f"unknown workspace: {workspace_id}")
        if self.pane_owner(pane.id) is not None:
            return self._invalid(f"pane already belongs to a workspace: {pane.id}")
        result = self.model(workspace_id).register_pane(pane, close_policy)
        if result.applied:
            self._ownership_epochs[pane.id] = self._next_epoch(pane.id)
            self.assert_invariants()
        return result

    def transfer_pane(
        self,
        pane_id: str,
        target_workspace_id: ApplicationIdentity,
    ) -> OperationResult:
        source_id = self.pane_owner(pane_id)
        if source_id is None:
            return self._invalid(f"pane has no workspace owner: {pane_id}")
        if target_workspace_id not in self._workspaces:
            return self._invalid(f"unknown workspace: {target_workspace_id}")
        if source_id == target_workspace_id:
            return self._invalid("pane already belongs to the target workspace")

        source = self.model(source_id)
        target = self.model(target_workspace_id)
        if pane_id in target.panes:
            return self._invalid(f"target already contains pane: {pane_id}")
        pane = source.panes[pane_id]
        if pane.kind is PaneKind.SHELL:
            return OperationResult(
                OperationStatus.UNSUPPORTED,
                "cross-workspace shell transfer is not supported",
            )
        if (
            Capability.SAVE_RESTORE not in source.backend.capabilities
            or Capability.SAVE_RESTORE not in target.backend.capabilities
        ):
            return OperationResult(
                OperationStatus.UNSUPPORTED,
                "transactional pane transfer requires save/restore capability",
            )

        source_layout = deepcopy(source.serialize_layout())
        target_layout = deepcopy(target.serialize_layout())
        try:
            transfer = source.release_pane(pane_id)
            result = target.accept_pane(transfer)
        except Exception as error:
            return self._rollback_transfer(
                source,
                target,
                source_layout,
                target_layout,
                locals().get("transfer"),
                f"pane transfer failed: {error}",
            )
        if not result.applied:
            return self._rollback_transfer(
                source,
                target,
                source_layout,
                target_layout,
                transfer,
                result.detail or "target rejected pane transfer",
            )

        self._ownership_epochs[pane_id] = self._next_epoch(pane_id)
        self.assert_invariants()
        return self._applied()

    def activate_workspace(self, workspace_id: ApplicationIdentity) -> OperationResult:
        if workspace_id not in self._workspaces:
            return self._invalid(f"unknown workspace: {workspace_id}")
        self._active_workspace_id = workspace_id
        return self._applied()

    def activate_pane(
        self, workspace_id: ApplicationIdentity, pane_id: str
    ) -> OperationResult:
        if self.pane_owner(pane_id) != workspace_id:
            return self._invalid("pane does not belong to the requested workspace")
        result = self.model(workspace_id).activate(pane_id)
        if result.applied:
            self._active_workspace_id = workspace_id
        return result

    def adopt_backend_activation(
        self, workspace_id: ApplicationIdentity, pane_id: str
    ) -> OperationResult:
        if self.pane_owner(pane_id) != workspace_id:
            return self._invalid("pane does not belong to the requested workspace")
        result = self.model(workspace_id).adopt_backend_activation(pane_id)
        if result.applied:
            self._active_workspace_id = workspace_id
        return result

    def resolve_active_context(self) -> ActiveContext:
        workspace_id = self._active_workspace_id
        if workspace_id is None:
            return ActiveContext()
        return self._capture(self.model(workspace_id).resolve_active_context())

    def resolve_workspace_context(
        self,
        workspace_id: ApplicationIdentity,
        pane_id: str | None = None,
    ) -> ActiveContext | None:
        runtime = self._workspaces.get(workspace_id)
        if runtime is None:
            return None
        if pane_id is None:
            return ActiveContext(workspace_id=workspace_id)
        if self.pane_owner(pane_id) != workspace_id:
            return None
        context = runtime.model.resolve_pane_context(pane_id)
        return self._capture(context) if context is not None else None

    def context_is_current(self, context: ActiveContext) -> bool:
        if context.workspace_id is None:
            return (
                context.pane is None
                and context.frame_id is None
                and context.group_id is None
                and context.ownership_epoch is None
            )
        runtime = self._workspaces.get(context.workspace_id)
        if runtime is None:
            return False
        if context.pane is None:
            return (
                context.frame_id is None
                and context.group_id is None
                and context.ownership_epoch is None
            )
        pane_id = context.pane.id
        if self.pane_owner(pane_id) != context.workspace_id:
            return False
        if context.ownership_epoch != self._ownership_epochs.get(pane_id):
            return False
        current = runtime.model.resolve_pane_context(pane_id)
        return (
            current is not None
            and current.frame_id == context.frame_id
            and current.group_id == context.group_id
        )

    def pane_owner(self, pane_id: str) -> ApplicationIdentity | None:
        owners = [
            workspace_id
            for workspace_id, runtime in self._workspaces.items()
            if pane_id in runtime.model.panes
        ]
        if len(owners) > 1:
            raise RuntimeError(f"pane belongs to several workspaces: {pane_id}")
        return owners[0] if owners else None

    def assert_invariants(self) -> bool:
        seen: dict[str, ApplicationIdentity] = {}
        for workspace_id, runtime in self._workspaces.items():
            assert runtime.descriptor.identity == workspace_id
            assert runtime.model.workspace_id == workspace_id
            for pane_id in runtime.model.panes:
                assert pane_id not in seen, (
                    f"pane {pane_id} belongs to both {seen[pane_id]} and "
                    f"{workspace_id}"
                )
                seen[pane_id] = workspace_id
        assert self._active_workspace_id is None or (
            self._active_workspace_id in self._workspaces
        )
        return True

    def _capture(self, context: ActiveContext) -> ActiveContext:
        if context.pane is None:
            return context
        pane_id = context.pane.id
        self._ownership_epochs.setdefault(pane_id, 1)
        return replace(
            context,
            ownership_epoch=self._ownership_epochs[pane_id],
        )

    def _rollback_transfer(
        self,
        source: WorkspaceModel,
        target: WorkspaceModel,
        source_layout: Mapping[str, object],
        target_layout: Mapping[str, object],
        transfer,
        detail: str,
    ) -> OperationResult:
        if transfer is not None and transfer.pane.id in target.panes:
            transfer = target.release_pane(transfer.pane.id)
            layout_result = target.restore_layout(target_layout)
            if not layout_result.applied:
                raise RuntimeError("pane transfer rollback could not restore target")
        if transfer is not None and transfer.pane.id not in source.panes:
            restored = source.accept_pane(transfer)
            if not restored.applied:
                raise RuntimeError("pane transfer rollback could not restore ownership")
            layout_result = source.restore_layout(source_layout)
            if not layout_result.applied:
                raise RuntimeError("pane transfer rollback could not restore layout")
        self.assert_invariants()
        return self._invalid(detail)

    def _runtime(self, workspace_id: ApplicationIdentity) -> WorkspaceRuntime:
        try:
            return self._workspaces[workspace_id]
        except KeyError:
            raise KeyError(f"unknown workspace: {workspace_id}") from None

    def _next_epoch(self, pane_id: str) -> int:
        return self._ownership_epochs.get(pane_id, 0) + 1

    @staticmethod
    def _validate_workspace_identity(identity: ApplicationIdentity) -> None:
        if identity.kind is not IdentityKind.WORKSPACE:
            raise ValueError("workspace identity must have workspace kind")

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("workspace name must be a non-empty string")

    @staticmethod
    def _applied() -> OperationResult:
        return OperationResult(OperationStatus.APPLIED)

    @staticmethod
    def _invalid(detail: str) -> OperationResult:
        return OperationResult(OperationStatus.INVALID, detail)
