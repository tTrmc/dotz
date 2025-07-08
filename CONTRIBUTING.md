# Contributing to loom

Thank you forPlease [open an issue](https://github.com/tTrmc/loom/issues) for any bugs you encounter:
- Describe the steps to reproduce.
- Include logs or stack traces if available.
- Mention your environment (OS, Python version, etc.).

## Suggestions & Questions

For feature ideas or general questions, [open an issue](https://github.com/tTrmc/loom/issues). I'll do my best to respond promptly.terest in contributing to loom! I welcome all pull requests, bug reports, and feature suggestions.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/tTrmc/loom.git
   cd loom
   ```
3. Set up the development environment:
   ```bash
   ./setup-dev.sh  # This sets up virtual environment and installs dependencies
   ```
   Or manually:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev,test]"
   ```
4. Create a new branch for your changes:
   ```bash
   git checkout -b feature/my-new-feature
   ```
5. Make your changes locally in this new branch.
6. Test your changes:
   ```bash
   make test    # Run the test suite
   make lint    # Check code style
   make build   # Build the package
   ```

## Development Tools

This project uses modern Python development tools:
- **pytest**: Testing framework
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **GitHub Actions**: CI/CD pipeline

Run all checks with:
```bash
make test lint
```

## Code Style

Please follow [PEP 8](https://peps.python.org/pep-0008/) guidelines for Python code.

## Commit Messages

Keep commits clear and descriptive:
- Explain what changed and why.  
- Use imperative mood (e.g., “Add support for…” instead of “Added support for…”).  
- Group related changes into a single commit when possible.

## Pull Requests

When you’re ready:
1. Push your branch to your fork on GitHub:
   ```bash
   git push -u origin feature/my-new-feature
   ```
2. Open a pull request (PR):
   - Clearly describe your changes and link to any related issues.
   - Include instructions on how to reproduce or test your changes if necessary.

Once your PR is approved, it will be merged into the main branch.

## Reporting Bugs

Please [open an issue](https://github.com/<yourusername>/loom/issues) for any bugs you encounter:
- Describe the steps to reproduce.
- Include logs or stack traces if available.
- Mention your environment (OS, Python version, etc.).

## Suggestions & Questions

For feature ideas or general questions, [open an issue](https://github.com/<yourusername>/loom/issues). I’ll do my best to respond promptly.

I appreciate your contributions!
