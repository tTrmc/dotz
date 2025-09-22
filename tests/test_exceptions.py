"""Tests for dotz exception classes."""

import pytest

from dotz.exceptions import (
    DotzBackupError,
    DotzError,
    DotzFileNotFoundError,
    DotzGitError,
    DotzRepositoryNotFoundError,
    DotzValidationError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy and behavior."""

    def test_base_exception(self):
        """Test base DotzError exception."""
        error = DotzError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_repository_not_found_error(self):
        """Test DotzRepositoryNotFoundError."""
        error = DotzRepositoryNotFoundError("Repository not found")
        assert str(error) == "Repository not found"
        assert isinstance(error, DotzError)

    def test_file_not_found_error(self):
        """Test DotzFileNotFoundError."""
        error = DotzFileNotFoundError("File not found")
        assert str(error) == "File not found"
        assert isinstance(error, DotzError)

    def test_git_error(self):
        """Test DotzGitError."""
        error = DotzGitError("Git operation failed")
        assert str(error) == "Git operation failed"
        assert isinstance(error, DotzError)

    def test_validation_error(self):
        """Test DotzValidationError."""
        error = DotzValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, DotzError)

    def test_backup_error(self):
        """Test DotzBackupError."""
        error = DotzBackupError("Backup operation failed")
        assert str(error) == "Backup operation failed"
        assert isinstance(error, DotzError)


class TestExceptionUsage:
    """Test exception usage patterns."""

    def test_raising_exceptions(self):
        """Test that exceptions can be raised and caught properly."""
        with pytest.raises(DotzRepositoryNotFoundError):
            raise DotzRepositoryNotFoundError("Test repository error")

        with pytest.raises(DotzFileNotFoundError):
            raise DotzFileNotFoundError("Test file error")

        with pytest.raises(DotzGitError):
            raise DotzGitError("Test git error")

    def test_exception_with_empty_message(self):
        """Test exceptions with empty messages."""
        error = DotzError("")
        assert str(error) == ""

    def test_exception_inheritance_catching(self):
        """Test that specific exceptions can be caught as base DotzError."""
        with pytest.raises(DotzError):
            raise DotzRepositoryNotFoundError("Specific error")

        with pytest.raises(DotzError):
            raise DotzFileNotFoundError("Another specific error")
