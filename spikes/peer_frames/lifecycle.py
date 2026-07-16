"""Application-owned document, editor-view, and shell lifecycle policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Protocol

from .contract import (
    CloseDecision,
    CloseRequest,
    CloseVote,
    PaneDescriptor,
)


class DocumentLifecycle(Protocol):
    def is_dirty(self) -> bool:
        """Return whether final-view closure requires dirty-document policy."""

    def save_document(self) -> bool:
        """Persist the document, returning true only when saving succeeded."""

    def close_document(self, disposition: DocumentCloseDisposition) -> None:
        """Release the document after its final view transaction commits."""


class DirtyCloseChoice(str, Enum):
    SAVE = "save"
    DISCARD = "discard"
    CANCEL = "cancel"


class DocumentCloseDisposition(str, Enum):
    CLEAN = "clean"
    SAVED = "saved"
    DISCARDED = "discarded"


class ShellState(str, Enum):
    DEAD = "dead"
    IDLE = "idle"
    RUNNING = "running"
    DEBUGGING = "debugging"
    STARTING_OR_UNKNOWN = "starting-or-unknown"


class ShellCloseChoice(str, Enum):
    TERMINATE = "terminate"
    CANCEL = "cancel"


class ShellCloseDisposition(str, Enum):
    DEAD = "dead"
    TERMINATED = "terminated"


class ShellLifecycle(Protocol):
    def shell_state(self) -> ShellState:
        """Return the current interpreter state for close validation."""

    def close_shell(self, disposition: ShellCloseDisposition) -> None:
        """Release the shell after its pane transaction commits."""


@dataclass
class _DocumentState:
    lifecycle: DocumentLifecycle
    view_ids: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class _ViewState:
    document_id: str
    is_pinned: Callable[[], bool]


class DocumentViewClosePolicy:
    """Vote and commit on behalf of one document view pane."""

    def __init__(self, registry: DocumentViewRegistry, pane_id: str):
        self._registry = registry
        self._pane_id = pane_id

    def prepare_close(
        self, pane: PaneDescriptor, request: CloseRequest
    ) -> CloseVote:
        return self._registry.prepare_close(self._pane_id, request)

    def validate_close(
        self, pane: PaneDescriptor, request: CloseRequest
    ) -> CloseVote:
        return self._registry.validate_close(self._pane_id, request)

    def did_close(self, pane: PaneDescriptor, request: CloseRequest) -> None:
        self._registry.did_close(self._pane_id)


class DocumentViewRegistry:
    """Own document/view membership independently from frame placement."""

    def __init__(self):
        self._documents: dict[str, _DocumentState] = {}
        self._views: dict[str, _ViewState] = {}
        self._resolving_documents: set[str] = set()
        self._pending_dispositions: dict[str, DocumentCloseDisposition] = {}

    @property
    def document_ids(self) -> frozenset[str]:
        return frozenset(self._documents)

    def view_ids(self, document_id: str) -> frozenset[str]:
        state = self._documents.get(document_id)
        return frozenset() if state is None else frozenset(state.view_ids)

    def document_id_for_view(self, pane_id: str) -> str | None:
        view = self._views.get(pane_id)
        return None if view is None else view.document_id

    def forget_view(self, pane_id: str) -> None:
        """Roll back a binding that never became an installed close policy."""

        view = self._views.pop(pane_id, None)
        if view is None:
            return
        document = self._documents[view.document_id]
        document.view_ids.discard(pane_id)
        if not document.view_ids:
            del self._documents[view.document_id]
            self._pending_dispositions.pop(view.document_id, None)

    def register_view(
        self,
        pane_id: str,
        document_id: str,
        lifecycle: DocumentLifecycle,
        *,
        is_pinned: Callable[[], bool] | None = None,
    ) -> DocumentViewClosePolicy:
        if pane_id in self._views:
            raise ValueError(f"view already registered: {pane_id}")
        state = self._documents.get(document_id)
        if state is None:
            state = _DocumentState(lifecycle)
            self._documents[document_id] = state
        elif state.lifecycle is not lifecycle:
            raise ValueError(f"document lifecycle does not match: {document_id}")
        state.view_ids.add(pane_id)
        self._views[pane_id] = _ViewState(document_id, is_pinned or (lambda: False))
        return DocumentViewClosePolicy(self, pane_id)

    def prepare_close(self, pane_id: str, request: CloseRequest) -> CloseVote:
        view = self._views.get(pane_id)
        if view is None:
            return CloseVote(
                pane_id, CloseDecision.REFUSE, "document view is not registered"
            )
        if view.is_pinned():
            return CloseVote(
                pane_id,
                CloseDecision.REFUSE,
                "pinned editor negotiation is not installed yet",
            )
        document = self._documents[view.document_id]
        if view.document_id in self._resolving_documents:
            return CloseVote(
                pane_id,
                CloseDecision.REFUSE,
                "document close negotiation is already in progress",
            )
        surviving_views = document.view_ids.difference(request.pane_ids)
        if not surviving_views and document.lifecycle.is_dirty():
            closing_views = [
                candidate
                for candidate in request.pane_ids
                if candidate in document.view_ids
            ]
            if closing_views and closing_views[0] != pane_id:
                return CloseVote(pane_id, CloseDecision.ALLOW)
            return CloseVote(
                pane_id,
                CloseDecision.CONFIRM,
                "dirty document requires save, discard, or cancel",
            )
        return CloseVote(pane_id, CloseDecision.ALLOW)

    def validate_close(self, pane_id: str, request: CloseRequest) -> CloseVote:
        view = self._views.get(pane_id)
        if view is None:
            return CloseVote(
                pane_id, CloseDecision.REFUSE, "document view is not registered"
            )
        if view.is_pinned():
            return CloseVote(pane_id, CloseDecision.REFUSE, "editor view is pinned")
        document = self._documents[view.document_id]
        surviving_views = document.view_ids.difference(request.pane_ids)
        if surviving_views or not document.lifecycle.is_dirty():
            return CloseVote(pane_id, CloseDecision.ALLOW)
        if (
            self._pending_dispositions.get(view.document_id)
            is DocumentCloseDisposition.DISCARDED
        ):
            return CloseVote(pane_id, CloseDecision.ALLOW)
        return CloseVote(
            pane_id,
            CloseDecision.REFUSE,
            "dirty document close was not resolved",
        )

    def resolve_confirmations(
        self,
        votes: tuple[CloseVote, ...],
        choose: Callable[[str, DocumentLifecycle], DirtyCloseChoice | str],
    ) -> bool:
        document_ids: list[str] = []
        for vote in votes:
            view = self._views.get(vote.pane_id)
            if view is None:
                return False
            if view.document_id not in document_ids:
                document_ids.append(view.document_id)
        if not document_ids or self._resolving_documents.intersection(document_ids):
            return False

        self._resolving_documents.update(document_ids)
        accepted = False
        try:
            choices: list[tuple[str, DirtyCloseChoice]] = []
            for document_id in document_ids:
                document = self._documents.get(document_id)
                if document is None:
                    return False
                try:
                    choice = DirtyCloseChoice(choose(document_id, document.lifecycle))
                except (TypeError, ValueError):
                    return False
                choices.append((document_id, choice))
            if any(choice is DirtyCloseChoice.CANCEL for _, choice in choices):
                return False

            dispositions: dict[str, DocumentCloseDisposition] = {}
            for document_id, choice in choices:
                document = self._documents.get(document_id)
                if document is None:
                    return False
                if not document.lifecycle.is_dirty():
                    dispositions[document_id] = DocumentCloseDisposition.CLEAN
                elif choice is DirtyCloseChoice.DISCARD:
                    dispositions[document_id] = DocumentCloseDisposition.DISCARDED
                else:
                    try:
                        saved = document.lifecycle.save_document()
                    except Exception:
                        saved = False
                    if not saved or document.lifecycle.is_dirty():
                        return False
                    dispositions[document_id] = DocumentCloseDisposition.SAVED

            self._pending_dispositions.update(dispositions)
            accepted = True
            return True
        finally:
            self._resolving_documents.difference_update(document_ids)
            if not accepted:
                for document_id in document_ids:
                    self._pending_dispositions.pop(document_id, None)

    def did_close(self, pane_id: str) -> None:
        view = self._views.pop(pane_id, None)
        if view is None:
            return
        document = self._documents[view.document_id]
        document.view_ids.discard(pane_id)
        if document.view_ids:
            return
        del self._documents[view.document_id]
        disposition = self._pending_dispositions.pop(
            view.document_id, DocumentCloseDisposition.CLEAN
        )
        document.lifecycle.close_document(disposition)


@dataclass
class _ShellState:
    lifecycle: ShellLifecycle
    resolving: bool = False
    pending_disposition: ShellCloseDisposition | None = None


class ShellClosePolicy:
    """Require an explicit terminate decision for every live shell."""

    def __init__(self, registry: ShellLifecycleRegistry, pane_id: str):
        self._registry = registry
        self._pane_id = pane_id

    def prepare_close(
        self, pane: PaneDescriptor, request: CloseRequest
    ) -> CloseVote:
        return self._registry.prepare_close(self._pane_id)

    def validate_close(
        self, pane: PaneDescriptor, request: CloseRequest
    ) -> CloseVote:
        return self._registry.validate_close(self._pane_id)

    def did_close(self, pane: PaneDescriptor, request: CloseRequest) -> None:
        self._registry.did_close(self._pane_id)


class ShellLifecycleRegistry:
    """Own shell identity and termination approval outside frame placement."""

    def __init__(self):
        self._shells: dict[str, _ShellState] = {}

    @property
    def pane_ids(self) -> frozenset[str]:
        return frozenset(self._shells)

    def register_shell(
        self, pane_id: str, lifecycle: ShellLifecycle
    ) -> ShellClosePolicy:
        if pane_id in self._shells:
            raise ValueError(f"shell already registered: {pane_id}")
        self._shells[pane_id] = _ShellState(lifecycle)
        return ShellClosePolicy(self, pane_id)

    def forget_shell(self, pane_id: str) -> None:
        """Roll back a shell binding that was never installed."""

        self._shells.pop(pane_id, None)

    def cancel_pending(self, pane_ids: tuple[str, ...]) -> None:
        """Clear uncommitted termination authority after a wider veto."""

        for pane_id in pane_ids:
            shell = self._shells.get(pane_id)
            if shell is not None:
                shell.pending_disposition = None

    def prepare_close(self, pane_id: str) -> CloseVote:
        shell = self._shells.get(pane_id)
        if shell is None:
            return CloseVote(pane_id, CloseDecision.REFUSE, "shell is not registered")
        if shell.resolving:
            return CloseVote(
                pane_id,
                CloseDecision.REFUSE,
                "shell close negotiation is already in progress",
            )
        if shell.lifecycle.shell_state() is ShellState.DEAD:
            return CloseVote(pane_id, CloseDecision.ALLOW)
        return CloseVote(
            pane_id,
            CloseDecision.CONFIRM,
            "live shell requires terminate-and-close confirmation",
        )

    def validate_close(self, pane_id: str) -> CloseVote:
        shell = self._shells.get(pane_id)
        if shell is None:
            return CloseVote(pane_id, CloseDecision.REFUSE, "shell is not registered")
        if shell.lifecycle.shell_state() is ShellState.DEAD:
            return CloseVote(pane_id, CloseDecision.ALLOW)
        if shell.pending_disposition is ShellCloseDisposition.TERMINATED:
            return CloseVote(pane_id, CloseDecision.ALLOW)
        return CloseVote(
            pane_id,
            CloseDecision.REFUSE,
            "live shell termination was not approved",
        )

    def resolve_confirmations(
        self,
        votes: tuple[CloseVote, ...],
        choose: Callable[[str, ShellLifecycle], ShellCloseChoice | str],
    ) -> bool:
        pane_ids: list[str] = []
        for vote in votes:
            if vote.pane_id not in self._shells:
                return False
            if vote.pane_id not in pane_ids:
                pane_ids.append(vote.pane_id)
        if not pane_ids or any(
            self._shells[pane_id].resolving for pane_id in pane_ids
        ):
            return False

        for pane_id in pane_ids:
            self._shells[pane_id].resolving = True
        accepted = False
        try:
            choices: list[tuple[str, ShellCloseChoice]] = []
            for pane_id in pane_ids:
                shell = self._shells.get(pane_id)
                if shell is None:
                    return False
                try:
                    choice = ShellCloseChoice(choose(pane_id, shell.lifecycle))
                except (TypeError, ValueError):
                    return False
                choices.append((pane_id, choice))
            if any(choice is ShellCloseChoice.CANCEL for _, choice in choices):
                return False

            for pane_id, _choice in choices:
                shell = self._shells.get(pane_id)
                if shell is None:
                    return False
                shell.pending_disposition = ShellCloseDisposition.TERMINATED
            accepted = True
            return True
        finally:
            for pane_id in pane_ids:
                shell = self._shells.get(pane_id)
                if shell is not None:
                    shell.resolving = False
                    if not accepted:
                        shell.pending_disposition = None

    def did_close(self, pane_id: str) -> None:
        shell = self._shells.pop(pane_id, None)
        if shell is None:
            return
        disposition = (
            ShellCloseDisposition.DEAD
            if shell.lifecycle.shell_state() is ShellState.DEAD
            else shell.pending_disposition or ShellCloseDisposition.DEAD
        )
        shell.lifecycle.close_shell(disposition)
