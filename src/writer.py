from __future__ import annotations
import logging
from pathlib import Path
import httpx

from .config import OBSIDIAN_REST_URL, OBSIDIAN_API_KEY, OUTPUT_PATH, CONFIG_DIR
from .models import NoteContext

log = logging.getLogger(__name__)

# Default template — matches local-whisper-obsidian frontmatter standard.
# To override: create ~/.config/whisper-ollama-enricher/note_template.md
# See docs/TEMPLATES.md for examples.
_DEFAULT_TEMPLATE = """\
---
type: voice
source: voice
status: unprocessed
language: {language}
audio: "[[{source_file}]]"
tags:
{tags_yaml}
summary: "{summary}"
---

# {title}

## Transcript

{transcript}

## Action Items

{action_items}
"""


def _load_template() -> str:
    custom = CONFIG_DIR / "note_template.md"
    if custom.exists():
        log.debug("Using custom template: %s", custom)
        return custom.read_text(encoding="utf-8")
    return _DEFAULT_TEMPLATE


def _render(ctx: NoteContext) -> str:
    e = ctx.enrichment
    tags_yaml = (
        "\n".join(f"- {t}" for t in e.tags)
        if e and e.tags
        else "- voice"
    )
    action_items = (
        "\n".join(f"- [ ] {a}" for a in e.action_items)
        if e and e.action_items
        else "- [ ] (no action items)"
    )
    return _load_template().format_map({
        "title":        e.title if e else ctx.whisper.source_file,
        "summary":      e.summary if e else "",
        "tags_yaml":    tags_yaml,
        "action_items": action_items,
        "language":     ctx.whisper.language,
        "source_file":  ctx.whisper.source_file,
        "transcript":   ctx.whisper.transcript,
        "date":         ctx.date_str,
        "date_time":    ctx.date_time_str,
        "date_compact": ctx.date_compact,
        "duration":     ctx.duration_formatted,
        "model":        ctx.whisper.whisper_model,
        "slug":         e.title.lower().replace(" ", "-")[:40] if e else "note",
    })


def _filename(ctx: NoteContext) -> str:
    title = ctx.enrichment.title if ctx.enrichment else ctx.whisper.source_file
    safe = "".join(c if c.isalnum() or c in " -_" else "" for c in title).strip()
    return f"{ctx.date_str} {safe[:60]}.md"


def write_note(ctx: NoteContext) -> Path:
    content  = _render(ctx)
    filename = _filename(ctx)

    if OBSIDIAN_API_KEY:
        try:
            return _write_via_rest(filename, content)
        except Exception as exc:
            log.warning("Obsidian REST API failed (%s) — falling back to direct write", exc)

    return _write_direct(filename, content)


def _write_via_rest(filename: str, content: str) -> Path:
    url = f"{OBSIDIAN_REST_URL}/vault/{filename}"
    with httpx.Client(timeout=10, verify=False) as client:
        r = client.put(
            url,
            content=content.encode(),
            headers={
                "Authorization": f"Bearer {OBSIDIAN_API_KEY}",
                "Content-Type": "text/markdown",
            },
        )
        r.raise_for_status()
    log.info("Written via Obsidian REST API → %s", filename)
    return Path(filename)


def _write_direct(filename: str, content: str) -> Path:
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    dest = OUTPUT_PATH / filename
    dest.write_text(content, encoding="utf-8")
    log.info("Written directly → %s", dest)
    return dest
