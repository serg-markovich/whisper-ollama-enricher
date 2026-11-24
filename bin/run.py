#!/usr/bin/env python3
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="whisper-ollama-enricher",
        description="Watch inbox, enrich whisper transcripts via Ollama, write notes.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="process inbox and retry queue once, then exit (no watcher)",
    )
    args = parser.parse_args()

    # Imported after argparse so `--help` works without a configured .env.
    from src.config import INBOX_PATH, LOG_LEVEL
    from src.lock import AlreadyRunningError, acquire_lock
    from src.watcher import process_once, run

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not INBOX_PATH.exists():
        raise SystemExit(f"INBOX_PATH does not exist: {INBOX_PATH}")

    try:
        lock = acquire_lock(INBOX_PATH)
    except AlreadyRunningError as exc:
        raise SystemExit(f"[whisper-ollama-enricher] FATAL: {exc}")

    try:
        if args.once:
            process_once()
        else:
            run()
    finally:
        lock.close()


if __name__ == "__main__":
    main()
