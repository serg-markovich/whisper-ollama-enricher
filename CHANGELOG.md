# Changelog

All notable changes documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Planned
- Retry queue for failed enrichments
- Prompt editor via .env (v0.3.0)
- Multi-inbox support with per-inbox templates (v0.3.0)

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
