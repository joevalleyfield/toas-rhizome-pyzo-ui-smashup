"""Application-owned commands resolved against peer-workspace context."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable

from .contract import ActiveContext, WorkspaceModel


CommandHandler = Callable[[ActiveContext], object]
CommandPredicate = Callable[[ActiveContext], bool]
CommandLabel = Callable[[ActiveContext], str]
CommandShortcuts = Callable[[ActiveContext], tuple[str, ...]]
ContextResolver = Callable[[], ActiveContext]
QuitHandler = Callable[[], object]


CLOSE_PANE_COMMAND = "workspace.close-pane"
CLOSE_GROUP_COMMAND = "workspace.close-group"
CLOSE_FRAME_COMMAND = "workspace.close-frame"
QUIT_COMMAND = "application.quit"


def _enabled(_context: ActiveContext) -> bool:
    return True


def _unchecked(_context: ActiveContext) -> bool:
    return False


@dataclass(frozen=True)
class CommandDescriptor:
    """Toolkit-neutral definition owned once by the application."""

    id: str
    label: str
    handler: CommandHandler
    enabled_when: CommandPredicate = _enabled
    checked_when: CommandPredicate = _unchecked
    label_for: CommandLabel | None = None
    shortcuts: tuple[str, ...] = ()
    shortcuts_for: CommandShortcuts | None = None
    checkable: bool = False


@dataclass(frozen=True)
class CommandState:
    id: str
    label: str
    enabled: bool
    checked: bool
    shortcuts: tuple[str, ...]
    checkable: bool


class InvocationStatus(str, Enum):
    INVOKED = "invoked"
    DISABLED = "disabled"


@dataclass(frozen=True)
class CommandInvocation:
    status: InvocationStatus
    value: object = None

    @property
    def invoked(self) -> bool:
        return self.status is InvocationStatus.INVOKED


class CommandRegistry:
    """Ordered command service with late-bound application context."""

    def __init__(self, context_resolver: ContextResolver):
        self._context_resolver = context_resolver
        self._descriptors: dict[str, CommandDescriptor] = {}

    @property
    def descriptors(self) -> tuple[CommandDescriptor, ...]:
        return tuple(self._descriptors.values())

    def register(self, descriptor: CommandDescriptor) -> None:
        if not descriptor.id:
            raise ValueError("command id must not be empty")
        if descriptor.id in self._descriptors:
            raise ValueError(f"command already registered: {descriptor.id}")
        self._descriptors[descriptor.id] = descriptor

    def state(self, command_id: str) -> CommandState:
        return self.states_for((command_id,))[0]

    def states(self) -> tuple[CommandState, ...]:
        return self.states_for(self._descriptors)

    def resolve_context(self) -> ActiveContext:
        return self._context_resolver()

    def states_for(
        self,
        command_ids: Iterable[str],
        context: ActiveContext | None = None,
    ) -> tuple[CommandState, ...]:
        context = self.resolve_context() if context is None else context
        return tuple(
            self._state(self._descriptor(command_id), context)
            for command_id in command_ids
        )

    def invoke(self, command_id: str) -> CommandInvocation:
        descriptor = self._descriptor(command_id)
        context = self._context_resolver()
        if not descriptor.enabled_when(context):
            return CommandInvocation(InvocationStatus.DISABLED)
        return CommandInvocation(
            InvocationStatus.INVOKED,
            descriptor.handler(context),
        )

    def _descriptor(self, command_id: str) -> CommandDescriptor:
        try:
            return self._descriptors[command_id]
        except KeyError:
            raise KeyError(f"unknown command: {command_id}") from None

    @staticmethod
    def _state(
        descriptor: CommandDescriptor, context: ActiveContext
    ) -> CommandState:
        label = (
            descriptor.label_for(context)
            if descriptor.label_for is not None
            else descriptor.label
        )
        shortcuts = (
            descriptor.shortcuts_for(context)
            if descriptor.shortcuts_for is not None
            else descriptor.shortcuts
        )
        return CommandState(
            id=descriptor.id,
            label=label,
            enabled=descriptor.enabled_when(context),
            checked=descriptor.checked_when(context),
            shortcuts=shortcuts,
            checkable=descriptor.checkable,
        )


def register_close_commands(
    registry: CommandRegistry,
    workspace: WorkspaceModel,
    quit_handler: QuitHandler,
) -> None:
    """Register distinct application-owned pane, group, frame, and Quit routes."""

    registry.register(
        CommandDescriptor(
            CLOSE_PANE_COMMAND,
            "Close Pane",
            lambda context: workspace.request_close_pane(context.pane.id),
            enabled_when=lambda context: context.pane is not None,
        )
    )
    registry.register(
        CommandDescriptor(
            CLOSE_GROUP_COMMAND,
            "Close Group",
            lambda context: workspace.request_close_group(context.group_id),
            enabled_when=lambda context: context.group_id is not None,
        )
    )
    registry.register(
        CommandDescriptor(
            CLOSE_FRAME_COMMAND,
            "Close Frame",
            lambda context: workspace.request_close_frame(context.frame_id),
            enabled_when=lambda context: context.frame_id is not None,
        )
    )
    registry.register(
        CommandDescriptor(
            QUIT_COMMAND,
            "Quit",
            lambda _context: quit_handler(),
            shortcuts=("Ctrl+Q",),
        )
    )
