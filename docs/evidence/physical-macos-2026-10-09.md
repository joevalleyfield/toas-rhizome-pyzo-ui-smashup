# Physical macOS workspace run — 2026-10-09

Task [037](../../tasks/open/037-physical-macos-workspace-acceptance.md) records
**partial measured physical coverage** and bounded repairs. The observed native
cases below pass. The user accepted the macOS follow-up complete on 2026-10-10
with those coverage limits; full Stage 7 remains open.
[Replay steps](../physical-macos-workspace-checklist.md) include the remaining
manual checks.

## Environment and method

Apple Silicon macOS, Python 3.12.13, PySide6 and the local QtADS
`5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64` wheel. A compiled embedded-Python
`.app` supplied a native LaunchServices/accessibility identity and real
File → Restart. The launcher copies the current implementation into a disposable
runtime, and configures Cocoa, isolated appdata/recovery/workspaces and explicit
Python kernel executables. It does not contact the user's command-line server.

All typing, menus, keyboard commands, floating gestures and dialog choices used
native computer UI. Initial two-owner topology was fixture setup. JSON snapshots
and the event filter observe resources, focus, layouts and exits; they do not
perform acceptance actions. No `QMainWindow` existed in the Cocoa snapshots.
The retained fixture directories are `/private/tmp/pyzo-physical-native-2026-10-09`
and `/private/tmp/pyzo-physical-final-2026-10-09`; copied evidence survives temporary
fixture cleanup. The launcher builds a fresh fixture unless given `--directory`.

## Observed native results

| Case | Actual observation | Evidence |
| --- | --- | --- |
| A/B local typing | A-only 101 and B-only 202 stayed in their respective local documents | `a-local-edit.json`, `b-local-edit.json` |
| Shared edit/Command-Z | B's shared edit and undo propagated to both views of the same document | `shared-undo-local-shell.json` |
| B shell input | `physical_b_kernel` appeared only in B's live interpreter history | same snapshot |
| File → Open / Command-O | After the menu repair, B received its own view; the earlier two-owner replay reused A's canonical ingress document | `file-open-b-after.json`, final `final-file-open-b.json` |
| Float | Actual tab drags created A's local float and B's shared float without changing durable view/document/text ownership | `final-float.json`, `final-b-float.json` |
| Single B view close | Native close removed exactly B's floated shared view; A's view, all document resources and shells survived | `final-b-view-close.json` |
| Live shell frame Cancel | Clicking A's native shell-frame close and Cancel preserved exact views, shell instance/epoch and topology | `final-before-frame-close.json`, `final-frame-cancel.json` |
| Application Quit Cancel | Native Command-Q prompt Cancel preserved live editors, kernels and placement | `quit-prompt.json`, `quit-cancel.json` |
| Quit / fresh relaunch | Confirmed native Quit published clean exits; fresh launch retained all document/view identities and text | `initial-events.jsonl`, `final-events.jsonl`, `final-after-quit-relaunch.json` |
| File → Restart | Confirmed real Restart retained both owners' views/text, editor/tool topology, A's float and surviving frame geometry; fresh interpreter epoch | `final-before-restart.json`, `final-after-restart.json` |
| Affiliation | Rebuilt frame captions identify their own workspace, including the secondary owner | final restart/relaunch snapshots and CUA accessibility traces |

Files in the table live in [the evidence directory](physical-macos-2026-10-09/).
`fixture.json` is the first fixture; `final-fixture.json` belongs to the final
replay. The initial failed relaunch is retained as `relaunch-before-topology.json`.
A checkpoint copied after that failure already contained its altered placement;
final topology acceptance therefore used a fresh fixture.

The [evidence verifier](physical-macos-2026-10-09/verify.py) checks recorded native
identity/text/geometry, owner captions, Cancel invariants, B-only view removal,
unchanged resources and empty exit-error lists. It passes. This verifier checks
observations, not the fidelity of a physical gesture.

## Repairs and automated verification

Secondary editor dock titles now use the owning runtime. Shared native menu
callbacks resolve context on invocation; owned popup/frame ancestry still wins,
and a File dialog retains its captured owner if focus changes while it is open.
File and Tools menus refresh their contextual state on showing.

Restoration reuses an empty host only in its own runtime. Modern view/tool mapping
also applies when a fresh default interpreter exists; saved placement is pruned
to retained panes, merged with fresh shell placement using unique frame/group
IDs, and restored through session metadata for both owners. Surviving exact frame
IDs receive their saved geometry. Frame affiliation refresh repairs native titles.
Old kernels remain ephemeral and are not revived.

