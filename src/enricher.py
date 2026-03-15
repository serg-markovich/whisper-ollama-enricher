from __future__ import annotations
import json
import logging
from pathlib import Path
import httpx

from .config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_SYSTEM_PROMPT
from .models import WhisperOutput, OllamaEnrichment

log = logging.getLogger(__name__)


class OllamaUnavailableError(Exception):
    """Raised when Ollama is unreachable — triggers retry queue."""


_DEFAULT_SYSTEM_PROMPT = """You are a note enrichment assistant for personal voice memos.
Given a voice transcript, return ONLY valid JSON with exactly these fields:

{
  "title": "short descriptive title in the SAME language as the transcript (max 8 words)",
  "summary": "one sentence summary in the SAME language as the transcript",
  "tags": ["english", "lowercase", "tags", "3 to 5 items"],
  "action_items": ["action item 1", "action item 2"]
}

Rules:
- title and summary: always in the same language as the transcript
- tags: always in English, lowercase, no spaces (use hyphens)
- action_items: extract only explicit tasks/todos, empty array if none
- Respond ONLY with JSON, no explanation, no markdown fences"""


def _load_system_prompt() -> str:
    if not OLLAMA_SYSTEM_PROMPT:
        return _DEFAULT_SYSTEM_PROMPT
    p = Path(OLLAMA_SYSTEM_PROMPT)
    if p.exists():
        log.debug("Using system prompt from file: %s", p)
        return p.read_text(encoding="utf-8").strip()
    # treat as inline string
    return OLLAMA_SYSTEM_PROMPT


def enrich(whisper: WhisperOutput) -> OllamaEnrichment | None:
    prompt = f"Language: {whisper.language}\n\nTranscript:\n{whisper.transcript}"
    try:
        with httpx.Client(timeout=OLLAMA_TIMEOUT) as client:
            r = client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "system": _load_system_prompt(),
                    "stream": False,
                    "format": "json",
                },
            )
            r.raise_for_status()
        return OllamaEnrichment(**json.loads(r.json()["response"]))
    except httpx.ConnectError:
        raise OllamaUnavailableError(f"Ollama unreachable at {OLLAMA_BASE_URL}")
    except Exception as exc:
        log.warning("Enrichment failed: %s — writing note without enrichment", exc)
        return None
