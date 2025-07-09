import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import typer
from git import Repo
from typing_extensions import Annotated

from .core import (
    add_dotfile,
    add_file_pattern,
    clone_repo,
    create_backup,
    delete_dotfile,
    get_config_value,
    get_home_dir,
    get_repo_status,
    init_repo,
    list_backups,
    list_tracked_files,
    load_config,
    pull_repo,
    push_repo,
    remove_file_pattern,
    reset_config,
    restore_all_dotfiles,
    restore_dotfile,
    restore_from_backup,
    set_config_value,
    validate_symlinks,
)
from .watcher import main as watcher_main

app = typer.Typer(help="loom - a Git-backed dot-files manager")


def get_cli_paths() -> Tuple[Path, Path, Path]:
    """Get CLI-related paths based on current home directory."""
    home = get_home_dir()
    loom_dir = home / ".loom"
    work_tree = loom_dir / "repo"
    return home, loom_dir, work_tree


HOME, LOOM_DIR, WORK_TREE = get_cli_paths()


def refresh_cli_paths() -> None:
    """Refresh CLI paths when HOME environment changes."""
    global HOME, LOOM_DIR, WORK_TREE
    HOME, LOOM_DIR, WORK_TREE = get_cli_paths()


def update_cli_paths(home_dir: Path) -> None:
    """Update CLI paths. Useful for testing."""
    global HOME, LOOM_DIR, WORK_TREE
    HOME = home_dir
    LOOM_DIR = home_dir / ".loom"
    WORK_TREE = home_dir / ".loom" / "repo"


@app.command()
def init(
    remote: Annotated[
        str, typer.Option(help="Optional remote URL to add as origin (SSH or HTTPS).")
    ] = "",
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive",
            "-n",
            help="Run without prompts (for scripting)",
            is_flag=True,
        ),
    ] = False,
) -> None:
    """Initialize a new loom repository."""
    if not non_interactive and not remote:
        typer.secho("loom Interactive Setup", fg=typer.colors.CYAN, bold=True)
        typer.echo(
            "Welcome! Let's configure your loom repository for managing dotfiles.\n"
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
                            "Invalid URL format. Please use https://, git@, or "
                            "ssh:// URLs.",
                            fg=typer.colors.RED,
                        )
                else:
                    typer.secho(
                        "URL cannot be empty. Please enter a valid URL or press "
                        "Ctrl+C to skip.",
                        fg=typer.colors.RED,
                    )
        else:
            remote = ""

        # Initial dotfiles setup
        typer.echo()
        typer.secho("Initial Dotfiles Setup", fg=typer.colors.BLUE, bold=True)
        typer.echo(
            "Would you like to automatically add common dotfiles to get started?"
        )
        typer.echo("This will search for and add files like:")
        typer.echo("  • Shell configs: .bashrc, .zshrc, .profile")
        typer.echo("  • Git config: .gitconfig, .gitignore_global")
        typer.echo("  • SSH config: .ssh/config")
        typer.echo("  • Editor configs: .vimrc, .tmux.conf")

        setup_dotfiles = typer.confirm(
            "\nAutomatically discover and add common dotfiles?", default=True
        )

        typer.echo()
        typer.secho("Initializing loom repository...", fg=typer.colors.CYAN)
    else:
        setup_dotfiles = False

    success = init_repo(remote=remote, quiet=False)
    if not success:
        raise typer.Exit(code=1)

    # Handle initial dotfiles setup if requested
    if setup_dotfiles:
        typer.echo()
        typer.secho("Discovering common dotfiles...", fg=typer.colors.CYAN)

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
                typer.echo(f"  • {f}")

            if typer.confirm(
                f"\nAdd these {len(found_files)} files to loom?", default=True
            ):
                added_count = 0
                for dotfile in found_files:
                    try:
                        success = add_dotfile(
                            Path(dotfile), push=False, quiet=True, recursive=False
                        )
                        if success:
                            added_count += 1
                            typer.secho(f"  ✓ Added {dotfile}", fg=typer.colors.GREEN)
                    except Exception:
                        typer.secho(
                            f"  ! Could not add {dotfile}", fg=typer.colors.YELLOW
                        )

                if added_count > 0:
                    typer.secho(
                        f"\nSuccessfully added {added_count} dotfiles!",
                        fg=typer.colors.GREEN,
                    )
                else:
                    typer.secho("No dotfiles were added.", fg=typer.colors.YELLOW)
            else:
                typer.secho("Skipped automatic dotfile setup.", fg=typer.colors.YELLOW)
        else:
            typer.secho(
                "No common dotfiles found in your home directory.",
                fg=typer.colors.YELLOW,
            )
            typer.echo("You can add dotfiles later with: loom add <filename>")

    # Show completion message
    typer.echo()
    typer.secho("Repository initialization complete!", fg=typer.colors.GREEN, bold=True)

    if remote:
        typer.secho(
            "Next steps:",
            fg=typer.colors.CYAN,
        )
        typer.echo("  • Add more dotfiles: loom add <filename>")
        typer.echo("  • Push to remote: loom push")
        typer.echo("  • Check status: loom status")
    else:
        typer.secho(
            "Next steps:",
            fg=typer.colors.CYAN,
        )
        typer.echo("  • Add dotfiles: loom add <filename>")
        typer.echo("  • Add remote later: git -C ~/.loom/repo remote add origin <url>")
        typer.echo("  • Check status: loom status")


