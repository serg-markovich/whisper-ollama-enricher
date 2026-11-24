# CONTEXT.md

## Project Map
```
.
├── bin/run.py            Entrypoint: logging setup, then src.watcher.run()
├── src/                  Pipeline: config, models, watcher, enricher, writer
├── tests/                30 pytest tests (incl. real run/process_once/_retry_pass coverage)
├── docs/                 ARCHITECTURE.md, MACOS.md, TEMPLATES.md
├── docker/               Dockerfile, compose (host vault mounted at /vault), .env.example
├── systemd/              user unit; Makefile substitutes __VENV__/__PROJECT_DIR__
├── launchd/              whisper-ollama-enricher.plist; installed with placeholders resolved
├── .github/workflows/    CI: ruff + pytest on ubuntu-22.04, macos-latest
├── Makefile              install/start/once/stop/status/logs/test/lint/docker targets
├── requirements.txt      Runtime + dev deps, unpinned (`>=`)
├── ruff.toml             Lint baseline (E4/E7/E9/F), stable across Ruff releases
├── .env.example          Config template (all values blank/default)
└── CHANGELOG.md, README.md, LICENSE (MIT)
```

## Entrypoints & Data Flow
- `bin/run.py` parses `--once`, inserts repo root on `sys.path`, imports `src.config` (loads `~/.config/whisper-ollama-enricher/.env`), then calls `src.watcher.process_once()` or `run()`.
- `run()`/`process_once()` share `_startup_scan()`: validates `INBOX_PATH` exists → scans `INBOX_PATH/*.md` → drains `.retry/*.md`; `run()` then starts `_retry_worker` thread + `watchdog` observer (`recursive=False`).
- `_process()`: wait for stable size → require text starting `{` → `WhisperOutput.model_validate_json` → `NoteContext` → `enrich()`.
- `enrich()`: `POST {OLLAMA_BASE_URL}/api/generate` with JSON prompt, `format=json` → `OllamaEnrichment`. `ConnectError` → `.retry/`; other errors → `None` (note written unenriched).
- `write_note()`: `_render()` (built-in template or `CONFIG_DIR/note_template.md`) → REST `PUT {OBSIDIAN_REST_URL}/vault/{filename}` if `OBSIDIAN_API_KEY` set, else `OUTPUT_PATH/{date} {title}.md`; source `.md` unlinked only on success.

## External Dependencies
- Ollama HTTP API (`OLLAMA_BASE_URL`, default `http://localhost:11434`).
- Obsidian Local REST API (optional; `OBSIDIAN_REST_URL`, `OBSIDIAN_API_KEY`).
- Input producer: `local-whisper-obsidian` JSON files.
- Env vars read by `src/config.py`: `INBOX_PATH`, `VAULT_PATH`, `OUTPUT_PATH`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`, `RETRY_INTERVAL`, `RETRY_MAX_ATTEMPTS`, `OLLAMA_SYSTEM_PROMPT`, `OBSIDIAN_REST_URL`, `OBSIDIAN_API_KEY`, `LOG_LEVEL`.
- Docker-only vars (compose): `VAULT_PATH`, `CURRENT_UID`, `CURRENT_GID`; template in `docker/.env.example` (vault mounted at `/vault`, inbox must live inside it).
- No database, no cloud services, no auth beyond optional Obsidian bearer token.

## Tech Debt & Risks
- Obsidian REST path writes to `{REST}/vault/{filename}` (vault root), ignoring `OUTPUT_PATH`; direct-write and REST modes land in different folders.
- Only `httpx.ConnectError` triggers retries; timeouts/HTTP 5xx/invalid JSON silently produce unenriched notes (data-quality risk).
- Duplicate `date + title` filenames overwrite existing notes with no collision check.
- No file locking across processes; `.retry/*.count` sidecars are keyed by filename only.
- Legacy tests in `test_v030.py` still re-implement retry/startup logic; real coverage lives in `tests/test_pipeline.py`.
- Deps unpinned (`>=`), no lockfile; `pytest`/`ruff` mixed into runtime requirements; Ruff floor drift mitigated only by `ruff.toml`.
- Docker image still installs `pytest`/`ruff` and has no runtime healthcheck; `.dockerignore` now excludes `.git`/tests/docs.
- Repo was stale (last feature commit 2026-04-08); CI targets Python 3.11, local env Python 3.14 (untested combo).
- Version `0.4.0` exists only in CHANGELOG; no version constant in code.
- `systemd-analyze verify` / `docker compose config` not exercised in CI — unit and compose validated only by review `[UNKNOWN / NEEDS CHECK]`.

## Revival Effort Estimate
`Low` — `make install && make start` now produces a working unit on Linux and macOS; manual run needs Python 3.11+, a venv and two env vars, with Ollama as the only external service. Remaining work is product decisions (REST output path, retry semantics) plus dependency pinning.
