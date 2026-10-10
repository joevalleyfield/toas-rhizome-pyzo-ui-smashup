"""Safety controls for checkout reuse and subprocess descendant ownership."""

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from scripts.bootstrap import checkout
from spikes.peer_frames.owned_process import owned_process, terminate_owned


class CheckoutTests(unittest.TestCase):
    def test_clone_reuse_and_rejections_preserve_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            subprocess.run(["git", "init", source], check=True, stdout=subprocess.DEVNULL)
            (source / "tracked.txt").write_text("accepted\n")
            subprocess.run(["git", "add", "."], cwd=source, check=True)
            subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                            "commit", "-m", "Fixture"], cwd=source, check=True, stdout=subprocess.DEVNULL)
            revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
            entry = {"path": "clone", "url": str(source), "commit": revision}
            checkout(entry, root=root)
            checkout(entry, root=root)
            target = root / "clone/tracked.txt"
            target.write_text("user edit\n")
            with self.assertRaisesRegex(RuntimeError, "Refusing to change"):
                checkout(entry, root=root)
            self.assertEqual(target.read_text(), "user edit\n")
            target.write_text("accepted\n")
            with self.assertRaisesRegex(RuntimeError, "Refusing to change"):
                checkout({**entry, "commit": "0" * 40}, root=root)
            with self.assertRaisesRegex(RuntimeError, "Refusing to change"):
                checkout({**entry, "url": "https://example.invalid/other.git"}, root=root)
            self.assertEqual(target.read_text(), "accepted\n")

    def test_failed_clone_never_leaves_partial_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = {"path": "clone", "url": str(root / "missing"), "commit": "0" * 40}
            with self.assertRaises(subprocess.CalledProcessError):
                checkout(entry, root=root)
            self.assertFalse((root / "clone").exists())
            self.assertFalse(list(root.glob(".clone-*")))


class OwnedProcessTests(unittest.TestCase):
    def test_failure_exit_is_preserved(self):
        with owned_process([sys.executable, "-c", "raise SystemExit(17)"]) as process:
            process.communicate(timeout=5)
            self.assertEqual(process.returncode, 17)

    def test_timeout_stops_descendant_even_after_leader_exits(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "escaped.txt"
            child = f"import time, pathlib; time.sleep(1); pathlib.Path({str(marker)!r}).touch()"
            parent = f"import subprocess,sys; subprocess.Popen([sys.executable,'-c',{child!r}])"
            with owned_process([sys.executable, "-c", parent]) as process:
                with self.assertRaises(subprocess.TimeoutExpired):
                    process.communicate(timeout=0.15)
                terminate_owned(process)
                process.communicate(timeout=5)
            time.sleep(1.1)
            self.assertFalse(marker.exists(), "owned descendant escaped cleanup")

    @unittest.skipUnless(os.name == "nt", "real Windows Job Object control")
    def test_exec_successor_remains_owned(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "escaped-exec.txt"
            child = f"import time,pathlib; time.sleep(1); pathlib.Path({str(marker)!r}).touch()"
            parent = f"import os,sys; os.execv(sys.executable,[sys.executable,'-c',{child!r}])"
            with owned_process([sys.executable, "-c", parent]) as process:
                with self.assertRaises(subprocess.TimeoutExpired):
                    process.communicate(timeout=0.15)
                terminate_owned(process)
                process.communicate(timeout=5)
            time.sleep(1.1)
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
