# whisper-ollama-enricher

**Status:** `PROTOTYPE` — pipeline and deployment artifacts work and are tested; remaining gaps are live integration coverage and release automation. Watches a folder for voice transcripts, enriches them with a local Ollama model, writes structured Markdown notes into an Obsidian-compatible vault. Local-only, no cloud, no API keys required.

## Overview

- Detects whisper JSON in `.md` files by content (`local-whisper-obsidian` output), not by filename.
- Ollama produces `title`, `summary`, `tags` (English), `action_items` (transcript language).
- Renders Markdown + YAML frontmatter via Obsidian REST API or direct file write fallback.
- Unreachable Ollama → `.retry/` (retried every `RETRY_INTERVAL`s) → `.failed/` after `RETRY_MAX_ATTEMPTS`.

## Quick Start

```bash
git clone https://github.com/serg-markovich/whisper-ollama-enricher && cd whisper-ollama-enricher
make install
nano ~/.config/whisper-ollama-enricher/.env   # set INBOX_PATH, VAULT_PATH
make start && make logs
```

Manual/one-shot run (cron, timer, or debug):

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
INBOX_PATH=/path/inbox VAULT_PATH=/path/vault .venv/bin/python bin/run.py   # add --once to exit after one scan
```

Requires Python 3.11+ and Ollama locally (`gemma3:1b` minimum, `mistral` recommended).

## Configuration

File: `~/.config/whisper-ollama-enricher/.env` (see `.env.example`).

| Var | Default | Description |
|---|---|---|
| `INBOX_PATH` | — (required) | Watched folder for transcript `.md` |
| `VAULT_PATH` | — (required) | Obsidian vault root |
| `OUTPUT_PATH` | `$VAULT_PATH/1_enriched` | Direct-write output folder |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `mistral` | Enrichment model |
| `OLLAMA_TIMEOUT` | `60` | Request timeout (seconds) |
| `OLLAMA_SYSTEM_PROMPT` | empty | Custom prompt: file path or inline string |
| `RETRY_INTERVAL` | `30` | Retry scan interval (seconds) |
| `RETRY_MAX_ATTEMPTS` | `5` | Failures before moving to `.failed/` |
| `OBSIDIAN_REST_URL` | `http://127.0.0.1:27124` | Local REST API base |
| `OBSIDIAN_API_KEY` | empty | Empty = direct file write |
| `LOG_LEVEL` | `INFO` | `DEBUG`/`INFO`/`WARNING`/`ERROR` |

Ollama location: `localhost:11434` (native), `172.17.0.1:11434` (Docker host), `192.168.x.x:11434` (LAN).

## Commands

| Command | Action |
|---|---|
| `make install` | venv + systemd (Linux) / launchd (macOS) |
| `make start` / `stop` / `restart` | service control |
| `make status` / `logs` | state / live logs |
| `make once` / `test` / `lint` | one-shot scan / pytest / ruff |
| `make docker-build` / `up` / `down` / `logs` | Docker stack |

## Docker

`cp docker/.env.example docker/.env`, fill `VAULT_PATH` (host path), `CURRENT_UID`/`CURRENT_GID` (`id -u`, `id -g`), then `make docker-build && make docker-up`. Only the vault is mounted (at `/vault`), so keep `INBOX_PATH=/vault/0_inbox`; use `OLLAMA_BASE_URL=http://172.17.0.1:11434` for host Ollama. The image ships runtime deps only and has a healthcheck that verifies the vault mount is writable.

## Notes & Templates

Output is plain `.md` + YAML frontmatter — works with Obsidian, Logseq, Foam, Dendron, Zettlr, Joplin. Override the built-in template at `~/.config/whisper-ollama-enricher/note_template.md`, then `make restart`. Placeholders: `docs/TEMPLATES.md`. Architecture and failure modes: `docs/ARCHITECTURE.md`.

## Status & Roadmap

**Working**
- Startup scan of inbox and `.retry/` queue; stability polling; duplicate-processing guard.
- Ollama JSON enrichment; REST and direct writes both target `OUTPUT_PATH`; retry on transport errors/timeouts/5xx.
- Collision-safe filenames; single-instance lock; retry counter sidecars; `.failed/` quarantine.
- One-shot mode (`--once`, `make once`) for cron/systemd timers.
- systemd/Docker/launchd packaging; 41 pytest tests; CI on Python 3.11–3.14 (Ubuntu + macOS).

**Broken / Incomplete**
- HTTP 4xx/invalid JSON still produce an unenriched note (logged, not retried by design).
- Docker healthcheck probes the vault mount only, not Ollama/Obsidian connectivity.
- No live integration test against a real Ollama or Obsidian REST API (HTTP is mocked).
- Release creation is manual; no tag-driven automation.

**Next Steps**
1. Add an opt-in live integration test (real Ollama + Obsidian REST) in CI.
2. Automate releases on tag push (notes from `CHANGELOG.md`, attach artifacts).
3. Consider `--dry-run` and structured logs/metrics for observability.

License: MIT (see `LICENSE`).
