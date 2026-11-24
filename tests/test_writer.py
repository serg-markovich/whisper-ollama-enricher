from datetime import datetime, timezone
from unittest.mock import patch

from src.models import WhisperOutput, OllamaEnrichment, NoteContext
from src.writer import _render, _filename, _rest_relpath, _write_via_rest, write_note


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


def test_rest_relpath_uses_output_path_inside_vault(tmp_path):
    vault = tmp_path / "vault"
    out = vault / "1_enriched"
    with patch("src.writer.VAULT_PATH", vault), patch("src.writer.OUTPUT_PATH", out):
        assert _rest_relpath("2026-03-14 note.md") == "1_enriched/2026-03-14%20note.md"


def test_rest_relpath_none_when_output_outside_vault(tmp_path):
    with (
        patch("src.writer.VAULT_PATH", tmp_path / "vault"),
        patch("src.writer.OUTPUT_PATH", tmp_path / "elsewhere"),
    ):
        assert _rest_relpath("note.md") is None


def test_write_via_rest_targets_output_path_and_encodes_url(tmp_path):
    vault = tmp_path / "vault"
    out = vault / "1_enriched"
    with (
        patch("src.writer.VAULT_PATH", vault),
        patch("src.writer.OUTPUT_PATH", out),
        patch("src.writer.OBSIDIAN_API_KEY", "test-key"),
        patch("src.writer.OBSIDIAN_REST_URL", "http://127.0.0.1:27124"),
        patch("src.writer.httpx.Client") as mock_client,
    ):
        dest = _write_via_rest("2026-03-14 note.md", "body")

    url = mock_client.return_value.__enter__.return_value.put.call_args.args[0]
    assert url == "http://127.0.0.1:27124/vault/1_enriched/2026-03-14%20note.md"
    assert dest == out / "2026-03-14 note.md"


def test_write_note_falls_back_when_output_outside_vault(tmp_path):
    out = tmp_path / "outside"
    with (
        patch("src.writer.VAULT_PATH", tmp_path / "vault"),
        patch("src.writer.OUTPUT_PATH", out),
        patch("src.writer.OBSIDIAN_API_KEY", "test-key"),
    ):
        dest = write_note(_ctx())

    assert dest == out / _filename(_ctx())
    assert dest.exists()
