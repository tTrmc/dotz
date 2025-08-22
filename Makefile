# Makefile for dotz development

.PHONY: help install test lint format clean build

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package for development
	poetry install --with dev,test --extras gui

test:  ## Run tests (when available)
	@echo "Tests directory is empty - skipping tests"

format:  ## Auto-format code
	poetry run black src
	poetry run isort src

lint:  ## Check code style and quality  
	poetry run flake8 src
	poetry run black --check src
	poetry run isort --check-only src

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