@app.command()
def add(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to dotfile or directory (relative to your home directory)"
        ),
    ],
    push: Annotated[
        bool, typer.Option("--push", "-p", help="Push commit to origin", is_flag=True)
    ] = False,
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive/--no-recursive",
            help="Recursively add dotfiles in subdirectories",
            is_flag=True,
        ),
    ] = True,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
) -> None:
    """Add a file or directory to loom, then symlink it in your home directory."""
    success = add_dotfile(path, push=push, quiet=quiet, recursive=recursive)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def delete(
    path: Annotated[
        List[Path], typer.Argument(help="Paths to dotfiles or directories to delete")
    ],
    push: Annotated[
        bool, typer.Option("--push", "-p", help="Push commit to origin", is_flag=True)
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
) -> None:
    """
    Remove a loom-managed file or directory and delete the symlink in your
    home directory.
    """
    success = delete_dotfile(path, push=push, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def status() -> None:
    """
    Show the status of your loom repo (untracked, modified, staged), and
    dotfiles in $HOME not tracked by loom.
    """
    status_data = get_repo_status()

    typer.secho("Status of loom repository:", fg=typer.colors.WHITE)

    if (
        not status_data["untracked"]
        and not status_data["modified"]
        and not status_data["staged"]
    ):
        typer.secho("✓ No changes", fg=typer.colors.GREEN)
    else:
        if status_data["untracked"]:
            typer.secho("Untracked files:", fg=typer.colors.YELLOW)
            for file in status_data["untracked"]:
                typer.secho(f"  - {file}", fg=typer.colors.YELLOW)
        if status_data["modified"]:
            typer.secho("Modified files:", fg=typer.colors.YELLOW)
            for file in status_data["modified"]:
                typer.secho(f"  - {file}", fg=typer.colors.YELLOW)
        if status_data["staged"]:
            typer.secho("Staged files:", fg=typer.colors.YELLOW)
            for file in status_data["staged"]:
                typer.secho(f"  - {file}", fg=typer.colors.YELLOW)

    if status_data["unpushed"]:
        typer.secho("Unpushed changes:", fg=typer.colors.YELLOW)
        for file in status_data["unpushed"]:
            typer.secho(f"  - {file}", fg=typer.colors.YELLOW)

    if status_data["untracked_home_dotfiles"]:
        typer.secho("Dotfiles in $HOME not tracked by loom:", fg=typer.colors.MAGENTA)
        for f in status_data["untracked_home_dotfiles"]:
            typer.secho(f"  - {f}", fg=typer.colors.MAGENTA)


@app.command()
def list_files() -> None:
    """
    List all files currently tracked by loom.
    """
    tracked_files = list_tracked_files()
    if not tracked_files:
        typer.secho("No files tracked by loom.", fg=typer.colors.YELLOW)
        return

    typer.secho("Files tracked by loom:", fg=typer.colors.WHITE)
    for f in tracked_files:
        typer.secho(f"  - {f}", fg=typer.colors.YELLOW)


@app.command()
def restore(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to dotfile or directory (relative to your home directory)"
        ),
    ],
    push: Annotated[
        bool, typer.Option("--push", "-p", help="Push commit to origin", is_flag=True)
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
) -> None:
    """
    Restore a dotfile or directory from the loom repository to your home directory.
    Overwrites any existing file or symlink at that location.
    """
    success = restore_dotfile(path, quiet=quiet, push=push)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def pull(
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
) -> None:
    """
    Pull the latest changes from the 'origin' remote into the local loom repository.
    """
    success = pull_repo(quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def push(
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
) -> None:
    """
    Push all local commits to the 'origin' remote, if it exists.
    """
    success = push_repo(quiet=quiet)
    if not success:
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
    """Show loom version."""
    typer.secho("loom version 0.3.0", fg=typer.colors.GREEN)


@app.command()
def completion() -> None:
    """
    Show instructions for enabling shell completion.
    """
    typer.echo("Run: loom --install-completion")


@app.command()
def diagnose() -> None:
    """
    Diagnose common loom and git issues and print helpful advice.
    """
    from git import InvalidGitRepositoryError

    typer.secho("Running loom diagnostics...\n", fg=typer.colors.WHITE, bold=True)

    # Check repo existence
    if not LOOM_DIR.exists() or not WORK_TREE.exists():
        typer.secho("ERROR: loom repo not initialized.", fg=typer.colors.RED)
        typer.secho("Run: loom init", fg=typer.colors.YELLOW)
        return

    # Check if .git exists
    git_dir = WORK_TREE / ".git"
    if not git_dir.exists():
        typer.secho("ERROR: No .git directory found in loom repo.", fg=typer.colors.RED)
        typer.secho("Try re-initializing with: loom init", fg=typer.colors.YELLOW)
        return

    # Try loading the repo
    try:
        repo = Repo(str(WORK_TREE))
    except InvalidGitRepositoryError:
        typer.secho("ERROR: Invalid git repository in loom repo.", fg=typer.colors.RED)
        return

    # Check for remotes
    remotes = list(repo.remotes)
    if not remotes:
        typer.secho("WARNING: No git remote set.", fg=typer.colors.YELLOW)
        typer.secho(
            "Set one with: git -C ~/.loom/repo remote add origin <url>",
            fg=typer.colors.YELLOW,
        )
    else:
        typer.secho(
            f"✓ Remote(s) found: {', '.join(r.name for r in remotes)}",
            fg=typer.colors.GREEN,
        )

    # Check for tracking branch
    try:
        branch = repo.active_branch
        tracking = branch.tracking_branch()
        if tracking is None:
            typer.secho(
                f"WARNING: Branch '{branch.name}' is not tracking a remote " "branch.",
                fg=typer.colors.YELLOW,
            )
            typer.secho(
                f"Set upstream with: git -C ~/.loom/repo branch "
                f"--set-upstream-to=origin/{branch.name} {branch.name}",
                fg=typer.colors.YELLOW,
            )
        else:
            typer.secho(
                f"✓ Branch '{branch.name}' is tracking '{tracking}'",
                fg=typer.colors.GREEN,
            )
    except Exception:
        typer.secho(
            "WARNING: Could not determine active branch or tracking info.",
            fg=typer.colors.YELLOW,
        )

    # Check for uncommitted changes
    if repo.is_dirty(untracked_files=True):
        typer.secho(
            "WARNING: There are uncommitted changes in your loom repo.",
            fg=typer.colors.YELLOW,
        )
        typer.secho("Run: loom status", fg=typer.colors.YELLOW)
    else:
        typer.secho("✓ No uncommitted changes.", fg=typer.colors.GREEN)

    # Check tracked directories
    tracked_dirs_file = LOOM_DIR / "tracked_dirs.json"
    if not tracked_dirs_file.exists() or not json.loads(
        tracked_dirs_file.read_text() or "[]"
    ):
        typer.secho("WARNING: No tracked directories found.", fg=typer.colors.YELLOW)
        typer.secho("Add one with: loom add <directory>", fg=typer.colors.YELLOW)
    else:
        dirs = json.loads(tracked_dirs_file.read_text())
        typer.secho(f"✓ Tracked directories: {', '.join(dirs)}", fg=typer.colors.GREEN)

    typer.secho("\nDiagnosis complete.", fg=typer.colors.WHITE, bold=True)


# Configuration management commands
config_app = typer.Typer(help="Manage loom configuration")
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
    typer.secho("Loom Configuration Help", fg=typer.colors.WHITE, bold=True)
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
    typer.echo("  loom config add-pattern '*.py'        # Track Python files")
    typer.echo("  loom config add-pattern '.env*'       # Track environment files")
    typer.echo("  loom config add-pattern '*.log' -t exclude  # Ignore log files")
    typer.echo(
        "  loom config set search_settings.recursive false  "
        "# Disable recursive search"
    )
    typer.echo("  loom config show file_patterns.include  # Show include patterns")

    typer.secho("\nDefault patterns include:", fg=typer.colors.CYAN)
    typer.echo("  Dotfiles (.*), config files (*.conf, *.config, *.cfg, *.ini)")
    typer.echo("  YAML/JSON (*.yaml, *.yml, *.json), TOML files (*.toml)")

    typer.secho("\nDefault exclusions:", fg=typer.colors.CYAN)
    typer.echo("  System files (.DS_Store, .cache), VCS (.git, .svn)")
    typer.echo("  Temporary files (*.log, *.tmp)")

    typer.secho("\nConfiguration is stored in:", fg=typer.colors.MAGENTA)
    typer.echo("  ~/.loom/config.json")


@app.command()
def clone(
    remote_url: Annotated[
        str, typer.Argument(help="Remote repository URL to clone (SSH or HTTPS)")
    ],
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
) -> None:
    """
    Clone an existing loom repository from a remote URL and automatically restore
    all tracked dotfiles to their home directory locations.

    This enables automated setup on fresh systems.

    Examples:
      loom clone git@github.com:username/dotfiles.git
      loom clone https://github.com/username/dotfiles.git
    """
    success = clone_repo(remote_url, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def restore_all(
    push: Annotated[
        bool, typer.Option("--push", "-p", help="Push commit to origin", is_flag=True)
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
    confirm: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
) -> None:
    """
    Restore all tracked dotfiles from the loom repository to your home directory.
    Creates symlinks for all files currently tracked by loom.
    This is useful for setting up dotfiles on a new system or when you want
    to restore all files at once.
    """
    if not confirm and not quiet:
        # Show what will be restored
        from .core import list_tracked_files

        tracked_files = list_tracked_files()

        if not tracked_files:
            typer.secho("No files tracked by loom to restore.", fg=typer.colors.YELLOW)
            return

        typer.secho(
            f"This will restore {len(tracked_files)} tracked files:",
            fg=typer.colors.CYAN,
        )
        for file_path in tracked_files[:10]:  # Show first 10
            typer.secho(f"  • {file_path}", fg=typer.colors.WHITE)

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

    success = restore_all_dotfiles(quiet=quiet, push=push)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def validate(
    repair: Annotated[
        bool,
        typer.Option("--repair", "-r", help="Automatically repair broken symlinks"),
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
) -> None:
    """
    Validate all symlinks managed by loom and optionally repair broken ones.

    This command checks that all tracked dotfiles are properly symlinked from
    your home directory to the loom repository. It can detect:
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


# Backup management commands
backup_app = typer.Typer(help="Manage loom backups")
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
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
) -> None:
    """
    Create a manual backup of a file or directory.

    This creates a timestamped backup in the loom backups directory.
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
        typer.Option("--verbose", "-v", help="Show detailed information", is_flag=True),
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

        # Parse backup filename to extract information
        parts = backup_name.split("_")
        if len(parts) >= 3:
            # Reconstruct original path (everything before operation and timestamp)
            operation_idx = -2
            original_parts = parts[:operation_idx]
            original_file = "/".join(original_parts)
            operation = parts[operation_idx]
            timestamp = parts[-1]

            # Format timestamp for display
            try:
                dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                formatted_time = timestamp

            if verbose:
                # Get file size
                size = backup_path.stat().st_size
                size_str = f"{size:,} bytes"
                if size > 1024:
                    size_kb = size / 1024
                    if size_kb > 1024:
                        size_mb = size_kb / 1024
                        size_str = f"{size_mb:.1f} MB"
                    else:
                        size_str = f"{size_kb:.1f} KB"

                typer.secho(f"📦 {original_file}", fg=typer.colors.CYAN, bold=True)
                typer.secho(f"   Operation: {operation}", fg=typer.colors.WHITE)
                typer.secho(f"   Created:   {formatted_time}", fg=typer.colors.WHITE)
                typer.secho(f"   Size:      {size_str}", fg=typer.colors.WHITE)
                typer.secho(
                    f"   File:      {backup_name}", fg=typer.colors.BRIGHT_BLACK
                )
                typer.echo()
            else:
                typer.secho(
                    f"📦 {original_file:<30} {operation:<12} {formatted_time}",
                    fg=typer.colors.CYAN,
                )
        else:
            # Fallback for malformed backup names
            typer.secho(f"📦 {backup_name}", fg=typer.colors.YELLOW)


@backup_app.command("restore")
def backup_restore(
    backup_file: Annotated[
        str,
        typer.Argument(
            help="Backup filename to restore from "
            "(use 'loom backup list' to see available backups)"
        ),
    ],
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
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
            "Use 'loom backup list' to see available backups.",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(code=1)

    # Parse backup filename to show what will be restored
    backup_name = backup_path.name
    parts = backup_name.split("_")
    if len(parts) >= 3:
        operation_idx = -2
        original_parts = parts[:operation_idx]
        original_file = "/".join(original_parts)

        if not confirm and not quiet:
            typer.secho(
                f"This will restore '{original_file}' from backup.",
                fg=typer.colors.CYAN,
            )
            typer.secho(
                f"Backup: {backup_file}",
                fg=typer.colors.WHITE,
            )

            home = get_home_dir()
            target_path = home / original_file
            if target_path.exists():
                typer.secho(
                    f"⚠️  This will overwrite the current file at {original_file}",
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
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
) -> None:
    """
    Clean old backup files.

    Removes backup files older than the specified number of days.
    Default is to remove backups older than 30 days.
    """
    from datetime import datetime, timedelta

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
                f"  📦 {backup_path.name} ({backup_time.strftime('%Y-%m-%d')})",
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
                typer.secho(f"✓ Removed {backup_path.name}", fg=typer.colors.GREEN)
        except Exception as e:
            failed_count += 1
            if not quiet:
                typer.secho(
                    f"✗ Failed to remove {backup_path.name}: {e}",
                    fg=typer.colors.RED,
                )

    if not quiet:
        if removed_count > 0:
            typer.secho(
                f"✓ Successfully removed {removed_count} backup(s)",
                fg=typer.colors.GREEN,
                bold=True,
            )
        if failed_count > 0:
            typer.secho(
                f"✗ Failed to remove {failed_count} backup(s)",
                fg=typer.colors.RED,
                bold=True,
            )


@backup_app.command("help")
def backup_help() -> None:
    """Show detailed help for backup management."""
    typer.secho("Loom Backup Management Help", fg=typer.colors.WHITE, bold=True)
    typer.secho("=" * 50, fg=typer.colors.WHITE)

    typer.secho("\nBackup System:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  Loom automatically creates backups when:")
    typer.echo("  • Restoring files that would overwrite existing files")
    typer.echo("  • Cloning a repository that would overwrite existing files")
    typer.echo("  • Running operations that modify existing dotfiles")
    typer.echo("  • You manually create backups with 'loom backup create'")

    typer.secho("\nBackup Location:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  All backups are stored in: ~/.loom/backups/")
    typer.echo("  Backup files use format: <path>_<operation>_<timestamp>")

    typer.secho("\nCommands:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  create    Create a manual backup of a file")
    typer.echo("  list      List all available backups")
    typer.echo("  restore   Restore a file from backup")
    typer.echo("  clean     Remove old backup files")
    typer.echo("  help      Show this help message")

    typer.secho("\nExamples:", fg=typer.colors.YELLOW, bold=True)
    typer.echo("  loom backup create .bashrc              " "# Backup .bashrc manually")
    typer.echo("  loom backup list                        " "# List all backups")
    typer.echo("  loom backup list --verbose              " "# List with details")
    typer.echo(
        "  loom backup restore .bashrc_manual_20250708_143022  " "# Restore backup"
    )
    typer.echo("  loom backup clean --older-than 7        " "# Remove old backups")
    typer.echo("  loom backup clean --older-than 30 --yes " "# Skip confirmation")

    typer.secho("\nSafety Features:", fg=typer.colors.CYAN, bold=True)
    typer.echo("  • Existing files are automatically backed up before restoration")
    typer.echo("  • Backups include timestamps for easy identification")
    typer.echo("  • Multiple backups of the same file are preserved")
    typer.echo("  • Confirmation prompts prevent accidental operations")


if __name__ == "__main__":
    app()
