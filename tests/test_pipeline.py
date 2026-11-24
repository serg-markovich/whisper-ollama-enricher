from __future__ import annotations
import json
import os
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

SAMPLE_WHISPER = {
    "transcript": "Need to call John tomorrow about the project.",
    "language": "en",
    "source_file": "test_note.m4a",
    "whisper_model": "small",
    "duration_sec": 5.0,
    "processed_at": "2026-03-15T10:00:00+00:00",
}


@pytest.fixture()
def inbox(tmp_path):
    d = tmp_path / "inbox"
    d.mkdir()
    return d


@pytest.fixture()
def retry_path(inbox):
    return inbox / ".retry"


def _whisper_file(directory: Path, name: str = "2026-03-15 test_note.md") -> Path:
    f = directory / name
    f.write_text(json.dumps(SAMPLE_WHISPER), encoding="utf-8")
    return f


def _patched(inbox, retry_path, written, **extra):
    """Common pipeline patches; written collects NoteContext objects."""
    patches = {
        "src.watcher.INBOX_PATH": inbox,
        "src.watcher.RETRY_PATH": retry_path,
        "src.watcher.enrich": MagicMock(return_value=None),
        "src.watcher.write_note": MagicMock(
            side_effect=lambda ctx: written.append(ctx) or inbox / "out.md"
        ),
    }
    patches.update(extra)
    return patches


def _run_with(inbox, retry_path, written, **extra):
    from src.watcher import run

    observer = MagicMock()
    observer.is_alive.return_value = False
    patches = _patched(
        inbox,
        retry_path,
        written,
        **{
            "src.watcher.Observer": MagicMock(return_value=observer),
            "src.watcher.threading.Thread": MagicMock(),
            **extra,
        },
    )
    with ExitStack() as stack:
        for target, value in patches.items():
            stack.enter_context(patch(target, value))
        run()
    return observer


def test_run_processes_existing_files_at_startup(inbox, retry_path):
    source = _whisper_file(inbox)
    written = []

    _run_with(inbox, retry_path, written)

    assert len(written) == 1
    assert not source.exists(), "processed source must be deleted"


def test_run_drains_retry_queue_at_startup(inbox, retry_path):
    retry_path.mkdir()
    queued = _whisper_file(retry_path)
    written = []

    _run_with(inbox, retry_path, written)

    assert len(written) == 1
    assert not queued.exists(), "retry file must be consumed"


def test_run_fails_when_inbox_missing(tmp_path, retry_path):
    from src.watcher import run

    missing = tmp_path / "missing"
    with (
        patch("src.watcher.INBOX_PATH", missing),
        patch("src.watcher.RETRY_PATH", retry_path),
        pytest.raises(SystemExit, match="INBOX_PATH does not exist"),
    ):
        run()


def test_process_once_processes_inbox_and_retry(inbox, retry_path):
    retry_path.mkdir()
    _whisper_file(inbox, "inbox_note.md")
    _whisper_file(retry_path, "retry_note.md")
    written = []

    from src.watcher import process_once

    with ExitStack() as stack:
        for target, value in _patched(inbox, retry_path, written).items():
            stack.enter_context(patch(target, value))
        process_once()

    assert len(written) == 2
    assert not list(inbox.glob("*.md"))
    assert not list(retry_path.glob("*.md"))


def test_startup_scan_does_not_retry_file_queued_in_same_scan(inbox, retry_path):
    """One outage must consume ONE retry attempt, not two."""
    from src.enricher import OllamaUnavailableError
    from src.watcher import process_once

    _whisper_file(inbox, "outage_note.md")
    patches = _patched(
        inbox,
        retry_path,
        [],
        **{
            "src.watcher.enrich": MagicMock(
                side_effect=OllamaUnavailableError("Ollama down")
            ),
            "src.watcher.RETRY_MAX_ATTEMPTS": 2,
        },
    )
    with ExitStack() as stack:
        for target, value in patches.items():
            stack.enter_context(patch(target, value))
        process_once()

    assert (retry_path / "outage_note.md").exists()
    assert (retry_path / "outage_note.md.count").read_text() == "1"
    assert not (inbox / ".failed").exists()


def test_retry_pass_moves_and_processes_queued_file(inbox, retry_path):
    retry_path.mkdir()
    queued = _whisper_file(retry_path)

    from src.watcher import _retry_pass

    with (
        patch("src.watcher.INBOX_PATH", inbox),
        patch("src.watcher.RETRY_PATH", retry_path),
        patch("src.watcher._process") as mock_process,
    ):
        _retry_pass()

    assert not queued.exists()
    mock_process.assert_called_once_with(inbox / queued.name)


def test_retry_worker_runs_retry_pass_each_interval(inbox, retry_path):
    from src.watcher import _retry_worker

    with (
        patch("src.watcher.RETRY_PATH", retry_path),
        patch("src.watcher.INBOX_PATH", inbox),
        patch("src.watcher._retry_pass") as mock_pass,
        patch("src.watcher.time.sleep", side_effect=[None, KeyboardInterrupt]),
        pytest.raises(KeyboardInterrupt),
    ):
        _retry_worker()

    mock_pass.assert_called_once()


def test_cli_help_works_without_config():
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run.py"), "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env={k: v for k, v in os.environ.items() if k not in ("INBOX_PATH", "VAULT_PATH")},
    )

    assert proc.returncode == 0, proc.stderr
    assert "--once" in proc.stdout


def test_cli_once_processes_and_exits(inbox, tmp_path):
    _whisper_file(inbox, "cli_note.md")
    env = {
        **{k: v for k, v in os.environ.items() if "proxy" not in k.lower()},
        "INBOX_PATH": str(inbox),
        "VAULT_PATH": str(tmp_path / "vault"),
        "OUTPUT_PATH": str(tmp_path / "out"),
        "OLLAMA_BASE_URL": "http://127.0.0.1:1",  # refuse promptly
        "OLLAMA_TIMEOUT": "1",
        "RETRY_MAX_ATTEMPTS": "2",
        "NO_PROXY": "*",
    }
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "bin" / "run.py"), "--once"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=90,
    )

    assert proc.returncode == 0, proc.stderr
    assert not list(inbox.glob("*.md")), "source processed or queued"
    assert list((inbox / ".retry").glob("*.md")), "Ollama down → file queued for retry"
