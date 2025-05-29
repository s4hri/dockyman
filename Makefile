# Configurable Variables
PYTHON := python3
VERSION := $(shell cat dockyman/VERSION)
TARGET_DIR?=.
VENV_DIR := $(TARGET_DIR)/.venv

# Install virtual environment in custom target directory
install-venv:
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install .

# Build a wheel
build:
	$(VENV_DIR)/bin/pip install build
	$(VENV_DIR)/bin/python -m build

# Install system-wide
install:
	$(PYTHON) -m build
	$(PYTHON) -m pip install dist/*.whl

# Uninstall system-wide
uninstall:
	$(PYTHON) -m pip uninstall -y dockyman

# Run tests in venv
test: install-venv
	$(VENV_DIR)/bin/pytest tests -s

# Clean venvs and build artifacts
clean-venv:
	rm -rf $(TARGET_DIR)/.venv

clean:
	rm -rf $(TARGET_DIR)/.venv dist build *.egg-info .pytest_cache
	find . -name __pycache__ -exec rm -rf {} +

