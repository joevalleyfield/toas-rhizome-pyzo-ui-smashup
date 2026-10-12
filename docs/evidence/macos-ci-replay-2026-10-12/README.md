# macOS CI investigation and local parity — 2026-10-12

Baseline coordinating commit: `a9946e653b92b1f2c88c1e42163c40d4a91b4d28`.
Pyzo pin: `93d3f97f66d00cd4964a14a44c588cc3be403935`; binding pin:
`764eb4a487abccb162dcbee1a8f0383916561e0e`; native QtADS pin:
`244157db5bdffdf9d250e58a6edf8ee6acfd3a61`.

## Hosted failure

[Run 38292168062](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38292168062),
macOS job 114954594331, uses macOS 15.7.9 arm64, image 20260907.0337.1 and
AppleClang 17.0.0. The runtime is uv-managed Python 3.12.13, not the host
actions/setup-python interpreter 3.12.10.

Bootstrap: 6 passed, 1 skipped. Units: 731 passed, 30 skipped, 2 warnings.
Live: 14 passed, 1 failed, then fail-fast stopped at workspace close.
The close probe failed before teardown at its two-distinct-integer-PIDs
assertion, without printing the values. Raw setup/XML is in `hosted-job/`.

## Diagnosis and bounds

One unchanged local close replay plus five repeats all pass. An observation-only
diagnostic also passes and prints two distinct integer PIDs, each returned in
about 35 ms. The application completes cancellation, failed publication, retry,
durable retention before A-only termination, actual A exit, unchanged B kernel,
reopen and source-byte preservation.

The query helper calls `Future.result_or_cancel(0.2)`. Actual source behavior
for the request statuses is:

| Future status | Query return if unfinished at the wait boundary | Original PID assertion |
| --- | --- | --- |
| Waiting | None, request canceled | Fails |
| Running | None, cancellation refused | Fails |
| Canceled | None | Fails |
| Error | None, exception hidden by this helper | Fails |
| Successful integer | Integer | Passes if both distinct |
| Successful equal PIDs or non-integer | Returned value | Fails |

The two-PID invariant remains
`len(set(pids)) == 2 and all(isinstance(pid, int) for pid in pids)`.
The source-status check evaluated all five Future status codes; only success
returned its PID. An unfinished response is therefore an unhandled readiness
case at this assertion, even while the kernels are otherwise valid.

`diagnostics/diagnose-close.py --delay-pid-ms 250` delays local processing of
only PID requests in the unchanged probe. It returns null PID results after
about 0.2 seconds and reproduces the same assertion. This is synthetic failure
evidence, not a natural reproduction of the hosted failure. The original probe
prints a traceback; the diagnostic launcher's process status alone is not its
acceptance result. The ordinary harness rejects such tracebacks.

The missing hosted PID values prevent proving the exact historical cause.
Timing sensitivity is demonstrated; no production close defect is established.
Potential follow-up: retain PID futures across timer ticks and assert results
only after completion, propagating canceled/error responses while preserving
the existing PID invariant and phase/external deadlines. No such repair is
included in this investigation.

## Local replay results

| Control | Fresh local build | Exact hosted wheel |
| --- | --- | --- |
| Bootstrap | 6 passed, 1 skipped | 6 passed, 1 skipped |
| Units | 731 passed, 30 skipped, 2 warnings | 731 passed, 30 skipped, 2 warnings |
| Complete live suite | 27 passed, 158.231 s | 27 passed, 157.994 s |

Both replays preserve CI ordering and fail-fast behavior. The second installs
the wheel uploaded by the failing hosted run, removing the local QtADS compiler
and build from that comparison. Both use the exact source/runtime pins and all
61 package versions captured from the hosted installation log; local resolution
matched them without constraints. QtADS is the additional built-wheel package.

Hosted wheel SHA256:
`d97465fbab762654411518064aeff0c874c31fdf22a3882f79e4acaea54232e1`.
Local wheel SHA256:
`dd80445f3444cb5dfca23fb52a712873c126b6bcfb154a858a55cb0c815ef846`.
The wheel binaries remain in local `.platform/` and downloaded artifact storage.
Raw replay logs, XML and package/environment records are in `local-build/` and
`hosted-wheel/`. Raw diagnostic/build logs are in `diagnostics/`.

## Environment parity

| Property | Hosted | Local |
| --- | --- | --- |
| Architecture | arm64 | arm64 |
| Runtime Python | 3.12.13 | 3.12.13 |
| PySide6/Qt/shiboken | 6.11.1 | 6.11.1 |
| IPython | 9.17.1 | 9.17.1 |
| Source pins and captured package versions | Recorded pins, 61 versions | All match |
| QPA | offscreen | offscreen |
| OS | 15.7.9 | 27.0.1 |
| QtADS compiler | AppleClang 17 | AppleClang 21 for local build; hosted binary for artifact replay |
| System frameworks/hardware/scheduling | Hosted image | This Mac |

The runner image's [immutable software snapshot](https://github.com/actions/runner-images/blob/macos-15-arm64/20260907.0337/images/macos/macos-15-arm64-Readme.md)
documents the OS/compiler difference. Exact macOS 15 OS/framework parity was
not attempted; this is the closest tested native runtime on the present host.

The initial tools-venv setup using uv-managed host Python failed because the
copied executable could not resolve its relative libpython dylib. A symlinked
tools venv succeeds. `scripts/replay_macos_ci.py` prepares that environment,
uses pinned uv, records source pins/packages/workflow and rejects changed
workflow commands or a project-local wrapper. Its revision helper and workflow
drift rejection were checked separately after the full replay runs.

## Scope

Application code, original probes, assertion thresholds/deadlines and the
workflow itself are unchanged. Windows belongs to the user's separate session.
No macOS 15 VM, hardware/resource emulation or visible native desktop acceptance
was performed. Task 041 and Stage 7 remain open. Replay instructions are in
[the local guide](../../macos-ci-replay.md).
