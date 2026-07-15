"""Application-owned commands resolved against peer-workspace context."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .contract import ActiveContext


CommandHandler = Callable[[ActiveContext], object]
CommandPredicate = Callable[[ActiveContext], bool]
CommandLabel = Callable[[ActiveContext], str]
ContextResolver = Callable[[], ActiveContext]


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
