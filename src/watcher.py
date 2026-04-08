from __future__ import annotations
import logging
import shutil
import threading
import time
from pathlib import Path

from pydantic import ValidationError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from .config import INBOX_PATH, RETRY_INTERVAL, RETRY_MAX_ATTEMPTS
from .models import WhisperOutput, NoteContext
from .enricher import enrich, OllamaUnavailableError
from .writer import write_note

log = logging.getLogger(__name__)
_PROCESSING: set[str] = set()
RETRY_PATH = INBOX_PATH / ".retry"
FAILED_PATH = INBOX_PATH / ".failed"


def _counter_file(path: Path) -> Path:
    return RETRY_PATH / (path.name + ".count")


def _get_retry_count(path: Path) -> int:
    cf = _counter_file(path)
    try:
        return int(cf.read_text())
    except (FileNotFoundError, ValueError):
        return 0


def _increment_retry_count(path: Path) -> int:
    RETRY_PATH.mkdir(parents=True, exist_ok=True)
    count = _get_retry_count(path) + 1
    _counter_file(path).write_text(str(count))
    return count


def _clear_retry_count(path: Path) -> None:
    cf = _counter_file(path)
    if cf.exists():
        cf.unlink()


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

        try:
            ctx.enrichment = enrich(whisper)
        except OllamaUnavailableError as exc:
            retry_count = _increment_retry_count(path)
            if retry_count >= RETRY_MAX_ATTEMPTS:
                log.error(
                    "Max retries (%d) exceeded for %s — moving to .failed/",
                    RETRY_MAX_ATTEMPTS, path.name,
                )
                FAILED_PATH.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), FAILED_PATH / path.name)
                _clear_retry_count(path)
            else:
                log.warning(
                    "%s — retry queue (attempt %d/%d)",
                    exc, retry_count, RETRY_MAX_ATTEMPTS,
                )
                RETRY_PATH.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), RETRY_PATH / path.name)
            return

        dest = write_note(ctx)
        path.unlink()
        _clear_retry_count(path)
        log.info("✓ %s → %s (source deleted)", path.name, dest)

    except Exception as exc:
        log.error("Failed to process %s: %s", path.name, exc)
    finally:
        _PROCESSING.discard(key)


def _retry_worker() -> None:
    while True:
        time.sleep(RETRY_INTERVAL)
        if not RETRY_PATH.exists():
            continue
        queued = list(RETRY_PATH.glob("*.md"))
        if not queued:
            continue
        log.info("Retry queue: %d file(s) pending", len(queued))
        for f in queued:
            dest = INBOX_PATH / f.name
            shutil.move(str(f), dest)
            _process(dest)


class _InboxHandler(FileSystemEventHandler):
    def on_created(self, event: FileCreatedEvent) -> None:
        if not event.is_directory and Path(event.src_path).suffix == ".md":
            log.info("New file: %s", Path(event.src_path).name)
            _process(Path(event.src_path))


def run() -> None:
    if not INBOX_PATH.exists():
        raise SystemExit(f"INBOX_PATH does not exist: {INBOX_PATH}")

    existing = list(INBOX_PATH.glob("*.md"))
    if existing:
        log.info("Startup scan: %d file(s) in inbox", len(existing))
        for f in existing:
            _process(f)

    if RETRY_PATH.exists():
        queued = list(RETRY_PATH.glob("*.md"))
        if queued:
            log.info("Startup scan: %d file(s) in retry queue", len(queued))
            for f in queued:
                dest = INBOX_PATH / f.name
                shutil.move(str(f), dest)
                _process(dest)

    log.info("Watching %s ...", INBOX_PATH)

    retry_thread = threading.Thread(target=_retry_worker, daemon=True)
    retry_thread.start()
    log.info("Retry worker started (interval: %ds)", RETRY_INTERVAL)

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
