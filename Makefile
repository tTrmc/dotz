# Makefile for dotz development

.PHONY: help install install-dev test test-cov lint format clean build upload

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -e ".[dev,test,gui]"

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=dotz --cov-report=html --cov-report=term

format:  ## Format code
	black src tests
	isort src tests

lint:  ## Run linting tools
	flake8 src tests
	mypy src
	black --check src tests
	isort --check-only src tests

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
