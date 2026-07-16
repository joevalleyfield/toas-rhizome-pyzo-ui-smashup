"""Application lifetime policy above peer-frame and pane topology."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum


class ZeroFrameResult(str, Enum):
    SURVIVING = "surviving"
    QUIT_REQUESTED = "quit-requested"
    FRAME_EXISTS = "frame-exists"
    FRAME_CREATED = "frame-created"
    COALESCED = "coalesced"
    FATAL = "fatal"


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
