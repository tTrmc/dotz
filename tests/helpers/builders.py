"""
Test data builders for dotz tests.

This module provides builder classes and factory functions for creating
test data in a consistent and reusable way. These builders help reduce
code duplication and make tests more maintainable.
"""

import json
import tempfile
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from faker import Faker

fake = Faker()


class ConfigBuilder:
    """Builder for dotz configuration objects."""
    
    def __init__(self):
        """Initialize with default configuration."""
        self._config = {
            "file_patterns": {
                "include": [".*", "*.conf", "*.config", "*.cfg", "*.ini"],
                "exclude": [".DS_Store", ".git", ".svn", "*.log", "*.tmp"]
            },
            "search_settings": {
                "recursive": True,
                "case_sensitive": False,
                "follow_symlinks": False
            }
        }
    
    def with_include_patterns(self, patterns: List[str]) -> "ConfigBuilder":
        """Set include patterns."""
        self._config["file_patterns"]["include"] = patterns
        return self
    
    def with_exclude_patterns(self, patterns: List[str]) -> "ConfigBuilder":
        """Set exclude patterns."""
        self._config["file_patterns"]["exclude"] = patterns
        return self
    
    def with_recursive(self, recursive: bool) -> "ConfigBuilder":
        """Set recursive search setting."""
        self._config["search_settings"]["recursive"] = recursive
        return self
    
    def with_case_sensitive(self, case_sensitive: bool) -> "ConfigBuilder":
        """Set case sensitive search setting."""
        self._config["search_settings"]["case_sensitive"] = case_sensitive
        return self
    
    def with_follow_symlinks(self, follow_symlinks: bool) -> "ConfigBuilder":
        """Set follow symlinks setting."""
        self._config["search_settings"]["follow_symlinks"] = follow_symlinks
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the configuration."""
        return self._config.copy()


class TemplateBuilder:
    """Builder for template metadata and files."""
    
    def __init__(self, name: str = None):
        """Initialize with template name."""
        self._name = name or fake.word()
        self._metadata = {
            "name": self._name,
            "description": fake.sentence(),
            "created": datetime.now().isoformat(),
            "files": [],
            "author": fake.name(),
            "version": "1.0.0"
        }
        self._files = {}
    
    def with_name(self, name: str) -> "TemplateBuilder":
        """Set template name."""
        self._name = name
        self._metadata["name"] = name
        return self
    
    def with_description(self, description: str) -> "TemplateBuilder":
        """Set template description."""
        self._metadata["description"] = description
        return self
    
    def with_author(self, author: str) -> "TemplateBuilder":
        """Set template author."""
        self._metadata["author"] = author
        return self
    
    def with_version(self, version: str) -> "TemplateBuilder":
        """Set template version."""
        self._metadata["version"] = version
        return self
    
    def with_created_date(self, date: Union[str, datetime]) -> "TemplateBuilder":
        """Set creation date."""
        if isinstance(date, datetime):
            date = date.isoformat()
        self._metadata["created"] = date
        return self
    
    def with_file(self, filename: str, content: str = None) -> "TemplateBuilder":
        """Add a file to the template."""
        if content is None:
            content = fake.text()
        
        self._files[filename] = content
        if filename not in self._metadata["files"]:
            self._metadata["files"].append(filename)
        return self
    
    def with_files(self, files: Dict[str, str]) -> "TemplateBuilder":
        """Add multiple files to the template."""
        for filename, content in files.items():
            self.with_file(filename, content)
        return self
    
    def build_metadata(self) -> Dict[str, Any]:
        """Build and return template metadata."""
        return self._metadata.copy()
    
    def build_files(self) -> Dict[str, str]:
        """Build and return template files."""
        return self._files.copy()
    
    def create_in_directory(self, base_dir: Path) -> Path:
        """Create the template in the specified directory."""
        template_dir = base_dir / self._name
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Write metadata
        metadata_file = template_dir / "template.json"
        metadata_file.write_text(json.dumps(self._metadata, indent=2))
        
        # Write files
        for filename, content in self._files.items():
            file_path = template_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        return template_dir


class ProfileBuilder:
    """Builder for profile metadata and state."""
    
    def __init__(self, name: str = None):
        """Initialize with profile name."""
        self._name = name or fake.word()
        self._metadata = {
            "name": self._name,
            "description": fake.sentence(),
            "created": datetime.now().isoformat(),
            "last_used": None,
            "template": None,
            "environment": {}
        }
        self._state = {}
    
    def with_name(self, name: str) -> "ProfileBuilder":
        """Set profile name."""
        self._name = name
        self._metadata["name"] = name
        return self
    
    def with_description(self, description: str) -> "ProfileBuilder":
        """Set profile description."""
        self._metadata["description"] = description
        return self
    
    def with_template(self, template: str) -> "ProfileBuilder":
        """Set base template."""
        self._metadata["template"] = template
        return self
    
    def with_environment(self, env_vars: Dict[str, str]) -> "ProfileBuilder":
        """Set environment variables."""
        self._metadata["environment"] = env_vars
        return self
    
    def with_last_used(self, date: Union[str, datetime]) -> "ProfileBuilder":
        """Set last used date."""
        if isinstance(date, datetime):
            date = date.isoformat()
        self._metadata["last_used"] = date
        return self
    
    def with_state(self, state: Dict[str, Any]) -> "ProfileBuilder":
        """Set profile state."""
        self._state = state
        return self
    
    def build_metadata(self) -> Dict[str, Any]:
        """Build and return profile metadata."""
        return self._metadata.copy()
    
    def build_state(self) -> Dict[str, Any]:
        """Build and return profile state."""
        return self._state.copy()
    
    def create_in_directory(self, base_dir: Path) -> Path:
        """Create the profile in the specified directory."""
        profile_dir = base_dir / self._name
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Write metadata
        metadata_file = profile_dir / "profile.json"
        metadata_file.write_text(json.dumps(self._metadata, indent=2))
        
        # Write state if present
        if self._state:
            state_file = profile_dir / "state.json"
            state_file.write_text(json.dumps(self._state, indent=2))
        
        return profile_dir


class DotfileBuilder:
    """Builder for dotfile content and structure."""
    
    def __init__(self):
        """Initialize empty dotfile builder."""
        self._files = {}
    
    def with_bashrc(self, content: str = None) -> "DotfileBuilder":
        """Add .bashrc file."""
        if content is None:
            content = self._generate_bashrc()
        self._files[".bashrc"] = content
        return self
    
    def with_vimrc(self, content: str = None) -> "DotfileBuilder":
        """Add .vimrc file."""
        if content is None:
            content = self._generate_vimrc()
        self._files[".vimrc"] = content
        return self
    
    def with_gitconfig(self, content: str = None) -> "DotfileBuilder":
        """Add .gitconfig file."""
        if content is None:
            content = self._generate_gitconfig()
        self._files[".gitconfig"] = content
        return self
    
    def with_ssh_config(self, content: str = None) -> "DotfileBuilder":
        """Add SSH config file."""
        if content is None:
            content = self._generate_ssh_config()
        self._files[".ssh/config"] = content
        return self
    
    def with_custom_file(self, filename: str, content: str) -> "DotfileBuilder":
        """Add custom file."""
        self._files[filename] = content
        return self
    
    def with_config_directory(self, app_name: str, files: Dict[str, str] = None) -> "DotfileBuilder":
        """Add config directory for an application."""
        if files is None:
            files = {"config.conf": self._generate_config_file()}
        
        for filename, content in files.items():
            full_path = f".config/{app_name}/{filename}"
            self._files[full_path] = content
        return self
    
    def build(self) -> Dict[str, str]:
        """Build and return all files."""
        return self._files.copy()
    
    def create_in_directory(self, base_dir: Path) -> List[Path]:
        """Create all files in the specified directory."""
        created_files = []
        
        for filename, content in self._files.items():
            file_path = base_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            created_files.append(file_path)
        
        return created_files
    
    def _generate_bashrc(self) -> str:
        """Generate realistic .bashrc content."""
        return f"""# {fake.sentence()}
