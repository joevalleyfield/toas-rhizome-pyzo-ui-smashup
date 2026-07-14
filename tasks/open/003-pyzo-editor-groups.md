# Experiment 003: Introduce multiple editor groups in Pyzo

## Objective

Make the smallest Pyzo-local change that supports multiple simultaneously
visible editor groups while retaining document tabs and ordinary editing.

## Acceptance criteria

- Two or more editor groups are visible simultaneously.
- Documents can be opened and moved between groups without losing content.
- Nested splits, floating groups, drag-and-drop, and re-docking work.
- Existing editor operations and document-tab behavior remain usable.
- The change is attributable to a clear Pyzo fork or integration boundary.

## Allowed write surface

- The local Pyzo project surface under `deps/pyzo` or its explicitly chosen
  fork/worktree.
- Root-level integration notes.
- This task artifact for evidence.

## Completion evidence

Record the changed Pyzo components, demonstration procedure, known limitations,
and whether the change required a fork rather than extension points.
