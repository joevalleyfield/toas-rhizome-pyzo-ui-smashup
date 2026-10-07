# Stage 6: Workspace contextual state and tools

## Status

DONE, accepted 2026-10-06. Implements the existing 014 Stage 6 gate after
accepted Stage 5 (031), preserving the September amendment.

## Contract and write surfaces

The September amendment remains normative. Implement durable independent
workspace preferences, shell profiles, projects, command history, built-in tool
instances/following, capability request/effective reporting, third-party
compatibility, and visible/accessibility affiliation. Preserve application
theme/language/style/scale capability fallback and legacy/vanilla paths.

Allowed: coordinating models/tests/probes in spikes/peer_frames, Pyzo core/tools
and tests, this task, Stage 6 census/evidence/logs and completion ledger updates.
No binding changes, shell migration, zombies, portable sync, File Move/Fork UX,
or Stage 7 physical/platform claims.

## Pre-edit state/assertion coverage

The user's explicit Stage 6 instruction authorizes implementation of this
existing gate. Use the state-assertion-fix-gate map before touching each boundary.

| State | Handling and machine assertion | Observed gap |
|---|---|---|
| Legacy/no peer service, initialization before services | original services; `config_for(widget) is pyzo.config` | preserve |
| A/B loaded, foreground switches, background widget callbacks | owner via durable dock/view context; `owner(callback_resource)==owner(widget)` | tools and preferences use globals |
| Owner empty/no eligible editor or shell; removed/failed/closing owner | local empty/visible failure; `selected is None`; `foreign_writes==0` | foreign fallback |
| Preference/project/history/tool edits and nested mutable values | deep per-owner snapshots; `snapshot(B)==before_B`; copy then edit `snapshot(copy)!=snapshot(source)` | shared config/history |
| Capability request A differs from process effective value | `requested(A)==input`; `effective(A)==application_effective`; `requested(B)==before_B` | no distinction |
| Default/site/user/dynamic/unknown/deprecated config | census owner for every key; `flatten(defaults)<=classified`; `unknown_after==unknown_before` | census provisional |
| Loaded/unloaded/reloaded tools, A and B same tool, delayed reply/restart/frame drift | separate instances/modules; receipt guards; `instance(A) is not instance(B)`; `stale_writes==0` | one instance per tool ID |
| Built-in editor/shell following and cross-tool actions | local facade; `all(owner(x)==owner(tool) for x in followed)`; absent local resource empty | global following |
| Third-party unknown/global/one-instance assumptions, failed import/construction | scoped declared opt-in or visible local refusal; `B_after==B_before`; unknown config roundtrip | undeclared contract |
| Save/close Cancel/failure/reopen/fresh-process restore | existing atomic generation; `durable.profile==live.profile`; cancelled/failing close leaves tools/resources intact | profile not captured |
| One/multiple owners, rename/focus/theme/move/float/restore | visible owner text + accessibleName on each dock/content; `name in visible_title and name in accessibleName` | partial frame-only labels |

## Acceptance evidence required

Complete Experiment 013 C01–C30/P01–P06/L01–L34 resolution with source and
test mapping; full coordinating/Pyzo suite; real two-workspace built-in tool
replay including local-empty and stale replies; durable close/reopen and new
process restore; full peer/legacy controls; compile/lint/whitespace; exact root,
Pyzo, binding revisions. Record limitations truthfully and advance to Stage 7
only after the complete Stage 6 gate passes.

## Native state refinements before each repair

- Startup builds menu callbacks before a local shell exists. The local editor
  service must implement the manager methods as well as host methods, and the
  shell service must expose its signals with zero eligible shells. Assertions:
  native startup completes; `local.getCurrentShell() is None`; no foreign host
  is created or selected. Initial smoke exposed missing interface methods.
- One-owner frame titles retain existing metadata; multiple-owner titles append
  affiliation. Assert exact single-owner title and owner name on each multiple-
  owner dock/content/frame. Initial smoke exposed over-eager single-owner suffix.
- Tool lifecycle policy construction uses `(application, pane_id, dock)` and the
  same close transaction in every runtime. Assert close removes exactly that
  manager entry and releases its pending receipts; existing native control
  caught the missing policy argument before accepting any tool lifecycle.
- Saved layouts may mix retained editor IDs and stable tool IDs after restore;
  terminated shell IDs are pruned. Assert every current retained editor and tool
  is placed once, and no old shell is resurrected.
- Execute File and retained Main have an invoking view even when Main has no
  open editor. Resolve `changeDirOnFileExec` from that captured invoking view;
  assert the owning preference applies for both open/closed Main and no foreign
  preference is read. The existing runner test caught an undefined source
  editor in the initial preference adapter.
- Initial tool placement uses the contract's BELOW direction; assert the tool
  is placed exactly once with the requested same-owner split target. Do not
  translate native enum names into unverified contract names.
- Menu synchronization (construction/refresh/programmatic checked selection)
  differs from explicit user toggling. Assert synchronization emits zero setting
  mutations and opens zero modal dialogs; a user activation writes one owner
  request. Native tracing identified callback-driven initial selection opening
  a capability dialog during construction, before shell menus existed.
- Retire owner-bound signal proxies and manager/backend bindings only after a
  successful close. Assert cancelled/failed close keeps instances; successful
  close rejects delayed callbacks; reopen constructs fresh bindings against the
  new runtime while restoring durable history/preferences/tool state.
