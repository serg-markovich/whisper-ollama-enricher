# AGENTS.md

## Tech Stack
- Python 3.11 (CI target; local interpreter may differ). No packaging metadata (`pyproject.toml` absent).
- Runtime deps: `httpx`, `pydantic>=2.5`, `python-dotenv`, `watchdog`. Dev: `pytest`, `ruff` (same `requirements.txt`).
- Plain modules: `src/*.py` pipeline + `bin/run.py` entrypoint; no framework, no async, no DB.

## Commands
- Install: `make install` → venv at `~/.local/share/whisper-ollama-enricher/venv`, copies `.env.example` to `~/.config/whisper-ollama-enricher/.env`, installs systemd/launchd unit.
- Run: `~/.local/share/whisper-ollama-enricher/venv/bin/python bin/run.py` (needs `INBOX_PATH`, `VAULT_PATH`); `--once` = single scan without watcher (`make once`).
- Test: `make test` (= `<venv>/bin/pytest tests/ -v`); CI sets `INBOX_PATH=/tmp/inbox VAULT_PATH=/tmp/vault`.
- Lint: `make lint` (= `<venv>/bin/ruff check src/ tests/`); rule baseline in `ruff.toml`.
- Docker: `make docker-build`, `make docker-up`, `make docker-logs` (`docker/.env` from `.env.example`).

## Architecture & Boundaries
- `src/config.py` — all env parsing at import time; `_require()` exits on missing required vars; exports `CONFIG_DIR`.
- `src/models.py` — Pydantic contracts: `WhisperOutput` (inbox JSON), `OllamaEnrichment` (LLM output), `NoteContext` (derived date/duration props).
- `src/watcher.py` — watchdog observer, filtering, retry/failed queue, orchestration; owns all file moves/deletes.
- `src/enricher.py` — single Ollama `/api/generate` call; raises `OllamaUnavailableError` only on `httpx.ConnectError`.
- `src/writer.py` — template rendering, filename generation, Obsidian REST or direct write; no config/IO logic elsewhere.

## Coding Conventions & Guardrails
- Start every `src` module with `from __future__ import annotations`; use module-level `log = logging.getLogger(__name__)`.
- Config is module-level constants imported by name; code/tests patch `src.watcher.INBOX_PATH`, `src.enricher.enrich`, `src.writer.CONFIG_DIR` etc. — keep names and import locations stable.
- Errors: fail fast with `SystemExit` + actionable message for config; per-file failures log and continue (never crash the observer loop).
- Keep the source `.md` deletion strictly after `write_note()` succeeds; preserve retry semantics (`.retry/` + `.retry/*.count` sidecar, `.failed/` after max attempts).
- `run()` (watcher) and `process_once()` (`--once`) must share `_startup_scan()`; retry loop must stay in `_retry_pass()` so it is unit-testable.
- Whisper input is detected by JSON content + Pydantic validation, not filename. Do not add filename-pattern filtering.
- Do not write to the vault, inbox, or real config paths from tests; use `tmp_path` and mocks.
- Update `CHANGELOG.md` and `README.md` config table when adding env vars or targets.
