"""Transactional ordinary workspace unload/reload over durable generations."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Mapping

from .workspace_persistence import (
    WorkspacePersistenceLoad,
    WorkspacePersistenceState,
    WorkspacePersistenceStore,
)


@dataclass(frozen=True)
class WorkspaceLifecycleResult:
    applied: bool
    detail: str = ""


class WorkspaceLifecycleCancelled(RuntimeError):
    """The user cancelled recovery or close negotiation."""


class WorkspaceLifecycleCoordinator:
    """Compose topology detach/restore with one durable loaded-set commit."""

    def __init__(
        self,
        store: WorkspacePersistenceStore,
        loaded: WorkspacePersistenceLoad,
        runtimes: Mapping[str, object],
        *,
        capture_workspace: Callable[[str, object], Mapping[str, object]],
        capture_recovery: Callable[[str, object], Mapping[str, object]],
        detach_workspace: Callable[
            [str, object, frozenset[str]], object
        ],
        restore_detached: Callable[[str, object, object], None],
        construct_workspace: Callable[
            [str, Mapping[str, object], Mapping[str, object]], object
        ],
        dispose_constructed: Callable[[str, object], None],
        capture_token: Callable[[str, object], object] | None = None,
    ) -> None:
        self.store = store
        self.state = loaded.state.detached_copy()
        self.unavailable_workspace_ids = set(loaded.unavailable_workspace_ids)
        self.runtimes = dict(runtimes)
        self._capture_workspace = capture_workspace
        self._capture_recovery = capture_recovery
        self._detach_workspace = detach_workspace
        self._restore_detached = restore_detached
        self._construct_workspace = construct_workspace
        self._dispose_constructed = dispose_constructed
        self._capture_token = capture_token or (
            lambda _workspace_id, _runtime: None
        )
        self._assert_invariants()

    @property
    def loaded_workspace_ids(self) -> tuple[str, ...]:
        return self.state.loaded_workspace_ids

    def unload(self, workspace_id: str) -> WorkspaceLifecycleResult:
        return self.unload_many((workspace_id,))

    def unload_many(
        self, workspace_ids: tuple[str, ...]
    ) -> WorkspaceLifecycleResult:
        if len(workspace_ids) != len(set(workspace_ids)):
            return WorkspaceLifecycleResult(False, "duplicate workspace unload")
        if any(workspace_id not in self.runtimes for workspace_id in workspace_ids):
            return WorkspaceLifecycleResult(False, "workspace is not loaded")
        before = self.state.detached_copy()
        records = deepcopy(dict(before.workspaces))
        recovery = deepcopy(dict(before.recovery))
        targets = set(workspace_ids)
        try:
            for workspace_id in workspace_ids:
                runtime = self.runtimes[workspace_id]
                token_before = deepcopy(
                    self._capture_token(workspace_id, runtime)
                )
                record = deepcopy(
                    dict(self._capture_workspace(workspace_id, runtime))
                )
                record.setdefault("identity", workspace_id)
                records[workspace_id] = record
                captured = deepcopy(
                    dict(self._capture_recovery(workspace_id, runtime))
                )
                captured.setdefault("workspace_id", workspace_id)
                recovery[workspace_id] = captured
                token_after = deepcopy(
                    self._capture_token(workspace_id, runtime)
                )
                if token_after != token_before:
                    raise RuntimeError(
                        "workspace changed while persistence was captured"
                    )
        except WorkspaceLifecycleCancelled as error:
            return WorkspaceLifecycleResult(False, str(error) or "unload cancelled")
        except Exception as error:
            return WorkspaceLifecycleResult(
                False, f"workspace capture failed: {error}"
            )

        surviving = tuple(
            identity
            for identity in before.loaded_workspace_ids
            if identity not in targets
        )
        shared_by_target = {
            workspace_id: self._documents_shared_with_survivors(
                workspace_id, targets, before.shared_resources
            )
            for workspace_id in workspace_ids
        }
        detached: list[tuple[str, object, object]] = []
        try:
            for workspace_id in workspace_ids:
                runtime = self.runtimes[workspace_id]
                token = self._detach_workspace(
                    workspace_id, runtime, shared_by_target[workspace_id]
                )
                detached.append((workspace_id, runtime, token))
            next_state = WorkspacePersistenceState(
                surviving,
                (
                    before.active_workspace_id
                    if before.active_workspace_id in surviving
                    else (surviving[0] if surviving else None)
                ),
                records,
                before.shared_resources,
                recovery,
                before.application_state,
            )
            committed = self.store.commit(next_state)
        except Exception as error:
            rollback_errors = self._rollback_detached(detached)
            detail = f"workspace unload failed: {error}"
            if rollback_errors:
                detail += "; rollback failed: " + "; ".join(rollback_errors)
            return WorkspaceLifecycleResult(False, detail)

        for workspace_id in workspace_ids:
            del self.runtimes[workspace_id]
        self.state = committed.state.detached_copy()
        self.unavailable_workspace_ids = set(
            committed.unavailable_workspace_ids
        )
        self._assert_invariants()
        return WorkspaceLifecycleResult(True)

    def reload(self, workspace_id: str) -> WorkspaceLifecycleResult:
        if workspace_id in self.runtimes:
            return WorkspaceLifecycleResult(False, "workspace is already loaded")
        refreshed = self.store.load()
        if workspace_id in refreshed.unavailable_workspace_ids:
            self.unavailable_workspace_ids = set(
                refreshed.unavailable_workspace_ids
            )
            return WorkspaceLifecycleResult(False, "workspace record is unavailable")
        record = refreshed.state.workspaces.get(workspace_id)
        if record is None:
            return WorkspaceLifecycleResult(False, "unknown workspace")
        recovery = refreshed.state.recovery.get(
            workspace_id,
            {"workspace_id": workspace_id, "snapshots": []},
        )
        try:
            runtime = self._construct_workspace(workspace_id, record, recovery)
        except Exception as error:
            return WorkspaceLifecycleResult(
                False, f"workspace restore failed: {error}"
            )

        loaded_ids = tuple(
            (*refreshed.state.loaded_workspace_ids, workspace_id)
        )
        next_state = WorkspacePersistenceState(
            loaded_ids,
            workspace_id,
            refreshed.state.workspaces,
            refreshed.state.shared_resources,
            refreshed.state.recovery,
            refreshed.state.application_state,
        )
        try:
            committed = self.store.commit(next_state)
        except Exception as error:
            try:
                self._dispose_constructed(workspace_id, runtime)
            except Exception as rollback_error:
                return WorkspaceLifecycleResult(
                    False,
                    f"workspace reload commit failed: {error}; "
                    f"rollback failed: {rollback_error}",
                )
            return WorkspaceLifecycleResult(
                False, f"workspace reload commit failed: {error}"
            )

        self.runtimes[workspace_id] = runtime
        self.state = committed.state.detached_copy()
        self.unavailable_workspace_ids = set(
            committed.unavailable_workspace_ids
        )
        self._assert_invariants()
        return WorkspaceLifecycleResult(True)

    def refresh_unavailable(self) -> tuple[str, ...]:
        loaded = self.store.load()
        self.unavailable_workspace_ids = set(loaded.unavailable_workspace_ids)
        return tuple(loaded.unavailable_workspace_ids)

    def _rollback_detached(
        self, detached: list[tuple[str, object, object]]
    ) -> tuple[str, ...]:
        errors = []
        for workspace_id, runtime, token in reversed(detached):
            try:
                self._restore_detached(workspace_id, runtime, token)
            except Exception as error:
                errors.append(f"{workspace_id}: {error}")
        return tuple(errors)

    @staticmethod
    def _documents_shared_with_survivors(
        workspace_id: str,
        unloading: set[str],
        resources: Mapping[str, object],
    ) -> frozenset[str]:
        views = resources.get("views", {})
        if not isinstance(views, Mapping):
            return frozenset()
        owned = {
            view.get("document_id")
            for view in views.values()
            if isinstance(view, Mapping)
            and view.get("workspace_id") == workspace_id
            and isinstance(view.get("document_id"), str)
        }
        surviving = {
            view.get("document_id")
            for view in views.values()
            if isinstance(view, Mapping)
            and view.get("workspace_id") not in unloading
            and isinstance(view.get("document_id"), str)
        }
        return frozenset(owned.intersection(surviving))

    def _assert_invariants(self) -> None:
        assert set(self.state.loaded_workspace_ids) == set(self.runtimes)
        assert set(self.state.loaded_workspace_ids).issubset(
            self.state.workspaces
        )
        assert not set(self.runtimes).intersection(self.unavailable_workspace_ids)
