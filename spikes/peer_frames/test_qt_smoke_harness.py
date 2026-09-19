from __future__ import annotations

import sys
import unittest

from spikes.peer_frames.qt_smoke_harness import run_bounded


class QtSmokeHarnessTests(unittest.TestCase):
    def test_success_preserves_child_exit_code(self) -> None:
        result = run_bounded(
            (sys.executable, "-c", "print('SMOKE_OK')"),
            deadline=2.0,
        )
        self.assertEqual(result, 0)

    def test_external_deadline_is_failure_and_reaps_owned_process(self) -> None:
        result = run_bounded(
            (
                sys.executable,
                "-c",
                "import time; time.sleep(5)",
            ),
            deadline=0.05,
        )
        self.assertEqual(result, 124)


if __name__ == "__main__":
    unittest.main()
