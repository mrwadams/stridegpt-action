# STRIDE-GPT GitHub Action Makefile

.PHONY: help install test test-cov test-watch lint format clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

dev-install: ## Install development dependencies
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black flake8

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test-watch: ## Run tests in watch mode
	pytest-watch tests/ -- -v

test-unit: ## Run only unit tests
	pytest tests/ -v -m "not integration"

test-integration: ## Run only integration tests
	pytest tests/ -v -m integration

lint: ## Run linting
	flake8 src entrypoint.py
	black --check src entrypoint.py

format: ## Format code
	black src entrypoint.py

clean: ## Clean up generated files
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

test-action: ## Test the action locally
	@echo "Testing GitHub Action locally..."
	STRIDE_API_KEY=test_key \
	GITHUB_TOKEN=test_token \
	GITHUB_REPOSITORY=test/repo \
	TRIGGER_MODE=manual \
	python entrypoint.py

run-tests-ci: ## Run tests as in CI
	flake8 src entrypoint.py --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check src entrypoint.py
	pytest tests/ -v --cov=src --cov-report=xml

check: lint test ## Run linting and tests

all: clean install lint test ## Clean, install, lint, and test