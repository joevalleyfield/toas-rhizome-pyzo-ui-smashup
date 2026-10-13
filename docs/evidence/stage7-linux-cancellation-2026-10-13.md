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
with `IOError`. The failure output does not report the future's status history,
so it cannot distinguish these two causes.

Inspection of the pinned source found no explicit cancellation of expression
viewer requests: `ExpressionProxy.evaluateExpressions` submits requests, its
completion callback accepts cancellation as “no living kernel,” and
`nativeRequests.request` rejects stale callbacks without cancelling the Future.
The prior acceptance hold intercepted every A-shell request until all held
Futures completed, even though its intent is to delay one response from the
explicit `manualRefresh()`. That makes unrelated later request failures capable
of failing the stale-reply check. The hold now exists only during that
synchronous refresh call, asserts that it intercepted exactly one
`evalMultiple` request, then restores `ReqChannel`'s dynamic proxy correctly.
Cancelled or failed target requests still raise; diagnostic output includes
method, elapsed hold time, Yoton status, cancellation state, and its configured
auto-cancel timeout. No timeout or deadline was extended.

Validation: pinned Pyzo was checked out read-only at 803afaf3 under
`/private/tmp`. A new fake-request regression demonstrates that the old
interval-wide hold also captures a later unrelated canceled request, while the
scoped hold allows that request to remain independent and still fails if the
target expression request itself is canceled (2 tests pass). The exact-pinned
live `workspace-tools` seed and fresh-process `tools-restore` pair both pass
locally on macOS in 4.157s and 0.713s respectively, including delivery of the
genuine stale expression response after reload. The unmodified interval-wide probe also passes locally and
captures one `evalMultiple` request, so this does not reproduce the Linux
intermittency. The original Linux artifact has no request method/status/timing
telemetry, so its cancellation cause remains unknown pending hosted Linux
replay. Original phase and external deadlines and success assertions are
unchanged.
