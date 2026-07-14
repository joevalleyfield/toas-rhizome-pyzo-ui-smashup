# Experiment 010: Bound the required technology forks

## Objective

Convert the preceding experiment evidence into a precise ownership and fork
decision for Pyzo, the Python QtADS binding, and QtADS itself.

## Dependencies

- Experiments 006 through 009 are complete or have bounded blockers.
- Experiment 004 has verified the required run/debug and post-mortem workflow.

## Acceptance criteria

- Every requirement is mapped to stock behavior, adapter policy, Pyzo change,
  binding change, QtADS change, or unsupported behavior.
- Each proposed fork point names the smallest source component and invariant it
  must provide.
- QtADS changes distinguish instrumentation, macOS-only workarounds, binding
  exposure, and cross-platform architectural changes.
- The assessment compares maintaining a narrow fork with replacing the docking
  backend, without assuming sunk-cost continuation.
- Windows and Linux validation obligations are listed for every platform-
  sensitive change.
- The result recommends stock-plus-adapter, bounded fork, deeper fork, or
  replacement with explicit rationale and unresolved risks.

## Allowed write surface

- Root-level feasibility, dependency, and fork-boundary documentation.
- This task artifact for evidence.
- No new implementation beyond tiny reproductions needed to attribute an
  unresolved behavior.

## Completion evidence

Record a requirement-to-owner matrix, exact candidate fork surfaces, upstream
compatibility considerations, portability obligations, and the recommendation
consumed by Experiment 005.

