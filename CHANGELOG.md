# Changelog

All notable changes documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.6.0] - 2026-11-24

### Added
- Filename collision handling: an existing `date + title` note is kept, the new one
  becomes `... (2).md`, `(3)`, ...
- Single-instance lock (`INBOX_PATH/.enricher.lock`, `flock`): a second `run`/`--once`
  exits with a clear error instead of racing the first one
- Docker `HEALTHCHECK` (inbox mount exists and is writable)
- CI matrix: Python 3.11–3.14 on Ubuntu + macOS

### Changed
- Runtime deps split into `requirements.txt`; `pytest`/`ruff` moved to
  `requirements-dev.txt` (`make install` still installs dev deps)
- Docker image installs runtime deps only and copies just `src/`, `bin/`, `requirements.txt`

## [0.5.1] - 2026-11-24

### Fixed
- Obsidian REST writes now honor `OUTPUT_PATH` (vault-relative, URL-encoded) instead of
  always writing to the vault root; falls back to direct write if `OUTPUT_PATH` is
  outside `VAULT_PATH`
- Ollama timeouts and HTTP 5xx now enter the retry queue; HTTP 4xx stays permanent
  (note written without enrichment) to avoid burning retry attempts on a bad model name
- `_write_via_rest()` returns the real output path instead of a bare filename

### Changed
- `requirements.txt` pinned to the exact versions covered by CI

## [0.5.0] - 2026-11-24

### Added
- `--once` / `make once`: process inbox and retry queue once, then exit (cron/timer use)
- Real pipeline tests exercising `run()`, `process_once()`, `_retry_pass()`, `_retry_worker()` and the CLI
- `ruff.toml` lint baseline — `make lint` stable across Ruff releases
- CLI `--help` works without a configured `.env`

### Fixed
- Empty `systemd/whisper-ollama-enricher.service` — Linux install now produces a working unit
- Empty `docker/.env.example` — Docker quick start is usable again (vault-only mount documented)
- launchd plist name now matches the Makefile (`launchd/whisper-ollama-enricher.plist`);
  `__CONFIG_DIR__` is substituted during install; `RunAtLoad` enabled
- Startup scan snapshots `.retry/` before processing the inbox — one outage no longer
  consumes two retry attempts in a single scan
- Added `LICENSE` (MIT), `.dockerignore`; `.gitignore` covers logs, `.DS_Store`, IDE folders
- Docs synced: README status/Docker/one-shot, `docs/MACOS.md` (no manual placeholder step),
  `AGENTS.md`/`CONTEXT.md` refreshed

## [0.4.0] - 2026-04-08

### Added
- Startup scan on service init: processes `.md` files already in `INBOX_PATH`
  and `.retry/` that arrived while the service was offline
- `RETRY_MAX_ATTEMPTS` — moves files to `.failed/` after N failed attempts (default: 5)
- End-to-end integration test for full pipeline

### Fixed
- `ARCHITECTURE.md`: corrected Ollama failure mode — file moves to `.retry/`,
  note without enrichment is NOT written
- `docker/.env.example`: typo `0inbox` → `0_inbox`, added missing env vars
- `src/writer.py`: removed unnecessary `verify=False` in Obsidian REST client
- Retry counter sidecar stored in `.retry/` by filename, survives file moves

## [0.3.0] - 2026-03-15

### Added
- Retry queue: files are moved to `.retry/` when Ollama is unreachable,
  reprocessed automatically every 30 seconds (configurable via `RETRY_INTERVAL`)
- Custom system prompt via `OLLAMA_SYSTEM_PROMPT` env var —
  accepts file path or inline string

### Changed
- `OllamaUnavailableError` now raised explicitly on ConnectError
  instead of silently returning `None`

### Fixed
- Docker section in README: added CURRENT_UID/GID documentation
- README: removed speculative Nextcloud/WebDAV from architecture diagram
- Added System Requirements table and minimum viable setup note


## [0.2.0] - 2026-03-15

### Added
- macOS support via launchd (`launchd/whisper-ollama-enricher.plist`)
- `make install/start/stop/restart/status/logs` auto-detect OS (Linux/macOS)
- CI matrix: ubuntu-22.04 + macos-latest
- `docs/MACOS.md` — launchd setup, known limitations, troubleshooting
- Docker tested end-to-end with vault mount and Ollama on host

### Fixed
- CI: use `macos-latest` instead of deprecated `macos-13-us-default`

## [0.1.0] - 2026-03-14

### Added
- Pipes & Filters pipeline: watcher → enricher → writer
- `src/models.py` — Pydantic contracts: WhisperOutput, OllamaEnrichment, NoteContext
- `src/config.py` — fail-fast env config, CONFIG_DIR export
- `src/watcher.py` — watchdog observer, JSON filter, double-processing guard, source file cleanup
- `src/enricher.py` — Ollama /api/generate call, graceful fallback when unavailable
- `src/writer.py` — template engine, Obsidian REST API write, direct file fallback
- Default note template baked into code, overridable via ~/.config/.../note_template.md
- `docs/TEMPLATES.md` — placeholder reference, 4 ready-made templates
- `docs/ARCHITECTURE.md` — design decisions and failure mode map
- systemd user service
- docker-compose with CURRENT_UID/GID
- GitHub Actions CI
- 13 tests passing
