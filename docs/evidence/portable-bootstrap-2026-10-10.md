# Portable GitHub bootstrap, 2026-10-10

Task [040](../../tasks/open/040-portable-github-bootstrap.md) implements the
user-authorized public source handoff. The bootstrap is published and native
build/import succeeds on Windows, Linux and macOS. Application acceptance is
still incomplete; the hosted failures below remain Stage 7 work.

## Published sources and reproduction

The public coordinating repository is
[joevalleyfield/toas-rhizome-pyzo-ui-smashup](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup).
Its [manifest](../../platform-sources.json) clones exact accepted commits from:

| Repository | Accepted commit |
| --- | --- |
| [Pyzo](https://github.com/joevalleyfield/pyzo/tree/codex/peer-frames) | `c956237aa6cf53a0cea21b286d8ee6518d814d8c` |
| [Binding](https://github.com/joevalleyfield/pyside6_qtads/tree/codex/peer-frames) | `764eb4a487abccb162dcbee1a8f0383916561e0e` |
| [Native QtADS](https://github.com/joevalleyfield/Qt-Advanced-Docking-System/tree/codex/peer-frames) | `244157db5bdffdf9d250e58a6edf8ee6acfd3a61` |

The bootstrap code revision is `6977f88221f6c37065d85c11e2057ec85d1fd01d`.
All three fork branches retain upstream history and licenses. Existing binding
packaging edits were preserved locally and excluded from publication. A scan of
historical blobs found no matches for the checked private-key, GitHub token and
AWS access-ID patterns; that bounded scan is not an exhaustive secret audit.

Install Python >=3.12, Git and the native prerequisites in the
[platform guide](../platform-bootstrap.md). In Windows x64 VS 2022 Developer
PowerShell:

```powershell
git clone https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup.git
cd toas-rhizome-pyzo-ui-smashup
py -3.12 scripts/bootstrap.py setup
py -3.12 scripts/bootstrap.py test
py -3.12 scripts/bootstrap.py launch
```

Use `python3` in place of `py -3.12` on Ubuntu/WSL/macOS. Setup clones all three
dependencies, creates the pinned runtime and downloads the matching Qt SDK,
then builds and installs a platform wheel. It does not require copied caches,
the Mac-local wrapper or a prebuilt Mac wheel. The runtime pins Python 3.12.13,
Qt/PySide6/shiboken 6.11.1 and IPython 9.17.1. Direct requirements and source
commits are pinned; transitive packages and system libraries can vary.

Setup refuses foreign origins, modified sources and different revisions. Build
copies use short temporary paths and leave all pinned source clones clean.
The launcher owns its fixture and descendants, including Windows exec
successors, and supports online real-kernel tests plus a visible desktop with
fresh profiles. The older macOS app-bundle launcher remains available for
macOS application-menu and Finder event acceptance.

## Fresh-clone local evidence

A fresh public Git clone at `/private/tmp/pyzo-github-bootstrap-2026-10-10`
cloned all dependencies online and compiled its own binding. A second setup
reused the clean source checkouts and rebuilt successfully. The resulting
`pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_27_0_arm64.whl` SHA256 is
`fe212387f9dbba0b847d340256cac14588b2d4945dd680b2d6a373f361f422ea`.

- [Fresh setup](portable-bootstrap-2026-10-10/fresh-setup.log) and
  [repeat setup](portable-bootstrap-2026-10-10/reuse-setup.log).
- [Complete local replay](portable-bootstrap-2026-10-10/local-complete-pass.log):
  **705 coordinated tests passed**, 28 skipped, followed by **26 live controls
  passed** in 136.31 seconds. Opt-in live tests intentionally skip in the unit
  phase and run in the separate live phase. The other skips are platform or
  capability conditions recorded in the log.
- [Final unit replay](portable-bootstrap-2026-10-10/local-final-units.log):
  705 passed, 28 skipped after the platform-relative QtADS menu assertions.
- [Independent bootstrap controls](portable-bootstrap-2026-10-10/local-bootstrap-controls.log):
  checkout safety, failure exit and descendant termination; Windows-only exec
  control is skipped on this Mac.
- [Runtime/desktop summary](portable-bootstrap-2026-10-10/runtime.json):
  visible Cocoa fixture, two workspace frames and two Ready shells, zero
  QMainWindow instances and no recorded application errors. The documented
  supervisor stop cleaned up the fixture. This was readiness observation,
  not a new physical docking/focus/drop acceptance run.

Bootstrap checks also cover failed clones leaving no partial destination and
refusal preserving edited files. Existing timeout/assertion/Qt callback failure
controls retain their deadlines and failing exits; no failure was converted to
a pass or suppressed to make CI green.

## Hosted platform results and follow-up candidates

[Hosted run 38061739001](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38061739001)
tests root `b5fa0cda5a3e2295bc60cefb5047186174e132a8` with the same manifest.
All three jobs successfully clone, compile and import the patched binding with
the pinned runtime. First application failures are retained verbatim:

| Platform | Verified outcome | First remaining failure |
| --- | --- | --- |
| Windows Server 2022 x64 | Build/import passed; 88 unit tests passed before failure | Legacy recovery migration calls `_fsync_directory`; `os.open(directory, O_RDONLY)` raises Windows PermissionError. This is persistence behavior, not fixture cleanup. |
| Ubuntu 24.04 x64 | Build/import and 705 units passed; 9 live tests passed before failure | Run variants reaches `file-script` then fails the assertion that `main_value` is absent from the restarted shell globals. |
| Hosted macOS 15 | Build/import and 705 units passed; 11 live tests passed before failure | Peer application smoke reaches ordinary Run/live-debug success, then asserts the editor debug indicator equals line 5 and exits 1. |

Logs: [Windows](portable-bootstrap-2026-10-10/ci-windows-first-failure.log),
[Linux](portable-bootstrap-2026-10-10/ci-linux-first-failure.log),
[macOS](portable-bootstrap-2026-10-10/ci-macos-first-failure.log).
These observations do not establish whether the live failures are production
lifecycle bugs or missing readiness in the probes; that diagnosis remains open.
Earlier complete Linux live replay also exposed deleted QAction callbacks and
other execution/restore failures. No assertion or deadline was weakened.

The final workflow adds independent bootstrap controls before application
acceptance, so persistence failure cannot conceal Windows descendant cleanup.
Its first isolated Windows run exposed an unquoted CRT exec argument in the
new fixture ([failure log](portable-bootstrap-2026-10-10/windows-exec-fixture-failure.log)).
The fixture now matches Pyzo's existing per-argument `list2cmdline` quoting and
requires a successor-written readiness marker before timeout/termination.
This prevents an early failed exec from masquerading as ownership evidence;
production restart code and the Job Object implementation were unchanged.
The corrected [final run 38062805425](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38062805425)
at root `6977f88221f6c37065d85c11e2057ec85d1fd01d` passes native setup/import and
independent bootstrap controls on all three platforms:
[Windows](portable-bootstrap-2026-10-10/ci-windows-bootstrap-controls.log)
passes all five, including the real ready exec successor; Linux and macOS pass
four and skip only the Windows-specific control
([Linux](portable-bootstrap-2026-10-10/ci-linux-bootstrap-controls.log),
[macOS](portable-bootstrap-2026-10-10/ci-macos-bootstrap-controls.log)).
Application acceptance remains red. Python 3.12 compilation, scoped Ruff and
local document-link checks also pass for the handoff implementation/evidence.
The final Windows run reproduces directory fsync failure after 88 passing units;
Linux again fails Run variants after 705 passing units. Hosted macOS also passes
705 units, but this time reaches post-mortem re-entry and then the 10-second
`wait-affinity-run` deadline. Both observed macOS smoke failure states remain
open; a passing local replay does not resolve the hosted failures.
Physical Windows/Linux acceptance, WSLg-versus-desktop coverage, remaining macOS
interactions and the complete Stage 7 requirement/platform matrix remain open.
The handoff task completes without changing the accepted production source pins.