export PATH=$PATH:/usr/local/bin
export EDITOR={fake.random_element(['vim', 'nano', 'code'])}

# Aliases
alias ll='ls -la'
alias grep='grep --color=auto'
alias {fake.word()}='{fake.word()}'

# Custom function
function {fake.word()}() {{
    {fake.sentence()}
}}

# History settings
HISTSIZE=1000
HISTFILESIZE=2000
"""
    
    def _generate_vimrc(self) -> str:
        """Generate realistic .vimrc content."""
        return f""""" {fake.sentence()}
set number
set relativenumber
set tabstop={fake.random_int(2, 8)}
set shiftwidth={fake.random_int(2, 8)}
set expandtab
syntax on
colorscheme {fake.random_element(['desert', 'slate', 'murphy'])}

"" Key mappings
nnoremap <leader>w :w<CR>
nnoremap <leader>q :q<CR>
nnoremap <leader>{fake.random_letter()} :{fake.word()}<CR>
"""
    
    def _generate_gitconfig(self) -> str:
        """Generate realistic .gitconfig content."""
        return f"""[user]
    name = {fake.name()}
    email = {fake.email()}

[core]
    editor = {fake.random_element(['vim', 'nano', 'code'])}
    autocrlf = input

[alias]
    st = status
    co = checkout
    br = branch
    cm = commit
    {fake.word()} = {fake.word()}
    
[push]
    default = simple
"""
    
    def _generate_ssh_config(self) -> str:
        """Generate realistic SSH config content."""
        return f"""Host {fake.domain_word()}
    HostName {fake.domain_name()}
    User {fake.user_name()}
    Port {fake.random_int(22, 9999)}
    IdentityFile ~/.ssh/id_rsa

Host {fake.domain_word()}
    HostName {fake.ipv4()}
    User {fake.user_name()}
    Port {fake.random_int(22, 9999)}
"""
    
    def _generate_config_file(self) -> str:
        """Generate generic config file content."""
        return f"""# {fake.sentence()}
