"""Opt-in end-to-end retention acceptance harness.

The default focused suite does not launch Pyzo. Run this module with
``RUN_LOCAL_RETENTION_ACCEPTANCE=1`` to execute the test-owned Qt processes
with fresh application data and an external deadline.
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UVT = ROOT / ".codex-local" / "bin" / "uvt"
PROBE = ROOT / "spikes" / "peer_frames" / "qt_workspace_set_restore_probe.py"
DOCUMENT_PROBE = (
    ROOT / "spikes" / "peer_frames" / "qt_live_document_roundtrip_probe.py"
)
QTADS_WHEELS = tuple(
    (ROOT / "deps" / "pyside6-qtads" / "dist").glob("*.whl")
)


def _terminate_owned_group(process: subprocess.Popen[str]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        process.wait(timeout=1.0)


def run_owned_probe(
    phase: str,
    probe_dir: Path,
    *,
    expected_returncode: int = 0,
    probe: Path = PROBE,
    phase_variable: str = "PYZO_WORKSPACE_SET_PHASE",
    directory_variable: str = "PYZO_WORKSPACE_SET_PROBE_DIR",
    environment_overrides: dict[str, str] | None = None,
    deadline: float = 25.0,
):
    if not UVT.is_file():
        raise AssertionError(f"configured launcher is missing: {UVT}")
    if len(QTADS_WHEELS) != 1:
        raise AssertionError(
            f"expected one local QtAds wheel, found: {QTADS_WHEELS}"
        )
    command = [
        str(UVT),
        "run",
        "--offline",
        "--python",
        "3.12",
        "--with",
        "PySide6",
        "--with",
        str(QTADS_WHEELS[0]),
        "--with",
        "ipython",
        "python",
        str(probe),
    ]
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": os.pathsep.join(
                (str(ROOT / "deps" / "pyzo"), str(ROOT))
            ),
            "QT_QPA_PLATFORM": "offscreen",
            "PYZO_PEER_FRAMES": "1",
            phase_variable: phase,
            directory_variable: str(probe_dir),
        }
    )
    if environment_overrides:
        environment.update(environment_overrides)
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=environment,
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        output, _ = process.communicate(timeout=deadline)
    except subprocess.TimeoutExpired as error:
        _terminate_owned_group(process)
        output = error.output or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        raise AssertionError(
            f"{phase} exceeded external deadline {deadline}s:\n{output}"
        ) from error
    elapsed = time.monotonic() - started
    output = output or ""
    if process.returncode != expected_returncode:
        raise AssertionError(
            f"{phase} exited {process.returncode}, expected {expected_returncode}, "
            f"after {elapsed:.3f}s:\n{output}"
        )
    if "Traceback" in output or "PROBE TEARDOWN" in output:
        raise AssertionError(f"{phase} reported a failure:\n{output}")
    return elapsed, output


@unittest.skipUnless(
    os.environ.get("RUN_LOCAL_RETENTION_ACCEPTANCE") == "1",
    "set RUN_LOCAL_RETENTION_ACCEPTANCE=1 to launch the configured Qt harness",
)
class LocalRetentionAcceptanceTests(unittest.TestCase):
    def test_workspace_restart_retry_cancel_matrix(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-022-") as directory:
            probe_dir = Path(directory)
            expected = {
                "first": "FIRST WORKSPACES workspace-a workspace-b",
                "retry": "RETRY WORKSPACES workspace-a workspace-b",
                "verify": "VERIFY WORKSPACES workspace-a workspace-b",
                "cancel-close": "CANCEL CLOSE workspace-a workspace-b",
            }
            results = {}
            for phase, marker in expected.items():
                elapsed, output = run_owned_probe(phase, probe_dir)
                self.assertIn(marker, output)
                results[phase] = elapsed
            self.assertTrue(all(elapsed < 25.0 for elapsed in results.values()))

    def test_forced_crash_after_checkpoint_restores_retained_state(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-022-crash-") as directory:
            probe_dir = Path(directory)
            _elapsed, output = run_owned_probe(
                "crash",
                probe_dir,
                expected_returncode=42,
                probe=DOCUMENT_PROBE,
                phase_variable="PYZO_019_PHASE",
                directory_variable="PYZO_019_APP_DIR",
                environment_overrides={"PYZO_TEST_WORKSPACE_PERSISTENCE": "1"},
            )
            self.assertIn("CRASH DURABLE", output)
            _elapsed, output = run_owned_probe(
                "crash-second",
                probe_dir,
                probe=DOCUMENT_PROBE,
                phase_variable="PYZO_019_PHASE",
                directory_variable="PYZO_019_APP_DIR",
                environment_overrides={"PYZO_TEST_WORKSPACE_PERSISTENCE": "1"},
            )
            self.assertIn("CRASH RESTORED", output)

    def test_live_checkpoint_and_restart_undo_redo_roundtrip(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-022-roundtrip-") as directory:
            probe_dir = Path(directory)
            _elapsed, output = run_owned_probe(
                "first",
                probe_dir,
                probe=DOCUMENT_PROBE,
                phase_variable="PYZO_019_PHASE",
                directory_variable="PYZO_019_APP_DIR",
                environment_overrides={"PYZO_TEST_WORKSPACE_PERSISTENCE": "1"},
            )
            self.assertIn("CHECKPOINT_LATENCY", output)
            self.assertIn("HISTORY 1", output)
            _elapsed, output = run_owned_probe(
                "second",
                probe_dir,
                probe=DOCUMENT_PROBE,
                phase_variable="PYZO_019_PHASE",
                directory_variable="PYZO_019_APP_DIR",
                environment_overrides={"PYZO_TEST_WORKSPACE_PERSISTENCE": "1"},
            )
            self.assertIn("SECOND", output)

    def test_external_disk_change_preserves_retained_text_without_source_write(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-022-external-") as directory:
            probe_dir = Path(directory)
            _elapsed, output = run_owned_probe(
                "external-first",
                probe_dir,
                probe=DOCUMENT_PROBE,
                phase_variable="PYZO_019_PHASE",
                directory_variable="PYZO_019_APP_DIR",
                environment_overrides={"PYZO_TEST_WORKSPACE_PERSISTENCE": "1"},
            )
            self.assertIn("EXTERNAL DURABLE", output)
            (probe_dir / "saved.py").write_bytes(
                b"# coding: latin-1\nexternal \xe9\n"
            )
            _elapsed, output = run_owned_probe(
                "external-second",
                probe_dir,
                probe=DOCUMENT_PROBE,
                phase_variable="PYZO_019_PHASE",
                directory_variable="PYZO_019_APP_DIR",
                environment_overrides={"PYZO_TEST_WORKSPACE_PERSISTENCE": "1"},
            )
            self.assertIn("EXTERNAL CONFLICT", output)
            (probe_dir / "saved.py").write_text("disk\n", encoding="utf-8")
            _elapsed, output = run_owned_probe(
                "external-third",
                probe_dir,
                probe=DOCUMENT_PROBE,
                phase_variable="PYZO_019_PHASE",
                directory_variable="PYZO_019_APP_DIR",
                environment_overrides={"PYZO_TEST_WORKSPACE_PERSISTENCE": "1"},
            )
            self.assertIn("EXTERNAL RESOLVED", output)

    def test_failed_checkpoint_does_not_write_source_file(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-022-failure-") as directory:
            probe_dir = Path(directory)
            _elapsed, output = run_owned_probe(
                "failed-checkpoint",
                probe_dir,
                probe=DOCUMENT_PROBE,
                phase_variable="PYZO_019_PHASE",
                directory_variable="PYZO_019_APP_DIR",
                environment_overrides={"PYZO_TEST_WORKSPACE_PERSISTENCE": "1"},
            )
            self.assertIn("CHECKPOINT FAILURE VISIBLE CLOSE REFUSED", output)
            self.assertIn("CHECKPOINT RETRY COMPLETED", output)

    def test_sustained_checkpoint_reports_completion_latency_and_storage(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-022-latency-") as directory:
            _elapsed, output = run_owned_probe(
                "latency",
                Path(directory),
                probe=DOCUMENT_PROBE,
                phase_variable="PYZO_019_PHASE",
                directory_variable="PYZO_019_APP_DIR",
                environment_overrides={"PYZO_TEST_WORKSPACE_PERSISTENCE": "1"},
            )
            self.assertIn("SUSTAINED CHECKPOINT", output)
            max_latency = re.search(r"MAX_LATENCY ([0-9.]+)", output)
            writes_during_edit = re.search(
                r"WRITES_DURING_EDIT (\d+)", output
            )
            coalesced_batches = re.search(r"COALESCED_BATCHES (\d+)", output)
            history_entries = re.search(r"HISTORY_ENTRIES (\d+)", output)
            storage_bytes = re.search(r"STORAGE_BYTES (\d+)", output)
            self.assertIsNotNone(max_latency, output)
            self.assertIsNotNone(writes_during_edit, output)
            self.assertIsNotNone(coalesced_batches, output)
            self.assertIsNotNone(history_entries, output)
            self.assertIsNotNone(storage_bytes, output)
            self.assertLess(float(max_latency.group(1)), 3.0)
            self.assertGreaterEqual(int(writes_during_edit.group(1)), 1)
            self.assertGreaterEqual(int(coalesced_batches.group(1)), 1)
            self.assertGreaterEqual(int(history_entries.group(1)), 2)
            self.assertGreater(int(storage_bytes.group(1)), 0)

    def test_zero_open_workspace_restart_sequence(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-022-empty-") as directory:
            probe_dir = Path(directory)
            expected = {
                "first": "FIRST WORKSPACES workspace-a workspace-b",
                "close": "CLOSE WORKSPACES workspace-b",
                "close-empty": "CLOSE WORKSPACES",
                "reopen-empty": "REOPEN WORKSPACES workspace-a",
            }
            for phase, marker in expected.items():
                _elapsed, output = run_owned_probe(phase, probe_dir)
                self.assertIn(marker, output)


if __name__ == "__main__":
    unittest.main()
