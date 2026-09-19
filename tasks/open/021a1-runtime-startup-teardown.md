# 021a1: Harden isolated runtime startup and teardown

## Status

IN_PROGRESS — owner Codex; started 2026-09-18. Dependency: 021a0 complete;
the remaining callback cleanup is the explicit 021a1 handoff.
Follow the [prerequisite review](../021-runtime-prerequisites.md) and
[batch contract](../local-retention-batch.md).

## Outcome

Make real single-runtime startup and smoke failures bounded, isolated, and
non-interactive so test-owned Pyzo processes cannot leave timers, command
servers, modal close prompts, or orphan Qt callbacks behind.

## Allowed writes

Pyzo `pyzo/_start.py`, `pyzo/core/main.py`, `pyzo/core/editor.py`,
`pyzo/core/workspaceRuntime.py`, and focused tests. Root
`spikes/peer_frames/application_lifecycle.py` and matching harness tests are
allowed only for the failure/cleanup contract. Evidence belongs at
`docs/evidence/task-021a1-runtime-startup-teardown.md`.

## Implementation contract

- Every real-app smoke process redirects app-data, config, tools, workspace,
  and recovery paths into test-owned directories without overriding HOME or
  touching user preferences.
- The periodic test timer stops on success and normal timeout. Callback
  failures are routed to a separate test-abort entry point that produces a
  nonzero result and invokes bounded best-effort cleanup.
- Test-abort cleanup never opens Save/Discard or shell terminate dialogs; it
  invalidates pending callbacks, disposes runtime-owned Qt state once, stops
  the command server, and leaves no test-owned shell requiring manual action.
  This path is test-only and cannot bypass production retention or shell-close
  confirmation.
- An external deadline in the launch harness supervises the process. If Qt
  hangs and the in-process timer cannot fire, the harness terminates only its
  owned process tree and records failure. Forced termination is never a pass
  for ordinary startup/shutdown acceptance.
- Passing startup still exercises default-frame creation, editor/tab/frame
  close, retained reopen, restart, and shell-close cancellation. Cleanup
  errors remain visible in logs and do not become false passes.

## Acceptance

- Repeated fresh-process runs complete within a bounded timeout with explicit
  completion markers, no callback traceback, and no surviving test-owned
  Pyzo process or modal dialog.
- Inject a callback assertion failure and verify nonzero exit plus test-abort
  cleanup; separately inject a normal close cancellation and verify the
  production confirmation path preserves usable editors/shells.
- Force the external deadline and verify termination is reported as failure,
  with no process or modal dialog left behind.
- Existing real-editor retention and workspace-session smokes remain passing.

## Stop boundary

Do not add a new process supervisor, alter user launch commands, or hide a
failed assertion behind forced success. If kernel or Qt teardown cannot be
bounded within the existing lifecycle services, return the exact owner and
cleanup seam.

## Completion evidence

Record fresh-path setup, timeout/exit behavior, process cleanup observation,
commands, logs, and separate root/Pyzo revisions at the evidence path above.
