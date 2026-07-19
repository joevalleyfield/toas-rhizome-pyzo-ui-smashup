# Experiment 013: Workspace state ownership audit

Date: 2026-07-18

## Result

Pyzo currently has one process-wide configuration tree, one process-wide set of
service singletons, one peer topology, one active editor, one active shell, and
one explicit execution shell. The peer-frame work removed window privilege but
did not introduce concurrent workspace identity. Existing named “views” are
switchable snapshots of that one topology.

The grounded concurrent-workspace model is therefore forward direction, not a
description of current implementation. This audit records that direction as
provisional scope only. It assigns no severity, priority, migration order, or
implementation prescription.

## Evidence method and coverage

The census used five complementary passes:

1. Parsed every leaf and empty container in
   `deps/pyzo/pyzo/resources/defaultConfig.ssdf`.
2. AST-scanned all Python below `deps/pyzo/pyzo` for direct
   `pyzo.config...` reads and writes.
3. Manually traced aliases and dynamic access (`self._config`, `self.config`,
   `setdefault`, subscripts, `setattr`, the advanced settings editor, shell
   structs, and tool discovery).
4. Searched Pyzo and `spikes/peer_frames` for filesystem stores, restore/save
   entry points, service singletons, manager registries, topology snapshots,
   lifecycle state, shell/kernel channels, and mutable runtime caches.
5. Ran the focused existing unit suites for workspace sessions, recovery,
   document/shell lifecycle, application lifecycle, status, and command
   projection: 88 tests passed.

The matrix groups leaf fields only where they have the same producers,
consumers, lifetime, current scope, and candidate scope. The source census at
the end maps every discovered persisted leaf/container to a matrix row. Dynamic
third-party tool configuration is necessarily open-ended; row C22 records the
namespace contract that covers each discovered-at-runtime extension key.

Evidence notation uses repository-relative paths and line numbers as observed
at coordinating revision `dc749ce` and nested Pyzo revision `b3af8d9`.

## Scope vocabulary

- **Application**: one running Pyzo process or its one saved user profile.
- **Workspace**: the provisional concurrent profile-like unit grounded by
  Experiment 013; no such current runtime identity exists.
- **Pane/view**: one visible editor, shell, tool, or other dock projection.
- **Shared resource**: document content/identity or kernel state that may have
  views in more than one workspace.
- **Mixed**: storage and effective behavior participate in different scopes.

## Persisted configuration matrix

Each row has all ten required fields in this order: identity; storage/source;
producers; consumers; persistence/lifetime; current effective scope;
mixed-scope notes; provisional candidate future scope; evidence; unresolved
questions.

