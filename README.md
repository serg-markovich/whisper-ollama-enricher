# whisper-ollama-enricher

Watches an Obsidian inbox for voice transcripts, enriches them via local Ollama, writes structured notes.

![CI](https://github.com/serg-markovich/whisper-ollama-enricher/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Part of [eigenstack](https://github.com/serg-markovich/eigenstack) — a privacy-first local AI stack.

> **Platform support:** Developed and tested on Ubuntu 24.04.
> macOS support (launchd) is planned for v0.2.0.
> Docker deployment works on any platform.

## Quick Start

```bash
git clone https://github.com/serg-markovich/whisper-ollama-enricher
cd whisper-ollama-enricher
make install
nano ~/.config/whisper-ollama-enricher/.env
make start
make logs
```

## How it works

```
vault/0_inbox/*.md   ← JSON transcript from local-whisper-obsidian
        │
  Watcher            watchdog, non-recursive, skips non-whisper files
        │
  Enricher           Ollama → title, summary, tags, action_items
        │
  Writer      ──►    Obsidian REST API :27124
              └─►    Direct file write → OUTPUT_PATH  (fallback)
        │
  source .md deleted after successful write
```

## Requirements

- Python 3.11+
- Ubuntu 22.04+ (macOS planned for v0.2.0)
- [Ollama](https://ollama.com) running locally — any setup works:
  - native install (`ollama serve`)
  - via [openwebui-systemd-stack](https://github.com/serg-markovich/openwebui-systemd-stack) on Linux
  - via Docker on macOS or NAS
- [local-whisper-obsidian](https://github.com/serg-markovich/local-whisper-obsidian) — recommended source of input JSON files
- Obsidian with [Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api) (optional)

## Configuration

All settings in `~/.config/whisper-ollama-enricher/.env`:

| Variable            | Default                       | Description                            |
|---------------------|-------------------------------|----------------------------------------|
| `INBOX_PATH`        | —                             | Folder to watch (required)             |
| `VAULT_PATH`        | —                             | Obsidian vault root (required)         |
| `OUTPUT_PATH`       | `$VAULT_PATH/1_enriched`      | Where to write enriched notes          |
| `OLLAMA_BASE_URL`   | `http://localhost:11434`      | Ollama endpoint                        |
| `OLLAMA_MODEL`      | `mistral`                     | Model used for enrichment              |
| `OLLAMA_TIMEOUT`    | `60`                          | Seconds before Ollama call times out   |
| `OBSIDIAN_REST_URL` | `http://127.0.0.1:27124`      | Obsidian Local REST API URL            |
| `OBSIDIAN_API_KEY`  | empty                         | API key — leave empty for direct write |
| `LOG_LEVEL`         | `INFO`                        | Logging verbosity                      |

### Ollama location examples

```bash
OLLAMA_BASE_URL=http://localhost:11434        # native on same host
OLLAMA_BASE_URL=http://172.17.0.1:11434      # Docker on same host
OLLAMA_BASE_URL=http://192.168.1.50:11434    # another machine in LAN
```

If Ollama is unreachable, the note is written without enrichment (title = filename, no tags or summary).

## Note templates

Output format is fully customizable. The default template is built into the code
and works without any additional files.

To override:
```bash
nano ~/.config/whisper-ollama-enricher/note_template.md
make restart
```

See [docs/TEMPLATES.md](docs/TEMPLATES.md) for available placeholders and ready-made
templates (Default, Zettelkasten, GTD, Minimal).

## Commands

| Command            | Description                        |
|--------------------|------------------------------------|
| `make install`     | venv + systemd user service        |
| `make start`       | start service                      |
| `make stop`        | stop service                       |
| `make restart`     | restart after config changes       |
| `make status`      | service status                     |
| `make logs`        | live logs via journalctl           |
| `make test`        | run tests                          |
| `make lint`        | ruff check                         |
| `make docker-up`   | start via docker compose           |
| `make docker-down` | stop docker compose                |

## Docker (NAS / headless)

```bash
cp docker/.env.example docker/.env
nano docker/.env   # set VAULT_PATH, then: id -u && id -g for CURRENT_UID/GID
make docker-build
make docker-up
make docker-logs
```

Ollama on the host is reachable from the container at `http://172.17.0.1:11434`.

## My setup

- Hardware: HP EliteBook 845 G8, Ubuntu 24.04
- Vault: `~/obsidian/privat/`
- Inbox: `0_inbox/` — produced by local-whisper-obsidian
- Output: `0_inbox/records_transcribed/`
- Enrichment model: `mistral`

## Eigenstack

This project is the third component of a local-first, privacy-first AI stack
that runs entirely on your own hardware — no cloud APIs, no subscriptions.

```
📱 Voice memo
     │ Syncthing
💻  inotifywait
     │
[local-whisper-obsidian]   transcription (Faster Whisper)
     │
[whisper-ollama-enricher]  enrichment (Ollama)   ← this project
     │
[Obsidian vault]           knowledge base
     │ WebDAV
☁️  Nextcloud (Hetzner)    sync & backup
```

**Related projects:**
- [eigenstack](https://github.com/serg-markovich/eigenstack) — project hub and architecture overview
- [local-whisper-obsidian](https://github.com/serg-markovich/local-whisper-obsidian) — stage 1: voice transcription
- [openwebui-systemd-stack](https://github.com/serg-markovich/openwebui-systemd-stack) — Ollama + Open WebUI service management on Linux

## License

MIT
