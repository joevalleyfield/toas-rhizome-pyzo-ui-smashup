"""Run Pyzo's full startup smoke with test-owned configuration and logs.

Launch through ``run_owned_probe`` with phase ``peer`` or ``legacy`` and the
default workspace-set phase/directory environment variables. Both modes use
the selected binding wheel; legacy means the non-peer QMainWindow path.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

from pyzo.util import paths


directory = Path(os.environ["PYZO_WORKSPACE_SET_PROBE_DIR"])
directory.mkdir(parents=True, exist_ok=True)
(directory / "tools").mkdir(exist_ok=True)
os.chdir(directory)
paths.prepare_appdata_appconfig_dirs = lambda: (str(directory), str(directory))
os.environ["PYZO_WORKSPACE_DIR"] = str(directory / "workspaces")
os.environ["PYZO_RECOVERY_DIR"] = str(directory / "recovery")
os.environ["PYZO_LOG"] = str(directory / "application.log")

# Avoid attaching to the user's command server. Kernel processes remain real.
commandline = types.ModuleType("pyzo.core.commandline")
commandline.is_our_server_running = lambda: False
commandline.handle_cmd_args = lambda: None
commandline.stop_our_server = lambda: None
sys.modules["pyzo.core.commandline"] = commandline

phase = os.environ["PYZO_WORKSPACE_SET_PHASE"]
if phase not in {"peer", "legacy"}:
    raise ValueError(f"unknown smoke phase: {phase}")
os.environ["PYZO_PEER_FRAMES"] = "1" if phase == "peer" else "0"
sys.argv = ["pyzolauncher.py", "--test"]

import pyzo._start
from pyzo.core.main import MainWindow
from pyzo.qt import QtWidgets


original_init = MainWindow.__init__


def inspect_host(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    windows = [
        widget for widget in QtWidgets.QApplication.topLevelWidgets()
        if isinstance(widget, QtWidgets.QMainWindow)
    ]
    if phase == "peer":
        assert not windows, windows
        assert pyzo.application is not None
    else:
        assert self in windows
        assert pyzo.application is None
    print(f"APPLICATION HOST {phase} VERIFIED", flush=True)


MainWindow.__init__ = inspect_host
failure = os.environ.get("PYZO_SMOKE_INJECT_FAILURE")
if failure == "timeout":
    MainWindow._testPeerRunAndLiveDebugTick = lambda self: False
elif failure == "exception":
    def fail_tick(self):
        raise AssertionError("injected smoke phase failure")

    MainWindow._testPeerRunAndLiveDebugTick = fail_tick
pyzo._start.start()
print(f"APPLICATION SMOKE {phase} COMPLETE", flush=True)