The broader suite repeatedly exposed a retired native-frame destruction callback
matching a reused Python numeric ID. Callbacks now hold weak references and
compare the exact wrapper. A forced numeric-collision regression fails before
and passes after; genuine current-object destruction still reports a fatal
invariant breach. The task's T/F/R/D tables record the state/assertion coverage.

An early version of that regression forced synchronous deletion of an already
retired native container and caused a later Qt menu teardown crash. The final
fixture uses the normal deferred native deletion path; the combined backend/menu
controls and whole suite pass. The failed whole-suite log is kept for provenance,
not treated as accepted evidence.

Final controls:

- **698 tests, 351 subtests, 23 intentional skips**, 6.52 seconds:
  [unit log](physical-macos-2026-10-09/units-final-pass.log).
- **All 22 opt-in live controls pass**, 105.17 seconds, including the new
  two-process restart with B foreground and real kernels:
  [live log](physical-macos-2026-10-09/live-final-pass.log).
- The deterministic collision, cache/deferred deletion, immediate-destruction,
  retired callbacks and command-projection controls pass together:
  [native log](physical-macos-2026-10-09/native-deferred-collision.log).
- The reviewed context census remains 70 rows; the live inventory has **717
  references** after removal of the primary-global `newFile` restore call.
  Python 3.12 AST review/locations were refreshed; classifications remain intact.

Before/after title, menu, restart, affiliation and lifecycle regression logs are
retained alongside the snapshots. Source compilation, changed-code lint and
whitespace checks are recorded separately.

## Remaining physical obligations and limits

Physical split, re-dock and cross-owner drag refusal are **unaccepted**. Native
coordinate input sometimes returned `noWindowsAvailable` after real Restart;
rebinding allowed AX actions. A clean relaunch allowed clicks and another float,
but the drag endpoint placed B's float at `[-866, 947, 168, 595]`, outside the
screen instead of the intended docking target. That test-owned view was closed
through its native close button; no model call was used to claim a successful
re-dock. Screenshot capture also needed an exposed AX Raise after relaunch.

Finder-delivered `QFileOpenEvent`, Finder drop, confirmed individual live-shell
closure, zero-visible-frame OS activation and complete keyboard/tab/menu
traversal remain unperformed. File-dialog success and offscreen ingress controls
do not substitute for those physical cases. Splitter pixel proportions were
not preserved by the model; semantic topology and outer geometry were checked.
Main/conflict/tool preferences have separate automated coverage, not a complete
physical integrated replay here. Windows/Linux, vanilla and migrated-user-state
acceptance remain Stage 7 obligations. No TOAS/Rhizome integration, File Move/Fork
UX or shell migration is accepted by this run.

## Revisions

Implementation and acceptance revisions are recorded below after the local
commits. Nothing is pushed.

- Pyzo implementation: `99f585fe33cb806378269809fcc27a9add93cc93`.
- Coordinating implementation: `51fb28ecdfd08e9222125fb9286a0212d8cb0c6b`.
- Tested wheel SHA-256:
  `2243093d5518a0c8c13fbcc574f734690c631f508f1755de30f8d0288d28db20`.
- Physical OS: macOS 27.0.1, build 26A434.

Final source compilation and changed-code lint (`E9,F63,F7,F82`) pass; root and
Pyzo whitespace checks pass. Unchanged AST scopes were restored to their prior
formatting to keep the patch focused, and the inventory was rechecked afterward
([2 checks pass](physical-macos-2026-10-09/source-inventory.log)). Copied diagnostic
logs have trailing whitespace normalized; their assertions and outcomes are
unchanged. Pyzo has a clean working copy. Existing binding working-copy changes
were preserved and were not included in these commits.

Binding working-copy revision remains `b8d9c0a784db678227833ef8e545765a974ad4cb`,
parent `764eb4a487abccb162dcbee1a8f0383916561e0e`; native/reference QtADS sources
and wheel are unchanged from [036's revision record](stage-seven-scale-census-2026-10-08.md).
That record identifies PySide6/Qt 6.11.1 and IPython 9.17.1 for the same pinned
cached runtime. The separate acceptance commit follows the implementation.


## User disposition — 2026-10-10

The user accepted this macOS follow-up as complete after the launcher bootstrap
repair and shell/workspace creation instructions. This sign-off does not add
physical observations to the 2026-10-09 record. The unperformed cases above are
retained as coverage limits, rather than blockers for this accepted macOS slice.
Vanilla/legacy/migrated-state compatibility, full integrated acceptance and
Windows/Linux native validation remain in Stage 7.
