# Experiment 010 fork-boundary evidence

## Decision

The demonstrated stack is viable with bounded maintained forks. Replacing the
docking backend is not justified by the observed evidence.

Stock QtADS already supplies peer-frame topology, native docking feedback,
layout capture/restore, cross-frame moves, and a private hidden coordinator.
The required QtADS fork is confined to the non-stock product requirement for
independent four-side tab rails and the interaction/accessibility behavior of
those rails. The Python binding fork only exposes and verifies that source API.
The largest maintained surface is Pyzo, where application services must be
separated from the legacy visible-`QMainWindow` model.

## Accepted revisions

| Layer | Upstream baseline | Accepted revision | Divergence |
| --- | --- | --- | --- |
| Coordinating repository | local baseline | `d295a7286e1d94ab116e78c0d2c2e18bb0bca9ac` | Contract, stock adapter, projectors, tests, and evidence |
| Pyzo | `26c2c32778dddf8fca3c1a44112941b22f075264` (`origin/main`) | `84dc182d945deed8a146b111a3b41785796f2db7` | 25 commits |
| PySide6-QtAds | `29cef87f149b9779a10a200f56c85a713def71ef` (`origin/main`) | `764eb4a487abccb162dcbee1a8f0383916561e0e` | 5 commits |
| Embedded QtADS | `812ce784ce9ee2eba89d6a91e46cc4bcc86e9fd0` (`origin/master`) | `244157db5bdffdf9d250e58a6edf8ee6acfd3a61` | 5 commits |

The standalone QtADS checkout remains at unmodified upstream `812ce78` and is
the stock control. The embedded source is detached at the accepted fork tip.
The binding checkout currently has generated `src/PySide6_QtAds.egg-info/`
untracked; it is a local build artifact, not part of the accepted revision.

## Requirement-to-owner matrix

| Requirement or deviation | Narrowest owner | Fork status | Smallest invariant/surface |
| --- | --- | --- | --- |
| Stable frame, group, pane, placement, active-context, and lifecycle semantics | Application contract/adapter | No dependency fork | `spikes/peer_frames` model and projector interfaces remain backend-neutral |
| All visible frames behave as peers while QtADS retains one privileged manager/root | Stock QtADS plus adapter | No QtADS fork | Parentless hidden `CDockManager`; visible `CFloatingDockContainer` peers; adapter never exposes the root |
| Native split, tab, float, cross-frame drag, re-dock, overlays, and layout reverse capture | Stock QtADS plus adapter | No QtADS fork | `QtAdsPeerFrameBackend` projection and settled-layout adoption |
| Application-owned commands, per-frame/shared menus, status, and focus context | Application projectors plus Pyzo integration | Pyzo fork | Stable command/status services projected into peer chrome; focus maps to pane identity |
| Independent editor and shell panes with stable document/interpreter identity | Pyzo | Pyzo fork | `EditorGroupManager`, `ShellGroupManager`, one resource host per application pane |
| Run/Debug target does not change with pane focus and remains textually visible | Pyzo | Pyzo fork | Explicit execution-shell state, Run/Shell menu labels, explicit shell target command |
| Clean/dirty document, live shell, frame, application, retained-session, and backend-destruction lifecycle | Application lifecycle plus Pyzo callbacks | Pyzo fork; no QtADS fork | Prepare/confirm/commit transactions; native close bridge; live hide/delete rejection |
| Zero-frame survival and activation recreation on macOS | Application policy plus Pyzo platform integration | Pyzo fork | `ApplicationFrameLifecycle`; no dependence on Qt implicit last-window quit |
| Post-mortem re-entry, captured-frame navigation/execution, and debugger state across moves | Existing Pyzo kernel/debugger plus Pyzo peer routing | Pyzo fork; kernel protocol remains stock | Preserve shell context, stack state, source identity, breakpoints, and explicit execution target |
| Per-group top/bottom/left/right tab placement and persistence | QtADS source | Required QtADS fork | `CDockAreaWidget::eTabPosition`, per-area state, XML persistence, body/rail layout |
| Vertical tab hit testing, reorder, undock, overflow, and group drag | QtADS source | Required QtADS fork | Orientation-aware `CDockAreaTabBar`/`CDockWidgetTab`; rail event forwarding |
| Bottom rail list-all-tabs and one-pane non-top rails | QtADS source | Required QtADS fork | Move the single native menu button between owners; retain non-top rail for one pane |
| Python access to per-area tab positions | PySide6-QtAds | Required binding fork | Shiboken enum, getter, setter, and signal exposure |
| Accessible names for tabs, close controls, and list-all-tabs | QtADS source | Candidate upstream fix | Stable accessible names derived from dock titles and control roles |
| macOS docking-guide visibility workaround and window-order tracking | Pyzo/application integration | Platform-specific Pyzo fork | Presentation-only guide/window-order shim; native QtADS docking decisions remain authoritative |
| Hidden `QMainWindow` removal | Pyzo | Required final cleanup, not a QtADS blocker | Replace hidden menu behavior, layout blobs, dialog parenting, tool construction, startup/splash, and metadata projection with application services |

## Candidate fork surfaces and upstreamability

### Pyzo

The 25-commit Pyzo branch is a feasibility branch, not yet the ideal upstream
series. Its durable seams are independently upstreamable in smaller groups:

