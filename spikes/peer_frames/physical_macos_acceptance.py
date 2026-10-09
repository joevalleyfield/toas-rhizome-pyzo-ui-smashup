"""Build an isolated Cocoa acceptance app; open the printed .app in Finder.

Use --directory with the previous fixture directory to replay retained state.
The embedded native executable keeps macOS accessibility and real Restart tied
to the same application bundle; kernels use the pinned Python binary.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def runtime_paths(wheel):
    command = [
        str(ROOT / ".codex-local/bin/uvt"),
        "run",
        "--offline",
        "--python",
        "3.12",
        "--with",
        "PySide6",
        "--with",
        str(wheel),
        "--with",
        "ipython",
        "python",
        "-c",
        "import json,os,sys; print(json.dumps(dict(executable=os.path.realpath(sys.executable),"
        'path=[p for p in sys.path if p.endswith("site-packages")])) )',
    ]
    output = subprocess.check_output(command, cwd=ROOT, text=True)
    runtime = json.loads(output.splitlines()[-1])
    # uvt's builds-v0 temporary environment disappears when the command ends.
    # Its persistent archive-v0 dependency environment remains available.
    runtime["path"] = [p for p in runtime["path"] if Path(p).is_dir()]
    if not any("archive-v0" in p for p in runtime["path"]):
        raise SystemExit("No persistent pinned dependency environment found.")
    return runtime


def build_bundle(directory, runtime):
    # Keep LaunchServices startup independent of access to the user's Documents
    # directory. These are test-owned copies of the current reviewed sources.
    stage = directory / "runtime"
    shutil.copytree(
        ROOT / "deps/pyzo/pyzo",
        stage / "pyzo",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copytree(
        ROOT / "spikes/peer_frames",
        stage / "spikes/peer_frames",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    bundle = directory / "Pyzo Physical Acceptance.app"
    contents = bundle / "Contents"
    executable_dir = contents / "MacOS"
    executable_dir.mkdir(parents=True, exist_ok=True)
    info = dict(
        CFBundleIdentifier="org.pyzo.physical.acceptance.native",
        CFBundleName="Pyzo Physical Acceptance",
        CFBundleDisplayName="Pyzo Physical Acceptance",
        CFBundleExecutable="PyzoPhysical",
        CFBundlePackageType="APPL",
        CFBundleVersion="3",
        NSHighResolutionCapable=True,
        CFBundleDocumentTypes=[
            dict(
                CFBundleTypeName="Python fixture",
                CFBundleTypeRole="Editor",
                CFBundleTypeExtensions=["py"],
                LSHandlerRank="Alternate",
            )
        ],
    )
    with (contents / "Info.plist").open("wb") as stream:
        plistlib.dump(info, stream)
    base = Path(runtime["executable"]).parent.parent
    environment = dict(
        PYTHONPATH=os.pathsep.join([str(stage), *runtime["path"]]),
        PYZO_PHYSICAL_DIR=str(directory),
        PYZO_PHYSICAL_PYTHON=runtime["executable"],
        PYZO_PEER_FRAMES="1",
        QT_QPA_PLATFORM="cocoa",
        PYTHONFAULTHANDLER="1",
    )
    settings = "\n".join(
        f"  setenv({json.dumps(k)}, {json.dumps(v)}, 1);"
        for k, v in environment.items()
    )
    source = directory / "launcher.c"
    source.write_text(f"""#include <Python.h>
#include <stdlib.h>
#include <stdio.h>
int main(int argc, char **argv) {{
  freopen({json.dumps(str(directory / "process.log"))}, "a", stdout);
  freopen({json.dumps(str(directory / "process.log"))}, "a", stderr);
{settings}
  PyConfig config;
  PyConfig_InitPythonConfig(&config);
  PyStatus status = PyConfig_SetString(&config, &config.home, L{json.dumps(str(base))});
  if (PyStatus_Exception(status)) Py_ExitStatusException(status);
  char *args[] = {{argv[0], {json.dumps(str(stage / "spikes/peer_frames/qt_physical_macos_probe.py"))}}};
  status = PyConfig_SetBytesArgv(&config, 2, args);
  if (PyStatus_Exception(status)) Py_ExitStatusException(status);
  status = Py_InitializeFromConfig(&config);
  PyConfig_Clear(&config);
  if (PyStatus_Exception(status)) Py_ExitStatusException(status);
  return Py_RunMain();
}}
""")
    subprocess.run(
        [
            "xcrun",
            "clang",
            str(source),
            "-I" + str(base / "include/python3.12"),
            "-L" + str(base / "lib"),
            "-lpython3.12",
            "-Wl,-rpath," + str(base / "lib"),
            "-o",
            str(executable_dir / "PyzoPhysical"),
        ],
        check=True,
    )
    (directory / "launch.json").write_text(
        json.dumps(
            dict(bundle=str(bundle), runtime=runtime, environment=environment), indent=2
        )
    )
    return bundle


def main():
    if sys.platform != "darwin":
        raise SystemExit("This physical acceptance launcher requires macOS.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args()
    directory = (
        args.directory or Path(tempfile.mkdtemp(prefix="pyzo-physical-"))
    ).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    snapshot = directory / "snapshot.json"
    if snapshot.exists():
        pid = json.loads(snapshot.read_text())["pid"]
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        else:
            raise SystemExit(
                "Quit the previous fixture through its UI before rebuilding."
            )
    wheels = list((ROOT / "deps/pyside6-qtads/dist").glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit("Expected exactly one pinned local QtADS wheel.")
    bundle = build_bundle(directory, runtime_paths(wheels[0]))
    print(
        json.dumps(
            dict(
                bundle=str(bundle),
                directory=str(directory),
                snapshot=str(snapshot),
                log=str(directory / "process.log"),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
