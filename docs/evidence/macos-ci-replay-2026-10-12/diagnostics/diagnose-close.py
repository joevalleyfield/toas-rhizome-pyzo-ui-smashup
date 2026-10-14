"""Observe query results in the unchanged close probe; optional synthetic delay."""

import argparse
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import time

parser = argparse.ArgumentParser()
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--delay-pid-ms", type=float, default=0)
args = parser.parse_args()
root = args.root.resolve()
probe = root / "spikes/peer_frames/qt_workspace_close_probe.py"
sys.path[:0] = [str(root / "deps/pyzo/pyzo"), str(root / "deps/pyzo"), str(root)]
os.environ.update(QT_QPA_PLATFORM="offscreen", PYZO_PEER_FRAMES="1")

from yoton.channels.channels_reqrep import Future

original = Future.result_or_cancel


def observe(future, timeout=1):
    caller = sys._getframe(1)
    selected = caller.f_code.co_filename == str(probe) and caller.f_code.co_name == "value"
    expression = caller.f_locals.get("expression") if selected else None
    channel = future._req_channel
    process_events = channel._process_events_local
    started = time.monotonic()
    if selected and "getpid()" in expression and args.delay_pid_ms:
        def delayed_events():
            if time.monotonic() - started >= args.delay_pid_ms / 1000:
                process_events()
        channel._process_events_local = delayed_events
    try:
        result = original(future, timeout)
    finally:
        channel._process_events_local = process_events
    if selected:
        print("QUERY OBSERVATION", json.dumps({
            "expression": expression, "result": result, "status": future._status,
            "elapsed": round(time.monotonic() - started, 4),
            "synthetic_delay_ms": args.delay_pid_ms,
        }), flush=True)
    return result


Future.result_or_cancel = observe
with tempfile.TemporaryDirectory(prefix="pyzo-close-observed-") as directory:
    os.environ["PYZO_WORKSPACE_SET_PROBE_DIR"] = directory
    runpy.run_path(str(probe), run_name="__main__")
