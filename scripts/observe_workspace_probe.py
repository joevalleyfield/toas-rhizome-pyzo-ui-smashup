"""Log query timing while running an unchanged test-owned workspace probe."""

import argparse
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("probe", choices=("close", "debugger"))
args = parser.parse_args()
probe = ROOT / f"spikes/peer_frames/qt_workspace_{args.probe}_probe.py"
sys.path[:0] = [str(ROOT / "deps/pyzo/pyzo"), str(ROOT / "deps/pyzo"), str(ROOT)]

from yoton.channels.channels_reqrep import Future

from scripts.query_observation import wrap_query

Future.result_or_cancel = wrap_query(
    Future.result_or_cancel, probe=probe, method="result_or_cancel", default_timeout=1,
)
Future.result = wrap_query(
    Future.result, probe=probe, method="result", default_timeout=None,
)
runpy.run_path(str(probe), run_name="__main__")
