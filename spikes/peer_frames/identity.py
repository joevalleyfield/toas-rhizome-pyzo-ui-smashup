"""Explicit application identity kinds and their persistence lifetimes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class IdentityKind(str, Enum):
    WORKSPACE = "workspace"
    DOCUMENT = "document"
    VIEW = "view"
    SHELL = "shell"
    KERNEL_GENERATION = "kernel-generation"
    OPERATION = "operation"
    DEBUG_SESSION = "debug-session"
    RECOVERY_SNAPSHOT = "recovery-snapshot"


class IdentityLifetime(str, Enum):
    DURABLE = "durable"
    LIVE_SESSION = "live-session"
    GENERATION = "generation"


IDENTITY_LIFETIMES = {
    IdentityKind.WORKSPACE: IdentityLifetime.DURABLE,
    IdentityKind.DOCUMENT: IdentityLifetime.DURABLE,
    IdentityKind.VIEW: IdentityLifetime.DURABLE,
    IdentityKind.SHELL: IdentityLifetime.LIVE_SESSION,
    IdentityKind.KERNEL_GENERATION: IdentityLifetime.GENERATION,
    IdentityKind.OPERATION: IdentityLifetime.LIVE_SESSION,
    IdentityKind.DEBUG_SESSION: IdentityLifetime.LIVE_SESSION,
    IdentityKind.RECOVERY_SNAPSHOT: IdentityLifetime.DURABLE,
}


@dataclass(frozen=True)
class ApplicationIdentity:
    """Opaque identity whose kind determines its persistence contract."""

    kind: IdentityKind
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, IdentityKind):
            raise TypeError("identity kind must be an IdentityKind")
        if not isinstance(self.value, str) or not self.value.strip():
            raise ValueError("identity value must be a non-empty string")

    @property
    def lifetime(self) -> IdentityLifetime:
        return IDENTITY_LIFETIMES[self.kind]

    def __str__(self) -> str:
        return self.value


def new_identity(kind: IdentityKind) -> ApplicationIdentity:
    return ApplicationIdentity(kind, uuid4().hex)
