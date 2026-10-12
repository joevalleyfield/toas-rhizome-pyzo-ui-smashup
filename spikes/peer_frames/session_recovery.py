"""Durable, technology-neutral recovery snapshots for dirty documents."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Protocol

from .persistence_io import fsync_directory


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RecoverySnapshot:
    document_id: str
    filename: str | None
    display_name: str
    text: str
    encoding: str
    use_bom: bool
    line_endings: str
    disk_signature: str | None = None
    workspace_affinity: str | None = None

    @property
    def digest(self) -> str:
        payload = json.dumps(
            asdict(self), sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class RecoveryIssue:
    source: str
    detail: str
    quarantined_to: str | None = None


@dataclass(frozen=True)
class RecoveryLoadResult:
    snapshots: tuple[RecoverySnapshot, ...]
    issues: tuple[RecoveryIssue, ...]


class RecoveryWriteError(RuntimeError):
    """A new recovery generation could not be committed durably."""


class RetentionFailureChoice(str, Enum):
    RETRY = "retry"
    SAVE = "save"
    DISCARD = "discard"
    CANCEL = "cancel"


class RetainableDocument(Protocol):
    def is_dirty(self) -> bool: ...

    def recovery_snapshot(self) -> RecoverySnapshot: ...

    def save_document(self) -> bool: ...

    def discard_recovery_for_exit(self) -> None: ...


class RecoveryRetentionCoordinator:
    """Make automatic retention a pre-commit application transaction."""

    def __init__(
        self,
        store: RecoveryStore,
        choose_failure: Callable[
            [tuple[RetainableDocument, ...], Exception],
            RetentionFailureChoice | str,
        ],
    ):
        self.store = store
        self._choose_failure = choose_failure

    def retain(self, documents: tuple[RetainableDocument, ...]) -> bool:
        pending = tuple(documents)
        while True:
            try:
                snapshots = tuple(document.recovery_snapshot() for document in pending)
                for document, captured in zip(pending, snapshots):
                    if (
                        not document.is_dirty()
                        or document.recovery_snapshot().digest != captured.digest
                    ):
                        raise RecoveryWriteError(
                            "document changed while recovery was being captured"
                        )
                existing = {
                    snapshot.document_id: snapshot
                    for snapshot in self.store.load().snapshots
                }
                for snapshot in snapshots:
                    if existing.get(snapshot.document_id) != snapshot:
                        self.store.commit({snapshot.document_id: snapshot})
                return True
            except Exception as error:
                committed = {
                    snapshot.document_id: snapshot
                    for snapshot in self.store.load().snapshots
                }
                affected_items = []
                for document in pending:
                    try:
                        captured = document.recovery_snapshot()
                    except Exception:
                        affected_items.append(document)
                        continue
                    if committed.get(captured.document_id) != captured:
                        affected_items.append(document)
                affected = tuple(affected_items)
                if not affected:
                    affected = pending
                try:
                    choice = RetentionFailureChoice(
                        self._choose_failure(affected, error)
                    )
                except (TypeError, ValueError):
                    return False
                if choice is RetentionFailureChoice.RETRY:
                    pending = affected
                    continue
                if choice is RetentionFailureChoice.SAVE:
                    results = [
                        not document.is_dirty() or document.save_document()
                        for document in affected
                    ]
                    return all(results)
                if choice is RetentionFailureChoice.DISCARD:
                    for document in affected:
                        document.discard_recovery_for_exit()
                    return True
                return False


def named_document_id(filename: str) -> str:
    normalized = os.path.normcase(os.path.abspath(filename)).encode("utf-8")
    return "named-" + hashlib.sha256(normalized).hexdigest()


def new_untitled_document_id() -> str:
    return "untitled-" + uuid.uuid4().hex


def file_signature(filename: str | None) -> str | None:
    if not filename:
        return None
    try:
        with open(filename, "rb") as stream:
            digest = hashlib.sha256(stream.read()).hexdigest()
        stat = os.stat(filename)
    except OSError:
        return "missing"
    return f"{stat.st_size}:{stat.st_mtime_ns}:{digest}"


class RecoveryStore:
    """Commit complete recovery generations behind one atomic manifest."""

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root)
        self.generations = self.root / "generations"
        self.quarantine = self.root / "quarantine"
        self.manifest = self.root / "manifest.json"

    def load(self) -> RecoveryLoadResult:
        if not self.manifest.exists():
            return RecoveryLoadResult((), ())
        try:
            manifest = self._read_json(self.manifest)
            if manifest.get("schema") != SCHEMA_VERSION:
                raise ValueError(f"unsupported manifest schema: {manifest.get('schema')}")
            generation = self._safe_component(manifest["generation"])
            entries = manifest["records"]
            if not isinstance(entries, list):
                raise ValueError("manifest records must be a list")
        except Exception as error:
            issue = self._quarantine_path(self.manifest, f"manifest: {error}")
            return RecoveryLoadResult((), (issue,))

        snapshots = []
        issues = []
        identities = set()
        filenames = set()
        for entry in entries:
            source = self.manifest
            try:
                if not isinstance(entry, dict):
                    raise ValueError("record entry must be an object")
                filename = self._safe_component(entry["file"])
                source = self.generations / generation / filename
                payload = self._read_json(source)
                snapshot = RecoverySnapshot(**payload)
                self._validate_snapshot(snapshot)
                if snapshot.digest != entry["digest"]:
                    raise ValueError("record digest mismatch")
                normalized_filename = (
                    os.path.normcase(os.path.abspath(snapshot.filename))
                    if snapshot.filename
                    else None
                )
                if snapshot.document_id in identities:
                    raise ValueError("duplicate document identity")
                if normalized_filename and normalized_filename in filenames:
                    raise ValueError("duplicate named document")
                identities.add(snapshot.document_id)
                if normalized_filename:
                    filenames.add(normalized_filename)
                snapshots.append(snapshot)
            except Exception as error:
                issues.append(self._quarantine_path(source, f"record: {error}"))
        return RecoveryLoadResult(tuple(snapshots), tuple(issues))

    def commit(
        self,
        snapshots: Mapping[str, RecoverySnapshot],
        *,
        remove_ids: frozenset[str] = frozenset(),
    ) -> RecoveryLoadResult:
        current = self.load()
        merged = {snapshot.document_id: snapshot for snapshot in current.snapshots}
        for document_id in remove_ids:
            merged.pop(document_id, None)
        merged.update(snapshots)

        generation = uuid.uuid4().hex
        temporary = self.generations / f".tmp-{generation}"
        destination = self.generations / generation
        manifest_temporary = self.root / f".manifest-{generation}.tmp"
        try:
            for document_id, snapshot in snapshots.items():
                if document_id != snapshot.document_id:
                    raise ValueError("snapshot key does not match document identity")
            self._validate_generation(tuple(merged.values()))
            temporary.mkdir(parents=True, exist_ok=False)
            entries = []
            for index, snapshot in enumerate(merged.values()):
                record_name = f"{index:06d}-{uuid.uuid4().hex}.json"
                self._write_json(temporary / record_name, asdict(snapshot))
                entries.append(
                    {
                        "document_id": snapshot.document_id,
                        "file": record_name,
                        "digest": snapshot.digest,
                    }
                )
            self._fsync_directory(temporary)
            os.replace(temporary, destination)
            self._fsync_directory(self.generations)
            self.root.mkdir(parents=True, exist_ok=True)
            self._write_json(
                manifest_temporary,
                {
                    "schema": SCHEMA_VERSION,
                    "generation": generation,
                    "records": entries,
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
            raise RecoveryWriteError(str(error)) from error

        self._remove_old_generations(generation)
        return RecoveryLoadResult(tuple(merged.values()), current.issues)

    def retire(self, *document_ids: str) -> RecoveryLoadResult:
        return self.commit({}, remove_ids=frozenset(document_ids))

    def invalidate(self, *document_ids: str) -> None:
        """Destructively prevent explicitly abandoned snapshots restoring.

        This path is reserved for a user-approved discard when a normal atomic
        manifest update cannot be written (for example, a full disk).
        """

        if not self.manifest.exists():
            return
        manifest = self._read_json(self.manifest)
        generation = self._safe_component(manifest["generation"])
        selected = set(document_ids)
        for entry in manifest.get("records", ()):
            if isinstance(entry, dict) and entry.get("document_id") in selected:
                filename = self._safe_component(entry["file"])
                try:
                    (self.generations / generation / filename).unlink()
                except FileNotFoundError:
                    pass

    def _read_json(self, path: Path) -> dict:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
        if not isinstance(value, dict):
            raise ValueError("JSON root must be an object")
        return value

    def _write_json(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())

    def _quarantine_path(self, path: Path, detail: str) -> RecoveryIssue:
        quarantined_to = None
        if path.exists():
            try:
                self.quarantine.mkdir(parents=True, exist_ok=True)
                target = self.quarantine / f"{uuid.uuid4().hex}-{path.name}"
                os.replace(path, target)
                quarantined_to = str(target)
            except OSError:
                pass
        return RecoveryIssue(str(path), detail, quarantined_to)

    @staticmethod
    def _safe_component(value: object) -> str:
        if not isinstance(value, str) or not value or Path(value).name != value:
            raise ValueError("unsafe path component")
        return value

    @staticmethod
    def _validate_snapshot(snapshot: RecoverySnapshot) -> None:
        if not isinstance(snapshot.document_id, str) or not snapshot.document_id:
            raise ValueError("invalid document identity")
        if snapshot.filename is not None and not isinstance(snapshot.filename, str):
            raise ValueError("invalid filename")
        for label, value in (
            ("display name", snapshot.display_name),
            ("text", snapshot.text),
            ("encoding", snapshot.encoding),
        ):
            if not isinstance(value, str):
                raise ValueError(f"invalid {label}")
        if not isinstance(snapshot.use_bom, bool):
            raise ValueError("invalid BOM flag")
        if snapshot.line_endings not in {"CR", "LF", "CRLF"}:
            raise ValueError("invalid line-ending mode")
        if snapshot.disk_signature is not None and not isinstance(
            snapshot.disk_signature, str
        ):
            raise ValueError("invalid disk signature")
        if snapshot.workspace_affinity is not None and not isinstance(
            snapshot.workspace_affinity, str
        ):
            raise ValueError("invalid workspace affinity")

    @classmethod
    def _validate_generation(
        cls, snapshots: tuple[RecoverySnapshot, ...]
    ) -> None:
        identities = set()
        filenames = set()
        for snapshot in snapshots:
            cls._validate_snapshot(snapshot)
            if snapshot.document_id in identities:
                raise ValueError("duplicate document identity")
            identities.add(snapshot.document_id)
            if snapshot.filename:
                filename = os.path.normcase(os.path.abspath(snapshot.filename))
                if filename in filenames:
                    raise ValueError("duplicate named document")
                filenames.add(filename)

    def _remove_old_generations(self, current: str) -> None:
        if not self.generations.exists():
            return
        for path in self.generations.iterdir():
            if path.name != current:
                shutil.rmtree(path, ignore_errors=True)

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        fsync_directory(path)
