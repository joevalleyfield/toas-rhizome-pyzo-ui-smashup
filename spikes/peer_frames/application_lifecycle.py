"""Application lifetime policy above peer-frame and pane topology."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class ZeroFrameResult(str, Enum):
    SURVIVING = "surviving"
    QUIT_REQUESTED = "quit-requested"
    FRAME_EXISTS = "frame-exists"
    FRAME_CREATED = "frame-created"
    COALESCED = "coalesced"
    FATAL = "fatal"


class ApplicationExitDisposition(str, Enum):
    QUIT = "quit"
    RESTART = "restart"


class ApplicationExitPhase(str, Enum):
    IDLE = "idle"
    NEGOTIATING = "negotiating"
    CLEANING = "cleaning"
    FINISHED = "finished"


class ApplicationExitResult(str, Enum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    COALESCED = "coalesced"
    FAILED = "failed"


@dataclass(frozen=True)
class CleanupStep:
    name: str
    run: Callable[[], None]


@dataclass(frozen=True)
class WorkspaceShutdownResult:
    accepted: bool
    cleanup_errors: tuple[str, ...] = ()


class ApplicationShutdownCoordinator:
    """Own one explicit application-exit transaction.

    Pane/resource negotiation commits before process cleanup starts. Once that
    boundary is crossed, cleanup is best-effort and cannot roll topology back.
    """

    def __init__(
        self,
        *,
        confirm_exit: Callable[[ApplicationExitDisposition], bool],
        request_workspace_shutdown: Callable[[], bool | WorkspaceShutdownResult],
        prepare_cleanup: Callable[[], None] | None = None,
        cleanup_steps: tuple[CleanupStep, ...],
        finish_quit: Callable[[int], None],
        replace_process: Callable[[], None],
        log_error: Callable[[str], None],
    ):
        self._confirm_exit = confirm_exit
        self._prepare_cleanup = prepare_cleanup
        self._request_workspace_shutdown = request_workspace_shutdown
        self._cleanup_steps = cleanup_steps
        self._finish_quit = finish_quit
        self._replace_process = replace_process
        self._log_error = log_error
        self.phase = ApplicationExitPhase.IDLE
        self.disposition: ApplicationExitDisposition | None = None
        self.last_errors: tuple[str, ...] = ()

    def request(
        self, disposition: ApplicationExitDisposition
    ) -> ApplicationExitResult:
        if self.phase is not ApplicationExitPhase.IDLE:
            return ApplicationExitResult.COALESCED

        self.phase = ApplicationExitPhase.NEGOTIATING
        self.disposition = disposition
        self.last_errors = ()
        try:
            if not self._confirm_exit(disposition):
                self._reset_after_cancellation()
                return ApplicationExitResult.CANCELLED
            if self._prepare_cleanup is not None:
                try:
                    self._prepare_cleanup()
                except Exception as error:
                    self._log_error(f"application persistence preflight failed: {error}")
                    self._reset_after_cancellation()
                    return ApplicationExitResult.CANCELLED
            workspace_result = self._request_workspace_shutdown()
            if isinstance(workspace_result, bool):
                workspace_result = WorkspaceShutdownResult(workspace_result)
            if not workspace_result.accepted:
                self._reset_after_cancellation()
                return ApplicationExitResult.CANCELLED
        except Exception as error:
            self._log_error(f"application exit negotiation failed: {error}")
            self._reset_after_cancellation()
            return ApplicationExitResult.FAILED

        self.phase = ApplicationExitPhase.CLEANING
        errors = list(workspace_result.cleanup_errors)
        for message in workspace_result.cleanup_errors:
            self._log_error(message)
        for step in self._cleanup_steps:
            try:
                step.run()
            except Exception as error:
                message = f"application cleanup failed ({step.name}): {error}"
                errors.append(message)
                self._log_error(message)
        self.last_errors = tuple(errors)

        if disposition is ApplicationExitDisposition.QUIT:
            self.phase = ApplicationExitPhase.FINISHED
            self._finish_quit(1 if errors else 0)
            return ApplicationExitResult.COMPLETED

        try:
            self._replace_process()
        except Exception as error:
            message = f"application restart failed: {error}"
            self.last_errors += (message,)
            self._log_error(message)
            self.phase = ApplicationExitPhase.FINISHED
            self._finish_quit(1)
            return ApplicationExitResult.FAILED

        self.phase = ApplicationExitPhase.FINISHED
        return ApplicationExitResult.COMPLETED

    def _reset_after_cancellation(self) -> None:
        self.phase = ApplicationExitPhase.IDLE
        self.disposition = None


class DefaultTemplateUnreadable(RuntimeError):
    """The configured template cannot be interpreted at all."""


class ApplicationFrameLifecycle:
    """Coordinate zero-frame survival without owning workspace resources."""

    def __init__(
        self,
        *,
        has_independent_handle: Callable[[], bool],
        frame_count: Callable[[], int],
        request_quit: Callable[[], None],
        create_configured_frame: Callable[[], None],
        create_factory_frame: Callable[[], None],
        log_error: Callable[[str], None],
        fatal_exit: Callable[[int, str], None],
    ):
        self._has_independent_handle = has_independent_handle
        self._frame_count = frame_count
        self._request_quit = request_quit
        self._create_configured_frame = create_configured_frame
        self._create_factory_frame = create_factory_frame
        self._log_error = log_error
        self._fatal_exit = fatal_exit
        self._creating = False
        self._pending_activation = False

    @property
    def creating_default_frame(self) -> bool:
        return self._creating

    @property
    def has_pending_activation(self) -> bool:
        return self._pending_activation

    def zero_frames_reached(self) -> ZeroFrameResult:
        if self._frame_count():
            return ZeroFrameResult.FRAME_EXISTS
        if self._has_independent_handle():
            return ZeroFrameResult.SURVIVING
        self._request_quit()
        return ZeroFrameResult.QUIT_REQUESTED

    def application_activated(self) -> ZeroFrameResult:
        if self._frame_count():
            return ZeroFrameResult.FRAME_EXISTS
        return self.initialize_default_frame()

    def initialize_default_frame(self) -> ZeroFrameResult:
        """Compose the default layout, including from temporary startup frames."""

        if self._creating:
            self._pending_activation = True
            return ZeroFrameResult.COALESCED

        self._creating = True
        try:
            try:
                self._create_configured_frame()
            except DefaultTemplateUnreadable as error:
                self._log_error(f"configured default frame failed: {error}")
                self._create_factory_frame()
            except Exception as error:
                self._log_error(f"configured default frame failed: {error}")
                self._create_factory_frame()
            else:
                if not self._frame_count():
                    self._log_error(
                        "configured default frame did not construct any pane"
                    )
                    self._create_factory_frame()

            if not self._frame_count():
                message = "factory default could not construct any pane"
                self._log_error(message)
                self._fatal_exit(1, message)
                return ZeroFrameResult.FATAL
            return ZeroFrameResult.FRAME_CREATED
        except Exception as error:
            message = f"factory default frame failed: {error}"
            self._log_error(message)
            self._fatal_exit(1, message)
            return ZeroFrameResult.FATAL
        finally:
            self._creating = False
            self._pending_activation = False
