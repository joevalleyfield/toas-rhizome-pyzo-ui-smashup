# Stage 6 workspace contextual state and tools acceptance — 2026-10-06

Local Experiment 014 Stage 6 is **accepted** through
[task 032](../../tasks/open/032-workspace-contextual-state-and-tools.md), preserving
Astra's [September amendment](../local-workspace-scope-2026-09-06.md).
NEXT is existing Stage 7: external ingress, integrated compatibility, scaling,
final direct-global census and physical/platform acceptance. File Move/Fork UX,
live shell migration, zombies, portable synchronization and broad Rhizome/TOAS
integration remain separate/deferred.

## Exact implementation and runtime

- Root implementation: `b985fa0a920e522a4c4e1750b649843e5cdc0c3d`; parent Stage 5 completion
  `62334f42eec3f65b57c3b2e17ba52019c9b9ff90`.
- Pyzo implementation: `6544d31cd7d3562856a57c242f7fd9ea254910db`; parent Stage 5 implementation
  `0797bb43363cd1152fea5dd1d2046ac05a81de2c`.
- Binding unchanged: `b8d9c0a784db678227833ef8e545765a974ad4cb` (parent
  `764eb4a4`). Preexisting .gitignore, egg-info and uv.lock changes retained.
- Python **3.12.13**, PySide6/Qt **6.11.1**, IPython **9.17.1**, pinned
  `pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl`.
  [Runtime record](workspace-tools-2026-10-06/runtime.log).

## Accepted behavior and proof

[The final census](workspace-context-census-2026-10-06.md) resolves all **70**
Experiment 013 rows (C01–C30, P01–P06, L01–L34), with owner, storage/copy,
live-update behavior, compatibility treatment and executable evidence mapping.
The current defaults contain **116** leaves/empty containers; tests cover every
one, all explicit shared exceptions and late/unknown contextual fields.

| Boundary | Executable proof |
| --- | --- |
| Contextual state | A/B private config/history/shell-profile/project snapshots; a production service copy then nested mutations leaves the source, B and application archive unchanged. Bytes and unknown nested fields round-trip. Late extension defaults become private snapshots. |
| Ordinary checkpoints | Native preference/history mutations publish without further document edits; local live font zoom/status follow each owner. One-second context census plus one-second existing retention checkpoint, with event-loop/writer latency; observed 0.322s. |
| Ten built-ins | All ten distinct A/B widgets use owner-private module trees/facades. Expression viewers return actual A/B kernel markers; source trees use own editors. Captured namespace, help history/query/pause, browser navigation, expression flags, snippet search, shell profiles and project records survive reopen and fresh process. |
| Resource following | Tools select only their owner's foreground eligible editor/kernel. Reopened A has no eligible kernel, empty expression results and unavailable debugger capability while B keeps its actual live kernel. No old interpreter/results are revived. |
| Stale replies and callbacks | A genuine held query cannot write to A's retired/reloaded consumer; B continues returning B. A tool launcher captured in A reloads A while B is foreground. Source/editor completion/help/snippet/project lookups use invoking owner context. |
| Capabilities | Per-owner requests for language/theme/style/scale persist while getters/report show application effective values. Debugger capability reflects eligible interpreter advertisement, otherwise unavailable/shared. Menu initialization/normalization does not overwrite requests or invoke user mutation callbacks. |
| Extensions | Explicit workspace_api/context-constructor tool loads separate A/B instances. Undeclared tool refuses visibly/accessibly before its import side effect; unknown config survives. Metadata discovery cannot execute arbitrary expressions; malformed names fail locally. Declared Python remains responsible for respecting its context contract. |
| Diagnostics | Separate Logger consoles receive the explicitly shared application diagnostic stream. Owner cleanup removes its own subscription; no dead widget retained by stream callbacks. |
| Lifecycle/restore | Cancel and injected manifest publication failure retain exact widgets. Accepted A close checkpoints full contextual data before disposal; B survives. Reopen creates new owner bindings and restores state. Quit then a fresh process restores both owners and all built-ins with no restore warning. Private module prefixes release at successful retirement. |
| Affiliation | Several owners show their names in every dock title and dock/content accessibleName. Owner rename, focus, native same-owner movement/floating and fresh-process restore retain affiliation. Theme is an application capability; text/accessibility does not depend on theme/color. Semantic model titles stay separate from the visible suffix. |

## Acceptance repairs

Native acceptance caught menu synchronization invoking settings callbacks before
construction completed; checked-state synchronization now blocks QAction signals.
Language alias normalization preserves contextual requests. Fixed-owner local
adapters cover ordinary manager methods, starting shell controls and lazy Find
callbacks without creating editor hosts merely to bind menus.

Session capture addresses the specific runtime. Mixed editor/tool layout restore
maps retained editor IDs plus stable local tool IDs before checking complete
membership, pruning terminated shell IDs. Session archive callbacks rebind after
primary owner replacement. Failed-owner startup avoids legacy default tool
loading; construction uses the existing non-persisted empty bootstrap, preserving
opaque unavailable records for retry. Native movement refreshes the live floating
window census and checks wrapper validity before affiliation access. Committed
editor-host removal stops repeating find timers; worker cleanup uses keyword
arguments supported by file-browser workers. Cancel/failure performs none of
this retirement. All these states and assertions are recorded in task 032.

## Verification and reproduction

**501 coordinated tests, 56 subtests, and all 16 live controls pass.** Coordinated
skips are the 16 opt-in live cases and the stock four-tab-side expectation
superseded by the pinned fork. Two existing Qt high-DPI deprecation warnings
remain. **29** touched Python files compile; Ruff F and whitespace checks pass.
Full peer smoke **10.971s**; maintained-fork legacy **7.649s**. Final all-live suite
**57.79s**. Stage 6 integrated tool replay **3.477s**, fresh-process restore
**0.861s**.

Logs: [coordinated](workspace-tools-2026-10-06/coordinated.log),
[all live](workspace-tools-2026-10-06/live.log),
[peer](workspace-tools-2026-10-06/peer.log),
[legacy](workspace-tools-2026-10-06/legacy.log),
[source checks](workspace-tools-2026-10-06/source-checks.log),
[smoke durations](workspace-tools-2026-10-06/smoke.log).

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo/pyzo:deps/pyzo:. \
  ./.codex-local/bin/uvt run --offline --python 3.12 \
  --with pytest --with PySide6 \
  --with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl \
  --with ipython python -m pytest spikes/peer_frames deps/pyzo/tests -q -rs

RUN_LOCAL_RETENTION_ACCEPTANCE=1 RUN_LOCAL_EXECUTION_ACCEPTANCE=1 PYTHONPATH=. \
  ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest python -m pytest \
  spikes/peer_frames/test_local_retention_acceptance.py \
  spikes/peer_frames/test_local_execution_acceptance.py -q -s
```

Probes own isolated appdata/workspace/recovery directories, stub command-server
ingress and real kernels. Each phase has a 12-second deadline; the external
harness owns process-group cleanup and a 35-second tool/smoke deadline. Temporary
probe state is removed; no user interpreter or unrelated process is targeted.
Root/Pyzo implementations and completion evidence are separately committed; no push.

This is macOS offscreen acceptance. Physical window-manager/accessibility/drag,
Windows/Linux, pristine upstream vanilla Pyzo, scaling and the final external
open/global-context boundary replay remain **Stage 7**. The legacy control is the
maintained fork's non-peer host. Application theme/language/style/scale and
keyboard-map capability fallbacks are explicit; richer tool/resource bindings
remain deferred. No Stage 7 obligation is marked accepted here.