- editor/shell manager facades and stable resource hosts;
- application command, status, and explicit execution-affinity services;
- lifecycle transactions and native close routing;
- peer workspace projection and zero-frame policy;
- real-kernel smoke coverage for Run/Debug and post-mortem behavior.

The QtADS-specific peer bootstrap, macOS guide/window-order shims, and temporary
hidden-main compatibility calls should remain isolated integration modules.
Hidden-main removal should not be attempted as a single mechanical deletion:
the dependency inventory names command behavior, persistence, dialog modality,
tool construction, startup, and metadata as separate migration seams.

### QtADS

The maintained QtADS source series is exactly:

1. `0edfe64` — per-area top/bottom positions and persistence;
2. `b5942e5` — left/right rail layout and orientation behavior;
3. `1bff425` — non-top whole-group drag surfaces;
4. `c149a7f` — bottom rail tabs menu and one-pane rail behavior;
5. `244157d` — accessible names for tab controls.

The accessibility naming and some orientation-neutral correctness changes are
strong upstream candidates. Four-side rails are a larger product feature and
may remain a maintained fork unless upstream accepts the API and UX. None of
these changes grants architectural privilege to a visible frame or alters the
application lifecycle model.

### PySide6-QtAds

The binding series `c77dd6e`, `16e495e`, `50d8c74`, `f9fe64f`, and `764eb4a`
tracks the five QtADS slices. Only the enum/property/signal exposure is runtime
API; the later commits primarily provide binding-level interaction,
accessibility, and scale tests. This fork should follow the embedded QtADS pin
exactly and can disappear if the source API and generated bindings are
released upstream.

## Hidden-main decision

Removing the hidden `QMainWindow` is required before calling the architecture
finished, but it is optional for continued feasibility work and does not
require a QtADS fork. The host is currently private migration scaffolding; it
does not represent a user-visible privileged frame. Removal is blocked only by
named Pyzo service assumptions: behavior-bearing menu objects, legacy
`saveState()`/named-view persistence, hidden-parent dialogs, tool factories,
startup/splash flow, and title/busy/debug metadata projection.

## Portability obligations

macOS native and offscreen evidence is acceptance for this spike, not portable
proof. Windows and Linux native replay is explicitly scheduled as a release
gate before any toas/rhizome integration or production adoption of this stack.
Each platform must replay:

- stock and fork docking, overlapping-frame targets, native overlays, whole-
  group and individual-tab drags, frame close, and empty-wrapper cleanup;
- shared/per-frame menu ownership, shortcuts, explicit execution-target UI,
  focus restoration, dialog modality, taskbar/application lifetime, and zero-
  frame policy;
- lifecycle matrices for dirty documents, live/debugging shells, Quit,
  Restart, retained sessions, forced hide, and deletion;
- Run, live debug, post-mortem re-entry, captured-frame execution, multi-kernel
  targeting, cwd preservation, and the layout-transition matrix;
- four-side rails at native 100%, 125%, and 200% scaling with each platform
  style, including minimum-size content, elision, hit testing, and controls;
- platform accessibility inspection for tab, close-tab, and list-all-tabs
  names, roles, traversal, and activation.

The macOS-first implementation has not removed Windows or Linux support paths.
The contract, adapter, lifecycle, command, debugger, and execution-target
services are platform-neutral; macOS window-order and docking-guide behavior is
isolated behind platform checks; and the legacy Pyzo workspace remains a
control path. Native Windows/Linux acceptance is still pending, so this is a
bounded portability obligation rather than evidence of cross-platform parity.

Direct keyboard traversal of QtADS group tabs remains an explicit open
question. The current custom controls preserve content focus and expose stable
names but use `Qt::NoFocus`. The product must choose application commands and
shortcuts or a richer QtADS accessible-tab/focus implementation; macOS evidence
does not decide that cross-platform policy.

## Fork versus replacement

A replacement backend would still need the application contract, resource
lifecycle, command/status projection, execution affinity, session model, and
platform policies. It would discard already-passing native docking behavior to
avoid a five-commit QtADS feature series. That trade is presently unfavorable.

Reconsider replacement only if native Windows/Linux validation exposes an
unbounded structural failure in peer-window targeting, accessibility,
high-DPI/minimum-size behavior, or lifecycle interception that cannot be kept
behind the adapter. Until then, the recommended posture is:

1. keep the application contract and lifecycle backend-neutral;
2. maintain the bounded Pyzo integration fork while extracting services;
3. maintain the five-commit QtADS and binding series for four-side rails;
4. upstream isolated correctness/accessibility pieces where practical; and
5. treat platform validation and hidden-main removal as explicit gates, not as
   reasons to expose the private QtADS root or replace the backend prematurely.

## Open questions

- Will upstream QtADS accept per-area four-side tab positions as a supported
  feature, or only the accessibility/correctness subsets?
- Should keyboard tab traversal be application-command policy or a QtADS focus
  and accessibility feature?
- What peer owns global dialog modality on Windows and Linux?
- What schema replaces Pyzo named views and hidden-main `saveState()` when
  multiple workspaces are supported?
- Do native Windows/Linux results preserve the bounded-fork recommendation, or
  reveal a backend-level blocker requiring reassessment?
