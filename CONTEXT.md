# CONTEXT.md

## Project Map
```
.
├── bin/run.py            Entrypoint: `--once` / watcher mode, then src.watcher
├── src/                  Pipeline: config, models, lock, watcher, enricher, writer
├── tests/                41 pytest tests (pipeline, lock, writer/enricher units)
├── docs/                 ARCHITECTURE.md, MACOS.md, TEMPLATES.md
├── docker/               Dockerfile (runtime deps + healthcheck), compose, .env.example
├── systemd/              user unit; Makefile substitutes __VENV__/__PROJECT_DIR__
├── launchd/              whisper-ollama-enricher.plist; installed with placeholders resolved
├── .github/workflows/    CI: ruff + pytest, Python 3.11–3.14 × Ubuntu/macOS
├── Makefile              install/start/once/stop/status/logs/test/lint/docker targets
├── requirements.txt      Runtime deps only, exact pins
├── requirements-dev.txt  Runtime + pytest/ruff (used by `make install` and CI)
├── ruff.toml             Lint baseline (E4/E7/E9/F), stable across Ruff releases
├── .env.example          Config template (all values blank/default)
└── CHANGELOG.md, README.md, LICENSE (MIT)
```

## Entrypoints & Data Flow
- `bin/run.py` parses `--once`, inserts repo root on `sys.path`, imports `src.config` (loads `~/.config/whisper-ollama-enricher/.env`), takes the instance lock, then calls `src.watcher.process_once()` or `run()`.
- Lock: `src.lock.acquire_lock(INBOX_PATH)` creates `INBOX_PATH/.enricher.lock` with `flock(LOCK_EX|LOCK_NB)`; a second process exits with `FATAL: another instance is running`.
- `run()`/`process_once()` share `_startup_scan()`: validates `INBOX_PATH` exists → scans `INBOX_PATH/*.md` → drains `.retry/*.md`; `run()` then starts `_retry_worker` thread + `watchdog` observer (`recursive=False`).
- `_process()`: wait for stable size → require text starting `{` → `WhisperOutput.model_validate_json` → `NoteContext` → `enrich()`.
- `enrich()`: `POST {OLLAMA_BASE_URL}/api/generate` with JSON prompt, `format=json` → `OllamaEnrichment`. Transport errors/timeouts/HTTP 5xx → `OllamaUnavailableError` (`.retry/`); HTTP 4xx and invalid payloads → `None` (note written unenriched, not retried).
- `write_note()`: `_render()` (built-in template or `CONFIG_DIR/note_template.md`) → unique filename (`... (2).md` on collision) → REST `PUT {OBSIDIAN_REST_URL}/vault/{OUTPUT_PATH-relative, URL-encoded}` if `OBSIDIAN_API_KEY` set and `OUTPUT_PATH` is inside `VAULT_PATH`; otherwise direct write to `OUTPUT_PATH`. Source `.md` unlinked only on success.

## External Dependencies
- Ollama HTTP API (`OLLAMA_BASE_URL`, default `http://localhost:11434`).
- Obsidian Local REST API (optional; `OBSIDIAN_REST_URL`, `OBSIDIAN_API_KEY`).
- Input producer: `local-whisper-obsidian` JSON files.
- Env vars read by `src/config.py`: `INBOX_PATH`, `VAULT_PATH`, `OUTPUT_PATH`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`, `RETRY_INTERVAL`, `RETRY_MAX_ATTEMPTS`, `OLLAMA_SYSTEM_PROMPT`, `OBSIDIAN_REST_URL`, `OBSIDIAN_API_KEY`, `LOG_LEVEL`.
- Docker-only vars (compose): `VAULT_PATH`, `CURRENT_UID`, `CURRENT_GID`; template in `docker/.env.example` (vault mounted at `/vault`, inbox must live inside it).
- No database, no cloud services, no auth beyond optional Obsidian bearer token.

## Tech Debt & Risks
- HTTP 4xx and invalid JSON produce an unenriched note by design; no alerting when this happens.
- Legacy tests in `test_v030.py` still re-implement retry/startup logic; real coverage lives in `tests/test_pipeline.py`.
- No live integration test against a real Ollama or Obsidian REST API (all HTTP is mocked).
- Docker healthcheck only probes the vault mount (existence + writability), not Ollama connectivity.
- `flock` lock is advisory and per-host; two containers sharing a vault are protected only via the shared inbox lock.
- Release creation is manual (`gh release create`); no tag-driven workflow.
- Version exists only in CHANGELOG/git tags; no version constant in code.
- `systemd-analyze verify` / `docker compose config` are not exercised in CI — validated manually.
- Collision suffix is check-then-write (not atomic); safe only because the instance lock serializes writes.

## Revival Effort Estimate
`Low` — `make install && make start` produces a working unit on Linux and macOS; manual run needs Python 3.11+, a venv and two env vars, with Ollama as the only external service. Remaining work is hardening (live integration tests, release automation).
