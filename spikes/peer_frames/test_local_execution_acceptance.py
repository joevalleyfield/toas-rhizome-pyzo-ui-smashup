"""Opt-in, deadline-bounded real workspace Selection acceptance."""

import os
import json
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from spikes.peer_frames.test_local_retention_acceptance import ROOT, run_owned_probe


@unittest.skipUnless(
    os.environ.get("RUN_LOCAL_EXECUTION_ACCEPTANCE") == "1",
    "opt-in live two-workspace kernels",
)
class LocalExecutionAcceptanceTests(unittest.TestCase):
    def test_restart_with_secondary_foreground_and_live_shells(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-restart-") as directory:
            for phase, marker in (
                ("restart-seed", "SEED"),
                ("restart-restore", "RESTORE"),
            ):
                elapsed, output = run_owned_probe(
                    phase,
                    Path(directory),
                    probe=ROOT / "spikes/peer_frames/qt_workspace_restart_probe.py",
                    deadline=25,
                )
                self.assertIn(f"WORKSPACE RESTART {marker} COMPLETE", output)
                print(f"{phase} passed in {elapsed:.3f}s", flush=True)

    def test_representative_workspace_scale(self):
        from spikes.peer_frames.workspace_persistence import WorkspacePersistenceStore

        for count in (1, 4, 8):
            with tempfile.TemporaryDirectory(prefix="pyzo-scale-") as directory:
                probe_dir = Path(directory)
                for phase in ("scale-seed", "scale-restore"):
                    elapsed, output = run_owned_probe(
                        phase, probe_dir,
                        probe=ROOT / "spikes/peer_frames/qt_workspace_scale_probe.py",
                        deadline=60,
                        environment_overrides={
                            "PYZO_SCALE_WORKSPACES": str(count),
                            "PYTHONFAULTHANDLER": "1",
                        },
                    )
                    marker = "SEED" if phase == "scale-seed" else "RESTORE"
                    self.assertIn(f"WORKSPACE SCALE {marker} COMPLETE", output)
                    self.assertNotIn("Uncaught Python exception", output)
                    self.assertNotIn("Could not restore peer workspace session", output)
                    print(output, flush=True)
                    print(f"Scale {count} {phase} passed in {elapsed:.3f}s", flush=True)
                    if phase == "scale-seed":
                        # Add a test-owned requested failure after normal quit
                        # captures the seed's actually loaded runtime set.
                        store = WorkspacePersistenceStore(probe_dir / "workspaces")
                        loaded = store.load()
                        store.commit(replace(
                            loaded.state,
                            loaded_workspace_ids=loaded.state.loaded_workspace_ids
                            + ("scale-unavailable",),
                        ))
                samples = json.loads((probe_dir / "scale-metrics.json").read_text())["samples"]
                for key in (
                    "workspaces", "timers", "panes", "frames", "documents",
                    "views", "retained_views", "modules", "signal_receivers", "callbacks",
                ):
                    self.assertEqual(len({sample[key] for sample in samples}), 1, (count, key, samples))
                if len(samples) > 1:
                    self.assertEqual(samples[-1]["widgets"], samples[-2]["widgets"], (count, samples))

    def test_application_smoke_peer_and_legacy(self):
        for phase in ("peer", "legacy"):
            with tempfile.TemporaryDirectory(prefix="pyzo-smoke-") as directory:
                elapsed, output = run_owned_probe(
                    phase, Path(directory),
                    probe=ROOT / "spikes/peer_frames/qt_application_smoke_probe.py",
                    deadline=35,
                )
                self.assertIn(f"APPLICATION SMOKE {phase} COMPLETE", output)
                self.assertNotIn("did not complete", output)
                if phase == "peer":
                    self.assertIn("Pyzo multi-kernel execution-affinity smoke test passed", output)
                print(output, flush=True)
                print(f"Application smoke {phase} passed in {elapsed:.3f}s", flush=True)

    def test_application_smoke_failures_exit_nonzero(self):
        for failure in ("timeout", "exception"):
            with tempfile.TemporaryDirectory(prefix="pyzo-smoke-failure-") as directory:
                elapsed, output = run_owned_probe(
                    "peer", Path(directory), expected_returncode=1,
                    probe=ROOT / "spikes/peer_frames/qt_application_smoke_probe.py",
                    environment_overrides={"PYZO_SMOKE_INJECT_FAILURE": failure},
                    allow_traceback=failure == "exception", deadline=35,
                )
                self.assertIn("Test callback failure; aborting test-owned run", output)
                self.assertNotIn("APPLICATION SMOKE peer COMPLETE", output)
                self.assertIn("did not complete" if failure == "timeout" else "injected smoke phase failure", output)
                print(f"Smoke {failure} rejected in {elapsed:.3f}s", flush=True)

    def test_native_workspace_restore_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-native-restore-") as directory:
            elapsed, output = run_owned_probe(
                "native-restore",
                Path(directory),
                probe=ROOT / "spikes/peer_frames/qt_native_restore_probe.py",
                environment_overrides={"PYTHONFAULTHANDLER": "1"},
            )
            self.assertIn("NATIVE RESTORE LIFECYCLE COMPLETE", output)
            self.assertNotIn("manager None", output)
            print(output, flush=True)
            print(f"Native restore lifecycle passed in {elapsed:.3f}s", flush=True)

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
