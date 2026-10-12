# Reproduce the peer-frame workspace on another platform

## One-time prerequisites

All platforms need Git on PATH and Python 3.12 or newer to run the bootstrap.
The prepared application runtime is separately pinned to Python 3.12.13,
PySide6/Qt/shiboken 6.11.1 and IPython 9.17.1.

**Windows x64:** install Visual Studio 2022 Build Tools (or Visual Studio 2022)
with **Desktop development with C++**, including the MSVC compiler and Windows
SDK. Open **Developer PowerShell for VS 2022** with the x64 toolchain, or an
**x64 Native Tools Command Prompt**. `cl` must be on PATH. Use native Windows
Python for the Windows checks. WSL Python produces Linux evidence.

**Ubuntu 24.04 x64, including WSL2 and desktop VMs:** install the native packages:

```sh
sudo apt-get update
sudo apt-get install -y build-essential clang libclang-dev libgl1-mesa-dev libegl1 libopengl0 libxkbcommon-dev libxkbcommon-x11-0 libxcb-cursor0 libxcb-keysyms1 libxcb-icccm4 libxcb-image0 libxcb-render-util0 libxcb-xinerama0 libxcb-xkb1 libx11-xcb1 libfontconfig1 libdbus-1-3
```

Install Python 3.12 and Git if absent. Keep a separate Linux checkout/environment
inside WSL, for example under `~/src`. WSLg supports visible applications; a
desktop VM supplies a Linux desktop for final physical acceptance. Docker can
run offscreen checks, but needs a separately configured display/desktop for
interactive checks. [Microsoft WSLg guidance](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps).

**macOS arm64/x64:** install Xcode command-line tools (`xcode-select --install`).
The new console launcher supports Cocoa. The existing
[application-bundle launcher](physical-macos-workspace-checklist.md) remains the
fixture for macOS application-menu and Finder-delivered file-open checks.

