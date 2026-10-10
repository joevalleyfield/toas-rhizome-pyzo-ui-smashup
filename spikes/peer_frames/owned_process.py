"""Own probe descendants through POSIX sessions or Windows kill-on-close jobs."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from contextlib import contextmanager


class WindowsJob:
    def __init__(self):
        import ctypes
        from ctypes import wintypes

        class Limits(ctypes.Structure):
            _fields_ = [
                ("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                ("flags", wintypes.DWORD), ("min_working_set", ctypes.c_size_t),
                ("max_working_set", ctypes.c_size_t), ("active_processes", wintypes.DWORD),
                ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                ("scheduling", wintypes.DWORD),
            ]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("basic", Limits), ("io_counters", ctypes.c_uint64 * 6),
                ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t),
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        kernel.SetInformationJobObject.restype = wintypes.BOOL
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel.TerminateJobObject.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        self.kernel, self.ctypes = kernel, ctypes
        self.handle = kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def assign(self, process):
        if not self.kernel.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise self.ctypes.WinError(self.ctypes.get_last_error())

    def terminate(self):
        if self.handle and not self.kernel.TerminateJobObject(self.handle, 124):
            raise self.ctypes.WinError(self.ctypes.get_last_error())

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def terminate_owned(process):
    if getattr(process, "_owned_cleaned", False):
        return
    job = getattr(process, "_owned_job", None)
    if job:
        job.terminate()
        process.wait(timeout=5)
        process._owned_cleaned = True
        return
    signal_group(process.pid, signal.SIGTERM)
    # A leader's successful exit does not establish that its descendants exited.
    signal_group(process.pid, signal.SIGKILL)
    process.wait(timeout=5)
    process._owned_cleaned = True


def signal_group(group, requested_signal):
    try:
        os.killpg(group, requested_signal)
    except ProcessLookupError:
        return
    except PermissionError:
        # macOS returns EPERM for a group containing only orphan zombies after
        # its leader has been reaped. Suppress that case only after proving that
        # no live member remains; real signalling permission failures still fail.
        if sys.platform != "darwin":
            raise
        listing = subprocess.check_output(["ps", "-axo", "pgid=,stat="], text=True)
        alive = [row for row in listing.splitlines()
                 if len(row.split()) == 2 and row.split()[0] == str(group)
                 and not row.split()[1].startswith("Z")]
        if alive:
            raise


@contextmanager
def owned_process(command, *, cwd=None, env=None):
    command = [str(argument) for argument in command]
    job = WindowsJob() if os.name == "nt" else None
    process = None
    try:
        if job:
            # No probe/kernel can start before the parent assigns ownership.
            gate = (
                "import subprocess, sys; "
                "assert sys.stdin.readline() == 'GO\\n'; "
                "sys.exit(subprocess.call(sys.argv[1:], stdin=subprocess.DEVNULL))"
            )
            process = subprocess.Popen(
                [sys.executable, "-c", gate, *command], cwd=cwd, env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
            )
            try:
                job.assign(process)
            except Exception:
                process.kill()
                process.wait(timeout=5)
                raise
            process._owned_job = job
            process.stdin.write("GO\n")
            process.stdin.close()
            process.stdin = None
        else:
            process = subprocess.Popen(
                command, cwd=cwd, env=env, start_new_session=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
            )
        yield process
    finally:
        try:
            if process is not None:
                terminate_owned(process)
                if process.stdout:
                    process.stdout.close()
        finally:
            if job:
                job.close()
