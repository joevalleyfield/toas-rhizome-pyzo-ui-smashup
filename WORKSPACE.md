# Workspace Topology and Authority

## Vision

This repository is the coordinating root for a Python development workbench
experiment. It is the control plane for combining ideas and code from Pyzo,
toas, rhizome, and Qt Advanced Docking System (QtADS), while those projects
remain independently identifiable and independently maintainable.

The root repository should provide one coherent working context without forcing
an early decision to merge everything into a monorepo or fork Pyzo. It records
the shared requirements, dependency choices, integration boundaries, and
evidence needed to decide which upstreams become long-lived forks.

## Authority model

The root's instructions and requirements govern the assembled workspace. They
describe the intended product behavior and integration contract. A dependency's
own instructions continue to govern changes made within that dependency, unless
the root explicitly establishes a narrower integration requirement.

Authority flows downward through the assembled workspace:

```text
workbench root
  ├── Pyzo upstream or local fork
  ├── QtADS upstream or compatible docking implementation
  ├── toas upstream or local fork
  └── rhizome upstream or local fork
```

The root owns cross-project decisions. Each project surface owns its internal
implementation. A change should be made in the smallest project surface that
can own it, then validated from the root integration context.

## Project surfaces

The workspace may contain checked-out dependencies, linked working trees,
submodules, or local forks. The assembly mechanism is deliberately left open
until the upstream repositories and their development workflows are inspected.

The important boundary is ownership, not the checkout mechanism:

- **Pyzo surface:** editor, shell, file browser, run workflow, and debugging.
- **Docking surface:** QtADS or a compatible implementation of Visual Studio-
  like layout management.
- **toas surface:** future transcript-editor and agent/workflow integration.
- **rhizome surface:** future supporting ideas, code, and integration candidates.
- **Root surface:** requirements, topology, dependency pins, integration
  evidence, and decisions about whether a local fork is warranted.

## Fork policy

Upstream projects should remain upstream references until a concrete integration
need requires local changes. A fork is justified when the required behavior
cannot be achieved through supported extension points or a thin integration
layer. Local changes should remain attributable to the project surface where
they belong, even when the root coordinates their use.

Upstreamability is a useful quality signal, but it is not a first-prototype
constraint. The immediate priority is proving the multi-editor docking and
post-mortem debugging workflow described in `REQUIREMENTS.md`.

## Assembly principles

- Keep dependency identity and provenance explicit.
- Prefer reproducible references over implicit copies.
- Preserve each dependency's tests and development workflow.
- Keep cross-project glue at the root or in a clearly owned integration
  surface.
- Avoid irreversible repository restructuring before the Pyzo feasibility
  question is answered.
- Validate the assembled workspace from the root, while preserving local
  ownership of dependency-specific changes.

## Initial assembly objective

Discover the canonical repositories and compatible versions for Pyzo, QtADS (or
an equivalent), toas, and rhizome. Assemble them under this coordinating root
in a way that supports inspection and experimentation without yet committing
to a permanent monorepo or Pyzo fork.

Record the chosen sources, revisions, assembly mechanism, and any blockers in
the root as the workspace evolves.
