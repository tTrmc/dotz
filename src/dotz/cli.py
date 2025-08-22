"""CLI commands for dotz - a Git-backed dotfiles manager."""

import json
from contextlib import nullcontext
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import typer
from git import InvalidGitRepositoryError, Repo
from rich.console import Console
from rich.status import Status
from typing_extensions import Annotated

from dotz import core

from . import templates
from .core import (
    add_dotfile,
    add_file_pattern,
    clone_repo,
    commit_repo,
    create_backup,
    delete_dotfile,
    diff_files,
    get_config_value,
    get_dotz_paths,
    get_home_dir,
    get_repo_status,
    init_repo,
    list_backups,
    list_tracked_files,
    load_config,
    parse_backup_filename,
    pull_repo,
    push_repo,
    remove_file_pattern,
    reset_config,
    restore_dotfile,
    restore_from_backup,
    set_config_value,
    update_paths,
    validate_symlinks,
)
from .watcher import main as watcher_main

# Constants
DEFAULT_VERSION = "0.4.0"
MAX_DISPLAYED_FILES = 10
MAX_DISPLAYED_BACKUPS = 5

# Global app and console instances
app = typer.Typer(help="dotz - a Git-backed dotfiles manager")
console = Console()

# Global path variables - initialized on first use
HOME: Path
DOTZ_DIR: Path
WORK_TREE: Path


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        size_kb = size_bytes / 1024
        return f"{size_kb:.1f} KB"
    else:
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.1f} MB"


# Initialize global paths from core
_paths = get_dotz_paths()
HOME = _paths["home"]
DOTZ_DIR = _paths["dotz_dir"]
WORK_TREE = _paths["work_tree"]


