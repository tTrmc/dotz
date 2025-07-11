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

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "Installing development dependencies..."
pip install -e ".[dev,test]"

# Install build tools
echo "Installing build tools..."
pip install build twine

echo ""
echo "Development environment setup complete!"
echo ""
echo "To activate the environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "Available commands:"
echo "  make help          # Show all available commands"
echo "  make test          # Run tests"
echo "  make test-cov      # Run tests with coverage"
echo "  make lint          # Run linting"
echo "  make format        # Format code"
echo "  dotz --help     # Test CLI"
echo ""
