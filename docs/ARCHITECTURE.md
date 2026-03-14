# Architecture

## Overview

whisper-ollama-enricher is a Pipes & Filters pipeline that watches an Obsidian inbox
for JSON transcripts produced by local-whisper-obsidian, enriches them via a local
Ollama LLM, and writes structured Markdown notes back to the vault.

```
voice-memo.m4a
     │
     ▼
[local-whisper-obsidian]
     │  faster-whisper transcription
     │  writes JSON → vault/0_inbox/voice-2026-03-14.md
     ▼
[whisper-ollama-enricher]  ← this project
     │
     ├─ Filter 1: Watcher     (watchdog, non-recursive)
     ├─ Filter 2: Enricher    (Ollama /api/generate)
     └─ Filter 3: Writer      (Obsidian REST API → direct file fallback)
     │
     ▼
vault/0_inbox/records_transcribed/2026-03-14 Title.md
```

## Design decisions

### Pipes & Filters over event queue

A message queue (Redis, RabbitMQ) would be overkill for a single-user local tool
processing one file at a time. Three sequential functions sharing a `NoteContext`
object are simpler to debug and extend.

### watchdog over inotify-simple

watchdog is cross-platform and handles the inotify fd limit automatically.
inotify-simple gives lower overhead but requires manual fd management and
breaks on macOS. For this workload (1-10 files/day) the difference is irrelevant.

### Non-recursive watcher

`recursive=False` is intentional. Only files dropped directly into `INBOX_PATH`
are processed. Subdirectories (e.g. `records_transcribed/`) are ignored,
which prevents feedback loops when `OUTPUT_PATH` is a subdirectory of `INBOX_PATH`.

### JSON detection by content, not filename

Whisper files are identified by `text.startswith("{")` + Pydantic validation,
not by filename pattern. This means any tool can drop a whisper-compatible JSON
into the inbox and it will be processed — no naming convention required.
Non-whisper notes fail silently at DEBUG level.

### Source file deleted after successful write

The JSON `.md` file is a transport artifact, not a note. It is deleted only
after `write_note()` succeeds. If writing fails, the source stays in inbox
for manual inspection.

### Template baked into code

The default note template lives in `src/writer.py` as `_DEFAULT_TEMPLATE`.
A custom template can override it by placing a file at
`~/.config/whisper-ollama-enricher/note_template.md`.
This avoids shipping template files that users might edit in the wrong location.
See `docs/TEMPLATES.md` for examples.

### Obsidian REST API with direct file fallback

Primary write path uses the Obsidian Local REST API plugin (port 27123/27124)
so Obsidian indexes the note immediately. If the API key is empty or the call
fails, the enricher writes directly to `OUTPUT_PATH` on disk.
This makes the tool usable without the plugin installed.

### Config in ~/.config, not in project root

`~/.config/whisper-ollama-enricher/.env` follows the XDG pattern used by
local-whisper-obsidian. A single config file survives `git pull`, re-clones,
and multiple project copies. The systemd unit uses `EnvironmentFile=%h/.config/...`
which resolves to the correct home directory without hardcoded paths.

### Ollama prompt language strategy

`title` and `summary` are generated in the transcript language.
`tags` are always English — they are used for cross-language search and
Obsidian graph linking, where consistent language matters.

## Failure modes and mitigations

| Failure | Mitigation |
|---|---|
| `INBOX_PATH` or `VAULT_PATH` not set | `_require()` exits immediately with actionable message |
| File written while still being copied | `_wait_for_stable()` polls size until stable |
| Same file triggered twice | `_PROCESSING` in-memory set guards against re-entry |
| Ollama unavailable | `enrich()` returns `None`, note written without enrichment |
| Ollama returns invalid JSON | caught by `except Exception`, same fallback |
| Obsidian REST API unavailable | falls back to direct file write |
| Output path does not exist | `OUTPUT_PATH.mkdir(parents=True, exist_ok=True)` |
| Source file is a regular note, not whisper JSON | skipped silently at DEBUG level |

## Module map

```
src/
├── config.py     env vars, fail-fast _require(), CONFIG_DIR export
├── models.py     WhisperOutput, OllamaEnrichment, NoteContext (Pydantic)
├── watcher.py    watchdog observer, JSON filter, pipeline orchestration
├── enricher.py   Ollama HTTP call, prompt, fallback
└── writer.py     template engine, REST API write, direct file fallback
```
