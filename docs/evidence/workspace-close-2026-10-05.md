# Real-kernel workspace closure — accepted 2026-10-05

[Task 030](../../tasks/open/030-live-workspace-close-acceptance.md) closes the
integrated closure evidence debt in [014 Stage 4](../../tasks/open/014-concurrent-workspace-implementation.md#4-workspace-execution-routing-and-shell-transfer-refusal).
The 029 sign-off was too broad: separate retention, cancel and shell-close
controls did not establish retention-before-teardown with two ready kernels.
029's native provenance acceptance stands; this dated correction supplies the
missing combined proof. Local Stage 4 is now accepted through 026–030 under
[Astra's September amendment](../local-workspace-scope-2026-09-06.md).

Root implementation: `ee98fae17fdc1d73cec0845ca65e68d13f139fdc`.
Pyzo implementation: `27b3aa04a8252a9a9a6b6858d07b691e6ddb7512`.
Starting accepted heads: root `2eeeed20`, Pyzo
`233f62debcaf619a7af9f0b9e00f3b51d44106a6`. Binding remains unchanged at the
pre-existing `b8d9c0a784db678227833ef8e545765a974ad4cb`; its packaging edits
were untouched. The pinned wheel remains
`pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl`.
Native/coordinated verification uses Python 3.12.13 and PySide6/Qt 6.11.1.

## Executed acceptance

The owned native Qt probe creates actual A/B interpreters, waits for Ready and
queries distinct PIDs and independent namespace markers. It uses dirty named
A/B buffers, an untitled A buffer and separate A/B views of A's shared resource,
with explicit local Selection assignments. B is active when A closes. Native
workspace close/reopen and real termination paths execute; only confirmation
decisions and one private manifest publication are controlled by the probe.

| Gate | Observed assertion |
| --- | --- |
| Cancel | Exact loaded owners, active owner, layouts, resources/undo/view epochs, binding objects, assignments and native shell contexts/generations survive; both PIDs live; zero termination, shell-close or editor-unbind events |
| Failed retention publication | `os.replace` of the test-owned manifest fails before publication; old manifest bytes remain authoritative; native INVALID result contains the persistence refusal; exact live snapshot survives with zero irreversible events and no pending termination authority |
| Failure → cancel → accepted retry | Each attempt invokes fresh shell confirmation; the second Cancel preserves the same objects and both live kernels |
| Durable accepted close | Every A editor-unbind, native shell-close and actual terminate call loads and verifies the same committed disk generation, containing current A/B text, clean baselines, undo/redo and A view records |
| Isolation and asynchronous exit | Only A terminates/closes; actual A `Popen.poll()` reports exit within the owned deadline; A shell/bindings and old receipts are retired; B retains its PID, native context, model generation and explicit assignment and executes another command |
| Retained resume | B edits the shared resource while A is suspended; same-process A resume restores original document/view identities and exact frame/group placement, selection/scroll, current dirty text, clean baseline and actual undo/redo; no A interpreter or old assignment is revived; old workspace/view contexts remain rejected |
| Source authority | Both named files retain their original saved bytes through cancel, failure, termination, shared edit, resume and undo/redo |

The final live run used A PID **90476**, B PID **90494** and durable generation
`73d9b98631ee4a699ac35c27a2cba595`. Its irreversible event order was two
A editor-unbinds, A native shell-close, then A terminate. The on-disk generation
was verified before each event. A exited; B remained the same live process.

## Bounded repairs exposed by the proof

- Persistence failure discarded the model preflight but left approved shell
  termination intent pending. Rollback now clears only the closing owner's
  pane intents. A focused regression preserves unrelated B approval.
- The coordinator permanently rejected retired durable workspace IDs.
  Explicit restore can now resume that identity, with a new workspace runtime
  epoch so captured old contexts stay invalid even with reused pane/frame IDs.
  Ordinary duplicate registration remains rejected.
- Native resume now admits actual retained view identities and takes text from
  the current shared resource. Optional session view-to-pane metadata restores
  surviving editor placement while pruning absent shell/tool groups and
  collapsing empty splits. Older snapshots retain the existing startup
  remapping fallback. Incomplete mappings refuse before layout commit.
- A synchronous dirty-state tab refresh could read a registry view already
  retired but not yet unbound. Main projection now returns false for that state;
  the live control rejects uncaught Qt callback exceptions.

The pre-edit assertion map and its observed-state refinements are in task 030.
The first genuine publication-failure run caught pending termination authority;
its [regression log](workspace-close-2026-10-05/regression.log) is preserved.
Probe setup corrections did not relax the native close, retention, PID,
placement or callback assertions.

## Verification and reproduction

**458 coordinated tests, 51 subtests and 14 live controls pass.** The coordinated
suite skips those 14 opt-in live cases, which pass separately, plus one stock
four-tab-side expectation that the pinned fork supersedes. The two existing Qt
high-DPI deprecation warnings remain. Full peer and maintained-fork legacy
controls pass in **11.783s** and **7.801s**. The integrated close proof passes in
**3.449s** inside the **53.69s** live suite. All ten touched Python files compile;
Ruff F and source whitespace checks pass.

Logs: [coordinated](workspace-close-2026-10-05/coordinated.log),
[all live controls](workspace-close-2026-10-05/live.log),
[closure excerpt](workspace-close-2026-10-05/close.log),
[peer](workspace-close-2026-10-05/peer.log),
[legacy](workspace-close-2026-10-05/legacy.log).

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo/pyzo:deps/pyzo:. \
  ./.codex-local/bin/uvt run --offline --python 3.12 \
  --with pytest --with PySide6 \
  --with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl \
  --with ipython python -m pytest spikes/peer_frames deps/pyzo/tests -q -rs

RUN_LOCAL_RETENTION_ACCEPTANCE=1 RUN_LOCAL_EXECUTION_ACCEPTANCE=1 PYTHONPATH=. \
  ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest \
  python -m pytest spikes/peer_frames/test_local_retention_acceptance.py \
  spikes/peer_frames/test_local_execution_acceptance.py -q -s
```

For the close control alone, select `-k close` in the execution acceptance
module. Full startup controls use `run_owned_probe`,
`qt_application_smoke_probe.py`, phases `peer` and `legacy`, fresh temporary
directories and a 35-second external deadline. The close control has the same
external deadline and 12-second phase deadlines. Command-server access is
stubbed and appdata/workspace/recovery paths are private. Teardown terminates
only test-owned kernels; temporary harness artifacts are removed after logs
are captured. Implementation commits precede this completion ledger. Nothing
was pushed.

## Remaining scope

NEXT remains **014 Stage 5**: durable breakpoint overlays, debugger/session
ownership, postmortem attribution and state-specific conservative closure
warnings. This proof accepts normal ready-kernel closure under Stage 4; it
does not accept Stage 5. Tool/config/history isolation remains Stage 6.
Physical macOS window-manager interaction and Windows/Linux native validation
remain Stage 7 acceptance debt; offscreen execution does not establish them.
The publication-failure proof covers the pre-teardown manifest gate, not a
transactional reversal of already-completed termination after a later write
failure. The legacy control uses the maintained fork, not pristine upstream.
Live shell migration, zombies, portable synchronization and broad TOAS/Rhizome
integration remain deferred. File Move/Fork UX remains a separate local slice.
