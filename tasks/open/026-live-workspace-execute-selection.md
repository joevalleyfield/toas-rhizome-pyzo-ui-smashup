# 026: Route Execute Selection through the invoking workspace

## Status

READY after the accepted 023–025 retention integration review, 2026-10-04.
This is Experiment 014 Stage 4's first live slice under the September amendment.
It is a follow-up candidate; no implementation or Stage 4 acceptance is implied.

## Outcome

Two real workspaces each own a live shell and can Execute Selection into their
own interpreter. Invoking an editor in A while a shell in B was most recently
foregrounded must not send A's code to B. Use the existing pure execution router
and preserve the legacy single-workspace route.

## Allowed surface

Root execution model/probe/tests; Pyzo shell runtime creation and registration,
application execution service, RunCommandService selection path, focused tests;
this task and linked evidence. Do not migrate all Run variants, breakpoints,
tools or preferences in this slice. No QtADS/binding or TOAS/Rhizome changes.

## State/assertion gate before implementation

- Invoking view belongs to A/B, or is retired/unavailable; never capture an
  operation from the compatibility primary alias when its owner is known.
- Local foreground shell is eligible, absent, lost, or recycled. Foreground
  recency in another workspace must not create a fallback queue.
- Captured view/shell identity and kernel generation may remain current or
  become stale between invocation and dispatch/completion.
- Native pane/frame movement within an owner preserves shell identity;
  cross-workspace transfer is visibly refused.

Encode delivery counts and values in two actual kernel namespaces, captured
workspace/view/shell identities, source bytes unchanged by Execute Selection,
no send on an ineligible or stale target, and a visible explanation on refusal.
Map every case to a meaningful assertion before changing the routing boundary.

## Acceptance

The real two-kernel probe verifies A/B routing in both focus orders, no local
shell, target loss, recycle, stale result rejection, and source-byte preservation.
Focused router/service controls and full peer/legacy Run/live-debug/postmortem
controls stay green. Commit the bounded slice and record revisions and remaining
Stage 4 gates: explicit assignment UI, broken-target correction, all Execute and
File/Main variants, and complete operation provenance. Shell migration and
zombies remain deferred. File Move/Fork UX remains a later explicit local slice.
