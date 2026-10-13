"""Replay the repository's macOS Actions commands in a fresh native checkout."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import venv

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/platform-acceptance.yml"
EXPECTED = [
    "python scripts/bootstrap.py setup",
    "python scripts/bootstrap.py test --bootstrap-only",
    "python scripts/bootstrap.py test --fail-fast",
]


def revision(path, env):
    if (path / ".jj").is_dir():
        jj = shutil.which("jj")
        if jj is None:
            raise RuntimeError("jj is required to inspect this checkout")
        command = [jj, "--ignore-working-copy", "log", "--no-graph", "-r", "@-", "-T", "commit_id"]
    else:
        command = ["/usr/bin/git", "rev-parse", "HEAD"]
    return subprocess.check_output(command, cwd=path, env=env, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests-only", action="store_true", help="reuse the prepared runtime")
    parser.add_argument("--artifact", type=Path, help="downloaded acceptance-macos-15 artifact directory")
    parser.add_argument("--constraints", type=Path, help="resolved package versions from a specific CI run")
    args = parser.parse_args()
    if sys.platform != "darwin" or sys.version_info < (3, 12):
        parser.error("run with Python >=3.12 on native macOS")
    commands = re.findall(r"^\s+run: (python scripts/bootstrap\.py[^\n]*)$", WORKFLOW.read_text(), re.M)
    if commands != EXPECTED:
        parser.error(f"workflow commands changed; review this replay before using it: {commands}")
    if (ROOT / ".codex-local/bin/uvt").is_file():
        parser.error("use a fresh checkout without a project-local uvt wrapper for CI parity")
    manifest = json.loads((ROOT / "platform-sources.json").read_text())
    state = ROOT / ".platform"
    reports = state / "replay" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    reports.mkdir(parents=True)
    (reports / "workflow.yml").write_text(WORKFLOW.read_text())
    # Retain system identity/certificate settings. Application, uv, Qt and build
    # overrides from a developer shell must not change the hosted-style run.
    keep = {"HOME", "USER", "LOGNAME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE",
            "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "__CF_USER_TEXT_ENCODING"}
    env = {key: value for key, value in os.environ.items() if key in keep}
    env.update(PATH="/usr/bin:/bin:/usr/sbin:/sbin", PYTHONDONTWRITEBYTECODE="1",
               UV_CACHE_DIR=str(state / "uv-cache"), PIP_CACHE_DIR=str(state / "pip-cache"))
    if args.constraints:
        env["UV_CONSTRAINT"] = str(args.constraints.resolve(strict=True))
    deadline = time.monotonic() + 45 * 60

    def run(label, command):
        log = reports / f"{label}.log"
        started = time.time_ns()
        print(f"{label}: {log}", flush=True)
        with log.open("w") as output:
            output.write(json.dumps([str(arg) for arg in command]) + "\n")
            output.flush()
            result = subprocess.run([str(arg) for arg in command], cwd=ROOT, env=env,
                                    stdout=output, stderr=subprocess.STDOUT,
                                    timeout=max(1, deadline - time.monotonic()))
        if label in {"bootstrap", "acceptance"}:
            for report in (state / "reports").glob("*.xml"):
                if report.stat().st_mtime_ns >= started:
                    shutil.copy2(report, reports / report.name)
        if result.returncode:
            raise subprocess.CalledProcessError(result.returncode, command)

    tools = state / "tools" / "bin" / "python"
    if not args.tests_only:
        if not tools.exists():
            # uv-managed CPython links its library relative to its executable.
            # A copied venv executable cannot find that library on this host.
            venv.EnvBuilder(with_pip=True, symlinks=True).create(state / "tools")
        run("tools", [tools, "-m", "pip", "install", f"uv=={manifest['uv']}"])
        run("setup", [sys.executable, "scripts/bootstrap.py", "setup"])
    python = state / "environment" / "bin" / "python"
    if not python.exists():
        parser.error("runtime absent; run once without --tests-only in a fresh checkout")
    dependency_revisions = {entry["path"]: revision(ROOT / entry["path"], env)
                            for entry in manifest["repositories"]}
    if any(dependency_revisions[entry["path"]] != entry["commit"]
           for entry in manifest["repositories"]):
        parser.error("dependency checkout differs from its manifest pin")
    artifact_hash = None
    if args.artifact:
        artifact = args.artifact.resolve(strict=True)
        hosted = json.loads((artifact / "setup.json").read_text())
        if hosted["manifest"] != manifest:
            parser.error("artifact manifest differs from this checkout")
        wheel = artifact / "wheels" / hosted["wheel"]
        artifact_hash = hashlib.sha256(wheel.read_bytes()).hexdigest()
        run("hosted-wheel", [tools, "-m", "uv", "pip", "install", "--python", python,
                             "--reinstall", "--no-deps", wheel])
    package_code = "import importlib.metadata as m,json; print(json.dumps({d.metadata['Name']:d.version for d in m.distributions()},sort_keys=True))"
    packages = json.loads(subprocess.check_output([str(python), "-c", package_code], env=env, text=True))
    compiler = subprocess.check_output(["/usr/bin/xcrun", "clang", "--version"], env=env, text=True)
    (reports / "environment.json").write_text(json.dumps({
        "platform": platform.platform(), "architecture": platform.machine(),
        "cpu_count": os.cpu_count(),
        "host_python": sys.version, "runtime_python": str(python), "compiler": compiler,
        "manifest": manifest, "packages": packages, "workflow_commands": commands,
        "source_parent": revision(ROOT, env), "dependency_revisions": dependency_revisions,
        "workflow_sha256": hashlib.sha256(WORKFLOW.read_bytes()).hexdigest(),
        "wheel_mode": "hosted-artifact" if args.artifact else "local-build",
        "artifact": str(args.artifact.resolve()) if args.artifact else None,
        "artifact_wheel_sha256": artifact_hash,
    }, indent=2) + "\n")
    run("bootstrap", [sys.executable, "scripts/bootstrap.py", "test", "--bootstrap-only"])
    run("acceptance", [sys.executable, "scripts/bootstrap.py", "test", "--fail-fast"])
    print(f"Replay passed. Evidence: {reports}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"Replay failed; retain the reported logs: {error}", file=sys.stderr)
        raise SystemExit(getattr(error, "returncode", 1))
