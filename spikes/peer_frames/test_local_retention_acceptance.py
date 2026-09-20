"""Opt-in end-to-end retention acceptance harness.

The default focused suite does not launch Pyzo. Run this module with
``RUN_LOCAL_RETENTION_ACCEPTANCE=1`` to execute the test-owned Qt processes
with fresh application data and an external deadline.
"""

from __future__ import annotations

import os
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
QTADS_WHEELS = tuple(
    (ROOT / "deps" / "pyside6-qtads" / "dist").glob("*.whl")
)


def _terminate_owned_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
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


def run_owned_probe(phase: str, probe_dir: Path, *, deadline: float = 25.0):
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
        str(PROBE),
    ]
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONPATH": os.pathsep.join(
                (str(ROOT / "deps" / "pyzo"), str(ROOT))
            ),
            "QT_QPA_PLATFORM": "offscreen",
            "PYZO_PEER_FRAMES": "1",
            "PYZO_WORKSPACE_SET_PHASE": phase,
            "PYZO_WORKSPACE_SET_PROBE_DIR": str(probe_dir),
        }
    )
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
    if process.returncode != 0:
        raise AssertionError(
            f"{phase} exited {process.returncode} after {elapsed:.3f}s:\n{output}"
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


if __name__ == "__main__":
    unittest.main()