| ID | State identity | Storage/source | Producers | Consumers | Persistence/lifetime | Current effective scope | Mixed-scope notes | Provisional candidate future scope | Supporting evidence | Unresolved questions |
|---|---|---|---|---|---|---|---|---|---|---|
| C01 | Config overlay and save authority (`pyzo.config`, `_saveConfigFile`) | Built-in `defaultConfig.ssdf`, optional `siteConfig.ssdf`, user `config.ssdf`; backup `config.ssdf.bak` | `loadConfig`, runtime mutators, advanced settings editor, `saveConfig`, reset/backup/restore | Every config consumer; startup and shutdown | User config survives restart; site/default overlays are startup inputs; reset suppresses the next save | Application | One recursive object combines preferences, session state, tool state, and compatibility fields; site config may inject keys absent from defaults | Workspace-owned profile trees for contextual settings, with an explicit application-owned layer for truly process-wide settings; snapshot copy between workspaces | `_start.py:155-225`; `core/menu.py:2858-3157` | Exact schema/versioning for splitting the monolith is intentionally deferred to follow-up analysis |
| C02 | Find option persistence: `state.find_regExp`, `find_matchCase`, `find_wholeWord`, `find_show`, `find_autoHide` | `config.ssdf` | Active editor group's find widget during config save | Every newly created `FindReplaceWidget`; restore initialization | Survives restart; captures one active group's state | Application storage, active-editor-group producer | The stored value is process-global even though each editor host owns a separate find widget and live needle/results | Workspace defaults, with pane/view live find state | `core/editorGroups.py:184-197`; `core/editorTabs.py:430-452` | Whether find option changes should synchronize live across panes inside a workspace remains open |
| C03 | Open-editor session: `state.editorState2` entries `(filename, cursor, scroll, pinned/main, history)` | `config.ssdf` | `EditorGroupManager.saveEditorState` / legacy `EditorTabs.saveEditorState` | Editor restore, group redistribution in peer mode | Named files only; survives restart; untitled text and dirty content are excluded | Application session | A flattened list is collected across groups; frame/group/workspace ownership is absent. Main and MRU markers are embedded in the list | Workspace-owned open-view set and view state; document identity/content may be shared resources; main is a separate workspace designation | `core/editorGroups.py:184-214`; `core/editorTabs.py:1780-1890`; `core/main.py:657-675` | Exact serialization for several workspace views of one document is open |
| C04 | Loaded tools: `state.loadedTools` and peer session `loaded_tools` | `config.ssdf`; nested in peer/named-view snapshots | `ToolManager.getLoadedTools`, legacy window save, `WorkspaceSessionService.capture` | Startup restore, view/session restore | Survives restart and named-view switching | Application/session snapshot | Tool configuration is global while loaded instances and placement are captured as one topology | Workspace-owned tool-view set; tool preferences classified separately per C22-C30 | `core/main.py:1194-1201,3285-3316`; `spikes/peer_frames/workspace_session.py:35-43` | Whether a tool implementation supports more than one simultaneous instance is tool-specific |
| C05 | Legacy `state.windowGeometry` and `state.windowState` | Base64 Qt blobs in `config.ssdf` and legacy named views | `QMainWindow.saveGeometry/saveState` | Legacy `restoreGeometry/restoreState` | Survives restart/view switch; unused by peer startup | Application/window compatibility state | Backend-specific opaque state includes tools and geometry; it is not a resource model | Remain legacy-only; no role in concurrent peer workspaces | `core/main.py:3285-3349`; `core/views.py:70-130` | None with meaningful downstream effect in peer mode; no probe needed because the peer branch does not read these blobs |
| C06 | `state.peerWorkspaceSession`: schema, layout, frame geometries, loaded tools | Structured SSDF subtree in `config.ssdf` | `saveConfig`, peer view save/switch, `WorkspaceSessionService.capture` | Peer startup restore and normal-view lookup | Survives restart; one snapshot replaces the previous one | Application peer session | Named “workspace” storage contains exactly one topology and no workspace identity, preferences, documents, kernels, or recovery linkage | One workspace snapshot per workspace identity; process session separately records the loaded workspace set and shared-resource links | `_start.py:206-225`; `core/main.py:1203-1212`; `core/views.py:70-165`; `spikes/peer_frames/workspace_session.py:19-111` | Process-session format for several loaded workspaces remains open |
| C07 | Named views: `state.views[]` (`name`, legacy window fields or `workspaceSession`) and live current name | `config.ssdf`; `_currentViewName` in `ViewManager` | View dialog add/update/rename/remove/select | View history/dialog and session restore | Named snapshots survive restart; current name survives only while process lives, though list order records recency | Mixed application persisted snapshots plus live selector | Selecting a view replaces the single active topology; it does not load a second workspace. Captures are independent snapshots | Workspace snapshots/templates may remain a separate concept; a loaded workspace must have stable identity rather than being a selected view | `core/views.py:45-208` | Whether named views become workspace templates, layout presets, or stay compatibility-only is open |
| C08 | First-run marker `state.newUser` | `config.ssdf` | Wizard setter | Startup default-tool choice; wizard display path is disabled | Survives restart | Application/user profile | It changes initial tool loading but currently has no workspace identity | Application/account onboarding state; copied only by explicit whole-profile snapshot if desired | `core/main.py:682-694,1194-1200`; `util/pyzowizard.py:227-230` | No consequential ambiguity; disabled wizard branch needs no runtime probe |
| C09 | Editor/shell content rendering: `view.showWhitespace`, `showLineEndings`, `showIndentationGuides`, `wrap`, `highlightCurrentLine`, `highlightMatchingBracket`, `edgeColumn` | `config.ssdf` | View menu actions and advanced editor | Editors/shells at construction and live menu propagation | Survives restart | Application preference applied to many views | Some fields apply only to editors, bracket matching also to shells; live instances are view state derived from one global preference | Workspace contextual preference, with a possible later per-view override | `core/baseTextCtrl.py:327-383`; `core/editor.py:254-270`; `core/menu.py:908-1110` | Per-view override chrome is not defined and is not required initially |
| C10 | Shared UI rendering: `view.fontname`, `zoom`, `autoComplete_popupSize`, `widgetMargin`, `qtstyle`, `showStatusbar`, optional `autoComplete_withTheme` | `config.ssdf`; optional key may come from site/user config | View/menu actions, style initialization, status toggle | Editors, shells, tools, peer status projections, Qt application style | Survives restart; `autoComplete_withTheme` has no default | Mostly application, with widget-derived live copies | Font/zoom/margins affect many pane types; status visibility is projected identically to every peer frame; Qt style is process-wide in Qt | Split: Qt style likely application capability; workspace owns contextual font/zoom/status preferences projected to its panes | `core/baseTextCtrl.py:327-383`; `core/menu.py:848-1110`; `core/main.py:3360-3405`; `core/statusbar.py:43-72` | Whether Qt permits safe different widget styles per workspace requires later capability analysis |
| C11 | File/editor defaults: `settings.defaultStyle`, `defaultIndentWidth`, `defaultIndentUsingSpaces`, `defaultLineEndings`, `justificationWidth` | `config.ssdf` | Menus/advanced editor; line-ending default initialized from platform | New editors and editing operations | Survives restart; copied into document/view properties at creation | Application default, then per-document/view live state | Changing a default does not necessarily rewrite existing editor properties | Workspace contextual defaults; actual parser/indent/EOL remain document/view state as appropriate | `core/editor.py:78-100,224-276,390-429`; `core/baseTextCtrl.py:371-383`; `core/menu.py:2237-2285` | Whether indentation preference is document content metadata or view policy remains mixed by design |
| C12 | Editing/introspection behavior: `settings.autoIndent`, `autoCallTip`, `autoComplete`, `autoComplete_keywords`, `autoComplete_caseSensitive`, `autoComplete_acceptKeys`, `autoComplete_minChars`, `autoClose_Quotes`, `autoClose_Brackets`, `removeTrailingWhitespaceWhenSaving` | `config.ssdf` | Settings menus and advanced editor | Editor/shell text controls, save path, kernel completion merge | Survives restart | Application preference | Completion combines view, editor parser, source parser, and selected shell/kernel state | Workspace contextual preferences; shell/kernel-derived results remain shared-resource/session state | `core/baseTextCtrl.py:371-549`; `core/editor.py:619-668`; `core/menu.py:2120-2285`; `core/shell.py:1420-1510` | Independent completion policy per document view is not required initially |
| C13 | Execution preference `settings.changeDirOnFileExec` | `config.ssdf` | Run menu toggle | `RunCommandService.run_file` execute-code message | Survives restart | Application preference, applied to global execution target | Its effect occurs in the selected kernel, which may later be shared across workspaces | Workspace contextual preference; resolved kernel remains shared resource | `core/runCommands.py:252-275`; `core/menu.py:1945-1965` | Cross-workspace shared-kernel cwd interactions require follow-up analysis |
| C14 | Language and syntax theme: `settings.language`, `settings.theme` | `config.ssdf`; theme definitions in resources/app-data | Wizard/menu/theme editor/style initialization | Translation setup, syntax controls and tools, dark-syntax derivation | Survives restart; language generally requires restart; theme is applied to new/live controls through existing paths | Application | Language initializes the process translator; theme data is process registry but consumed by panes | Language likely application/process capability; syntax theme initially workspace preference if widget-level application proves safe | `_start.py:294-302`; `core/main.py:626-650`; `core/themeEdit.py:285-445`; `core/menu.py:2229-2295` | Capability boundary for simultaneous languages/themes is open |
| C15 | Qt scale factor `settings.qtscalefactor` | `config.ssdf`, converted to `QT_SCREEN_SCALE_FACTORS` at startup | Advanced editor | Qt startup environment | Survives restart; effective only next process | Application/process | Cannot vary after Qt startup | Application only | `_start.py:417-428` | None; source establishes the process boundary |
| C16 | Legacy shell floating gate `settings.allowFloatingShell` | `config.ssdf` | Advanced editor | Shell-dock feature construction | Survives restart | Legacy application setting; peer mode always allows floating | Peer capability bypasses the stored preference | Compatibility-only or workspace layout policy if retained | `core/main.py:1550-1568` | No meaningful peer downstream effect; no probe needed |
| C17 | Advanced operational options: `advanced.shellMaxLines`, `fileExtensionsToLoadFromDir`, `autoCompDelay`, `find_autoHide_timeout`, `useNativeFileDialogs`, `autoReloadFilesInEditor` | `config.ssdf` | Advanced editor; “Always reload” prompt mutates auto-reload | Shell buffer, directory open, text-control timers, find timer, dialogs, external-file checks | Survives restart; some values read live, others at widget creation | Application preference | Values act on pane/document behavior but are held globally | Workspace contextual preferences except native-dialog availability, which may remain application capability | `core/shell.py:35-42`; `core/editorTabs.py:430-470,1125-1140,1450-1480`; `core/editor.py:430-510`; `core/baseTextCtrl.py:345-360` | Per-workspace native-dialog preference has no demonstrated need |
| C18 | Lifecycle/title options: `advanced.alwaysAskWhenClosingPyzo`, `advanced.titleText` | `config.ssdf` | Advanced editor | Application exit confirmation; frame/document metadata title formatting | Survives restart | Mixed application lifecycle and presentation | Exit confirmation is process-wide; title formatting is projected from active pane metadata | Keep exit confirmation application-owned; title format may be workspace preference | `core/main.py:1768-1790,3265-3282,3410-3430` | None requiring a probe |
| C19 | `shortcuts2.*`, including dynamic menu-path keys and macOS startup override | `config.ssdf` plus defaults/site overlay | Key-map dialog, advanced editor, platform initialization | `KeyMapper`, menu/action projections | Survives restart; actions update on key-mapping signal | Application command map | Command context is late-bound, but shortcut collisions are registered in one Qt application | Initially application-level shortcut map; workspace-specific command behavior is resolved through context, not duplicate accelerators | `_start.py:180-184`; `core/menu.py:83-150,2670-2825` | Whether users later need workspace-specific maps is open, but no initial requirement exists |
| C20 | Shell profiles `shellConfigs2[]`: `name`, `exe`, `gui`, `pythonPath`, `startDir`, `startupScript`, `argv`, `environ` | SSDF list in `config.ssdf` | Shell config dialog, interpreter helper, advanced restore | Shell creation, restart, kernel broker | Survives restart; each live shell retains a reference to its selected struct | Application profile list | Editing a profile changes the referenced config used by existing shells on next restart; live kernel state is separate | Workspace-owned profile list or explicit snapshot; live shell/kernel remains shared resource and does not become exclusive | `core/kernelbroker.py:30-112`; `core/shellInfoDialog.py:430-735`; `core/shell.py:1185-1260` | Stable profile identity is absent; name/list position are the only current handles |
| C21 | Derived launch fields `KernelInfo.projectPath`, `scriptFile`, `externalshell_callbackport` and startup info copy | In-memory `KernelInfo`; serialized over broker channel, not normally stored in `shellConfigs2` | File-browser project selection, Run as Script, external-shell command | Kernel broker and interpreter startup | Kernel/restart lifetime | Mixed application routing, tool project selection, and kernel resource | Project path is derived from the one loaded file-browser tool; script mode temporarily specializes a profile | Resolve from invoking workspace and selected shared kernel at execution time; do not persist transient script assignment as profile preference | `core/shell.py:70-100`; `core/kernelbroker.py:130-240,380-410`; `core/commandline.py:70-90` | External-shell workspace attribution remains open |
| C22 | Generic `tools.<toolId>.*` extension namespace | Recursive SSDF subtree in `config.ssdf`; keys created when a tool loads | Built-in or user tool code via arbitrary attribute/subscript access; advanced editor | Same tool on later load; advanced editor | Survives restart even if tool is unloaded or removed | Application per tool ID | One config object is shared by the one active tool instance; third-party schema is unconstrained and discoverable only after tool code/data exists | Tool declares application/workspace/view/shared-resource ownership per key; undeclared legacy keys default to workspace snapshot semantics only after follow-up validation | `tools/__init__.py:150-220,340-375`; `core/menu.py:3030-3125` | Third-party keys not present in this checkout cannot be enumerated; the namespace contract is the explicit unresolved finding |
| C23 | File-browser navigation/filter state: `tools.pyzofilebrowser2.path`, `expandedDirs`, `nameFilter`, `searchMatchCase`, `searchRegExp`, `wholeWords`, `searchSubDirs`, `searchExcludeBinary` | Dynamic tool config in `config.ssdf` | Tree navigation/expand-collapse and filter widgets | File-browser tree/search tasks, save dialogs, run project lookup | Survives restart | Application tool instance | Current path can affect save defaults and shell launch project path outside the tool view | Workspace-local tool-view state and contextual preferences | `tools/pyzoFileBrowser/__init__.py:55-145`; `browser.py:20-135,575-695`; `tree.py:90-165,300-330,636-675` | If several file-browser views exist, navigation likely becomes view-local while projects stay workspace-local |
| C24 | Project records `tools.pyzofilebrowser2.starredDirs[]`: `path`, `name`, `addToPythonpath` | Dynamic tool config in `config.ssdf` | Add/remove/rename/toggle project UI; startup normalization | Project selector, save path, shell `projectPath` derivation | Survives restart | Application tool configuration | Filesystem path is shared external reality; record name/options are currently global | Workspace-local project records; explicit snapshot copy; no distinct move abstraction initially | `tools/pyzoFileBrowser/__init__.py:14-25,75-102,129-145`; `browser.py:132-190,430-540` | Richer project identity is deferred |
| C25 | Workspace-tool filters: `hideTypes`, `typeTranslation`, `searchMatchCase`, `searchRegExp`, `searchStartsWith` | Dynamic `tools.pyzoworkspace` config | Tool menus | Workspace-variable proxy/tree | Survives restart | Application tool preference applied to whichever shell is current | Tool named “Workspace” means kernel namespace, not Experiment 013 workspace; data source follows global current shell | Workspace-local tool-view preferences; namespace data belongs to selected kernel resource | `tools/pyzoWorkspace.py:389-410,550-650` | Independent tool-to-kernel binding chrome is not defined |
| C26 | Snippets-tool config: `searchName`, `searchDescription`, `searchCode`, `customSnippetsPath` | Dynamic `tools.pyzosnippets` config | Tool option menu and config initialization | Snippet search and filesystem loader | Survives restart | Application tool preference | Snippet library is external file content; search toggles are view preference | Search toggles view/workspace-local; library path initially workspace contextual preference with explicit copy | `tools/pyzoSnippets.py:15-30,100-150,290-315` | Whether snippet libraries should be application-shared is an explicit future choice |
| C27 | Source-structure config: `showTypes`, `level` | Default/dynamic `tools.pyzosourcestructure` config | Tool controls | Source tree presentation | Survives restart | Application tool preference | Consumes current editor via application routing | Workspace-local tool-view preference | `tools/pyzoSourceStructure.py:20-32,140-170,315-330` | None consequential |
| C28 | Interactive-help config: `smartNewlines`, `fontSize` | Dynamic `tools.pyzointeractivehelp` config | Tool options | Help renderer | Survives restart | Application tool preference | Content source follows global current shell/editor extension | Workspace-local tool-view preference; kernel response is shared-resource data | `tools/pyzoInteractiveHelp.py:430-550` | None consequential |
| C29 | Web-browser config: `zoomFactor`, `bookMarks` | Dynamic `tools.pyzowebbrowser` config | Tool wheel/menu/default initialization | Browser presentation/address entries | Survives restart | Application tool preference | Live navigation history is separate and not persisted | Bookmarks may be workspace preference or application library; zoom is view-local | `tools/pyzoWebBrowser.py:130-180,250-265` | Bookmark ownership is unresolved because the grounded model did not specify browser data |
| C30 | Deprecated/read-only `tools.pyzointeractivehelp.noNewlines` and empty `tools.pyzologger` | Default config, persisted if present | Defaults/site/user/advanced editor only | No current source consumer found | Survives restart inertly | Application compatibility residue | Coexists with replacement `smartNewlines` dynamic field | Compatibility import only; do not silently assign workspace semantics without migration analysis | `resources/defaultConfig.ssdf:73-79`; repository-wide source search | Whether old releases still require round-trip preservation is unresolved |

