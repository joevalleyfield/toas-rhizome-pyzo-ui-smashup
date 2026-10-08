# Stage 7 local final contextual-state census — 2026-10-08

All C01–C30, P01–P06 and L01–L34 rows of
[Experiment 013](experiment-013-workspace-state-ownership-audit.md) have been
replayed against the current sources. These tables restate the Stage 6 ownership
contract and add the demonstrated consumer/restore/ingress corrections from
[036](../../tasks/open/036-stage-seven-scale-and-final-census.md).
[Acceptance and commands](stage-seven-scale-census-2026-10-08.md) record the final
suite, real controls and 1/4/8 scale samples. Physical macOS, Windows/Linux,
unmodified vanilla and migrated-user-state integration gates remain open.

The [executable inventory](../../spikes/peer_frames/workspace_context_audit.py)
and [review manifest](../../spikes/peer_frames/workspace_context_review.json)
cover 718 syntactic references in 37 Pyzo files, including literal/dynamic
attribute lookup. Product model/adapter files under `spikes/peer_frames` add zero
references. Test probes, tests and external/native dependencies are excluded;
the unsupported bundled reference extension and built-in test helpers are
included and classified. There are no unclassified inventory entries. This is a
source review with effects evidence, not whole-program alias/dataflow proof or a
sandbox for arbitrary declared extensions.

| Classification | References | Meaning |
| --- | ---: | --- |
| Explicit application | 173 | Shared capabilities/services or registries indexed by explicit widget/resource/owner |
| Bootstrap/archive | 167 | Startup seed/import, compatibility archive and process shutdown |
| Test/example | 133 | Built-in smoke/demo and undeclared reference extension |
| Fixed owner | 132 | Local facade/membership bridge and private built-in module namespace |
| Legacy | 78 | Legacy fallback/archive/preset excluded from concurrent contextual authority |
| Receipt guarded | 35 | Explicit application resource service with captured provenance |

Every entry records path, line, enclosing function, expression, class, proof and
an enclosing-scope AST digest. The test rejects changed inventory or consumer
scope until its effects are reviewed again. `command_history` is included along
with the obsolete `commandHistory` spelling; application/metadata services are
included explicitly. One dynamic lookup is WorkspaceContext's compatibility
application-capability delegation; named config/editor/shell/history/tool fields
are fixed facade properties. Literal `pyzo` import aliases and imported named
context values are recognized by the scanner and its fixture.

New **LOCAL** evidence is
[consumer effects](../../deps/pyzo/tests/test_workspace_census_consumers.py),
[all ingress commands](../../deps/pyzo/tests/test_workspace_ingress.py),
[tool ID translation](../../deps/pyzo/tests/test_workspace_persistence_projection.py)
and the [real scale replay](../../spikes/peer_frames/qt_workspace_scale_probe.py).
It supplements every affected row below. Existing evidence codes were rerun by
the complete unit and live suites, not inferred from the older dated census.

## Storage, copy and live-update contracts

`WorkspaceContexts` snapshots default/site/user contextual values once per owner.
The atomic workspace generation stores `profile.contextual` schema 1 with
`config`, `history`, `tool_states` and `loaded_tools`. Unknown valid fields survive
capture and restore. Missing contextual data imports legacy defaults; malformed
or future contextual containers isolate that workspace as an opaque unavailable
record. Advanced preference leaf values retain Pyzo's existing value semantics;
this does not claim per-leaf type validation.

The owner-thread census runs every second. Changed preferences/history/tool
states enter the existing one-second retention checkpoint: two seconds of
scheduling plus writer/event-loop latency. Live editor/shell setters, dock
margins, status and affiliation project on the context census. Operational
preferences are read at the next operation; tool filters are read at the tool's
next refresh/action or reconstruction. Creation defaults do not rewrite existing
document format/indentation. Changing a shell profile never mutates a running
interpreter's launch snapshot.

`pyzo.application.workspace_context.copy(source, destination)` copies contextual
configuration, command history and retained tool state as deep snapshots. It
reloads destination tools against their new config and applies destination live
preferences. It preserves the destination loaded-tool set. This explicit service
API adds no new copy UI. It neither copies shared document text, live interpreters,
installation files nor creates continuing propagation. Requests for application
capabilities copy as requests; effective values remain application/interpreter
capabilities. Application/compatibility fields in the archived seed remain
non-authoritative contextual residue.

