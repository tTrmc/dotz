"""Test runner script and integration tests."""

import subprocess
import sys
from pathlib import Path


def run_tests() -> int:
    """Run all tests with coverage."""
    project_root = Path(__file__).parent.parent

    # Run tests with coverage
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov=src/dotz",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--junit-xml=junit.xml",
        "-v",
    ]

    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
