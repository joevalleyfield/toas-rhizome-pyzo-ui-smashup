# Stage 7 Linux cancelled request follow-up

The earlier three-platform acceptance run recorded in
`tasks/open/042-stage7-automated-acceptance.md` passed on all three platforms
([run 38327905266](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38327905266)).
A later companion push run,
[38329136851](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38329136851), intermittently failed Linux in
`qt_workspace_tools_probe.py` while releasing the held expression-viewer
request. The traceback reports Yoton's `CancelledError` from `Future.exception()`;
the separate [pull-request check run 38329141514](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38329141514) passed all three platform jobs.
The cancellation must remain visible as a failure if the request does not
complete successfully.

The complete GitHub Actions failure log and artifact were retrieved. The failing
testcase took 5.355 seconds total, so the earlier 10-second-timeout hypothesis
was incorrect. Pinned Pyzo 803afaf3 creates its shell `ReqChannel` with a
0.5-second default future timeout. Yoton cancels a request if it remains in the
waiting state at that timeout; it also cancels if sending the pre-request fails
with `IOError`.

Inspection of the pinned source found no explicit cancellation of expression
viewer requests: `ExpressionProxy.evaluateExpressions` submits requests, its
completion callback accepts cancellation as “no living kernel,” and
`nativeRequests.request` rejects stale callbacks without cancelling the Future.
The prior acceptance hold intercepted every A-shell request until all held
Futures completed, even though its intent is to delay one response from the
explicit `manualRefresh()`. The hold now exists only during that synchronous
refresh call, asserts that it intercepted exactly one `evalMultiple` request,
then restores `ReqChannel`'s dynamic proxy correctly. This scoping correction
alone did not resolve the Linux failure: the follow-up PR run below failed on the
target `evalMultiple` itself. Its diagnostic recorded status 2 (cancelled),
configured auto-cancel timeout 0.5 seconds, and 0.688 seconds held. That timing
is consistent with the Yoton timeout, but the log does not prove whether timeout
or send `IOError` caused the cancellation.

A local instrumented replay found about ten older, incomplete A-shell
`evalMultiple` Futures queued immediately before the old in-tick refresh. The
probe now moves the target refresh into the existing held phase and waits for
the A request queue to have no incomplete Futures for three 100ms ticks before
issuing it. Those three idle ticks allow already-queued automatic-refresh
callbacks to settle. The existing 12-second phase guard includes the drain and
the target response; it is not reset when the queue empties. The 35-second
external deadline, original success assertions, and Yoton's 0.5-second
auto-cancel timeout are unchanged. Target cancellation still fails, and
diagnostic output includes method, elapsed time, Yoton status, cancellation
state, and configured timeout.

Validation: pinned Pyzo was checked out read-only at 803afaf3 under
`/private/tmp`. Three focused fake-request tests pass: the old interval-wide
hook captures a later unrelated canceled request, the scoped hook isolates that
request while keeping target cancellation fatal, and queue draining waits only
for incomplete requests. The exact-pinned live `workspace-tools` seed and
fresh-process `tools-restore` pair pass locally on macOS in 4.681s and 0.716s;
the seed drains the queue then delivers the genuine stale expression response
after reload. Raw stdout/stderr are retained at
`/private/tmp/stage7-retained-seed.log` and
`/private/tmp/stage7-retained-restore.log`. The earlier scoped-only candidate passed locally but failed in
Linux CI, demonstrating the intermittent behavior was not fixed by scoping
alone. [PR run 38480339404](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38480339404)
failed Linux after the diagnostic was added; [its Linux job log](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38480339404)
records the canceled target. The [Ubuntu acceptance artifact 11856528899](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38480339404/artifacts/11856528899)
contains the JUnit report and setup metadata.
The run's other platform jobs are pending. Hosted confirmation of the bounded
drain candidate is still required.
