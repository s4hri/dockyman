PYTHON=python3
VERSION=3.0
VENV_DIR=.dockyman-${VERSION}

install-venv:
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install .

test: install-venv
	$(VENV_DIR)/bin/pytest tests -s
	make clean

clean:
	rm -rf $(VENV_DIR) dist build *.egg-info .pytest_cache
	find . -name __pycache__ -exec rm -rf {} +
