# Native request/result provenance — accepted 2026-10-05

[Task 029](../../tasks/open/029-native-request-result-provenance.md) closes the
remaining native provenance gate in [014 Stage 4](../../tasks/open/014-concurrent-workspace-implementation.md#4-workspace-execution-routing-and-shell-transfer-refusal).
Together with accepted 026–028, Stage 4 is accepted for the local offscreen
workflow under the normative [September amendment](../local-workspace-scope-2026-09-06.md).
The next existing gate is Stage 5 debugger/session ownership, breakpoint overlays,
postmortem attribution and conservative workspace closure.

Root implementation: `9072a23e98ff7c878553edd12aaa68c4020c93f4`.
Pyzo implementation: `e79cf5e442f2f9156414d0c7ca1540b0a58e1a7c`.
Starting revisions: root `bf6a8275e9836a716f54adb31ce87a310b82399f`,
Pyzo `43a1376ecf3a4447ce93ef78cee5e77bf2e771d5`.
Binding remains at the pre-existing `b8d9c0a784db678227833ef8e545765a974ad4cb`;
its packaging changes were untouched. The pinned wheel remains
`pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl`.
Coordinated/native verification uses Python 3.12.13 and PySide6/Qt 6.11.1.

## Result

Native completion/signature and editor-originated help now resolve through the
invoking view's workspace assignment. A receipt carries operation, command,
workspace/process owner, view/shell identity and epoch, and model interpreter
generation. Native transport has a distinct epoch that changes on every restart
or context replacement. The kernel verifies that transport epoch before evaluating
an introspection expression or executing a tagged command, then echoes the exact
receipt. Callback metadata is attached before callback registration.

The shared native reply gate checks exact echo, current route/generation, source
view lifetime, document revision, cursor context, consumer lifetime and latest
query before invoking the native handler. Canceled/failed futures preserve the
existing native error handling; malformed or stale envelopes produce no consumer
writes. Completion caches carry the receipt. A current reply for a background
view may fill that view's cache but cannot show a popup/calltip in the active
foreign view. Auto-import uses the captured editor and shell, with dispatch
validation; shell completion cannot import from a foreign global editor.

Workspace and expression tools and interactive help use the gate. Tool proxies
have their tree as QObject parent; close/reload explicitly retires a tool and its
children before deferred Qt deletion. Tool print/evaluate/delete/import/history
and directory commands also carry direct-shell operation receipts. Their current
selection policy remains the compatibility behavior pending Stage 6 isolation.
Interactive help retains the actual source of each completion/calltip extension.

Run code and line commands, native debugger controls and frame commands use an
OBJECT operation channel alongside the unchanged ordinary native stdin channel.
Accepted/completed receipts, debugger status and kernel UI actions are tagged.
Old or unknown receipts cannot update status/actions; an open/clear action cannot
mutate a foreign active workspace. Shell text streams retain their native behavior.
Ordinary direct shell execution is also tagged; peer refusal cannot fall through
to the untagged legacy channel. Dispatch restores its temporary operation context
on success or exception, and native receipt history is bounded to 128 entries.

Regular Python scripts retain native autosave/restart. Startup echoes the original
operation, exact successor transport and accepted successor model generation.
A later unrelated recycle cannot masquerade as that startup. IPython keeps its
native `%cd`/`%run -i` branch and generation, now using tagged command delivery.
Legacy mode retains raw native request results and original execution policies.

The live proof exposed two additional states. Debugger startup reset occurs before
startup metadata is available; tagging must permit that initial reset. A restart
can finish between bridge synchronizations without any check seeing the transient
unavailable state. The bridge now detects a changed native transport epoch and
advances its model generation anyway. Retired startup channels and startup epochs
are rejected before native widget access.

## Assertions and live proof

The 31 focused native assertions cover immediate completion, exact wire fields,
reverse-order queries, malformed echoes, failures/cancellation, implicit/explicit/
direct targets, foreign focus, assignment/foreground drift, loss/reconnect/context
replacement, source close/reopen/move/revision/cursor changes, consumer retirement,
cache invalidation, nested dispatch cleanup and exact script successor linkage.
They extend the existing routing, Run/save and ownership assertions.

The [new test-owned Qt probe](../../spikes/peer_frames/qt_native_provenance_probe.py)
uses two actual workspace-owned kernels. With B globally active, A's completion
returns list methods, A's signature names `a_only`, and editor help returns A's
documentation. B's workspace/expression tools query B's dictionary and expression
value 1. Both Run receipts round-trip through the real kernel. Genuine tool
replies released in reverse order keep the latest namespace query. Genuine
completion replies held across source edit, restart and native view closure make
zero cache/display writes. Background results make zero popup/calltip calls.
The new kernel rejects an old-epoch introspection request and queued old-epoch
execution; old Run results are rejected. Fresh direct/debugger command receipts
complete in the successor. Source baseline bytes remain unchanged.

The existing [Run variants probe](../../spikes/peer_frames/qt_workspace_run_variants_probe.py)
now additionally verifies actual File/Main script startup receipt echoes and
successor-generation linkage. Earlier Selection, assignments, retained Main,
Python/IPython policies and all retention controls remain green. Full application
probes preserve ordinary Run, live debugging, postmortem re-entry/frame inspection,
multi-kernel affinity and peer/legacy host topology.

Initial live attempts exposed the early debugger-reset initialization failure;
then the new probe exposed the unobserved restart transition. Both were repaired
within this gate. Harness expression tuple indexing/fixture target setup and
helper import-name collisions were corrected. Failed child runs were bounded and
cleaned by the owned harness; no failure was treated as acceptance.

## Validation and cleanup

| Check | Final result |
| --- | --- |
| Coordinated suite | **451 passed, 14 skipped, 45 subtests**, 2.36s |
| Live execution and retention | **13 passed**, 44.31s |
| New native provenance probe | **3.625s** |
| Real script/Run variants | **5.748s** |
| Full peer application | **10.941s** |
| Full legacy application | **7.550s** |
| Changed Python files | **24** compile; Ruff F and added-line whitespace pass |

Thirteen default skips are the separately run live controls; the remaining
stock four-tab-edge skip and two existing Qt high-DPI deprecation warnings remain.
Logs: [coordinated](native-provenance-2026-10-05/coordinated.log),
[live](native-provenance-2026-10-05/live.log),
[peer](native-provenance-2026-10-05/peer.log),
[legacy](native-provenance-2026-10-05/legacy.log).

Reproduce from the coordinating root:

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo/pyzo:deps/pyzo:. \
  ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest --with PySide6 \
  --with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl \
  --with ipython python -m pytest spikes/peer_frames deps/pyzo/tests -q -rs
RUN_LOCAL_RETENTION_ACCEPTANCE=1 RUN_LOCAL_EXECUTION_ACCEPTANCE=1 PYTHONPATH=. \
  ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest python -m pytest \
  spikes/peer_frames/test_local_retention_acceptance.py \
  spikes/peer_frames/test_local_execution_acceptance.py -q -s
```

Full application controls use `run_owned_probe` with
`qt_application_smoke_probe.py`, phases `peer` and `legacy`, fresh temporary
application data and 35-second external deadlines. Probes stub the user command
server and terminate only their own kernels/process groups. Logs are copied into
this evidence directory; temporary harness scripts/log copies are removed after
completion. Implementation commits precede roadmap advancement. Root/Pyzo are
clean after the completion commit; nothing was pushed.

## Acceptance limits

Stage 4 covers local execution routing and native provenance, with the existing
retention/persistence-before-teardown boundary. Stage 5 still owns durable
breakpoint overlays, debugger/session ownership, postmortem attribution and
terminate-or-cancel closure warnings/negotiation. Tools, config and history
isolation remain Stage 6. Physical macOS interaction and Windows/Linux native
portability are not accepted by offscreen evidence. Live shell migration, zombies,
portable synchronization and broad TOAS/Rhizome integration remain deferred.
File Move/Fork UX remains separate. No binding or TOAS/Rhizome changes were made.
