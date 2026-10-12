"""Optional filesystem affordances available to the current account."""

import os


def create_optional_symlink(alias, target):
    """Return False only when Windows denies symlink creation privilege.

    Other filesystem errors remain failures; no system setting is changed.
    """
    try:
        alias.symlink_to(target)
    except OSError as error:
        if os.name == "nt" and getattr(error, "winerror", None) == 1314:
            return False
        raise
    return True
