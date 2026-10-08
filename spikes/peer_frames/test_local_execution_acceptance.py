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
    def test_external_file_open_routing(self):
        for phase, marker in (
            ("ingress", "WORKSPACE INGRESS COMPLETE"),
            ("ingress-empty", "WORKSPACE INGRESS EMPTY COMPLETE"),
        ):
            with tempfile.TemporaryDirectory(prefix="pyzo-workspace-ingress-") as directory:
                elapsed, output = run_owned_probe(
                    phase, Path(directory),
                    probe=ROOT / "spikes/peer_frames/qt_workspace_ingress_probe.py",
                    deadline=25,
                )
                self.assertIn(marker, output)
                self.assertNotIn("Uncaught Python exception", output)
                print(output, flush=True)
                print(f"{phase} passed in {elapsed:.3f}s", flush=True)

    def test_workspace_tools_contextual_state_and_restore(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-workspace-tools-") as directory:
            for phase, marker in (
                ("workspace-tools", "WORKSPACE TOOLS COMPLETE"),
                ("tools-restore", "WORKSPACE TOOLS RESTART COMPLETE"),
            ):
                elapsed, output = run_owned_probe(
                    phase,
                    Path(directory),
                    probe=ROOT / "spikes/peer_frames/qt_workspace_tools_probe.py",
                    deadline=35,
                )
                self.assertIn(marker, output)
                self.assertNotIn("Uncaught Python exception", output)
                self.assertNotIn("Could not restore peer workspace session", output)
                print(output, flush=True)
                print(f"{phase} passed in {elapsed:.3f}s", flush=True)

    def test_workspace_debugger_and_breakpoint_ownership(self):
        with tempfile.TemporaryDirectory(
            prefix="pyzo-workspace-debugger-"
        ) as directory:
            elapsed, output = run_owned_probe(
                "workspace-debugger",
                Path(directory),
                probe=ROOT / "spikes/peer_frames/qt_workspace_debugger_probe.py",
                deadline=35,
            )
            self.assertIn("WORKSPACE DEBUGGER COMPLETE", output)
            self.assertNotIn("Uncaught Python exception", output)
            print(output, flush=True)
            print(f"Workspace debugger live probe passed in {elapsed:.3f}s", flush=True)
            elapsed, output = run_owned_probe(
                "debugger-restore",
                Path(directory),
                probe=ROOT / "spikes/peer_frames/qt_workspace_debugger_probe.py",
                deadline=35,
            )
            self.assertIn("WORKSPACE DEBUGGER RESTART COMPLETE", output)
            self.assertNotIn("Uncaught Python exception", output)
            self.assertNotIn("Could not restore peer workspace session", output)
            print(output, flush=True)
            print(
                f"Workspace debugger fresh-process restore passed in {elapsed:.3f}s",
                flush=True,
            )

    def test_live_workspace_close_retention_boundary(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-workspace-close-") as directory:
            elapsed, output = run_owned_probe(
                "workspace-close",
                Path(directory),
                probe=ROOT / "spikes/peer_frames/qt_workspace_close_probe.py",
                deadline=35,
            )
            self.assertIn("WORKSPACE CLOSE COMPLETE", output)
            self.assertIn("PUBLICATION FAILURE PRESERVED", output)
            self.assertIn("A PROCESS EXITED", output)
            self.assertNotIn("Uncaught Python exception", output)
            print(output, flush=True)
            print(f"Workspace close live probe passed in {elapsed:.3f}s", flush=True)

    def test_native_request_result_provenance(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-native-provenance-") as directory:
            elapsed, output = run_owned_probe(
                "native-provenance",
                Path(directory),
                probe=ROOT / "spikes/peer_frames/qt_native_provenance_probe.py",
                deadline=35,
            )
            self.assertIn("NATIVE PROVENANCE COMPLETE", output)
            print(f"Native provenance live probe passed in {elapsed:.3f}s", flush=True)

    def test_all_workspace_run_variants(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-run-variants-") as directory:
            elapsed, output = run_owned_probe(
                "run-variants",
                Path(directory),
                probe=ROOT / "spikes/peer_frames/qt_workspace_run_variants_probe.py",
                deadline=35,
            )
            self.assertIn("WORKSPACE RUN VARIANTS COMPLETE", output)
            print(f"Run variants live probe passed in {elapsed:.3f}s", flush=True)

    def test_live_selection_assignments_and_correction(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-assignment-") as directory:
            elapsed, output = run_owned_probe(
                "assignment",
                Path(directory),
                probe=ROOT / "spikes/peer_frames/qt_selection_assignment_probe.py",
                deadline=35,
            )
            self.assertIn("SELECTION ASSIGNMENT COMPLETE", output)
            print(f"Assignment live probe passed in {elapsed:.3f}s", flush=True)

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
