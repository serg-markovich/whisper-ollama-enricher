# whisper-ollama-enricher

Watches a folder for voice transcripts, enriches them via local Ollama,
writes structured Markdown notes.

No cloud. No API keys. Runs on CPU.

![CI](https://github.com/serg-markovich/whisper-ollama-enricher/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> **Platform support:** Linux (systemd) and macOS (launchd).
> Docker deployment works on any platform.
> 🍎 **macOS users:** see [docs/MACOS.md](docs/MACOS.md) for setup instructions.

---

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

If Ollama is unreachable, the file is moved to .retry/ queue
and reprocessed automatically when the service recovers. No data is lost.

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python    | 3.11+   | 3.11+       |
| RAM       | 500 MB  | 1 GB        |
| OS        | Ubuntu 22.04+ / macOS 13+ | Ubuntu 24.04 |
| Ollama    | any model ≥ 1B | mistral (4.1 GB) |
| Disk      | 100 MB + model size | — |

> **Minimum viable setup:** `ollama run gemma3:1b` — runs on 4 GB RAM total,
> quality is lower but usable for short notes.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally — any setup works:
  - native install (`ollama serve`)
  - via [openwebui-systemd-stack](https://github.com/serg-markovich/openwebui-systemd-stack)
  - via Docker on macOS or NAS
- [local-whisper-obsidian](https://github.com/serg-markovich/local-whisper-obsidian)
  — recommended source of input transcripts
- Obsidian [Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api)
  — optional, falls back to direct file write

## Configuration

All settings in `~/.config/whisper-ollama-enricher/.env`:

| Variable            | Default                  | Description                            |
|---------------------|--------------------------|----------------------------------------|
| `INBOX_PATH`        | —                        | Folder to watch (required)             |
| `VAULT_PATH`        | —                        | Obsidian vault root (required)         |
| `OUTPUT_PATH`       | `$VAULT_PATH/1_enriched` | Where to write enriched notes          |
| `OLLAMA_BASE_URL`   | `http://localhost:11434` | Ollama endpoint                        |
| `OLLAMA_MODEL`      | `mistral`                | Model used for enrichment              |
| `OLLAMA_TIMEOUT`    | `60`                     | Seconds before Ollama call times out   |
| `OBSIDIAN_REST_URL` | `http://127.0.0.1:27124` | Obsidian Local REST API URL            |
| `OBSIDIAN_API_KEY`  | empty                    | API key — leave empty for direct write |
| `LOG_LEVEL`         | `INFO`                   | Logging verbosity                      |

### Ollama location examples

```bash
OLLAMA_BASE_URL=http://localhost:11434      # native on same host
OLLAMA_BASE_URL=http://172.17.0.1:11434    # Docker on same host
OLLAMA_BASE_URL=http://192.168.1.50:11434  # another machine in LAN
```

## Note templates

Output format is fully customizable. The default template is built into the code.

To override:
```bash
nano ~/.config/whisper-ollama-enricher/note_template.md
make restart
```

See [docs/TEMPLATES.md](docs/TEMPLATES.md) for available placeholders and
ready-made templates (Default, Zettelkasten, GTD, Minimal).

## Commands

| Command            | Description                              |
|--------------------|------------------------------------------|
| `make install`     | venv + systemd (Linux) / launchd (macOS) |
| `make start`       | start service                            |
| `make stop`        | stop service                             |
| `make restart`     | restart after config changes             |
| `make status`      | service status                           |
| `make logs`        | live logs                                |
| `make test`        | run tests                                |
| `make lint`        | ruff check                               |
| `make docker-up`   | start via docker compose                 |
| `make docker-down` | stop docker compose                      |

## Docker (NAS / headless)

```bash
cp docker/.env.example docker/.env
nano docker/.env
make docker-build
make docker-up
make docker-logs
```

**`docker/.env` configuration:**

| Variable          | Default                    | Description                    |
|-------------------|----------------------------|--------------------------------|
| `VAULT_PATH`      | —                          | Absolute path to vault on host |
| `OLLAMA_BASE_URL` | `http://172.17.0.1:11434`  | Ollama on host                 |
| `CURRENT_UID`     | —                          | Host user ID — run `id -u`     |
| `CURRENT_GID`     | —                          | Host group ID — run `id -g`    |

> **Why CURRENT_UID/GID?** Without this, enriched `.md` files are created
> as `root:root` inside the mounted volume and Obsidian cannot read them.
> Run `id -u && id -g` on your host to get the correct values.

## PKM Compatibility

Output is plain `.md` with YAML frontmatter — works with any
Markdown-based knowledge tool: **Obsidian, Logseq, Foam, Dendron, Zettlr, Joplin**.

No vendor lock-in. Point `OUTPUT_PATH` at any folder your PKM tool watches.

## My setup

- Hardware: HP EliteBook 845 G8, Ubuntu 24.04
- Vault: `~/obsidian/privat/`
- Inbox: `0_inbox/` — produced by local-whisper-obsidian
- Output: `0_inbox/records_transcribed/`
- Model: `mistral`

## Eigenstack

This project is built around the [eigenstack](https://github.com/serg-markovich/eigenstack)
philosophy — privacy-first, local-first infrastructure where every service
runs on your own hardware, no cloud dependencies, no vendor lock-in.

**Related projects:**
- [eigenstack](https://github.com/serg-markovich/eigenstack) — architecture overview
- [local-whisper-obsidian](https://github.com/serg-markovich/local-whisper-obsidian) — stage 1: voice transcription
- [openwebui-systemd-stack](https://github.com/serg-markovich/openwebui-systemd-stack) — Ollama + Open WebUI on Linux

## License

MIT
