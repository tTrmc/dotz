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
from .templates import (
    apply_template,
    create_profile,
    create_template,
    delete_profile,
    delete_template,
    get_active_profile,
    list_profiles,
    list_templates,
    switch_profile,
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
    # Template and Profile functions
    "create_template",
    "list_templates",
    "apply_template",
    "delete_template",
    "create_profile",
    "list_profiles",
    "switch_profile",
    "get_active_profile",
    "delete_profile",
]
