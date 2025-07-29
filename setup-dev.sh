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
echo "Installing contributor-friendly development dependencies..."
pip install -e ".[dev,test]"

# Ask if user wants full maintainer setup
echo ""
read -p "Are you a maintainer and want the full toolset? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing full maintainer dependencies..."
    pip install -e ".[maintainer]"
fi

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
echo "🎉 Development environment setup complete!"
echo ""
echo "IMPORTANT: To activate the environment in your current shell, run:"
echo "  source .venv/bin/activate"
echo ""
echo "Quick start commands:"
echo "  make help          # Show all available commands"
echo "  make test          # Run core tests (fast, contributor-friendly)"
echo "  make format        # Auto-format your code"
echo "  make lint          # Basic code checks"
echo ""
echo "Optional commands:"
echo "  make test-all      # Run all tests including GUI"
echo "  make test-cov      # Run tests with coverage"
echo "  make lint-maintainer # Full linting suite"
echo ""
echo "Pre-commit hooks are set up with minimal, auto-fixing rules."
echo "They'll mostly fix formatting issues for you automatically!"
echo ""
echo "Check out docs/CONTRIBUTING_SIMPLE.md for a quick start guide."
echo ""
