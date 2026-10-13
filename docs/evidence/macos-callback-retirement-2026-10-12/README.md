# macOS callback retirement: pre-edit diagnosis

As Engineer, diagnosed the pinned source without application, dependency-pin,
acceptance-control or deadline edits. The actual hosted resource evidence is
in [the preceding experiment](../hosted-macos-timing-2026-10-12/README.md).

## Evidence and limits

Pyzo source is `93d3f97f66d00cd4964a14a44c588cc3be403935`. Diagnostics execute
the unchanged AST-extracted method bodies with minimal collaborators. Shell
diagnostics use real QTextEdit widgets and real shiboken native deletion;
the queued-event diagnostic uses the real Yoton Signal and event queue.
These are bounded method diagnostics, not full application acceptance.

- [16 callback combinations](diagnostic-results.json): eight checkpoint
  combinations and eight broker callback combinations. Ten invariants pass,
  six expose gaps. `close_committed` in this matrix is a diagnostic policy
  input; the existing callback does not inspect that synthetic marker.
- [Actual committed-close method](committed-shell-results.json): successful
  `closeShellCommitted()` leaves the old broker identity current. A later
  callback closes the context again and writes a lost-connection message.
  Minimal fixtures produce warnings when disconnecting unbound Qt signals;
  they do not model the full shell initialization.
- [16 exit transactions and queued event](ordering-results.json): both quit
  and restart across confirmation cancellation, persistence failure,
  workspace cancellation, negotiation failure, completion, cleanup failure,
  replacement failure and reentrant requests. Exit-flag assertions all pass.
  The queued broker callback survives signal unbinding and reaches native
  deletion while its Python wrapper is still alive.
- [Six checkpoint edges](checkpoint-edge-results.json): absent context,
  empty owners, unchanged snapshot, resumed cancellation and unrelated errors
  have the expected existing behavior. Synthetic retirement during snapshot
  exposes an additional reentrancy gap; this is not observed hosted causality.
- [Existing lifecycle controls](existing-lifecycle-tests.log): 18 passed.

No load, CPU limit, memory pressure or sleep was injected. Hosted resources
can affect dispatch order, but the failing lifetime states are reproducible
on the local machine independently of those constraints. The historic PID
timeout remains a distinct issue; these diagnostics do not reproduce it.

## Step 1: state enumeration

The relevant decision inputs are context existence, application-exit flag,
workspace-closing flag, owner/catalog agreement, snapshot/config changes,
broker identity, native validity and committed shell retirement. Each boolean
cross-product is either listed below or in the raw callback matrix. Events
can dispatch directly, queue before retirement or queue afterward. Unbinding
changes future subscription delivery; it cannot revoke an existing event.

| State | Conditions / ordering | Expected behavior | Existing path / coverage |
| --- | --- | --- | --- |
| C0 | Context absent | Return without work | main.py:2384; passing edge control |
| C1 | Workspace close/preflight in progress, any exit/catalog state | Return without work | `_peerClosingWorkspace` guard; four passing matrix rows |
| C2 | Idle or cancellation completed, valid owners | Snapshot; apply changed config; refresh affiliation/status | lines 2386–2400; passing matrix/edge controls |
| C3 | Idle, valid owners, unchanged snapshot or no owners | Preserve existing refresh behavior | passing edge controls |
| C4 | Exit requested: negotiation, cleaning, completed or failed committed exit; workspace-close flag false | Do not checkpoint owners while exit owns persistence/teardown | flag absent from checkpoint guard; two matrix gaps |
| C5 | Runtime already disposed while identity still present; callback enters after shutdown | No access to retired runtime | line 2396 → WorkspaceContexts.context → catalog.runtime; reproduced KeyError; hosted failure path |
| C6 | Exit canceled / preflight or negotiation fails before commitment | Clear exit flag and permit future checkpoints | actual request/coordinator: 16 exit-state assertions plus resumed edge control pass |
| C7 | Callback enters live, collaborator retires owner during snapshot | Revalidate before touching retired owner | synthetic reentrancy gap; no hosted proof; must be resolved or explicitly bounded before claiming comprehensive coverage |
| C8 | Idle identity/catalog drift without a shutdown transition | Surface an ownership inconsistency; do not catch unrelated failures globally | matrix identifies existing KeyError; unsupported application state, not evidence to silently skip owners |
| C9 | Snapshot/preferences raises unrelated exception | Preserve failure visibility | ValueError edge control passes |
| S0 | Old/foreign connection after reconnect, any native state | Ignore without closing current context or changing UI | identity guard: four passing matrix rows |
| S1 | Current connection, live native widget, no committed close; normal unexpected disconnect | Close context, show lost-connection message and read-only state | live control passes; same behavior needed after canceled close |
| S2 | Shell close has committed, native widget still valid | Retire broker callback before context/native release | actual close method leaves identity current; reproduced extra context-close and UI mutation |
| S3 | Current callback, Python wrapper alive, native Qt widget deleted | Ignore before accessing Qt cursors or widget | two matrix gaps; actual Qt deletion reproduces RuntimeError |
| S4 | Signal emitted, then unbound/retired, then dispatched | Reject previously queued callback at delivery | real Yoton event reproduces failure after unbind; unbind alone is insufficient |
| S5 | Python wrapper collected before delivery | Existing weak callback naturally no-ops | events.py:70–72 `isdead`; source coverage, not separately executed |
| S6 | Committed close collaborator fails during terminate/flush/context close | Callback must already be retired; preserve cleanup error visibility | close retirement currently absent; pre-edit coverage gap; not injected in full application |
| S7 | Live unexpected disconnect with absent context | Preserve UI error indication without context close | shell.py:2039 conditional context close; source coverage |
| S8 | Live unexpected disconnect context close raises | Preserve error reporting; do not continue unsafe UI work | shell.py:2040 exception path, caught/logged by Yoton; source coverage |

