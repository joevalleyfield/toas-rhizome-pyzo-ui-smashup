"""Shared document resources with workspace-owned editor-view state."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from enum import Enum
from typing import Callable, Mapping

from .identity import ApplicationIdentity, IdentityKind, new_identity
from .lifecycle import DocumentCloseDisposition


class DocumentOperationStatus(str, Enum):
    APPLIED = "applied"
    INVALID = "invalid"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class DocumentOperationResult:
    status: DocumentOperationStatus
    detail: str = ""
    document_id: ApplicationIdentity | None = None
    view_id: ApplicationIdentity | None = None

    @property
    def applied(self) -> bool:
        return self.status is DocumentOperationStatus.APPLIED


@dataclass
class DocumentViewState:
    cursor: int = 0
    selection: tuple[int, int] = (0, 0)
    scroll: int = 0
    focused: bool = False
    presentation: dict[str, object] = field(default_factory=dict)
    pinned: bool = False
    run_highlight: tuple[int, int] | None = None
    affiliation: str | None = None


@dataclass(frozen=True)
class CacheToken:
    document_id: ApplicationIdentity
    revision: int
    view_id: ApplicationIdentity | None = None
    view_epoch: int | None = None


@dataclass
class _ViewRecord:
    identity: ApplicationIdentity
    document_id: ApplicationIdentity
    workspace_id: ApplicationIdentity
    state: DocumentViewState
    epoch: int = 1
    notify: Callable[[ApplicationIdentity, str, int], None] | None = None


@dataclass(frozen=True)
class MainReference:
    workspace_id: ApplicationIdentity
    document_id: ApplicationIdentity
    path: str | None
    available: bool


@dataclass(frozen=True)
class RetainedViewDescriptor:
    """Identity and view projection kept after a view is closed."""

    view_id: ApplicationIdentity
    document_id: ApplicationIdentity
    workspace_id: ApplicationIdentity
    state: DocumentViewState
    epoch: int
    suspended: bool = False


class DocumentResource:
    """One live content/undo resource shared by any number of views."""

    def __init__(
        self,
        identity: ApplicationIdentity,
        text: str,
        *,
        path: str | None = None,
        dirty: bool = False,
    ) -> None:
        if identity.kind is not IdentityKind.DOCUMENT:
            raise ValueError("document resource requires document identity")
        self.identity = identity
        self.path = path
        self.text = text
        self.revision = 1
        self.live = True
        self.available = True
        self._clean_text: str | None = None if dirty else text
        self._undo: list[str] = []
        self._redo: list[str] = []
        self._mutating = False
        self.save_count = 0
        self.close_count = 0
        self.close_dispositions: list[DocumentCloseDisposition] = []
        self._save: Callable[[str, str], bool] | None = None

    @property
    def undo_depth(self) -> int:
        return len(self._undo)

    @property
    def redo_depth(self) -> int:
        return len(self._redo)

    def is_dirty(self) -> bool:
        return self._clean_text is None or self.text != self._clean_text

    def set_save_handler(self, save: Callable[[str, str], bool] | None) -> None:
        self._save = save

    def save_document(self) -> bool:
        if not self.path or self._save is None:
            return False
        self.save_count += 1
        try:
            saved = bool(self._save(self.path, self.text))
        except Exception:
            return False
        if saved:
            self._clean_text = self.text
            self.revision += 1
        return saved

    def close_document(self, disposition: DocumentCloseDisposition) -> None:
        self.close_count += 1
        self.close_dispositions.append(disposition)
        self.live = False
        self.revision += 1


class DocumentResourceRegistry:
    """Own durable document identity and workspace-local view projections."""

    def __init__(self) -> None:
        self._documents: dict[ApplicationIdentity, DocumentResource] = {}
        self._views: dict[ApplicationIdentity, _ViewRecord] = {}
        self._retained_views: dict[ApplicationIdentity, RetainedViewDescriptor] = {}
        self._paths: dict[str, ApplicationIdentity] = {}
        self._mains: dict[ApplicationIdentity, ApplicationIdentity] = {}
        self._persistence_extensions: dict[str, object] = {}

    @property
    def document_ids(self) -> tuple[ApplicationIdentity, ...]:
        return tuple(self._documents)

    @property
    def view_ids(self) -> tuple[ApplicationIdentity, ...]:
        return tuple(self._views)

    @property
    def retained_view_ids(self) -> tuple[ApplicationIdentity, ...]:
        return tuple(self._retained_views)

    def retained_views_for_document(
        self, document_id: ApplicationIdentity
    ) -> tuple[RetainedViewDescriptor, ...]:
        return tuple(
            descriptor
            for descriptor in self._retained_views.values()
            if descriptor.document_id == document_id
        )

    def retained_view(self, view_id: ApplicationIdentity) -> RetainedViewDescriptor:
        try:
            return self._retained_views[view_id]
        except KeyError:
            raise KeyError(f"unknown retained view: {view_id}") from None

    def create_document(
        self,
        text: str = "",
        *,
        path: str | None = None,
        dirty: bool = False,
        identity: ApplicationIdentity | None = None,
        save: Callable[[str, str], bool] | None = None,
    ) -> ApplicationIdentity:
        identity = identity or new_identity(IdentityKind.DOCUMENT)
        self._validate_identity(identity, IdentityKind.DOCUMENT)
        if identity in self._documents:
            raise ValueError(f"document identity is already registered: {identity}")
        if path is not None and path in self._paths:
            raise ValueError(f"document path is already registered: {path}")
        resource = DocumentResource(identity, text, path=path, dirty=dirty)
        resource.set_save_handler(save)
        self._documents[identity] = resource
        if path is not None:
            self._paths[path] = identity
        self.assert_invariants()
        return identity

    def resource(self, document_id: ApplicationIdentity) -> DocumentResource:
        try:
            return self._documents[document_id]
        except KeyError:
            raise KeyError(f"unknown document: {document_id}") from None

    def forget_document(self, document_id: ApplicationIdentity) -> bool:
        if (
            self.views_for_document(document_id)
            or self.retained_views_for_document(document_id)
            or document_id in self._mains.values()
        ):
            return False
        resource = self._documents.pop(document_id, None)
        if resource is None:
            return False
        if resource.path is not None:
            self._paths.pop(resource.path, None)
        self.assert_invariants()
        return True

    def open_view(
        self,
        document_id: ApplicationIdentity,
        workspace_id: ApplicationIdentity,
        *,
        identity: ApplicationIdentity | None = None,
        state: DocumentViewState | None = None,
        notify: Callable[[ApplicationIdentity, str, int], None] | None = None,
    ) -> ApplicationIdentity:
        resource = self.resource(document_id)
        self._validate_identity(workspace_id, IdentityKind.WORKSPACE)
        identity = identity or new_identity(IdentityKind.VIEW)
        self._validate_identity(identity, IdentityKind.VIEW)
        if identity in self._views:
            raise ValueError(f"view identity is already registered: {identity}")
        if identity in self._retained_views:
            raise ValueError(f"view identity is retained: {identity}")
        resource.live = True
        self._views[identity] = _ViewRecord(
            identity,
            document_id,
            workspace_id,
            deepcopy(state or DocumentViewState()),
            notify=notify,
        )
        self._retained_views.pop(identity, None)
        self.assert_invariants()
        return identity

    def view(self, view_id: ApplicationIdentity) -> _ViewRecord:
        try:
            return self._views[view_id]
        except KeyError:
            raise KeyError(f"unknown view: {view_id}") from None

    def views_for_document(
        self, document_id: ApplicationIdentity
    ) -> tuple[ApplicationIdentity, ...]:
        return tuple(
            view_id
            for view_id, view in self._views.items()
            if view.document_id == document_id
        )

    def update_view_state(
        self, view_id: ApplicationIdentity, **changes: object
    ) -> DocumentViewState:
        view = self.view(view_id)
        unknown = set(changes).difference(DocumentViewState.__dataclass_fields__)
        if unknown:
            raise ValueError(f"unknown view-state fields: {sorted(unknown)}")
        for name, value in changes.items():
            setattr(view.state, name, deepcopy(value))
        return view.state

    def replace_text(self, view_id: ApplicationIdentity, text: str) -> int:
        view = self.view(view_id)
        resource = self.resource(view.document_id)
        if not resource.live:
            raise RuntimeError("document resource is closed")
        if resource._mutating:
            raise RuntimeError("recursive document mutation")
        if text == resource.text:
            return resource.revision
        resource._mutating = True
        try:
            resource._undo.append(resource.text)
            resource._redo.clear()
            resource.text = text
            resource.revision += 1
            self._notify(resource, view_id)
            return resource.revision
        finally:
            resource._mutating = False

    def undo(self, view_id: ApplicationIdentity) -> bool:
        view = self.view(view_id)
        resource = self.resource(view.document_id)
        if resource._mutating or not resource._undo:
            return False
        resource._mutating = True
        try:
            resource._redo.append(resource.text)
            resource.text = resource._undo.pop()
            resource.revision += 1
            self._notify(resource, view_id)
            return True
        finally:
            resource._mutating = False

    def redo(self, view_id: ApplicationIdentity) -> bool:
        view = self.view(view_id)
        resource = self.resource(view.document_id)
        if resource._mutating or not resource._redo:
            return False
        resource._mutating = True
        try:
            resource._undo.append(resource.text)
            resource.text = resource._redo.pop()
            resource.revision += 1
            self._notify(resource, view_id)
            return True
        finally:
            resource._mutating = False

    def move_view(
        self, view_id: ApplicationIdentity, workspace_id: ApplicationIdentity
    ) -> DocumentOperationResult:
        self._validate_identity(workspace_id, IdentityKind.WORKSPACE)
        view = self.view(view_id)
        if view.workspace_id == workspace_id:
            return self._invalid("view already belongs to the target workspace")
        view.workspace_id = workspace_id
        view.epoch += 1
        self.assert_invariants()
        return self._applied(view_id=view_id, document_id=view.document_id)

    def close_view(self, view_id: ApplicationIdentity) -> bool:
        view = self._views.pop(view_id, None)
        if view is None:
            return False
        resource = self.resource(view.document_id)
        self._retained_views[view_id] = RetainedViewDescriptor(
            view.identity,
            view.document_id,
            view.workspace_id,
            deepcopy(view.state),
            view.epoch + 1,
        )
        if not self.views_for_document(view.document_id):
            resource.live = False
            resource.revision += 1
        self.assert_invariants()
        return True

    def reopen_view(
        self,
        document_id: ApplicationIdentity,
        *,
        view_id: ApplicationIdentity | None = None,
        workspace_id: ApplicationIdentity | None = None,
        notify: Callable[[ApplicationIdentity, str, int], None] | None = None,
    ) -> ApplicationIdentity:
        """Reopen a retained view by document identity, without path guessing."""

        candidates = self.retained_views_for_document(document_id)
        if view_id is not None:
            descriptor = self.retained_view(view_id)
            if descriptor.document_id != document_id:
                raise ValueError("retained view does not belong to document")
        elif len(candidates) == 1:
            descriptor = candidates[0]
            view_id = descriptor.view_id
        elif not candidates:
            raise KeyError(f"no retained view for document: {document_id}")
        else:
            raise ValueError("multiple retained views require an explicit view identity")

        target_workspace = workspace_id or descriptor.workspace_id
        self._retained_views.pop(descriptor.view_id)
        try:
            reopened = self.open_view(
                document_id,
                target_workspace,
                identity=view_id,
                state=descriptor.state,
                notify=notify,
            )
            # The retained descriptor's epoch was advanced when it closed.
            # Restore that epoch so an older token can never become current.
            self._views[reopened].epoch = descriptor.epoch
        except Exception:
            self._retained_views[descriptor.view_id] = descriptor
            raise
        self.assert_invariants()
        return reopened

    def rename_document(
        self, document_id: ApplicationIdentity, path: str
    ) -> DocumentOperationResult:
        if not isinstance(path, str) or not path:
            return self._invalid("document path must be non-empty")
        resource = self.resource(document_id)
        owner = self._paths.get(path)
        if owner is not None and owner != document_id:
            return self._invalid("path belongs to another document identity")
        old_path = resource.path
        if old_path == path:
            return self._applied(document_id=document_id)
        if old_path is not None:
            self._paths.pop(old_path, None)
        resource.path = path
        resource.available = True
        resource.revision += 1
        self._paths[path] = document_id
        self.assert_invariants()
        return self._applied(document_id=document_id)

    def save_as(
        self,
        document_id: ApplicationIdentity,
        path: str | None,
        save: Callable[[str, str], bool],
    ) -> DocumentOperationResult:
        if not path:
            return DocumentOperationResult(DocumentOperationStatus.CANCELLED)
        resource = self.resource(document_id)
        owner = self._paths.get(path)
        if owner is not None and owner != document_id:
            return self._invalid("path belongs to another document identity")
        try:
            saved = bool(save(path, resource.text))
        except Exception as error:
            return self._invalid(f"save failed: {error}")
        if not saved:
            return self._invalid("save failed")
        old_path = resource.path
        if old_path is not None and old_path != path:
            self._paths.pop(old_path, None)
        resource.path = path
        resource.available = True
        resource._clean_text = resource.text
        resource._save = save
        resource.save_count += 1
        resource.revision += 1
        self._paths[path] = document_id
        self.assert_invariants()
        return self._applied(document_id=document_id)

    def can_assign_path(
        self, document_id: ApplicationIdentity, path: str | None
    ) -> bool:
        if not path or document_id not in self._documents:
            return False
        owner = self._paths.get(path)
        return owner is None or owner == document_id

    def adopt_saved(
        self,
        document_id: ApplicationIdentity,
        path: str,
        text: str,
    ) -> DocumentOperationResult:
        """Adopt a successful foreground Pyzo save without writing again."""

        if not self.can_assign_path(document_id, path):
            return self._invalid("path belongs to another document identity")
        resource = self.resource(document_id)
        old_path = resource.path
        if old_path is not None and old_path != path:
            self._paths.pop(old_path, None)
        resource.path = path
        resource.text = text
        resource._clean_text = text
        resource.available = True
        resource.revision += 1
        self._paths[path] = document_id
        self.assert_invariants()
        return self._applied(document_id=document_id)

    def branch_view(
        self,
        source_view_id: ApplicationIdentity,
        *,
        branch_view_id: ApplicationIdentity | None = None,
        path: str | None = None,
    ) -> DocumentOperationResult:
        source_view = self.view(source_view_id)
        source = self.resource(source_view.document_id)
        if path is not None and path in self._paths:
            return self._invalid("path belongs to another document identity")
        document_id = self.create_document(source.text, path=path, dirty=True)
        try:
            view_id = self.open_view(
                document_id,
                source_view.workspace_id,
                identity=branch_view_id,
                state=source_view.state,
            )
        except Exception:
            resource = self._documents.pop(document_id)
            if resource.path is not None:
                self._paths.pop(resource.path, None)
            raise
        return self._applied(document_id=document_id, view_id=view_id)

    def set_main(
        self,
        workspace_id: ApplicationIdentity,
        document_id: ApplicationIdentity,
    ) -> MainReference:
        self._validate_identity(workspace_id, IdentityKind.WORKSPACE)
        resource = self.resource(document_id)
        if resource.path is None:
            raise ValueError("a pathless document must be saved before becoming main")
        self._mains[workspace_id] = document_id
        return self.main(workspace_id)

    def clear_main(self, workspace_id: ApplicationIdentity) -> None:
        self._mains.pop(workspace_id, None)

    def main(self, workspace_id: ApplicationIdentity) -> MainReference | None:
        document_id = self._mains.get(workspace_id)
        if document_id is None:
            return None
        resource = self.resource(document_id)
        return MainReference(
            workspace_id,
            document_id,
            resource.path,
            resource.available and resource.path is not None,
        )

    def mark_unavailable(self, document_id: ApplicationIdentity) -> None:
        resource = self.resource(document_id)
        resource.available = False
        resource.revision += 1

    def resource_token(self, document_id: ApplicationIdentity) -> CacheToken:
        resource = self.resource(document_id)
        return CacheToken(document_id, resource.revision)

    def view_token(self, view_id: ApplicationIdentity) -> CacheToken:
        view = self.view(view_id)
        resource = self.resource(view.document_id)
        return CacheToken(
            view.document_id,
            resource.revision,
            view_id,
            view.epoch,
        )

    def token_is_current(self, token: CacheToken) -> bool:
        resource = self._documents.get(token.document_id)
        if resource is None or not resource.live or resource.revision != token.revision:
            return False
        if token.view_id is None:
            return token.view_epoch is None
        view = self._views.get(token.view_id)
        return bool(
            view is not None
            and view.document_id == token.document_id
            and view.epoch == token.view_epoch
        )

    def apply_if_current(self, token: CacheToken, apply: Callable[[], None]) -> bool:
        if not self.token_is_current(token):
            return False
        apply()
        return True

    def snapshot(self) -> Mapping[str, object]:
        return {
            "documents": {
                str(identity): {
                    "path": resource.path,
                    "text": resource.text,
                    "revision": resource.revision,
                    "dirty": resource.is_dirty(),
                    "live": resource.live,
                    "available": resource.available,
                    "undo": tuple(resource._undo),
                    "redo": tuple(resource._redo),
                }
                for identity, resource in self._documents.items()
            },
            "views": {
                str(identity): {
                    "document_id": str(view.document_id),
                    "workspace_id": str(view.workspace_id),
                    "state": deepcopy(view.state),
                    "epoch": view.epoch,
                }
                for identity, view in self._views.items()
            },
            "retained_views": {
                str(identity): {
                    "document_id": str(descriptor.document_id),
                    "workspace_id": str(descriptor.workspace_id),
                    "state": deepcopy(descriptor.state),
                    "epoch": descriptor.epoch,
                    "suspended": descriptor.suspended,
                }
                for identity, descriptor in self._retained_views.items()
            },
            "mains": {
                str(workspace_id): str(document_id)
                for workspace_id, document_id in self._mains.items()
            },
        }

    def persistence_snapshot(self) -> Mapping[str, object]:
        """Return a JSON-compatible identity/reference snapshot.

        Recovery text remains separately workspace-owned. The clean baseline is
        retained here only to reproduce shared live dirty semantics without
        granting any file-write authority during restoration.
        """

        return {
            "schema": 1,
            "documents": {
                str(identity): {
                    "path": resource.path,
                    "text": resource.text,
                    "clean_text": resource._clean_text,
                    "revision": resource.revision,
                    "live": resource.live,
                    "available": resource.available,
                    "undo": list(resource._undo),
                    "redo": list(resource._redo),
                }
                for identity, resource in self._documents.items()
            },
            "views": {
                str(identity): {
                    "document_id": str(view.document_id),
                    "workspace_id": str(view.workspace_id),
                    "state": asdict(view.state),
                    "epoch": view.epoch,
                }
                for identity, view in self._views.items()
            },
            "retained_views": {
                str(identity): {
                    "document_id": str(descriptor.document_id),
                    "workspace_id": str(descriptor.workspace_id),
                    "state": asdict(descriptor.state),
                    "epoch": descriptor.epoch,
                    "suspended": descriptor.suspended,
                }
                for identity, descriptor in self._retained_views.items()
            },
            "mains": {
                str(workspace_id): str(document_id)
                for workspace_id, document_id in self._mains.items()
            },
            "extensions": deepcopy(self._persistence_extensions),
        }

    def restore_persistence_snapshot(self, snapshot: Mapping[str, object]) -> None:
        """Transactionally restore shared identities without writing files."""

        if not isinstance(snapshot, Mapping) or snapshot.get("schema") != 1:
            raise ValueError("unsupported document-resource schema")
        documents = snapshot.get("documents")
        views = snapshot.get("views")
        retained_views = snapshot.get("retained_views", {})
        mains = snapshot.get("mains")
        extensions = snapshot.get("extensions", {})
        if not all(isinstance(value, Mapping) for value in (documents, views, retained_views, mains, extensions)):
            raise TypeError("document-resource sections must be objects")

        restored = DocumentResourceRegistry()
        restored._persistence_extensions = deepcopy(dict(extensions))
        for identity_value, value in documents.items():
            if not isinstance(identity_value, str) or not isinstance(value, Mapping):
                raise TypeError("invalid document record")
            identity = ApplicationIdentity(IdentityKind.DOCUMENT, identity_value)
            text = value.get("text")
            path = value.get("path")
            clean_text = value.get("clean_text")
            if not isinstance(text, str):
                raise TypeError("document text must be a string")
            if path is not None and not isinstance(path, str):
                raise TypeError("document path must be a string or null")
            if clean_text is not None and not isinstance(clean_text, str):
                raise TypeError("clean text must be a string or null")
            restored.create_document(
                text,
                path=path,
                dirty=clean_text is None or clean_text != text,
                identity=identity,
            )
            resource = restored.resource(identity)
            resource._clean_text = clean_text
            resource.revision = self._positive_int(value.get("revision", 1), "revision")
            resource.live = self._bool(value.get("live", True), "live")
            resource.available = self._bool(
                value.get("available", True), "available"
            )
            undo = value.get("undo", [])
            redo = value.get("redo", [])
            if not isinstance(undo, list) or not all(isinstance(item, str) for item in undo):
                raise TypeError("undo history must be strings")
            if not isinstance(redo, list) or not all(isinstance(item, str) for item in redo):
                raise TypeError("redo history must be strings")
            resource._undo = list(undo)
            resource._redo = list(redo)

        for identity_value, value in views.items():
            if not isinstance(identity_value, str) or not isinstance(value, Mapping):
                raise TypeError("invalid view record")
            state = value.get("state")
            if not isinstance(state, Mapping):
                raise TypeError("view state must be an object")
            normalized = dict(state)
            selection = normalized.get("selection", (0, 0))
            highlight = normalized.get("run_highlight")
            normalized["selection"] = tuple(selection)
            normalized["run_highlight"] = (
                tuple(highlight) if highlight is not None else None
            )
            view_id = ApplicationIdentity(IdentityKind.VIEW, identity_value)
            restored.open_view(
                ApplicationIdentity(IdentityKind.DOCUMENT, value["document_id"]),
                ApplicationIdentity(IdentityKind.WORKSPACE, value["workspace_id"]),
                identity=view_id,
                state=DocumentViewState(**normalized),
            )
            restored.view(view_id).epoch = self._positive_int(
                value.get("epoch", 1), "view epoch"
            )

        for identity_value, value in retained_views.items():
            if not isinstance(identity_value, str) or not isinstance(value, Mapping):
                raise TypeError("invalid retained-view record")
            state = value.get("state")
            if not isinstance(state, Mapping):
                raise TypeError("retained view state must be an object")
            normalized = dict(state)
            normalized["selection"] = tuple(normalized.get("selection", (0, 0)))
            highlight = normalized.get("run_highlight")
            normalized["run_highlight"] = tuple(highlight) if highlight is not None else None
            view_id = ApplicationIdentity(IdentityKind.VIEW, identity_value)
            document_id = ApplicationIdentity(IdentityKind.DOCUMENT, value["document_id"])
            workspace_id = ApplicationIdentity(IdentityKind.WORKSPACE, value["workspace_id"])
            if document_id not in restored._documents:
                raise KeyError(f"unknown retained document: {document_id}")
            restored._retained_views[view_id] = RetainedViewDescriptor(
                view_id,
                document_id,
                workspace_id,
                DocumentViewState(**normalized),
                self._positive_int(value.get("epoch", 1), "retained view epoch"),
                self._bool(value.get("suspended", False), "retained view suspension"),
            )

        for workspace_value, document_value in mains.items():
            if not isinstance(workspace_value, str) or not isinstance(document_value, str):
                raise TypeError("main references must use string identities")
            workspace_id = ApplicationIdentity(IdentityKind.WORKSPACE, workspace_value)
            document_id = ApplicationIdentity(IdentityKind.DOCUMENT, document_value)
            restored._mains[workspace_id] = document_id
        restored.assert_invariants()

        self._documents = restored._documents
        self._views = restored._views
        self._retained_views = restored._retained_views
        self._paths = restored._paths
        self._mains = restored._mains
        self._persistence_extensions = restored._persistence_extensions

    @staticmethod
    def _positive_int(value: object, label: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"{label} must be a positive integer")
        return value

    @staticmethod
    def _bool(value: object, label: str) -> bool:
        if not isinstance(value, bool):
            raise TypeError(f"{label} must be a boolean")
        return value

    def assert_invariants(self) -> bool:
        assert set(self._paths.values()).issubset(self._documents)
        assert len(self._paths.values()) == len(set(self._paths.values()))
        for path, document_id in self._paths.items():
            assert self._documents[document_id].path == path
        for view in self._views.values():
            assert view.identity.kind is IdentityKind.VIEW
            assert view.document_id in self._documents
            assert view.workspace_id.kind is IdentityKind.WORKSPACE
        for descriptor in self._retained_views.values():
            assert descriptor.view_id.kind is IdentityKind.VIEW
            assert descriptor.document_id in self._documents
            assert descriptor.workspace_id.kind is IdentityKind.WORKSPACE
            assert descriptor.view_id not in self._views
        assert set(self._mains.values()).issubset(self._documents)
        return True

    def _notify(
        self, resource: DocumentResource, origin_view_id: ApplicationIdentity
    ) -> None:
        for view_id in self.views_for_document(resource.identity):
            notify = self._views[view_id].notify
            if notify is not None:
                notify(origin_view_id, resource.text, resource.revision)

    @staticmethod
    def _validate_identity(
        identity: ApplicationIdentity, kind: IdentityKind
    ) -> None:
        if not isinstance(identity, ApplicationIdentity) or identity.kind is not kind:
            raise ValueError(f"identity must have {kind.value} kind")

    @staticmethod
    def _applied(
        *,
        document_id: ApplicationIdentity | None = None,
        view_id: ApplicationIdentity | None = None,
    ) -> DocumentOperationResult:
        return DocumentOperationResult(
            DocumentOperationStatus.APPLIED,
            document_id=document_id,
            view_id=view_id,
        )

    @staticmethod
    def _invalid(detail: str) -> DocumentOperationResult:
        return DocumentOperationResult(DocumentOperationStatus.INVALID, detail)
