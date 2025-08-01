# Makefile for dotz development

.PHONY: help install install-dev test test-cov lint format clean build upload pre-commit-install pre-commit-run setup security docs

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## Run development setup script
	./setup-dev.sh

install:  ## Install the package
	pip install -e .

install-dev:  ## Install essential development dependencies
	pip install -e ".[dev,test,gui]"

install-maintainer:  ## Install all development dependencies (for maintainers)
	pip install -e ".[full,test,gui,maintainer]"

pre-commit-install:  ## Install pre-commit hooks
	pre-commit install
	pre-commit install --hook-type commit-msg

pre-commit-run:  ## Run pre-commit hooks on all files
	pre-commit run --all-files

test:  ## Run tests (contributor-friendly)
	pytest -m "not gui" --tb=short

test-all:  ## Run all tests including GUI tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=dotz --cov-report=html --cov-report=term -m "not gui"

test-ci:  ## Run tests for CI (excluding GUI tests)
	pytest --cov=dotz --cov-report=xml --junitxml=junit.xml -o junit_family=legacy -m "not gui" --tb=short

format:  ## Format code (auto-fix)
	black src tests
	isort src tests

lint:  ## Basic linting (contributor-friendly)
	flake8 src tests
	black --check src tests
	isort --check-only src tests

lint-maintainer:  ## Full linting suite (for maintainers)
	flake8 src tests
	mypy src
	black --check src tests
	isort --check-only src tests
	bandit -r src
	pydocstyle src

security:  ## Run security checks
	bandit -r src -f json -o bandit-report.json
	bandit -r src

docs:  ## Check documentation style
	pydocstyle src

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	python -m build

upload-test:  ## Upload to Test PyPI
	python -m twine upload --repository testpypi dist/*

upload:  ## Upload to PyPI
	python -m twine upload dist/*

check:  ## Check package before upload
	python -m twine check dist/*
