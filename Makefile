.PHONY: help setup test test-unit test-integration lint format run-cli run-web run-scheduler clean

# Use uv for Python package management
PYTHON := python
PIP := uv pip
PYTEST := pytest
UV := uv
ADK := adk

# Help target that lists all available targets with descriptions
help:
	@echo "radbot Makefile Targets:"
	@echo "=========================="
	@echo "setup          : Install development dependencies using uv"
	@echo "test           : Run all tests"
	@echo "test-unit      : Run only unit tests"
	@echo "test-integration: Run only integration tests"
	@echo "lint           : Run all linting checks (flake8, mypy, black, isort)"
	@echo "format         : Auto-format code with black and isort"
	@echo "run-cli        : Start the radbot CLI interface"
	@echo "run-web        : Start the radbot web interface using ADK"
	@echo "run-scheduler  : Run the scheduler with optional arguments (use ARGS=\"--your-args\")"
	@echo "clean          : Remove build artifacts and cache files"
	@echo ""
	@echo "Example usage:"
	@echo "  make setup              # Install development dependencies"
	@echo "  make test               # Run all tests"
	@echo "  make run-cli            # Start the interactive CLI"
	@echo "  make run-web            # Start the web interface"
	@echo "  make run-scheduler ARGS=\"--additional-args\""

# Set help as the default target
.DEFAULT_GOAL := help

setup:
	$(UV) pip install -e ".[dev]"
	$(UV) pip install --upgrade pip

test:
	$(PYTEST)

test-unit:
	$(PYTEST) tests/unit

test-integration:
	$(PYTEST) tests/integration

lint:
	flake8 radbot tests
	mypy radbot tests
	black --check radbot tests
	isort --check radbot tests

format:
	black radbot tests
	isort radbot tests

run-cli:
	$(PYTHON) -m radbot.cli.main

run-web:
	$(ADK) web

run-scheduler:
	$(PYTHON) -m radbot.cli.scheduler $(ARGS)

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.mypy_cache" -exec rm -rf {} +