[{fake.word()}]
{fake.word()} = {fake.word()}
{fake.word()} = {fake.random_int(1, 100)}
{fake.word()} = {fake.boolean()}

[{fake.word()}]
{fake.word()} = "{fake.sentence()}"
{fake.word()} = {fake.random_element(['debug', 'info', 'warning', 'error'])}
"""


class BackupBuilder:
    """Builder for backup archives."""
    
    def __init__(self):
        """Initialize backup builder."""
        self._files = {}
        self._timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def with_timestamp(self, timestamp: Union[str, datetime]) -> "BackupBuilder":
        """Set backup timestamp."""
        if isinstance(timestamp, datetime):
            timestamp = timestamp.strftime("%Y%m%d_%H%M%S")
        self._timestamp = timestamp
        return self
    
    def with_file(self, filename: str, content: str) -> "BackupBuilder":
        """Add file to backup."""
        self._files[filename] = content
        return self
    
    def with_files(self, files: Dict[str, str]) -> "BackupBuilder":
        """Add multiple files to backup."""
        self._files.update(files)
        return self
    
    def create_archive(self, backup_dir: Path) -> Path:
        """Create backup archive in specified directory."""
        backup_dir.mkdir(parents=True, exist_ok=True)
        archive_path = backup_dir / f"backup_{self._timestamp}.tar.gz"
        
        with tarfile.open(archive_path, "w:gz") as tar:
            for filename, content in self._files.items():
                # Create temporary file for content
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
                    tmp.write(content)
                    tmp.flush()
                    
                    # Add to archive
                    tar.add(tmp.name, arcname=filename)
                    
                    # Clean up temporary file
                    Path(tmp.name).unlink()
        
        return archive_path


class RepoStatusBuilder:
    """Builder for Git repository status data."""
    
    def __init__(self):
        """Initialize with clean repository status."""
        self._status = {
            "is_dirty": False,
            "untracked_files": [],
            "has_remote": False,
            "ahead": 0,
            "behind": 0,
            "branch": "main"
        }
    
    def with_dirty_state(self, is_dirty: bool = True) -> "RepoStatusBuilder":
        """Set dirty state."""
        self._status["is_dirty"] = is_dirty
        return self
    
    def with_untracked_files(self, files: List[str]) -> "RepoStatusBuilder":
        """Add untracked files."""
        self._status["untracked_files"] = files
        return self
    
    def with_remote(self, has_remote: bool = True) -> "RepoStatusBuilder":
        """Set remote status."""
        self._status["has_remote"] = has_remote
        return self
    
    def with_ahead_behind(self, ahead: int, behind: int) -> "RepoStatusBuilder":
        """Set ahead/behind counts."""
        self._status["ahead"] = ahead
        self._status["behind"] = behind
        return self
    
    def with_branch(self, branch: str) -> "RepoStatusBuilder":
        """Set current branch."""
        self._status["branch"] = branch
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return repository status."""
        return self._status.copy()


def create_sample_dotfiles(count: int = 5) -> Dict[str, str]:
    """Create a set of sample dotfiles with realistic content."""
    builder = DotfileBuilder()
    
    # Add common dotfiles
    builder.with_bashrc().with_vimrc().with_gitconfig()
    
    # Add random additional files
    for i in range(count - 3):
        filename = f".{fake.word()}rc"
        content = fake.text()
        builder.with_custom_file(filename, content)
    
    return builder.build()


def create_sample_config_directory(app_name: str = None) -> Dict[str, str]:
    """Create a sample config directory structure."""
    if app_name is None:
        app_name = fake.word()
    
    builder = DotfileBuilder()
    
    # Create multiple config files for the app
    config_files = {
        "config.conf": fake.text(),
        "settings.json": json.dumps({
            fake.word(): fake.word(),
            fake.word(): fake.random_int(1, 100),
            fake.word(): fake.boolean()
        }),
        "theme.css": f"/* {fake.sentence()} */\\nbody {{ color: {fake.color()}; }}"
    }
    
    builder.with_config_directory(app_name, config_files)
    return builder.build()


def create_test_templates(count: int = 3) -> List[TemplateBuilder]:
    """Create multiple test templates."""
    templates = []
    
    for i in range(count):
        template = (TemplateBuilder(f"template_{i}")
                   .with_description(fake.sentence())
                   .with_author(fake.name())
                   .with_file(".bashrc", fake.text())
                   .with_file(".vimrc", fake.text()))
        
        templates.append(template)
    
    return templates


def create_test_profiles(count: int = 3) -> List[ProfileBuilder]:
    """Create multiple test profiles."""
    profiles = []
    
    for i in range(count):
        profile = (ProfileBuilder(f"profile_{i}")
                  .with_description(fake.sentence())
                  .with_template(f"template_{i}")
                  .with_environment({
                      "EDITOR": fake.random_element(['vim', 'nano', 'code']),
                      "SHELL": fake.random_element(['/bin/bash', '/bin/zsh']),
                      fake.word().upper(): fake.word()
                  }))
        
        profiles.append(profile)
    
    return profiles