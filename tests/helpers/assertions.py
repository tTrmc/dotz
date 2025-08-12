"""
Custom assertion helpers for dotz tests.

This module provides specialized assertion functions that make test code
more readable and provide better error messages for common test patterns.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pytest


def assert_file_exists(file_path: Union[str, Path], message: str = "") -> None:
    """
    Assert that a file exists.
    
    Args:
        file_path: Path to the file to check
        message: Optional custom error message
    """
    path = Path(file_path)
    assert path.exists(), f"File does not exist: {path} {message}".strip()
    assert path.is_file(), f"Path exists but is not a file: {path} {message}".strip()


def assert_file_not_exists(file_path: Union[str, Path], message: str = "") -> None:
    """
    Assert that a file does not exist.
    
    Args:
        file_path: Path to the file to check
        message: Optional custom error message
    """
    path = Path(file_path)
    assert not path.exists(), f"File should not exist: {path} {message}".strip()


def assert_directory_exists(dir_path: Union[str, Path], message: str = "") -> None:
    """
    Assert that a directory exists.
    
    Args:
        dir_path: Path to the directory to check
        message: Optional custom error message
    """
    path = Path(dir_path)
    assert path.exists(), f"Directory does not exist: {path} {message}".strip()
    assert path.is_dir(), f"Path exists but is not a directory: {path} {message}".strip()


def assert_symlink_correct(symlink_path: Union[str, Path], target_path: Union[str, Path], message: str = "") -> None:
    """
    Assert that a symlink points to the correct target.
    
    Args:
        symlink_path: Path to the symlink
        target_path: Expected target path
        message: Optional custom error message
    """
    symlink = Path(symlink_path)
    target = Path(target_path)
    
    assert symlink.exists(), f"Symlink does not exist: {symlink} {message}".strip()
    assert symlink.is_symlink(), f"Path is not a symlink: {symlink} {message}".strip()
    
    resolved_symlink = symlink.resolve()
    resolved_target = target.resolve()
    
    assert resolved_symlink == resolved_target, (
        f"Symlink {symlink} points to {resolved_symlink}, "
        f"expected {resolved_target} {message}".strip()
    )


def assert_file_content(file_path: Union[str, Path], expected_content: str, message: str = "") -> None:
    """
    Assert that a file contains the expected content.
    
    Args:
        file_path: Path to the file to check
        expected_content: Expected file content
        message: Optional custom error message
    """
    path = Path(file_path)
    assert_file_exists(path)
    
    actual_content = path.read_text()
    assert actual_content == expected_content, (
        f"File content mismatch in {path}:\n"
        f"Expected: {repr(expected_content)}\n"
        f"Actual: {repr(actual_content)} {message}".strip()
    )


def assert_file_contains(file_path: Union[str, Path], substring: str, message: str = "") -> None:
    """
    Assert that a file contains a specific substring.
    
    Args:
        file_path: Path to the file to check
        substring: Substring that should be present
        message: Optional custom error message
    """
    path = Path(file_path)
    assert_file_exists(path)
    
    content = path.read_text()
    assert substring in content, (
        f"File {path} does not contain '{substring}' {message}".strip()
    )


def assert_json_file_valid(file_path: Union[str, Path], message: str = "") -> Dict[str, Any]:
    """
    Assert that a file contains valid JSON and return the parsed data.
    
    Args:
        file_path: Path to the JSON file
        message: Optional custom error message
        
    Returns:
        Parsed JSON data
    """
    path = Path(file_path)
    assert_file_exists(path)
    
    try:
        with open(path) as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in {path}: {e} {message}".strip())


def assert_json_content(file_path: Union[str, Path], expected_data: Dict[str, Any], message: str = "") -> None:
    """
    Assert that a JSON file contains the expected data.
    
    Args:
        file_path: Path to the JSON file
        expected_data: Expected JSON data
        message: Optional custom error message
    """
    actual_data = assert_json_file_valid(file_path)
    assert actual_data == expected_data, (
        f"JSON content mismatch in {file_path}:\n"
        f"Expected: {expected_data}\n"
        f"Actual: {actual_data} {message}".strip()
    )


def assert_git_committed(repo_path: Union[str, Path], commit_message: str = None, message: str = "") -> None:
    """
    Assert that changes have been committed to a Git repository.
    
    Args:
        repo_path: Path to the Git repository
        commit_message: Optional expected commit message
        message: Optional custom error message
    """
    from git import Repo
    
    repo = Repo(str(repo_path))
    
    # Check that repository is not dirty
    assert not repo.is_dirty(), f"Repository has uncommitted changes {message}".strip()
    
    # Check commit message if provided
    if commit_message:
        latest_commit = repo.head.commit
        actual_message = latest_commit.message.strip()
        assert commit_message in actual_message, (
            f"Expected commit message '{commit_message}' not found in '{actual_message}' {message}".strip()
        )


def assert_git_clean(repo_path: Union[str, Path], message: str = "") -> None:
    """
    Assert that a Git repository is clean (no uncommitted changes).
    
    Args:
        repo_path: Path to the Git repository
        message: Optional custom error message
    """
    from git import Repo
    
    repo = Repo(str(repo_path))
    
    assert not repo.is_dirty(), f"Repository has uncommitted changes {message}".strip()
    assert not repo.untracked_files, f"Repository has untracked files: {repo.untracked_files} {message}".strip()


def assert_config_valid(config_data: Dict[str, Any], message: str = "") -> None:
    """
    Assert that configuration data has the expected structure.
    
    Args:
        config_data: Configuration data to validate
        message: Optional custom error message
    """
    required_keys = ["file_patterns", "search_settings"]
    
    for key in required_keys:
        assert key in config_data, f"Missing required config key: {key} {message}".strip()
    
    # Check file_patterns structure
    file_patterns = config_data["file_patterns"]
    assert "include" in file_patterns, f"Missing 'include' in file_patterns {message}".strip()
    assert "exclude" in file_patterns, f"Missing 'exclude' in file_patterns {message}".strip()
    assert isinstance(file_patterns["include"], list), f"'include' must be a list {message}".strip()
    assert isinstance(file_patterns["exclude"], list), f"'exclude' must be a list {message}".strip()
    
    # Check search_settings structure
    search_settings = config_data["search_settings"]
    required_search_keys = ["recursive", "case_sensitive", "follow_symlinks"]
    
    for key in required_search_keys:
        assert key in search_settings, f"Missing '{key}' in search_settings {message}".strip()
        assert isinstance(search_settings[key], bool), f"'{key}' must be boolean {message}".strip()


def assert_backup_valid(backup_path: Union[str, Path], expected_files: List[str] = None, message: str = "") -> None:
    """
    Assert that a backup archive is valid and contains expected files.
    
    Args:
        backup_path: Path to the backup archive
        expected_files: Optional list of files that should be in the backup
        message: Optional custom error message
    """
    import tarfile
    
    path = Path(backup_path)
    assert_file_exists(path)
    
    # Check that it's a valid tar.gz file
    try:
        with tarfile.open(path, "r:gz") as tar:
            archive_files = tar.getnames()
    except (tarfile.ReadError, tarfile.CompressionError) as e:
        pytest.fail(f"Invalid backup archive {path}: {e} {message}".strip())
    
    # Check expected files if provided
    if expected_files:
        for expected_file in expected_files:
            assert expected_file in archive_files, (
                f"Expected file '{expected_file}' not found in backup {path} {message}".strip()
            )


def assert_template_valid(template_dir: Union[str, Path], expected_files: List[str] = None, message: str = "") -> None:
    """
    Assert that a template directory is valid.
    
    Args:
        template_dir: Path to the template directory
        expected_files: Optional list of files that should be in the template
        message: Optional custom error message
    """
    path = Path(template_dir)
    assert_directory_exists(path)
    
    # Check for metadata file
    metadata_file = path / "template.json"
    assert_file_exists(metadata_file, f"Template metadata missing {message}")
    
    # Validate metadata
    metadata = assert_json_file_valid(metadata_file)
    required_metadata_keys = ["name", "description", "files"]
    
    for key in required_metadata_keys:
        assert key in metadata, f"Missing '{key}' in template metadata {message}".strip()
    
    # Check template files if provided
    if expected_files:
        for expected_file in expected_files:
            file_path = path / expected_file
            assert_file_exists(file_path, f"Template file missing {message}")


def assert_profile_valid(profile_dir: Union[str, Path], message: str = "") -> None:
    """
    Assert that a profile directory is valid.
    
    Args:
        profile_dir: Path to the profile directory
        message: Optional custom error message
    """
    path = Path(profile_dir)
    assert_directory_exists(path)
    
    # Check for metadata file
    metadata_file = path / "profile.json"
    assert_file_exists(metadata_file, f"Profile metadata missing {message}")
    
    # Validate metadata
    metadata = assert_json_file_valid(metadata_file)
    required_metadata_keys = ["name", "description"]
    
    for key in required_metadata_keys:
        assert key in metadata, f"Missing '{key}' in profile metadata {message}".strip()


def assert_operation_result(result: Dict[str, Any], expected_success: bool = True, message: str = "") -> None:
    """
    Assert that an operation result has the expected structure and success status.
    
    Args:
        result: Operation result dictionary
        expected_success: Whether the operation should have succeeded
        message: Optional custom error message
    """
    assert isinstance(result, dict), f"Result must be a dictionary {message}".strip()
    assert "success" in result, f"Result missing 'success' key {message}".strip()
    
    actual_success = result["success"]
    assert actual_success == expected_success, (
        f"Expected success={expected_success}, got {actual_success} {message}".strip()
    )
    
    if expected_success:
        # Successful operations should have a message
        assert "message" in result or "files_added" in result or "commit_hash" in result, (
            f"Successful operation should have additional info {message}".strip()
        )
    else:
        # Failed operations might have error details
        if "error" in result:
            assert isinstance(result["error"], str), f"Error should be a string {message}".strip()


def assert_files_equal(file1: Union[str, Path], file2: Union[str, Path], message: str = "") -> None:
    """
    Assert that two files have identical content.
    
    Args:
        file1: Path to first file
        file2: Path to second file
        message: Optional custom error message
    """
    path1, path2 = Path(file1), Path(file2)
    
    assert_file_exists(path1)
    assert_file_exists(path2)
    
    content1 = path1.read_text()
    content2 = path2.read_text()
    
    assert content1 == content2, (
        f"Files {path1} and {path2} have different content {message}".strip()
    )


def assert_list_contains_all(actual_list: List[Any], expected_items: List[Any], message: str = "") -> None:
    """
    Assert that a list contains all expected items.
    
    Args:
        actual_list: The actual list to check
        expected_items: Items that should be present
        message: Optional custom error message
    """
    missing_items = set(expected_items) - set(actual_list)
    assert not missing_items, (
        f"List missing expected items: {missing_items} {message}".strip()
    )


def assert_list_contains_none(actual_list: List[Any], unexpected_items: List[Any], message: str = "") -> None:
    """
    Assert that a list contains none of the unexpected items.
    
    Args:
        actual_list: The actual list to check
        unexpected_items: Items that should not be present
        message: Optional custom error message
    """
    found_items = set(unexpected_items) & set(actual_list)
    assert not found_items, (
        f"List contains unexpected items: {found_items} {message}".strip()
    )