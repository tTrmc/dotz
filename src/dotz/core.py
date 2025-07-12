"""Core functionality for dotz - a Git-backed dotfiles manager."""

import fnmatch
import json
import os
import shutil
import tarfile
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from git import GitCommandError, Repo
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.status import Status

# Constants
DOTZ_DIR_NAME = ".dotz"
REPO_DIR_NAME = "repo"
TRACKED_DIRS_FILENAME = "tracked_dirs.json"
CONFIG_FILENAME = "config.json"
BACKUP_DIR_NAME = "backups"
PROGRESS_THRESHOLD = 50  # Show progress bar for operations with 50+ items

# Global console instance
console = Console()


# ============================================================================
# PATH MANAGEMENT
# ============================================================================


def get_home_dir() -> Path:
    """Get the home directory, respecting environment variables for testing."""
    # Check for test override first
    if "HOME" in os.environ:
        return Path(os.environ["HOME"])
    return Path.home()


def get_dotz_paths(home_dir: Optional[Path] = None) -> Dict[str, Path]:
    """Get all dotz-related paths based on home directory."""
    if home_dir is None:
        home_dir = get_home_dir()

    dotz_dir = home_dir / DOTZ_DIR_NAME
    work_tree = dotz_dir / REPO_DIR_NAME
    tracked_dirs_file = dotz_dir / TRACKED_DIRS_FILENAME
    config_file = dotz_dir / CONFIG_FILENAME
    backup_dir = dotz_dir / BACKUP_DIR_NAME

    return {
        "home": home_dir,
        "dotz_dir": dotz_dir,
        "work_tree": work_tree,
        "tracked_dirs_file": tracked_dirs_file,
        "config_file": config_file,
        "backup_dir": backup_dir,
    }


def update_paths(home_dir: Optional[Path] = None) -> None:
    """Update global paths. Useful for testing or when HOME changes."""
    global HOME, DOTZ_DIR, WORK_TREE, TRACKED_DIRS_FILE, CONFIG_FILE, BACKUP_DIR
    paths = get_dotz_paths(home_dir)
    HOME = paths["home"]
    DOTZ_DIR = paths["dotz_dir"]
    WORK_TREE = paths["work_tree"]
    TRACKED_DIRS_FILE = paths["tracked_dirs_file"]
    CONFIG_FILE = paths["config_file"]
    BACKUP_DIR = paths["backup_dir"]


# ============================================================================
# GLOBAL CONFIGURATION AND PATHS
# ============================================================================

# Default configuration
DEFAULT_CONFIG = {
    "file_patterns": {
        "include": [
            ".*",  # dotfiles (files starting with .)
            "*.conf",  # configuration files
            "*.config",  # config files
            "*.cfg",  # cfg files
            "*.ini",  # ini files
            "*.toml",  # toml files
            "*.yaml",  # yaml files
            "*.yml",  # yml files
            "*.json",  # json config files
        ],
        "exclude": [
            ".DS_Store",  # macOS system files
            ".Trash*",  # Trash folders
            ".cache",  # cache directories
            ".git",  # git directories
            ".svn",  # svn directories
            "*.log",  # log files
            "*.tmp",  # temporary files
        ],
    },
    "search_settings": {
        "recursive": True,  # default recursive search
        "case_sensitive": False,  # case insensitive pattern matching
        "follow_symlinks": False,  # don't follow symlinks by default
    },
}

