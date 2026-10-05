# Live Selection assignments — 2026-10-05

Task [027](../../tasks/open/027-live-selection-assignments.md) is accepted under
“Take the next.” Astra's September amendment remains normative. This is current
Codex acceptance of the bounded Selection-assignment slice; Stage 4 as a whole
remains open.

| Boundary | Revision |
| --- | --- |
| Starting coordinating root | `c666da458f6c70f0cbf1d1b495426e09d9f86501` |
| Starting Pyzo | `3abb51c5ffaad46d7d6053c9e32bada071eaa664` |
| Root epoch model / actual-kernel proof | `58f689f709527bc819c13389d9230ea9e7a6b2d7` |
| Pyzo assignments / chooser / connection guard | `19d619a09667b92253d2c42c40903b356dcfa019` |
| Unchanged binding | `b8d9c0a7`, local dev10 wheel |

Root `58f689f7` requires Pyzo `19d619a0` for the new live probe. Completion and
queue cleanup follow these implementation commits. No QtADS/binding or TOAS/
Rhizome edits. No shell migration, zombies, synchronization or broad integration.
Nothing pushed.

## Behavior and removed assumptions

Run > Selection target lists only the invoking live view's eligible local shells,
with numbered names to distinguish duplicates. Workspace foreground clears an
assignment; a chosen shell is checked and remains sticky across local and foreign
foreground changes. A broken assignment appears as a checked unavailable target,
with execution status directing the user to correct or clear it. Each action
captures and revalidates its original editor/view/owner/epoch. Temporary shell
choices are hidden from the durable shortcut model. Legacy has no chooser and
keeps its original execution-target label; peer File/Main/cell commands retain
their compatibility route and have a label that describes that scope.

The application bridge no longer assumes every resolved Selection token uses
the native foreground shell. It dispatches the captured explicit shell, while
retaining 026's no-fallback guard for implicit routing. Native pane ownership
and process ownership are checked independently of the pure model, including
injected model drift into its deferred migration state. No such migration is
wired into the application.

Assignments belong to live views and never enter document persistence. Two
views of one resource choose independently. The bridge distinguishes the same
live resource record moving/changing epoch from a new reopened record with the
same view ID. A live owner/epoch change conservatively preserves broken intent;
an unobserved owner round trip cannot silently repair it. A reopened view defaults
to implicit and rejects the old chooser context and operation. A fresh execution
service likewise starts implicit. Native movement within the owner preserves
view/shell identity, generation and assignment.

Unexpected loss remains broken despite other eligible local or foreign shells.
The same live shell reconnecting repairs its assignment with a new generation.
Confirmed shell closure resets assigned views to implicit; canceled closure
preserves assignment and operation validity. If there is no eligible selected
implicit foreground afterward, it refuses rather than choosing a recency fallback.

## Before/after evidence

- Bridge matrix initially **4 failed, 14 passed**: explicit dispatch depended on
  foreground, unhealthy foreground blocked a healthy explicit target, correction
  text was absent, and transferred views silently dropped assignment. Those cases
  pass after unified resolution, dispatch and record/epoch synchronization.
- Two new router controls initially errored on missing `synchronize_view`; all
  **12 router tests pass**, including transfer/return and unobserved round trips.
- The first live launch exposed my incorrect Shell-menu insertion and missing
  Pyzo `menuPath` contract. Both were corrected in the Run menu. A real wrapper/
  shortcut control initially **1 failed, 6 passed**, then all seven passed after
  the chooser's transient entries were hidden through the existing hide contract.
- Actual reconnect initially exceeded the unchanged 35-second outer cap. Added
  phase assertions identified a replacement context already disconnected, with
  empty state/version. The old connection's queued callback used the current
  `self._context`, closing the replacement. Native callback controls initially
  **2 failed, 2 passed**; the five-case final control now passes. It covers current,
  retired, preparing, absent-context and failed-preparation events. Connection
  creation retires the prior identity before preparing; only the current identity
  may close the context or publish lost-connection UI.
- Native-owner drift controls initially **2 failed, 34 passed**. Admission and
  dispatch now refuse the mismatch even when the pure router reports a valid
  explicit route. They do not introduce live migration.

