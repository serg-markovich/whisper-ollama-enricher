# Changelog

All notable changes documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Planned
- macOS support via launchd (replaces systemd in Makefile)
- `make logs` via `log stream` on macOS
- CI matrix: ubuntu-22.04 + macos-13

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
