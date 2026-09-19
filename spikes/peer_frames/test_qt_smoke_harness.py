from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path

from spikes.peer_frames.qt_smoke_harness import run_bounded


class QtSmokeHarnessTests(unittest.TestCase):
    def test_success_preserves_child_exit_code(self) -> None:
        result = run_bounded(
            (sys.executable, "-c", "print('SMOKE_OK')"),
            deadline=2.0,
        )
        self.assertEqual(result, 0)

    def test_external_deadline_is_failure_and_reaps_owned_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "grandchild-finished"
            child_script = (
                "import pathlib, time; time.sleep(1); "
                f"pathlib.Path({str(marker)!r}).touch()"
            )
            script = (
                "import subprocess, sys, time; "
                f"subprocess.Popen([sys.executable, '-c', {child_script!r}]); "
                "time.sleep(5)"
            )
            result = run_bounded(
                (sys.executable, "-c", script),
                deadline=0.05,
            )
            self.assertEqual(result, 124)
            time.sleep(1.2)
            self.assertFalse(
                marker.exists(),
                "a descendant escaped the harness-owned process group",
            )


if __name__ == "__main__":
    unittest.main()
