from __future__ import annotations
import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from src.enricher import OllamaUnavailableError


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
def sample_md(inbox):
    f = inbox / "2026-03-15 test_note.md"
    f.write_text(json.dumps(SAMPLE_WHISPER), encoding="utf-8")
    return f


# ── Retry queue ─────────────────────────────────────────────────────────────

def test_ollama_unavailable_moves_to_retry(inbox, sample_md):
    """When Ollama is unreachable, file moves to .retry/, not deleted."""
    retry_path = inbox / ".retry"

    with (
        patch("src.watcher.INBOX_PATH", inbox),
        patch("src.watcher.RETRY_PATH", retry_path),
        patch("src.watcher.enrich", side_effect=OllamaUnavailableError("Ollama down")),
        patch("src.watcher.write_note"),
    ):
        from src.watcher import _process
        _process(sample_md)

    assert not sample_md.exists(), "Source file should be moved, not stay in inbox"
    assert (retry_path / sample_md.name).exists(), "File should appear in .retry/"


def test_ollama_unavailable_does_not_write_note(inbox, sample_md):
    """When Ollama is unreachable, no enriched note is written."""
    retry_path = inbox / ".retry"

    with (
        patch("src.watcher.INBOX_PATH", inbox),
        patch("src.watcher.RETRY_PATH", retry_path),
        patch("src.watcher.enrich", side_effect=OllamaUnavailableError("Ollama down")),
        patch("src.watcher.write_note") as mock_write,
    ):
        from src.watcher import _process
        _process(sample_md)

    mock_write.assert_not_called()


def test_retry_worker_reprocesses_queued_file(inbox, tmp_path):
    """Files in .retry/ are moved back to inbox and processed."""
    retry_path = inbox / ".retry"
    retry_path.mkdir()

    queued = retry_path / "2026-03-15 test_note.md"
    queued.write_text(json.dumps(SAMPLE_WHISPER), encoding="utf-8")

    written = []

    def fake_process(path: Path):
        written.append(path)

    with (
        patch("src.watcher.INBOX_PATH", inbox),
        patch("src.watcher.RETRY_PATH", retry_path),
        patch("src.watcher._process", side_effect=fake_process),
    ):
        for f in retry_path.glob("*.md"):
            dest = inbox / f.name
            shutil.move(str(f), dest)
            fake_process(dest)

    assert len(written) == 1
    assert written[0].name == queued.name


# ── Custom system prompt ─────────────────────────────────────────────────────

def test_default_system_prompt_used_when_env_empty():
    """When OLLAMA_SYSTEM_PROMPT is empty, default prompt is returned."""
    with patch("src.enricher.OLLAMA_SYSTEM_PROMPT", ""):
        from src.enricher import _load_system_prompt, _DEFAULT_SYSTEM_PROMPT
        assert _load_system_prompt() == _DEFAULT_SYSTEM_PROMPT


def test_inline_system_prompt_used_when_set():
    """When OLLAMA_SYSTEM_PROMPT is a plain string, it is used as-is."""
    custom = "You are a minimal note assistant. Return JSON only."
    with patch("src.enricher.OLLAMA_SYSTEM_PROMPT", custom):
        from src.enricher import _load_system_prompt
        assert _load_system_prompt() == custom


def test_file_system_prompt_loaded(tmp_path):
    """When OLLAMA_SYSTEM_PROMPT is a file path, content is read from file."""
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("Custom prompt from file.", encoding="utf-8")

    with patch("src.enricher.OLLAMA_SYSTEM_PROMPT", str(prompt_file)):
        from src.enricher import _load_system_prompt
        assert _load_system_prompt() == "Custom prompt from file."


# ── RETRY_MAX_ATTEMPTS ───────────────────────────────────────────────────────

def test_max_retries_moves_to_failed(inbox, sample_md):
    """After RETRY_MAX_ATTEMPTS exhausted, file moves to .failed/, not .retry/."""
    retry_path = inbox / ".retry"
    failed_path = inbox / ".failed"
    retry_path.mkdir()

    with (
        patch("src.watcher.INBOX_PATH", inbox),
        patch("src.watcher.RETRY_PATH", retry_path),
        patch("src.watcher.FAILED_PATH", failed_path),
        patch("src.watcher.RETRY_MAX_ATTEMPTS", 2),
        patch("src.watcher.enrich", side_effect=OllamaUnavailableError("down")),
        patch("src.watcher.write_note"),
        patch("src.watcher._get_retry_count", return_value=1),
    ):
        from src.watcher import _process
        _process(sample_md)

    assert not sample_md.exists()
    assert (failed_path / sample_md.name).exists()
    assert not (retry_path / sample_md.name).exists()


def test_startup_scan_processes_existing_files(inbox, sample_md):
    """Files already in INBOX_PATH are processed on service start."""
    processed = []

    existing = list(inbox.glob("*.md"))
    for f in existing:
        processed.append(f)

    assert len(processed) == 1
    assert processed[0].name == sample_md.name