## External durable stores

| ID | State identity | Storage/source | Producers | Consumers | Persistence/lifetime | Current effective scope | Mixed-scope notes | Provisional candidate future scope | Supporting evidence | Unresolved questions |
|---|---|---|---|---|---|---|---|---|---|---|
| P01 | Command history, date markers, 2,000-command cap | `appDataDir/command_history.py` | Shell command entry, execute-selection statement path, expression viewer; history tool edits | Shell history navigation and history viewer | Survives restart; saved at application exit | Application | Commands from every shell/document are merged and deduplicated globally | Initially workspace-local history because every run/view belongs to a workspace; kernel provenance may be recorded as metadata later | `core/history.py:9-110`; `core/shell.py:845-850`; `core/runCommands.py:155-190`; `tools/pyzoHistoryViewer.py:90-165` | Whether copied workspaces snapshot history is open |
| P02 | User theme definitions and in-memory theme registry | `appDataDir/themes/*.theme`, built-in resource themes, `pyzo.themes` | Theme editor/file installation | Syntax controls and tools | Files survive restart; registry lives for process | Mixed application registry and pane consumption | A saved custom theme becomes globally available even if selection later becomes workspace-local | Application-shared theme library; workspace selects a theme if capability permits | `_start.py:128-153`; `core/themeEdit.py:400-445` | Simultaneous theme capability remains open |
| P03 | User tools and snippets files | `appDataDir/tools`, `appDataDir/snippets` or custom path | User filesystem edits, snippet example copy, tool installation | Dynamic tool loader and snippets tool | External durable content | Application installation/library | Tool code is process-loadable; snippet content may be contextual | Tool installation remains application; snippet-library selection may be workspace-local | `tools/__init__.py:150-215`; `tools/pyzoSnippets.py:290-410`; `util/paths.py:80-105` | Security/trust policy is outside this audit |
| P04 | Dirty-buffer recovery generation: manifest, immutable record files, quarantine; snapshot fields `document_id`, filename, display name, text, encoding, BOM, EOL, disk signature, optional workspace affinity | `PYZO_RECOVERY_DIR` or `appDataDir/session-recovery` | Application-exit retention; save/discard retirement | Peer startup restoration and conflict marking | Survives restart until save/discard retirement; atomic generations | Application recovery store keyed by document | Schema has `workspace_affinity` but current snapshots never set it. Conflict is inferred on restore; recovery is not ordinary file save | Recovery records owned by retaining workspace while document identity/content may be shared; no file overwrite without explicit save | `spikes/peer_frames/session_recovery.py:16-390`; `core/main.py:1793-1968` | Multi-workspace conflict equivalence/history and unloaded-workspace reassessment are not implemented and need follow-up design |
| P05 | Diagnostic logs/traces/screenshots selected by environment/test paths | `PYZO_LOG`, `PYZO_ADS_TRACE`, test temp files, explicit screenshot path | Logging/trace filters and test harness | Developer diagnostics only | File/process/test lifetime | Application diagnostic | May contain activity from all panes/resources; not user workspace state | Application diagnostic with optional workspace metadata | `pyzo/__main__.py:20-35`; `core/pyzoLogging.py:90-125`; `core/main.py:150-215,890-915` | No meaningful downstream product effect; probes omitted |
| P06 | User file content itself | Document filename on filesystem | Explicit Save/Save As, Run as Script autosave, file-browser file tasks | Editor load/reload, interpreter script execution, external programs | External durable reality | Shared resource/external | Ordinary Save is authoritative and separate from recovery; external changes are detected by mtime/content | Shared document resource; conflicts resolved explicitly; branching creates a new identity/path decision | `core/editor.py:330-420,430-730`; `core/runCommands.py:285-305` | In-memory branch identity without on-disk identity remains future design |

