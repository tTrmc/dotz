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

test:  ## Run tests (contributor-friendly)
	poetry run pytest -m "not gui" --tb=short

test-all:  ## Run all tests including GUI tests
	poetry run pytest

test-cov:  ## Run tests with coverage
	poetry run pytest --cov=dotz --cov-report=html --cov-report=term -m "not gui"

test-ci:  ## Run tests for CI (excluding GUI tests)
	poetry run pytest --cov=dotz --cov-report=xml --junitxml=junit.xml -o junit_family=legacy -m "not gui" --tb=short

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
