"""
dotz - A minimal, Git-backed dotfiles manager for Linux.

dotz simplifies tracking, versioning, and synchronizing your configuration
files across machines using Git and automatic symlinking.
"""

__version__ = "0.3.0"
__author__ = "Moustafa Salem"
__email__ = "salemmoustafa442@gmail.com"
__license__ = "GPL-3.0-or-later"

from .core import (
    add_dotfile,
    delete_dotfile,
    get_repo_status,
    init_repo,
    list_tracked_files,
    pull_repo,
    push_repo,
    restore_dotfile,
)

__all__ = [
    "init_repo",
    "add_dotfile",
    "delete_dotfile",
    "restore_dotfile",
    "get_repo_status",
    "list_tracked_files",
    "pull_repo",
    "push_repo",
]
