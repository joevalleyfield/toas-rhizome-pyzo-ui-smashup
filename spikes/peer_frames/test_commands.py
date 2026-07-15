from __future__ import annotations

import unittest

from spikes.peer_frames.commands import (
    CommandDescriptor,
    CommandRegistry,
    InvocationStatus,
)
from spikes.peer_frames.contract import (
    ActiveContext,
    PaneDescriptor,
    PaneKind,
    WorkspaceModel,
)
from spikes.peer_frames.fake_backend import FakeBackend


class ApplicationCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = FakeBackend()
        self.model = WorkspaceModel(self.backend)

    def register_pane(self, pane_id: str, kind: PaneKind) -> None:
        result = self.model.register_pane(
            PaneDescriptor(pane_id, kind, pane_id.title())
        )
        self.assertTrue(result.applied)

    def test_active_context_tracks_application_identity_through_moves(self) -> None:
        self.assertEqual(self.model.resolve_active_context(), ActiveContext())
        self.register_pane("editor", PaneKind.EDITOR)
        self.register_pane("shell", PaneKind.SHELL)
        self.model.create_frame("editor", "editor-frame")
        editor_context = self.model.resolve_active_context()
        self.assertEqual(editor_context.pane.id, "editor")
        self.assertEqual(editor_context.frame_id, "editor-frame")
        self.assertIsNotNone(editor_context.group_id)

        self.model.create_frame("shell", "shell-frame")
        shell_context = self.model.resolve_active_context()
        self.assertEqual(shell_context.pane.id, "shell")
        self.assertEqual(shell_context.frame_id, "shell-frame")

        self.model.tab("shell", "editor")
        merged_context = self.model.resolve_active_context()
        self.assertEqual(merged_context.pane.id, "shell")
        self.assertEqual(merged_context.frame_id, "editor-frame")
        self.assertEqual(merged_context.group_id, editor_context.group_id)

        self.model.float("editor", "floated-editor")
        floated_context = self.model.resolve_active_context()
        self.assertEqual(floated_context.pane.id, "editor")
        self.assertEqual(floated_context.frame_id, "floated-editor")
        self.assertNotEqual(floated_context.group_id, editor_context.group_id)

    def test_registry_resolves_dynamic_state_and_invocation_late(self) -> None:
        seen: list[ActiveContext] = []
        commands = CommandRegistry(self.model.resolve_active_context)
        commands.register(
            CommandDescriptor(
                id="editor.inspect",
                label="Inspect editor",
                label_for=lambda context: (
                    f"Inspect {context.pane.title}"
                    if context.pane is not None
                    else "Inspect editor"
                ),
                handler=lambda context: seen.append(context) or context.pane.id,
                enabled_when=lambda context: (
                    context.pane is not None
                    and context.pane.kind is PaneKind.EDITOR
                ),
                checked_when=lambda context: context.frame_id == "editor-frame",
                shortcuts=("Ctrl+I", "Alt+I"),
            )
        )

        state = commands.state("editor.inspect")
        self.assertEqual(state.label, "Inspect editor")
        self.assertFalse(state.enabled)
        self.assertFalse(commands.invoke("editor.inspect").invoked)
        self.assertEqual(seen, [])

        self.register_pane("editor", PaneKind.EDITOR)
        self.model.create_frame("editor", "editor-frame")
        state = commands.state("editor.inspect")
        self.assertEqual(state.label, "Inspect Editor")
        self.assertTrue(state.enabled)
        self.assertTrue(state.checked)
        self.assertEqual(state.shortcuts, ("Ctrl+I", "Alt+I"))
        invocation = commands.invoke("editor.inspect")
        self.assertEqual(invocation.status, InvocationStatus.INVOKED)
        self.assertEqual(invocation.value, "editor")
        self.assertEqual(seen[-1], self.model.resolve_active_context())

        self.register_pane("shell", PaneKind.SHELL)
        self.model.create_frame("shell", "shell-frame")
        state = commands.state("editor.inspect")
        self.assertEqual(state.label, "Inspect Shell")
        self.assertFalse(state.enabled)
        self.assertFalse(state.checked)
        self.assertEqual(
            commands.invoke("editor.inspect").status,
            InvocationStatus.DISABLED,
        )
        self.assertEqual(len(seen), 1)

    def test_registration_is_ordered_and_unique(self) -> None:
        commands = CommandRegistry(self.model.resolve_active_context)
        first = CommandDescriptor("first", "First", lambda _context: None)
        second = CommandDescriptor("second", "Second", lambda _context: None)
        commands.register(first)
        commands.register(second)

        self.assertEqual(commands.descriptors, (first, second))
        self.assertEqual(
            [state.id for state in commands.states()],
            ["first", "second"],
        )
        with self.assertRaisesRegex(ValueError, "already registered"):
            commands.register(first)
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            commands.register(CommandDescriptor("", "Empty", lambda _context: None))
        with self.assertRaisesRegex(KeyError, "unknown command"):
            commands.state("missing")


if __name__ == "__main__":
    unittest.main()
