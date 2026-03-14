from datetime import datetime, timezone
from unittest.mock import patch

from src.models import WhisperOutput, OllamaEnrichment, NoteContext
from src.writer import _render, _filename


def _ctx() -> NoteContext:
    return NoteContext(
        whisper=WhisperOutput(
            source_file="диктофон-1.m4a",
            transcript="Купить молоко и позвонить врачу.",
            language="ru",
            duration_sec=30.0,
            whisper_model="small",
            processed_at=datetime(2026, 3, 14, 14, 5, 0, tzinfo=timezone.utc),
        ),
        enrichment=OllamaEnrichment(
            title="Купить молоко и позвонить врачу",
            summary="Голосовая заметка с двумя задачами.",
            tags=["shopping", "health", "tasks"],
            action_items=["Купить молоко", "Позвонить врачу"],
        )
    )


def test_render_contains_title():
    assert "Купить молоко" in _render(_ctx())


def test_render_contains_tags():
    rendered = _render(_ctx())
    assert "- shopping" in rendered


def test_render_action_items():
    rendered = _render(_ctx())
    assert "- [ ] Купить молоко" in rendered


def test_filename_has_date():
    assert _filename(_ctx()).startswith("2026-03-14")


def test_render_uses_custom_template(tmp_path):
    custom = tmp_path / "note_template.md"
    custom.write_text("TITLE={title}\nLANG={language}")
    with patch("src.writer.CONFIG_DIR", tmp_path):
        result = _render(_ctx())
    assert result.startswith("TITLE=Купить молоко")
    assert "LANG=ru" in result
