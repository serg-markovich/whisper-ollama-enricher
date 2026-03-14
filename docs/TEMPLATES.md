# Note Templates

whisper-ollama-enricher uses a single active template to render Obsidian notes.

## How it works

1. On startup, the enricher looks for a custom template at:
   `~/.config/whisper-ollama-enricher/note_template.md`
2. If found — uses it. If not — falls back to the built-in default.
3. To switch templates: replace that file and `make restart`.

## Available placeholders

| Placeholder      | Example value                        | Description                        |
|------------------|--------------------------------------|------------------------------------|
| `{title}`        | Купить молоко и позвонить врачу      | AI title, same language as transcript |
| `{summary}`      | Заметка с двумя задачами.            | One-sentence summary, same language |
| `{tags_yaml}`    | - shopping\n- health                 | Tags as YAML list items (English)  |
| `{action_items}` | - [ ] Купить молоко                  | Task list, `- [ ]` format          |
| `{transcript}`   | Купить молоко...                     | Original transcript text           |
| `{source_file}`  | диктофон-1.m4a                       | Original audio filename            |
| `{language}`     | ru                                   | Language code from Whisper         |
| `{date}`         | 2026-03-14                           | Date (YYYY-MM-DD)                  |
| `{date_time}`    | 2026-03-14 14:05                     | Date + time                        |
| `{date_compact}` | 202603141405                         | Compact timestamp (Zettelkasten ID)|
| `{duration}`     | 2m05s                                | Recording duration                 |
| `{model}`        | small                                | Whisper model used                 |
| `{slug}`         | купить-молоко-и-позвонить-врачу      | URL-safe title slug (40 chars max) |

---

## Template examples

### Default (local-whisper-obsidian compatible)

```markdown
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
```

### Zettelkasten

```markdown
---
id: {date_compact}
type: fleeting
source: voice
language: {language}
tags:
{tags_yaml}
---

# {title}

{summary}

## Raw Transcript

{transcript}

## Follow-up

{action_items}
```

### GTD

```markdown
---
type: voice
status: inbox
language: {language}
audio: "[[{source_file}]]"
tags:
{tags_yaml}
---

# {title}

## Context

{summary}

## Next Actions

{action_items}

## Transcript

{transcript}
```

### Minimal

```markdown
# {title}

{transcript}
```

---

## Switching templates

```bash
# Copy one of the examples above into your config:
nano ~/.config/whisper-ollama-enricher/note_template.md

# Then restart:
make restart
```