Missing-module chooser collection and early standalone Yoton/config fixture
errors are setup gaps, not product measurements. A shared pytest-fixture alias
was cleaned up for lint and all seven menu controls were rerun afterward.
Unrelated router formatter churn was removed before final validation.

## Live proof and checks

The new test-owned Qt app starts three actual interpreters: two in A and one in B.
The actual Run chooser assigns A's first shell and B's shell, then opposite
focus/global-target orders still deliver values 11/22 only to their assigned
namespaces. A's alternate initially has no assigned variable. Float/redock leaves
the assignment/token/context current. Actual restart keeps shell identity, changes
generation, refuses pending execution, and rejects a real old-generation value;
a current-generation 42 is accepted.

The probe disconnects A's assigned transport while its alternate and B stay alive;
no fallback send occurs. It exercises native `connectToKernel` on that same shell
view, proves repair and new generation, then disconnects it again. The chooser
corrects the assignment to A's alternate (value 33), clears back to implicit (34),
and proves canceled close preserves assignment while confirmed close resets it.
B remains independently assigned and accepts value 23. Closing/reopening B's
retained native view with the same ID produces a fresh implicit assignment and
rejects the retired widget and prior operation. Named source bytes remain the
original saved baseline. The connection recovery proof uses the native lifecycle
API; no new reconnect button is claimed.

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo/pyzo:deps/pyzo:. ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest --with PySide6 --with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl --with ipython python -m pytest spikes/peer_frames deps/pyzo/tests -q -rs
RUN_LOCAL_RETENTION_ACCEPTANCE=1 RUN_LOCAL_EXECUTION_ACCEPTANCE=1 PYTHONPATH=. ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest python -m pytest spikes/peer_frames/test_local_retention_acceptance.py spikes/peer_frames/test_local_execution_acceptance.py -q -s
```

Final combined: **381 passed, 12 skipped, 45 subtests**, 2.41s.
Final live: **11 passed**, 35.39s; assignment probe **3.956s**, previous Selection
probe **3.449s**. Focused Run/bridge/menu/connection matrix: **54 passed**, 0.18s.
The unchanged full smoke runner from the [retention evidence](retention-integration-2026-10-04.md#initial-review-measurements)
passes peer **11.531s** and legacy **7.321s**, retaining Run/live-debug, postmortem,
multi-kernel and lifecycle assertions. Eleven opt-in tests account for separate
live execution; the other default skip is the stock tab-side control superseded
by the fork. Two existing Qt high-DPI deprecation warnings remain.

Eleven touched Python files compile. Ruff name/import diagnostics and root/nested
added-line whitespace pass. Runtime: Python 3.12.13, PySide6/Qt 6.11.1 and the pinned
local `pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl`.
Each live process uses fresh config/data/workspace/recovery paths, stubs the user's
command listener, and owns its real kernels. Timeout cleanup targets only that
owned process group. No existing assertion or deadline was relaxed; the new probe
retains a 35-second external deadline with a stricter 12-second per-phase diagnostic.

Logs: [combined](selection-assignments-2026-10-05/combined.log),
[live](selection-assignments-2026-10-05/live.log),
[peer](selection-assignments-2026-10-05/peer.log),
[legacy](selection-assignments-2026-10-05/legacy.log),
[bridge before](selection-assignments-2026-10-05/bridge-before.log),
[callback before](selection-assignments-2026-10-05/connection-before.log),
[reconnect diagnostic](selection-assignments-2026-10-05/reconnect-before.log),
[owner drift before](selection-assignments-2026-10-05/owner-before.log).

## Remaining gates and limits

NEXT is the existing Stage 4 remaining Execute/cell/File/Main/Run-as-Script routing
gate, preserving each command's buffer/save/recycle policy. Complete native
completion/help/tool/Run/debugger request/result provenance still follows before
Stage 4 acceptance. Stage 5 debugger ownership and Stage 6 contextual tools remain
pending. File Move/Fork UX remains a later local slice.

Physical macOS drag/accessibility and Windows/Linux replay are not claimed by
offscreen native movement and QAction activation. Legacy is the maintained local
fork, not pristine upstream or a published-wheel installation. September deferrals
for shell migration, zombies, portable workspaces/synchronization and broad TOAS/Rhizome
integration remain unchanged.