@app.command()
def init(
    remote: Annotated[
        str, typer.Option(help="Optional remote URL to add as origin (SSH or HTTPS).")
    ] = "",
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive", "-n", help="Run without prompts (for scripting)"
        ),
    ] = False,
) -> None:
    """Initialize a new dotz repository."""
    if not non_interactive and not remote:
        typer.secho("dotz Interactive Setup", fg=typer.colors.CYAN, bold=True)
        typer.echo(
            "Welcome! Let's configure your dotz repository for managing dotfiles.\n"
        )

        # Remote URL configuration
        typer.secho("Git Remote Configuration", fg=typer.colors.BLUE, bold=True)
        typer.echo("Would you like to connect to a remote Git repository?")
        typer.echo("This allows you to backup and sync your dotfiles across devices.")
        typer.echo("Examples:")
        typer.echo("  • GitHub: https://github.com/username/dotfiles.git")
        typer.echo("  • GitLab: https://gitlab.com/username/dotfiles.git")
        typer.echo("  • SSH:    git@github.com:username/dotfiles.git")

        use_remote = typer.confirm("\nAdd a remote repository?", default=False)
        if use_remote:
            while True:
                remote = typer.prompt("Enter the remote URL")
                if remote.strip():
                    # Basic validation
                    if any(
                        remote.startswith(prefix)
                        for prefix in ["https://", "http://", "git@", "ssh://"]
                    ):
                        break
                    else:
                        typer.secho(
                            "Invalid URL format. Please use https://, git@, or ssh://",
                            fg=typer.colors.RED,
                            err=True,
                        )
                else:
                    typer.secho(
                        "URL cannot be empty. Please enter a valid URL.",
                        fg=typer.colors.RED,
                        err=True,
                    )
        else:
            remote = ""

        # Initial dotfiles setup
        typer.echo()
        typer.secho("Initial Dotfiles Setup", fg=typer.colors.CYAN, bold=True)
        typer.echo(
            "Would you like to automatically add common dotfiles to get started?"
        )
        typer.echo("This will search for and add files like:")
        typer.echo("  Shell configs: .bashrc, .zshrc, .profile")
        typer.echo("  Git config: .gitconfig, .gitignore_global")
        typer.echo("  SSH config: .ssh/config")
        typer.echo("  Editor configs: .vimrc, .tmux.conf")

        setup_dotfiles = typer.confirm(
            "\nAutomatically discover and add common dotfiles?", default=True
        )

        typer.echo()
        typer.secho("Initializing dotz repository...", fg=typer.colors.BLUE)
    else:
        setup_dotfiles = False

    try:
        success = init_repo(remote=remote, quiet=False)
        if not success:
            raise typer.Exit(code=1)
    except KeyboardInterrupt:
        typer.secho("Operation cancelled by user", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # Handle initial dotfiles setup if requested
    if setup_dotfiles:
        typer.echo()
        typer.secho("Discovering common dotfiles...", fg=typer.colors.BLUE)

        home = get_home_dir()
        common_dotfiles = [
            ".bashrc",
            ".zshrc",
            ".profile",
            ".bash_profile",
            ".gitconfig",
            ".gitignore_global",
            ".gitignore",
            ".vimrc",
            ".vim",
            ".tmux.conf",
            ".ssh/config",
        ]

        found_files = []
        for dotfile in common_dotfiles:
            dotfile_path = home / dotfile
            if dotfile_path.exists():
                found_files.append(dotfile)

        if found_files:
            typer.secho(
                f"Found {len(found_files)} common dotfiles:", fg=typer.colors.GREEN
            )
            for f in found_files:
                typer.echo(f"  {f}")

            if typer.confirm(
                f"\nAdd these {len(found_files)} files to dotz?", default=True
            ):
                added_count = 0
                for dotfile in found_files:
                    try:
                        success = add_dotfile(
                            Path(dotfile), push=False, quiet=True, recursive=False
                        )
                        if success:
                            added_count += 1
                            typer.secho(f"Added {dotfile}", fg=typer.colors.GREEN)
                    except Exception:
                        typer.secho(f"Could not add {dotfile}", fg=typer.colors.YELLOW)

                if added_count > 0:
                    typer.secho(
                        f"Successfully added {added_count} dotfiles",
                        fg=typer.colors.GREEN,
                        bold=True,
                    )
                else:
                    typer.secho("No dotfiles were added.", fg=typer.colors.YELLOW)
            else:
                typer.secho("Skipped automatic dotfile setup.", fg=typer.colors.YELLOW)
        else:
            typer.secho(
                "No common dotfiles found in your home directory",
                fg=typer.colors.YELLOW,
            )
            typer.echo("You can add dotfiles later with: dotz add <filename>")

    # Show completion message
    typer.echo()
    typer.secho(
        "Dotz repository initialized successfully", fg=typer.colors.GREEN, bold=True
    )

    if remote:
        typer.secho(
            "Next steps:",
            fg=typer.colors.CYAN,
        )
        typer.echo("  Add more dotfiles: dotz add <filename>")
        typer.echo("  Push to remote: dotz push")
        typer.echo("  Check status: dotz status")
    else:
        typer.secho(
            "Next steps:",
            fg=typer.colors.CYAN,
        )
        typer.echo("  Add dotfiles: dotz add <filename>")
        typer.echo("  Add remote later: git -C ~/.dotz/repo remote add origin <url>")
        typer.echo("  Check status: dotz status")


# ============================================================================
# MAIN COMMANDS
# ============================================================================


@app.command()
def add(
    path: str = typer.Argument(..., help="Path to add to the project"),
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", "-r", help="Add directory recursively"
    ),
    push: bool = typer.Option(
        False, "--push", "-p", help="Push to remote after adding"
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress output"),
) -> None:
    """Add files or directories to dotz with progress tracking."""
    update_paths()

    target_path = Path(path).expanduser()
    if not target_path.is_absolute():
        # For relative paths, check both current directory and home directory
        cwd_path = Path.cwd() / target_path
        home_path = get_home_dir() / target_path

        if cwd_path.exists():
            target_path = cwd_path
        elif home_path.exists():
            target_path = home_path
        else:
            target_path = cwd_path  # Default to cwd for error message

    if not target_path.exists():
        if not quiet:
            typer.secho(
                f"Error: Path {path} does not exist", fg=typer.colors.RED, err=True
            )
        raise typer.Exit(1)

    if target_path.is_file():
        _handle_single_file_add(target_path, push, quiet, recursive)
    elif target_path.is_dir():
        _handle_directory_add(target_path, path, recursive, push, quiet)


def _handle_single_file_add(
    target_path: Path, push: bool, quiet: bool, recursive: bool
) -> None:
    """Handle adding a single file."""
    with (
        Status(f"Adding {target_path.name}...", console=console)
        if not quiet
        else nullcontext()
    ):
        success = core.add_dotfile(
            target_path, push=push, quiet=quiet, recursive=recursive
        )

    if success and not quiet:
        typer.secho(f"Added {target_path.name}", fg=typer.colors.GREEN)
    elif not success:
        if not quiet:
            typer.secho(
                f"Failed to add {target_path.name}", fg=typer.colors.RED, err=True
            )
        raise typer.Exit(1)


def _handle_directory_add(
    target_path: Path, original_path: str, recursive: bool, push: bool, quiet: bool
) -> None:
    """Handle adding a directory with multiple files."""
    config = core.load_config()
    files_to_add = core.find_config_files(target_path, config, recursive)

    if not files_to_add:
        if not quiet:
            typer.secho(
                f"No matching files found in {original_path}", fg=typer.colors.YELLOW
            )
        return

    try:
        # Use progress function if available
        result: Dict[str, int] = core.add_dotfiles_with_progress(
            files_to_add, push=push, quiet=quiet, description="Adding files"
        )
        _display_add_results(result, original_path, quiet)
    except AttributeError:
        # Fallback to basic add_dotfile for each file
        _fallback_directory_add(files_to_add, original_path, push, quiet)


def _display_add_results(result: Dict[str, int], path: str, quiet: bool) -> None:
    """Display results of add operation."""
    if not quiet:
        total = result["success"] + result["failed"]
        typer.secho(
            f"Added {result['success']}/{total} files from {path}",
            fg=typer.colors.GREEN,
        )
        if result["failed"] > 0:
            typer.secho(
                f"{result['failed']} files failed to add", fg=typer.colors.YELLOW
            )


def _fallback_directory_add(
    files_to_add: List[Path], original_path: str, push: bool, quiet: bool
) -> None:
    """Fallback method for adding directory files."""
    success_count = 0
    failed_count = 0

    for file_path in files_to_add:
        try:
            if core.add_dotfile(file_path, push=False, quiet=True):
                success_count += 1
            else:
                failed_count += 1
        except Exception:
            failed_count += 1

    if push and success_count > 0:
        core.push_repo(quiet=quiet)

    if not quiet:
        total = success_count + failed_count
        console.print(
            f"[green]✓[/green] Added {success_count}/{total} files from {original_path}"
        )
        if failed_count > 0:
            console.print(
                f"[bold yellow]Warning:[/bold yellow] {failed_count} files "
                "failed to add"
            )


@app.command()
def restore_all(
    push: Annotated[
        bool, typer.Option("--push", "-p", help="Push commit to origin")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
    confirm: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """
    Restore all tracked dotfiles from the dotz repository to your home directory.
    Creates symlinks for all files currently tracked by dotz.
    This is useful for setting up dotfiles on a new system or when you want
    to restore all files at once.
    """
    update_paths()

    if not confirm and not quiet:
        # Show what will be restored
        tracked_files = core.list_tracked_files()

        if not tracked_files:
            typer.secho("No files tracked by dotz to restore.", fg=typer.colors.YELLOW)
            return

        typer.secho(
            f"This will restore {len(tracked_files)} tracked files:",
            fg=typer.colors.CYAN,
        )
        for file_path in tracked_files[:10]:  # Show first 10
            typer.secho(f"  {file_path}", fg=typer.colors.WHITE)

        if len(tracked_files) > 10:
            typer.secho(
                f"  ... and {len(tracked_files) - 10} more files", fg=typer.colors.WHITE
            )

        typer.echo()
        typer.secho(
            "This will overwrite any existing files at these locations!",
            fg=typer.colors.YELLOW,
            bold=True,
        )

        if not typer.confirm("Do you want to continue?"):
            typer.secho("Restore cancelled.", fg=typer.colors.YELLOW)
            return

    try:
        tracked_files = core.list_tracked_files()

        if not tracked_files:
            if not quiet:
                typer.secho("No tracked files to restore", fg=typer.colors.YELLOW)
            return

        # Convert to Path objects
        file_paths = [HOME / f for f in tracked_files]

        # Use progress function for multiple files or fallback
        try:
            result = core.restore_dotfiles_with_progress(
                file_paths, quiet=quiet, description="Restoring files"
            )
            if not quiet:
                total = result["success"] + result["failed"]
                typer.secho(
                    f"Restored {result['success']}/{total} files",
                    fg=typer.colors.GREEN,
                )
                if result["failed"] > 0:
                    typer.secho(
                        f"{result['failed']} files failed", fg=typer.colors.YELLOW
                    )
        except AttributeError:
            # Fallback to basic restore for each file
            success_count = 0
            failed_count = 0

            for tracked_file in tracked_files:
                try:
                    # Use Path object directly for restore_dotfile
                    restore_path: Path = Path(tracked_file)
                    if core.restore_dotfile(restore_path, quiet=True, push=False):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception:
                    failed_count += 1

            if push and success_count > 0:
                core.push_repo(quiet=quiet)

            if not quiet:
                total = success_count + failed_count
                console.print(
                    f"[green]✓[/green] Restored {success_count}/{total} files"
                )
                if failed_count > 0:
                    console.print(
                        f"[bold yellow]Warning:[/bold yellow] {failed_count} "
                        "files failed"
                    )
    except Exception as e:
        if not quiet:
            console.print(f"[red]Error during restore: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def delete(
    path: Annotated[
        List[Path], typer.Argument(help="Paths to dotfiles or directories to delete")
    ],
    push: Annotated[
        bool, typer.Option("--push", "-p", help="Push commit to origin")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """
    Remove a dotz-managed file or directory and delete the symlink in your
    home directory.
    """
    # Confirm deletion unless in quiet mode
    if not quiet:
        files_str = ", ".join(str(p) for p in path)
        if not typer.confirm(f"Delete {files_str}?"):
            typer.secho("Deletion cancelled.", fg=typer.colors.YELLOW)
            return

    success = delete_dotfile(path, push=push, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


# ============================================================================
# REPOSITORY STATUS AND MANAGEMENT COMMANDS
# ============================================================================


@app.command()
def status() -> None:
    """
    Show the status of your dotz repo (untracked, modified, staged), and
    dotfiles in $HOME not tracked by dotz.
    """
    try:
        status_data = get_repo_status()
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.secho("Dotz repository status:", fg=typer.colors.WHITE, bold=True)

    if (
        not status_data["untracked"]
        and not status_data["modified"]
        and not status_data["staged"]
    ):
        typer.secho("Repository is clean", fg=typer.colors.GREEN)
    else:
        if status_data["untracked"]:
            typer.secho("Untracked files:", fg=typer.colors.YELLOW)
            for file in status_data["untracked"]:
                typer.secho(f"  {file}", fg=typer.colors.YELLOW)
            typer.secho(
                "  → Run 'dotz commit -m \"Add new files\"' to commit these",
                fg=typer.colors.CYAN,
            )
        if status_data["modified"]:
            typer.secho("Modified files:", fg=typer.colors.YELLOW)
            for file in status_data["modified"]:
                typer.secho(f"  {file}", fg=typer.colors.YELLOW)
            typer.secho(
                "  → Run 'dotz diff' to see changes, "
                "'dotz commit -m \"Update dotfiles\"' to commit",
                fg=typer.colors.CYAN,
            )
        if status_data["staged"]:
            typer.secho("Staged files:", fg=typer.colors.YELLOW)
            for file in status_data["staged"]:
                typer.secho(f"  {file}", fg=typer.colors.YELLOW)
            typer.secho(
                "  → Run 'dotz commit -m \"Commit staged changes\"' to commit",
                fg=typer.colors.CYAN,
            )

    if status_data["unpushed"]:
        typer.secho("Unpushed changes:", fg=typer.colors.YELLOW)
        for file in status_data["unpushed"]:
            typer.secho(f"  {file}", fg=typer.colors.YELLOW)
        typer.secho(
            "  → Run 'dotz push' to push commits to remote repository",
            fg=typer.colors.CYAN,
        )

    if status_data["untracked_home_dotfiles"]:
        typer.secho("Untracked dotfiles in home directory:", fg=typer.colors.CYAN)
        for f in status_data["untracked_home_dotfiles"]:
            typer.secho(f"  {f}", fg=typer.colors.CYAN)


@app.command()
def list_files() -> None:
    """
    List all files currently tracked by dotz.
    """
    tracked_files = list_tracked_files()
    if not tracked_files:
        typer.secho("No files tracked by dotz.", fg=typer.colors.YELLOW)
        return

    typer.secho("Tracked files:", fg=typer.colors.WHITE, bold=True)
    for f in tracked_files:
        typer.secho(f"  {f}", fg=typer.colors.GREEN)


@app.command()
def restore(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to dotfile or directory (relative to your home directory)"
        ),
    ],
    push: Annotated[
        bool, typer.Option("--push", "-p", help="Push commit to origin")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """
    Restore a dotfile or directory from the dotz repository to your home directory.
    Overwrites any existing file or symlink at that location.
    """
    success = restore_dotfile(path, quiet=quiet, push=push)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def pull(
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """
    Pull the latest changes from the 'origin' remote into the local dotz repository.
    """
    try:
        success = pull_repo(quiet=quiet)
        if not success:
            raise typer.Exit(code=1)
        if not quiet:
            typer.secho("Pull completed successfully", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def push(
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """
    Push all local commits to the 'origin' remote, if it exists.
    """
    try:
        success = push_repo(quiet=quiet)
        if not success:
            raise typer.Exit(code=1)
        if not quiet:
            typer.secho("Push completed successfully", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def watch() -> None:
    """
    Start watching for new dotfiles in tracked directories and automatically add them.
    """
    typer.secho("Starting watcher...", fg=typer.colors.WHITE)
    try:
        watcher_main()
    except KeyboardInterrupt:
        typer.secho("Watcher stopped.", fg=typer.colors.YELLOW)
        raise typer.Exit()


@app.command()
def version() -> None:
    """Show dotz version."""
    try:
        from importlib.metadata import version as get_version

        version_str = get_version("dotz")
    except ImportError:
        from importlib.metadata import version as get_version

        version_str = DEFAULT_VERSION
    except Exception:
        version_str = DEFAULT_VERSION

    typer.secho(f"dotz version {version_str}", fg=typer.colors.GREEN)


# ============================================================================
# UTILITY COMMANDS
# ============================================================================


@app.command()
def completion() -> None:
    """Show instructions for enabling shell completion."""
    typer.echo("Run: dotz --install-completion")


@app.command()
def diagnose() -> None:
    """
    Diagnose common dotz and git issues and print helpful advice.
    """
    typer.secho("Dotz Diagnostics", fg=typer.colors.WHITE, bold=True)
    typer.echo()

    # Check repo existence
    if not DOTZ_DIR.exists() or not WORK_TREE.exists():
        typer.secho(
            "ERROR: Dotz repository not initialized", fg=typer.colors.RED, bold=True
        )
        typer.secho("Solution: Run 'dotz init' to initialize", fg=typer.colors.CYAN)
        return

    # Check if .git exists
    git_dir = WORK_TREE / ".git"
    if not git_dir.exists():
        typer.secho(
            "ERROR: No git directory found in dotz repository", fg=typer.colors.RED
        )
        typer.secho(
            "Solution: Try re-initializing with 'dotz init'", fg=typer.colors.CYAN
        )
        return

    # Try loading the repo
    try:
        repo = Repo(str(WORK_TREE))
    except InvalidGitRepositoryError:
        typer.secho("ERROR: Invalid git repository", fg=typer.colors.RED)
        return

    # Check for remotes
    remotes = list(repo.remotes)
    if not remotes:
        typer.secho("WARNING: No git remote configured", fg=typer.colors.YELLOW)
        typer.secho(
            "Add remote: git -C ~/.dotz/repo remote add origin <url>",
            fg=typer.colors.CYAN,
        )
    else:
        typer.secho(
            f"Remote(s) configured: {', '.join(r.name for r in remotes)}",
            fg=typer.colors.GREEN,
        )

    # Check for tracking branch
    try:
        branch = repo.active_branch
        tracking = branch.tracking_branch()
        if tracking is None:
            typer.secho(
                f"WARNING: Branch '{branch.name}' is not tracking remote branch",
                fg=typer.colors.YELLOW,
            )
            typer.secho(
                f"Set upstream: git -C ~/.dotz/repo branch "
                f"--set-upstream-to=origin/{branch.name} {branch.name}",
                fg=typer.colors.CYAN,
            )
        else:
            typer.secho(
                f"Branch '{branch.name}' tracking '{tracking}'",
                fg=typer.colors.GREEN,
            )
    except Exception:
        typer.secho(
            "WARNING: Could not determine branch tracking information",
            fg=typer.colors.YELLOW,
        )

    # Check for uncommitted changes
    if repo.is_dirty(untracked_files=True):
        typer.secho("WARNING: Uncommitted changes detected", fg=typer.colors.YELLOW)
        typer.secho("Check status: dotz status", fg=typer.colors.CYAN)
    else:
        typer.secho("Repository is clean", fg=typer.colors.GREEN)

    # Check tracked directories
    tracked_dirs_file = DOTZ_DIR / "tracked_dirs.json"
    if not tracked_dirs_file.exists() or not json.loads(
        tracked_dirs_file.read_text() or "[]"
    ):
        typer.secho("WARNING: No tracked directories found", fg=typer.colors.YELLOW)
        typer.secho("Add directories: dotz add <directory>", fg=typer.colors.CYAN)
    else:
        dirs = json.loads(tracked_dirs_file.read_text())
        typer.secho(f"Tracked directories: {', '.join(dirs)}", fg=typer.colors.GREEN)

    typer.secho("Diagnosis complete", fg=typer.colors.WHITE, bold=True)


# ============================================================================
# CONFIGURATION MANAGEMENT COMMANDS
# ============================================================================

config_app = typer.Typer(help="Manage dotz configuration")
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show(
    key: Annotated[
        str,
        typer.Argument(
            help="Configuration key to show (e.g., 'file_patterns.include' "
            "or leave empty for all)"
        ),
    ] = "",
) -> None:
    """Show current configuration or a specific configuration value."""
    if key:
        value = get_config_value(key, quiet=True)
        if value is not None:
            if isinstance(value, (list, dict)):
                typer.echo(json.dumps(value, indent=2))
            else:
                typer.echo(str(value))
        else:
            typer.secho(
                f"Configuration key '{key}' not found.", fg=typer.colors.RED, err=True
            )
            raise typer.Exit(code=1)
    else:
        config = load_config()
        typer.echo(json.dumps(config, indent=2))


@config_app.command("set")
def config_set(
    key: Annotated[
        str,
        typer.Argument(
            help="Configuration key to set (e.g., 'search_settings.recursive')"
        ),
    ],
    value: Annotated[
        str, typer.Argument(help="Value to set (JSON strings for lists/objects)")
    ],
) -> None:
    """Set a configuration value."""
    success = set_config_value(key, value)
    if not success:
        raise typer.Exit(code=1)


@config_app.command("add-pattern")
def config_add_pattern(
    pattern: Annotated[
        str, typer.Argument(help="File pattern to add (e.g., '*.xml', '.bashrc')")
    ],
    pattern_type: Annotated[
        str, typer.Option("--type", "-t", help="Pattern type: 'include' or 'exclude'")
    ] = "include",
) -> None:
    """Add a file pattern to include or exclude lists."""
    success = add_file_pattern(pattern, pattern_type)
    if not success:
        raise typer.Exit(code=1)


@config_app.command("remove-pattern")
def config_remove_pattern(
    pattern: Annotated[str, typer.Argument(help="File pattern to remove")],
    pattern_type: Annotated[
        str, typer.Option("--type", "-t", help="Pattern type: 'include' or 'exclude'")
    ] = "include",
) -> None:
    """Remove a file pattern from include or exclude lists."""
    success = remove_file_pattern(pattern, pattern_type)
    if not success:
        raise typer.Exit(code=1)


@config_app.command("reset")
def config_reset(
    confirm: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """Reset configuration to defaults."""
    if not confirm:
        if not typer.confirm(
            "This will reset all configuration to defaults. Continue?"
        ):
            typer.secho("Reset cancelled.", fg=typer.colors.YELLOW)
            return

    reset_config()


@config_app.command("list-patterns")
def config_list_patterns() -> None:
    """List all current file patterns."""
    config = load_config()

    typer.secho("Include patterns:", fg=typer.colors.GREEN, bold=True)
    for pattern in config["file_patterns"]["include"]:
        typer.secho(f"  + {pattern}", fg=typer.colors.GREEN)

    typer.secho("\nExclude patterns:", fg=typer.colors.RED, bold=True)
    for pattern in config["file_patterns"]["exclude"]:
        typer.secho(f"  - {pattern}", fg=typer.colors.RED)

    typer.secho("\nSearch settings:", fg=typer.colors.BLUE, bold=True)
    for key, value in config["search_settings"].items():
        typer.secho(f"  {key}: {value}", fg=typer.colors.BLUE)


@config_app.command("help")
def config_help() -> None:
    """Show detailed help for configuration management."""
    typer.secho("Dotz Configuration Help", fg=typer.colors.WHITE, bold=True)
    typer.secho("=" * 50, fg=typer.colors.WHITE)

    typer.secho("\nFile Patterns:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  Include patterns: Files matching these patterns will be tracked")
    typer.echo("  Exclude patterns: Files matching these patterns will be ignored")
    typer.echo("  Patterns support shell-style wildcards:")
    typer.echo("    * matches any number of characters")
    typer.echo("    ? matches a single character")
    typer.echo("    [abc] matches any character in brackets")
    typer.echo("    .* matches files starting with . (dotfiles)")

    typer.secho("\nSearch Settings:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  recursive: Search subdirectories recursively")
    typer.echo("  case_sensitive: Whether pattern matching is case-sensitive")
    typer.echo("  follow_symlinks: Whether to follow symbolic links")

    typer.secho("\nExamples:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  dotz config add-pattern '*.py'        # Track Python files")
    typer.echo("  dotz config add-pattern '.env*'       # Track environment files")
    typer.echo("  dotz config add-pattern '*.log' -t exclude  # Ignore log files")
    typer.echo(
        "  dotz config set search_settings.recursive false  "
        "# Disable recursive search"
    )
    typer.echo("  dotz config show file_patterns.include  # Show include patterns")

    typer.secho("\nDefault patterns include:", fg=typer.colors.CYAN)
    typer.echo("  Dotfiles (.*), config files (*.conf, *.config, *.cfg, *.ini)")
    typer.echo("  YAML/JSON (*.yaml, *.yml, *.json), TOML files (*.toml)")

    typer.secho("\nDefault exclusions:", fg=typer.colors.CYAN)
    typer.echo("  System files (.DS_Store, .cache), VCS (.git, .svn)")
    typer.echo("  Temporary files (*.log, *.tmp)")

    typer.secho("\nConfiguration is stored in:", fg=typer.colors.MAGENTA)
    typer.echo("  ~/.dotz/config.json")


@app.command()
def clone(
    remote_url: Annotated[
        str, typer.Argument(help="Remote repository URL to clone (SSH or HTTPS)")
    ],
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """
    Clone an existing dotz repository from a remote URL and automatically restore
    all tracked dotfiles to their home directory locations.

    This enables automated setup on fresh systems.

    Examples:
      dotz clone git@github.com:username/dotfiles.git
      dotz clone https://github.com/username/dotfiles.git
    """
    success = clone_repo(remote_url, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def validate(
    repair: Annotated[
        bool,
        typer.Option("--repair", "-r", help="Automatically repair broken symlinks"),
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """
    Validate all symlinks managed by dotz and optionally repair broken ones.

    This command checks that all tracked dotfiles are properly symlinked from
    your home directory to the dotz repository. It can detect:
    - Broken symlinks (pointing to non-existent files)
    - Missing symlinks (tracked files not linked in home directory)
    - Wrong targets (symlinks pointing to wrong locations)
    - Regular files that should be symlinks

    Use --repair to automatically fix detected issues.
    """
    results = validate_symlinks(repair=repair, quiet=quiet)

    if not results:
        raise typer.Exit(code=1)

    # Calculate exit code based on results
    total_issues = (
        len(results.get("broken", []))
        + len(results.get("missing", []))
        + len(results.get("wrong_target", []))
        + len(results.get("not_symlink", []))
    )

    repair_failures = len(results.get("repair_failed", []))

    # Exit with error if there are unfixed issues
    if total_issues > 0 and not repair:
        raise typer.Exit(code=1)
    elif repair and repair_failures > 0:
        raise typer.Exit(code=1)


# ============================================================================
# BACKUP MANAGEMENT COMMANDS
# ============================================================================

backup_app = typer.Typer(help="Manage dotz backups")
app.add_typer(backup_app, name="backup")


@backup_app.command("create")
def backup_create(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to file or directory to backup (relative to your home directory)"
        ),
    ],
    operation: Annotated[
        str,
        typer.Option("--operation", "-o", help="Operation name for backup labeling"),
    ] = "manual",
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """
    Create a manual backup of a file or directory.

    This creates a timestamped backup in the dotz backups directory.
    Useful before making manual changes to important dotfiles.
    """
    home = get_home_dir()
    file_path = home / path

    if not file_path.exists():
        typer.secho(
            f"Error: {path} does not exist in your home directory.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    backup_path = create_backup(file_path, operation=operation, quiet=quiet)

    if backup_path is None:
        typer.secho(
            f"Failed to create backup for {path}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    if not quiet:
        typer.secho(
            "✓ Backup created successfully",
            fg=typer.colors.GREEN,
        )


@backup_app.command("list")
def backup_list(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed information"),
    ] = False,
) -> None:
    """
    List all available backups.

    Shows backup files sorted by creation time (newest first).
    Use --verbose for detailed information including file sizes and timestamps.
    """
    backups = list_backups()

    if not backups:
        typer.secho("No backups found.", fg=typer.colors.YELLOW)
        return

    typer.secho(f"Found {len(backups)} backup(s):", fg=typer.colors.WHITE, bold=True)
    typer.echo()

    for backup_path in backups:
        backup_name = backup_path.name
        original_file, operation, formatted_time = parse_backup_filename(backup_name)

        if original_file != backup_name:  # Successfully parsed
            if verbose:
                size = backup_path.stat().st_size
                size_str = format_file_size(size)

                typer.secho(f"{original_file}", fg=typer.colors.CYAN, bold=True)
                typer.secho(f"   Operation: {operation}", fg=typer.colors.WHITE)
                typer.secho(f"   Created:   {formatted_time}", fg=typer.colors.WHITE)
                typer.secho(f"   Size:      {size_str}", fg=typer.colors.WHITE)
                typer.secho(
                    f"   File:      {backup_name}", fg=typer.colors.BRIGHT_BLACK
                )
                typer.echo()
            else:
                typer.secho(
                    f"{original_file:<30} {operation:<12} {formatted_time}",
                    fg=typer.colors.CYAN,
                )
        else:
            # Fallback for malformed backup names
            typer.secho(f"{backup_name}", fg=typer.colors.YELLOW)


@backup_app.command("restore")
def backup_restore(
    backup_file: Annotated[
        str,
        typer.Argument(
            help="Backup filename to restore from "
            "(use 'dotz backup list' to see available backups)"
        ),
    ],
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
    confirm: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """
    Restore a file from a backup.

    This will restore the file to its original location in your home directory.
    The current file (if it exists) will be backed up before restoration.
    """
    # Find the backup file
    backups = list_backups()
    backup_path = None

    for bp in backups:
        if bp.name == backup_file:
            backup_path = bp
            break

    if backup_path is None:
        typer.secho(
            f"Error: Backup file '{backup_file}' not found.",
            fg=typer.colors.RED,
            err=True,
        )
        typer.secho(
            "Use 'dotz backup list' to see available backups.",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(code=1)

    # Parse backup filename to show what will be restored
    backup_name = backup_path.name
    original_file, operation, formatted_time = parse_backup_filename(backup_name)

    if original_file != backup_name:  # Successfully parsed
        if not confirm and not quiet:
            typer.secho(
                f"This will restore '{original_file}' from backup.",
                fg=typer.colors.CYAN,
            )
            typer.secho(f"Backup: {backup_file}", fg=typer.colors.WHITE)
            typer.secho(f"Created: {formatted_time}", fg=typer.colors.WHITE)
            typer.secho(f"Operation: {operation}", fg=typer.colors.WHITE)

            home = get_home_dir()
            target_path = home / original_file
            if target_path.exists():
                typer.secho(
                    f"WARNING: This will overwrite the current file at {original_file}",
                    fg=typer.colors.YELLOW,
                    bold=True,
                )
                typer.secho(
                    "(The current file will be backed up first)",
                    fg=typer.colors.BRIGHT_BLACK,
                )

            if not typer.confirm("Do you want to continue?"):
                typer.secho("Restore cancelled.", fg=typer.colors.YELLOW)
                return

    success = restore_from_backup(backup_path, quiet=quiet)

    if not success:
        raise typer.Exit(code=1)


@backup_app.command("clean")
def backup_clean(
    older_than_days: Annotated[
        int,
        typer.Option(
            "--older-than", "-t", help="Remove backups older than this many days"
        ),
    ] = 30,
    confirm: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """
    Clean old backup files.

    Removes backup files older than the specified number of days.
    Default is to remove backups older than 30 days.
    """
    backups = list_backups()

    if not backups:
        if not quiet:
            typer.secho("No backups found to clean.", fg=typer.colors.YELLOW)
        return

    # Filter backups older than specified days
    cutoff_time = datetime.now() - timedelta(days=older_than_days)
    old_backups = []

    for backup_path in backups:
        backup_time = datetime.fromtimestamp(backup_path.stat().st_mtime)
        if backup_time < cutoff_time:
            old_backups.append(backup_path)

    if not old_backups:
        if not quiet:
            typer.secho(
                f"No backups older than {older_than_days} days found.",
                fg=typer.colors.GREEN,
            )
        return

    if not confirm and not quiet:
        typer.secho(
            f"Found {len(old_backups)} backup(s) older than {older_than_days} days:",
            fg=typer.colors.YELLOW,
        )

        for backup_path in old_backups[:5]:  # Show first 5
            backup_time = datetime.fromtimestamp(backup_path.stat().st_mtime)
            typer.secho(
                f"  {backup_path.name} ({backup_time.strftime('%Y-%m-%d')})",
                fg=typer.colors.WHITE,
            )

        if len(old_backups) > 5:
            typer.secho(
                f"  ... and {len(old_backups) - 5} more",
                fg=typer.colors.BRIGHT_BLACK,
            )

        if not typer.confirm(f"Delete these {len(old_backups)} backup(s)?"):
            typer.secho("Cleanup cancelled.", fg=typer.colors.YELLOW)
            return

    # Remove old backups
    removed_count = 0
    failed_count = 0

    for backup_path in old_backups:
        try:
            backup_path.unlink()
            removed_count += 1
            if not quiet:
                typer.secho(f"Removed {backup_path.name}", fg=typer.colors.GREEN)
        except Exception as e:
            failed_count += 1
            if not quiet:
                typer.secho(
                    f"Failed to remove {backup_path.name}: {e}",
                    fg=typer.colors.RED,
                )

    if not quiet:
        if removed_count > 0:
            typer.secho(
                f"Successfully removed {removed_count} backup(s)",
                fg=typer.colors.GREEN,
                bold=True,
            )
        if failed_count > 0:
            typer.secho(
                f"Failed to remove {failed_count} backup(s)",
                fg=typer.colors.RED,
                bold=True,
            )


@backup_app.command("help")
def backup_help() -> None:
    """Show detailed help for backup management."""
    typer.secho("Dotz Backup Management Help", fg=typer.colors.WHITE, bold=True)
    typer.secho("=" * 50, fg=typer.colors.WHITE)

    typer.secho("\nBackup System:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  Dotz automatically creates backups when:")
    typer.echo("  Restoring files that would overwrite existing files")
    typer.echo("  Cloning a repository that would overwrite existing files")
    typer.echo("  Running operations that modify existing dotfiles")
    typer.echo("  You manually create backups with 'dotz backup create'")

    typer.secho("\nBackup Location:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  All backups are stored in: ~/.dotz/backups/")
    typer.echo("  Backup files use format: <path>_<operation>_<timestamp>")

    typer.secho("\nCommands:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  create    Create a manual backup of a file")
    typer.echo("  list      List all available backups")
    typer.echo("  restore   Restore a file from backup")
    typer.echo("  clean     Remove old backup files")
    typer.echo("  help      Show this help message")

    typer.secho("\nExamples:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  dotz backup create .bashrc              " "# Backup .bashrc manually")
    typer.echo("  dotz backup list                        " "# List all backups")
    typer.echo("  dotz backup list --verbose              " "# List with details")
    typer.echo(
        "  dotz backup restore .bashrc_manual_20250708_143022  " "# Restore backup"
    )
    typer.echo("  dotz backup clean --older-than 7        " "# Remove old backups")
    typer.echo("  dotz backup clean --older-than 30 --yes " "# Skip confirmation")

    typer.secho("\nSafety Features:", fg=typer.colors.CYAN, bold=True)
    typer.echo("  Existing files are automatically backed up before restoration")
    typer.echo("  Backups include timestamps for easy identification")
    typer.echo("  Multiple backups of the same file are preserved")
    typer.echo("  Confirmation prompts prevent accidental operations")


@app.command()
def commit(
    message: Annotated[
        str, typer.Option("--message", "-m", help="Commit message")
    ] = "",
    files: Annotated[
        Optional[List[str]],
        typer.Option("--file", "-f", help="Specific files to commit (optional)"),
    ] = None,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """
    Commit modified files in the dotz repository.

    This command stages and commits changes to tracked dotfiles.
    If no files are specified, all modified files will be committed.
    """
    if not message:
        # Get status to show what will be committed
        status_data = get_repo_status()

        if not status_data["modified"] and not status_data["untracked"]:
            typer.secho("No changes to commit", fg=typer.colors.YELLOW)
            return

        typer.secho("Files to be committed:", fg=typer.colors.CYAN)
        for file in status_data["modified"]:
            typer.secho(f"  modified: {file}", fg=typer.colors.YELLOW)
        for file in status_data["untracked"]:
            typer.secho(f"  new file: {file}", fg=typer.colors.GREEN)

        message = typer.prompt("Enter commit message")

    success = commit_repo(message=message, files=files, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def diff(
    files: Annotated[
        Optional[List[str]],
        typer.Argument(help="Files to show diff for (optional - shows all if empty)"),
    ] = None,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """
    Show differences in modified files.

    Displays what has changed in your dotfiles since the last commit.
    If no files are specified, shows changes for all modified files.
    """
    success = diff_files(files=files, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def gui() -> None:
    """
    Launch the graphical user interface.

    Opens the dotz GUI application for managing dotfiles with a
    point-and-click interface.
    """
    try:
        # Import GUI here to avoid dependency issues if PySide6 is not installed
        from .gui.main import main as gui_main
    except ImportError:
        typer.secho(
            "Error: GUI dependencies not installed. "
            "Install with: pip install dotz[gui]",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        gui_main()
    except Exception as e:
        typer.secho(
            f"Error launching GUI: {e}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)


# ============================================================================
# TEMPLATE MANAGEMENT COMMANDS
# ============================================================================

template_app = typer.Typer(help="Manage dotfile templates")
app.add_typer(template_app, name="template")


@template_app.command("create")
def template_create(
    name: Annotated[str, typer.Argument(help="Template name")],
    description: Annotated[
        str, typer.Option("--description", "-d", help="Template description")
    ] = "",
    files: Annotated[
        Optional[List[str]],
        typer.Option("--file", "-f", help="Specific files to include (optional)"),
    ] = None,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """Create a new template from current tracked files or specified files."""
    success = templates.create_template(
        name=name, description=description, files=files, quiet=quiet
    )
    if not success:
        raise typer.Exit(code=1)


@template_app.command("list")
def template_list(
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show detailed information")
    ] = False,
) -> None:
    """List all available templates."""
    template_list = templates.list_templates()

    if not template_list:
        typer.secho("No templates found.", fg=typer.colors.YELLOW)
        return

    typer.secho(
        f"Found {len(template_list)} template(s):", fg=typer.colors.WHITE, bold=True
    )
    typer.echo()

    for template in template_list:
        name = template.get("name", "unknown")
        description = template.get("description", "")
        created = template.get("created", "unknown")
        file_count = template.get("file_count", 0)

        if verbose:
            typer.secho(f"{name}", fg=typer.colors.CYAN, bold=True)
            if description:
                typer.secho(f"   Description: {description}", fg=typer.colors.WHITE)
            typer.secho(f"   Created:     {created}", fg=typer.colors.WHITE)
            typer.secho(f"   Files:       {file_count}", fg=typer.colors.WHITE)

            # Get additional info
            info = templates.get_template_info(name)
            if info:
                total_size = info.get("total_size", 0)
                size_str = format_file_size(total_size)
                typer.secho(f"   Size:        {size_str}", fg=typer.colors.WHITE)

            typer.echo()
        else:
            desc_part = f" - {description}" if description else ""
            typer.secho(
                f"{name:<20} {file_count:>3} files   {created}{desc_part}",
                fg=typer.colors.CYAN,
            )


@template_app.command("apply")
def template_apply(
    name: Annotated[str, typer.Argument(help="Template name to apply")],
    merge: Annotated[
        bool,
        typer.Option("--merge", help="Merge mode - don't overwrite existing files"),
    ] = False,
    no_backup: Annotated[
        bool, typer.Option("--no-backup", help="Skip creating backup")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """Apply a template to the current dotz repository."""
    success = templates.apply_template(
        name=name, merge=merge, backup=not no_backup, quiet=quiet
    )
    if not success:
        raise typer.Exit(code=1)


@template_app.command("delete")
def template_delete(
    name: Annotated[str, typer.Argument(help="Template name to delete")],
    confirm: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """Delete a template."""
    if not confirm and not quiet:
        if not typer.confirm(f"Delete template '{name}'?"):
            typer.secho("Deletion cancelled.", fg=typer.colors.YELLOW)
            return

    success = templates.delete_template(name=name, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@template_app.command("export")
def template_export(
    name: Annotated[str, typer.Argument(help="Template name to export")],
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output file path")
    ] = "",
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """Export a template as a portable archive."""
    if not output:
        output = f"{name}.tar.gz"

    success = templates.export_template(name=name, output_path=output, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@template_app.command("import")
def template_import(
    archive: Annotated[str, typer.Argument(help="Archive file to import")],
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """Import a template from an archive."""
    success = templates.import_template(archive_path=archive, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@template_app.command("info")
def template_info(
    name: Annotated[str, typer.Argument(help="Template name")],
) -> None:
    """Show detailed information about a template."""
    info = templates.get_template_info(name)

    if not info:
        typer.secho(f"Template '{name}' not found.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.secho(f"Template: {name}", fg=typer.colors.CYAN, bold=True)
    typer.echo()

    description = info.get("description", "")
    if description:
        typer.secho(f"Description:  {description}", fg=typer.colors.WHITE)

    typer.secho(
        f"Created:      {info.get('created', 'unknown')}", fg=typer.colors.WHITE
    )
    typer.secho(f"Files:        {info.get('file_count', 0)}", fg=typer.colors.WHITE)

    total_size = info.get("total_size", 0)
    size_str = format_file_size(total_size)
    typer.secho(f"Size:         {size_str}", fg=typer.colors.WHITE)
    typer.secho(
        f"Version:      {info.get('version', 'unknown')}", fg=typer.colors.WHITE
    )

    files = info.get("files", [])
    if files:
        typer.echo()
        typer.secho("Files included:", fg=typer.colors.YELLOW, bold=True)
        for file_path in files[:10]:  # Show first 10
            typer.secho(f"  {file_path}", fg=typer.colors.WHITE)

        if len(files) > 10:
            typer.secho(
                f"  ... and {len(files) - 10} more files", fg=typer.colors.BRIGHT_BLACK
            )


@template_app.command("help")
def template_help() -> None:
    """Show detailed help for template management."""
    typer.secho("Dotz Template Management Help", fg=typer.colors.WHITE, bold=True)
    typer.secho("=" * 50, fg=typer.colors.WHITE)

    typer.secho("\nTemplates:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  Templates are snapshots of your dotfiles configuration that can be")
    typer.echo("  applied to quickly set up specific environments or restore known")
    typer.echo("  working configurations.")

    typer.secho("\nUse Cases:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  • Save working configurations before experimenting")
    typer.echo("  • Create environment-specific setups (work, personal, minimal)")
    typer.echo("  • Share configurations with others")
    typer.echo("  • Quick setup on new machines")

    typer.secho("\nCommands:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  create    Create template from current files")
    typer.echo("  list      List all available templates")
    typer.echo("  apply     Apply template to current repository")
    typer.echo("  delete    Delete a template")
    typer.echo("  export    Export template as portable archive")
    typer.echo("  import    Import template from archive")
    typer.echo("  info      Show detailed template information")

    typer.secho("\nExamples:", fg=typer.colors.YELLOW, bold=True)
    typer.echo('  dotz template create work -d "Work environment setup"')
    typer.echo("  dotz template list --verbose")
    typer.echo("  dotz template apply work --merge")
    typer.echo("  dotz template export work -o work-config.tar.gz")
    typer.echo("  dotz template import shared-config.tar.gz")

    typer.secho("\nTemplate Storage:", fg=typer.colors.CYAN, bold=True)
    typer.echo("  Templates are stored in: ~/.dotz/templates/")
    typer.echo("  Each template contains: files/, template.json")


# ============================================================================
# PROFILE MANAGEMENT COMMANDS
# ============================================================================

profile_app = typer.Typer(help="Manage dotfile profiles for different environments")
app.add_typer(profile_app, name="profile")


@profile_app.command("create")
def profile_create(
    name: Annotated[str, typer.Argument(help="Profile name")],
    description: Annotated[
        str, typer.Option("--description", "-d", help="Profile description")
    ] = "",
    environment: Annotated[
        str,
        typer.Option(
            "--env", "-e", help="Environment type (work, personal, server, etc.)"
        ),
    ] = "",
    copy_from: Annotated[
        str, typer.Option("--copy-from", help="Copy from existing profile")
    ] = "",
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """Create a new profile for managing different dotfile environments."""
    success = templates.create_profile(
        name=name,
        description=description,
        environment=environment,
        copy_from=copy_from if copy_from else None,
        quiet=quiet,
    )
    if not success:
        raise typer.Exit(code=1)


@profile_app.command("list")
def profile_list(
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show detailed information")
    ] = False,
) -> None:
    """List all available profiles."""
    profile_list = templates.list_profiles()

    if not profile_list:
        typer.secho("No profiles found.", fg=typer.colors.YELLOW)
        typer.echo("Create a profile with: dotz profile create <name>")
        return

    typer.secho(
        f"Found {len(profile_list)} profile(s):", fg=typer.colors.WHITE, bold=True
    )
    typer.echo()

    for profile in profile_list:
        name = profile.get("name", "unknown")
        description = profile.get("description", "")
        environment = profile.get("environment", "")
        created = profile.get("created", "unknown")
        last_used = profile.get("last_used", "never")
        active = profile.get("active", False)

        # Format active indicator
        active_indicator = " ●" if active else "  "

        if verbose:
            color = typer.colors.GREEN if active else typer.colors.CYAN
            typer.secho(f"{active_indicator} {name}", fg=color, bold=True)
            if description:
                typer.secho(f"     Description: {description}", fg=typer.colors.WHITE)
            if environment:
                typer.secho(f"     Environment: {environment}", fg=typer.colors.WHITE)
            typer.secho(f"     Created:     {created}", fg=typer.colors.WHITE)
            typer.secho(f"     Last used:   {last_used}", fg=typer.colors.WHITE)

            # Get additional info
            info = templates.get_profile_info(name)
            if info:
                file_count = info.get("file_count", 0)
                total_size = info.get("total_size", 0)
                size_str = format_file_size(total_size)
                typer.secho(f"     Files:       {file_count}", fg=typer.colors.WHITE)
                typer.secho(f"     Size:        {size_str}", fg=typer.colors.WHITE)

            if active:
                typer.secho(
                    "     Status:      ACTIVE", fg=typer.colors.GREEN, bold=True
                )

            typer.echo()
        else:
            color = typer.colors.GREEN if active else typer.colors.CYAN
            env_part = f" ({environment})" if environment else ""
            desc_part = f" - {description}" if description else ""
            typer.secho(
                f"{active_indicator} {name:<18}{env_part:<12} {last_used}{desc_part}",
                fg=color,
            )


@profile_app.command("switch")
def profile_switch(
    name: Annotated[str, typer.Argument(help="Profile name to switch to")],
    no_backup: Annotated[
        bool, typer.Option("--no-backup", help="Skip saving current state")
    ] = False,
    confirm: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """Switch to a different profile."""
    current_profile = templates.get_active_profile()

    if current_profile == name:
        if not quiet:
            typer.secho(f"Already using profile '{name}'", fg=typer.colors.YELLOW)
        return

    if not confirm and not quiet:
        typer.secho(f"Switch to profile '{name}'?", fg=typer.colors.CYAN)
        if current_profile:
            backup_msg = (
                "save current state" if not no_backup else "discard current state"
            )
            typer.secho(
                f"Current profile '{current_profile}' will {backup_msg}",
                fg=typer.colors.WHITE,
            )

        if not typer.confirm("Continue?"):
            typer.secho("Profile switch cancelled.", fg=typer.colors.YELLOW)
            return

    success = templates.switch_profile(name=name, backup=not no_backup, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@profile_app.command("delete")
def profile_delete(
    name: Annotated[str, typer.Argument(help="Profile name to delete")],
    confirm: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
) -> None:
    """Delete a profile."""
    if not confirm and not quiet:
        if not typer.confirm(f"Delete profile '{name}'?"):
            typer.secho("Deletion cancelled.", fg=typer.colors.YELLOW)
            return

    success = templates.delete_profile(name=name, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@profile_app.command("current")
def profile_current() -> None:
    """Show the currently active profile."""
    active_profile = templates.get_active_profile()

    if not active_profile:
        typer.secho("No active profile", fg=typer.colors.YELLOW)
        typer.echo("Create a profile with: dotz profile create <name>")
        return

    info = templates.get_profile_info(active_profile)

    if not info:
        typer.secho(
            f"Active profile '{active_profile}' (metadata not found)",
            fg=typer.colors.RED,
        )
        return

    typer.secho(f"Active profile: {active_profile}", fg=typer.colors.GREEN, bold=True)

    description = info.get("description", "")
    if description:
        typer.secho(f"Description: {description}", fg=typer.colors.WHITE)

    environment = info.get("environment", "")
    if environment:
        typer.secho(f"Environment: {environment}", fg=typer.colors.WHITE)

    typer.secho(f"Last used: {info.get('last_used', 'never')}", fg=typer.colors.WHITE)
    typer.secho(f"Files: {info.get('file_count', 0)}", fg=typer.colors.WHITE)


@profile_app.command("info")
def profile_info(
    name: Annotated[str, typer.Argument(help="Profile name")],
) -> None:
    """Show detailed information about a profile."""
    info = templates.get_profile_info(name)

    if not info:
        typer.secho(f"Profile '{name}' not found.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    active = info.get("active", False)
    color = typer.colors.GREEN if active else typer.colors.CYAN

    typer.secho(f"Profile: {name}", fg=color, bold=True)
    if active:
        typer.secho("Status: ACTIVE", fg=typer.colors.GREEN, bold=True)
    typer.echo()

    description = info.get("description", "")
    if description:
        typer.secho(f"Description:  {description}", fg=typer.colors.WHITE)

    environment = info.get("environment", "")
    if environment:
        typer.secho(f"Environment:  {environment}", fg=typer.colors.WHITE)

    typer.secho(
        f"Created:      {info.get('created', 'unknown')}", fg=typer.colors.WHITE
    )
    typer.secho(
        f"Last used:    {info.get('last_used', 'never')}", fg=typer.colors.WHITE
    )
    typer.secho(f"Files:        {info.get('file_count', 0)}", fg=typer.colors.WHITE)

    total_size = info.get("total_size", 0)
    size_str = format_file_size(total_size)
    typer.secho(f"Size:         {size_str}", fg=typer.colors.WHITE)
    typer.secho(
        f"Version:      {info.get('version', 'unknown')}", fg=typer.colors.WHITE
    )


@profile_app.command("help")
def profile_help() -> None:
    """Show detailed help for profile management."""
    typer.secho("Dotz Profile Management Help", fg=typer.colors.WHITE, bold=True)
    typer.secho("=" * 50, fg=typer.colors.WHITE)

    typer.secho("\nProfiles:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  Profiles are complete dotfile environments that you can switch")
    typer.echo("  between. Each profile maintains its own set of files and")
    typer.echo("  configuration, perfect for different contexts or environments.")

    typer.secho("\nUse Cases:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  • Work vs Personal configurations")
    typer.echo("  • Development vs Production environments")
    typer.echo("  • Minimal vs Full feature setups")
    typer.echo("  • Machine-specific configurations")

    typer.secho("\nCommands:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  create    Create a new profile")
    typer.echo("  list      List all available profiles")
    typer.echo("  switch    Switch to a different profile")
    typer.echo("  current   Show the currently active profile")
    typer.echo("  delete    Delete a profile")
    typer.echo("  info      Show detailed profile information")

    typer.secho("\nExamples:", fg=typer.colors.YELLOW, bold=True)
    typer.echo('  dotz profile create work -d "Work setup" -e work')
    typer.echo("  dotz profile create personal --copy-from work")
    typer.echo("  dotz profile list --verbose")
    typer.echo("  dotz profile switch work")
    typer.echo("  dotz profile current")

    typer.secho("\nProfile Switching:", fg=typer.colors.CYAN, bold=True)
    typer.echo("  When switching profiles:")
    typer.echo("  • Current state is automatically saved to the current profile")
    typer.echo("  • Repository is updated with the new profile's files")
    typer.echo("  • Configuration settings are updated")
    typer.echo("  • Changes are committed to git")

    typer.secho("\nProfile Storage:", fg=typer.colors.CYAN, bold=True)
    typer.echo("  Profiles are stored in: ~/.dotz/profiles/")
    typer.echo("  Each profile contains: files/, config/, profile.json")
    typer.echo("  Active profile is tracked in: ~/.dotz/active_profile")


if __name__ == "__main__":
    app()