# Global paths - can be overridden for testing
_paths = get_dotz_paths()
HOME = _paths["home"]
DOTZ_DIR = _paths["dotz_dir"]
WORK_TREE = _paths["work_tree"]
TRACKED_DIRS_FILE = _paths["tracked_dirs_file"]
CONFIG_FILE = _paths["config_file"]
BACKUP_DIR = _paths["backup_dir"]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def ensure_repo() -> Repo:
    """Ensure that a dotz repository exists and return it."""
    try:
        return Repo(str(WORK_TREE))
    except Exception:
        typer.secho(
            "Error: Dotz repository not initialized. Run 'dotz init' first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)


def count_files_in_directory(path: Path) -> int:
    """Count all files recursively in a directory."""
    if path.is_file():
        return 1
    elif path.is_dir():
        count = 0
        for item in path.rglob("*"):
            if item.is_file():
                count += 1
        return count
    return 0


def parse_backup_filename(backup_name: str) -> tuple[str, str, str]:
    """Parse backup filename to extract original path, operation, and timestamp.

    Returns:
        Tuple of (original_path, operation, formatted_timestamp)
    """
    # Remove .tar.gz extension if present
    name = backup_name
    if name.endswith(".tar.gz"):
        name = name[:-7]

    parts = name.split("_")
    if len(parts) < 3:
        return backup_name, "unknown", "unknown"

    # Remove timestamp parts from the end (format: YYYYMMDD_HHMMSS)
    remaining_parts = parts[:]
    if (
        len(remaining_parts) >= 2
        and remaining_parts[-1].isdigit()
        and len(remaining_parts[-1]) == 6
        and remaining_parts[-2].isdigit()
        and len(remaining_parts[-2]) == 8
    ):
        timestamp = f"{remaining_parts[-2]}_{remaining_parts[-1]}"
        remaining_parts = remaining_parts[:-2]
    else:
        timestamp = "unknown"

    # Remove operation part (should be last now)
    if remaining_parts:
        operation = remaining_parts[-1]
        remaining_parts = remaining_parts[:-1]
    else:
        operation = "unknown"

    if not remaining_parts:
        return backup_name, operation, timestamp

    original_path = "/".join(remaining_parts)

    # Format timestamp for display
    try:
        if timestamp != "unknown":
            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            formatted_time = timestamp
    except ValueError:
        formatted_time = timestamp

    return original_path, operation, formatted_time


# ============================================================================
# TRACKED DIRECTORY MANAGEMENT
# ============================================================================


def save_tracked_dir(dir_path: Path) -> None:
    """Add a directory to the tracked_dirs.json file."""
    if not TRACKED_DIRS_FILE.exists():
        tracked = []
    else:
        with open(TRACKED_DIRS_FILE, "r") as f:
            tracked = json.load(f)
    dir_str = str(dir_path)
    if dir_str not in tracked:
        tracked.append(dir_str)
        with open(TRACKED_DIRS_FILE, "w") as f:
            json.dump(tracked, f)


def remove_tracked_dir(dir_path: Path) -> None:
    """Remove a directory from the tracked_dirs.json file."""
    if not TRACKED_DIRS_FILE.exists():
        return
    with open(TRACKED_DIRS_FILE, "r") as f:
        tracked = json.load(f)
    dir_str = str(dir_path)
    if dir_str in tracked:
        tracked.remove(dir_str)
        with open(TRACKED_DIRS_FILE, "w") as f:
            json.dump(tracked, f)


# ============================================================================
# REPOSITORY INITIALIZATION AND MANAGEMENT
# ============================================================================


def init_repo(remote: str = "", quiet: bool = False) -> bool:
    if DOTZ_DIR.exists():
        if not quiet:
            typer.secho("Dotz already initialized", fg=typer.colors.YELLOW)
        return False

    if not quiet:
        typer.secho("Initializing dotz repository...", fg=typer.colors.BLUE)
    DOTZ_DIR.mkdir()
    WORK_TREE.mkdir()

    repo = Repo.init(str(WORK_TREE))
    repo.git.config("user.name", "dotz")
    repo.git.config("user.email", "dotz@example.com")
    if not quiet:
        typer.secho("Creating initial commit...", fg=typer.colors.BLUE)
    repo.git.commit("--allow-empty", "-m", "Initial commit")
    if not quiet:
        typer.secho("Initial commit created", fg=typer.colors.GREEN)

    # Create default configuration file
    save_config(DEFAULT_CONFIG)

    # Create tracked directories file
    TRACKED_DIRS_FILE.write_text("[]")

    # Create backups directory
    BACKUP_DIR.mkdir(exist_ok=True)

    if remote:
        repo.create_remote("origin", remote)
        if not quiet:
            typer.secho(
                "WARNING: Ensure your remote repository is private for sensitive data",
                fg=typer.colors.YELLOW,
                bold=True,
            )

    if not quiet:
        typer.secho("Dotz repository initialized successfully", fg=typer.colors.GREEN)
    return True


# ============================================================================
# DOTFILE MANAGEMENT
# ============================================================================


def add_dotfile(
    path: Path, push: bool = False, quiet: bool = False, recursive: bool = True
) -> bool:
    """
    Add a file or directory to dotz, then symlink it in your home directory.
    Set quiet=True to suppress typer.secho output (for watcher).
    """
    repo = ensure_repo()
    src = (HOME / path).expanduser()

    if not src.exists():
        if not quiet:
            typer.secho(f"Error: {src} not found", fg=typer.colors.RED, err=True)
        return False

    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Prevent SameFileError and redundant symlinking
    if src.is_symlink() and src.resolve() == dest.resolve():
        return True
    if src.resolve() == dest.resolve():
        return True

    if src.is_file():
        try:
            shutil.copy2(src, dest)
            tracked_path = dest.relative_to(WORK_TREE).as_posix()
            repo.index.add([tracked_path])
            repo.index.commit(f"Add {rel}")
            src.unlink()
            src.symlink_to(dest)
            if not quiet:
                typer.secho(f"Added {rel}", fg=typer.colors.GREEN)
        except OSError as e:
            if not quiet:
                typer.secho(
                    f"Error: Could not add {rel}: {e}",
                    fg=typer.colors.RED,
                    err=True,
                )
            return False

    elif src.is_dir():
        save_tracked_dir(src)
        config = load_config()
        dotfiles = find_config_files(src, config, recursive)
        if not dotfiles:
            if not quiet:
                typer.secho(f"No config files found in {rel}", fg=typer.colors.YELLOW)
            return True

        # Copy the entire directory structure to dotz repo
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)

        # Add all files to git
        for df in dotfiles:
            sub_rel = df.relative_to(HOME)
            tracked_path = (WORK_TREE / sub_rel).relative_to(WORK_TREE).as_posix()
            repo.index.add([tracked_path])

        repo.index.commit(f"Add dotfiles in {rel}")

        # Replace original directory with symlink
        shutil.rmtree(src)
        src.symlink_to(dest)

        if not quiet:
            typer.secho(
                f"Added {len(dotfiles)} dotfiles from {rel}", fg=typer.colors.GREEN
            )

    else:
        if not quiet:
            typer.secho(
                f"Error: {src} is not a regular file or directory",
                fg=typer.colors.RED,
                err=True,
            )
        return False

    if push:
        try:
            origin = repo.remote("origin")
            branch = repo.active_branch.name
            result = origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
            if any(r.flags & r.ERROR for r in result):
                for r in result:
                    if r.flags & r.ERROR and not quiet:
                        typer.secho(
                            f"Error pushing to origin: {r.summary}",
                            fg=typer.colors.RED,
                            err=True,
                        )
                return False
            if not quiet:
                typer.secho("✓ Pushed to origin", fg=typer.colors.GREEN)
        except GitCommandError as e:
            if not quiet:
                typer.secho(
                    f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True
                )
            return False
    return True


def delete_dotfile(paths: List[Path], push: bool = False, quiet: bool = False) -> bool:
    """Delete multiple dotfiles and their symlinks."""
    repo = ensure_repo()
    all_success = True
    removed_files = []

    for path in paths:
        src = (HOME / path).expanduser()

        if not src.is_symlink():
            if not quiet:
                typer.secho(
                    f"Error: {src} is not a symlink managed by dotz",
                    fg=typer.colors.RED,
                    err=True,
                )
            all_success = False
            continue

        rel = src.relative_to(HOME)
        dest = WORK_TREE / rel

        if not dest.exists():
            if not quiet:
                typer.secho(
                    f"Error: {dest} does not exist in the dotz repository",
                    fg=typer.colors.RED,
                    err=True,
                )
            all_success = False
            continue

        # Remove symlink
        src.unlink()

        # Remove from git repo
        if dest.is_file():
            dest.unlink()
            tracked_path = dest.relative_to(WORK_TREE).as_posix()
            repo.index.remove([tracked_path])
        elif dest.is_dir():
            shutil.rmtree(dest)
            tracked_path = dest.relative_to(WORK_TREE).as_posix()
            repo.index.remove([tracked_path], r=True)
            remove_tracked_dir(src)

        removed_files.append(rel)
        if not quiet:
            typer.secho(f"Removed {rel}", fg=typer.colors.GREEN)

    # Commit all removals in one commit
    if removed_files:
        if len(removed_files) == 1:
            commit_msg = f"Remove {removed_files[0]}"
        else:
            commit_msg = f"Remove {len(removed_files)} files"
        repo.index.commit(commit_msg)

        if push:
            try:
                origin = repo.remote("origin")
                branch = repo.active_branch.name
                result = origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
                if any(r.flags & r.ERROR for r in result):
                    for r in result:
                        if r.flags & r.ERROR and not quiet:
                            typer.secho(
                                f"Error pushing to origin: {r.summary}",
                                fg=typer.colors.RED,
                                err=True,
                            )
                    return False
                if not quiet:
                    typer.secho("✓ Pushed to origin", fg=typer.colors.GREEN)
            except GitCommandError as e:
                if not quiet:
                    typer.secho(
                        f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True
                    )
                return False

    return all_success


