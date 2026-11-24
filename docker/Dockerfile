FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY bin ./bin

# Mount/writability probe: catches a missing or read-only vault mount.
HEALTHCHECK --interval=60s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, pathlib, sys; p = pathlib.Path(os.environ.get('INBOX_PATH', '')); sys.exit(0 if p.is_dir() and os.access(p, os.W_OK) else 1)"

CMD ["python", "bin/run.py"]