Scope notation in the tables:

- **W**: durable workspace snapshot; deep-copy permitted; owner-only updates.
- **V**: view state under its workspace, captured where specified; reconstructed
  mechanics/results are not copied as live resources.
- **R**: shared document or interpreter resource; identity-linked, never aliased
  through contextual preference copy.
- **A**: explicit application installation/capability/service; shared, no
  contextual copy or owner-specific live mutation.
- **K**: legacy archive/compatibility state; preserved for non-peer paths, excluded
  from peer authority.
- **Q**: per-workspace request, effective A/interpreter capability; shown by
  Settings → Workspace effective settings. Runtime language/theme/Qt style/scale
  remain application-wide. Debugger selection is independent only when the
  current eligible interpreter advertises it, otherwise shared/unavailable.

Executable evidence codes:

- **CFG**: [census/default/dynamic/copy/capability tests](../../deps/pyzo/tests/test_workspace_context.py).
- **STORE**: [contextual schema/opaque isolation and atomic generation tests](../../spikes/peer_frames/test_workspace_persistence.py).
- **TOOLS**: [real ten-tool, two-kernel, close/reopen/restart probe](../../spikes/peer_frames/qt_workspace_tools_probe.py).
- **DOC**: [document resources](../../spikes/peer_frames/test_document_resources.py),
  [Qt retention](../../spikes/peer_frames/test_qt_document_retention_probe.py),
  [workspace recovery](../../spikes/peer_frames/test_workspace_recovery.py).
- **RUN**: [routing](../../spikes/peer_frames/test_execution_routing.py),
  [native execution](../../deps/pyzo/tests/test_workspace_execution.py),
  [run variants](../../deps/pyzo/tests/test_workspace_run_commands.py).
- **DEBUG**: [accepted Stage 5](workspace-debugger-2026-10-06.md) and its final
  real-kernel replay rerun in Stage 6.
- **LIFE**: [workspace lifecycle](../../spikes/peer_frames/test_workspace_lifecycle.py),
  [native close](../../deps/pyzo/tests/test_workspace_close.py),
  [application lifecycle](../../spikes/peer_frames/test_application_lifecycle.py).
- **UI**: [model](../../spikes/peer_frames/test_contract.py),
  [status](../../spikes/peer_frames/test_status.py),
  [native runtime](../../deps/pyzo/tests/test_workspace_runtime_qt.py), full
  peer/legacy smoke and TOOLS affiliation assertions.
- **PROV**: [native provenance acceptance](native-provenance-2026-10-05.md),
  parser and execution tests plus the real held-reply replay rerun in Stage 6.

## Configuration rows

The original source census enumerates every default leaf and every discovered
built-in dynamic field. CFG walks all current default leaves/empty containers,
checks explicit shared exceptions, independent mutations and capability request
retention. All other current/dynamic/unknown fields default to W, including late
extension fields introduced after seeding. No mutable fallback aliases the
application tree. Dynamic third-party keys remain open-ended W namespaces.

