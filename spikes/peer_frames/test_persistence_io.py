import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from spikes.peer_frames.persistence_io import fsync_directory
from spikes.peer_frames.session_recovery import RecoveryStore, RecoveryWriteError
from spikes.peer_frames.test_session_recovery import snapshot
from spikes.peer_frames.test_workspace_persistence import state
from spikes.peer_frames.workspace_persistence import (
    WorkspacePersistenceError,
    WorkspacePersistenceStore,
)


class PersistenceIOTests(unittest.TestCase):
    def test_windows_does_not_try_crt_directory_open(self):
        with patch("spikes.peer_frames.persistence_io.os.name", "nt"), patch(
            "spikes.peer_frames.persistence_io.os.open"
        ) as open_directory:
            fsync_directory("unused")
        open_directory.assert_not_called()

    def test_posix_flush_error_propagates_and_closes_descriptor(self):
        with patch("spikes.peer_frames.persistence_io.os.name", "posix"), patch(
            "spikes.peer_frames.persistence_io.os.open", return_value=42
        ), patch(
            "spikes.peer_frames.persistence_io.os.fsync", side_effect=OSError("flush failed")
        ), patch("spikes.peer_frames.persistence_io.os.close") as close:
            with self.assertRaisesRegex(OSError, "flush failed"):
                fsync_directory("unused")
        close.assert_called_once_with(42)

    def test_file_flush_failure_preserves_previous_generation_in_both_stores(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recovery = RecoveryStore(root / "recovery")
            workspace = WorkspacePersistenceStore(root / "workspace")
            cases = (
                (recovery, {"document": snapshot()}, RecoveryWriteError),
                (workspace, state(), WorkspacePersistenceError),
            )
            for store, payload, error_type in cases:
                with self.subTest(store=type(store).__name__):
                    store.commit(payload)
                    before = store.manifest.read_bytes()
                    with patch("os.fsync", side_effect=OSError("file flush failed")):
                        with self.assertRaisesRegex(error_type, "file flush failed"):
                            store.commit(payload)
                    self.assertEqual(store.manifest.read_bytes(), before)
                    self.assertFalse(store.load().issues)
