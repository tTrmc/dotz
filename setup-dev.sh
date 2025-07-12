#!/bin/bash
# Development setup script for dotz

set -e

echo "Setting up dotz development environment..."

# Check if Python 3.9+ is available
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
required_version="3.9"

if ! python3 -c "import sys; exit(not (sys.version_info >= (3, 9)))"; then
    echo "ERROR: Python 3.9 or higher is required. Found: Python $python_version"
    exit 1
fi

echo "Python $python_version found"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Verify we're in the virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment activated: $VIRTUAL_ENV"
else
    echo "Warning: Virtual environment not activated properly"
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "Installing development dependencies..."
pip install -e ".[dev,test]"

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
if command -v pre-commit >/dev/null 2>&1; then
    pre-commit install
    pre-commit install --hook-type commit-msg
    echo "Pre-commit hooks installed successfully"
else
    echo "Warning: pre-commit not found, installing..."
    pip install pre-commit
    pre-commit install
    pre-commit install --hook-type commit-msg
    echo "Pre-commit hooks installed successfully"
fi

echo ""
echo "Development environment setup complete!"
echo ""
echo "IMPORTANT: To activate the environment in your current shell, run:"
echo "  source .venv/bin/activate"
echo ""
echo "Available commands:"
echo "  make help          # Show all available commands"
echo "  make test          # Run tests"
echo "  make test-cov      # Run tests with coverage"
echo "  make lint          # Run code quality checks"
echo "  make format        # Auto-format code"
echo "  pre-commit run     # Run pre-commit hooks manually"
echo "  dotz --help        # Test CLI"
echo ""
echo "Note: The script has set up the environment, but you need to activate"
echo "      it manually in your shell to use the installed packages."
echo ""
