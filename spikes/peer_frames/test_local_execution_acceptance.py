"""Opt-in, deadline-bounded real workspace Selection acceptance."""

import os
from pathlib import Path
import tempfile
import unittest

from spikes.peer_frames.test_local_retention_acceptance import ROOT, run_owned_probe


@unittest.skipUnless(
    os.environ.get("RUN_LOCAL_EXECUTION_ACCEPTANCE") == "1",
    "opt-in live two-workspace kernels",
)
class LocalExecutionAcceptanceTests(unittest.TestCase):
    def test_selection_in_real_workspace_owned_kernels(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-execution-") as directory:
            elapsed, output = run_owned_probe(
                "selection",
                Path(directory),
                probe=ROOT / "spikes/peer_frames/qt_workspace_execution_probe.py",
                deadline=35,
            )
            self.assertIn("WORKSPACE EXECUTION COMPLETE", output)
            print(f"Selection live probe passed in {elapsed:.3f}s", flush=True)