| Row | Final owner, storage/copy | Live update and compatibility treatment | Evidence |
| --- | --- | --- | --- |
| C01 | W config, A defaults/site/user import/archive | Seed once; checkpoint nested edits; legacy config save remains K/A | CFG, STORE, TOOLS |
| C02 | W find defaults; V needle/results | Capture active local group's flags; other local pane state remains V; next host uses W defaults | CFG, TOOLS, UI |
| C03 | W view records linked to R documents; flattened editorState2 K | Retention/view membership authoritative; compatibility list never selects peer owner | DOC, STORE, LIFE |
| C04 | W loaded tool IDs and placement | Exact saved tool set; semantic tool_panes map translates changed primary/secondary prefixes; two exact old forms supported; old loadedTools K | TOOLS, STORE, UI, LOCAL |
| C05 | K windowGeometry/windowState | Non-peer Qt restore only; no concurrent authority/copy | UI peer/legacy controls |
| C06 | W sessions; A loaded-owner manifest | Capture/restore each runtime; old peerWorkspaceSession K | STORE, TOOLS, UI |
| C07 | K named views; legacy topology presets | Remain compatibility snapshots, do not instantiate/replace concurrent owner identity | UI peer/legacy controls |
| C08 | A onboarding marker | Shared account/process startup gate, not preference copy | CFG, UI |
| C09 | W rendering preferences; V projection | Existing local editors/shells project applicable setters; derived paint not copied | CFG, TOOLS |
| C10 | W font/zoom/popup/margin/status/theme-popup option; Q qtstyle | Owner-only live controls/status; Qt style effective A; single-owner legacy preserved | CFG, TOOLS, UI |
| C11 | W file/editor creation defaults | New local editor/next formatting operation reads owner; existing R format stays authoritative | CFG, DOC, TOOLS |
| C12 | W editing/introspection preferences | Local live setters or next owner operation; native receipt guards remain | CFG, PROV, TOOLS |
| C13 | W changeDirOnFileExec | Invoking editor context also for closed Main; read on run, no background directory action | CFG, RUN |
| C14 | Q language/theme requests; A effective libraries | Requests preserved through menus/restart; explicit capability report, no focus-driven global switch | CFG, TOOLS |
| C15 | Q scale request; A effective Qt scale | Process capability retained/reported; no live owner scaling claim | CFG |
| C16 | A legacy floating-shell gate | Existing compatibility gate; peer panes use their backend | CFG, UI |
| C17 | W operational preferences except A native-dialog gate | Delay/line limits project locally, file handling/reload/find timeout read at operation; native chooser is shared process capability | CFG, DOC, TOOLS |
| C18 | A application close confirmation; W retained titleText, K legacy consumer | Peer pane titles derive document/shell metadata; legacy main-window formatting alone reads the application archive; exit aggregates live owners | CFG, LIFE, UI |
| C19 | A keyboard map, including dynamic shortcuts2 children | Explicit shared UI capability; contextual copy does not change shortcuts; action context still fixed by invoking owner | CFG, UI |
| C20 | W shell profile structs | Deep-copy templates; later edits affect next launch/dialog only | CFG, TOOLS, RUN |
| C21 | R launch/startup snapshot from W profile/project | Captured owner-specific launch fields; not live interpreter transfer/copy | RUN, TOOLS |
| C22 | W unknown tool config, V tool state; A code install | Unknown data retained; declared explicit context or local visible refusal before import; no arbitrary metadata eval | CFG, STORE, TOOLS |
| C23 | W file-browser path/filter/expanded dirs | Own module/config/resource context; next local refresh/action or reload | CFG, TOOLS |
| C24 | W project records/options | Own starredDirs snapshots; project membership does not choose owner; next local launch/file action | CFG, TOOLS, RUN |
| C25 | W namespace filters; V namespace path; R values | Distinct local eligible-shell proxy; path captured, values queried afresh | CFG, TOOLS, PROV |
| C26 | W snippet filters/path; V search; A/R snippet files | Local search captured; editing referenced shared snippet files remains explicit | CFG, TOOLS |
| C27 | W source-tree options; V tree; R local source | Local editor following; level/types read on next refresh; derived tree rebuilt | CFG, TOOLS, PROV |
| C28 | W help options; V history/query/pause; R response | Capture query/history/pause; local-shell receipt guards; next formatting refresh uses config | CFG, TOOLS, PROV |
| C29 | W browser zoom/bookmarks; V URL/back/forward | Restore navigation without automatic fetch; network results not copied | CFG, TOOLS |
| C30 | K obsolete noNewlines and empty logger config | Preserve archive, no peer semantics; logger console is V, diagnostics A | CFG, TOOLS |

## Non-config persistence rows

| Row | Final owner, storage/copy | Live update and compatibility treatment | Evidence |
| --- | --- | --- | --- |
| P01 | W commands/date markers/cap in contextual history | Owner history viewers/shell navigation; bootstrap imports legacy once, new owner empty; deep copy resets destination signal | CFG, TOOLS |
| P02 | A theme definitions/files/registry; Q selection | Referenced library remains shared; workspace selection request reported with effective A | CFG, TOOLS, UI |
| P03 | A installed tool modules and snippet libraries; W selections/config | Private owner module namespaces/instances; explicit shared-file edits remain file actions | TOOLS, PROV |
| P04 | R retained documents and recovery, W memberships; A manifest | Atomic generation/checkpoints; independent unavailable records; no user-file background writes | DOC, STORE, LIFE |
| P05 | A diagnostic traces/logs, V logger consoles | Multiple subscribers to shared diagnostics; closing/reloading one removes only its subscription | TOOLS, UI |
| P06 | R user-file bytes, identity linked across W | Only explicit Save/Run-as-Script changes file; contextual snapshot copy never copies/rewrites bytes | DOC, RUN, LIFE |

