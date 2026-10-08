# Stage 7 slice: External file-open routing

## Status

DONE, accepted 2026-10-07. Claimed by Codex under the user's “Do it”, authorizing
the external file-open slice identified in the preceding review, bounded repairs,
tests and acceptance evidence. Dependencies: accepted 014 Stage 6 / 032.
Stage 7 remains open until its other integrated gates pass.

## Contract and write surfaces

Command-line and OS file opens select the most recently foregrounded eligible
loaded workspace at GUI dispatch. Skip unavailable, retired and closing owners;
create a default only when no workspace is loaded. Project membership never
selects the owner. Open a local view of shared text, without foreign activation
or background writes. Preserve legacy dispatch and recovery selection.

Allowed: root coordinator/tests/probes, Pyzo application/command entry points,
associated tests, this task and evidence/queue links. No binding changes or
other Stage 7 acceptance claims. No strict external-validation mode requested.

## Pre-edit state/assertion coverage

| State | Code path and machine assertion | Current coverage/gap |
| --- | --- | --- |
| A/B foreground sequence, repeated focus, editor/tool/shell focus | coordinator activation history; `target == last_eligible(history)` | active identity only; no history |
| One/zero-frame loaded owner; startup owner without explicit focus | loaded-order fallback; `target in eligible_loaded` | global editor group may belong elsewhere |
| MRU unavailable/missing/disposed/closing/shutdown; next eligible or none | explicit eligibility; `target not in excluded`; `created == 0` if loaded nonempty | no exclusion |
| Empty loaded set with bootstrap/unavailable/retained records | default creation; `len(loaded_after)==1`; `opaque_records_after==before` | factory may use bootstrap |
| Close dialog reentrancy; Cancel/failure/retry; nested owner closure | mark identity before preflight, restore guard in finally; `target != closing_owner`; `closing_after == before` | process boolean cannot identify closing owner |
| Quit/restart negotiating/cleaning/finished; cancellation back to idle | refuse during application transaction; `opens == []`; `created == 0` | queued global callback unguarded |
| Request server thread, OS event, startup command, queued focus/retirement drift | one GUI callback resolves current services; `target == eligible_at_dispatch`; `UI_calls_before_dispatch == []` | captures global bound manager method |
| Shared/already-local/retained resource; alias path; project in another owner | fixed local editor facade; `view.owner == target`; `document_id == existing_id`; `source_bytes_after == before` | global dedup activates foreign view |
| Recovery selection Cancel/failure; modal focus drift or target retirement | recovery gate then eligibility recheck; `loads == []` on refusal; accepted load remains in selected owner | global-only gate; local open needs explicit gate |
| Empty/missing/malformed filename, load or creation failure | existing command validation/errors and callback failure reporting; `foreign_writes == 0` | preserve; do not broaden CLI grammar |
| Legacy/vanilla/no peer controller | GUI callback uses current legacy manager; `legacy_calls == [(filename,)]` | preserve compatibility |

Each new discovered state must be added before its repair. Verification:
coordinator and dispatch tests; actual Qt application and QFileOpenEvent probe
with test-owned appdata/server stub; full coordinating/Pyzo tests, all existing
live controls, peer/legacy smokes, compilation/Ruff/whitespace. Record exact
revisions and platform limitations; commit this slice before completion.

## Native refinements before repair

- A live resource in A with unsaved text, opened as a new B view, reaches the
  ordinary editor constructor with no durable identity. The native probe
  reproduced duplicate path registration and missing view identity. Resolve
  canonical paths in the live resource registry before opening; use the existing
  retained-view constructor for shared or closed resources. Assert
  `doc(A)==doc(B)`, `text(B)==retained_text`, unchanged disk bytes and one local
  view after alias/CLI/OS reopen. Unknown paths keep normal native construction.
- Application Quit sets `_peerApplicationExitRequested` before negotiation but
  does not clear it after cancellation/failure. Clear it only when the shutdown
  coordinator has returned to idle. Assert cancelled/failed then ingress succeeds;
  coalesced/cleaning/finished still refuses. Test both actual lifecycle and unit
  dispatch without adding any shutdown behavior.
- Focus queues native external-file checks. Successful workspace retirement
  can run before that check, leaving a callback on an unbound editor. The native
  replay reached a retired context read. Guard before filesystem/widget access
  and after modal reload confirmation: `checks(retired)==0`,
  `reloads(retired)==0`; live and legacy checks remain active. Retained resources
  themselves are not retired by this guard.
- Legacy selection currently reads foreground ownership after its chooser.
  A focus change can publish the selected recovery view in a foreign workspace
  before ingress's later guard. Capture the explicit ingress owner and its epoch
  before the chooser; assert `publication.workspace_id==captured_owner`, and
  `publications==[]` for retired/reloaded/closing/exit states. Ordinary recovery
  commands capture their invoking owner at entry as well.
- The existing tools replay twice cancelled its survivor query after 0.2s.
  An isolated diagnostic recorded `None`, B still Ready with one connection,
  and the unchanged `"B"` value on a later bounded query. Replace this one
  synchronous proof with a held Future and a separate event-loop phase, with
  a two-second auto-cancel and existing external/phase deadlines. Assert the
  original B shell, a noncancelled/error-free result exactly `"B"`, then the
  unchanged reopen/restore assertions. Do not change production kernel behavior.

## Remaining Stage 7 compatibility observation

One full-suite attempt exited 139 during debugger fresh-process startup.
The macOS faulting stack begins `ads::CDockManager::componentsFactory()` →
`DockAreaWidgetPrivate::createTitleBar()` → dock-area/container construction →
the binding's `addDockWidgetToContainer`. The isolated debugger replay with
fault diagnostics enabled passes, including both live kernels and fresh restore.
Preserve the failed replay and fault summary as a compatibility follow-up in
the existing Stage 7 gate. No binding source or packaging changes are authorized
by this slice, and no physical/platform or full Stage 7 acceptance is claimed.

## Completion

Root implementation `be1f8db4bed48b65736492a634542193e2350d18`; Pyzo
`0e334f57de142cf4deeee4dd43b5b1453b9ad6f4`. Both implementation commits
precede this acceptance. Binding unchanged; nothing pushed.

588 tests/56 subtests, all 17 live controls, full peer/maintained-fork legacy
smokes and ten-source compile/Ruff F/whitespace checks pass.
[Accepted evidence](../../docs/evidence/workspace-ingress-2026-10-07.md)
records routing/close/recovery state coverage, real worker/CLI/QFileOpenEvent,
shared retained identity, missing source, empty-set opaque-record preservation,
exact revisions and the native restore observation. This completes the local
external file-open slice only. NEXT remains 014 Stage 7's other integrated gates.
