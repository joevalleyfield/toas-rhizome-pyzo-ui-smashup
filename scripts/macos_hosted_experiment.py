"""Record runner resources and repeat unchanged macOS close/debugger controls."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.bootstrap import runtime_environment
from spikes.peer_frames.owned_process import owned_process, terminate_owned

NODES = [
    "spikes/peer_frames/test_local_execution_acceptance.py::LocalExecutionAcceptanceTests::test_live_workspace_close_retention_boundary",
    "spikes/peer_frames/test_local_execution_acceptance.py::LocalExecutionAcceptanceTests::test_workspace_debugger_and_breakpoint_ownership",
]


def resources():
    memory = psutil.virtual_memory()
    observed = {}
    for key in ("hw.model", "machdep.cpu.brand_string", "hw.physicalcpu", "hw.logicalcpu", "hw.memsize"):
        result = subprocess.run(["/usr/sbin/sysctl", "-n", key], capture_output=True, text=True)
        observed[key] = result.stdout.strip() if result.returncode == 0 else None
    return {"utc": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(),
            "architecture": platform.machine(), "python": sys.version,
            "cpu_count": psutil.cpu_count(), "physical_cpu_count": psutil.cpu_count(logical=False),
            "memory_total": memory.total, "memory_available": memory.available,
            "load_average": os.getloadavg(), "reported_hardware": observed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, choices=range(1, 6), default=3)
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("this experiment requires native macOS")
    reports = ROOT / ".platform/hosted-experiment" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    reports.mkdir(parents=True)
    (reports / "identity.json").write_text(json.dumps({
        "source_sha": os.environ.get("GITHUB_SHA"), "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "manifest": json.loads((ROOT / "platform-sources.json").read_text()),
        "initial_resources": resources(),
    }, indent=2) + "\n")
    inherited = runtime_environment()
    keep = {"HOME", "USER", "LOGNAME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE",
            "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "__CF_USER_TEXT_ENCODING",
            "PYTHONPATH", "PYZO_PEER_FRAMES", "PYZO_ACCEPTANCE_CURRENT_PYTHON",
            "PYTHONFAULTHANDLER", "PYTHONUNBUFFERED"}
    environment = {key: value for key, value in inherited.items() if key in keep}
    environment.update(PATH=str(Path(sys.executable).parent) + ":/usr/bin:/bin:/usr/sbin:/sbin",
                       PYTHONDONTWRITEBYTECODE="1")
    environment.update(QT_QPA_PLATFORM="offscreen", RUN_LOCAL_EXECUTION_ACCEPTANCE="1")
    results = []

    def run(label, command, *, deadline, require_marker=None, extra=None):
        before = resources()
        env = environment.copy()
        env.update(extra or {})
        started = time.monotonic()
        timed_out = False
        with owned_process(command, cwd=ROOT, env=env) as process:
            try:
                output, _ = process.communicate(timeout=deadline)
            except subprocess.TimeoutExpired:
                timed_out = True
                terminate_owned(process)
                output, _ = process.communicate(timeout=5)
        output = output or ""
        (reports / f"{label}.log").write_text(output)
        forbidden = ("Traceback", "Uncaught Python exception", "PROBE TEARDOWN", "Exception while handling event")
        diagnostic_errors = [marker for marker in forbidden if marker in output] if require_marker else []
        passed = not timed_out and process.returncode == 0
        if require_marker:
            passed = passed and require_marker in output and not diagnostic_errors
        result = {"label": label, "returncode": process.returncode, "passed": passed,
                  "timed_out": timed_out, "elapsed": round(time.monotonic() - started, 4),
                  "command": command, "resource_before": before, "resource_after": resources(),
                  "diagnostic_errors": diagnostic_errors}
        results.append(result)
        (reports / "results.json").write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps({key: result[key] for key in ("label", "passed", "returncode", "elapsed", "timed_out")}), flush=True)

    for index in range(1, args.rounds + 1):
        run(f"unchanged-{index}", [sys.executable, "-m", "pytest", *NODES, "-q", "-s",
            f"--junitxml={reports / f'unchanged-{index}.xml'}"], deadline=120)
    for probe, phase, marker in [("close", "workspace-close", "WORKSPACE CLOSE COMPLETE"),
                                 ("debugger", "workspace-debugger", "WORKSPACE DEBUGGER COMPLETE")]:
        with tempfile.TemporaryDirectory(prefix="pyzo-hosted-observation-") as directory:
            run(f"observed-{probe}", [sys.executable, str(ROOT / "scripts/observe_workspace_probe.py"), probe],
                deadline=35, require_marker=marker,
                extra={"PYZO_WORKSPACE_SET_PHASE": phase, "PYZO_WORKSPACE_SET_PROBE_DIR": directory})
    print(f"Hosted experiment evidence: {reports}", flush=True)
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
