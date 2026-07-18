# Experiment 005 integrated feasibility decision

## Decision

Pyzo is a viable foundation for the peer-frame application model with bounded
maintained forks and explicit completion gates. It is not viable unchanged:
the accepted implementation depends on a 25-commit Pyzo integration series and
the product requirement for independent four-side tab rails depends on matched
five-commit QtADS source and PySide6 binding series.

The demonstrated architecture keeps documents, interpreters, debugger state,
commands, lifecycle, and peer topology outside frame ownership. The private
QtADS manager and temporary hidden Pyzo `QMainWindow` are implementation
scaffolding, not user-visible privileged frames. The remaining work is bounded
and named; no observed result justifies replacing QtADS or abandoning Pyzo.

## Final replay

The final replay ran on macOS 26.5.2 with CPython 3.12.13, Pyzo 4.21.0, the
published `PySide6-QtAds` runtime wheel, and the offscreen Qt platform plugin.

| Surface | Result |
| --- | --- |
| Peer contract, lifecycle, session recovery, commands, status, and stock QtADS adapter | 147 tests passed; 3 expected skips for four-side behavior unavailable in the published wheel |
| Legacy Pyzo control | Passed editor docks, debugger document routing, file-browser/tool container, native ADS feedback, independent shells, and clean shutdown |
| Peer Pyzo integration | Passed independent editor, shell, and file-browser/tool panes; native overlay ownership; pane movement; clean/dirty lifecycle; zero-frame recreation; and shutdown |
| Run and live debug | Passed with real kernels after pane and frame rearrangement |
| Post-mortem workflow | Passed exception capture, post-mortem re-entry, captured outer-frame selection, source navigation, and live execution in the selected frame |
| Multi-kernel execution affinity | Passed explicit Run/Debug target selection independently of focused shell and preserved cwd/kernel context across layout changes |

The deterministic contract/backend command was:

```sh
UV_CACHE_DIR=/tmp/pyzo-uv-cache PYTHONPATH=. QT_QPA_PLATFORM=offscreen \
  uv run --offline --python 3.12 --with PySide6-QtAds \
  python -m unittest discover -s spikes/peer_frames -p 'test_*.py'
```

The real peer replay ran from `deps/pyzo`:

```sh
UV_CACHE_DIR=/tmp/pyzo-uv-cache PYTHONPATH=../..:. \
  QT_QPA_PLATFORM=offscreen PYZO_PEER_FRAMES=1 \
  uv run --offline --python 3.12 --with PySide6-QtAds --with ipython \
  python pyzolauncher.py --test
```

The legacy control used the same source launcher without `PYZO_PEER_FRAMES=1`
and with `PYTHONPATH=.`. The first sandboxed legacy attempt could not bind
kernel sockets or write Pyzo preferences and was discarded; the unrestricted
rerun passed.

## Accepted revision map

| Layer | Replay revision | Disposition |
| --- | --- | --- |
| Coordinating repository | `02718acfcc75fbb19455a68444c223012ca527cb` | Contract, stock adapter, lifecycle, commands/status, tests, and fork evidence |
| Pyzo | `84dc182d945deed8a146b111a3b41785796f2db7` | Accepted 25-commit feasibility fork over `origin/main` |
| PySide6-QtAds | `764eb4a487abccb162dcbee1a8f0383916561e0e` | Accepted five-commit binding fork |
| Embedded QtADS | `244157db5bdffdf9d250e58a6edf8ee6acfd3a61` | Accepted five-commit four-side/accessibility source fork |
| Stock QtADS control | `812ce784ce9ee2eba89d6a91e46cc4bcc86e9fd0` | Unmodified comparison checkout |

The generated `deps/pyside6-qtads/src/PySide6_QtAds.egg-info/` directory remains
an untracked local build artifact and is not part of the accepted revision.

## Requirement disposition

The complete `REQUIREMENTS.md` acceptance workflow is demonstrated on macOS:
multiple source documents occupy split and floating peer groups; groups move
and re-dock without changing document or interpreter identity; code runs and
live-debug state survives; an unhandled exception enters post-mortem mode; a
captured frame can be selected and navigated; live interpreter code executes
against that frame; and editor, shell, file-browser, lifecycle, layout, menu,
status, and Run/Debug workflows remain usable afterward.

Four-side native rails are accepted through the matched source/binding fork
evidence from Experiment 011 rather than the published-wheel replay. The three
suite skips make that runtime distinction explicit.

## Conditions and follow-up candidates

Before the architecture is called complete:

1. remove the hidden Pyzo `QMainWindow` by replacing its remaining menu,
   persistence, dialog-parenting, tool-construction, startup, and metadata
   service assumptions;
2. replay the scheduled native Windows and Linux matrix before production
   adoption or toas/rhizome integration;
3. decide whether group-tab keyboard traversal is application command policy
   or requires a richer QtADS focus/accessibility implementation; and
4. keep the Pyzo, binding, and embedded QtADS pins matched while extracting and
   upstreaming independently useful service, correctness, and accessibility
   slices.

After those gates, the bounded candidates are a toas transcript-editor pane
and broader rhizome window integration through the application pane/command/
lifecycle contracts. This experiment does not begin either integration.

## Portability assessment

The architecture remains practical for Windows and Linux: platform-neutral
services own state, macOS window-order and guide workarounds are isolated, and
the legacy workspace remains a control. Cross-platform parity is not yet
claimed. Native docking targets, menus and shortcuts, dialog modality, focus,
taskbar/application lifetime, lifecycle, debugger routing, four-side rails at
100/125/200 percent scaling, and platform accessibility inspection remain an
explicit release gate documented by Experiment 010.
