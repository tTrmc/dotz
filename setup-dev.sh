#!/bin/bash
# Development setup script for dotz

set -e

echo "Setting up dotz development environment..."

# Check Python version
if ! python3 -c "import sys; exit(not (sys.version_info >= (3, 9)))"; then
    echo "ERROR: Python 3.9+ required"
    exit 1
fi

# Install Poetry if needed
if ! command -v poetry >/dev/null 2>&1; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Configure Poetry
poetry config virtualenvs.in-project true

# Install dependencies
echo "Installing dependencies..."
poetry install --with dev,test --extras gui

# Development setup complete

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Quick start:"
echo "  poetry shell           # Activate environment"
echo "  make help              # Show available commands"
echo "  poetry run dotz --help # Test CLI"