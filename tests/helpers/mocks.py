"""
Mock objects and utilities for dotz tests.

This module provides specialized mock objects and utilities that are commonly
used across different test modules, helping to reduce code duplication and
ensure consistent mocking patterns.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock, MagicMock, PropertyMock

from git import Repo


class MockGitRepo:
    """Comprehensive mock Git repository with realistic behavior."""
    
    def __init__(self, 
                 is_dirty: bool = False,
                 untracked_files: List[str] = None,
                 has_remote: bool = False,
                 branch_name: str = "main"):
        """
        Initialize mock Git repository.
        
        Args:
            is_dirty: Whether repo has uncommitted changes
            untracked_files: List of untracked files
            has_remote: Whether repo has remote configured
            branch_name: Current branch name
        """
        self.mock = Mock(spec=Repo)
        
        # Basic repository state
        self.mock.is_dirty.return_value = is_dirty
        self.mock.untracked_files = untracked_files or []
        self.mock.bare = False
        self.mock.git_dir = "/tmp/test_repo/.git"
        self.mock.working_dir = "/tmp/test_repo"
        
        # Git command interface
        self._setup_git_commands()
        
        # Index operations
        self._setup_index()
        
        # Branch operations
        self._setup_branches(branch_name)
        
        # Remote operations
        self._setup_remotes(has_remote)
        
        # Diff operations
        self._setup_diffs()
    
    def _setup_git_commands(self):
        """Set up git command interface."""
        git_mock = Mock()
        git_mock.ls_files.return_value = ""
        git_mock.status.return_value = "On branch main\\nnothing to commit, working tree clean"
        git_mock.add.return_value = None
        git_mock.commit.return_value = None
        git_mock.pull.return_value = None
        git_mock.push.return_value = None
        self.mock.git = git_mock
    
    def _setup_index(self):
        """Set up index operations."""
        index_mock = Mock()
        
        # Mock commit returns
        commit_mock = Mock()
        commit_mock.hexsha = "abc123def456789"
        commit_mock.message = "Test commit"
        index_mock.commit.return_value = commit_mock
        
        # Mock add/remove operations
        index_mock.add.return_value = None
        index_mock.remove.return_value = None
        
        # Mock diff operations
        index_mock.diff.return_value = []
        
        self.mock.index = index_mock
    
    def _setup_branches(self, branch_name: str):
        """Set up branch operations."""
        # Active branch
        branch_mock = Mock()
        branch_mock.name = branch_name
        branch_mock.tracking_branch.return_value = None
        
        self.mock.active_branch = branch_mock
        self.mock.heads = [branch_mock]
        
        # Head reference
        head_mock = Mock()
        commit_mock = Mock()
        commit_mock.hexsha = "abc123def456789"
        commit_mock.message = "Latest commit"
        commit_mock.diff.return_value = []
        head_mock.commit = commit_mock
        
        self.mock.head = head_mock
    
    def _setup_remotes(self, has_remote: bool):
        """Set up remote operations."""
        if has_remote:
            remote_mock = Mock()
            remote_mock.name = "origin"
            remote_mock.url = "git@github.com:user/dotfiles.git"
            remote_mock.pull.return_value = []
            remote_mock.push.return_value = []
            
            self.mock.remotes = [remote_mock]
            self.mock.remote.return_value = remote_mock
        else:
            self.mock.remotes = []
            self.mock.remote.side_effect = Exception("No remote configured")
    
    def _setup_diffs(self):
        """Set up diff operations."""
        self.mock.head.commit.diff.return_value = []
    
    def add_tracked_files(self, files: List[str]):
        """Add files to the tracked files list."""
        self.mock.git.ls_files.return_value = "\\n".join(files)
    
    def add_untracked_files(self, files: List[str]):
        """Add files to untracked files list."""
        self.mock.untracked_files.extend(files)
    
    def make_dirty(self, dirty: bool = True):
        """Change dirty state of repository."""
        self.mock.is_dirty.return_value = dirty
    
    def set_commit_message(self, message: str):
        """Set the latest commit message."""
        self.mock.head.commit.message = message
        self.mock.index.commit.return_value.message = message
    
    def get_mock(self) -> Mock:
        """Get the configured mock object."""
        return self.mock


class MockFileSystem:
    """Mock file system operations for testing."""
    
    def __init__(self):
        """Initialize mock file system."""
        self._files = {}
        self._directories = set()
    
    def create_file(self, path: Union[str, Path], content: str = ""):
        """Create a mock file with content."""
        self._files[str(path)] = content
        # Ensure parent directories exist
        parent = Path(path).parent
        self._directories.add(str(parent))
    
    def create_directory(self, path: Union[str, Path]):
        """Create a mock directory."""
        self._directories.add(str(path))
    
    def file_exists(self, path: Union[str, Path]) -> bool:
        """Check if mock file exists."""
        return str(path) in self._files
    
    def directory_exists(self, path: Union[str, Path]) -> bool:
        """Check if mock directory exists."""
        return str(path) in self._directories
    
    def get_file_content(self, path: Union[str, Path]) -> str:
        """Get content of mock file."""
        return self._files.get(str(path), "")
    
    def list_files(self, pattern: str = "*") -> List[str]:
        """List files matching pattern."""
        import fnmatch
        return [f for f in self._files.keys() if fnmatch.fnmatch(f, pattern)]
    
    def setup_path_mocks(self, monkeypatch):
        """Set up monkeypatch for Path methods."""
        def mock_exists(self):
            path_str = str(self)
            return (path_str in self._files or 
                   path_str in self._directories)
        
        def mock_is_file(self):
            return str(self) in self._files
        
        def mock_is_dir(self):
            return str(self) in self._directories
        
        def mock_read_text(self):
            content = self._files.get(str(self))
            if content is None:
                raise FileNotFoundError(f"File not found: {self}")
            return content
        
        def mock_write_text(self, content):
            self._files[str(self)] = content
        
        monkeypatch.setattr(Path, "exists", mock_exists)
        monkeypatch.setattr(Path, "is_file", mock_is_file)
        monkeypatch.setattr(Path, "is_dir", mock_is_dir)
        monkeypatch.setattr(Path, "read_text", mock_read_text)
        monkeypatch.setattr(Path, "write_text", mock_write_text)


class MockConsole:
    """Mock Rich console for testing output."""
    
    def __init__(self):
        """Initialize mock console."""
        self.printed_messages = []
        self.mock = Mock()
        self.mock.print.side_effect = self._capture_print
    
    def _capture_print(self, *args, **kwargs):
        """Capture print calls."""
        message = " ".join(str(arg) for arg in args)
        self.printed_messages.append(message)
    
    def get_printed_messages(self) -> List[str]:
        """Get all printed messages."""
        return self.printed_messages.copy()
    
    def clear_messages(self):
        """Clear captured messages."""
        self.printed_messages.clear()
    
    def assert_message_printed(self, expected_message: str):
        """Assert that a specific message was printed."""
        assert any(expected_message in msg for msg in self.printed_messages), \
               f"Expected message '{expected_message}' not found in: {self.printed_messages}"
    
    def get_mock(self) -> Mock:
        """Get the mock console object."""
        return self.mock


class MockTyperContext:
    """Mock Typer context for CLI testing."""
    
    def __init__(self):
        """Initialize mock Typer context."""
        self.exit_called = False
        self.exit_code = None
        self.echo_messages = []
        
        self.mock = Mock()
        self.mock.exit.side_effect = self._capture_exit
        self.mock.echo.side_effect = self._capture_echo
    
    def _capture_exit(self, code: int = 0):
        """Capture exit calls."""
        self.exit_called = True
        self.exit_code = code
    
    def _capture_echo(self, message: str, **kwargs):
        """Capture echo calls."""
        self.echo_messages.append(message)
    
    def get_mock(self) -> Mock:
        """Get the mock context object."""
        return self.mock


class MockProgressBar:
    """Mock progress bar for testing long operations."""
    
    def __init__(self):
        """Initialize mock progress bar."""
        self.tasks = {}
        self.current_task_id = 0
        
        self.mock = Mock()
        self.mock.add_task.side_effect = self._add_task
        self.mock.update.side_effect = self._update_task
        self.mock.__enter__.return_value = self.mock
        self.mock.__exit__.return_value = None
    
    def _add_task(self, description: str, total: int = 100):
        """Add a task to the progress bar."""
        task_id = self.current_task_id
        self.tasks[task_id] = {
            "description": description,
            "total": total,
            "completed": 0
        }
        self.current_task_id += 1
        return task_id
    
    def _update_task(self, task_id: int, advance: int = 1, **kwargs):
        """Update task progress."""
        if task_id in self.tasks:
            self.tasks[task_id]["completed"] += advance
    
    def get_task_progress(self, task_id: int) -> Dict[str, Any]:
        """Get progress for a specific task."""
        return self.tasks.get(task_id, {})
    
    def get_mock(self) -> Mock:
        """Get the mock progress bar object."""
        return self.mock


class MockWatchdog:
    """Mock watchdog file system observer."""
    
    def __init__(self):
        """Initialize mock watchdog."""
        self.is_alive = False
        self.observers = []
        self.handlers = []
        
        self.mock = Mock()
        self.mock.start.side_effect = self._start
        self.mock.stop.side_effect = self._stop
        self.mock.join.side_effect = self._join
        self.mock.schedule.side_effect = self._schedule
        self.mock.is_alive.side_effect = lambda: self.is_alive
    
    def _start(self):
        """Start the observer."""
        self.is_alive = True
    
    def _stop(self):
        """Stop the observer."""
        self.is_alive = False
    
    def _join(self, timeout=None):
        """Join the observer thread."""
        pass
    
    def _schedule(self, handler, path, recursive=False):
        """Schedule a handler for a path."""
        self.handlers.append({
            "handler": handler,
            "path": path,
            "recursive": recursive
        })
    
    def trigger_event(self, event_type: str, src_path: str):
        """Trigger a file system event."""
        for handler_info in self.handlers:
            handler = handler_info["handler"]
            if hasattr(handler, "on_any_event"):
                event_mock = Mock()
                event_mock.event_type = event_type
                event_mock.src_path = src_path
                event_mock.is_directory = False
                handler.on_any_event(event_mock)
    
    def get_mock(self) -> Mock:
        """Get the mock observer object."""
        return self.mock


def create_temp_git_repo() -> Path:
    """Create a temporary Git repository for testing."""
    import tempfile
    from git import Repo
    
    temp_dir = Path(tempfile.mkdtemp())
    repo = Repo.init(temp_dir)
    
    # Configure user for commits
    with repo.config_writer() as git_config:
        git_config.set_value("user", "name", "Test User")
        git_config.set_value("user", "email", "test@example.com")
    
    # Create initial commit
    readme = temp_dir / "README.md"
    readme.write_text("# Test Repository")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    
    return temp_dir


def mock_datetime_now(fixed_datetime):
    """Create a mock for datetime.now() that returns a fixed value."""
    from unittest.mock import patch
    from datetime import datetime
    
    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_datetime
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        return mock_datetime


def mock_time_time(fixed_timestamp: float):
    """Create a mock for time.time() that returns a fixed value."""
    from unittest.mock import patch
    
    with patch("time.time") as mock_time:
        mock_time.return_value = fixed_timestamp
        return mock_time


def create_mock_operation_result(success: bool = True, **extra_fields) -> Dict[str, Any]:
    """Create a standardized operation result dictionary."""
    result = {
        "success": success,
        "message": "Operation completed" if success else "Operation failed"
    }
    result.update(extra_fields)
    return result


def create_mock_repo_status(is_dirty: bool = False, 
                           untracked_files: List[str] = None,
                           has_remote: bool = True,
                           ahead: int = 0,
                           behind: int = 0) -> Dict[str, Any]:
    """Create a mock repository status dictionary."""
    return {
        "is_dirty": is_dirty,
        "untracked_files": untracked_files or [],
        "has_remote": has_remote,
        "ahead": ahead,
        "behind": behind,
        "branch": "main"
    }


def create_mock_config() -> Dict[str, Any]:
    """Create a mock dotz configuration."""
    return {
        "file_patterns": {
            "include": [".*", "*.conf", "*.config"],
            "exclude": [".DS_Store", "*.log", "*.tmp"]
        },
        "search_settings": {
            "recursive": True,
            "case_sensitive": False,
            "follow_symlinks": False
        }
    }


class MockEnvironment:
    """Mock environment manager for testing."""
    
    def __init__(self):
        """Initialize mock environment."""
        self.original_env = {}
        self.current_env = {}
    
    def set_env_var(self, key: str, value: str):
        """Set environment variable."""
        import os
        if key not in self.original_env:
            self.original_env[key] = os.environ.get(key)
        os.environ[key] = value
        self.current_env[key] = value
    
    def unset_env_var(self, key: str):
        """Unset environment variable."""
        import os
        if key not in self.original_env:
            self.original_env[key] = os.environ.get(key)
        if key in os.environ:
            del os.environ[key]
        self.current_env.pop(key, None)
    
    def restore_environment(self):
        """Restore original environment."""
        import os
        for key, original_value in self.original_env.items():
            if original_value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = original_value
        
        self.original_env.clear()
        self.current_env.clear()


def setup_mock_paths(monkeypatch, home_dir: Path):
    """Set up common path mocks for testing."""
    from dotz import core
    
    # Mock home directory
    monkeypatch.setattr(core, "HOME_DIR", home_dir)
    
    # Update core paths
    core.update_paths(home_dir)
    
    # Mock environment variables
    monkeypatch.setenv("HOME", str(home_dir))


def create_integration_test_environment(tmp_path: Path) -> Dict[str, Path]:
    """Create a complete test environment for integration tests."""
    # Create directory structure
    home_dir = tmp_path / "home"
    dotz_dir = home_dir / ".dotz"
    work_tree = dotz_dir / "repo"
    templates_dir = dotz_dir / "templates"
    profiles_dir = dotz_dir / "profiles"
    backup_dir = dotz_dir / "backups"
    
    # Create directories
    for directory in [home_dir, dotz_dir, work_tree, templates_dir, profiles_dir, backup_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Initialize Git repository
    repo = Repo.init(str(work_tree))
    with repo.config_writer() as git_config:
        git_config.set_value("user", "name", "Test User")
        git_config.set_value("user", "email", "test@example.com")
    
    # Create initial commit
    readme = work_tree / "README.md"
    readme.write_text("# Test Repository")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    
    return {
        "home": home_dir,
        "dotz": dotz_dir,
        "work_tree": work_tree,
        "templates": templates_dir,
        "profiles": profiles_dir,
        "backups": backup_dir
    }