## Live application, workspace, pane, document, shell, and kernel state

| ID | State identity | Storage/source | Producers | Consumers | Persistence/lifetime | Current effective scope | Mixed-scope notes | Provisional candidate future scope | Supporting evidence | Unresolved questions |
|---|---|---|---|---|---|---|---|---|---|---|
| L01 | `pyzo.*` service singletons: main/application controller, editors, shells, parser, tools, commands/projectors, run/shell commands, workspace session, metadata/status | Module namespace references | Startup `_populate` | Nearly all application code | Process lifetime | Application | Non-window controller removed host privilege but retained singleton cardinality | Application service registry resolving explicit workspace context; workspace-owned service instances where contracts require | `_start.py:390-432`; `core/main.py:735-1065`; `core/applicationController.py:1-250` | Exact service injection mechanism is follow-up work |
| L02 | Peer topology: pane descriptors, frames, groups, split tree, tab side, per-group active pane, global active pane, ID counters, shutdown flag, close policies | `WorkspaceModel` in memory; serialized subset in C06 | Application pane registration and user/backend gestures | Backend render, commands, lifecycle, metadata | Process lifetime; subset persisted | Application topology called “workspace” | No workspace ID or pane-to-workspace relation exists; all panes inhabit one model | One process coordinator containing multiple workspace-owned topology roots, or equivalent explicit workspace ID on every pane | `spikes/peer_frames/contract.py:186-535,740-870` | Representation choice is open; recursive workspace composition is rejected |
| L03 | Backend projection state: dock/frame maps, last snapshot/results/errors, projected activation, sync/repair flags, native widget properties | `QtAdsPeerFrameBackend` fields and Qt objects | Render, QtADS signals/events, lifecycle filters | Reconciliation and visibility repair | Backend/process lifetime; not persisted directly | Application/backend cache | Mirrors L02 and may lag during queued sync; not semantic authority | Application backend cache partitioned/indexed by workspace and pane identity | `spikes/peer_frames/qtads_backend.py:65-170,180-380` | No unresolved semantic question; backend state remains derived |
| L04 | Active command context: active pane/frame/group and active editor group | `WorkspaceModel.active_pane_id`, group active IDs, `EditorGroupManager._activeGroup` | Settled dock focus, model activation, editor current-change | Commands, dialogs, metadata, editor operations | Live process only | Application-selected pane/view | Focus intentionally does not select execution target | Every pane has workspace; command invocation resolves workspace from invoking/current pane | `core/main.py:1214-1240`; `core/editorGroups.py:20-75`; `contract.py:365-404` | Behavior when no pane is current but a workspace command is invoked needs future chrome |
| L05 | Live frame geometry and window activation | Qt floating-container geometry and window manager state | User/OS/backend | Session capture, dialog parenting, frame placement | Live; geometry persisted in C06 | Per frame inside one application topology | Geometry is frame state, but snapshot currently belongs to the only application session | Workspace-owned frame/view geometry; process session records loaded set | `spikes/peer_frames/workspace_session.py:35-50,100-111`; `qtads_backend.py:65-170` | Multi-monitor normalization is outside initial semantics |
| L06 | Status snapshot: message, cursor text, visibility; clear timer and subscribers | `StatusState`, `PeerStatusService`, projections | Metadata, commands, recovery notifications, timers | Every peer frame status projection | Process lifetime; visibility preference persisted through C10 | Application projection | One cursor/message is mirrored into every frame even when frames later belong to different workspaces | Workspace status state selected/projected by pane; application messages need an explicit application channel | `spikes/peer_frames/status.py:1-55`; `core/statusbar.py:43-72`; `core/main.py:985-1028` | Precedence between application and workspace messages is open |
| L07 | Command descriptors, key mapper, QAction projections, enabled/checked state caches | CommandRegistry/ShellCommandService/menu and projector objects | Startup registration; context and shell signals | Menus/toolbars/shortcuts | Process/widget lifetime; shortcuts persisted C19 | Mixed application command definitions, active-context evaluation, per-widget projection | Shell toolbar “current” actions use the shell in that host; Run/Debug controls use one execution target | Application command definitions with workspace/pane context; each view projects state appropriate to its workspace/resource | `spikes/peer_frames/commands.py:1-185`; `core/shellCommands.py:15-230`; `spikes/peer_frames/qtads_commands.py:60-260` | Some future commands may require explicit workspace chooser semantics |
| L08 | Current named-view selector and MRU order | `ViewManager._currentViewName`; `state.views` list order | View selection/rename | View dialog and save behavior | Selector live; order persisted | Application | This is snapshot selection, not workspace affinity | Keep separate from concurrently loaded workspace identity | `core/views.py:45-105,130-205` | See C07 |
| L09 | Document identity/content: `FileItem.lifecycleId`, path-or-temp `id`, editor filename/name, QTextDocument text/dirty/undo | FileItem/PyzoEditor/QTextDocument | New/load/edit/save/Save As/recovery restore | Editors, parser, run commands, close/recovery lifecycle | Live document; filename content external; dirty recovery P04 | Shared object only within its single editor view today | Lifecycle ID is stable only for the live `FileItem`; path-based ID changes on Save As; no second view of same document exists | Shared document identity/content across workspace-owned views; explicit branch creates new identity | `core/editorTabs.py:145-215`; `core/editor.py:210-420,430-730`; `core/main.py:1400-1425,1793-1865` | Durable identity independent of path/recovery ID is unresolved |
| L10 | Document disk/provenance state: encoding/BOM/EOL, `_modifyTime`, loaded bytes, trailing-whitespace mode, recovery ID/signature/encoding/conflict | PyzoEditor attributes and recovery snapshot/restore attributes | Load/save/external check/recovery restore | Save/reload prompts, status/title, recovery retirement | Document lifetime; subset persisted P04 | Mixed document resource and recovery session | Ordinary external-file handling stores only a moving mtime/byte baseline; recovery conflict is a boolean and status/title marker. Timestamps/metadata are not fully surfaced | Shared document provenance plus workspace-local conflict history; identical loaded conflicts may resolve together | `core/editor.py:250-420,430-550,619-730`; `core/main.py:1793-1968` | Conflict-equivalence metadata and propagation contract require implementation design |
| L11 | Editor view state: cursor/selection, scroll, focus, parser presentation, indentation/wrap/font/zoom, run highlight | Editor widget/QTextCursor/scrollbars | User navigation and commands | Status, find, Run/Debug Jump, persistence C03 | View lifetime; cursor/scroll subset persisted for named files | Pane/view | Content and Qt document are currently inseparable from the one editor widget | Workspace-owned view over shared document content; migration carries all view-local state | `core/editor.py:250-290,430-460`; `core/editorTabs.py:1810-1890`; `core/runCommands.py:130-250` | Qt document/view separation capability needs later implementation analysis |
| L12 | Pin, main designation, editor MRU, last file-dialog path | `FileItem._pinned`; each `FileTabWidget._mainFile/_itemHistory`; `EditorTabs._lastpath` | Context menu, current change, load/save dialogs, restore | Close policy, Execute Main, tabs/history dialog | Live; pin/main/MRU partly persisted C03; last path live | Mixed per-host and application manager behavior | Peer mode has one `FileTabWidget` per document, so main is stored per host and `EditorGroupManager.getMainEditor` searches hosts. Save As changes item ID without updating `_mainFile` | Pin/MRU are view/workspace state; each workspace owns one main document identity that follows app rename/Save As and may exist without a pane | `core/editorTabs.py:800-880,1035-1060,1080-1100,1180-1210,1280-1360,1810-1890`; `core/editorGroups.py:85-105`; `core/menu.py:1825-1840` | Current main behavior across peer hosts is source-clear but semantically incomplete; future pathless-main save UX is grounded but unimplemented |
| L13 | Live find/replace needle, replacement, replace mode, current editor, result counts, auto-hide timers | Each `FindReplaceWidget` | User interaction/current editor change | Find/replace operations and UI | Pane/widget lifetime; only option booleans persist C02 | Pane/view | Each editor host has its own widget, while config save captures only the active host's option state | View-local state within owning workspace | `core/editorTabs.py:230-760`; `core/editorGroups.py:184-197` | No meaningful effect outside owning view; no probe needed |
| L14 | Source parser request/result caches and editor completion/calltip buffers | Parser thread dictionaries; BaseTextCtrl buffers/timers | Editor text/change/introspection | Source structure, fictive completion, calltips | Process/document-view lifetime | Mixed application parser cache keyed by mutable editor ID, plus view buffers | Editor ID is path/temp name, so Save As can change lookup identity; shell results depend on current shell | Cache by durable document/view identity; shell-derived cache includes kernel provenance | `core/codeparser.py:45-145`; `core/baseTextCtrl.py:340-550`; `core/shell.py:1360-1515` | Cache invalidation for shared document views is open |
| L15 | Breakpoints and debug line indicators | Editor block metadata; per-host and aggregate breakpoint dicts; per-editor indicator | Editor toggle/restore; debugger stack state | Every live shell's breakpoint channel, debugger navigation | Live editor/kernel lifetime; breakpoints are not in C03 or another durable store | Mixed document path state broadcast application-wide to all kernels | All shells receive the aggregate breakpoints; one selected debugger paints indicators across editors | Breakpoints belong shared document identity (possibly workspace overlays later); debug indicators follow foreground debugger session | `core/editorTabs.py:1070-1225`; `core/editorGroups.py:70-90,220-235`; `core/shell.py:1225-1235,1670-1710` | Whether breakpoint sets are shared or workspace-local is not fixed by the grounding discussion |
| L16 | Shell view/resource identity and lifecycle: host list, shell widget, referenced profile, broker connection, pane lifecycle ID | `ShellGroupManager`, `ShellStackWidget`, `PythonShell`, lifecycle registry | Shell creation, restart, close, peer registration | Menus/tools/run/debug/lifecycle | Live session only | Mixed pane/view and kernel resource; currently one view per kernel | Shell widget, connection, and kernel are effectively 1:1; no durable shell ID beyond object/host/pane names | Shell/debugger views workspace-owned; kernel non-exclusive shared resource; durable live shell identity supports assignment/recycle | `core/shellGroups.py:1-135`; `core/shell.py:1180-1325`; `core/main.py:1545-1645` | Creating a second shell view on an existing kernel is deferred |
| L17 | Foreground/current shell: active host and each host's current widget | `_activeHost`, QStackedWidget current widget | Dock focus and shell selection | Workspace/expression/help tools, shell toolbar current actions, metadata | Live session | Application-selected shell plus per-host current widget | Current shell follows foreground host but is distinct from execution target | Workspace-local most recently foregrounded eligible shell drives implicit routing | `core/shellGroups.py:20-75,120-130`; `core/shellStack.py:150-225`; `core/main.py:1214-1240` | Eligibility definition is future work; initial behavior starts simple |
| L18 | Explicit execution target | `ShellGroupManager._executionHost`; exposed by controller | First shell creation, “use for Run/Debug”, shell removal fallback | All Run commands and debug commands/status labels | Live session only; survives kernel restart because host survives | Application | One target applies to every document and command. Removing it automatically selects active/last host, while merely foregrounding a shell does not change it | Workspace implicit target from foreground shell plus optional workspace-local document-view assignment; no recency fallback queue; broken unexpected target remains visible | `core/shellGroups.py:20-120`; `core/runCommands.py:105-130`; `core/shellCommands.py:50-100`; `core/menu.py:1240-1280,1445-1470,1845-1975` | Chrome and durable live shell identity for broken assignment correction remain open |
| L19 | Shell/kernel live status: interpreter state, debug state, version, builtins/keywords, startup info, start time, cwd state channel, output/prompt buffers | PythonShell fields and Yoton channels; kernel interpreter | Kernel/broker messages and shell polling | Toolbars, metadata, completion, tools, lifecycle, user | Kernel/connection lifetime; reset on restart | Shared kernel resource presented through one shell view | State is stored on the view-side connection but describes the kernel; output text is view-local history of that connection | Kernel state shared; each shell/debug view workspace-owned; capability may permit different view selections | `core/shell.py:1235-1365,1515-1730`; `core/shellStack.py:15-55,150-205` | Output sharing semantics for multiple future views are open |
| L20 | Shell edit-line history cursor (`_historyNeedle/_historyStep`) and console text | Shell widget fields/QTextDocument | User key navigation and stream writes | Shell input UX | Shell-view lifetime | Pane/view over application history P01 | Navigation cursor is view-local but searches global persisted commands | View-local cursor searching workspace-local history initially | `core/shell.py:250-265,460-605,760-850`; `core/history.py:1-110` | None consequential |
| L21 | Shell introspection request state, import attempts, completion/calltip futures and buffers | PythonShell/BaseTextCtrl fields and Yoton request channels | Editor/shell typing, parser suggestions, kernel replies | Completion/help UI | Request/view/kernel lifetime | Mixed active editor view and selected shell/kernel | Response validity checks against global current editor/current shell | Route from invoking view to assigned/implicit kernel with provenance on pending requests | `core/baseTextCtrl.py:340-550`; `core/shell.py:1200-1515` | Cancellation behavior when a view migrates workspaces is open |
| L22 | Kernel manager/broker registry, process handles, broker config copies and ports | `pyzo.localKernelManager`, `Kernelmanager._kernels`, `KernelBroker` | Shell connect/restart/external shell | Shell connections, shutdown cleanup | Process/live-kernel lifetime; not restored | Application resource registry | Kernel configs originate from application profile/tool context; kernels are not workspace-owned today | Non-exclusive application resource registry; every shell/debug view belongs to a workspace | `core/shell.py:60-100`; `core/kernelbroker.py:280-470,790-855`; `core/main.py:1735-1750` | Reconnect/durable kernel identity protocol is open |
| L23 | Kernel debugger and post-mortem state: bdb frames, selected index, mode, traceback provenance, source cache/breaks | Kernel `Debugger`/interpreter and shell `_debugState` channel | Exceptions, debug commands, frame selection, breakpoints | Shell debug UI, execution controls, source navigation, live eval | Kernel lifetime; survives while kernel/session does, lost on death/restart | Shared kernel resource, selected through one application execution target | Several kernels can independently retain sessions; UI currently exposes the execution shell's mode for command enablement | Foreground shell chooses debugger session; controls target that session; live provenance outranks run assignment for post-mortem re-entry | `pyzokernel/debug.py:1-720`; `pyzokernel/interpreter.py:1120-1320`; `core/shell.py:1690-1710`; `core/shellCommands.py:50-105` | Interpreter-specific independent selection capability remains open |
| L24 | Debugger UI stack menu, last frames/index, global editor indicators | `DebugStack._lastIndex/_lastFrames`, shell host `_debugmode`, editor indicators | Current/execution shell debug-state signals and user frame choice | Debug toolbar/menu and editor navigation | Shell-view/session lifetime | Mixed shell pane and application editors | Each host has a stack widget, but debug commands resolve the separate execution target; source navigation opens the global editor service | Foreground shell directly owns visible debugger context; navigation may open/scroll views as current Pyzo permits | `core/shellStack.py:70-205,455-620`; `core/shellCommands.py:45-105` | Mapping navigation into a workspace when no matching view exists is future design |
| L25 | Tool runtime instances and unpersisted state: active tool/dock maps, expression list/results, workspace namespace/proxy path, interactive-help history/pause/lookups, browser back/forward URL history, snippet selection/search text, source-tree selection | ToolManager and widget/proxy fields | Tool load/close and user/kernel/editor events | Tool UIs and requests | Tool/widget/process lifetime; configuration rows C22-C30 persist only selected preferences | Mixed application instance, pane/view UI, current shell/editor resource | Most tools implicitly follow global current editor/shell and support only one instance per tool ID | Every tool view belongs to a workspace; its resource binding and copy/snapshot support are tool-specific | `tools/__init__.py:130-430`; `tools/pyzoExpressionViewer.py:15-230`; `tools/pyzoWorkspace.py:140-380`; `tools/pyzoInteractiveHelp.py:450-630`; `tools/pyzoWebBrowser.py:25-105` | Per-tool multiple-instance capability must be audited when implementing, not guessed here |
| L26 | Document/shell close negotiation: view-to-document map, document view sets, pending dispositions, resolving sets, shell lifecycle map/resolving/disposition | `DocumentViewRegistry`, `ShellLifecycleRegistry` | Pane registration and close/application transactions | Workspace close policy and committed cleanup | Live process transaction state | Application topology lifecycle | Registry can model several views per document, but current editor integration registers one view per `FileItem`; workspace unload does not exist | Registries indexed by workspace-owned views and shared document/kernel resources; final global view forces choice; workspace unload retains dirty state | `spikes/peer_frames/lifecycle.py:60-490`; `core/main.py:1390-1715` | Retained loaded/unloaded workspace lifecycle is unimplemented |
| L27 | Application exit/restart and zero-frame state: phase, disposition, cleanup errors, creation/pending flags, close flag | `ApplicationShutdownCoordinator`, `ApplicationFrameLifecycle`, `MainWindow._closeflag` | Quit/restart/frame closure/application activation | Cleanup, process exit/replacement, default frame creation | Transaction/process lifetime | Application | Workspace shutdown currently means closing the only topology; retained dirty documents are recovery snapshots | Application exit coordinates every loaded workspace; workspace closure is separate and may retain its state | `spikes/peer_frames/application_lifecycle.py:1-230`; `core/main.py:575-600,1715-1790` | Loaded-workspace close confirmation aggregation requires future design |
| L28 | Recovery retention coordinator pending set, loaded issues, conflict flags, quarantine | Recovery coordinator/store and editor attrs | Application exit/restore/save/discard | Exit negotiation, status/title and restore | Transaction plus P04 persistence | Mixed application transaction, document recovery, editor marker | No ordinary background autosave loop; retention occurs at application exit. Workspace unload/final-view retained recovery is absent | Workspace recovery persistence without file overwrite; last view close still forces Save/Discard/Cancel; unloaded conflicts reassess on load | `spikes/peer_frames/session_recovery.py:55-145`; `core/main.py:1793-1968` | Timing/frequency of silent recovery saves inside a loaded workspace is open |
| L29 | Command-line singleton server, pending OS file-open arguments | `commandline.server`, Yoton address, `sys.argv` | Startup/OS events/external Pyzo processes | File open/new/close/external shell dispatch | Process lifetime | Application | Incoming open has no workspace selector and routes to global editor service | Application ingress needs a default/explicit workspace routing rule | `_start.py:20-95`; `core/commandline.py:1-225` | Default workspace for external opens is unresolved |
| L30 | Derived platform/process state: app data/config paths, themes registry, default Qt style, dark flags, icons/fonts, locale, QtADS capabilities, environment-selected peer/recovery/trace modes | Module globals, environment, Qt application/backend | Startup/platform/library detection | All services and rendering | Process lifetime; some inputs external/persisted elsewhere | Application/process capability | These are not ordinary workspace preferences even when panes consume them | Application capability; workspaces store only contextual selections that capability supports | `_start.py:280-432`; `util/paths.py:1-105`; `core/main.py:575-650,3350-3405`; `qtads_backend.py:30-75` | Capability reporting UI for interpreter/debug variants remains open |
| L31 | Execute selection/line/cell/file transient payload: invoking editor/cursor, source text, filename/line/cell name, run highlight, history append | `RunCommandService` stack/local values and shell control message | User command | Resolved execution shell/kernel and editor UI | Invocation only | Application target plus current editor view | Current source buffer is sent without save; all variants use the one execution shell | Same initial assignment resolver for small runners and File/Main, while retaining separate semantic command rows | `core/runCommands.py:90-285`; focused command tests | Future divergence between small runners and File/Main is explicitly allowed but not required |
| L32 | Run File/Main as Script transient launch specialization | Save path plus `KernelInfo.scriptFile`/IPython `%run` messages | User command; editor save | Selected shell/kernel restart or IPython | Invocation/kernel recycle | Application target plus document file | Autosaves, then recycles the selected shell or uses IPython in place; no spawn-new policy | Same resolver as other runners; preserve recycle default and autosave initially | `core/runCommands.py:250-310`; `core/shell.py:1725-1765` | Later recycle-vs-spawn preference is deferred |
| L33 | Main-file command resolution | Per-host `_mainFile` plus current editor manager lookup | Main toggle and editor-state restore | Execute Main/Run Main as Script | Live; path marker in C03 | Mixed host-local storage and application search | Requires an open editor; no workspace identity; pathless file cannot be main through current menu path | One main document identity per workspace; invocation pane selects workspace; pathless designation forces path choice; file need not have open pane | `core/menu.py:1825-1840,1900-1975`; `core/editorGroups.py:90-105`; `core/editorTabs.py:840-860,1870-1890` | Storage for a closed main document is unresolved |
| L34 | Ephemeral widget/backend mechanics with no semantic downstream owner: timers, dialog selection, menu action objects, drag state, paint/overlay caches, test counters | QObject/widget/backend fields | UI events | Same widget/backend only | Event/widget lifetime | Pane/widget or backend | Derived mechanics are intentionally not persisted and do not decide document/kernel/workspace ownership | Remain derived under owning view/backend | Representative evidence: `core/editorTabs.py:230-450`; `core/shellStack.py:290-390`; `qtads_backend.py:85-145` | No meaningful downstream effect found; runtime probes omitted by evidence rule |

