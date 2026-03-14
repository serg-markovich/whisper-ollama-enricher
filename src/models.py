from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class WhisperOutput(BaseModel):
    """JSON contract produced by local-whisper-obsidian."""
    source_file: str
    transcript: str
    language: str
    duration_sec: float
    whisper_model: str
    processed_at: datetime


class OllamaEnrichment(BaseModel):
    """Structured payload returned by the Ollama enrichment call."""
    title: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)


class NoteContext(BaseModel):
    """Internal pipeline object passed between filters."""
    whisper: WhisperOutput
    enrichment: Optional[OllamaEnrichment] = None
    source_md_path: str = ""

    @property
    def duration_formatted(self) -> str:
        total = int(self.whisper.duration_sec)
        return f"{total // 60}m{total % 60:02d}s"

    @property
    def date_str(self) -> str:
        return self.whisper.processed_at.strftime("%Y-%m-%d")

    @property
    def date_time_str(self) -> str:
        return self.whisper.processed_at.strftime("%Y-%m-%d %H:%M")

    @property
    def date_compact(self) -> str:
        return self.whisper.processed_at.strftime("%Y%m%d%H%M")