The initial build recipes cover Windows x64, Ubuntu x64 and macOS arm64/x64.
ARM Windows/Linux builds are not included. The Qt SDK/compiler combinations
follow [Qt 6.11's supported platforms](https://doc.qt.io/qt-6.11/supported-platforms.html).

## Clone, build, test, launch

Clone the coordinating repository. You do not need to clone the three dependencies
yourself or initialize submodules: the script clones all three pinned forks,
including the native source at the binding's recorded submodule revision.

```sh
git clone https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup.git
cd toas-rhizome-pyzo-ui-smashup
python3 scripts/bootstrap.py setup
python3 scripts/bootstrap.py test
python3 scripts/bootstrap.py launch
```

On Windows replace `python3` with `py -3.12`. `setup` uses online downloads by
default. It prepares `.platform/environment`, downloads a Qt SDK under
`.platform/qt`, builds a temporary source copy at a short path, writes a wheel under
`.platform/wheels`, and installs it. It never builds inside the pinned clones.
An existing matching SDK can be supplied with `setup --qt-root PATH` (the root
containing `lib/cmake/Qt6/Qt6Config.cmake`).

Existing dependencies are reused only if their origin URL, revision and clean
status match the manifest. Setup refuses to reset or clean your edits. For a
different source pin or interrupted manual checkout, use a fresh coordinating
clone. Full Pyzo history preserves the pristine upstream control used by the
profile migration matrix. Source commits are pinned; resolved transitive package
dependencies and OS libraries can vary between platforms.

`test` first runs coordinated model/Qt/unit tests, then opt-in retention,
execution and upstream/legacy/peer compatibility controls with real kernels and
external deadlines. It selects the prepared Python directly, so the live probes
need no uv cache and no additional environment variables. Reports are written
to `.platform/reports`. `test --units-only` runs the first suite.
`test --bootstrap-only` independently checks safe checkout reuse and termination
of owned descendants, including Windows exec successors. CI runs these controls
before application tests, so an application failure cannot conceal their result.
`test --fail-fast` stops at the first failure; CI uses that option so a new
platform's first failing control is available promptly. The default command
continues through the complete live suite and preserves each failure.
`doctor` checks dependency versions, source import identity and patched tab APIs.

## Visible acceptance

`launch` uses a fresh temporary profile and prints its directory. It keeps a
supervisor running, streams logs and owns all fixture descendants. Quit through
the application's UI; Ctrl+C stops the owned fixture. To check persistence:

```sh
python3 scripts/bootstrap.py launch --directory /absolute/path/to/printed/fixture
```

Use the corresponding Windows path in PowerShell. The launcher explicitly
selects `windows` or `cocoa`; on Linux it selects `wayland` when WAYLAND_DISPLAY
is present, otherwise `xcb`. To exercise another available desktop backend use
`launch --qpa xcb` or `launch --qpa wayland`. The fixture asserts that Qt actually
selected the requested platform. No offscreen launch is accepted as visible
desktop evidence.

Wait for Physical A/B and real shell prompts, then record OS, architecture,
display backend, scaling and the fixture directory. Verify:

1. Local typing and File/New affect the invoking workspace. Shared-file edits
   and undo propagate to both views; cursor/focus remain local.
2. Run/Selection/debug/postmortem use the local shell. Close the last shell and
   recreate one through the shell menu. Create another workspace through its menu.
3. Move tabs, split groups, float and redock. Try all four tab sides and a foreign
   workspace drop; ownership must remain correct and refused transfers visible.
4. Cancel and confirm pane/frame closure with dirty editors and live shells.
   Close every frame and check the platform's command availability/exit policy.
5. Open the fixture's `ingress.py` through File/Open and drag it from the desktop
   file manager. Verify the foreground workspace receives it. Record separately
   whether actual OS file-association delivery was configured and exercised.
6. Cancel Quit; then Quit/Restart with retained unsaved text. Reopen the same
   fixture and verify text, layout, workspace affiliation, pin and tool state.
7. Exercise keyboard traversal, shortcuts, menus, display scaling and available
   multiple monitors. Record WSLg separately from a full Linux desktop session.

`console.log`, `events.jsonl`, `snapshot.json` and `application.log` capture
observations. Automated CI does not perform these physical interactions.

## Troubleshooting

### Windows persistence guarantees

Recovery and workspace records and manifests are flushed with `os.fsync` before
same-volume `os.replace` publication. Windows cannot use the CRT's `os.open` /
`os.fsync` on directories, so the stores omit that directory barrier on Windows.
POSIX still flushes directories and propagates barrier failures. File write,
file flush, and replacement failures still fail the transaction on both platforms.
This supports normal exit/restart and process-crash recovery on Windows, but
does not establish the POSIX directory-entry durability guarantee under power
loss. Physical power-loss/storage-device acceptance remains unverified.

The bootstrap can also be invoked with an installed Python 3.12 executable when
the optional Windows `py` launcher is absent. For a uv-managed installation,
`uv run --python 3.12 scripts/bootstrap.py setup` is an alternative; use the same
prefix for `test` and `launch`, in the x64 VS 2022 developer shell.
Use a host interpreter outside `.platform/environment` for `setup`: Windows
locks a running executable, so setup cannot recreate its own active environment.

Symlink alias handling is an optional filesystem affordance. On Windows,
controls that require a symlink skip when the current account cannot create one
(WinError 1314). Developer Mode and additional symlink privileges are not Windows
acceptance prerequisites. Accounts that already support symlinks still exercise
those controls. Other filesystem errors remain failures. The live ingress probe
omits only its symlink subcontrol and continues ordinary file-open coverage.

### Integrated Windows source revision

The Pyzo pin includes the Windows repairs in commit
`da26a6c7c07e28d947f193215368e3723065a684` on the fork's
`codex/stage7-acceptance` branch. Fresh setup clones that commit directly; no
manual dependency patch is required. Existing clean checkouts at an older pin
are preserved and rejected by setup; use a fresh coordinating clone as directed.
The retained patch is historical evidence against the former pin, not an extra
step to apply over the current source revision.

### Windows restart controls

The patched application starts a successor process with the original arguments
and standard streams, then exits the Qt event loop normally. This avoids the
CRT/DLL teardown crash reproduced by Windows `os.execv`; POSIX retains exec
replacement. Restart acceptance requires the successor's restored state and
real-kernel execution, not just a clean parent exit.

The compatibility suite also exports an unchanged upstream baseline
(`26c2c32778dddf8fca3c1a44112941b22f075264`). Its native Windows restart still
crashes in `os.execv` with this runtime. That control remains a reported failure.
A separate pristine save/quit control verifies migration into the patched peer
application and fallback without changing upstream sources or suppressing the
restart failure. See the Windows replay task and retained evidence for results.

### Common failures

- **Compiler missing:** use the Windows x64 developer shell, Ubuntu prerequisites,
  or Xcode tools described above; setup does not install system compilers.
- **Qt download/build error:** retain the console output, retry online, or supply
  an existing matching SDK. Do not substitute the Mac wheel or a stock QtADS wheel.
- **Linux display/plugin error:** use a functioning WSLg/desktop session and the
  matching `--qpa`; check the Ubuntu runtime packages above. Do not set
  QT_QPA_PLATFORM=offscreen for physical acceptance.
- **Checkout rejected:** move to a fresh clone. The script deliberately preserves
  dirty files, foreign origins and different revisions.
- **Automated failure:** reports identify the platform and test. A Windows/Linux
  failure is evidence to diagnose, not a reason to mark that platform accepted.
