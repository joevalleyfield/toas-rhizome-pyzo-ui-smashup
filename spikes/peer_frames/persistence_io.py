"""Platform-specific barriers used by the generation stores."""

import os
from pathlib import Path


def fsync_directory(path: Path) -> None:
    """Flush directory entries where the OS exposes a directory fsync.

    Windows' CRT cannot open directories for os.fsync. Records and manifests
    are still individually fsynced before same-volume os.replace publication;
    Windows does not get the POSIX directory-entry power-loss guarantee.
    File flush and publication errors must still fail the transaction.
    """
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