## Runtime rows

| Row | Final owner, storage/copy | Live update and compatibility treatment | Evidence |
| --- | --- | --- | --- |
| L01 | A service catalogs; W fixed contextual facades | Existing globals remain compatibility/application entry points; native contextual consumers bind durable owner | CFG, TOOLS, PROV |
| L02 | W model/frame/group/pane topology | One runtime per owner, plus non-persisted empty bootstrap for zero-available construction; no live alias via profile copy | UI, STORE, TOOLS |
| L03 | W backend projection; V native mechanics | Reconstructed runtime bindings after reopen; private docks; backend objects not persisted/copied | UI, TOOLS |
| L04 | W local foreground editor/shell; V invoking command | Focus updates only that owner's foreground; no foreign fallback for tools/commands | TOOLS, RUN, PROV |
| L05 | W frame geometries; A OS activation service | Live native registry refresh before geometry capture; disposed runtime empty; visible affiliation with several owners; physical WM behavior remains open | UI, TOOLS, LOCAL |
| L06 | W status visibility; V cursor/status projection; A diagnostic messages | Fixed owner visibility delegate; refresh local frames; same source message may project shared diagnostics | CFG, TOOLS, UI |
| L07 | A command descriptors/keymap; W/V QAction context | Programmatic synchronization blocks mutation signals; captured tool launcher changes original owner only | UI, TOOLS, RUN |
| L08 | K named-view selector/MRU | Legacy selector stays independent of concurrent workspace catalog; not profile copy authority | UI |
| L09 | R durable document identity/content/history; W view membership | Shared edits propagate through authoritative resource, private placement/cursor; no contextual copy of text | DOC, STORE |
| L10 | R disk signature/format/conflict metadata; V marker | Reassess unavailable/reopened resources; persistence retains bytes/history; no background user-file write | DOC, STORE, LIFE |
| L11 | V cursor/selection/scroll/indicators; W rendering defaults; R text | Restore V records; local preference projection; parser/paint rebuilt | DOC, CFG, UI |
| L12 | W Main identity; V pin/MRU/dialog path | Main survives no open view; native local manager operations; copy preferences does not duplicate view membership | DOC, RUN, LIFE |
| L13 | V live find state; W persisted find flags | Capture active local group options; Replace All snapshots invoking owner views, shared R edits propagate; live needle/results local | CFG, UI, LOCAL |
| L14 | V parser/completion buffers with R source and fixed receipts | Shared parser service A but captured owner/source guards reject stale consumers; no live future copy | PROV, TOOLS |
| L15 | W breakpoint overlay; R/V source lines/session indicators | Stage 5 independent overlays and fixed debug snapshots; no migration overlays/zombies | DEBUG |
| L16 | W shell view; R interpreter/broker; W profile snapshot | Local eligible shell lookup; initial release fixed ownership, close terminate/cancel; no revive/transfer in copy | RUN, LIFE, TOOLS |
| L17 | W foreground shell eligibility | Empty/starting/restarting/missing tool resource stays local empty; ordinary controls can select a starting local view | RUN, TOOLS, UI |
| L18 | V explicit assignment, W implicit resolver | Captured invoking view/owner; broken target visible; no preference-copy assignment link | RUN, PROV |
| L19 | R interpreter state/startup/cwd; V console | New queries use local eligible kernel; restored tools keep views but never revive old interpreter values | TOOLS, RUN, DEBUG |
| L20 | V shell edit-history cursor/console; W command list | Navigation/appends read own history; transient cursor/output not copied | CFG, TOOLS, RUN |
| L21 | V request futures/caches with R generation | Consumer retirement and exact provenance prevent old reload/foreign writes; no future persistence | PROV, TOOLS |
| L22 | A process registry; R owned kernel handles and launch copies | Application shutdown aggregates; workspace close terminates only its owned resources | LIFE, RUN, DEBUG |
| L23 | R debugger state with fixed W provenance; interpreter capability | Independent mode advertised by maintained kernel; unsupported reports unavailable/shared; no stack persistence | DEBUG, CFG, TOOLS |
| L24 | V debugger controls tied to W foreground session | Captured stack action/indicator ownership; source navigation resolves session document/W | DEBUG, PROV |
| L25 | W managers and V builtin widgets; A installation | Ten separate instances, selected state captured; retired owner module trees released; same-owner move/floating; destination creates its own tool instance | TOOLS, CFG |
| L26 | A close coordinator, W/V/R indexed negotiations | Cancel/publication failure preserves exact instances; durable checkpoint precedes retire/dispose | LIFE, TOOLS, DEBUG |
| L27 | A Quit/Restart/zero-frame transaction | Cleanup iterates every owner manager; peers retain existing zero-frame rules; not contextual copy | LIFE, UI, TOOLS |
| L28 | A persistence coordinator; R retention; W unavailable records | Nested contextual edits join ordinary checkpoints; failure remains visible; no teardown before publish | STORE, DOC, LIFE, TOOLS |
| L29 | A ingress service; target W | File/new/external-shell GUI dispatch uses eligible MRU; skip closing/failed/disposed, default only if empty, block exit; file modal rechecks epoch; no project-path owner inference | LOCAL, live ingress |
| L30 | A Qt/platform paths, icons/fonts/theme registry; Q requests | Capability panel preserves requests; affiliation is explicit text/accessibility, independent of theme | CFG, TOOLS, UI |
| L31 | V invocation; W history/preference; R execution | Captured invoking editor determines small-runner config/history, not changed foreground | RUN, PROV |
| L32 | V invocation; W target resolver; R file/kernel | Preserve explicit autosave/recycle/IPython behavior; script successor receipts remain guarded | RUN, PROV |
| L33 | W Main document identity, R retained source | May run without open view; requesting view supplies local behavior preferences | DOC, RUN |
| L34 | V/backend derived timers, selection/paint/dialog mechanics | Reconstructed; PDF source/preview inherits invoking owner; local cursor/group/help/reload/debug-focus callbacks use source identity; semantic state never inferred from mechanics | UI, TOOLS, PROV, LOCAL |

