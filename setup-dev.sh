#!/bin/bash
# Development setup script for dotz

set -e

echo "Setting up dotz development environment with Poetry..."

# Check if Python 3.9+ is available
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
required_version="3.9"

if ! python3 -c "import sys; exit(not (sys.version_info >= (3, 9)))"; then
    echo "ERROR: Python 3.9 or higher is required. Found: Python $python_version"
    exit 1
fi

echo "Python $python_version found"

# Check if Poetry is installed
if ! command -v poetry >/dev/null 2>&1; then
    echo "Poetry is not installed. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    echo "Poetry installed successfully"
else
    echo "Poetry is already installed"
fi

echo "Configuring Poetry to create virtual environment in project directory..."
poetry config virtualenvs.in-project true

# Install development dependencies
echo "Installing contributor-friendly development dependencies..."
poetry install --with dev,test

# Ask if user wants full maintainer setup
echo ""
read -p "Are you a maintainer and want the full toolset? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing full maintainer dependencies..."
    poetry install --with dev,test,maintainer --extras gui
else
    # Ask if user wants GUI dependencies
    read -p "Do you want to install GUI dependencies for testing? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        poetry install --with dev,test --extras gui
    fi
fi

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
if poetry run pre-commit --version >/dev/null 2>&1; then
    poetry run pre-commit install
    poetry run pre-commit install --hook-type commit-msg
    echo "Pre-commit hooks installed successfully"
else
    echo "Warning: pre-commit not found in virtual environment"
    echo "This should not happen if dependencies were installed correctly"
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "IMPORTANT: To activate the Poetry environment, run:"
echo "  poetry shell"
echo "Or prefix commands with 'poetry run', e.g.:"
echo "  poetry run dotz --help"
echo ""
echo "Quick start commands:"
echo "  make help          # Show all available commands"
echo "  make test          # Run core tests (fast, contributor-friendly)"
echo "  make format        # Auto-format your code"
echo "  make lint          # Basic code checks"
echo "  poetry run dotz --help  # Test the CLI directly"
echo ""
echo "Optional commands:"
echo "  make test-all      # Run all tests including GUI"
echo "  make test-cov      # Run tests with coverage"
echo "  make lint-maintainer # Full linting suite"
echo "  poetry add <package>  # Add a new dependency"
echo "  poetry add --group dev <package>  # Add a dev dependency"
echo ""
echo "Pre-commit hooks are set up with minimal, auto-fixing rules."
echo "They'll mostly fix formatting issues for you automatically!"
echo ""
echo "Check out docs/CONTRIBUTING_SIMPLE.md for a quick start guide."
echo ""
