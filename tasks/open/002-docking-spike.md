# Experiment 002: Prove the docking mechanism independently

## Objective

Demonstrate that QtADS or a functionally equivalent framework can provide the
required Visual Studio-like layout interactions with the Qt stack used by Pyzo.

## Acceptance criteria

- Multiple editor-like widgets can coexist in separate groups.
- Groups support horizontal and vertical nested splits.
- Groups or panes can float, move by drag-and-drop, and re-dock.
- The interaction works on macOS and does not depend on a platform-specific
  design that obviously blocks Windows or Linux.
- The binding/build decision and any compatibility gap with Pyzo are recorded.

## Allowed write surface

- A dedicated root-level spike directory.
- Dependency build/configuration files only when necessary for the experiment.
- This task artifact for evidence.

## Completion evidence

Record the runnable entry point, dependency revisions, screenshots or a concise
interaction log, and compatibility findings.
