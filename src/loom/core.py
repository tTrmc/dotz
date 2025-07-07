import fnmatch
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from git import GitCommandError, Repo


def get_home_dir() -> Path:
    """Get the home directory, respecting environment variables for testing."""
    # Check for test override first
    if "HOME" in os.environ:
        return Path(os.environ["HOME"])
    return Path.home()


def get_loom_paths(home_dir: Optional[Path] = None) -> Dict[str, Path]:
    """Get all loom-related paths based on home directory."""
    if home_dir is None:
        home_dir = get_home_dir()

    loom_dir = home_dir / ".loom"
    work_tree = loom_dir / "repo"
    tracked_dirs_file = loom_dir / "tracked_dirs.json"
    config_file = loom_dir / "config.json"

    return {
        "home": home_dir,
        "loom_dir": loom_dir,
        "work_tree": work_tree,
        "tracked_dirs_file": tracked_dirs_file,
        "config_file": config_file,
    }


# Global paths - can be overridden for testing
_paths = get_loom_paths()
HOME = _paths["home"]
LOOM_DIR = _paths["loom_dir"]
WORK_TREE = _paths["work_tree"]
TRACKED_DIRS_FILE = _paths["tracked_dirs_file"]
CONFIG_FILE = _paths["config_file"]

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


def ensure_repo() -> Repo:
    try:
        return Repo(str(WORK_TREE))
    except Exception:
        typer.secho(
            "Error: loom repository not initialized. Run `loom init` first.",
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


def init_repo(remote: str = "", quiet: bool = False) -> bool:
    if LOOM_DIR.exists():
        if not quiet:
            typer.secho("loom already initialised at ~/.loom", fg=typer.colors.YELLOW)
        return False

    if not quiet:
        typer.secho("Initialising loom...", fg=typer.colors.WHITE)
    LOOM_DIR.mkdir()
    WORK_TREE.mkdir()

    repo = Repo.init(str(WORK_TREE))
    repo.git.config("user.name", "loom")
    repo.git.config("user.email", "loom@example.com")
    if not quiet:
        typer.secho("Creating initial commit...", fg=typer.colors.CYAN)
    repo.git.commit("--allow-empty", "-m", "Initial commit")
    if not quiet:
        typer.secho("Created empty initial commit", fg=typer.colors.GREEN)

    if remote:
        repo.create_remote("origin", remote)
        if not quiet:
            typer.secho(
                "WARNING: If you are adding sensitive information, make sure "
                "your remote repository is private!",
                fg=typer.colors.RED,
                bold=True,
            )

    if not quiet:
        typer.secho(
            "Initialised loom repository in ~/.loom/repo", fg=typer.colors.GREEN
        )
    return True


def add_dotfile(
    path: Path, push: bool = False, quiet: bool = False, recursive: bool = True
) -> bool:
    """
    Add a file or directory to loom, then symlink it in your home directory.
    Set quiet=True to suppress typer.secho output (for watcher).
    """
    repo = ensure_repo()
    src = (HOME / path).expanduser()

    if not src.exists():
        if not quiet:
            typer.secho(f"Error: {src} not found.", fg=typer.colors.RED, err=True)
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
        shutil.copy2(src, dest)
        tracked_path = dest.relative_to(WORK_TREE).as_posix()
        repo.index.add([tracked_path])
        repo.index.commit(f"Add {rel}")
        src.unlink()
        src.symlink_to(dest)
        if not quiet:
            typer.secho(f"✓ Added {rel}", fg=typer.colors.GREEN)

    elif src.is_dir():
        save_tracked_dir(src)
        config = load_config()
        dotfiles = find_config_files(src, config, recursive)
        if not dotfiles:
            if not quiet:
                typer.secho(f"No config files found in {rel}.", fg=typer.colors.YELLOW)
            return True

        for df in dotfiles:
            sub_rel = df.relative_to(HOME)
            sub_dest = WORK_TREE / sub_rel
            sub_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(df, sub_dest)
            tracked_path = sub_dest.relative_to(WORK_TREE).as_posix()
            repo.index.add([tracked_path])
            df.unlink()
            df.symlink_to(sub_dest)
            if not quiet:
                typer.secho(f"✓ Added dotfile {sub_rel}", fg=typer.colors.GREEN)
        repo.index.commit(f"Add dotfiles in {rel}")
        if not quiet:
            typer.secho(
                f"✓ Added {len(dotfiles)} dotfiles from {rel}", fg=typer.colors.GREEN
            )

    else:
        if not quiet:
            typer.secho(
                f"Error: {src} is not a regular file or directory.",
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


def delete_dotfile(path: Path, push: bool = False, quiet: bool = False) -> bool:
    repo = ensure_repo()
    src = (HOME / path).expanduser()

    if not src.is_symlink():
        if not quiet:
            typer.secho(
                f"Error: {src} is not a symlink managed by loom.",
                fg=typer.colors.RED,
                err=True,
            )
        return False

    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel

    if not dest.exists():
        if not quiet:
            typer.secho(
                f"Error: {dest} does not exist in the loom repository.",
                fg=typer.colors.RED,
                err=True,
            )
        return False

    src.unlink()
    if dest.is_file():
        dest.unlink()
        tracked_path = dest.relative_to(WORK_TREE).as_posix()
        repo.index.remove([tracked_path])
    elif dest.is_dir():
        shutil.rmtree(dest)
        tracked_path = dest.relative_to(WORK_TREE).as_posix()
        repo.index.remove([tracked_path], r=True)
        remove_tracked_dir(src)

    repo.index.commit(f"Remove {rel}")
    if not quiet:
        typer.secho(f"✓ Removed {rel}", fg=typer.colors.GREEN)

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


def restore_dotfile(path: Path, quiet: bool = False, push: bool = False) -> bool:
    src = (HOME / path).expanduser()
    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel

    # Check if the file/directory is tracked (exists in the repo)
    if not dest.exists():
        if not quiet:
            typer.secho(
                f"Error: {rel} is not tracked by loom.",
                fg=typer.colors.RED,
                err=True,
            )
        return False

    # If there's already something at src, remove it
    if src.is_symlink():
        src.unlink()
    elif src.exists():
        if src.is_file():
            src.unlink()
        elif src.is_dir():
            shutil.rmtree(src)

    # Create symlink from home to repo (not a copy)
    src.symlink_to(dest)
    if not quiet:
        typer.secho(f"✓ Restored {rel}", fg=typer.colors.GREEN)

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
                "`loom init --remote <URL>` or `git remote add origin <URL>`.",
                fg=typer.colors.RED,
                err=True,
            )
        return False

    origin = repo.remote("origin")
    try:
        origin.pull()
        if not quiet:
            typer.secho("✓ Pulled latest changes from origin", fg=typer.colors.GREEN)
        return True
    except GitCommandError as e:
        msg = str(e)
        if "no tracking information" in msg.lower():
            typer.secho(
                "Error: No tracking branch set for this branch.\n"
                "Run: git -C ~/.loom/repo branch "
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
                "  git -C ~/.loom/repo pull --rebase\n"
                "  git -C ~/.loom/repo pull --no-rebase\n"
                "  git -C ~/.loom/repo pull --ff-only",
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
                "`loom init --remote <URL>` or `git remote add origin <URL>`.",
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
                            "  git -C ~/.loom/repo pull --rebase\n"
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
            typer.secho("✓ Pushed local commits to origin", fg=typer.colors.GREEN)
        return True
    except GitCommandError as e:
        msg = str(e)
        if (
            "no upstream branch" in msg.lower()
            or "no tracking information" in msg.lower()
        ):
            typer.secho(
                "Error: No upstream branch set for this branch.\n"
                "Run: git -C ~/.loom/repo branch "
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
        except Exception:
            pass

    # Dotfiles in $HOME not tracked by loom
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
    LOOM_DIR.mkdir(exist_ok=True)
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


def update_paths(home_dir: Optional[Path] = None) -> None:
    """Update global paths. Useful for testing or when HOME changes."""
    global HOME, LOOM_DIR, WORK_TREE, TRACKED_DIRS_FILE, CONFIG_FILE
    paths = get_loom_paths(home_dir)
    HOME = paths["home"]
    LOOM_DIR = paths["loom_dir"]
    WORK_TREE = paths["work_tree"]
    TRACKED_DIRS_FILE = paths["tracked_dirs_file"]
    CONFIG_FILE = paths["config_file"]
