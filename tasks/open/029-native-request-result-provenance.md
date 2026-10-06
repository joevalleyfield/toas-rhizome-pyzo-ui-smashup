# 029: Native request/result provenance

## Status

COMPLETE — accepted by Codex; compiled READY by Project Manager and claimed by Engineer,
2026-10-05 under user “Onward.” Depends on accepted 028. September scope amendment
remains normative; this is the existing Stage 4 gate, without new priorities.

## Outcome and allowed writes

Carry operation, invoking view/owner and interpreter generation through actual
completion/help/tool requests and Run/debugger transport. Reject stale replies
before caches, widgets or follow-up execution. Preserve native/legacy policies.
Allowed: Pyzo execution bridge, native request helper, editor/shell/help/tool
callback wiring, bounded kernel envelopes, focused tests, test-owned live probe,
evidence and mutable queue references. Stage 5 debugger/session/breakpoint
ownership, Stage 6 tool/config/history isolation, binding and September deferrals
remain outside this task.

## Pre-edit assertion map

| State/order | Assertion | Current path/gap |
| --- | --- | --- |
| Local implicit/explicit editor target, foreign focus | only resolved shell receives completion/help; echoed operation/owner/view/generation equal captured receipt | Native editor still uses global current shell |
| Direct shell/tool/debugger request | captured direct shell/process owner; focus/selection switch rejects consumer reply | Native direct channels have no receipt |
| Reply immediate, delayed, out of order, failed/canceled, malformed | metadata attached before callback; only latest valid consumer query updates; failed/invalid zero writes | Registration precedes future metadata; no latest-query guard |
| View close/reopen/move, document edit, cursor/query change, consumer destruction | zero UI/cache/follow-up execution for old source/lifetime/query | Native callbacks use global active editor and may touch retired widgets |
| Assignment/foreground changes, shell loss/reconnect/restart/context replacement | old generation/route rejected; fresh request accepted; no fallback | Bridge model guard exists but native callbacks bypass it |
| Cached completion from another route/generation/source | cache reused only if captured receipt/source remains current | Cache currently checks only name/timeout |
| Run/debugger actual transport and completion | kernel echoes exact receipt; old operation result rejected; ordinary stdout and legacy controls preserved | Native TEXT/OBJECT messages lack operation tags |
| Scripts restart versus in-process IPython | recycle receipt bridges startup without accepting old generation; legacy native behavior preserved | Native startup untagged |
| Legacy, live two-kernel, Run/debug/postmortem, retention | controls green, owned child processes terminated | Existing replay harness reused |

The native kernel emits an initial debugger reset before startup metadata exists:
assert this reset cannot prevent startup; retired startup channels/epochs and
queued old-transport execution must be rejected. A complete restart can occur
between two bridge synchronizations: assert transport-epoch change advances
the model generation even if the transient unavailable state was never observed. Tool-triggered commands and
native debugger frame selection use the same direct transport receipt.

A valid result for a background view may fill only its tagged cache; it must
not display a completion popup or calltip in the active foreign view. Shell
completion must not auto-import from a foreign global editor.

Assertions precede source/test edits. “Onward” authorizes this gate, necessary
fixes and verification; no external validation mode is requested. New states
discovered during implementation will extend this map before dependent edits.

## Acceptance

Focused executable state assertions plus real two-workspace kernels exercising
native requests and receipts, coordinated suite, full peer/legacy controls.
Record exact revisions, results, cleanup and remaining platform limits. Commit
implementation before accepting the gate and advancing the existing roadmap.


## Completion

Accepted root implementation `9072a23e98ff7c878553edd12aaa68c4020c93f4` and Pyzo
`e79cf5e442f2f9156414d0c7ca1540b0a58e1a7c`. Native queries, callbacks/caches,
Run/debugger transport and script startup now carry and validate receipts.
Retired generations, sources, consumers and superseded queries are rejected.
The real-kernel proof closes the observed startup-reset and missed-restart gaps.

**451 coordinated tests and 45 subtests pass; 13 live controls pass.** Full peer
and legacy workflows pass. All 24 changed Python files compile; Ruff F and
whitespace checks pass. Implementation commits precede roadmap advancement.
[Completion evidence and logs](../../docs/evidence/native-provenance-2026-10-05.md)
record exact revisions, genuine held replies, cleanup and platform limits.

Together with 026–028 this accepts local Stage 4. The next existing gate is 014
Stage 5; debugger/session/breakpoint ownership and conservative closure remain
there, tool/config/history isolation in Stage 6. The September amendment and all
its deferrals remain normative. Nothing was pushed.
