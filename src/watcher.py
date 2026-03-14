from __future__ import annotations
import logging
import time
from pathlib import Path

from pydantic import ValidationError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from .config import INBOX_PATH
from .models import WhisperOutput, NoteContext
from .enricher import enrich
from .writer import write_note

log = logging.getLogger(__name__)
_PROCESSING: set[str] = set()


def _wait_for_stable(path: Path, interval: float = 0.5, rounds: int = 6) -> bool:
    prev = -1
    for _ in range(rounds):
        if not path.exists():
            return False
        size = path.stat().st_size
        if size == prev and size > 0:
            return True
        prev = size
        time.sleep(interval)
    return True


def _process(path: Path) -> None:
    key = str(path)
    if key in _PROCESSING:
        log.debug("Already processing %s — skipping", path.name)
        return
    _PROCESSING.add(key)
    try:
        if not _wait_for_stable(path):
            log.warning("File vanished before processing: %s", path)
            return

        text = path.read_text(encoding="utf-8").strip()

        if not text.startswith("{"):
            log.debug("Not a whisper JSON, skipping: %s", path.name)
            return

        try:
            whisper = WhisperOutput.model_validate_json(text)
        except (ValidationError, ValueError):
            log.debug("Not a whisper file, skipping: %s", path.name)
            return

        ctx = NoteContext(whisper=whisper, source_md_path=str(path))
        ctx.enrichment = enrich(whisper)
        dest = write_note(ctx)

        path.unlink()
        log.info("✓ %s → %s (source deleted)", path.name, dest)

    except Exception as exc:
        log.error("Failed to process %s: %s", path.name, exc)
    finally:
        _PROCESSING.discard(key)


class _InboxHandler(FileSystemEventHandler):
    def on_created(self, event: FileCreatedEvent) -> None:
        if not event.is_directory and Path(event.src_path).suffix == ".md":
            log.info("New file: %s", Path(event.src_path).name)
            _process(Path(event.src_path))


def run() -> None:
    if not INBOX_PATH.exists():
        raise SystemExit(f"INBOX_PATH does not exist: {INBOX_PATH}")
    log.info("Watching %s ...", INBOX_PATH)
    observer = Observer()
    observer.schedule(_InboxHandler(), str(INBOX_PATH), recursive=False)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        log.info("Stopping...")
    finally:
        observer.stop()
        observer.join()
