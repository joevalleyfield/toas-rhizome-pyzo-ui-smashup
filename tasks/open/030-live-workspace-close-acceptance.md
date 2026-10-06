# 030: Real-kernel workspace-close acceptance

## Status

DONE — accepted by Engineer (Codex), 2026-10-05 under user “Do it to it.”
Depends on accepted 026–029. This closes the missing integrated Stage 4 closure
evidence identified in review; the September amendment remains normative.
The earlier broad Stage 4 sign-off did not establish this combined proof.

## Outcome and allowed writes

Two actual, ready workspace-owned kernels and unsaved retained documents prove
workspace Cancel, persistence failure before irreversible teardown, and accepted
termination/reopen with the other workspace intact. Capture durable evidence and
correct the acceptance ledger. Allowed: root owned Qt probe/harness and focused
tests; bounded workspace-close, persistence-preflight or shell confirmation cleanup
fixes if the proof exposes gaps; task/evidence and mutable roadmap references.
No Stage 5 breakpoint/debugger ownership implementation, Stage 6 isolation,
binding, TOAS/Rhizome or deferred migration/zombie/portable work.

## Pre-edit state/assertion map

| State/order | Executable assertion | Path / current evidence gap |
| --- | --- | --- |
| A/B ready kernels; independent namespaces, dirty named/untitled/shared views; explicit assignments | `ready(A) and ready(B)`; distinct process IDs; expected namespaces/source baselines/owner/view tokens | Existing two-kernel scaffold; workspace-close proof does not assert kernel readiness |
| Workspace A cancel; foreign B active; confirmation after a prior cancel | `result.cancelled`; exact A/B topology/view/assignment/context/generation snapshots unchanged; namespaces queryable; terminate/close/unbind events empty | Existing workspace cancellation checks only loaded IDs and manifest generation |
| Retention publication fails with terminate selected, before manifest replacement | `not result.applied`; old durable manifest/generation unchanged; zero terminate/close/unbind; exact live snapshots/namespaces intact; visible refusal | Separate application/model failure controls, no integrated workspace close |
| Failure then cancel then retry | fresh confirmation on every attempt; canceled/failed confirmation intent cannot silently authorize later close; same original native objects remain until accepted retry | Preflight pending-confirmation cleanup needs observation |
| Terminate-and-close A; B remains active | at first irreversible event: durable A/B resource text/undo/views in store; only A terminate/close/unbind; B context/assignment/model generation/PID/namespace preserved | Existing successful close proves loaded set; no durable-before-actual-kernel-termination assertion |
| Asynchronous termination / queued old callbacks | actual A PID exits within owned deadline; A pane/binding gone; old provenance rejected; B still executes; no retired Qt access | Individual shell controls exist; integrated process proof missing |
| Reopen A after B edits a shared resource while A suspended | restored identity/current retained edits/dirty baseline/undo/view placement; no explicit assignment or old interpreter revived; source bytes unchanged; B remains same live kernel | Existing retention restore proof reused with real running peer |
| Timeout, test failure, normal teardown | external owned-process deadline; terminate only test-owned children; fresh appdata/command-server stub; logs and child exits captured | Existing owned harness reused |

The user explicitly authorized these cases and necessary bounded fixes. No
strict external-validation mode is requested. New states discovered in execution
will extend this map before dependent edits. Project Manager stops at READY;
Engineer must claim before source/test edits.

## Acceptance

### Observed resume refinement, before dependent edits

The live close proof passes the pending-intent rollback after its bounded fix.
Same-process resume then exposes a distinct gap: `add_workspace` rejects a
retired durable ID. Expand resume coverage to new/loaded/retired IDs, ordinary
registration versus explicit restore, invalid restore arguments and repeated
close/resume. Assert default duplicate rejection, explicit resume acceptance,
unchanged foreign owner, and `not context_is_current(old_context)` even when
pane/frame/group IDs are reused. A runtime epoch on captured contexts guards
this boundary. Also map native restoration to live retained view identities and
current shared resource text rather than a stale captured generation; the
existing shared-edit/reopen assertion covers this path. Allowed bounded writes
include the coordinator/context boundary and native restore adapter required
by this integrated closure proof. No later-stage ownership work is authorized.

Resume now passes identity, text and undo assertions but exposes the layout
count assumption: retired shells/tools leave fewer panes than the saved layout.
Before layout edits, map retained editor views to their captured pane IDs;
assert exact original frame/group placement after pruning absent panes. Cover
all-retained, partial group, removed group/frame, collapsed split, missing
mapping and saved active pane removed. Do not revive interpreter/tool objects
to satisfy layout counts. Preserve the existing startup remapping fallback for
older snapshots lacking this optional view-to-pane metadata.

The complete reopen/undo proof exposes a synchronous teardown notification:
registry view retired, native editor still bound, `setModified(False)` causes
tab Main projection before unbind. Cover bound/live, bound/retired and legacy
unbound states; assert retired Main projection returns false without reading
missing registry state or falling back to an old Main flag. Reject uncaught Qt
callback exceptions in this acceptance control; passing process exit alone is
insufficient. This is a bounded editor teardown projection fix.

Genuine native workspace-close APIs and actual kernels; record cancel/failure/
success event order, on-disk retained generation, process exit and B continuity,
reopen and source-byte preservation. Focused checks and coordinated suite; replay
live execution/retention and full peer/legacy controls if production code changes.
Commit implementation before closing this evidence debt and returning NEXT to
the existing Stage 5 gate. Preserve physical/platform acceptance limits.

## Completion

Root implementation `ee98fae17fdc1d73cec0845ca65e68d13f139fdc`; Pyzo implementation
`27b3aa04a8252a9a9a6b6858d07b691e6ddb7512`. The actual two-kernel native proof
passes Cancel, manifest publication failure, fresh confirmation on retry,
durability before teardown, A process exit, unchanged live B and same-process
shared retained resume with original view placement and actual undo/redo.
Bounded repairs clear failed close intent, allow explicit durable-ID resume with
new context epochs, restore current retained views/placement and guard retired
tab projection. No old interpreter or assignment is revived.

458 coordinated tests and 51 subtests pass; all 14 live controls and full
peer/legacy controls pass. Ten changed Python files compile; Ruff F and
whitespace pass. [Acceptance evidence and logs](../../docs/evidence/workspace-close-2026-10-05.md)
record observed event order, exact revisions, limits and the corrected 029
sign-off. Local Stage 4 is accepted through 026–030; NEXT returns to existing
014 Stage 5. The September scope and deferrals remain normative. Nothing pushed.
