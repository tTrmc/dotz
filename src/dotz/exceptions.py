"""Exception classes for dotz - a Git-backed dotfiles manager."""

from typing import List, TypedDict


# Type definitions for structured data
class RepoStatusDict(TypedDict):
    """Type definition for repository status data."""

    untracked: List[str]
    modified: List[str]
    staged: List[str]
    unpushed: List[str]
    untracked_home_dotfiles: List[str]


class ValidationResultsDict(TypedDict):
    """Type definition for symlink validation results."""

    valid: List[str]
    broken: List[str]
    missing: List[str]
    wrong_target: List[str]
    not_symlink: List[str]
    repaired: List[str]
    repair_failed: List[str]


class OperationResultDict(TypedDict):
    """Type definition for operation results (add/restore)."""

    success: int
    failed: int


class TemplateMetadataDict(TypedDict):
    """Type definition for template metadata."""

    name: str
    description: str
    created: str
    files: List[str]
    file_count: int
    created_by: str
    version: str
    total_size: int  # Added dynamically in get_template_info
    path: str  # Added dynamically in list_templates


class ProfileMetadataDict(TypedDict):
    """Type definition for profile metadata."""

    name: str
    description: str
    environment: str
    created: str
    created_by: str
    version: str
    last_used: str
    active: bool
    file_count: int  # Added dynamically in get_profile_info
    total_size: int  # Added dynamically in get_profile_info
    path: str  # Added dynamically in list_profiles


class DotzError(Exception):
    """Base exception for all dotz-related errors."""

    pass


class DotzRepositoryError(DotzError):
    """Errors related to dotz repository operations."""

    pass


class DotzRepositoryNotFoundError(DotzRepositoryError):
    """Raised when dotz repository is not initialized or not found."""

    pass


class DotzRepositoryCorruptedError(DotzRepositoryError):
    """Raised when dotz repository is in an invalid state."""

    pass


class DotzFileOperationError(DotzError):
    """Errors related to file operations."""

    pass


class DotzFileNotFoundError(DotzFileOperationError):
    """Raised when a file or directory cannot be found."""

    pass


class DotzSymlinkError(DotzFileOperationError):
    """Errors related to symlink operations."""

    pass


class DotzBackupError(DotzError):
    """Errors related to backup operations."""

    pass


class DotzConfigurationError(DotzError):
    """Errors related to configuration management."""

    pass


class DotzTemplateError(DotzError):
    """Errors related to template operations."""

    pass


class DotzProfileError(DotzError):
    """Errors related to profile operations."""

    pass


class DotzGitError(DotzRepositoryError):
    """Errors related to Git operations."""

    pass


class DotzSecurityError(DotzError):
    """Errors related to security validation (e.g., path traversal)."""

    pass


class DotzArchiveError(DotzError):
    """Errors related to archive operations (tar, etc)."""

    pass


class DotzValidationError(DotzError):
    """Errors related to input or data validation."""

    pass
