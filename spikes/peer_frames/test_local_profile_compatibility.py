"""Opt-in compatibility matrix; launch with the pinned Qt acceptance runtime.

RUN_LOCAL_COMPATIBILITY_ACCEPTANCE=1 <python> -m unittest \
    spikes.peer_frames.test_local_profile_compatibility -v

The same Python executable runs every control and its real exec successor.
No implicit offline/cache requirement is added by this harness.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from pathlib import Path

from spikes.peer_frames.owned_process import owned_process
from spikes.peer_frames.test_local_retention_acceptance import (
    ROOT,
    _terminate_owned_group,
)

BASELINE = "26c2c32778dddf8fca3c1a44112941b22f075264"
PROBE = ROOT / "spikes/peer_frames/qt_profile_compatibility_probe.py"


def profile_digest(directory):
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*") if path.is_file()
    }


@unittest.skipUnless(
    os.environ.get("RUN_LOCAL_COMPATIBILITY_ACCEPTANCE") == "1",
    "opt-in pristine/legacy/peer profile controls",
)
class LocalProfileCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream = tempfile.TemporaryDirectory(prefix="pyzo-pristine-control-")
        cls.addClassCleanup(cls.upstream.cleanup)
        # jj has no archive command. Read-only git archive exports the exact
        # locally recorded baseline without updating refs or the checkout.
        archive = subprocess.run(
            ["git", "archive", BASELINE], cwd=ROOT / "deps/pyzo",
            check=True, stdout=subprocess.PIPE,
        )
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as files:
            files.extractall(cls.upstream.name, filter="data")

    def run_profile(self, mode, phase, directory, origin, *, inject_failure=False):
        source = Path(self.upstream.name) if mode == "vanilla" else ROOT / "deps/pyzo"
        environment = os.environ.copy()
        environment.update(
            PYTHONPATH=os.pathsep.join((str(source), str(ROOT))),
            QT_QPA_PLATFORM="offscreen",
            PYZO_PEER_FRAMES="1" if mode == "peer" else "0",
            PYZO_COMPAT_MODE=mode,
            PYZO_COMPAT_PHASE=phase,
            PYZO_COMPAT_ORIGIN=origin,
            PYZO_COMPAT_DIRECTORY=str(directory),
            PYZO_COMPAT_SOURCE=str(source),
            PYZO_COMPAT_INJECT_FAILURE="1" if inject_failure else "0",
            PYTHONFAULTHANDLER="1",
        )
        started = time.monotonic()
        with owned_process([sys.executable, str(PROBE)], cwd=ROOT, env=environment) as process:
            try:
                output, _ = process.communicate(timeout=45)
            except subprocess.TimeoutExpired:
                _terminate_owned_group(process)
                output, _ = process.communicate(timeout=5)
                self.fail(f"{mode}/{phase} exceeded external deadline:\n{output}")
        print(output, flush=True)
        if inject_failure:
            self.assertEqual(process.returncode, 1, output)
            self.assertIn("PROFILE FAILURE", output)
            self.assertIn("injected compatibility callback failure", output)
            self.assertNotIn("QUIT COMPLETE", output)
            return
        self.assertEqual(process.returncode, 0, output)
        for problem in ("Traceback", "PROFILE FAILURE", "Uncaught Python exception"):
            self.assertNotIn(problem, output)
        final_phase = "restarted" if phase in {"seed", "migrate"} else phase
        self.assertIn(f"PROFILE {mode} {final_phase} STATE VERIFIED", output)
        self.assertIn(f"PROFILE {mode} {final_phase} QUIT COMPLETE", output)
        self.assertIn(f"PROFILE {mode} {final_phase} KERNEL EXECUTION VERIFIED", output)
        if phase == "seed":
            self.assertIn(f"PROFILE {mode} CANCEL PRESERVED", output)
            self.assertIn(f"PROFILE {mode} RESTART REQUESTED", output)
        expected = json.loads((directory / "expected.json").read_text())
        for name, entry in expected["files"].items():
            source_file = directory / name
            self.assertEqual(source_file.read_bytes().hex(), entry["bytes"], name)
            self.assertEqual(source_file.stat().st_mtime_ns, entry["mtime_ns"], name)
        print(f"COMPATIBILITY {origin}: {mode}/{phase} {time.monotonic() - started:.3f}s", flush=True)

    def control_and_migration(self, origin):
        with tempfile.TemporaryDirectory(prefix=f"pyzo-profile-{origin}-") as temporary:
            directory = Path(temporary)
            self.run_profile(origin, "seed", directory, origin)
            self.run_profile(origin, "reopen", directory, origin)
            if origin == "peer":
                return
            self.run_profile("peer", "migrate", directory, origin)
            self.run_profile("peer", "reopen", directory, origin)
            retained = profile_digest(directory / "workspaces")
            self.run_profile(origin, "fallback", directory, origin)
            self.assertEqual(profile_digest(directory / "workspaces"), retained)
            self.run_profile("peer", "reopen", directory, origin)

    def test_vanilla_profile_migration_and_fallback(self):
        self.control_and_migration("vanilla")

    def test_legacy_profile_migration_and_fallback(self):
        self.control_and_migration("legacy")

    def test_fresh_peer_restart_and_reopen(self):
        self.control_and_migration("peer")

    def test_callback_failure_cannot_report_success(self):
        with tempfile.TemporaryDirectory(prefix="pyzo-compat-failure-") as temporary:
            self.run_profile("peer", "seed", Path(temporary), "peer", inject_failure=True)


if __name__ == "__main__":
    unittest.main()