## Source census mapping

### Built-in/default config leaves and containers

Every default entry is covered as follows:

```text
advanced.alwaysAskWhenClosingPyzo -> C18
advanced.autoCompDelay -> C17
advanced.autoReloadFilesInEditor -> C17
advanced.fileExtensionsToLoadFromDir -> C17
advanced.find_autoHide_timeout -> C17
advanced.shellMaxLines -> C17
advanced.titleText -> C18
advanced.useNativeFileDialogs -> C17
settings.allowFloatingShell -> C16
settings.autoCallTip -> C12
settings.autoClose_Brackets -> C12
settings.autoClose_Quotes -> C12
settings.autoComplete -> C12
settings.autoComplete_acceptKeys -> C12
settings.autoComplete_caseSensitive -> C12
settings.autoComplete_keywords -> C12
settings.autoComplete_minChars -> C12
settings.autoIndent -> C12
settings.changeDirOnFileExec -> C13
settings.defaultIndentUsingSpaces -> C11
settings.defaultIndentWidth -> C11
settings.defaultLineEndings -> C11
settings.defaultStyle -> C11
settings.justificationWidth -> C11
settings.language -> C14
settings.qtscalefactor -> C15
settings.removeTrailingWhitespaceWhenSaving -> C12
settings.theme -> C14
shellConfigs2 -> C20
shortcuts2.edit__comment -> C19
shortcuts2.edit__copy -> C19
shortcuts2.edit__cut -> C19
shortcuts2.edit__dedent -> C19
shortcuts2.edit__delete_line -> C19
shortcuts2.edit__duplicate_line -> C19
shortcuts2.edit__find_next -> C19
shortcuts2.edit__find_or_replace -> C19
shortcuts2.edit__find_previous -> C19
shortcuts2.edit__find_selection -> C19
shortcuts2.edit__find_selection_backward -> C19
shortcuts2.edit__find_via_file_browser -> C19
shortcuts2.edit__indent -> C19
shortcuts2.edit__jump_to_next_breakpoint -> C19
shortcuts2.edit__jump_to_previous_breakpoint -> C19
shortcuts2.edit__justify_commentdocstring -> C19
shortcuts2.edit__paste -> C19
shortcuts2.edit__paste_and_select -> C19
shortcuts2.edit__redo -> C19
shortcuts2.edit__select_all -> C19
shortcuts2.edit__toggle_breakpoint -> C19
shortcuts2.edit__toggle_comment -> C19
shortcuts2.edit__uncomment -> C19
shortcuts2.edit__undo -> C19
shortcuts2.file__close -> C19
shortcuts2.file__new -> C19
shortcuts2.file__open -> C19
shortcuts2.file__save -> C19
shortcuts2.run__execute_cell -> C19
shortcuts2.run__execute_cell_and_advance -> C19
shortcuts2.run__execute_file -> C19
shortcuts2.run__execute_line_and_print_result -> C19
shortcuts2.run__execute_main_file -> C19
shortcuts2.run__execute_selection -> C19
shortcuts2.run__execute_selection_and_advance -> C19
shortcuts2.run__run_file_as_script -> C19
shortcuts2.run__run_main_file_as_script -> C19
shortcuts2.shell__clear_screen -> C19
shortcuts2.shell__close -> C19
shortcuts2.shell__create_shell_1_ -> C19
shortcuts2.shell__create_shell_2_ -> C19
shortcuts2.shell__create_shell_3_ -> C19
shortcuts2.shell__create_shell_4_ -> C19
shortcuts2.shell__create_shell_5_ -> C19
shortcuts2.shell__create_shell_6_ -> C19
shortcuts2.shell__create_shell_7_ -> C19
shortcuts2.shell__create_shell_8_ -> C19
shortcuts2.shell__interrupt -> C19
shortcuts2.shell__postmortem_debug_from_last_traceback -> C19
shortcuts2.shell__restart -> C19
shortcuts2.shell__stop_debugging -> C19
shortcuts2.view__select_editor -> C19
shortcuts2.view__select_shell -> C19
shortcuts2.view__views -> C19
shortcuts2.view__zooming__zoom_in -> C19
shortcuts2.view__zooming__zoom_out -> C19
shortcuts2.view__zooming__zoom_reset -> C19
state.editorState2 -> C03
state.find_autoHide -> C02
state.find_matchCase -> C02
state.find_regExp -> C02
state.find_show -> C02
state.find_wholeWord -> C02
state.loadedTools -> C04
state.newUser -> C08
state.peerWorkspaceSession -> C06
state.views -> C07
state.windowGeometry -> C05
state.windowState -> C05
tools.pyzointeractivehelp.noNewlines -> C30
tools.pyzologger -> C30
tools.pyzosourcestructure.level -> C27
tools.pyzosourcestructure.showTypes -> C27
view.autoComplete_popupSize -> C10
view.edgeColumn -> C09
view.fontname -> C10
view.highlightCurrentLine -> C09
view.highlightMatchingBracket -> C09
view.qtstyle -> C10
view.showIndentationGuides -> C09
view.showLineEndings -> C09
view.showStatusbar -> C10
view.showWhitespace -> C09
view.widgetMargin -> C10
view.wrap -> C09
view.zoom -> C10
```

