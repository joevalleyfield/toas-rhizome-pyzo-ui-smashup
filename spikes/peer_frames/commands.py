"""Application-owned commands resolved against peer-workspace context."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .contract import ActiveContext, WorkspaceModel


CommandHandler = Callable[[ActiveContext], object]
CommandPredicate = Callable[[ActiveContext], bool]
CommandLabel = Callable[[ActiveContext], str]
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


@dataclass(frozen=True)
class CommandState:
    id: str
    label: str
    enabled: bool
    checked: bool
    shortcuts: tuple[str, ...]


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
        descriptor = self._descriptor(command_id)
        context = self._context_resolver()
        return self._state(descriptor, context)

    def states(self) -> tuple[CommandState, ...]:
        context = self._context_resolver()
        return tuple(
            self._state(descriptor, context)
            for descriptor in self._descriptors.values()
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
        return CommandState(
            id=descriptor.id,
            label=label,
            enabled=descriptor.enabled_when(context),
            checked=descriptor.checked_when(context),
            shortcuts=descriptor.shortcuts,
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
