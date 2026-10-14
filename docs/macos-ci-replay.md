# Reproduce the macOS GitHub Actions job locally

The repository already runs `.github/workflows/platform-acceptance.yml` on
pushes to `main` and `codex/**`, pull requests and manual workflow dispatches.
The matrix builds and tests Ubuntu 24.04, Windows Server 2022 and macOS 15.
Each job builds the pinned runtime, checks bootstrap/process ownership, then
runs units and live acceptance with fail-fast behavior. Hosted CI uses
`QT_QPA_PLATFORM=offscreen`; visible desktop acceptance is separate.

## Fresh local replay

Use a fresh coordinating checkout. A development checkout can have upstream
`origin` URLs, local dependency edits and wrappers that the bootstrap correctly
refuses to replace. The replay writes only into that checkout's `.platform/`
and test-owned temporary profiles. It does not use your ordinary Pyzo profile.

```sh
jj git clone https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup.git macos-ci
cd macos-ci
python3 scripts/replay_macos_ci.py
```

Use an installed Python 3.12 or newer for the host command. The application
interpreter comes from `platform-sources.json`: currently Python 3.12.13 with
PySide6/Qt/shiboken 6.11.1 and IPython 9.17.1. Host Python is only the setup driver.

The replay uses the manifest's uv version, a minimal system PATH, fresh runtime
dependencies and the existing bootstrap commands in exactly this order:

```sh
python3 scripts/bootstrap.py setup
python3 scripts/bootstrap.py test --bootstrap-only
python3 scripts/bootstrap.py test --fail-fast
```

The script checks those commands against the workflow before execution. It
records package versions, native architecture, OS and compiler, and gives the
whole invocation the workflow's 45-minute deadline. The bootstrap and probe
assertions/deadlines are unchanged. Logs and copied XML reports have separate
timestamped directories under `.platform/replay/`; the canonical bootstrap
reports remain under `.platform/reports/`.

For this Mac's uv-managed host Python, the tools venv must use symlinked
executables. A copied executable cannot find its relative `libpython` dylib.
The replay prepares a symlinked tools environment before calling the unchanged
bootstrap. The replay requires a checkout without a project-local `uvt` wrapper,
so the bootstrap uses its pinned tools environment. Local caches live in `.platform/`.

To reuse an already prepared runtime:

```sh
python3 scripts/replay_macos_ci.py --tests-only
```

## Compare a specific hosted binary

GitHub uploads the built wheel, setup manifest and pytest XML even if acceptance
fails. Download the macOS artifact with `gh` and install its exact wheel into
the isolated runtime:

```sh
gh run download 38292168062 \
  --repo joevalleyfield/toas-rhizome-pyzo-ui-smashup \
  --name acceptance-macos-15 --dir ../ci-macos-artifact
python3 scripts/replay_macos_ci.py --tests-only --artifact ../ci-macos-artifact
```

The replay refuses a hosted artifact whose manifest differs from this checkout.
Artifact mode replaces only the isolated environment's QtADS package. Retain the
artifact locally before GitHub retention expires; its wheel is not committed here.

For historical dependency parity, obtain resolved versions from that job's
installation log, record them as a requirements constraints file and pass
`--constraints PATH` on the initial replay. The normal manifest pins top-level
requirements; its transitive requirements can change with later resolution.
The 2026-10-12 comparison matched all 61 captured package versions without an
override. The evidence directory includes that package-version snapshot.

## What this host can match

The investigated hosted run used macOS 15.7.9 arm64 and AppleClang 17.0.0. This
Mac uses macOS 27.0.1 arm64 and AppleClang 21.0.0. Runtime versions, source pins,
resolved Python packages, QPA, test ordering and the exact hosted QtADS binary
can match. OS frameworks, hardware, scheduling and the full runner image remain
different. Installing the hosted wheel removes the local compiler/build difference
for that binary but still runs it against this Mac's frameworks.

The exact hosted image is documented by [GitHub's image snapshot](https://github.com/actions/runner-images/blob/macos-15-arm64/20260907.0337/images/macos/macos-15-arm64-Readme.md).
This is a native macOS replay; a Linux container exercises a different platform.
Exact OS parity requires a macOS 15 machine or VM and is not established by this
local environment.

## Current macOS investigation

For measurements on the actual GitHub runner, the branch-scoped
`.github/workflows/macos-timing-experiment.yml` builds the same pinned runtime,
then runs `scripts/macos_hosted_experiment.py`. It records reported CPU/model,
memory availability and load before/after three rounds of the unchanged close
and debugger controls, followed by observation-only query timing runs. Every
result is retained in the `macos-hosted-timing` artifact, and any failed control
or observed exception fails the experiment. The original phase and external
probe deadlines are preserved. These observations characterize the runner;
they do not by themselves attribute an error to virtual hardware.

The post-merge hosted failure occurs before workspace teardown: the close
probe asserts that two PID evaluations returned distinct integers. Its query
helper cancels after 0.2 seconds and returns `None` for pending, running, canceled
and failed requests. A diagnostic delay of 250 ms reproduces the same assertion
with null results while both real kernels remain available. Normal observation
returns two distinct PIDs in roughly 35 ms and completes the close contract.

This establishes a timing-sensitive test boundary. The hosted failure did not
print PID values or future states, so its exact historical cause remains unproven.
The application's close behavior and the original acceptance control remain
unchanged. See [retained investigation evidence](evidence/macos-ci-replay-2026-10-12/README.md).