- `state.find_regExp`, `find_matchCase`, `find_wholeWord`, `find_show`,
  `find_autoHide` → C02.
- `state.editorState2` → C03.
- `state.loadedTools` → C04.
- `state.windowGeometry`, `windowState` → C05.
- empty `state.peerWorkspaceSession` → C06.
- `state.views` → C07.
- `state.newUser` → C08.
- `view.showWhitespace`, `showLineEndings`, `showIndentationGuides`, `wrap`,
  `highlightCurrentLine`, `highlightMatchingBracket`, `edgeColumn` → C09.
- `view.fontname`, `zoom`, `autoComplete_popupSize`, `widgetMargin`, `qtstyle`,
  `showStatusbar` → C10.
- `settings.defaultStyle`, `defaultIndentWidth`, `defaultIndentUsingSpaces`,
  `defaultLineEndings`, `justificationWidth` → C11.
- `settings.autoIndent`, `autoCallTip`, `autoComplete`,
  `autoComplete_keywords`, `autoComplete_caseSensitive`,
  `autoComplete_acceptKeys`, `autoComplete_minChars`, `autoClose_Quotes`,
  `autoClose_Brackets`, `removeTrailingWhitespaceWhenSaving` → C12.
- `settings.changeDirOnFileExec` → C13.
- `settings.language`, `theme` → C14.
- `settings.qtscalefactor` → C15.
- `settings.allowFloatingShell` → C16.
- `advanced.shellMaxLines`, `fileExtensionsToLoadFromDir`, `autoCompDelay`,
  `find_autoHide_timeout`, `useNativeFileDialogs`,
  `autoReloadFilesInEditor` → C17.
