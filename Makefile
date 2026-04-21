PYTHON    ?= python3
VENV_DIR  := .venv
VENV_BIN  := $(VENV_DIR)/bin
PIP       := $(VENV_BIN)/pip

.DEFAULT_GOAL := help

.PHONY: help venv install dev uninstall test clean

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "  venv      Create the virtual environment in $(VENV_DIR)/"
	@echo "  install   Create venv (if needed) and install dockyman"
	@echo "  dev       Install in editable mode and open an activated shell"
	@echo "  test      Run the test suite"
	@echo "  uninstall Remove dockyman from the venv"
	@echo "  clean     Delete the virtual environment and build artifacts"

venv:
	@test -d $(VENV_DIR) || $(PYTHON) -m venv $(VENV_DIR)
	@echo "Virtual environment ready: $(VENV_DIR)/"

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install .
	@echo ""
	@echo "dockyman installed. Activate with:"
	@echo "  source $(VENV_BIN)/activate"

dev: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e .
	@echo ""
	@echo "Activating virtual environment (type 'exit' to deactivate) …"
	@bash --init-file $(VENV_BIN)/activate -i

uninstall:
	$(PIP) uninstall -y dockyman

test: venv
	$(PIP) install --quiet ".[dev]"
	$(VENV_BIN)/pytest tests/ -v

clean:
	rm -rf $(VENV_DIR) build dist *.egg-info
