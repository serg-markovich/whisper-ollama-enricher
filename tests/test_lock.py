from __future__ import annotations
import os

import pytest

from src.lock import LOCK_NAME, AlreadyRunningError, acquire_lock


def test_second_instance_is_rejected(tmp_path):
    first = acquire_lock(tmp_path)
    try:
        with pytest.raises(AlreadyRunningError):
            acquire_lock(tmp_path)
    finally:
        first.close()


def test_lock_is_released_on_close(tmp_path):
    acquire_lock(tmp_path).close()

    second = acquire_lock(tmp_path)
    second.close()


def test_lock_file_contains_pid(tmp_path):
    lock = acquire_lock(tmp_path)
    try:
        assert (tmp_path / LOCK_NAME).read_text(encoding="utf-8") == str(os.getpid())
    finally:
        lock.close()
