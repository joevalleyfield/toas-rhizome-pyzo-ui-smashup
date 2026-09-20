# 021 progress evidence: workspace suspend and resume

Date: 2026-09-19
Status: IN_PROGRESS

## Reopened lifecycle correction

The application workspace-close path now performs a non-mutating shutdown
preflight, saves the current workspace set, and only then commits pane cleanup,
runtime removal, and disposal. A persistence-preflight failure discards the
prepared close and leaves the workspace and its live panes intact. The root
contract tests cover the no-mutation preflight boundary; the configured Pyzo
path uses that boundary directly.

The persistent Qt probe now treats its deadline as failure (exit 2), reports
shutdown errors as failure, and makes test-owned live-shell termination
explicit. It no longer uses forced exit status 0 to hide teardown failures.
The no-connection/closed-connection kernel cleanup path is defensive so an
incompletely initialized test-owned broker does not leave cleanup errors.

Verification for this correction:

```
50 root lifecycle/contract tests passed
8 nested Pyzo workspace/peer-view tests passed
FIRST WORKSPACES workspace-a workspace-b
CLOSE WORKSPACES workspace-b
```

The configured Qt phases exited 0 with no teardown timeout, callback
traceback, or cleanup error. The full restart/reopen matrix remains the final
acceptance run before closing 021.

The explicit reopen correction promotes retained views belonging to the
reopened workspace into live views before editor construction. A clean
four-process run passed the close-to-empty-to-reopen slice:

```
FIRST WORKSPACES workspace-a workspace-b
CLOSE WORKSPACES workspace-b
CLOSE WORKSPACES
REOPEN WORKSPACES workspace-a
```

The probe scopes its restored-view assertion to the persisted document rather
than counting unrelated bootstrap untitled editors.

021c is complete and this task is now active. The first live slice adds
explicit `application.workspaces.close(identity)` and
`application.workspaces.reopen(identity)` operations over the existing runtime
catalog and coordinator.

## Close/reopen slice

Workspace close now performs the existing document/shell confirmation
transaction, drains all remaining workspace-owned panes, removes the runtime
from the loaded coordinator set, preserves the closed workspace record and
shared resources in the durable generation, and disposes only that runtime.
Owner-scoped editor, shell, and dock teardown no longer assumes the primary
runtime.

Explicit reopen reconstructs the runtime through 021c's factory, restores its
persisted views/layout, activates it, and commits the new loaded set.

The persistent configured Qt probe
`spikes/peer_frames/qt_workspace_set_restore_probe.py` passed:

```
CLOSE WORKSPACES workspace-b
REOPEN WORKSPACES workspace-a workspace-b
```

The close phase verified A's record remained while the persisted loaded set
became B-only. A fresh process started with B only, then reopened A explicitly.
The probe uses deterministic test-owned dirty-document and shell decisions;
production confirmation paths remain unchanged.

The slice also canonicalizes the merged resource snapshot so a view identity
cannot appear in both `views` and `retained_views`; retained state wins after
closure. The probe now has a test-only bounded process deadline so a blocked
Qt teardown cannot leave its owned shell behind. This does not alter ordinary
application shutdown or close confirmation.

The next slice adds a non-persisted bootstrap runtime for the empty loaded-set
case. It keeps startup chrome routable without exposing the bootstrap identity
as a loaded workspace or writing recovery for it. The fresh configured
four-process probe passed:

```
FIRST WORKSPACES workspace-a workspace-b
CLOSE WORKSPACES workspace-b
CLOSE WORKSPACES
REOPEN WORKSPACES workspace-a
```

The last two phases prove both workspaces can be closed, the next process
starts with no loaded workspace identities, and A can be explicitly reopened
with its retained view. The logs contained no traceback or failure marker;
the known kernel cleanup warning remains harness noise.

The same persistent matrix now seeds A and B as views of one document. After A
closes, B performs a real edit followed by shared Undo/Redo; the updated
unsaved text is checkpointed. Restarting with an empty loaded set and reopening
A restores that text and the same Undo/Redo history. The four-process run again
reached all markers without a traceback.

The matrix also carries an untitled document (`path is None`), an optional
missing root for A, and an unloaded optional root for C. Those records survive
close, empty restart, and explicit A reopen without blocking restoration.

Failed restore is also isolated in the persistent probe: an injected B runtime
construction failure leaves A live, reports B in `restore_failures`, retries B
successfully, and verifies both workspaces in the following process. The run
reached `RETRY FAILURES`, `RETRY WORKSPACES`, and `VERIFY WORKSPACES` without a
traceback.

Cancelled close is covered with a live shell vote: the shell chooser returns
cancel, close is rejected before teardown, both workspace identities remain
loaded, and the persistence generation is unchanged. The probe reached
`CANCEL CLOSE workspace-a workspace-b` without a traceback.

Persistence-failure rollback is covered by the existing coordinator and store
failure-injection suites: durable commit failure restores detached topology,
reload commit failure disposes the constructed runtime, multi-workspace unload
rolls back atomically, and all five publish-boundary failures preserve the
previous manifest. The focused run passed 3 lifecycle tests plus 1 persistence
test with 5 subtests.

Live/debug shell policy and cross-workspace shell ownership are covered at the
service/backend boundary: 13 shell lifecycle tests plus 4 subtests require
confirmation for live states and preserve topology on cancellation, while the
cross-workspace transfer regression passes without changing either model.
The configured Qt cancellation probe additionally exercised a real live shell
close decision. A separate OS-level drag gesture remains outside this
headless acceptance harness.

Revisions: root `cd343460`, `18bd6c46`, `aacfaee3`, `157be4f6`, `11864c97`, `63047d5c`; Pyzo `9314e70e`,
`dcb39071`, `d76d2898`. Focused verification: root coordinator/lifecycle/
document tests — 90 passed, 12 subtests passed; Pyzo controller/runtime tests
— 5 passed; the fresh configured four-process probe reached all four markers
with no callback traceback.

## Remaining 021 acceptance

The bounded 021 acceptance matrix is now covered. Full application/OS-level
manual smoke remains a later integration gate, not part of this task’s
headless evidence.
