"""Safety controls for checkout reuse and subprocess descendant ownership."""

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import bootstrap
from scripts.bootstrap import checkout
from spikes.peer_frames.owned_process import owned_process, process_for_pid, terminate_owned


class LinuxArmBootstrapTests(unittest.TestCase):
    def test_native_arm_setup_downloads_sdk_and_builds_with_linux_libraries(self):
        # A Qt config alone is an incomplete Linux SDK: ICU must be installed.
        for machine in ("aarch64", "arm64"):
            with self.subTest(machine=machine), tempfile.TemporaryDirectory() as temporary:
                state = Path(temporary)
                sdk = state / "qt" / bootstrap.MANIFEST["qt"] / "gcc_arm64"
                config = sdk / "lib/cmake/Qt6/Qt6Config.cmake"
                config.parent.mkdir(parents=True)
                config.touch()
                calls = []

                def record(command, **kwargs):
                    calls.append((command, kwargs))
                    if "--wheel" in command:
                        (state / "wheels/fixture.whl").touch()

                with (
                    patch.object(bootstrap.platform, "system", return_value="Linux"),
                    patch.object(bootstrap.platform, "machine", return_value=machine),
                    patch.object(bootstrap, "STATE", state),
                    patch.object(bootstrap.shutil, "which", return_value="/usr/bin/tool"),
                    patch.object(bootstrap.shutil, "copytree"),
                    patch.object(bootstrap, "checkout"),
                    patch.object(bootstrap, "uv_command", return_value=["uvt"]),
                    patch.object(bootstrap, "runtime_python", return_value=state / "environment/bin/python"),
                    patch.object(bootstrap, "run", side_effect=record),
                    patch.object(bootstrap, "doctor"),
                ):
                    bootstrap.setup(SimpleNamespace(qt_root=None))

                install = next(command for command, _ in calls if "install-qt" in command)
                self.assertEqual(install[4:8], ["linux_arm64", "desktop", bootstrap.MANIFEST["qt"], "linux_gcc_arm64"])
                self.assertEqual(install[-3:], ["--archives", "qtbase", "icu"])
                build_env = next(kwargs["env"] for command, kwargs in calls if "--wheel" in command)
                self.assertEqual(build_env["CMAKE_PREFIX_PATH"], str(sdk))
                self.assertEqual(build_env["LD_LIBRARY_PATH"].split(os.pathsep)[0], str(sdk / "lib"))

    def test_arm_requires_native_compiler_before_checkout(self):
        with (
            patch.object(bootstrap.platform, "system", return_value="Linux"),
            patch.object(bootstrap.platform, "machine", return_value="aarch64"),
            patch.object(bootstrap.shutil, "which", side_effect=lambda name: "/usr/bin/git" if name == "git" else None),
            patch.object(bootstrap, "checkout") as clone,
        ):
            with self.assertRaisesRegex(RuntimeError, "Ubuntu build prerequisites"):
                bootstrap.setup(SimpleNamespace(qt_root=None))
            clone.assert_not_called()


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
    def test_reported_interpreter_pid_belongs_to_launched_process_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "interpreter-pid.txt"
            code = (
                "import os,pathlib,time; "
                f"pathlib.Path({str(marker)!r}).write_text(str(os.getpid())); "
                "time.sleep(30)"
            )
            with owned_process([sys.executable, "-c", code]) as process:
                deadline = time.monotonic() + 5
                while not marker.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(marker.exists(), "interpreter never reached readiness")
                reported = int(marker.read_text())
                self.assertIs(process_for_pid([process], reported), process)
                with self.assertRaises(LookupError):
                    process_for_pid([process], os.getpid())

    def test_abrupt_exit_code_is_preserved(self):
        code = (
            "from spikes.peer_frames.owned_process import abrupt_exit; "
            "print('crash ready', flush=True); abrupt_exit(42)"
        )
        with owned_process([sys.executable, "-c", code]) as process:
            output, _ = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 42, output)
            self.assertEqual(output.strip(), "crash ready")

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
            ready = Path(temporary) / "successor-ready.txt"
            child = (f"import time,pathlib; pathlib.Path({str(ready)!r}).touch(); "
                     f"time.sleep(1); pathlib.Path({str(marker)!r}).touch()")
            # Preserve ownership of the pristine upstream CRT-exec control.
            parent = ("import os,sys; from subprocess import list2cmdline; "
                      f"args=[sys.executable,'-c',{child!r}]; "
                      "os.execv(sys.executable,[list2cmdline([s]) for s in args])")
            with owned_process([sys.executable, "-c", parent]) as process:
                deadline = time.monotonic() + 5
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(ready.exists(), "exec successor never reached readiness")
                with self.assertRaises(subprocess.TimeoutExpired):
                    process.communicate(timeout=0.15)
                terminate_owned(process)
                process.communicate(timeout=5)
            time.sleep(1.1)
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
