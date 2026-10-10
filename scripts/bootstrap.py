"""Clone pinned forks, build QtADS locally, test and launch an isolated desktop.

Requires Python >= 3.12, Git and the platform's C++ compiler. No shell-specific
activation, Mac-local wrapper, cached wheel or user Pyzo profile is required.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".platform"
MANIFEST = json.loads((ROOT / "platform-sources.json").read_text())


def run(command, *, cwd=ROOT, env=None, capture=False):
    print("+", subprocess.list2cmdline([str(arg) for arg in command]), flush=True)
    return subprocess.run(
        [str(arg) for arg in command], cwd=cwd, env=env, check=True,
        text=True, stdout=subprocess.PIPE if capture else None,
    ).stdout


def python_in(directory):
    return directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def uv_command():
    wrapper = ROOT / ".codex-local/bin/uvt"
    if os.name != "nt" and wrapper.is_file():
        return [str(wrapper)]
    uv = shutil.which("uv")
    if uv:
        return [uv]
    tools = STATE / "tools"
    python = python_in(tools)
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(tools)
    run([python, "-m", "pip", "install", f"uv=={MANIFEST['uv']}"])
    return [str(python), "-m", "uv"]


def checkout(entry, *, root=ROOT):
    path = root / entry["path"]
    revision = entry["commit"]
    # Git creates an empty directory for an uninitialized gitlink.
    if path.is_dir() and not any(path.iterdir()):
        path.rmdir()
    if path.exists():
        # Only reuse an independently cloned repository at the exact revision.
        # Never reset, clean or switch a user's checkout.
        top = run(["git", "rev-parse", "--show-toplevel"], cwd=path, capture=True)
        if Path(top.strip()).resolve() != path.resolve():
            raise RuntimeError(f"Not an independent repository: {path}")
        head = run(["git", "rev-parse", "HEAD"], cwd=path, capture=True).strip()
        url = run(["git", "remote", "get-url", "origin"], cwd=path, capture=True).strip()
        dirty = run(["git", "status", "--porcelain"], cwd=path, capture=True).strip()
        if head != revision or url != entry["url"] or dirty:
            raise RuntimeError(
                f"Refusing to change existing checkout: {path}. Expected clean "
                f"{entry['url']} at {revision}. Use a fresh coordinating clone."
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    # Clone to a sibling temporary directory so interruptions never leave an
    # apparently complete destination. Full history retains the pristine control.
    temporary = Path(tempfile.mkdtemp(prefix=".clone-", dir=path.parent))
    try:
        run(["git", "clone", "--no-checkout", entry["url"], temporary])
        run(["git", "checkout", "--detach", revision], cwd=temporary)
        actual = run(["git", "rev-parse", "HEAD"], cwd=temporary, capture=True).strip()
        if actual != revision:
            raise RuntimeError(f"Clone revision mismatch: {actual} != {revision}")
        temporary.rename(path)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def qt_spec():
    system, machine = platform.system(), platform.machine().lower()
    if system == "Windows" and machine in {"amd64", "x86_64"}:
        return "windows", "win64_msvc2022_64", "msvc2022_64"
    if system == "Linux" and machine in {"amd64", "x86_64"}:
        return "linux", "linux_gcc_64", "gcc_64"
    if system == "Darwin" and machine in {"arm64", "aarch64", "x86_64"}:
        return "mac", "clang_64", "macos"
    raise RuntimeError(f"No bootstrap build recipe for {system}/{machine} yet.")


def runtime_python():
    python = python_in(STATE / "environment")
    if not python.exists():
        raise RuntimeError("No prepared runtime. Run scripts/bootstrap.py setup first.")
    return python


def runtime_environment():
    environment = os.environ.copy()
    environment.update(
        PYTHONPATH=os.pathsep.join((str(ROOT / "deps/pyzo/pyzo"), str(ROOT / "deps/pyzo"), str(ROOT))),
        PYZO_PEER_FRAMES="1", PYZO_ACCEPTANCE_CURRENT_PYTHON="1",
        PYTHONFAULTHANDLER="1", PYTHONUNBUFFERED="1",
    )
    return environment


def setup(args):
    if not shutil.which("git"):
        raise RuntimeError("Install Git and put it on PATH before setup.")
    host, arch, qt_directory = qt_spec()
    if host == "windows" and not shutil.which("cl"):
        raise RuntimeError(
            "Run setup in an x64 Native Tools/Developer PowerShell for Visual "
            "Studio 2022 with Desktop development with C++ installed."
        )
    if host == "linux" and not shutil.which("g++"):
        raise RuntimeError("Install the documented Ubuntu build prerequisites first.")
    if host == "mac" and not shutil.which("clang"):
        raise RuntimeError("Install Xcode command-line tools first: xcode-select --install")
    for entry in MANIFEST["repositories"]:
        checkout(entry)
    STATE.mkdir(exist_ok=True)
    uv = uv_command()
    run([*uv, "venv", "--python", MANIFEST["python"], "--allow-existing",
         STATE / "environment"])
    python = runtime_python()
    run([*uv, "pip", "install", "--python", python, *MANIFEST["requirements"]])
    sdk = args.qt_root.resolve() if args.qt_root else STATE / "qt" / MANIFEST["qt"] / qt_directory
    sdk_complete = (sdk / "lib/cmake/Qt6/Qt6Config.cmake").is_file()
    if host == "linux":
        sdk_complete = sdk_complete and bool(list((sdk / "lib").glob("libicui18n.so*")))
    if not sdk_complete:
        if args.qt_root:
            raise RuntimeError(f"No Qt6 SDK at {sdk}")
        archives = ["qtbase", "icu"] if host == "linux" else ["qtbase"]
        run([python, "-m", "aqt", "install-qt", host, "desktop", MANIFEST["qt"],
             arch, "--outputdir", STATE / "qt", "--archives", *archives], cwd=STATE)
    environment = runtime_environment()
    environment["CMAKE_PREFIX_PATH"] = str(sdk)
    environment["PATH"] = os.pathsep.join((str(python.parent), str(sdk / "bin"), environment["PATH"]))
    if host == "linux":
        environment["LD_LIBRARY_PATH"] = os.pathsep.join(
            (str(sdk / "lib"), environment.get("LD_LIBRARY_PATH", ""))
        )
    wheels = STATE / "wheels"
    wheels.mkdir(exist_ok=True)
    for old in wheels.glob("*.whl"):
        old.unlink()
    # Short temporary source paths avoid MSVC's generated-object path limit.
    # Build copies also keep setuptools metadata out of the pinned repositories.
    with tempfile.TemporaryDirectory(prefix="pzo-") as temporary:
        source = Path(temporary)
        shutil.copytree(ROOT / "deps/pyside6-qtads", source, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".git", ".jj", "build", "dist", "__pycache__", "*.egg-info"))
        run([python, "-m", "build", "--wheel", "--no-isolation", "--outdir", wheels],
            cwd=source, env=environment)
    built = list(wheels.glob("*.whl"))
    if len(built) != 1:
        raise RuntimeError(f"Expected one built wheel: {built}")
    run([*uv, "pip", "install", "--python", python, "--reinstall", "--no-deps", built[0]])
    doctor()
    (STATE / "setup.json").write_text(json.dumps(
        {"manifest": MANIFEST, "platform": platform.platform(), "wheel": built[0].name}, indent=2
    ))
    print("Setup complete. Next: python scripts/bootstrap.py test", flush=True)


def doctor():
    code = (
        "import json, pathlib, platform, sys, PySide6, shiboken6, IPython, pyzo; "
        "from PySide6 import QtCore; from PySide6QtAds import CDockAreaWidget; "
        f"assert PySide6.__version__ == {MANIFEST['qt']!r}; "
        f"assert QtCore.qVersion() == {MANIFEST['qt']!r}; "
        f"assert shiboken6.__version__ == {MANIFEST['qt']!r}; "
        f"assert sys.version_info[:3] == {tuple(map(int, MANIFEST['python'].split('.')))!r}; "
        "assert IPython.__version__ == '9.17.1'; "
        f"assert pathlib.Path(pyzo.__file__).resolve().is_relative_to(pathlib.Path({str(ROOT / 'deps/pyzo')!r}).resolve()); "
        "assert all(hasattr(CDockAreaWidget, n) for n in ('setTabPosition', 'TabPositionLeft', 'TabPositionRight')); "
        "print(json.dumps(dict(python=sys.version, executable=sys.executable, "
        "platform=platform.platform(), qt=QtCore.qVersion(), pyside=PySide6.__version__, "
        "ipython=IPython.__version__, pyzo=pyzo.__file__), indent=2))"
    )
    run([runtime_python(), "-c", code], env=runtime_environment())


def test(args):
    doctor()
    environment = runtime_environment()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    for flag in ("RUN_LOCAL_RETENTION_ACCEPTANCE", "RUN_LOCAL_EXECUTION_ACCEPTANCE",
                 "RUN_LOCAL_COMPATIBILITY_ACCEPTANCE"):
        environment.pop(flag, None)
    reports = STATE / "reports"
    reports.mkdir(exist_ok=True)
    command = [runtime_python(), "-m", "pytest", "spikes/peer_frames", "deps/pyzo/tests",
               "scripts/tests", "-q", "-rs", f"--junitxml={reports / 'units.xml'}"]
    run(command, env=environment)
    if args.units_only:
        return
    environment.update(RUN_LOCAL_RETENTION_ACCEPTANCE="1", RUN_LOCAL_EXECUTION_ACCEPTANCE="1",
                       RUN_LOCAL_COMPATIBILITY_ACCEPTANCE="1")
    run([runtime_python(), "-m", "pytest", "spikes/peer_frames/test_local_retention_acceptance.py",
         "spikes/peer_frames/test_local_execution_acceptance.py",
         "spikes/peer_frames/test_local_profile_compatibility.py", "-q", "-s",
         f"--junitxml={reports / 'live.xml'}"], env=environment)


def launch(args):
    from spikes.peer_frames.owned_process import owned_process

    doctor()
    environment = runtime_environment()
    qpa = args.qpa or {"Windows": "windows", "Darwin": "cocoa"}.get(platform.system())
    if not qpa:
        qpa = "wayland" if environment.get("WAYLAND_DISPLAY") else "xcb"
    if qpa not in {"windows", "cocoa", "xcb", "wayland"}:
        raise RuntimeError("Visible acceptance needs windows, cocoa, xcb or wayland.")
    directory = args.directory.resolve() if args.directory else Path(tempfile.mkdtemp(prefix="pyzo-desktop-"))
    directory.mkdir(parents=True, exist_ok=True)
    environment.update(QT_QPA_PLATFORM=qpa, PYZO_PHYSICAL_QPA=qpa,
                       PYZO_PHYSICAL_DIR=str(directory), PYZO_PHYSICAL_PYTHON=str(runtime_python()))
    print(f"Fixture directory: {directory}\nQuit through the UI. Relaunch with --directory to restore.", flush=True)
    # Captured output keeps the supervisor alive across Windows exec successors.
    with (
        (directory / "console.log").open("a", encoding="utf-8") as log,
        owned_process([runtime_python(), ROOT / "spikes/peer_frames/qt_physical_macos_probe.py"],
                      cwd=ROOT, env=environment) as process,
    ):
        try:
            for line in process.stdout:
                print(line, end="", flush=True)
                log.write(line)
                log.flush()
            if process.wait() != 0:
                raise RuntimeError(f"Desktop fixture failed; see {directory / 'console.log'}")
        except KeyboardInterrupt:
            print("Stopping owned desktop fixture.", flush=True)


def main():
    if sys.version_info < (3, 12):
        raise SystemExit("Run this bootstrap with Python 3.12 or newer.")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    setup_parser = commands.add_parser("setup", help="clone forks and build a local runtime")
    setup_parser.add_argument("--qt-root", type=Path, help="existing matching Qt SDK; otherwise download it")
    test_parser = commands.add_parser("test", help="run coordinated and real-kernel controls")
    test_parser.add_argument("--units-only", action="store_true")
    launch_parser = commands.add_parser("launch", help="launch an isolated visible desktop fixture")
    launch_parser.add_argument("--directory", type=Path, help="reuse a previous fixture")
    launch_parser.add_argument("--qpa", choices=("windows", "cocoa", "xcb", "wayland"))
    commands.add_parser("doctor", help="verify the prepared runtime and patched binding")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    try:
        {"setup": setup, "test": test, "launch": launch,
         "doctor": lambda _: doctor()}[args.command](args)
    except (RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