- Session callbacks must address the runtime being captured/restored, including
  after bootstrap ownership changes. Assert `session.loaded_tools` equals that
  runtime's manager and all layout tool IDs are registered after restore. The
  full native smoke caught a callback retained from the superseded one-manager
  service, which falsely captured an empty tool set.
- Menu construction in a zero-editor workspace must not implicitly create a
  host. Assert `groups_after_build==groups_before_build` and zero foreign reads;
  native last-editor smoke detected the adapter creating a host merely to bind
  Find/Save callbacks. Bind lazy local callbacks; only explicit New/Open creates.
- Language-alias normalization is application initialization, not a workspace
  request write. Assert fresh-process menu construction preserves every recorded
  capability request. Restore acceptance caught normalization replacing the
  request with the application's effective language.
- Completion/help/snippet/project lookups originate from the invoking native
  editor/shell, including delayed/background callbacks. Assert the selected tool
  manager belongs to that widget, never the newly foregrounded owner.
- Logger views explicitly subscribe to the shared application diagnostic stream;
  each has its own Python console/view state. Assert both receive output, closing
  one removes only its callback, and reload does not retain a dead widget.
- Profile mutation can occur through nested containers or advanced dialogs,
  without an editor text edit. A one-second owner-thread census observes those
  mutations and enters the existing one-second durable checkpoint. Assert
  automatic publication within the documented two-second scheduling bound plus
  writer/event-loop latency, and visible failure. Native presentation updates
  only controls owned by the changed workspace; defaults for document format
  remain creation defaults. Status visibility is per-owner; diagnostic text is
  an explicitly application-shared projection.
- Menu/dialog/tool-description callbacks retain their construction owner across
  focus changes. Assert a launcher captured in A changes only A even while B is
  foreground; modal settings retain the same owner until accepted/cancelled.
- Built-in widgets can shadow `layout()` with a QLayout attribute. Use the
  native QWidget accessor and assert owner-only live preference publication
  completes with both logger views loaded. The initial preference timer caught
  this concrete polymorphic widget state before acceptance.
- A workspace contextual-profile child can be absent (legacy), current, future
  schema, malformed config/history/tool containers, or include unknown keys.
  Assert malformed/future children are independently unavailable and retained
  as opaque records; another workspace loads/saves, and unknown valid children
  round-trip without normalization or loss.
- Tool metadata discovery accepts string literals or literal translation calls.
  Unknown expressions, malformed syntax, invalid translation arguments, and
  import side effects must not execute or abort another tool's discovery.
  Assert invalid names fall back to the local tool ID without execution.
- A previously unknown mutable application key can appear after workspace
  seeding. Its first contextual read must take a private snapshot, not expose
  an application alias. Assert late A/B nested mutations leave the application
  and the other owner unchanged. Only `shortcuts2` and its children receive the
  keyboard-map exception; similarly named unknown keys remain contextual.
- All requested owners may fail startup, or the last owner may close. The
  application's existing non-persisted bootstrap runtime supplies construction
  defaults/local-empty services; it never addresses an unavailable owner's
  resources. Assert retry preserves opaque records and zero-open Quit has no
  cleanup errors. Rebind the legacy session archive callback after primary
  runtime replacement; assert it cannot call a disposed owner's tool manager.
- Restored layouts can contain editors and tools together. Translate editor
  IDs, add stable local tool IDs, then compare complete membership. Assert the
  mixed layout restores with no failure marker and original retained placement.
- Native ADS movement can delete a floating container before chrome refresh.
  Refresh the backend's live window census and assert wrapper validity before
  affiliation access. Assert movement/shutdown emits no deleted-wrapper errors.
- Semantic pane metadata stays unsuffixed; visible titles add workspace text.
  Assert the native title equals the owning model title plus the owning name,
  while another model remains untouched.
- An editor host's repeating find timer can outlive native pane removal. Stop
  both local find timers at committed host removal; assert retired callbacks
  cannot attempt contextual reads after owner disposal. Cancelled close does
  not stop timers. File-browser worker stop accepts keyword-only timeout;
  application cleanup uses the documented named argument, with no thread errors.
- Failed-owner startup must not enter the legacy new-user tool-loading branch.
  Assert zero loaded owners creates no tools/resources until explicit retry or
  workspace creation; application commands and defaults can still construct.
- Successful owner retirement releases its private tool module tree as well as
  signal proxies/managers. Assert its module prefix is absent after accepted
  close and recreated on reopen; Cancel/failure retain the original modules.

## Completion

[Accepted evidence](../../docs/evidence/workspace-tools-2026-10-06.md) and
[final 70-row census](../../docs/evidence/workspace-context-census-2026-10-06.md)
record ownership/copy/live-update/compatibility, exact revisions, repairs and
limitations. Root implementation `b985fa0a920e522a4c4e1750b649843e5cdc0c3d`;
Pyzo implementation `6544d31cd7d3562856a57c242f7fd9ea254910db`. Binding unchanged.

501 coordinated tests/56 subtests, all 16 live controls, full peer and maintained-
fork legacy smokes, and compile/Ruff F/whitespace checks on 29 touched Python
files pass. Ten independent built-ins restore all captured states with local
resources; unknown config and capability requests survive. Cancel/failure keeps
instances, accepted close retires proxies/modules, and fresh-process restore
passes without warnings. Two recorded test-owned kernel PIDs are confirmed gone.

Implementation commits precede this completion and movement of NEXT to existing
Stage 7. Physical/platform/vanilla/scaling/external-ingress and final direct-
global census obligations remain there. File Move/Fork UX is separate; no live
shell migration, zombies, sync or broad Rhizome/TOAS integration was added.
