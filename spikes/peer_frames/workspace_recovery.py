"""Workspace-owned immutable recovery snapshots and conflict equivalence."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class ExternalVersion:
    exists: bool
    text: str | None
    signature: str | None
    modified_at_ns: int | None
    observed_at_ns: int
    metadata: tuple[tuple[str, str], ...] = ()

    @property
    def content_digest(self) -> str | None:
        if self.text is None:
            return None
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    @property
    def equivalence_key(self) -> tuple[object, ...]:
        return (
            self.exists,
            self.content_digest,
            self.signature,
            self.modified_at_ns,
        )


@dataclass(frozen=True)
class WorkspaceRecoverySnapshot:
    snapshot_id: str
    workspace_id: str
    document_id: str
    path: str | None
    text: str
    captured_at_ns: int
    observed_external: ExternalVersion | None
    encoding: str = "utf-8"
    use_bom: bool = False
    line_endings: str = "LF"
    display_name: str = ""
    metadata: tuple[tuple[str, str], ...] = ()

    @property
    def digest(self) -> str:
        payload = json.dumps(
            asdict(self), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ConflictLineage:
    kind: str
    text: str | None
    content_digest: str | None
    timestamp_ns: int | None
    signature: str | None
    metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class WorkspaceConflict:
    workspace_id: str
    document_id: str
    snapshot_id: str
    retained: ConflictLineage
    external: ConflictLineage

    @property
    def equivalence_key(self) -> tuple[object, ...]:
        return (
            self.document_id,
            self.retained.content_digest,
            self.external.content_digest,
            self.external.signature,
            self.external.timestamp_ns,
        )


@dataclass(frozen=True)
class WorkspaceRestoreDecision:
    text: str
    dirty: bool
    conflict: WorkspaceConflict | None


class WorkspaceRecoveryRegistry:
    """Freeze recovery by workspace and resolve only equivalent loaded conflicts."""

    def __init__(self) -> None:
        self._snapshots: dict[
            tuple[str, str], WorkspaceRecoverySnapshot
        ] = {}
        self._conflicts: dict[tuple[str, str], WorkspaceConflict] = {}

    def capture(
        self,
        *,
        workspace_id: str,
        document_id: str,
        path: str | None,
        text: str,
        observed_external: ExternalVersion | None,
        captured_at_ns: int | None = None,
        encoding: str = "utf-8",
        use_bom: bool = False,
        line_endings: str = "LF",
        display_name: str = "",
        metadata: Mapping[str, object] | Iterable[tuple[str, object]] = (),
    ) -> WorkspaceRecoverySnapshot:
        self._identity(workspace_id, "workspace")
        self._identity(document_id, "document")
        if not isinstance(text, str):
            raise TypeError("recovery text must be a string")
        snapshot = WorkspaceRecoverySnapshot(
            "recovery-" + uuid.uuid4().hex,
            workspace_id,
            document_id,
            path,
            text,
            captured_at_ns if captured_at_ns is not None else time.time_ns(),
            observed_external,
            encoding,
            use_bom,
            line_endings,
            display_name,
            self._metadata(metadata),
        )
        self._snapshots[(workspace_id, document_id)] = snapshot
        self._conflicts.pop((workspace_id, document_id), None)
        return snapshot

    def adopt(self, snapshot: WorkspaceRecoverySnapshot) -> None:
        self._validate_snapshot(snapshot)
        self._snapshots[(snapshot.workspace_id, snapshot.document_id)] = snapshot
        self._conflicts.pop((snapshot.workspace_id, snapshot.document_id), None)

    def snapshot(
        self, workspace_id: str, document_id: str
    ) -> WorkspaceRecoverySnapshot | None:
        return self._snapshots.get((workspace_id, document_id))

    def snapshots_for_workspace(
        self, workspace_id: str
    ) -> tuple[WorkspaceRecoverySnapshot, ...]:
        return tuple(
            snapshot
            for (owner, _document_id), snapshot in self._snapshots.items()
            if owner == workspace_id
        )

    def restore(
        self,
        workspace_id: str,
        document_id: str,
        external: ExternalVersion | None,
    ) -> WorkspaceRestoreDecision:
        snapshot = self._snapshots[(workspace_id, document_id)]
        key = (workspace_id, document_id)
        if snapshot.path is None:
            self._conflicts.pop(key, None)
            return WorkspaceRestoreDecision(snapshot.text, True, None)
        if external is not None and external.exists and external.text == snapshot.text:
            self._conflicts.pop(key, None)
            return WorkspaceRestoreDecision(snapshot.text, False, None)

        retained_digest = hashlib.sha256(snapshot.text.encode("utf-8")).hexdigest()
        observed = snapshot.observed_external
        retained_metadata = (
            ("captured_at_ns", str(snapshot.captured_at_ns)),
            *snapshot.metadata,
        )
        external_metadata = (
            ("observed_at_ns", str(external.observed_at_ns))
            if external is not None
            else ("observed_at_ns", "unavailable")
        ,)
        if external is not None:
            external_metadata += external.metadata
        conflict = WorkspaceConflict(
            workspace_id,
            document_id,
            snapshot.snapshot_id,
            ConflictLineage(
                "retained",
                snapshot.text,
                retained_digest,
                snapshot.captured_at_ns,
                observed.signature if observed is not None else None,
                retained_metadata,
            ),
            ConflictLineage(
                "external",
                external.text if external is not None else None,
                external.content_digest if external is not None else None,
                external.modified_at_ns if external is not None else None,
                external.signature if external is not None else "missing",
                external_metadata,
            ),
        )
        self._conflicts[key] = conflict
        return WorkspaceRestoreDecision(snapshot.text, True, conflict)

    def conflict(
        self, workspace_id: str, document_id: str
    ) -> WorkspaceConflict | None:
        return self._conflicts.get((workspace_id, document_id))

    def resolve_loaded(
        self,
        workspace_id: str,
        document_id: str,
        *,
        resolved_text: str,
        loaded_workspace_ids: Iterable[str],
    ) -> tuple[str, ...]:
        if not isinstance(resolved_text, str):
            raise TypeError("resolved text must be a string")
        selected = self._conflicts.get((workspace_id, document_id))
        if selected is None:
            return ()
        loaded = set(loaded_workspace_ids)
        resolved = []
        for key, conflict in tuple(self._conflicts.items()):
            owner, candidate_document_id = key
            if (
                owner in loaded
                and candidate_document_id == document_id
                and conflict.equivalence_key == selected.equivalence_key
            ):
                del self._conflicts[key]
                resolved.append(owner)
        return tuple(resolved)

    def retire_workspace(self, workspace_id: str) -> None:
        for key in tuple(self._snapshots):
            if key[0] == workspace_id:
                del self._snapshots[key]
                self._conflicts.pop(key, None)

    @staticmethod
    def serialize_snapshot(snapshot: WorkspaceRecoverySnapshot) -> dict[str, object]:
        return asdict(snapshot)

    @classmethod
    def deserialize_snapshot(
        cls, payload: Mapping[str, object]
    ) -> WorkspaceRecoverySnapshot:
        value = dict(payload)
        external = value.get("observed_external")
        if external is not None:
            external_value = dict(external)
            external_value["metadata"] = tuple(
                tuple(item) for item in external_value.get("metadata", ())
            )
            value["observed_external"] = ExternalVersion(**external_value)
        value["metadata"] = tuple(tuple(item) for item in value.get("metadata", ()))
        snapshot = WorkspaceRecoverySnapshot(**value)
        cls._validate_snapshot(snapshot)
        return snapshot

    @classmethod
    def _validate_snapshot(cls, snapshot: WorkspaceRecoverySnapshot) -> None:
        cls._identity(snapshot.workspace_id, "workspace")
        cls._identity(snapshot.document_id, "document")
        cls._identity(snapshot.snapshot_id, "recovery snapshot")
        if not isinstance(snapshot.text, str):
            raise TypeError("recovery text must be a string")
        if snapshot.line_endings not in {"CR", "LF", "CRLF"}:
            raise ValueError("invalid line endings")

    @staticmethod
    def _metadata(
        value: Mapping[str, object] | Iterable[tuple[str, object]]
    ) -> tuple[tuple[str, str], ...]:
        items = value.items() if isinstance(value, Mapping) else value
        return tuple(sorted((str(key), str(item)) for key, item in items))

    @staticmethod
    def _identity(value: object, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} identity must be a non-empty string")
        return value
