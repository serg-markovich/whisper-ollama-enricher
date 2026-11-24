from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import pytest
import httpx

from src.models import WhisperOutput
from src.enricher import enrich, OllamaUnavailableError


def _whisper():
    return WhisperOutput(
        source_file="test.m4a",
        transcript="Купить молоко. Позвонить врачу.",
        language="ru",
        duration_sec=30.0,
        whisper_model="small",
        processed_at=datetime(2026, 3, 14, tzinfo=timezone.utc),
    )


def test_raises_when_ollama_unavailable():
    with patch("src.enricher.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.side_effect = (
            httpx.ConnectError("refused")
        )
        with pytest.raises(OllamaUnavailableError):
            enrich(_whisper())


def test_returns_none_on_bad_json():
    with patch("src.enricher.httpx.Client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "not valid json {{"}
        mock_client.return_value.__enter__.return_value.post.return_value = mock_resp
        assert enrich(_whisper()) is None


def _status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "http://localhost:11434/api/generate")
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError(f"HTTP {status}", request=request, response=response)


def test_raises_when_ollama_times_out():
    with patch("src.enricher.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.side_effect = (
            httpx.ReadTimeout("timed out")
        )
        with pytest.raises(OllamaUnavailableError):
            enrich(_whisper())


def test_raises_on_server_error():
    with patch("src.enricher.httpx.Client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = _status_error(503)
        mock_client.return_value.__enter__.return_value.post.return_value = mock_resp
        with pytest.raises(OllamaUnavailableError):
            enrich(_whisper())


def test_returns_none_on_client_error():
    """4xx is permanent (e.g. unknown model) — retrying cannot help."""
    with patch("src.enricher.httpx.Client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = _status_error(404)
        mock_client.return_value.__enter__.return_value.post.return_value = mock_resp
        assert enrich(_whisper()) is None
