# Makefile for dotz development

.PHONY: help install install-dev test test-cov lint format clean build upload pre-commit-install pre-commit-run setup security docs

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## Run development setup script
	./setup-dev.sh

install:  ## Install the package
	poetry install

install-dev:  ## Install essential development dependencies
	poetry install --with dev,test --extras gui

install-maintainer:  ## Install all development dependencies (for maintainers)
	poetry install --with dev,test,maintainer --extras gui

pre-commit-install:  ## Install pre-commit hooks
	pre-commit install
	pre-commit install --hook-type commit-msg

pre-commit-run:  ## Run pre-commit hooks on all files
	pre-commit run --all-files

test:  ## Run core tests (fast, contributor-friendly)
	poetry run pytest tests/unit -m "not gui and not slow" --tb=short

test-unit:  ## Run unit tests only
	poetry run pytest tests/unit -v --tb=short

test-integration:  ## Run integration tests only
	poetry run pytest tests/integration -v --tb=short

test-gui:  ## Run GUI tests only (requires display)
	poetry run pytest tests/gui -v --tb=short

test-performance:  ## Run performance tests only
	poetry run pytest tests/performance -v --benchmark-only

test-all:  ## Run all tests including GUI tests
	poetry run pytest

test-fast:  ## Run only fast tests (exclude slow and GUI)
	poetry run pytest -m "not slow and not gui" --tb=short

test-slow:  ## Run only slow tests
	poetry run pytest -m "slow" --tb=short

test-cov:  ## Run tests with coverage (excluding GUI and slow tests)
	poetry run pytest tests/unit tests/integration -m "not gui and not slow" --cov=dotz --cov-report=html --cov-report=term

test-cov-all:  ## Run all tests with coverage
	poetry run pytest --cov=dotz --cov-report=html --cov-report=term --cov-report=xml

test-ci:  ## Run tests for CI (excluding GUI tests)
	poetry run pytest tests/unit tests/integration tests/performance -m "not gui" --cov=dotz --cov-report=xml --junitxml=junit.xml -o junit_family=legacy --tb=short

test-parallel:  ## Run tests in parallel
	poetry run pytest -n auto tests/unit tests/integration -m "not gui"

test-watch:  ## Run tests in watch mode
	poetry run pytest-watch tests/ --ignore tests/gui --tb=short

test-random:  ## Run tests in random order
	poetry run pytest --random-order tests/unit

test-profile:  ## Profile test execution
	poetry run pytest --profile-svg tests/unit

test-debug:  ## Run tests with debugging enabled
	poetry run pytest -v -s --tb=long --pdb-trace

format:  ## Format code (auto-fix)
	poetry run black src tests
	poetry run isort src tests

lint:  ## Basic linting (contributor-friendly)
	poetry run flake8 src tests
	poetry run black --check src tests
	poetry run isort --check-only src tests

lint-maintainer:  ## Full linting suite (for maintainers)
	poetry run flake8 src tests
	poetry run mypy src
	poetry run black --check src tests
	poetry run isort --check-only src tests
	poetry run bandit -r src
	poetry run pydocstyle src

security:  ## Run security checks
	poetry run bandit -r src -f json -o bandit-report.json
	poetry run bandit -r src

docs:  ## Check documentation style
	poetry run pydocstyle src

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	poetry build

upload-test:  ## Upload to Test PyPI
	poetry publish --repository testpypi

upload:  ## Upload to PyPI
	poetry publish

check:  ## Check package before upload
	poetry build --format wheel
	poetry run twine check dist/*
