# macOS Setup

> Community-tested. If you encounter issues, please [open an issue](https://github.com/serg-markovich/whisper-ollama-enricher/issues).

whisper-ollama-enricher uses **launchd** on macOS instead of systemd.
`make install` detects the OS automatically and installs the correct service.

## Requirements

- macOS 13+
- Python 3.11+ (`brew install python@3.11`)
- [Ollama for macOS](https://ollama.com/download) — runs natively, no Docker needed

## Quick Start

```bash
git clone https://github.com/serg-markovich/whisper-ollama-enricher
cd whisper-ollama-enricher
make install
nano ~/.config/whisper-ollama-enricher/.env
make start
make logs
```

## One manual step after make install

The launchd plist needs your actual config path. Open the installed plist:

```bash
nano ~/Library/LaunchAgents/whisper-ollama-enricher.plist
```

Replace `__CONFIG_DIR__` with your actual config directory:

```xml
<!-- change this: -->
<string>__CONFIG_DIR__/.env</string>

<!-- to this: -->
<string>/Users/YOUR_USERNAME/.config/whisper-ollama-enricher/.env</string>
```

Then reload:

```bash
make restart
```

## Configuration

Same as Linux — all settings in `~/.config/whisper-ollama-enricher/.env`.

Ollama on macOS runs on `localhost:11434` by default:

```bash
OLLAMA_BASE_URL=http://localhost:11434
```

## Commands

| Command          | macOS equivalent               |
|------------------|-------------------------------|
| `make start`     | `launchctl load ~/Library/LaunchAgents/...plist`   |
| `make stop`      | `launchctl unload ~/Library/LaunchAgents/...plist` |
| `make restart`   | unload + load                  |
| `make status`    | `launchctl list | grep whisper-ollama-enricher`    |
| `make logs`      | `log stream --predicate 'process == "python3"'`    |

## Logs location

launchd writes logs to:

```
/tmp/whisper-ollama-enricher.log   # stdout
/tmp/whisper-ollama-enricher.err   # stderr
```

Quick view:

```bash
tail -f /tmp/whisper-ollama-enricher.log
```

## Known limitations on macOS

- `make logs` via `log stream` shows all python3 processes, not only this service.
  Use `tail -f /tmp/whisper-ollama-enricher.log` for cleaner output.
- launchd `KeepAlive=true` restarts the service on crash, but unlike systemd
  there is no `RestartSec` — restarts are immediate.

## Troubleshooting

**Service not starting:**
```bash
cat /tmp/whisper-ollama-enricher.err
```

**Ollama not reachable:**
```bash
curl http://localhost:11434/api/tags
# if empty — start Ollama: open -a Ollama
```

**Permission denied on vault:**
```bash
ls -la ~/path/to/vault/0_inbox
# ensure your user owns the directory
```