def restore_dotfile(path: Path, quiet: bool = False, push: bool = False) -> bool:
    ensure_repo()
    src = (HOME / path).expanduser()
    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel

    # Check if the file/directory is tracked (exists in the repo)
    if not dest.exists():
        if not quiet:
            typer.secho(
                f"Error: {rel} is not tracked by dotz.",
                fg=typer.colors.RED,
                err=True,
            )
        return False

    # If there's already something at src, backup and remove it
    if src.is_symlink():
        src.unlink()
    elif src.exists():
        # Create backup before removing
        create_backup(src, operation="restore", quiet=quiet)
        if src.is_file():
            src.unlink()
        elif src.is_dir():
            shutil.rmtree(src)

    # Create symlink from home to repo (not a copy)
    src.symlink_to(dest)
    if not quiet:
        typer.secho(f"Restored {rel}", fg=typer.colors.GREEN)

    if push:
        try:
            repo = ensure_repo()
            origin = repo.remote("origin")
            branch = repo.active_branch.name
            result = origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
            if any(r.flags & r.ERROR for r in result):
                for r in result:
                    if r.flags & r.ERROR and not quiet:
                        typer.secho(
                            f"Error pushing to origin: {r.summary}",
                            fg=typer.colors.RED,
                            err=True,
                        )
                return False
            if not quiet:
                typer.secho("✓ Pushed to origin", fg=typer.colors.GREEN)
        except GitCommandError as e:
            if not quiet:
                typer.secho(
                    f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True
                )
            return False
    return True


def pull_repo(quiet: bool = False) -> bool:
    repo = ensure_repo()
    # Check if 'origin' remote exists
    if "origin" not in [r.name for r in repo.remotes]:
        if not quiet:
            typer.secho(
                "Error: No 'origin' remote found. Please set one with "
                "`dotz init --remote <URL>` or `git remote add origin <URL>`.",
                fg=typer.colors.RED,
                err=True,
            )
        return False

    origin = repo.remote("origin")
    try:
        origin.pull()
        if not quiet:
            typer.secho("Pulled latest changes from origin", fg=typer.colors.GREEN)
        return True
    except GitCommandError as e:
        msg = str(e)
        if "no tracking information" in msg.lower():
            typer.secho(
                "Error: No tracking branch set for this branch.\n"
                "Run: git -C ~/.dotz/repo branch "
                "--set-upstream-to=origin/<branch> <branch>",
                fg=typer.colors.RED,
                err=True,
            )
        elif (
            "divergent branches" in msg.lower()
            or "need to specify how to reconcile divergent branches" in msg.lower()
        ):
            typer.secho(
                "Error: Local and remote branches have diverged.\n"
                "You need to reconcile them. Try one of the following:\n"
                "  git -C ~/.dotz/repo pull --rebase\n"
                "  git -C ~/.dotz/repo pull --no-rebase\n"
                "  git -C ~/.dotz/repo pull --ff-only",
                fg=typer.colors.RED,
                err=True,
            )
        else:
            typer.secho(
                f"Error pulling from origin: {e}", fg=typer.colors.RED, err=True
            )
        return False


def push_repo(quiet: bool = False) -> bool:
    repo = ensure_repo()

    # Make sure there is an 'origin' remote
    if "origin" not in [r.name for r in repo.remotes]:
        if not quiet:
            typer.secho(
                "Error: No 'origin' remote found. Please set one with "
                "`dotz init --remote <URL>` or `git remote add origin <URL>`.",
                fg=typer.colors.RED,
                err=True,
            )
        return False

    origin = repo.remote("origin")
    branch = repo.active_branch.name
    try:
        result = origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
        # Set upstream if not already set
        tracking_branch = repo.active_branch.tracking_branch()
        if tracking_branch is None:
            repo.git.branch("--set-upstream-to=origin/{}".format(branch), branch)
            if not quiet:
                typer.secho(
                    f"✓ Set upstream tracking branch to origin/{branch}",
                    fg=typer.colors.GREEN,
                )
        # Check for push errors
        if any(r.flags & r.ERROR for r in result):
            for r in result:
                if r.flags & r.ERROR and not quiet:
                    summary = r.summary.lower()
                    if "non-fast-forward" in summary or "rejected" in summary:
                        typer.secho(
                            "Error: Push rejected (non-fast-forward). You may "
                            "need to pull first:\n"
                            "  git -C ~/.dotz/repo pull --rebase\n"
                            "Or resolve conflicts and try again.",
                            fg=typer.colors.RED,
                            err=True,
                        )
                    else:
                        typer.secho(
                            f"Error pushing to origin: {r.summary}",
                            fg=typer.colors.RED,
                            err=True,
                        )
            return False
        if not quiet:
            typer.secho("Pushed local commits to origin", fg=typer.colors.GREEN)
        return True
    except GitCommandError as e:
        msg = str(e)
        if (
            "no upstream branch" in msg.lower()
            or "no tracking information" in msg.lower()
        ):
            typer.secho(
                "Error: No upstream branch set for this branch.\n"
                "Run: git -C ~/.dotz/repo branch "
                "--set-upstream-to=origin/<branch> <branch>",
                fg=typer.colors.RED,
                err=True,
            )
        else:
            typer.secho(f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True)
        return False


def get_repo_status() -> Dict[str, List[str]]:
    repo = ensure_repo()
    untracked = list(repo.untracked_files)
    modified = [
        item.a_path for item in repo.index.diff(None) if item.a_path is not None
    ]
    staged = [
        item.a_path for item in repo.index.diff("HEAD") if item.a_path is not None
    ]

    # Unpushed changes
    unpushed = []
    if "origin" in [r.name for r in repo.remotes]:
        branch = repo.active_branch.name
        remote_branch = f"origin/{branch}"
        try:
            unpushed = [
                diff_item.a_path
                for diff_item in repo.index.diff(remote_branch)
                if diff_item.a_path is not None
            ]
        except Exception:  # nosec B110
            pass

    # Dotfiles in $HOME not tracked by dotz
    config = load_config()
    home_config_files = find_config_files(HOME, config, recursive=False)
    home_config_file_names = [f.name for f in home_config_files]
    tracked_files = set(repo.git.ls_files().splitlines())
    untracked_home_dotfiles = [
        f for f in home_config_file_names if f not in tracked_files
    ]

    return {
        "untracked": untracked,
        "modified": modified,
        "staged": staged,
        "unpushed": unpushed,
        "untracked_home_dotfiles": untracked_home_dotfiles,
    }


