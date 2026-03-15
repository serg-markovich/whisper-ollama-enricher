from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

CONFIG_DIR = Path.home() / ".config" / "whisper-ollama-enricher"
_ENV_FILE = CONFIG_DIR / ".env"
load_dotenv(_ENV_FILE)


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise SystemExit(
            f"\n[whisper-ollama-enricher] FATAL: '{key}' is not set.\n"
            f"  Fix: edit {_ENV_FILE} and add {key}=<value>\n"
            f"  Example: cp .env.example {_ENV_FILE}\n"
        )
    return val


# ── Required ────────────────────────────────────────────────────────────────
INBOX_PATH = Path(_require("INBOX_PATH"))
VAULT_PATH  = Path(_require("VAULT_PATH"))

# ── Optional with defaults ───────────────────────────────────────────────────
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH") or str(VAULT_PATH / "1_enriched"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_TIMEOUT  = int(os.getenv("OLLAMA_TIMEOUT", "60"))
RETRY_INTERVAL: int = int(os.getenv("RETRY_INTERVAL", "30"))
OLLAMA_SYSTEM_PROMPT: str = os.getenv("OLLAMA_SYSTEM_PROMPT", "")

OBSIDIAN_REST_URL = os.getenv("OBSIDIAN_REST_URL", "http://127.0.0.1:27124")
OBSIDIAN_API_KEY  = os.getenv("OBSIDIAN_API_KEY", "")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
