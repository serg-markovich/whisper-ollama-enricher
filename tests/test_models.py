from datetime import datetime, timezone
from src.models import WhisperOutput, NoteContext


def _make(duration_sec=125.0) -> NoteContext:
    return NoteContext(whisper=WhisperOutput(
        source_file="voice-2026-03-14.m4a",
        transcript="Test",
        language="ru",
        duration_sec=duration_sec,
        whisper_model="small",
        processed_at=datetime(2026, 3, 14, 14, 5, 0, tzinfo=timezone.utc),
    ))


def test_duration_formatted():
    assert _make(125.0).duration_formatted == "2m05s"


def test_duration_zero_seconds():
    assert _make(120.0).duration_formatted == "2m00s"


def test_date_str():
    assert _make().date_str == "2026-03-14"


def test_date_time_str():
    assert _make().date_time_str == "2026-03-14 14:05"


def test_date_compact():
    assert _make().date_compact == "202603141405"
