"""Bounded launcher for test-owned real-Qt smoke processes."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from collections.abc import Sequence


def _terminate_owned_group(process: subprocess.Popen[str]) -> None:
    """Terminate only the process group created for this harness invocation."""

    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        process.wait(timeout=1.0)


def run_bounded(command: Sequence[str], deadline: float) -> int:
    """Run a test-owned command and fail if its external deadline is exceeded."""

    if not command:
        raise ValueError("a command is required")
    process = subprocess.Popen(
        list(command),
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        output, _ = process.communicate(timeout=deadline)
    except subprocess.TimeoutExpired as error:
        _terminate_owned_group(process)
        output = error.output or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        if output:
            print(output, end="")
        print(
            f"EXTERNAL_DEADLINE_FAILURE after {deadline:.3f}s",
            file=sys.stderr,
        )
        return 124
    if output:
        print(output, end="")
    return int(process.returncode or 0)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deadline", type=float, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    options = parser.parse_args(argv)
    command = list(options.command)
    if command[:1] == ["--"]:
        command.pop(0)
    return run_bounded(command, options.deadline)


if __name__ == "__main__":
    raise SystemExit(main())