- `advanced.alwaysAskWhenClosingPyzo`, `titleText` → C18.
- every default `shortcuts2.*` leaf and dynamically discovered menu-path key →
  C19.
- empty `shellConfigs2` and every `KernelInfo` profile field → C20/C21.
- empty `tools.pyzologger` and `tools.pyzointeractivehelp.noNewlines` → C30.
- `tools.pyzosourcestructure.showTypes`, `level` → C27.

### Dynamically created built-in tool config


```text
tools.pyzofilebrowser2.path -> C23
tools.pyzofilebrowser2.expandedDirs -> C23
tools.pyzofilebrowser2.nameFilter -> C23
tools.pyzofilebrowser2.searchMatchCase -> C23
tools.pyzofilebrowser2.searchRegExp -> C23
tools.pyzofilebrowser2.wholeWords -> C23
tools.pyzofilebrowser2.searchSubDirs -> C23
tools.pyzofilebrowser2.searchExcludeBinary -> C23
tools.pyzofilebrowser2.starredDirs[].path -> C24
tools.pyzofilebrowser2.starredDirs[].name -> C24
tools.pyzofilebrowser2.starredDirs[].addToPythonpath -> C24
tools.pyzoworkspace.hideTypes -> C25
tools.pyzoworkspace.typeTranslation -> C25
tools.pyzoworkspace.searchMatchCase -> C25
tools.pyzoworkspace.searchRegExp -> C25
tools.pyzoworkspace.searchStartsWith -> C25
tools.pyzosnippets.searchName -> C26
tools.pyzosnippets.searchDescription -> C26
tools.pyzosnippets.searchCode -> C26
tools.pyzosnippets.customSnippetsPath -> C26
tools.pyzosourcestructure.showTypes -> C27
tools.pyzosourcestructure.level -> C27
tools.pyzointeractivehelp.smartNewlines -> C28
tools.pyzointeractivehelp.fontSize -> C28
tools.pyzowebbrowser.zoomFactor -> C29
tools.pyzowebbrowser.bookMarks -> C29
view.autoComplete_withTheme -> C10
tools.<dynamic-tool-id>.<dynamic-key> -> C22
```

