# Stage 7: Physical macOS workspace acceptance

## Status

DONE — accepted by the user as complete, 2026-10-10.
The bounded native run and repairs completed 2026-10-09. User sign-off closes
this macOS follow-up with the recorded physical coverage limits; unperformed
cases are not claimed as tested. Windows/Linux and compatibility/integrated
Stage 7 obligations remain. User explicitly requested execution and steps.
Dependency: accepted 036. [Evidence](../../docs/evidence/physical-macos-2026-10-09.md)
and [user checklist](../../docs/physical-macos-workspace-checklist.md).

## Contract and write surfaces

Launch the pinned real Cocoa application with isolated test-owned appdata,
workspaces/recovery and disposable source fixtures. Use native computer UI for
focus, menus, keyboard, physical docking, file-open/drop, cancel closure,
Quit/relaunch/restart. Read-only instrumentation may record identities, resource
text, native topology, focus, event receipts, kernel state and exit disposition.
Fixture setup is not acceptance of a UI action. No user configuration/server is
used. Root launcher/probe, focused tests if needed, local evidence/checklist and
bounded demonstrated Pyzo/native fixes are allowed. No Windows/Linux, vanilla
or migrated-user-state acceptance is implied by this slice.

## States and assertion/coverage sheet

| ID | States | Machine-checkable invariant | Coverage |
| --- | --- | --- | --- |
| M01 | Cocoa vs offscreen; 2 loaded owners; foreground A/B | platformName == cocoa; no QMainWindow; loaded IDs exact; active owner follows clicked owned pane | read-only native snapshot plus CUA view |
| M02 | A/B local editors; shared text; keyboard/menu focus changes | local view IDs remain owner-specific; A-only edit leaves B-only text unchanged; shared resource ID/text identical | native text/identity snapshot plus actual typing/menu |
| M03 | same-owner tab/split/float/re-dock; foreign drag refusal; front/back windows | same owner + resource/view identity after drag; topology changes; shell kernel generation unchanged; no cross-owner pane | native topology snapshot + CUA drag |
| M04 | File dialog/drop/OS ingress while A/B foreground; focus drift | receipt target is eligible foreground owner, canonical document identity reused; disk bytes unchanged except explicit test fixture creation | real UI plus ingress event telemetry; distinguish OS event from injected/dropped open |
| M05 | live-shell/frame close: Cancel vs terminate; dirty retained document | Cancel keeps exact live views/shell/resource/placement; confirmed close affects intended owner only | real dialog choices + before/after snapshots |
| M06 | Quit Cancel/confirm; Restart; fresh relaunch | Cancel preserves instances; clean published exit; next launch retains IDs/text/owner data/Main/topology, starts fresh eligible interpreter | real app menu/dialog + persisted state snapshot |
| M07 | OS activation with peers/no visible frames; owner affiliation/menus | visible labels/accessibility name match owner; application survives expected zero-frame disposition and recreates eligible default frame | observe if exercised; do not infer from offscreen controls |

Before any demonstrated fix, refine the applicable state map and effects
assertions; existing user authorization covers bounded repairs. No strict
external-validation mode is requested. Capture actual UI evidence and mark
unperformed checks explicitly rather than substituting injected events/model
calls for physical acceptance. Provide a launcher and user checklist with
expected outcomes and retained test directory for replay.

## Demonstrated repair coverage (2026-10-09)

User's “Go for it. Do it yourself” authorizes these bounded repairs.

| State | Code path / assertion | Before |
| --- | --- | --- |
| T1 primary / secondary host, current named or untitled document; clean / dirty; active / inactive owner | `_updateEditorDockTitle`: `dock.windowTitle() == item.name + dirty_marker + owner_suffix` | secondary lookup misses dock (gap) |
| T2 empty host / unregistered or retired host | no item projects Untitled; missing dock causes no write | existing no-op path |
| T3 recovery / external conflict, either owner | conflict marker remains on owning dock; no foreign dock receives title | existing marker path after owning lookup |
| T4 vanilla runtime | original `_editorHosts` lookup and title path | unchanged |
| F1 shared native menu built with A, invoked with A / B foreground | callback resolves context at invocation; only invoking owner's editor count/text changes | callbacks hold A (gap) |
| F2 per-frame menu or owned context popup, foreign foreground | ancestry wins; only the explicitly owned context changes | existing `context_for` owner path |
| F3 modal File dialog, foreign focus while pending / Cancel / multiple paths | captured group/owner remains stable; Cancel adds no editor; all results enter captured owner | existing owned EditorTabs ancestry path |
| F4 no active or unavailable owner / bootstrap | existing context availability and ingress guards refuse unavailable work | existing guard path |
| F5 vanilla menus | deferred context returns `pyzo`; existing callbacks receive same arguments | legacy compatibility path |

