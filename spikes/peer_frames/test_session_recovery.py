from __future__ import annotations

import json
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from spikes.peer_frames.session_recovery import (
    RecoveryRetentionCoordinator,
    RecoverySnapshot,
    RecoveryStore,
    RecoveryWriteError,
    named_document_id,
)


def snapshot(document_id="document", filename=None, text="dirty\n"):
    return RecoverySnapshot(
        document_id=document_id,
        filename=filename,
        display_name=filename or "Untitled",
        text=text,
        encoding="utf-8",
        use_bom=False,
        line_endings="LF",
        disk_signature=None,
    )


class RecoveryStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "recovery"
        self.store = RecoveryStore(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def test_named_and_untitled_snapshots_round_trip_exact_metadata(self):
        named = snapshot("named", "/project/café.py", "print('café')\n")
        named = replace(named, encoding="latin-1", use_bom=True, line_endings="CRLF")
        untitled = snapshot("untitled-identity", text="draft")

        committed = self.store.commit({item.document_id: item for item in (named, untitled)})
        loaded = self.store.load()

        self.assertEqual(set(committed.snapshots), {named, untitled})
        self.assertEqual(set(loaded.snapshots), {named, untitled})
        self.assertEqual(loaded.issues, ())

    def test_changed_snapshot_replaces_record_and_unchanged_can_be_reused(self):
        first = snapshot(text="first")
        self.store.commit({first.document_id: first})
        original_generation = json.loads(self.store.manifest.read_text())["generation"]

        loaded = self.store.load().snapshots[0]
        self.assertEqual(loaded.digest, first.digest)
        second = replace(first, text="second")
        self.store.commit({second.document_id: second})

        self.assertEqual(self.store.load().snapshots, (second,))
        self.assertNotEqual(
            json.loads(self.store.manifest.read_text())["generation"],
            original_generation,
        )

    def test_retire_removes_only_selected_document(self):
        first = snapshot("first")
        second = snapshot("second")
        self.store.commit({"first": first, "second": second})

        self.store.retire("first")

        self.assertEqual(self.store.load().snapshots, (second,))

    def test_failed_manifest_replace_leaves_previous_generation_authoritative(self):
        first = snapshot(text="first")
        self.store.commit({first.document_id: first})
        original_replace = os.replace

        def fail_manifest(source, destination):
            if Path(destination) == self.store.manifest:
                raise OSError("disk full")
            return original_replace(source, destination)

        os.replace = fail_manifest
        try:
            with self.assertRaisesRegex(RecoveryWriteError, "disk full"):
                self.store.commit({first.document_id: replace(first, text="second")})
        finally:
            os.replace = original_replace

        self.assertEqual(self.store.load().snapshots, (first,))

    def test_corrupt_record_is_quarantined_while_valid_record_restores(self):
        first = snapshot("first")
        second = snapshot("second")
        self.store.commit({"first": first, "second": second})
        manifest = json.loads(self.store.manifest.read_text())
        corrupt = self.store.generations / manifest["generation"] / manifest["records"][0]["file"]
        corrupt.write_text("not json", encoding="utf-8")

        loaded = self.store.load()

        self.assertEqual(len(loaded.snapshots), 1)
        self.assertEqual(len(loaded.issues), 1)
        self.assertIsNotNone(loaded.issues[0].quarantined_to)

    def test_unknown_manifest_schema_is_quarantined(self):
        self.root.mkdir(parents=True)
        self.store.manifest.write_text('{"schema": 999}', encoding="utf-8")

        loaded = self.store.load()

        self.assertEqual(loaded.snapshots, ())
        self.assertEqual(len(loaded.issues), 1)
        self.assertFalse(self.store.manifest.exists())

    def test_invalid_record_metadata_is_quarantined(self):
        item = snapshot("document")
        self.store.commit({item.document_id: item})
        manifest = json.loads(self.store.manifest.read_text())
        record = (
            self.store.generations
            / manifest["generation"]
            / manifest["records"][0]["file"]
        )
        payload = json.loads(record.read_text())
        payload["line_endings"] = "sideways"
        record.write_text(json.dumps(payload), encoding="utf-8")
        manifest["records"][0]["digest"] = RecoverySnapshot(**payload).digest
        self.store.manifest.write_text(json.dumps(manifest), encoding="utf-8")

        loaded = self.store.load()

        self.assertEqual(loaded.snapshots, ())
        self.assertEqual(len(loaded.issues), 1)

    def test_duplicate_named_record_is_quarantined(self):
        first = snapshot("first", "/project/file.py")
        second = snapshot("second", "/project/other.py")
        self.store.commit({"first": first, "second": second})
        manifest = json.loads(self.store.manifest.read_text())
        record = (
            self.store.generations
            / manifest["generation"]
            / manifest["records"][1]["file"]
        )
        payload = json.loads(record.read_text())
        payload["filename"] = first.filename
        record.write_text(json.dumps(payload), encoding="utf-8")
        manifest["records"][1]["digest"] = RecoverySnapshot(**payload).digest
        self.store.manifest.write_text(json.dumps(manifest), encoding="utf-8")

        loaded = self.store.load()

        self.assertEqual(loaded.snapshots, (first,))
        self.assertEqual(len(loaded.issues), 1)

    def test_invalid_new_generation_is_rejected_before_manifest_commit(self):
        invalid = replace(snapshot("invalid"), line_endings="sideways")

        with self.assertRaisesRegex(RecoveryWriteError, "line-ending"):
            self.store.commit({invalid.document_id: invalid})

        self.assertFalse(self.store.manifest.exists())

    def test_explicit_invalidation_prevents_stale_snapshot_restoration(self):
        first = snapshot("first")
        second = snapshot("second")
        self.store.commit({"first": first, "second": second})

        self.store.invalidate("first")
        loaded = self.store.load()

        self.assertEqual(loaded.snapshots, (second,))
        self.assertEqual(len(loaded.issues), 1)

    def test_named_document_identity_is_path_stable(self):
        self.assertEqual(
            named_document_id("/project/../project/file.py"),
            named_document_id("/project/file.py"),
        )


class Retainable:
    def __init__(self, value, *, dirty=True, save_result=True):
        self.value = value
        self.dirty = dirty
        self.save_result = save_result
        self.saved = 0
        self.discarded = 0
        self.capture_mutation = None

    def is_dirty(self):
        return self.dirty

    def recovery_snapshot(self):
        result = snapshot(self.value, text=self.value)
        if self.capture_mutation is not None:
            mutation, self.capture_mutation = self.capture_mutation, None
            mutation()
        return result

    def save_document(self):
        self.saved += 1
        if self.save_result:
            self.dirty = False
        return self.save_result

    def discard_recovery_for_exit(self):
        self.discarded += 1
        self.dirty = False


class RecoveryRetentionCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.store = RecoveryStore(Path(self.temporary.name) / "recovery")

    def tearDown(self):
        self.temporary.cleanup()

    def test_valid_unchanged_snapshot_is_reused_without_commit(self):
        document = Retainable("document")
        self.store.commit({"document": document.recovery_snapshot()})
        commits = []
        original_commit = self.store.commit
        self.store.commit = lambda *args, **kwargs: commits.append((args, kwargs))
        coordinator = RecoveryRetentionCoordinator(
            self.store, lambda _documents, _error: "cancel"
        )

        self.assertTrue(coordinator.retain((document,)))
        self.assertEqual(commits, [])
        self.store.commit = original_commit

    def test_retry_reuses_success_and_commits_after_transient_failure(self):
        document = Retainable("document")
        choices = []
        original_commit = self.store.commit
        attempts = 0

        def flaky_commit(*args, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RecoveryWriteError("disk full")
            return original_commit(*args, **kwargs)

        self.store.commit = flaky_commit
        coordinator = RecoveryRetentionCoordinator(
            self.store,
            lambda _documents, _error: choices.append("retry") or "retry",
        )

        self.assertTrue(coordinator.retain((document,)))
        self.assertEqual(attempts, 2)
        self.assertEqual(choices, ["retry"])
        self.assertEqual(self.store.load().snapshots[0].text, "document")

    def test_later_document_failure_keeps_earlier_snapshot_for_retry(self):
        first = Retainable("first")
        second = Retainable("second")
        original_commit = self.store.commit
        attempts = []

        def fail_second(snapshots, **kwargs):
            document_id = next(iter(snapshots))
            attempts.append(document_id)
            if document_id == "second":
                raise RecoveryWriteError("second failed")
            return original_commit(snapshots, **kwargs)

        self.store.commit = fail_second
        affected = []
        coordinator = RecoveryRetentionCoordinator(
            self.store,
            lambda documents, _error: affected.extend(
                document.value for document in documents
            )
            or "cancel",
        )

        self.assertFalse(coordinator.retain((first, second)))
        self.assertEqual(self.store.load().snapshots, (first.recovery_snapshot(),))
        self.assertEqual(affected, ["second"])
        self.assertEqual(attempts, ["first", "second"])

    def test_save_discard_and_cancel_failure_choices_are_distinct(self):
        for choice, expected, saved, discarded, dirty in (
            ("save", True, 1, 0, False),
            ("discard", True, 0, 1, False),
            ("cancel", False, 0, 0, True),
        ):
            with self.subTest(choice=choice):
                document = Retainable(choice)
                coordinator = RecoveryRetentionCoordinator(
                    self.store, lambda _documents, _error, choice=choice: choice
                )
                self.store.commit = lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    RecoveryWriteError("unwritable")
                )

                self.assertEqual(coordinator.retain((document,)), expected)
                self.assertEqual(document.saved, saved)
                self.assertEqual(document.discarded, discarded)
                self.assertEqual(document.dirty, dirty)

    def test_failed_save_keeps_exit_blocked(self):
        document = Retainable("document", save_result=False)
        later = Retainable("later")
        self.store.commit = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RecoveryWriteError("unwritable")
        )
        coordinator = RecoveryRetentionCoordinator(
            self.store, lambda _documents, _error: "save"
        )

        self.assertFalse(coordinator.retain((document, later)))
        self.assertTrue(document.dirty)
        self.assertEqual(document.saved, 1)
        self.assertEqual(later.saved, 1)
        self.assertFalse(later.dirty)

    def test_document_change_during_capture_never_commits_stale_snapshot(self):
        document = Retainable("before")
        document.capture_mutation = lambda: setattr(document, "value", "after")
        coordinator = RecoveryRetentionCoordinator(
            self.store, lambda _documents, _error: "cancel"
        )

        self.assertFalse(coordinator.retain((document,)))
        self.assertEqual(self.store.load().snapshots, ())


if __name__ == "__main__":
    unittest.main()
