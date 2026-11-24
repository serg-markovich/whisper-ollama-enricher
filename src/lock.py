from __future__ import annotations
import fcntl
import logging
import os
from pathlib import Path
from typing import IO

log = logging.getLogger(__name__)

LOCK_NAME = ".enricher.lock"


class AlreadyRunningError(RuntimeError):
    """Raised when another process already holds the instance lock."""


def acquire_lock(inbox: Path) -> IO[str]:
    """Take an exclusive, non-blocking lock inside the inbox.

    The returned handle must stay open for the process lifetime; closing it
    releases the lock. `flock` is released automatically on process exit.
    """
    path = inbox / LOCK_NAME
    fh = path.open("w", encoding="utf-8")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fh.close()
        raise AlreadyRunningError(f"another instance is running (lock: {path})")
    fh.write(str(os.getpid()))
    fh.flush()
    return fh
