# 031: Workspace breakpoint and debugger ownership (014 Stage 5)

## Status

DONE — compiled, claimed and accepted by Engineer (Codex), 2026-10-06 under user
“Proceed with Stage 5.” Depends on accepted 026–030. The September amendment
remains normative; historical zombie/migration requirements do not apply.

## Outcome and allowed writes

Accept complete local Stage 5: persistent workspace/document breakpoint overlays,
independent native view projection and kernel delivery, fixed session overlay
ownership, foreground-shell debugger controls, live/postmortem provenance,
workspace-owned source navigation and conservative retained closure. Allowed:
root policy/model, focused/native tests, owned real-kernel probes/harness;
Pyzo editor/document adapters, shell commands/stack/transport, kernel debugger
and introspection, persistence and closure warnings; local task/evidence and
mutable roadmap completion. Preserve legacy behavior and accepted Stage 4.
No binding changes, Stage 6 tool/config/history isolation, live-shell transfer,
zombies/reconciliation, portability/synchronization or TOAS/Rhizome integration.

## Pre-edit state/assertion coverage

| State/order | Executable invariant | Handling/gap |
| --- | --- | --- |
| Shared document in A/B; multiple views within one owner; enabled/disabled/removed entries; shared text shifts | `overlay(A, doc) != overlay(B, doc)`; same-owner views agree; delivered paths contain only owner entries | Gap: native path aggregation/broadcast and editor block metadata |
| Checkpoint/restart; closed view/workspace; save failure | persisted workspace/document keys and tri-state entries survive; old manifest remains authoritative on failure | New overlay extension in existing shared resource persistence |
| Rename/Move/Save As same identity; Fork; unavailable/deleted identity; path reuse/reactivation; discard broken | same-ID entries survive; fork copies only branching owner then diverges; unavailable entries inactive; replacement ID cannot inherit; discard explicit | Resource registry operations plus overlay policy/projection |
| A/B running/debugging; overlay edit while session active; next session | session owner fixed; active session snapshot unchanged; subsequent session receives current owner's overlay | Gap: unconditional breakpoint channel broadcast; freeze at operation/session boundary |
| Foreground A/B/idle/lost shell, execution assignment to another shell; postmortem versus live | each control targets foreground shell directly; non-debug controls do not fall through; PM NEXT/STEP/RETURN/JUMP/CONTINUE rejected; STOP/FRAME and captured-frame expression execution supported | Gap: top-level controls use execution target/global mode |
| Independent concurrent debug/PM sessions; stack actions after foreground drift/frame change/restart/close | captured session/generation/sequence current before send/navigation; stale results and old action captures rejected | Extend existing request/transport receipts with debug session/sequence |
| Shell traceback/source navigation; retained dirty/unavailable source; two owners of same path | source opens/selects owning workspace's identity; captured dead origin never falls back; foreground changes do not mutate origin | Gap: global `loadFile` and global indicator broadcast |
| Handled exceptions sent through logging; later DB START | capture the logging operation's receipt with its traceback before another operation replaces it; PM start never borrows a different exception's origin | Existing logged-exception hook also needs the traceback provenance publication |
| Resume followed by quit/restart while an older checkpoint is pending; non-bootstrap runtime session capture | newest live/retained view membership remains authoritative; preserve complete session metadata for every owner | Fresh-process probe exposed an older pending document snapshot and overwritten non-bootstrap session metadata; bounded lifecycle/capture repair |
| Shared text projection blocks native Qt signals; text replacement recreates blocks; undo/redo and closed-owner edits | durable line anchors rebase once per resource edit for every overlay owner; native block markers rebuild from that state; frozen active sessions stay unchanged | Real shared insert/undo proof exposed stale native block references in the accepted document projection adapter |
| Native traceback path aliases (including macOS `/var`/`/private/var`) | canonical aliases resolve to the existing durable document identity in the session owner; never create a duplicate resource | Full peer control exposed navigation with a registered source under a different path spelling |
| Cancel and failed retention with active live/PM sessions; accepted close | exact topology/resources/assignments/context/session preserved with zero teardown; disk retention before owner-only termination; visible interpreter/stack loss warning; surviving session usable | Reuse 030 close boundary and extend actual session proof/warning assertions |
| Legacy mode and native full smoke | old non-peer breakpoint/control behavior retained; real Run/debug/PM/lifecycle controls green | Maintain explicit compatibility path |
| Timeout/error/normal shutdown | test-owned appdata/server stub, phase/external deadlines and owned kernel teardown; no uncaught Qt exceptions | Existing owned harness |

User authorization covers implementation and bounded repairs of these cases;
no strict external-validation mode is requested. Extend this map before editing
newly discovered states. Project Manager stops at READY; Engineer must claim
before source/test writes.

## Acceptance and completion

Machine-checkable policy/native assertions, genuine simultaneous real-kernel
live/postmortem sessions and independent shared-document overlays; durable
roundtrip/identity proofs and debug-session cancel/failure/termination evidence.
Run focused, coordinated, all live and full peer/legacy controls. Record exact
revisions, logs, cleanup and limits; commit implementation before accepting
Stage 5 and moving NEXT to the existing Stage 6 gate.

## Completion

Root implementation `b08895d843892da660068d65659c513cada9f3bc`; Pyzo implementation
`0797bb43363cd1152fea5dd1d2046ac05a81de2c`. Final root acceptance revision
`3d861eaa4af5d34d5ae3e9e11ace56faed6261b7` checks overlays on disk before
every irreversible teardown event. Durable owner/document overlays, native
projection and line rebasing, fixed session snapshots, foreground controls,
live/PM origin and frame guards, executable captured PM contexts and owner-only
source navigation are implemented. Genuine simultaneous kernels, stale action/
query rejection, visible stack-loss warnings, Cancel/failure/fresh retry, durable
A-only termination with B PM continuity, retained resume and fresh-process
enabled/disabled overlay restoration pass. Bounded shared-block, pending-snapshot,
membership/session-metadata, logged-exception and canonical-source repairs are
covered by the recorded assertions.

481 coordinated tests and 51 subtests; all 15 live controls; full peer/legacy
controls pass. All 20 touched Python files compile; Ruff F and whitespace pass.
[Acceptance evidence and logs](../../docs/evidence/workspace-debugger-2026-10-06.md)
record exact revisions, runtime, process/generation evidence and limits. Stage 5
is accepted; NEXT is the existing 014 Stage 6 gate. September deferrals remain
normative. Binding packaging is untouched; nothing pushed.
