PROJECT    := whisper-ollama-enricher
CONFIG_DIR := $(HOME)/.config/$(PROJECT)
ENV_FILE   := $(CONFIG_DIR)/.env
TEMPLATE   := $(CONFIG_DIR)/note_template.md
VENV       := $(HOME)/.local/share/$(PROJECT)/venv
PYTHON     := $(VENV)/bin/python
PIP        := $(VENV)/bin/pip
SERVICE    := $(PROJECT).service

.PHONY: install start stop restart status logs test lint clean \
        docker-build docker-up docker-down docker-logs

install:
	@mkdir -p $(CONFIG_DIR)
	@[ -f $(ENV_FILE) ] || cp .env.example $(ENV_FILE)
	@echo "→ Config:   $(ENV_FILE)"
	@echo "→ Template: $(TEMPLATE) (edit to override default)"
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt -q
	@mkdir -p $(HOME)/.config/systemd/user
	@sed "s|__VENV__|$(VENV)|g; s|__PROJECT_DIR__|$(PWD)|g" \
		systemd/$(SERVICE) > $(HOME)/.config/systemd/user/$(SERVICE)
	systemctl --user daemon-reload
	@echo ""
	@echo "✓ Done."
	@echo "  1. Edit $(ENV_FILE)"
	@echo "  2. Optionally: nano $(TEMPLATE)  (see docs/TEMPLATES.md)"
	@echo "  3. make start"

start:
	systemctl --user start $(SERVICE)

stop:
	systemctl --user stop $(SERVICE)

restart:
	systemctl --user restart $(SERVICE)

status:
	systemctl --user status $(SERVICE)

logs:
	journalctl --user -u $(SERVICE) -f

test:
	$(VENV)/bin/pytest tests/ -v

lint:
	$(VENV)/bin/ruff check src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete

docker-build:
	docker compose -f docker/docker-compose.yml build

docker-up:
	docker compose -f docker/docker-compose.yml up -d

docker-down:
	docker compose -f docker/docker-compose.yml down

docker-logs:
	docker compose -f docker/docker-compose.yml logs -f