Both quit and restart share cleanup before final disposition. Reentrant exit
requests coalesce and retain the exit flag. Cleanup failures do not roll back
committed topology. Confirmation/persistence/workspace cancellation and
negotiation failure reset to idle. The matrix includes the high-risk native
deleted/current broker case even when explicit retirement was missed.

## Steps 2–3: assertions and coverage

The executed JSON files contain boolean `invariant_passed` outcomes. Assertions
for the intended repair contract are:

```python
# C0/C1/C4/C5: no owner work when checkpointing is suspended.
assert error is None and calls == []
# C2/C6: normal operation resumes after canceled exit.
assert error is None and calls == ["snapshot", "preferences", "edit", "affiliation", "status"]
# C3: unchanged state still refreshes UI without reapplying preferences.
assert error is None and calls == ["snapshot", "affiliation", "status"]
# Exit coordinator, both dispositions and all eight exercised scenarios.
assert main._peerApplicationExitRequested is (coordinator.phase.value != "idle")
# S0/S2/S3/S4/S5/S6: stale/retired callbacks perform no context or UI work.
assert error is None and calls_after == calls_before and text_after == text_before
# S1/S7: real unexpected disconnects retain visible failure handling.
assert "Lost connection with broker:" in shell.toPlainText() and shell.isReadOnly()
# C9/S8: unrelated collaborator failures remain visible.
assert reported_error is not None
```

The table maps every state to a current code path and executed or source-only
coverage. C4/C5 and S2/S3/S4 are established bug gaps. C7 and S6 are explicit
pre-edit edge gaps. Source-only S5/S7/S8 need tests if a repair touches those
paths. No claim is made that the original application passes these assertions.

## Repair boundary for confirmation

The reviewable scope is checkpoint lifetime during application exit, followed
by broker callback lifetime during committed shell close/native destruction.
Work must preserve cancellation, live unexpected-disconnect reporting,
reconnect identity checks and unrelated error visibility. It must address
queued delivery rather than relying only on signal unbinding. Verify one
repair at a time; resolve or explicitly bound C7/S6 before a coverage claim.

The state-assertion-fix-gate skill requires explicit user confirmation after
this state/assertion pass. No repair has been implemented in this diagnosis.

## Verification plan after confirmation

Promote these diagnostic contracts into focused tests against actual classes
in the isolated Pyzo fork, including native deletion and queued Yoton delivery.
Run those tests and existing application/menu/workspace lifecycle controls.
Then run unchanged local close/debugger controls and the full native CI replay.
Publish the verified dependency revision with an honest pin, and repeat the
macOS hosted experiment on that exact revision before claiming upstream repair.
No virtual-hardware timing threshold should become an application assertion.

The existing lifecycle command executed here was:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=deps/pyzo:. \
/Users/tim/Library/Caches/dev.local/state/python/toas-rhizome-pyzo-ui-smashup_6f54515f/uv-cache/archive-v0/3wdjXdO842dqwlfO/bin/python \
-m pytest spikes/peer_frames/test_application_lifecycle.py -q -p no:cacheprovider
```

## Deferred / observed out of scope

Full application and hosted verification, visible desktop acceptance,
virtual CPU/load emulation, Windows/Linux repairs and the historic short PID
wait remain unperformed in this diagnosis. The generated runtime's hidden Qt
plugin flags remain an adjacent unexplained environment issue; this pass used
the known working cached interpreter. Stage 7/task 041 and draft PR #3 remain
open. Neither source pin nor original acceptance behavior changed.