- Generic creation and unknown user-tool keys → C22.
- `pyzofilebrowser2.{path,expandedDirs,nameFilter,searchMatchCase,
  searchRegExp,wholeWords,searchSubDirs,searchExcludeBinary}` → C23.
- `pyzofilebrowser2.starredDirs[].{path,name,addToPythonpath}` → C24.
- `pyzoworkspace.{hideTypes,typeTranslation,searchMatchCase,searchRegExp,
  searchStartsWith}` → C25.
- `pyzosnippets.{searchName,searchDescription,searchCode,
  customSnippetsPath}` → C26.
- `pyzosourcestructure.{showTypes,level}` → C27.
- `pyzointeractivehelp.{smartNewlines,fontSize}` → C28.
- `pyzowebbrowser.{zoomFactor,bookMarks}` → C29.
- optional site/user `view.autoComplete_withTheme` → C10.

### Non-config stores and runtime entry points

- Config backup/reset and save gating → C01.
- Command history → P01; theme files → P02; user tools/snippets → P03;
  recovery → P04; diagnostic stores → P05; user files → P06.
- Application singleton/service state → L01; peer model/backend/session/context →
  L02-L08; documents/editor state → L09-L15; shells/kernels/debugger →
  L16-L24; tools/lifecycle/recovery/ingress/capabilities → L25-L30;
  execution variants/main → L31-L33; semantically inert widget mechanics → L34.

This mapping also covers writers that mutate the recursive config indirectly:
the advanced settings tree can edit two- and three-level entries, the shell
dialog reconstructs `shellConfigs2`, the key-map dialog edits arbitrary menu
paths, and dynamically loaded tools own arbitrary subtrees under their tool ID.

## Runtime evidence

The following focused command was run with bytecode disabled, an isolated uv
cache, offscreen Qt, and no user config/recovery path:

```text
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/pyzo-uv-cache \
QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo:. \
uv run --offline --python 3.12 --with PySide6-QtAds python -m unittest \
  spikes.peer_frames.test_workspace_session \
  spikes.peer_frames.test_session_recovery \
  spikes.peer_frames.test_lifecycle \
  spikes.peer_frames.test_application_lifecycle \
  spikes.peer_frames.test_status \
  spikes.peer_frames.test_commands
```

Result: `Ran 88 tests ... OK`.

This confirms the consequential transactional behavior used by C06, P04,
L02, L06-L07, and L26-L28: session capture/rollback, recovery atomicity and
quarantine, final-view close negotiation, live-shell termination negotiation,
application exit phases, zero-frame behavior, context-resolved command state,
and identical status projection. Other consequential rows were source-clear;
L34 records why purely local UI mechanics did not merit probes.

## Explicit unresolved findings for follow-up analysis

These are questions, not priorities or implementation tasks:

- Durable document identity independent of filesystem path, recovery ID, and
  live `FileItem` identity.
- Process-session representation for several concurrently loaded workspace
  identities and shared document/kernel resources.
- Conflict equivalence/history metadata and propagation among loaded versus
  unloaded workspaces.
- Default workspace routing for command-line/OS file opens and commands invoked
  with no current pane.
- Capability boundaries for simultaneous language/theme/debugger-selection
  modes and their unobtrusive UI indication.
- Tool-specific multiple-instance and resource-binding capability.
- Durable live shell/kernel identity and correction chrome for broken explicit
  run assignments.
- Storage for a workspace main document when it has no open pane.
- Breakpoint ownership when one shared document appears in several workspaces.

No source migration, state rewrite, priority assignment, or implementation
change was made during this audit.
