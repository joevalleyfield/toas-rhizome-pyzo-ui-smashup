# Pyzo Docking Workbench Requirements

## Purpose

Explore whether Pyzo can serve as the foundation for a more capable Python
development workbench by combining Pyzo with Qt Advanced Docking System (QtADS),
or a functionally equivalent docking framework. The first prototype focuses on
removing Pyzo's single-editor-area limitation while preserving its debugging
workflow.

## First prototype

The prototype is a locally modified Pyzo based on the latest HEAD from Pyzo's
canonical published source. Substantial source changes or a local fork are
acceptable. Upstream compatibility is desirable, but is not an initial
priority.

The prototype must provide Visual Studio-like layout management:

- Multiple editor groups visible at the same time.
- Multiple document tabs within each editor group.
- Horizontal and vertical nested splits.
- Floating editor groups and panes.
- Drag-and-drop rearrangement and re-docking.

## Pyzo capabilities to preserve

The following native Pyzo workflows must remain usable alongside the new layout
system:

- Editor
- Shell
- File browser pane
- Running code
- Live debugging
- Post-mortem debugging

Post-mortem debugging is a hard requirement. The prototype must support entry
into a post-mortem debugging session after an unhandled exception, navigation
to a captured stack frame, and live interpreter execution against that selected
frame.

## Acceptance workflow

The prototype is viable if it can demonstrate this complete workflow:

1. Open multiple source documents.
2. Arrange them across multiple split editor groups.
3. Float, move, and re-dock editor groups.
4. Run code that raises an unhandled exception.
5. Enter post-mortem debugging.
6. Select a captured stack frame.
7. Execute live code in the interpreter against that frame.
8. Continue using the editor, shell, file browser, and run/debug workflows
   without losing state.

## Platform expectations

Development and initial validation will happen on macOS. The architecture must
remain practical to port to Windows and Linux, and should avoid platform-
specific choices that would make those ports difficult.

## Deferred scope

The first prototype does not include:

- A toas transcript-editor window type in Pyzo.
- Broader rhizome integration.

Those integrations remain candidate follow-up work after the Pyzo and docking
feasibility question has been answered.

## Important edge cases

- Moving or floating editors during an active debugging session.
- Preserving breakpoints, traceback navigation, shell state, and debugger
  context across layout changes.
- Executing code against the correct captured stack frame.
- Re-docking panes without losing documents or session state.
- Opening traceback locations in the correct editor group.
- Maintaining portability across Qt-supported desktop platforms.

## Feasibility deliverable

Alongside the runnable prototype, record whether Pyzo is a viable foundation for
later toas/rhizome integration, including any architectural limitations,
necessary local fork points, and portability risks discovered during the work.
