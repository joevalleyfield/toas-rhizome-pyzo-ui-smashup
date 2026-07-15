from __future__ import annotations

import unittest

from spikes.peer_frames.commands import (
    CLOSE_FRAME_COMMAND,
    CLOSE_GROUP_COMMAND,
    CLOSE_PANE_COMMAND,
    QUIT_COMMAND,
    CommandDescriptor,
    CommandRegistry,
    InvocationStatus,
    register_close_commands,
)
from spikes.peer_frames.contract import (
    ActiveContext,
    Direction,
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

    def test_state_snapshot_resolves_context_once_with_dynamic_shortcuts(self) -> None:
        contexts = [
            ActiveContext(PaneDescriptor("editor", PaneKind.EDITOR, "Editor")),
            ActiveContext(PaneDescriptor("shell", PaneKind.SHELL, "Shell")),
        ]
        resolutions: list[ActiveContext] = []

        def resolve() -> ActiveContext:
            context = contexts[len(resolutions)]
            resolutions.append(context)
            return context

        commands = CommandRegistry(resolve)
        for command_id in ("first", "second"):
            commands.register(
                CommandDescriptor(
                    command_id,
                    command_id.title(),
                    lambda _context: None,
                    label_for=lambda context, command_id=command_id: (
                        f"{command_id.title()} {context.pane.title}"
                    ),
                    checked_when=lambda context: (
                        context.pane is not None
                        and context.pane.kind is PaneKind.EDITOR
                    ),
                    shortcuts_for=lambda context: (
                        ("Ctrl+E",)
                        if context.pane is not None
                        and context.pane.kind is PaneKind.EDITOR
                        else ("Ctrl+S",)
                    ),
                    checkable=True,
                )
            )

        states = commands.states()

        self.assertEqual(resolutions, contexts[:1])
        self.assertEqual(
            [state.label for state in states],
            ["First Editor", "Second Editor"],
        )
        self.assertEqual([state.checked for state in states], [True, True])
        self.assertEqual([state.checkable for state in states], [True, True])
        self.assertEqual([state.shortcuts for state in states], [("Ctrl+E",)] * 2)

    def test_close_command_ids_and_empty_context_state_are_distinct(self) -> None:
        quit_calls: list[bool] = []
        commands = CommandRegistry(self.model.resolve_active_context)
        register_close_commands(
            commands, self.model, lambda: quit_calls.append(True)
        )

        self.assertEqual(
            [descriptor.id for descriptor in commands.descriptors],
            [
                CLOSE_PANE_COMMAND,
                CLOSE_GROUP_COMMAND,
                CLOSE_FRAME_COMMAND,
                QUIT_COMMAND,
            ],
        )
        self.assertEqual(
            [state.enabled for state in commands.states()],
            [False, False, False, True],
        )
        before = self.model.serialize_layout()
        for command_id in (
            CLOSE_PANE_COMMAND,
            CLOSE_GROUP_COMMAND,
            CLOSE_FRAME_COMMAND,
        ):
            self.assertEqual(
                commands.invoke(command_id).status,
                InvocationStatus.DISABLED,
            )
        self.assertEqual(self.model.serialize_layout(), before)
        self.assertTrue(commands.invoke(QUIT_COMMAND).invoked)
        self.assertEqual(quit_calls, [True])
        self.assertEqual(self.model.serialize_layout(), before)

    def test_close_commands_target_pane_group_and_frame_scopes(self) -> None:
        def populated() -> tuple[WorkspaceModel, CommandRegistry]:
            model = WorkspaceModel(FakeBackend())
            for pane_id in ("one", "two", "three", "other"):
                self.assertTrue(
                    model.register_pane(
                        PaneDescriptor(pane_id, PaneKind.EDITOR, pane_id.title())
                    ).applied
                )
            model.create_frame("one", "workspace")
            model.create_frame("two", "temporary")
            model.tab("two", "one")
            model.create_frame("three", "third-frame")
            model.split("three", "one", direction=Direction.RIGHT)
            model.create_frame("other", "other-frame")
            commands = CommandRegistry(model.resolve_active_context)
            register_close_commands(commands, model, lambda: None)
            return model, commands

        pane_model, pane_commands = populated()
        pane_model.activate("two")
        self.assertTrue(pane_commands.invoke(CLOSE_PANE_COMMAND).value.applied)
        self.assertEqual(set(pane_model.panes), {"one", "three", "other"})

        group_model, group_commands = populated()
        group_model.activate("two")
        self.assertTrue(group_commands.invoke(CLOSE_GROUP_COMMAND).value.applied)
        self.assertEqual(set(group_model.panes), {"three", "other"})
        self.assertIn("workspace", group_model.frames)

        frame_model, frame_commands = populated()
        frame_model.activate("one")
        self.assertTrue(frame_commands.invoke(CLOSE_FRAME_COMMAND).value.applied)
        self.assertEqual(set(frame_model.panes), {"other"})
        self.assertEqual(list(frame_model.frames), ["other-frame"])
        self.assertFalse(frame_model.shutdown_requested)

    def test_repeated_close_retargets_fresh_context_until_empty(self) -> None:
        for command_id in (
            CLOSE_PANE_COMMAND,
            CLOSE_GROUP_COMMAND,
            CLOSE_FRAME_COMMAND,
        ):
            with self.subTest(command_id=command_id):
                model = WorkspaceModel(FakeBackend())
                for pane_id in ("first", "second"):
                    model.register_pane(
                        PaneDescriptor(pane_id, PaneKind.EDITOR, pane_id.title())
                    )
                    model.create_frame(pane_id, f"{pane_id}-frame")
                model.activate("first")
                commands = CommandRegistry(model.resolve_active_context)
                register_close_commands(commands, model, lambda: None)

                self.assertTrue(commands.invoke(command_id).value.applied)
                self.assertEqual(set(model.panes), {"second"})
                self.assertTrue(commands.invoke(command_id).value.applied)
                self.assertEqual(model.panes, {})
                self.assertEqual(
                    commands.invoke(command_id).status,
                    InvocationStatus.DISABLED,
                )

if __name__ == "__main__":
    unittest.main()
