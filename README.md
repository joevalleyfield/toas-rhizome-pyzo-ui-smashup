# Pyzo peer-frame workspace experiment

This coordinating repository contains the peer-frame adapter, retained-document
and concurrent-workspace models, acceptance probes, and implementation evidence.
It uses maintained Pyzo, PySide6-QtAds and native QtADS forks. The platform
bootstrap clones their exact accepted revisions from GitHub and builds a matching
binding locally; it does not require a wheel or cache copied from another machine.

## Quick start

Install Python 3.12 or newer and Git. Install the platform's native prerequisites
listed in [the platform guide](docs/platform-bootstrap.md). On Windows, run the
following in **Developer PowerShell for Visual Studio 2022 (x64)**:

```powershell
git clone https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup.git
cd toas-rhizome-pyzo-ui-smashup
py -3.12 scripts/bootstrap.py setup
py -3.12 scripts/bootstrap.py test
py -3.12 scripts/bootstrap.py launch
```

On Ubuntu/WSL or macOS, use `python3` in place of `py -3.12`:

```sh
git clone https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup.git
cd toas-rhizome-pyzo-ui-smashup
python3 scripts/bootstrap.py setup
python3 scripts/bootstrap.py test
python3 scripts/bootstrap.py launch
```

Setup downloads a pinned Python runtime, dependencies and matching Qt development
SDK, then compiles the patched binding. Allow several minutes and disk space for
the first build. It uses `.codex-local/bin/uvt` where available, otherwise `uv`,
and installs a local pinned uv if neither exists. No activation is required.

GitHub Actions runs the bootstrap automatically on `main`/`codex/**` pushes and
pull requests. To reproduce its macOS command sequence in a fresh checkout, use
`python3 scripts/replay_macos_ci.py`; [local CI replay](docs/macos-ci-replay.md)
explains environment recording, hosted-wheel comparison and remaining OS differences.

`launch` opens two isolated workspaces with local editors, a shared document,
file browsers and real Python shells. The printed fixture directory contains
logs, snapshots, recovery and configuration. Quit through the UI; use
`launch --directory PATH` to restore that fixture. Your normal Pyzo profile is
not used. [Manual checks and troubleshooting](docs/platform-bootstrap.md).

## Sources and evidence

[platform-sources.json](platform-sources.json) pins Python/Qt/dependencies and:

- [Pyzo fork](https://github.com/joevalleyfield/pyzo/tree/codex/peer-frames)
- [Binding fork](https://github.com/joevalleyfield/pyside6_qtads/tree/codex/peer-frames)
- [Native QtADS fork](https://github.com/joevalleyfield/Qt-Advanced-Docking-System/tree/codex/peer-frames)

Each dependency retains its upstream license and notices. See
[WORKSPACE.md](WORKSPACE.md), [the execution checklist](EXECUTION_CHECKLIST.md),
and [the local compatibility evidence](docs/evidence/profile-compatibility-2026-10-10.md)
for scope and accepted revisions. Automated builds/tests run in
[GitHub Actions](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions).
Physical Windows/Linux docking, focus, OS ingress and display behavior require
the desktop checklist; a passing offscreen run does not accept those checks.

The pinned sources combine Stage 7 polling/DPI, shutdown callback lifetime, and
scoped stale-reply acceptance fixes. See the [integration record](docs/evidence/stage7-integration-2026-10-13.md)
and current platform checks for validation. The complete Stage 7 requirement
matrix and remaining native Linux desktop checks stay open.
