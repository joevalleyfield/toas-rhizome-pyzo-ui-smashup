"""Versioned, atomic persistence for a concurrently loaded workspace set."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


PROCESS_SCHEMA_VERSION = 1
WORKSPACE_SCHEMA_VERSION = 1
RESOURCE_SCHEMA_VERSION = 1
RECOVERY_SCHEMA_VERSION = 1
MIGRATION_SCHEMA_VERSION = 1


class WorkspacePersistenceError(RuntimeError):
    """A complete durable generation could not be published."""


@dataclass(frozen=True)
class WorkspacePersistenceIssue:
    kind: str
    identity: str | None
    source: str
    detail: str


@dataclass(frozen=True)
class WorkspacePersistenceState:
    loaded_workspace_ids: tuple[str, ...]
    active_workspace_id: str | None
    workspaces: Mapping[str, Mapping[str, object]]
    shared_resources: Mapping[str, object]
    recovery: Mapping[str, Mapping[str, object]]
    application_state: Mapping[str, object]

    def detached_copy(self) -> WorkspacePersistenceState:
        return WorkspacePersistenceState(
            tuple(self.loaded_workspace_ids),
            self.active_workspace_id,
            deepcopy(dict(self.workspaces)),
            deepcopy(dict(self.shared_resources)),
            deepcopy(dict(self.recovery)),
            deepcopy(dict(self.application_state)),
        )


@dataclass(frozen=True)
class WorkspacePersistenceLoad:
    state: WorkspacePersistenceState
    unavailable_workspace_ids: tuple[str, ...] = ()
    issues: tuple[WorkspacePersistenceIssue, ...] = ()
    generation: str | None = None


@dataclass(frozen=True)
class LegacyMigrationResult:
    load: WorkspacePersistenceLoad
    backup_path: str | None
    migrated: bool


@dataclass(frozen=True)
class LegacyRecoveryCandidate:
    document_id: str
    workspace_id: str
    payload: Mapping[str, object]
    digest: str


@dataclass(frozen=True)
class LegacyRecoveryMigration:
    recovery: Mapping[str, Mapping[str, object]]
    retained_documents: Mapping[str, Mapping[str, object]]
    candidates: Mapping[str, tuple[LegacyRecoveryCandidate, ...]] = ()
    blocked_document_ids: tuple[str, ...] = ()
    issues: tuple[WorkspacePersistenceIssue, ...] = ()


class WorkspacePersistenceStore:
    """Publish complete generations behind a small process manifest.

    Each workspace and each workspace recovery record is independently
    checksummed. A damaged child record therefore does not make the process
    manifest or the other workspaces unreadable.
    """

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root)
        self.generations = self.root / "generations"
        self.backups = self.root / "legacy-backups"
        self.manifest = self.root / "manifest.json"

    def load(self) -> WorkspacePersistenceLoad:
        empty = WorkspacePersistenceState((), None, {}, {}, {}, {})
        if not self.manifest.exists():
            return WorkspacePersistenceLoad(empty)
        try:
            manifest = self._read_json(self.manifest)
            self._require_schema(manifest, PROCESS_SCHEMA_VERSION, "process")
            generation = self._safe_component(manifest["generation"])
            loaded_ids = self._identity_list(
                manifest["loaded_workspace_ids"], "loaded workspace"
            )
            active_id = manifest.get("active_workspace_id")
            if active_id is not None and active_id not in loaded_ids:
                raise ValueError("active workspace is not in the loaded set")
            entries = manifest["workspaces"]
            if not isinstance(entries, list):
                raise ValueError("workspace entries must be a list")
            entry_by_id = {}
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError("workspace entry must be an object")
                workspace_id = self._identity(entry["id"], "workspace")
                if workspace_id in entry_by_id:
                    raise ValueError("duplicate workspace entry")
                entry_by_id[workspace_id] = entry
            if not set(loaded_ids).issubset(entry_by_id):
                raise ValueError("loaded workspace has no catalog entry")
            generation_root = self.generations / generation
        except Exception as error:
            issue = WorkspacePersistenceIssue(
                "process", None, str(self.manifest), str(error)
            )
            return WorkspacePersistenceLoad(empty, issues=(issue,))

        issues: list[WorkspacePersistenceIssue] = []
        unavailable: list[str] = []
        workspaces: dict[str, Mapping[str, object]] = {}
        recovery: dict[str, Mapping[str, object]] = {}
        for workspace_id in entry_by_id:
            entry = entry_by_id[workspace_id]
            try:
                payload = self._read_checked_record(
                    generation_root, entry, WORKSPACE_SCHEMA_VERSION, "workspace"
                )
                if payload.get("identity") != workspace_id:
                    raise ValueError("workspace record identity mismatch")
                workspaces[workspace_id] = payload
            except Exception as error:
                unavailable.append(workspace_id)
                issues.append(
                    WorkspacePersistenceIssue(
                        "workspace",
                        workspace_id,
                        str(self._entry_path(generation_root, entry)),
                        str(error),
                    )
                )
                continue

            recovery_entry = entry.get("recovery")
            if recovery_entry is None:
                recovery[workspace_id] = {
                    "schema": RECOVERY_SCHEMA_VERSION,
                    "workspace_id": workspace_id,
                    "snapshots": [],
                }
            else:
                try:
                    recovered = self._read_checked_record(
                        generation_root,
                        recovery_entry,
                        RECOVERY_SCHEMA_VERSION,
                        "recovery",
                    )
                    if recovered.get("workspace_id") != workspace_id:
                        raise ValueError("recovery workspace identity mismatch")
                    if not isinstance(recovered.get("snapshots"), list):
                        raise ValueError("recovery snapshots must be a list")
                    recovery[workspace_id] = recovered
                except Exception as error:
                    issues.append(
                        WorkspacePersistenceIssue(
                            "recovery",
                            workspace_id,
                            str(self._entry_path(generation_root, recovery_entry)),
                            str(error),
                        )
                    )

        resources: Mapping[str, object] = {}
        try:
            resources = self._read_checked_record(
                generation_root,
                manifest["shared_resources"],
                RESOURCE_SCHEMA_VERSION,
                "shared resources",
            )
        except Exception as error:
            issues.append(
                WorkspacePersistenceIssue(
                    "resources",
                    None,
                    str(
                        self._entry_path(
                            generation_root, manifest.get("shared_resources", {})
                        )
                    ),
                    str(error),
                )
            )

        application_state = manifest.get("application_state", {})
        if not isinstance(application_state, dict):
            issues.append(
                WorkspacePersistenceIssue(
                    "application",
                    None,
                    str(self.manifest),
                    "application state must be an object",
                )
            )
            application_state = {}
        migration_recovery = application_state.get("legacy_recovery", {})
        if isinstance(migration_recovery, Mapping):
            migration_issues = migration_recovery.get("issues", [])
            if isinstance(migration_issues, list):
                for issue in migration_issues:
                    if not isinstance(issue, Mapping):
                        continue
                    kind = issue.get("kind")
                    if kind not in {"ambiguous-recovery", "malformed-recovery"}:
                        continue
                    identity = issue.get("identity")
                    issues.append(
                        WorkspacePersistenceIssue(
                            str(kind),
                            identity if isinstance(identity, str) else None,
                            str(issue.get("source", self.manifest)),
                            str(issue.get("detail", "legacy recovery requires review")),
                        )
                    )
        available_active = (
            active_id
            if active_id is not None and active_id in workspaces
            else next(
                (
                    workspace_id
                    for workspace_id in loaded_ids
                    if workspace_id in workspaces
                ),
                None,
            )
        )
        state = WorkspacePersistenceState(
            loaded_ids,
            available_active,
            workspaces,
            resources,
            recovery,
            application_state,
        ).detached_copy()
        return WorkspacePersistenceLoad(
            state,
            tuple(unavailable),
            tuple(issues),
            generation,
        )

    def commit(
        self, state: WorkspacePersistenceState
    ) -> WorkspacePersistenceLoad:
        state = state.detached_copy()
        opaque_entries, opaque_generation = self._opaque_catalog_entries(
            set(state.workspaces)
        )
        self._validate_state(state, frozenset(opaque_entries))
        generation = uuid.uuid4().hex
        temporary = self.generations / f".tmp-{generation}"
        destination = self.generations / generation
        manifest_temporary = self.root / f".manifest-{generation}.tmp"
        try:
            temporary.mkdir(parents=True, exist_ok=False)
            workspace_entries = []
            for index, workspace_id in enumerate(state.workspaces):
                workspace_payload = deepcopy(dict(state.workspaces[workspace_id]))
                workspace_payload.setdefault("schema", WORKSPACE_SCHEMA_VERSION)
                workspace_payload.setdefault("identity", workspace_id)
                workspace_entry = self._write_record(
                    temporary,
                    f"workspace-{index:06d}-{uuid.uuid4().hex}.json",
                    workspace_payload,
                )
                recovery_payload = deepcopy(
                    dict(
                        state.recovery.get(
                            workspace_id,
                            {
                                "schema": RECOVERY_SCHEMA_VERSION,
                                "workspace_id": workspace_id,
                                "snapshots": [],
                            },
                        )
                    )
                )
                recovery_payload.setdefault("schema", RECOVERY_SCHEMA_VERSION)
                recovery_payload.setdefault("workspace_id", workspace_id)
                recovery_entry = self._write_record(
                    temporary,
                    f"recovery-{index:06d}-{uuid.uuid4().hex}.json",
                    recovery_payload,
                )
                workspace_entries.append(
                    {
                        "id": workspace_id,
                        **workspace_entry,
                        "recovery": recovery_entry,
                    }
                )
            for workspace_id, entry in opaque_entries.items():
                retained = deepcopy(entry)
                retained["generation"] = retained.get(
                    "generation", opaque_generation
                )
                recovery_entry = retained.get("recovery")
                if isinstance(recovery_entry, dict):
                    recovery_entry["generation"] = recovery_entry.get(
                        "generation", opaque_generation
                    )
                workspace_entries.append(retained)
            resources = deepcopy(dict(state.shared_resources))
            resources.setdefault("schema", RESOURCE_SCHEMA_VERSION)
            resources_entry = self._write_record(
                temporary,
                f"resources-{uuid.uuid4().hex}.json",
                resources,
            )
            self._fsync_directory(temporary)
            self.generations.mkdir(parents=True, exist_ok=True)
            os.replace(temporary, destination)
            self._fsync_directory(self.generations)
            self.root.mkdir(parents=True, exist_ok=True)
            self._write_json(
                manifest_temporary,
                {
                    "schema": PROCESS_SCHEMA_VERSION,
                    "generation": generation,
                    "loaded_workspace_ids": list(state.loaded_workspace_ids),
                    "active_workspace_id": state.active_workspace_id,
                    "workspaces": workspace_entries,
                    "shared_resources": resources_entry,
                    "application_state": deepcopy(dict(state.application_state)),
                },
            )
            os.replace(manifest_temporary, self.manifest)
            self._fsync_directory(self.root)
        except Exception as error:
            shutil.rmtree(temporary, ignore_errors=True)
            try:
                manifest_temporary.unlink()
            except OSError:
                pass
            raise WorkspacePersistenceError(str(error)) from error
        self._remove_stale_generations(generation)
        return self.load()

    def migrate_legacy(
        self,
        legacy_config: Mapping[str, object],
        *,
        default_workspace_id: str,
        default_workspace_name: str = "Default",
    ) -> LegacyMigrationResult:
        """Migrate one accepted peer session without reinterpreting named views."""

        if self.manifest.exists():
            return LegacyMigrationResult(self.load(), None, False)
        if not isinstance(legacy_config, Mapping):
            raise TypeError("legacy config must be an object")
        legacy = deepcopy(dict(legacy_config))
        state_node = legacy.get("state", {})
        if not isinstance(state_node, Mapping):
            state_node = {}
        session = deepcopy(dict(state_node).get("peerWorkspaceSession", {}))
        if not isinstance(session, Mapping):
            session = {}

        legacy_recovery = legacy.get("workspaceRecovery")
        if legacy_recovery is None:
            legacy_recovery = dict(state_node).get("workspaceRecovery", {})
        recovery_migration = self._migrate_legacy_recovery(legacy_recovery)

        backup_path = self._write_legacy_backup(legacy)
        workspace = {
            "schema": WORKSPACE_SCHEMA_VERSION,
            "identity": default_workspace_id,
            "name": default_workspace_name,
            "session": deepcopy(dict(session)),
            "profile": {},
            "extensions": {},
        }
        application_state = {
            "migration": {
                "schema": MIGRATION_SCHEMA_VERSION,
                "source": "peerWorkspaceSession",
                "backup": str(backup_path),
            },
            # Exact input is retained so unknown/deprecated and named-view fields
            # have an explicit lossless round-trip owner.
            "legacy_config": legacy,
            "legacy_recovery": {
                "candidates": {
                    document_id: [
                        deepcopy(dict(candidate.payload))
                        for candidate in candidates
                    ]
                    for document_id, candidates in recovery_migration.candidates.items()
                },
                "issues": [
                    {
                        "kind": issue.kind,
                        "identity": issue.identity,
                        "source": issue.source,
                        "detail": issue.detail,
                    }
                    for issue in recovery_migration.issues
                ],
                "blocked_documents": list(recovery_migration.blocked_document_ids),
            },
        }
        resources = {
            "schema": RESOURCE_SCHEMA_VERSION,
            "documents": {},
            "views": {},
            "mains": {},
            "retained_documents": deepcopy(
                dict(recovery_migration.retained_documents)
            ),
        }
        state = WorkspacePersistenceState(
            (default_workspace_id,),
            default_workspace_id,
            {default_workspace_id: workspace},
            resources,
            {
                default_workspace_id: recovery_migration.recovery[default_workspace_id]
            }
            if default_workspace_id in recovery_migration.recovery
            else {},
            application_state,
        )
        loaded = self.commit(state)
        if recovery_migration.issues:
            loaded = WorkspacePersistenceLoad(
                loaded.state,
                loaded.unavailable_workspace_ids,
                loaded.issues + recovery_migration.issues,
                loaded.generation,
            )
        return LegacyMigrationResult(loaded, str(backup_path), True)

    def select_legacy_recovery(
        self, document_id: str, candidate_index: int, *, workspace_id: str
    ) -> WorkspacePersistenceLoad:
        """Durably select one preserved candidate without modifying a source.

        All original candidates and raw legacy input remain recoverable. The
        selected document becomes a closed retained buffer in the addressed
        workspace; callers adopt it into the live registry after publication.
        """
        from .document_resources import DocumentResourceRegistry

        loaded = self.load()
        if any(
            issue.kind in {"process", "resources", "application"}
            for issue in loaded.issues
        ):
            raise WorkspacePersistenceError(
                "persistence needs repair before recovery selection"
            )
        state = loaded.state.detached_copy()
        if (
            workspace_id not in state.loaded_workspace_ids
            or workspace_id not in state.workspaces
        ):
            raise ValueError("open a workspace before selecting recovery")
        migration = state.application_state.get("legacy_recovery", {})
        if document_id not in migration.get("blocked_documents", []):
            raise ValueError("document has no unresolved legacy recovery")
        candidates = migration.get("candidates", {}).get(document_id, [])
        if type(candidate_index) is not int or not 0 <= candidate_index < len(
            candidates
        ):
            raise ValueError("invalid recovery candidate")
        candidate = deepcopy(candidates[candidate_index])
        resources = dict(state.shared_resources)
        for name in ("documents", "views", "retained_views", "mains", "extensions"):
            resources[name] = deepcopy(dict(resources.get(name, {})))
        resources["schema"] = 1
        if document_id in resources["documents"]:
            raise ValueError("an authoritative retained document already exists")
        path = candidate.get("path", candidate.get("filename")) or None
        if path is not None:
            if not isinstance(path, str):
                raise ValueError("recovery path must be a string")
            path = os.path.realpath(os.path.abspath(path))
            for record in resources["documents"].values():
                existing_path = record.get("path")
                if (
                    existing_path
                    and os.path.realpath(os.path.abspath(existing_path)) == path
                ):
                    raise ValueError(
                        "recovery path already belongs to another document"
                    )
        resources["documents"][document_id] = {
            "text": candidate["text"],
            "path": path,
            "clean_text": candidate.get("clean_text"),
            "revision": 1,
            "undo": deepcopy(candidate.get("undo", candidate.get("history", []))),
            "redo": deepcopy(candidate.get("redo", [])),
        }
        view_id = "legacy-recovery-" + uuid.uuid4().hex
        resources["retained_views"][view_id] = {
            "document_id": document_id,
            "workspace_id": workspace_id,
            "state": deepcopy(candidate.get("view_state", {})),
            "epoch": 1,
        }
        resources["extensions"].setdefault("legacy_recovery_selections", {})[
            document_id
        ] = candidate
        # Validate text/history/path and references before touching the manifest.
        validator = DocumentResourceRegistry()
        validator.restore_persistence_snapshot(resources)
        migration.setdefault("selections", {})[document_id] = {
            "candidate_index": candidate_index,
            "workspace_id": workspace_id,
            "view_id": view_id,
        }
        migration["blocked_documents"] = [
            identity
            for identity in migration["blocked_documents"]
            if identity != document_id
        ]
        migration["issues"] = [
            issue
            for issue in migration.get("issues", [])
            if issue.get("identity") != document_id
        ]
        return self.commit(
            WorkspacePersistenceState(
                state.loaded_workspace_ids,
                state.active_workspace_id,
                state.workspaces,
                resources,
                state.recovery,
                state.application_state,
            )
        )

    def _migrate_legacy_recovery(
        self, legacy_recovery: object
    ) -> LegacyRecoveryMigration:
        parse_issues: list[WorkspacePersistenceIssue] = []
        try:
            candidates_by_document = self._legacy_candidates(
                legacy_recovery, parse_issues
            )
        except ValueError as error:
            return LegacyRecoveryMigration(
                {},
                {},
                {},
                (),
                (
                    WorkspacePersistenceIssue(
                        "malformed-recovery",
                        None,
                        "legacy.workspaceRecovery",
                        str(error),
                    ),
                ),
            )
        recovery: dict[str, dict[str, object]] = {}
        retained: dict[str, dict[str, object]] = {}
        issues: list[WorkspacePersistenceIssue] = parse_issues
        blocked = {
            issue.identity
            for issue in issues
            if issue.identity is not None
        }
        for document_id, candidates in candidates_by_document.items():
            by_digest: dict[str, list[LegacyRecoveryCandidate]] = {}
            for candidate in candidates:
                by_digest.setdefault(candidate.digest, []).append(candidate)
                if document_id not in blocked:
                    record = recovery.setdefault(
                        candidate.workspace_id,
                        {
                            "schema": RECOVERY_SCHEMA_VERSION,
                            "workspace_id": candidate.workspace_id,
                            "snapshots": [],
                        },
                    )
                    snapshots = record["snapshots"]
                    assert isinstance(snapshots, list)
                    snapshots.append(deepcopy(dict(candidate.payload)))
            if len(by_digest) == 1 and document_id not in blocked:
                representative = candidates[0]
                retained[document_id] = {
                    "schema": 1,
                    "document_id": document_id,
                    "candidate": deepcopy(dict(representative.payload)),
                    "workspace_ids": sorted(
                        {candidate.workspace_id for candidate in candidates}
                    ),
                    "provenance": "legacy-workspace-recovery",
                }
            else:
                blocked.add(document_id)
                for record in recovery.values():
                    snapshots = record["snapshots"]
                    assert isinstance(snapshots, list)
                    record["snapshots"] = [
                        snapshot
                        for snapshot in snapshots
                        if snapshot.get("document_id") != document_id
                    ]
                issues.append(
                    WorkspacePersistenceIssue(
                        "ambiguous-recovery",
                        document_id,
                        "legacy.workspaceRecovery",
                        "divergent candidates preserved; explicit selection required",
                    )
                )
        recovery = {
            workspace_id: record
            for workspace_id, record in recovery.items()
            if record["snapshots"]
        }
        return LegacyRecoveryMigration(
            recovery,
            retained,
            {key: tuple(value) for key, value in candidates_by_document.items()},
            tuple(sorted(blocked)),
            tuple(issues),
        )

    def _legacy_candidates(
        self,
        legacy_recovery: object,
        issues: list[WorkspacePersistenceIssue] | None = None,
    ) -> dict[str, list[LegacyRecoveryCandidate]]:
        if legacy_recovery in (None, {}):
            return {}
        if not isinstance(legacy_recovery, Mapping):
            raise ValueError("legacy workspace recovery must be an object")
        result: dict[str, list[LegacyRecoveryCandidate]] = {}
        for workspace_id, value in legacy_recovery.items():
            if not isinstance(workspace_id, str) or not workspace_id.strip():
                raise ValueError("legacy recovery workspace identity is invalid")
            if isinstance(value, Mapping):
                raw_snapshots = value.get("snapshots", [])
            else:
                raw_snapshots = value
            if not isinstance(raw_snapshots, list):
                if issues is not None:
                    issues.append(
                        WorkspacePersistenceIssue(
                            "malformed-recovery",
                            None,
                            "legacy.workspaceRecovery",
                            "legacy recovery snapshots must be a list",
                        )
                    )
                    continue
                raise ValueError("legacy recovery snapshots must be a list")
            for snapshot in raw_snapshots:
                if not isinstance(snapshot, Mapping):
                    if issues is not None:
                        issues.append(
                            WorkspacePersistenceIssue(
                                "malformed-recovery",
                                None,
                                "legacy.workspaceRecovery",
                                "legacy recovery snapshot must be an object",
                            )
                        )
                        continue
                    raise ValueError("legacy recovery snapshot must be an object")
                document_id = snapshot.get("document_id")
                if not isinstance(document_id, str) or not document_id.strip():
                    if issues is not None:
                        issues.append(
                            WorkspacePersistenceIssue(
                                "malformed-recovery",
                                None,
                                "legacy.workspaceRecovery",
                                "legacy recovery document identity is invalid",
                            )
                        )
                        continue
                    raise ValueError("legacy recovery document identity is invalid")
                invalid = (
                    not isinstance(snapshot.get("text"), str),
                    "clean_text" in snapshot
                    and snapshot.get("clean_text") is not None
                    and not isinstance(snapshot.get("clean_text"), str),
                    "history" in snapshot
                    and (
                        not isinstance(snapshot.get("history"), list)
                        or not all(isinstance(item, str) for item in snapshot["history"])
                    ),
                )
                if any(invalid):
                    if issues is not None:
                        issues.append(
                            WorkspacePersistenceIssue(
                                "malformed-recovery",
                                document_id,
                                "legacy.workspaceRecovery",
                                "legacy recovery candidate has invalid editing state",
                            )
                        )
                        continue
                    raise ValueError("legacy recovery candidate has invalid editing state")
                payload = deepcopy(dict(snapshot))
                comparable = {
                    key: value
                    for key, value in payload.items()
                    if key not in {"snapshot_id", "workspace_id", "captured_at_ns"}
                }
                digest = self._digest(comparable)
                result.setdefault(document_id, []).append(
                    LegacyRecoveryCandidate(document_id, workspace_id, payload, digest)
                )
        return result

    def _write_legacy_backup(self, legacy: Mapping[str, object]) -> Path:
        self.backups.mkdir(parents=True, exist_ok=True)
        path = self.backups / f"legacy-{uuid.uuid4().hex}.json"
        self._write_json(path, legacy)
        self._fsync_directory(self.backups)
        return path

    def _validate_state(
        self,
        state: WorkspacePersistenceState,
        opaque_workspace_ids: frozenset[str] = frozenset(),
    ) -> None:
        loaded = self._identity_list(
            list(state.loaded_workspace_ids), "loaded workspace"
        )
        if len(loaded) != len(set(loaded)):
            raise ValueError("duplicate loaded workspace")
        if not set(loaded).issubset(
            set(state.workspaces).union(opaque_workspace_ids)
        ):
            raise ValueError("loaded workspace has no record")
        if state.active_workspace_id is not None and state.active_workspace_id not in loaded:
            raise ValueError("active workspace is not loaded")
        for workspace_id, workspace in state.workspaces.items():
            self._identity(workspace_id, "workspace")
            if not isinstance(workspace, Mapping):
                raise TypeError("workspace record must be an object")
            schema = workspace.get("schema", WORKSPACE_SCHEMA_VERSION)
            if schema != WORKSPACE_SCHEMA_VERSION:
                raise ValueError("unsupported workspace schema")
            identity = workspace.get("identity", workspace_id)
            if identity != workspace_id:
                raise ValueError("workspace record identity mismatch")
        for workspace_id, recovery in state.recovery.items():
            if workspace_id not in state.workspaces:
                raise ValueError("recovery refers to an unloaded workspace")
            if not isinstance(recovery, Mapping):
                raise TypeError("recovery record must be an object")
            if recovery.get("schema", RECOVERY_SCHEMA_VERSION) != RECOVERY_SCHEMA_VERSION:
                raise ValueError("unsupported recovery schema")
            if recovery.get("workspace_id", workspace_id) != workspace_id:
                raise ValueError("recovery workspace identity mismatch")
            if not isinstance(recovery.get("snapshots", []), list):
                raise TypeError("recovery snapshots must be a list")
        for label, value in (
            ("shared resources", state.shared_resources),
            ("application state", state.application_state),
        ):
            if not isinstance(value, Mapping):
                raise TypeError(f"{label} must be an object")
        resource_schema = state.shared_resources.get(
            "schema", RESOURCE_SCHEMA_VERSION
        )
        if resource_schema != RESOURCE_SCHEMA_VERSION:
            raise ValueError("unsupported shared-resource schema")

    def _read_checked_record(
        self,
        generation_root: Path,
        entry: object,
        schema: int,
        label: str,
    ) -> dict:
        if not isinstance(entry, Mapping):
            raise ValueError(f"{label} entry must be an object")
        source = self._entry_path(generation_root, entry)
        payload = self._read_json(source)
        if self._digest(payload) != entry.get("digest"):
            raise ValueError(f"{label} digest mismatch")
        self._require_schema(payload, schema, label)
        return payload

    def _write_record(
        self, root: Path, filename: str, payload: Mapping[str, object]
    ) -> dict[str, str]:
        path = root / filename
        self._write_json(path, payload)
        return {"file": filename, "digest": self._digest(payload)}

    @classmethod
    def _entry_path(cls, root: Path, entry: object) -> Path:
        if not isinstance(entry, Mapping):
            return root / "<invalid-entry>"
        try:
            generation = entry.get("generation")
            if generation is not None:
                root = root.parent / cls._safe_component(generation)
            return root / cls._safe_component(entry.get("file"))
        except ValueError:
            return root / "<invalid-file>"

    def _opaque_catalog_entries(
        self, available_workspace_ids: set[str]
    ) -> tuple[dict[str, dict], str | None]:
        if not self.manifest.exists():
            return {}, None
        try:
            manifest = self._read_json(self.manifest)
            generation = self._safe_component(manifest["generation"])
            entries = manifest["workspaces"]
            if not isinstance(entries, list):
                return {}, generation
        except Exception:
            return {}, None
        opaque = {}
        for entry in entries:
            if (
                isinstance(entry, dict)
                and isinstance(entry.get("id"), str)
                and entry["id"] not in available_workspace_ids
            ):
                opaque[entry["id"]] = deepcopy(entry)
        return opaque, generation

    @staticmethod
    def _digest(payload: object) -> str:
        encoded = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _read_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
        if not isinstance(value, dict):
            raise ValueError("JSON root must be an object")
        return value

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())

    @staticmethod
    def _safe_component(value: object) -> str:
        if not isinstance(value, str) or not value or Path(value).name != value:
            raise ValueError("unsafe path component")
        return value

    @staticmethod
    def _identity(value: object, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} identity must be a non-empty string")
        return value

    @classmethod
    def _identity_list(cls, value: object, label: str) -> tuple[str, ...]:
        if not isinstance(value, list):
            raise TypeError(f"{label} identities must be a list")
        return tuple(cls._identity(item, label) for item in value)

    @staticmethod
    def _require_schema(payload: Mapping[str, object], expected: int, label: str) -> None:
        if payload.get("schema") != expected:
            raise ValueError(f"unsupported {label} schema: {payload.get('schema')}")

    def _remove_stale_generations(self, current: str) -> None:
        if not self.generations.exists():
            return
        protected = {current}
        try:
            manifest = self._read_json(self.manifest)
            for entry in manifest.get("workspaces", ()):
                if isinstance(entry, dict):
                    if isinstance(entry.get("generation"), str):
                        protected.add(entry["generation"])
                    recovery = entry.get("recovery")
                    if (
                        isinstance(recovery, dict)
                        and isinstance(recovery.get("generation"), str)
                    ):
                        protected.add(recovery["generation"])
        except Exception:
            pass
        stale = [
            path
            for path in self.generations.iterdir()
            if path.name not in protected and not path.name.startswith(".tmp-")
        ]
        # Keep one prior complete generation as an additional recovery aid.
        stale.sort(key=lambda path: path.stat().st_mtime_ns, reverse=True)
        for path in stale[1:]:
            shutil.rmtree(path, ignore_errors=True)

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
