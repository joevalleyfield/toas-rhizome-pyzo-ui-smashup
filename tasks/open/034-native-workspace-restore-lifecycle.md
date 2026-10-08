# Stage 7 follow-up: Native workspace restore lifecycle

## Status

DONE, accepted 2026-10-07. Claimed by Codex under the user's “Take the next followup.”
Dependencies: accepted 033; observed native restore failure in its evidence.
This is the next bounded compatibility follow-up within existing 014 Stage 7.

## Contract and write surfaces

Reproduce the native restore fault using isolated application data; establish
its ownership/lifecycle cause; repair only a demonstrated gap; add regression
assertions and replay accepted controls. Root QtADS adapter, tests/probes,
local task/evidence and queue links are allowed. Pyzo restore code is allowed
only if the reproduction identifies its contract violation. Binding/native
source changes require a dependency blocker, minimal reproduction and a recorded
bounded decision first. No physical/platform or full Stage 7 acceptance claim.

## Pre-edit state/assertion coverage

Read-only investigation first. Relevant states at layout realization:

| State | Machine assertion / expected result | Current path / gap |
| --- | --- | --- |
| Empty / single / multiple frames; unchanged layout | `capture_layout()==desired`; `manager.dockAreaCount()==0` | render, ensure/realize frame; existing tests |
| New frame anchor unplaced / already in same frame / moved from another | `container.dockManager()==backend.manager`; every desired pane captured once | ensure frame followed by realize; ownership to trace |
| Existing frame retains docks / loses last dock then reused in same render | `isValid(window) and container.dockManager()==manager` before placement | cached frame dictionary; possible gap |
| Frame/pane order permutations; hash seed varies; active pane absent/present | normalized capture equals desired membership and activation | restore render; original intermittent failure unresolved |
| Native removal synchronous; deferred-delete pending / delivered | placement never calls a detached container; retired projection not reused | refresh only at render entry; investigate native removal |
| Queued sync/notification before / during / after close or failed restore | `native_calls_after_close==0`; other runtime unchanged | callback guards need inspection |
| Invalid/partial saved state or unavailable owner | failed result; original authoritative layout/other owner preserved | model/session validation and rollback controls |

A native subprocess exit/assertion is a machine-checkable failure. Run repeated
fresh restores from one immutable test-owned fixture and trace manager/container
identity at placement. Add refined state coverage before any demonstrated fix.
User authorization covers this bounded investigation and repairs; no strict
external-validation mode requested.

## Demonstrated gap and bounded repair decision

Thirty fresh debugger restores (hash seeds 0–29) passed unchanged. A two-pane
adapter reproduction deterministically exits 139: initial A(one), B(two),
restore A(two), C(one). The pre-placement trace prints `container.dockManager()
is None`. QtADS removes an empty floating container from its manager immediately
in `finishDropOperation()` and queues its deletion. Python wrapper validity
therefore does not prove registered-container ownership.

Refined states and assertions:

- Live registered window: `isValid(window)` and
  `window.dockContainer().dockManager() is backend.manager`; reuse it.
- Detached pending-deletion wrapper: wrapper may still be valid but manager is
  `None`; discard the mapping and create a replacement using the desired anchor.
- Deleted wrapper: `isValid(window)==False`; replace without dereferencing it.
- A prior ensure/move empties a later target, including swaps and frame renames:
  revalidate immediately at frame realization, not just render entry.
- Frame realized earlier retains at least its desired anchor. Desired pane
  membership is unique by model validation; later realization cannot steal it.
- Queued native sync/deletion after restore: assert exact captured layout before
  and after event delivery; every captured pane exactly once, hidden manager
  contains zero areas, no fatal projection-destruction error.

Minimal fix: validate window registration in `_ensure_frame` and call it at each
`_realize_frame` entry. No dependency changes: native behavior is understood and
adapter ownership checks suffice. Regression matrix covers all pane/frame order
permutations across unchanged/partially/new frame identities, active/no-active,
and immediate/deferred event delivery. Existing lifecycle/invalid-layout tests
and full live controls retain coverage for other rows. Queued callbacks after
backend close are outside this demonstrated fault and receive no speculative
repair in this cycle.

The first regression run exposed a test expectation error, not another native
fault: with no explicit active pane, existing capture intentionally chooses a
live pane (native focus, model, then first group). For that row assert
`captured.active_pane_id in desired_panes` and compare the remaining layout
exactly. Explicit activation must still compare exactly. No production change
is made for this existing capture contract.

## Second demonstrated lifecycle gap / separate verification cycle

The ownership permutation matrix passes. The full suite's explicit deferred
wrapper test then reproduces a queued sync firing after backend close and
manager deletion: `_synchronize_settled_layout` reads `floatingWidgets()` on an
invalid C++ manager. This is now a demonstrated in-scope lifecycle gap.

Before its separate repair, enumerate idle/pending sync, pending settled
notification, late area/focus signals, manager deletion pending/delivered,
and repeated close. Assertions: after `_closing`, scheduling leaves
`_sync_pending==False`; callbacks clear pending flags but make zero native
accesses/model adoptions/observer notifications; `close()` repeated succeeds;
existing live callbacks still synchronize/notify normally. Queue sync and a
settled observer, close, deliver DeferredDelete before timers, call late
area/focus handlers with retired wrappers, then process events. Any native
access raises on those wrappers and fails the test. Existing live/native focus,
drag/adoption and observer controls prove the live side.

Minimal second repair: check `_closing` at native signal/timer entry points and
make close idempotent. Visibility repair already has the guard. Do not change
any live synchronization semantics or native dependency code.

## Completion

Implementation `c53e5aff84eb9b8d849d84700650179530735c8a` precedes acceptance.
591 tests / 348 subtests, all 18 live controls and 30 final fresh debugger
restores pass. Legacy smoke passes; peer completes its host/editor/debug checks
with a pre-existing affinity-seed timeout, also present in 032/033 logs.
[Evidence](../../docs/evidence/native-restore-2026-10-07.md) documents both
demonstrated lifecycle repairs and corrects earlier broad peer-smoke claims.
The affinity timeout is a compatibility follow-up candidate; full Stage 7 stays
open. Pyzo/binding/native dependencies unchanged; nothing pushed.
