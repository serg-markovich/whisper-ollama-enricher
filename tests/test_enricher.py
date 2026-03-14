from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import httpx

from src.models import WhisperOutput
from src.enricher import enrich


def _whisper():
    return WhisperOutput(
        source_file="test.m4a",
        transcript="Купить молоко. Позвонить врачу.",
        language="ru",
        duration_sec=30.0,
        whisper_model="small",
        processed_at=datetime(2026, 3, 14, tzinfo=timezone.utc),
    )


def test_returns_none_when_ollama_unavailable():
    with patch("src.enricher.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.side_effect = (
            httpx.ConnectError("refused")
        )
        assert enrich(_whisper()) is None


def test_returns_none_on_bad_json():
    with patch("src.enricher.httpx.Client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "not valid json {{"}
        mock_client.return_value.__enter__.return_value.post.return_value = mock_resp
        assert enrich(_whisper()) is None