T states are checked by real loaded-host metadata assertions in the execution
probe, plus Cocoa replay. F states are checked by built shared/per-frame menu
actions and a dialog callback that changes foreground before returning; Cocoa
File dialog replay supplies the physical acceptance. Other native menu actions
that bound contextual methods during construction receive the same deferred
lookup; Tools refreshes its owner-bound entries before showing.

Restart repair coverage added after the real Quit/relaunch:

| State | Machine assertion / path | Before |
| --- | --- | --- |
| R1 primary A/B selection; saved view ordering interleaves owners; existing empty startup host | every loaded runtime editor host has an item; restored view IDs/text exact; reuse only an empty host in that runtime | global primary `newFile` leaves an empty host (gap) |
| R2 modern editor/tool map; zero or fresh native shells; old shells absent | semantic retained topology equals saved topology pruned to retained views/tools; fresh kernel epoch differs | any current shell bypasses semantic mapping (gap) |
| R3 current fresh shell frame/group ID collides with retained IDs, or no collision | all frame/group IDs unique; fresh panes placed exactly once; saved retained IDs/geometry remain stable | fresh placement merge absent (gap) |
| R4 incomplete modern editor/tool mapping, missing record/empty/legacy session | incomplete mapping refuses; empty session no-op; legacy existing translation path | guard and legacy path retained |
| R5 geometry for surviving/removed shell-only frames; primary/secondary owners | only surviving saved frame IDs receive their own saved geometry; removed IDs filtered | primary positional zip and missing secondary metadata (gap) |

Coverage: two-process real-kernel restart probe asserts R1/R2 for secondary
foreground startup, exact view/text/semantic placement and fresh epochs;
workspace-session unit controls cover R3; existing session invalid/rollback
controls cover R4; native Cocoa replay and saved geometry assertions cover R5.

T5: newly rebuilt/restored native frame, active pane inside/outside that frame,
multiple/single owner, empty/deleted frame: affiliation refresh selects the
frame's own active pane or its first group selection; title equals that pane's
projected label. Empty/deleted native targets are skipped. The restart probe's
`all(owner_name in frame.windowTitle())` fails before this repair; native Cocoa
replay checks the visible result. No focus or resource assignment is changed.

Native destruction callback coverage refined after repeated whole-suite failure:

| State | Assertion / path | Coverage before edit |
| --- | --- | --- |
| D1 current live pane/frame is destroyed synchronously | `fatal_backend_error is not None`; layout remains authoritative | existing immediate-destruction test |
| D2 removed identity, backend closing, or unbound model | no fatal and no current projection removed | existing close/retirement guards |
| D3 replaced projection with same identity; old callback before/after deferred deletion | current projection remains in registry; no fatal | numeric Python `id` comparison works unless reused |
| D4 callback captured no frame identity; Python wrapper retired and numeric id reused by another live wrapper | current registry and topology unchanged; no fatal | gap: numeric id can identify unrelated current projection |
| D5 old wrapper still alive, or garbage-collected before native callback | only the exact captured wrapper may be removed; dead reference is ignored | requires object identity without lifetime-dependent numeric reuse |

A deterministic control forces numeric id collisions while destroying a retired
native frame. It must leave the current registry exact and `fatal_backend_error`
None. Replace callback numeric tokens with weak references to the exact wrapper;
existing immediate-destruction and deferred-delete controls must continue passing.
This does not weaken the fatal guard for destruction of the current live object.


## Completion evidence

Actual Cocoa UI: A/B local typing, shared edit/undo, B shell input, foreground
File dialog opens, physical float, B-only shared-view close, shell-frame Cancel,
Quit Cancel/confirm, real File Restart and fresh relaunch. Recorded native
identity/text/geometry/affiliation, close/cancel and clean-exit assertions pass.
Final automated controls: 698 tests/351 subtests, 23 intentional skips; all
22 live controls pass. Current census: 70 rows/717 reviewed references.

Physical split/re-dock, foreign drag refusal, Finder OS-open/drop, confirmed
individual live-shell closure, zero-frame activation and full keyboard traversal
remain unaccepted due unavailable/unreliable coordinate input. Windows/Linux,
vanilla/migrated user-state and full integrated Stage 7 remain open. The fixture
was cleanly Quit; nothing was pushed. Exact local revisions are in the evidence.


## User acceptance — 2026-10-10

After the shell/workspace creation instructions, the user said:
“Let's call this complete then -- I assume you already did. What's next?”
This accepts the macOS follow-up as complete with its recorded coverage limits.
The preceding unperformed-case list remains historical evidence; it is no longer
an open blocker for this accepted slice. No extra physical checks were run by
this status update, and no Windows/Linux or compatibility acceptance is implied.
Task 038's offline/bootstrap repair is also complete. The next existing Stage 7
work is local vanilla/legacy and migrated-state compatibility, integrated replay,
and native Windows/Linux validation.
