# Feasibility Plan

This plan turns [REQUIREMENTS.md](REQUIREMENTS.md) into a sequence of
experiments. Each experiment should reduce one major uncertainty before the
next layer is attempted.

## Phase 0 — Establish the baseline

Run the assembled Pyzo checkout on macOS and document its current Qt binding,
editor/container architecture, run workflow, and live/post-mortem debugging
behavior. The result is a baseline against which every later experiment can be
compared.

## Phase 1 — Prove the docking mechanism independently

Build the smallest docking spike that demonstrates the required Visual
Studio-like interactions: multiple editor-like widgets, nested splits, floating
groups, drag-and-drop rearrangement, and re-docking. Confirm the binding and
build path are compatible with Pyzo's Qt stack before modifying Pyzo.

## Phase 2 — Prove multiple editor groups inside Pyzo

Introduce the smallest Pyzo-local change that permits more than one visible
editor group while preserving document tabs and ordinary editing. Demonstrate
that groups can be split, floated, moved, and re-docked without losing document
or editor state.

## Phase 3 — Preserve Pyzo's core tools

Exercise the editor, shell, file browser, run workflow, and live debugger in the
multi-group layout. Identify and repair assumptions that still treat the
editor as a single central pane.

## Phase 4 — Preserve post-mortem re-entry

Exercise the complete post-mortem workflow after an unhandled exception:
re-enter the captured session, select a stack frame, navigate to its source,
and execute live interpreter code against that frame. Repeat after layout
changes, including floating and re-docking.

## Phase 5 — Integrated feasibility demonstration

Run the full acceptance workflow from REQUIREMENTS.md, record portability risks
for Windows and Linux, and decide whether Pyzo is a viable foundation for a
longer-lived fork and later toas/rhizome window integrations.

## Ordering rule

Do not begin toas or rhizome UI integration until Phase 4 succeeds or produces
a clearly bounded blocker. The first decision is whether Pyzo can support the
required editor and debugging model; the later product shape depends on that
answer.
