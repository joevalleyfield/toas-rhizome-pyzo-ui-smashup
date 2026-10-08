# Stage 7 local scale and final census acceptance — 2026-10-08

[036](../../tasks/open/036-stage-seven-scale-and-final-census.md) is accepted for
representative local scaling and the final state/config/direct-context census.
The real application restores 1/4/8 loaded workspaces, shared unsaved resources,
local settings/history/Main/tools/affiliation and an opaque unavailable record.
The full local suite and all 21 live controls pass. Physical macOS,
Windows/Linux, unmodified vanilla and migrated-user-state integration remain
open in [014 Stage 7](../../tasks/open/014-concurrent-workspace-implementation.md#7-external-ingress-compatibility-scale-and-integrated-acceptance).

## Exact implementation and runtime

Root `0b2a8c82175481785799d8d69eaf56e5ee316389`, parent
`3957b98498205cff8c0dbc264d85df1f77af9fd2`; Pyzo
`d570a7daeda64a7acd95d995fd2a1e82e84b72ca`, parent
`db2475a7257115d3b50957c6f8698416ec53c2fc`. Both implementations precede the
separate acceptance commit. Nothing pushed.

Binding working-copy revision `b8d9c0a784db678227833ef8e545765a974ad4cb`, parent
`764eb4a487abccb162dcbee1a8f0383916561e0e`; embedded native QtADS
`243aa54b4f131212ce02ce78b347a13cb3713736`; reference checkout
`59d4730119466e02195f1a221a54386a9410b16f`. These are unchanged. Binding's
pre-existing .gitignore, egg-info and uv.lock edits are preserved. Pinned local
wheel `pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl` unchanged.
Python 3.12.13, PySide6/Qt 6.11.1, IPython 9.17.1; macOS 27.0.1 arm64 host;
Qt offscreen. Date is the client date 2026-10-08.

## Demonstrated repairs

- Replace All snapshots the invoking workspace's views. Editing a shared
  resource still propagates to its other views; foreign-only resources stay
  unchanged. Late help completion and help availability use the source control.
- Cursor/group/save/reload notifications use the invoking editor/group. Failed
  debugger source navigation focuses only its captured eligible session shell.
  PDF export captures its editor and parents the preview through that context.
- File drops, direct groups/dialogs/directory loads and application-manager loads
  enter the fixed local facade before native construction or global deduplication.
  Known canonical resources reuse retained identities/text/undo, even if the
  file is missing; modal recovery selection rechecks owner epoch/eligibility.
  The native reproduction before repair duplicated a shared identity and lost
  unsaved text. The full smoke then detected a preliminary empty host; manager
  delegation now happens before creating that host.
- Command-server new-file and external-shell requests resolve the application
  at GUI dispatch and use the same eligible MRU/empty/exit policy as file ingress.
  Exact shell configuration passes through. Legacy paths keep ordinary behavior.
- Persistence refreshes the runtime's live native frame registry before geometry
  reads and returns no frames for disposed runtimes. Four-owner scaling exposed
  an expired floating wrapper after deferred deletion.
- Restore maps tools by semantic tool ID when primary/secondary prefixes change.
  New snapshots carry `tool_panes`; older records accept the two exact historical
  owner/tool ID forms. An explicit saved tool set reconciles bootstrap defaults
  before layout restore; absent metadata retains legacy defaults. This removed
  lost tool placement and an unregistered file-browser restore warning.

The [task state maps](../../tasks/open/036-stage-seven-scale-and-final-census.md)
record each refinement before its repair. No routing/provenance guard was relaxed
and no product path saves a user file as a background retention operation.

## Representative scale results

[Final samples](stage-seven-scale-census-2026-10-08/scale-metrics.json) are extracted
from the [accepted live replay](stage-seven-scale-census-2026-10-08/live-recheck.log).
The [repeatable probe](../../spikes/peer_frames/qt_workspace_scale_probe.py) uses
isolated temporary appdata/recovery, a non-listening command server and bounded
owned process groups. Each owner has local text, four built-in tools, settings,
history and Main, plus one shared document; the seed owner also has its default
file browser and a closed retained view. Disk conflict/missing-file fixtures and
one injected unavailable runtime exercise isolation without changing real files.

| Loaded owners | First settled restore seconds | GUI RSS first → final MiB | Panes / frames | Timers | Private modules | Callbacks / receivers | Widgets first → final |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.3714 | 147.5 → 147.5 | 8 / 6 | 11 | 11 | 1 / 1 | 529 → 529 |
| 4 | 0.7006 | 191.0 → 192.6 | 26 / 25 | 35 | 32 | 4 / 4 | 1692 → 1678 |
| 8 | 0.8452 | 246.9 → 249.8 | 51 / 50 | 70 | 52 | 8 / 8 | 3225 → 3219 |

N=1 is a baseline; N=4/8 each close/reopen one owner three times. Every measured
native/service/document/live-view/retained-view/module/timer/receiver count stays
exactly constant across their four samples. Each live facade receives one
callback; a retired facade receives zero; surviving native editors keep their
view identity. Widgets plateau for the final two samples after reconstruction
warmup. Every tool/dock is valid, registered and placed, with exact local loaded
sets and owner accessibility labels. No QMainWindow or root-manager dock area
appears in peer mode. Opaque unavailable data/request survives restart and
checkpoint; the failed owner is never loaded.

Times above start after Python/Qt imports, before MainWindow construction, and
end at the first settled assertion sample. They are not end-user launch times.
Whole owned seed-process times were 1.366/1.401/1.825s; complete restore-process
runs, including three cycles for N=4/8, were 0.731/1.621/1.873s. RSS is the GUI
process's `ps` KiB value converted to MiB, excluding kernel children and caches.
Short local runs show bounded object/callback counts; they do not establish
long-soak RSS limits or physical/window-manager/cross-platform performance.

## Final census and validation

The [final C01–C30/P01–P06/L01–L34 tables](workspace-context-census-2026-10-08.md)
cover all 70 rows and their storage/copy/live/fallback contract. The
[review manifest](../../spikes/peer_frames/workspace_context_review.json) records
718 syntactic references in 37 files with line/function/expression/class/proof/
AST scope digest. Classes: application 173, bootstrap 167, test/example 133,
fixed owner 132, legacy 78, receipt guarded 35; zero unclassified.
The [inventory check](stage-seven-scale-census-2026-10-08/context-audit.log) and
[guard test](../../spikes/peer_frames/test_workspace_context_audit.py) reject
unreviewed changes. This is source/effects evidence, not arbitrary-extension
sandboxing or a whole-program alias proof.

- [Final complete suite](stage-seven-scale-census-2026-10-08/units-accepted.log):
  696 passed, 348 subtests, 22 skipped (21 opt-in live controls plus the existing
  stock tab-side capability case), two existing Qt deprecations.
- [Final live replay](stage-seven-scale-census-2026-10-08/live-recheck.log):
  21 passed in 102.00s. Includes peer/legacy startup, Run/debug/postmortem/affinity,
  timeout/exception exit 1, tools/restart, ingress, native restore, recovery,
  retention/closure/publication failure, provenance and scale. No positive
  completion follows a traceback or application restore warning. The existing
  shiboken deleted-shell warning also appears in the earlier 035 replay; this
  slice makes no new platform/teardown-warning acceptance claim.
- [Static checks](stage-seven-scale-census-2026-10-08/source-checks.log): Ruff F
  passes; all 19 changed Python sources compile without trailing whitespace.

Exploratory logs remain beside the accepted logs. `consumers*.log` and
`focused-final.log` include test-setup failures from importing native menu code
without a QApplication/config; the fixture now establishes those first. The
first full unit replay caught incomplete editor-map rejection ordering, then the
inventory generated with system Python 3.9 differed from accepted Python 3.12
ASTs; the final manifest/check is generated and verified with Python 3.12.
`scale*.log` record the actual geometry/tool failures and initial probe refinements:
retained resource availability differs from the physical Main-path predicate;
restore insertion order may prioritize active owner; widget warmup requires a
measured plateau rather than an arbitrary +5 bound. The final assertions preserve
resource identity, owner data, disk predicates, tool placement and active owner.
`live-final.log` captures the empty-host smoke regression fixed before acceptance.

Reproduce units with `QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo/pyzo:deps/pyzo:.`
and `.codex-local/bin/uvt run --offline --python 3.12 --with pytest --with PySide6
--with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl
--with ipython python -m pytest spikes/peer_frames deps/pyzo/tests -q -rs`.
Reproduce live controls with `RUN_LOCAL_RETENTION_ACCEPTANCE=1
RUN_LOCAL_EXECUTION_ACCEPTANCE=1 PYTHONFAULTHANDLER=1 PYTHONPATH=.` and
`.codex-local/bin/uvt run --offline --python 3.12 --with pytest python -m pytest
spikes/peer_frames/test_local_retention_acceptance.py
spikes/peer_frames/test_local_execution_acceptance.py -q -s`.
Use `-k representative_workspace_scale` for the six scale processes only.