def list_tracked_files() -> List[str]:
    repo = ensure_repo()
    files_output: str = repo.git.ls_files()
    return files_output.splitlines()


# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================


def load_config() -> Dict[str, Any]:
    """Load configuration from config file, or return default if not exists."""
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        # Merge with defaults to ensure all keys exist
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)

        # Ensure nested dictionaries are also merged
        if "file_patterns" in config and isinstance(config["file_patterns"], dict):
            file_patterns = merged_config["file_patterns"]
            if isinstance(file_patterns, dict):
                file_patterns.update(config["file_patterns"])
        if "search_settings" in config and isinstance(config["search_settings"], dict):
            search_settings = merged_config["search_settings"]
            if isinstance(search_settings, dict):
                search_settings.update(config["search_settings"])

        return merged_config
    except (json.JSONDecodeError, KeyError) as e:
        typer.secho(
            f"Warning: Error reading config file: {e}. Using defaults.",
            fg=typer.colors.YELLOW,
            err=True,
        )
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to config file."""
    DOTZ_DIR.mkdir(exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def matches_patterns(
    filename: str,
    include_patterns: List[str],
    exclude_patterns: List[str],
    case_sensitive: bool = False,
) -> bool:
    """
    Check if a filename matches the include patterns and doesn't match exclude
    patterns.
    """
    if not case_sensitive:
        filename = filename.lower()
        include_patterns = [p.lower() for p in include_patterns]
        exclude_patterns = [p.lower() for p in exclude_patterns]

    # Check if file matches any include pattern
    included = any(fnmatch.fnmatch(filename, pattern) for pattern in include_patterns)

    # Check if file matches any exclude pattern
    excluded = any(fnmatch.fnmatch(filename, pattern) for pattern in exclude_patterns)

    return included and not excluded


def find_config_files(
    directory: Path, config: Optional[Dict[str, Any]] = None, recursive: bool = True
) -> List[Path]:
    """Find files matching the configured patterns in a directory."""
    if config is None:
        config = load_config()

    include_patterns = config["file_patterns"]["include"]
    exclude_patterns = config["file_patterns"]["exclude"]
    case_sensitive = config["search_settings"]["case_sensitive"]
    follow_symlinks = config["search_settings"]["follow_symlinks"]

    found_files = []
    directory = Path(directory)

    if recursive:
        iterator = directory.rglob("*")
    else:
        iterator = directory.iterdir()

    for item in iterator:
        if not follow_symlinks and item.is_symlink():
            continue

        if item.is_file():
            if matches_patterns(
                item.name, include_patterns, exclude_patterns, case_sensitive
            ):
                found_files.append(item)

    return found_files


def get_config_value(key_path: str, quiet: bool = False) -> Any:
    """Get a configuration value by key path (e.g., 'file_patterns.include')."""
    config = load_config()
    keys = key_path.split(".")
    value = config

    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        if not quiet:
            typer.secho(
                f"Error: Configuration key '{key_path}' not found.",
                fg=typer.colors.RED,
                err=True,
            )
        return None


def set_config_value(key_path: str, value: Any, quiet: bool = False) -> bool:
    """Set a configuration value by key path."""
    config = load_config()
    keys = key_path.split(".")

    # Navigate to the parent of the final key
    current = config
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Set the final value
    try:
        # Try to parse as JSON for complex values
        if isinstance(value, str) and (value.startswith("[") or value.startswith("{")):
            parsed_value = json.loads(value)
            current[keys[-1]] = parsed_value
        elif value.lower() in ("true", "false"):
            current[keys[-1]] = value.lower() == "true"
        else:
            current[keys[-1]] = value

        save_config(config)
        if not quiet:
            typer.secho(
                f"✓ Set {key_path} = {current[keys[-1]]}", fg=typer.colors.GREEN
            )
        return True
    except json.JSONDecodeError:
        if not quiet:
            typer.secho(
                f"Error: Invalid JSON value: {value}", fg=typer.colors.RED, err=True
            )
        return False
    except Exception as e:
        if not quiet:
            typer.secho(
                f"Error setting config value: {e}", fg=typer.colors.RED, err=True
            )
        return False


def add_file_pattern(
    pattern: str, pattern_type: str = "include", quiet: bool = False
) -> bool:
    """Add a file pattern to include or exclude list."""
    if pattern_type not in ["include", "exclude"]:
        if not quiet:
            typer.secho(
                "Error: pattern_type must be 'include' or 'exclude'",
                fg=typer.colors.RED,
                err=True,
            )
        return False

    config = load_config()
    patterns = config["file_patterns"][pattern_type]

    if pattern not in patterns:
        patterns.append(pattern)
        save_config(config)
        if not quiet:
            typer.secho(
                f"✓ Added '{pattern}' to {pattern_type} patterns", fg=typer.colors.GREEN
            )
        return True
    else:
        if not quiet:
            typer.secho(
                f"Pattern '{pattern}' already in {pattern_type} list",
                fg=typer.colors.YELLOW,
            )
        return True


def remove_file_pattern(
    pattern: str, pattern_type: str = "include", quiet: bool = False
) -> bool:
    """Remove a file pattern from include or exclude list."""
    if pattern_type not in ["include", "exclude"]:
        if not quiet:
            typer.secho(
                "Error: pattern_type must be 'include' or 'exclude'",
                fg=typer.colors.RED,
                err=True,
            )
        return False

    config = load_config()
    patterns = config["file_patterns"][pattern_type]

    if pattern in patterns:
        patterns.remove(pattern)
        save_config(config)
        if not quiet:
            typer.secho(
                f"✓ Removed '{pattern}' from {pattern_type} patterns",
                fg=typer.colors.GREEN,
            )
        return True
    else:
        if not quiet:
            typer.secho(
                f"Pattern '{pattern}' not found in {pattern_type} list",
                fg=typer.colors.YELLOW,
            )
        return False


def reset_config(quiet: bool = False) -> bool:
    """Reset configuration to defaults."""
    save_config(DEFAULT_CONFIG)
    if not quiet:
        typer.secho("✓ Configuration reset to defaults", fg=typer.colors.GREEN)
    return True


def clone_repo(remote_url: str, quiet: bool = False) -> bool:
    """
    Clone an existing dotz repository from a remote URL and automatically restore
    all tracked dotfiles to their home directory locations.

    This enables automated setup on fresh systems.
    """
    if DOTZ_DIR.exists():
        if not quiet:
            typer.secho(
                "Error: dotz already initialized at ~/.dotz. Use 'dotz pull' to sync.",
                fg=typer.colors.RED,
                err=True,
            )
        return False

    if not quiet:
        typer.secho(
            f"Cloning dotz repository from {remote_url}...", fg=typer.colors.WHITE
        )

    try:
        # Create dotz directory
        DOTZ_DIR.mkdir(parents=True, exist_ok=True)

        # Clone the repository
        repo = Repo.clone_from(remote_url, str(WORK_TREE))

        if not quiet:
            typer.secho("✓ Repository cloned successfully", fg=typer.colors.GREEN)

        # Set up Git config for dotz
        repo.git.config("user.name", "dotz")
        repo.git.config("user.email", "dotz@example.com")

        # Get all tracked files from the repository
        tracked_files = repo.git.ls_files().splitlines()

        if not tracked_files:
            if not quiet:
                typer.secho("No files found in repository", fg=typer.colors.YELLOW)
            return True

        if not quiet:
            typer.secho(
                f"Found {len(tracked_files)} tracked files. "
                "Restoring to home directory...",
                fg=typer.colors.CYAN,
            )

        # Restore all tracked files
        restored_count = 0
        failed_files = []

        for file_path in tracked_files:
            try:
                # Create Path object relative to home
                rel_path = Path(file_path)
                home_path = HOME / rel_path
                repo_path = WORK_TREE / rel_path

                # Skip if the file doesn't exist in the repo (shouldn't happen)
                if not repo_path.exists():
                    continue

                # Remove existing file/symlink/directory if it exists
                if home_path.exists() or home_path.is_symlink():
                    if home_path.is_symlink():
                        home_path.unlink()
                    else:
                        # Create backup before removing
                        create_backup(home_path, operation="clone", quiet=quiet)
                        if home_path.is_file():
                            home_path.unlink()
                        elif home_path.is_dir():
                            shutil.rmtree(home_path)

                # Ensure parent directory exists
                home_path.parent.mkdir(parents=True, exist_ok=True)

                # Create symlink from home to repo
                home_path.symlink_to(repo_path)

                restored_count += 1
                if not quiet:
                    typer.secho(f"  ✓ Restored {rel_path}", fg=typer.colors.GREEN)

            except Exception as e:
                failed_files.append((file_path, str(e)))
                if not quiet:
                    typer.secho(
                        f"  ! Failed to restore {file_path}: {e}",
                        fg=typer.colors.YELLOW,
                    )

        # Summary
        if not quiet:
            typer.secho(
                f"\n✓ Clone complete! Restored {restored_count}/"
                f"{len(tracked_files)} files",
                fg=typer.colors.GREEN,
                bold=True,
            )

            if failed_files:
                typer.secho(
                    f"Failed to restore {len(failed_files)} files:",
                    fg=typer.colors.YELLOW,
                )
                for file_path, error in failed_files:
                    typer.secho(f"  - {file_path}: {error}", fg=typer.colors.YELLOW)

        return True

    except GitCommandError as e:
        if not quiet:
            msg = str(e)
            if "not found" in msg.lower() or "does not exist" in msg.lower():
                typer.secho(
                    f"Error: Repository not found at {remote_url}",
                    fg=typer.colors.RED,
                    err=True,
                )
            elif "permission denied" in msg.lower() or "authentication" in msg.lower():
                typer.secho(
                    f"Error: Authentication failed for {remote_url}. "
                    "Check your SSH keys or credentials.",
                    fg=typer.colors.RED,
                    err=True,
                )
            else:
                typer.secho(
                    f"Error cloning repository: {e}", fg=typer.colors.RED, err=True
                )

        # Clean up on failure
        if DOTZ_DIR.exists():
            shutil.rmtree(DOTZ_DIR)

        return False

    except Exception as e:
        if not quiet:
            typer.secho(
                f"Unexpected error during clone: {e}", fg=typer.colors.RED, err=True
            )

        # Clean up on failure
        if DOTZ_DIR.exists():
            shutil.rmtree(DOTZ_DIR)

        return False


def restore_all_dotfiles(quiet: bool = False, push: bool = False) -> bool:
    """
    Restore all tracked dotfiles from the dotz repository to their home directory
    locations. This creates symlinks for all files currently tracked by dotz.

    This is useful for setting up dotfiles on a new system after cloning a
    repository or when you want to restore all files at once.
    """
    repo = ensure_repo()

    # Get all tracked files from the repository
    try:
        tracked_files = repo.git.ls_files().splitlines()
    except Exception as e:
        if not quiet:
            typer.secho(
                f"Error getting tracked files: {e}", fg=typer.colors.RED, err=True
            )
        return False

    if not tracked_files:
        if not quiet:
            typer.secho("No files tracked by dotz to restore.", fg=typer.colors.YELLOW)
        return True

    if not quiet:
        typer.secho(
            f"Restoring {len(tracked_files)} tracked files...", fg=typer.colors.CYAN
        )

    restored_count = 0
    failed_files = []
    skipped_files = []

    for file_path in tracked_files:
        try:
            # Create Path objects
            rel_path = Path(file_path)
            home_path = HOME / rel_path
            repo_path = WORK_TREE / rel_path

            # Skip if the file doesn't exist in the repo (shouldn't happen)
            if not repo_path.exists():
                failed_files.append((file_path, "File not found in repository"))
                continue

            # Check if already properly symlinked
            if home_path.is_symlink() and home_path.resolve() == repo_path.resolve():
                skipped_files.append(file_path)
                if not quiet:
                    typer.secho(
                        f"  - {rel_path} (already linked)", fg=typer.colors.BLUE
                    )
                continue

            # Remove existing file/symlink/directory if it exists
            if home_path.exists() or home_path.is_symlink():
                if home_path.is_symlink():
                    home_path.unlink()
                else:
                    # Create backup before removing
                    create_backup(home_path, operation="restore_all", quiet=quiet)
                    if home_path.is_file():
                        home_path.unlink()
                    elif home_path.is_dir():
                        shutil.rmtree(home_path)

            # Ensure parent directory exists
            home_path.parent.mkdir(parents=True, exist_ok=True)

            # Create symlink from home to repo
            home_path.symlink_to(repo_path)

            restored_count += 1
            if not quiet:
                typer.secho(f"  ✓ Restored {rel_path}", fg=typer.colors.GREEN)

        except Exception as e:
            failed_files.append((file_path, str(e)))
            if not quiet:
                typer.secho(
                    f"  ! Failed to restore {file_path}: {e}",
                    fg=typer.colors.YELLOW,
                )

    # Summary
    if not quiet:
        typer.secho(
            f"\n✓ Restore complete! Restored {restored_count} files, "
            f"skipped {len(skipped_files)}, failed {len(failed_files)}",
            fg=typer.colors.GREEN,
            bold=True,
        )

        if failed_files:
            typer.secho(
                f"\nFailed to restore {len(failed_files)} files:",
                fg=typer.colors.YELLOW,
            )
            for file_path, error in failed_files:
                typer.secho(f"  - {file_path}: {error}", fg=typer.colors.YELLOW)

    # Only push if there were no failures and something was actually restored
    if push and restored_count > 0 and not failed_files:
        try:
            origin = repo.remote("origin")
            branch = repo.active_branch.name
            result = origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
            if any(r.flags & r.ERROR for r in result):
                for r in result:
                    if r.flags & r.ERROR and not quiet:
                        typer.secho(
                            f"Error pushing to origin: {r.summary}",
                            fg=typer.colors.RED,
                            err=True,
                        )
                return False
            if not quiet:
                typer.secho("✓ Pushed to origin", fg=typer.colors.GREEN)
        except GitCommandError as e:
            if not quiet:
                typer.secho(
                    f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True
                )
            return False

    # Return success if we restored at least some files and had no failures
    return len(failed_files) == 0


def validate_symlinks(
    repair: bool = False, quiet: bool = False
) -> Dict[str, List[str]]:
    """
    Validate all symlinks managed by dotz and optionally repair broken ones.

    Returns a dictionary with categories of symlinks:
    - 'valid': Working symlinks pointing to correct dotz files
    - 'broken': Symlinks that point to non-existent files
    - 'missing': Tracked files that should be symlinked but aren't
    - 'wrong_target': Symlinks pointing to wrong locations
    - 'not_symlink': Files that should be symlinks but are regular files/dirs
    - 'repaired': Files that were successfully repaired (if repair=True)
    - 'repair_failed': Files that couldn't be repaired (if repair=True)
    """
    repo = ensure_repo()

    # Get all tracked files from the repository
    try:
        tracked_files = repo.git.ls_files().splitlines()
    except Exception as e:
        if not quiet:
            typer.secho(
                f"Error getting tracked files: {e}", fg=typer.colors.RED, err=True
            )
        return {}

    if not quiet:
        typer.secho(
            f"Validating {len(tracked_files)} tracked symlinks...", fg=typer.colors.CYAN
        )

    results: Dict[str, List[str]] = {
        "valid": [],
        "broken": [],
        "missing": [],
        "wrong_target": [],
        "not_symlink": [],
        "repaired": [],
        "repair_failed": [],
    }

    for file_path in tracked_files:
        rel_path = Path(file_path)
        home_path = HOME / rel_path
        repo_path = WORK_TREE / rel_path

        # Skip if the file doesn't exist in the repo
        if not repo_path.exists():
            results["broken"].append(file_path)
            if not quiet:
                typer.secho(
                    f"  ! {rel_path}: File missing from repository", fg=typer.colors.RED
                )
            continue

        # Check if home path doesn't exist at all
        if not home_path.exists() and not home_path.is_symlink():
            results["missing"].append(file_path)
            if not quiet:
                typer.secho(
                    f"  ! {rel_path}: Missing symlink in home directory",
                    fg=typer.colors.YELLOW,
                )

            # Repair if requested
            if repair:
                try:
                    home_path.parent.mkdir(parents=True, exist_ok=True)
                    home_path.symlink_to(repo_path)
                    results["repaired"].append(file_path)
                    if not quiet:
                        typer.secho(
                            f"    ✓ Repaired: Created symlink for {rel_path}",
                            fg=typer.colors.GREEN,
                        )
                except Exception as e:
                    results["repair_failed"].append(file_path)
                    if not quiet:
                        typer.secho(
                            f"    ! Failed to repair {rel_path}: {e}",
                            fg=typer.colors.RED,
                        )
            continue

        # Check if it's a symlink
        if not home_path.is_symlink():
            results["not_symlink"].append(file_path)
            if not quiet:
                typer.secho(
                    f"  ! {rel_path}: Should be symlink but is regular file/directory",
                    fg=typer.colors.YELLOW,
                )

            # Repair if requested
            if repair:
                try:
                    # Create backup before removing
                    create_backup(home_path, operation="repair", quiet=quiet)
                    # Remove existing file/directory
                    if home_path.is_file():
                        home_path.unlink()
                    elif home_path.is_dir():
                        shutil.rmtree(home_path)

                    # Create symlink
                    home_path.symlink_to(repo_path)
                    results["repaired"].append(file_path)
                    if not quiet:
                        typer.secho(
                            f"    ✓ Repaired: Replaced with symlink {rel_path}",
                            fg=typer.colors.GREEN,
                        )
                except Exception as e:
                    results["repair_failed"].append(file_path)
                    if not quiet:
                        typer.secho(
                            f"    ! Failed to repair {rel_path}: {e}",
                            fg=typer.colors.RED,
                        )
            continue

        # Check if symlink points to the correct target
        try:
            symlink_target = home_path.resolve()
            expected_target = repo_path.resolve()

            if symlink_target != expected_target:
                results["wrong_target"].append(file_path)
                if not quiet:
                    typer.secho(
                        f"  ! {rel_path}: Points to {symlink_target} "
                        f"instead of {expected_target}",
                        fg=typer.colors.YELLOW,
                    )

                # Repair if requested
                if repair:
                    try:
                        home_path.unlink()
                        home_path.symlink_to(repo_path)
                        results["repaired"].append(file_path)
                        if not quiet:
                            typer.secho(
                                f"    ✓ Repaired: Fixed symlink target for {rel_path}",
                                fg=typer.colors.GREEN,
                            )
                    except Exception as e:
                        results["repair_failed"].append(file_path)
                        if not quiet:
                            typer.secho(
                                f"    ! Failed to repair {rel_path}: {e}",
                                fg=typer.colors.RED,
                            )
                continue

            # Check if symlink target actually exists
            if not symlink_target.exists():
                results["broken"].append(file_path)
                if not quiet:
                    typer.secho(
                        f"  ! {rel_path}: Broken symlink (target doesn't exist)",
                        fg=typer.colors.RED,
                    )

                # Repair if requested
                if repair:
                    try:
                        home_path.unlink()
                        home_path.symlink_to(repo_path)
                        results["repaired"].append(file_path)
                        if not quiet:
                            typer.secho(
                                f"    ✓ Repaired: Fixed broken symlink {rel_path}",
                                fg=typer.colors.GREEN,
                            )
                    except Exception as e:
                        results["repair_failed"].append(file_path)
                        if not quiet:
                            typer.secho(
                                f"    ! Failed to repair {rel_path}: {e}",
                                fg=typer.colors.RED,
                            )
                continue

            # If we get here, the symlink is valid
            results["valid"].append(file_path)
            if not quiet:
                typer.secho(f"  ✓ {rel_path}: Valid symlink", fg=typer.colors.GREEN)

        except Exception as e:
            results["broken"].append(file_path)
            if not quiet:
                typer.secho(
                    f"  ! {rel_path}: Error checking symlink: {e}", fg=typer.colors.RED
                )

    # Summary
    if not quiet:
        total_issues = (
            len(results["broken"])
            + len(results["missing"])
            + len(results["wrong_target"])
            + len(results["not_symlink"])
        )

        if total_issues == 0:
            typer.secho(
                f"\n✓ All {len(results['valid'])} symlinks are valid!",
                fg=typer.colors.GREEN,
                bold=True,
            )
        else:
            typer.secho(
                f"\nFound {total_issues} issues with symlinks:",
                fg=typer.colors.YELLOW,
                bold=True,
            )

            if results["broken"]:
                typer.secho(
                    f"  • {len(results['broken'])} broken symlinks", fg=typer.colors.RED
                )
            if results["missing"]:
                typer.secho(
                    f"  • {len(results['missing'])} missing symlinks",
                    fg=typer.colors.YELLOW,
                )
            if results["wrong_target"]:
                typer.secho(
                    f"  • {len(results['wrong_target'])} wrong targets",
                    fg=typer.colors.YELLOW,
                )
            if results["not_symlink"]:
                typer.secho(
                    f"  • {len(results['not_symlink'])} should be symlinks",
                    fg=typer.colors.YELLOW,
                )

        if repair:
            if results["repaired"]:
                typer.secho(
                    f"\n✓ Repaired {len(results['repaired'])} symlinks",
                    fg=typer.colors.GREEN,
                )
            if results["repair_failed"]:
                typer.secho(
                    f"! Failed to repair {len(results['repair_failed'])} symlinks",
                    fg=typer.colors.RED,
                )
        elif total_issues > 0:
            typer.secho(
                "\nRun 'dotz validate --repair' to fix these issues automatically.",
                fg=typer.colors.CYAN,
            )

    return results


# ============================================================================
# BACKUP MANAGEMENT
# ============================================================================


def create_backup(
    file_path: Path, operation: str = "restore", quiet: bool = False
) -> Optional[Path]:
    """
    Create a backup of a file before overwriting it.

    Args:
        file_path: Path to the file to backup
        operation: The operation being performed (for backup naming)
        quiet: If True, suppress output messages

    Returns:
        Path to the backup file if successful, None otherwise
    """
    if not file_path.exists():
        return None

    # Ensure backup directory exists
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Create timestamped backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if file_path.is_relative_to(HOME):
        relative_path = file_path.relative_to(HOME)
    else:
        relative_path = file_path
    backup_name = (
        f"{relative_path.as_posix().replace('/', '_')}_{operation}_{timestamp}"
    )
    # Add .tar.gz extension for directories
    if file_path.is_dir():
        backup_name += ".tar.gz"
    backup_path = BACKUP_DIR / backup_name

    try:
        if file_path.is_file():
            shutil.copy2(file_path, backup_path)
        elif file_path.is_dir():
            # Create a tar archive for directories
            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(file_path, arcname=file_path.name)
        else:
            # Handle symlinks and other special files
            shutil.copy2(file_path, backup_path, follow_symlinks=False)

        if not quiet:
            typer.secho(
                f"Backed up {relative_path} to backups/{backup_name}",
                fg=typer.colors.BLUE,
            )

        return backup_path
    except Exception as e:
        if not quiet:
            typer.secho(
                f"Warning: Failed to backup {relative_path}: {e}",
                fg=typer.colors.YELLOW,
            )
        return None


def list_backups() -> List[Path]:
    """List all backup files in the backup directory."""
    if not BACKUP_DIR.exists():
        return []

    backups = []
    for backup_file in BACKUP_DIR.iterdir():
        if backup_file.is_file():
            backups.append(backup_file)

    return sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True)


def restore_from_backup(backup_path: Path, quiet: bool = False) -> bool:
    """
    Restore a file from backup.

    Args:
        backup_path: Path to the backup file
        quiet: If True, suppress output messages

    Returns:
        True if successful, False otherwise
    """
    if not backup_path.exists():
        if not quiet:
            typer.secho(
                f"Error: Backup file {backup_path} not found", fg=typer.colors.RED
            )
        return False

    # Parse backup filename to determine original location
    backup_name = backup_path.name

    # Remove .tar.gz extension if present
    if backup_name.endswith(".tar.gz"):
        backup_name = backup_name[:-7]

    parts = backup_name.split("_")
    if len(parts) < 3:
        if not quiet:
            typer.secho(
                f"Error: Invalid backup filename format: {backup_name}",
                fg=typer.colors.RED,
            )
        return False

    # Reconstruct original path (everything before the operation and timestamp)
    # Find the operation part (second to last before timestamp)
    remaining_parts = parts[:]

    # Remove timestamp parts from the end (format: YYYYMMDD_HHMMSS)
    if len(remaining_parts) >= 2:
        # Check if last two parts look like timestamp
        if (
            remaining_parts[-1].isdigit()
            and len(remaining_parts[-1]) == 6
            and remaining_parts[-2].isdigit()
            and len(remaining_parts[-2]) == 8
        ):
            remaining_parts = remaining_parts[:-2]

    # Remove operation part (should be last now)
    if remaining_parts:
        remaining_parts = remaining_parts[:-1]

    if not remaining_parts:
        if not quiet:
            typer.secho(
                f"Error: Could not parse original path from backup filename: "
                f"{backup_name}",
                fg=typer.colors.RED,
            )
        return False

    original_relative = "/".join(remaining_parts)
    original_path = HOME / original_relative

    try:
        # Create parent directories if needed
        original_path.parent.mkdir(parents=True, exist_ok=True)

        # Backup current file if it exists
        if original_path.exists():
            create_backup(original_path, operation="pre_restore", quiet=quiet)

        # Restore from backup
        if backup_path.suffix == ".gz" or backup_path.name.endswith(".tar.gz"):
            # Extract tar archive
            with tarfile.open(backup_path, "r:gz") as tar:
                # Validate tar members for security
                def is_safe_path(path: Path, base_path: Path) -> bool:
                    """Check if the path is safe to extract."""
                    try:
                        resolved = (base_path / path).resolve()
                        return str(resolved).startswith(str(base_path.resolve()))
                    except (OSError, ValueError):
                        return False

                safe_members = []
                for member in tar.getmembers():
                    if member.isfile() and is_safe_path(
                        Path(member.name), original_path.parent
                    ):
                        safe_members.append(member)

                # Extract only safe members
                tar.extractall(  # nosec B202
                    path=original_path.parent, members=safe_members
                )
        else:
            # Copy regular file
            shutil.copy2(backup_path, original_path)

        if not quiet:
            typer.secho(
                f"✓ Restored {original_relative} from backup", fg=typer.colors.GREEN
            )

        return True
    except Exception as e:
        if not quiet:
            typer.secho(f"Error restoring from backup: {e}", fg=typer.colors.RED)
        return False


# ============================================================================
# PROGRESS TRACKING FUNCTIONS
# ============================================================================


def add_dotfiles_with_progress(
    paths: List[Path],
    push: bool = False,
    quiet: bool = False,
    description: str = "Adding dotfiles",
) -> Dict[str, int]:
    """
    Add multiple dotfiles with progress tracking.

    Returns:
        Dictionary with 'success' and 'failed' counts
    """
    results = {"success": 0, "failed": 0}

    if not paths:
        return results

    if quiet:
        # No progress bar in quiet mode
        for path in paths:
            if add_dotfile(path, push=False, quiet=True):
                results["success"] += 1
            else:
                results["failed"] += 1
    else:
        # Show progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(description, total=len(paths))

            for path in paths:
                rel_path = path.relative_to(HOME) if path.is_relative_to(HOME) else path
                progress.update(task, description=f"{description} {rel_path}")

                if add_dotfile(path, push=False, quiet=True):
                    results["success"] += 1
                else:
                    results["failed"] += 1

                progress.advance(task)

    # Push once at the end if requested
    if push and results["success"] > 0:
        with (
            Status("Pushing to remote...", console=console)
            if not quiet
            else nullcontext()
        ):
            push_repo(quiet=quiet)

    return results


def restore_dotfiles_with_progress(
    paths: List[Path], quiet: bool = False, description: str = "Restoring dotfiles"
) -> Dict[str, int]:
    """
    Restore multiple dotfiles with progress tracking.

    Returns:
        Dictionary with 'success' and 'failed' counts
    """
    results = {"success": 0, "failed": 0}

    if not paths:
        return results

    if quiet:
        # No progress bar in quiet mode
        for path in paths:
            if restore_dotfile(path, quiet=True):
                results["success"] += 1
            else:
                results["failed"] += 1
    else:
        # Show progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(description, total=len(paths))

            for path in paths:
                rel_path = path.relative_to(HOME) if path.is_relative_to(HOME) else path
                progress.update(task, description=f"{description} {rel_path}")

                if restore_dotfile(path, quiet=True):
                    results["success"] += 1
                else:
                    results["failed"] += 1

                progress.advance(task)

    return results


def find_config_files_with_progress(
    directory: Path,
    config: Optional[Dict[str, Any]] = None,
    recursive: bool = True,
    quiet: bool = False,
) -> List[Path]:
    """
    Find config files with progress indication for large directories.
    """
    if config is None:
        config = load_config()

    # For small directories, use the existing function without progress
    if quiet:
        return find_config_files(directory, config, recursive)

    # Count files first to show progress
    with Status("Scanning directory...", console=console):
        if recursive:
            all_files = list(directory.rglob("*"))
        else:
            all_files = list(directory.iterdir())

        files_to_check = [f for f in all_files if f.is_file()]

    # Use progress bar only for large directories
    if len(files_to_check) < PROGRESS_THRESHOLD:
        return find_config_files(directory, config, recursive)

    include_patterns = config["file_patterns"]["include"]
    exclude_patterns = config["file_patterns"]["exclude"]
    case_sensitive = config["search_settings"]["case_sensitive"]
    follow_symlinks = config["search_settings"]["follow_symlinks"]

    found_files = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning files...", total=len(files_to_check))

        for file_path in files_to_check:
            progress.update(task, description=f"Scanning {file_path.name}")

            if not follow_symlinks and file_path.is_symlink():
                progress.advance(task)
                continue

            if matches_patterns(
                file_path.name, include_patterns, exclude_patterns, case_sensitive
            ):
                found_files.append(file_path)

            progress.advance(task)

    return found_files


def commit_repo(
    message: str, files: Optional[List[str]] = None, quiet: bool = False
) -> bool:
    """Commit changes in the dotz repository."""
    try:
        repo = ensure_repo()

        if files:
            # Add specific files
            for file in files:
                try:
                    repo.index.add([file])
                except Exception as e:
                    if not quiet:
                        typer.secho(
                            f"Warning: Could not add {file}: {e}",
                            fg=typer.colors.YELLOW,
                        )
        else:
            # Add all modified and untracked files
            repo.git.add("-A")

        # Check if there are changes to commit
        if not repo.index.diff("HEAD") and not repo.untracked_files:
            if not quiet:
                typer.secho("No changes to commit", fg=typer.colors.YELLOW)
            return True

        commit = repo.index.commit(message)
        if not quiet:
            typer.secho(
                f"Committed changes: {commit.hexsha[:8]}", fg=typer.colors.GREEN
            )
            typer.secho(f"Message: {message}", fg=typer.colors.WHITE)
        return True
    except Exception as e:
        if not quiet:
            typer.secho(f"Failed to commit changes: {e}", fg=typer.colors.RED, err=True)
        return False


def diff_files(files: Optional[List[str]] = None, quiet: bool = False) -> bool:
    """Show diff for files in the dotz repository."""
    try:
        repo = ensure_repo()

        if files:
            # Show diff for specific files
            for file in files:
                try:
                    diff = repo.git.diff(file)
                    if diff:
                        if not quiet:
                            typer.secho(
                                f"Changes in {file}:", fg=typer.colors.CYAN, bold=True
                            )
                            typer.echo(diff)
                    else:
                        if not quiet:
                            typer.secho(f"No changes in {file}", fg=typer.colors.YELLOW)
                except Exception as e:
                    if not quiet:
                        typer.secho(
                            f"Error showing diff for {file}: {e}",
                            fg=typer.colors.RED,
                            err=True,
                        )
        else:
            # Show diff for all modified files
            diff = repo.git.diff()
            if diff:
                if not quiet:
                    typer.secho(
                        "Changes in repository:", fg=typer.colors.CYAN, bold=True
                    )
                    typer.echo(diff)
            else:
                if not quiet:
                    typer.secho("No changes to show", fg=typer.colors.YELLOW)
        return True
    except Exception as e:
        if not quiet:
            typer.secho(f"Error showing diff: {e}", fg=typer.colors.RED, err=True)
        return False
