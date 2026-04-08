PROJECT    := whisper-ollama-enricher
CONFIG_DIR := $(HOME)/.config/$(PROJECT)
ENV_FILE   := $(CONFIG_DIR)/.env
TEMPLATE   := $(CONFIG_DIR)/note_template.md
VENV       := $(HOME)/.local/share/$(PROJECT)/venv
PYTHON     := $(VENV)/bin/python
PIP        := $(VENV)/bin/pip
SERVICE    := $(PROJECT).service
PLIST      := $(HOME)/Library/LaunchAgents/$(PROJECT).plist
UNAME      := $(shell uname)

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
ifeq ($(UNAME), Darwin)
	@mkdir -p $(HOME)/Library/LaunchAgents
	@sed "s|__VENV__|$(VENV)|g; s|__PROJECT_DIR__|$(PWD)|g" \
		launchd/$(PROJECT).plist > $(PLIST)
	@echo "✓ launchd plist installed: $(PLIST)"
else
	@mkdir -p $(HOME)/.config/systemd/user
	@sed "s|__VENV__|$(VENV)|g; s|__PROJECT_DIR__|$(PWD)|g" \
		systemd/$(SERVICE) > $(HOME)/.config/systemd/user/$(SERVICE)
	systemctl --user daemon-reload
endif
	@echo ""
	@echo "✓ Done."
	@echo "  1. Edit $(ENV_FILE)"
	@echo "  2. Optionally: nano $(TEMPLATE)  (see docs/TEMPLATES.md)"
	@echo "  3. make start"

start:
ifeq ($(UNAME), Darwin)
	launchctl load $(PLIST)
else
	systemctl --user start $(SERVICE)
endif

stop:
ifeq ($(UNAME), Darwin)
	launchctl unload $(PLIST)
else
	systemctl --user stop $(SERVICE)
endif

restart:
ifeq ($(UNAME), Darwin)
	launchctl unload $(PLIST) 2>/dev/null || true
	launchctl load $(PLIST)
else
	systemctl --user restart $(SERVICE)
endif

status:
ifeq ($(UNAME), Darwin)
	launchctl list | grep $(PROJECT) || echo "Service not running"
else
	systemctl --user status $(SERVICE)
endif

logs:
ifeq ($(UNAME), Darwin)
	log stream --predicate 'process == "python3"' --level info
else
	journalctl --user -u $(SERVICE) -f
endif

test:
	$(VENV)/bin/pytest tests/ -v

lint:
	$(VENV)/bin/ruff check src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete

verify: lint test
	@git ls-files --error-unmatch .env 2>/dev/null && echo "FATAL: .env is tracked" && exit 1 || true
	@echo "✓ All checks passed"

docker-build:
	docker compose -f docker/docker-compose.yml build

docker-up:
	docker compose -f docker/docker-compose.yml up -d

docker-down:
	docker compose -f docker/docker-compose.yml down

docker-logs:
	docker compose -f docker/docker-compose.yml logs -f