## Built-in tool contract

All ten built-ins are supported with separate widgets and owner-private module
namespaces. Relative imports stay inside that owner's module tree. Each facade
provides local editors, eligible foreground shells, history/config and the local
tool manager. No eligible local editor/kernel means empty/inactive, not another
owner. Moving/floating within the owner's backend retains its facade; this adds
no cross-owner tool-transfer API.

| Tool | Retained state and resource binding | Copy/live/compatibility |
| --- | --- | --- |
| History viewer | W command list; local history signal | Deep copied commands, local updates; no global history save file |
| Workspace namespace | W filters, V namespace path; eligible local shell | Path captured; derived namespace/results queried afresh |
| Snippets | W filters/custom path, V search text | Search captured; application/referenced libraries shared |
| Editor list | Local W editor membership/foreground | Reconstructed list; native placement belongs to ADS, no legacy cross-list sorting |
| Source structure | W level/types; local foreground editor | Rebuild derived tree at refresh; source receipts fixed |
| Logger | V Python console/history; A diagnostics | Distinct consoles/subscriptions; diagnostic text explicitly shared; console interpreter not revived |
| Web browser | W zoom/bookmarks; V URL/back/forward | Navigation retained without restore fetch; rendered pages not captured |
| Expression viewer | V expression text/enabled flags; eligible local shell | Expressions retained; values not revived; stale reloaded consumer reply rejected |
| Interactive help | W format/font; V history/index/query/pause | View state retained; response from local eligible shell only |
| File browser | W path/expansion/filter and project records/options | Local actions/project launch inputs; actual filesystem shared |

An extension must declare literal `workspace_api = 1` and accept
`__init__(parent, *, context)`. It must use that explicit context for contextual
operations; arbitrary third-party Python is not sandboxed. An undeclared tool is
refused before import, with a visible accessible explanation and config preserved.
Discovery accepts literal names or literal translation calls, never arbitrary
metadata code. Declared imports/construction failures appear in that owner's
pane. Legacy mode retains its ordinary extension loading behavior.

See the historical [Stage 6 acceptance](workspace-tools-2026-10-06.md) and current
[036 acceptance/revisions](stage-seven-scale-census-2026-10-08.md).
