"""Log query timing while running an unchanged test-owned workspace probe."""

import argparse
import json
import os
from pathlib import Path
import runpy
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("probe", choices=("close", "debugger"))
args = parser.parse_args()
probe = ROOT / f"spikes/peer_frames/qt_workspace_{args.probe}_probe.py"
sys.path[:0] = [str(ROOT / "deps/pyzo/pyzo"), str(ROOT / "deps/pyzo"), str(ROOT)]

from yoton.channels.channels_reqrep import Future

original = Future.result_or_cancel


def observe(future, timeout=1):
    caller = sys._getframe(1)
    selected = caller.f_code.co_filename == str(probe)
    started = time.monotonic()
    before = future._status
    result = original(future, timeout)
    if selected:
        print("QUERY OBSERVATION", json.dumps({
            "probe": args.probe, "function": caller.f_code.co_name,
            "request": repr(future._req)[:240], "status_before": before,
            "status_after": future._status, "timeout": timeout,
            "elapsed": round(time.monotonic() - started, 6),
            "result": repr(result)[:240],
        }), flush=True)
    return result


Future.result_or_cancel = observe
runpy.run_path(str(probe), run_name="__main__")
