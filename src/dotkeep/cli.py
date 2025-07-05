import json
from pathlib import Path

import typer
from git import Repo
from typing_extensions import Annotated

from .core import (
    add_dotfile,
    add_file_pattern,
    delete_dotfile,
    get_config_value,
    get_home_dir,
    get_repo_status,
    init_repo,
    list_tracked_files,
    load_config,
    pull_repo,
    push_repo,
    remove_file_pattern,
    reset_config,
    restore_dotfile,
    set_config_value,
)
from .watcher import main as watcher_main

app = typer.Typer(help="dotkeep - a Git-backed dot-files manager")


def get_cli_paths():
    """Get CLI-related paths based on current home directory."""
    home = get_home_dir()
    dotkeep_dir = home / ".dotkeep"
    work_tree = dotkeep_dir / "repo"
    return home, dotkeep_dir, work_tree


HOME, DOTKEEP_DIR, WORK_TREE = get_cli_paths()


def refresh_cli_paths():
    """Refresh CLI paths when HOME environment changes."""
    global HOME, DOTKEEP_DIR, WORK_TREE
    HOME, DOTKEEP_DIR, WORK_TREE = get_cli_paths()


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
):
    if not non_interactive and not remote:
        typer.secho("dotkeep Interactive Setup", fg=typer.colors.CYAN, bold=True)
        typer.echo(
            "Welcome! Let's configure your dotkeep repository for managing dotfiles.\n"
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
        typer.secho("Initializing dotkeep repository...", fg=typer.colors.CYAN)
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
                f"\nAdd these {len(found_files)} files to dotkeep?", default=True
            ):
                added_count = 0
                for dotfile in found_files:
                    try:
                        success = add_dotfile(
                            dotfile, push=False, quiet=True, recursive=False
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
            typer.echo("You can add dotfiles later with: dotkeep add <filename>")

    # Show completion message
    typer.echo()
    typer.secho("Repository initialization complete!", fg=typer.colors.GREEN, bold=True)

    if remote:
        typer.secho(
            "Next steps:",
            fg=typer.colors.CYAN,
        )
        typer.echo("  • Add more dotfiles: dotkeep add <filename>")
        typer.echo("  • Push to remote: dotkeep push")
        typer.echo("  • Check status: dotkeep status")
    else:
        typer.secho(
            "Next steps:",
            fg=typer.colors.CYAN,
        )
        typer.echo("  • Add dotfiles: dotkeep add <filename>")
        typer.echo(
            "  • Add remote later: git -C ~/.dotkeep/repo remote add origin <url>"
        )
        typer.echo("  • Check status: dotkeep status")


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
):
    """Add a file or directory to dotkeep, then symlink it in your home directory."""
    success = add_dotfile(path, push=push, quiet=quiet, recursive=recursive)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def delete(
    path: Annotated[Path, ...],
    push: Annotated[
        bool, typer.Option("--push", "-p", help="Push commit to origin", is_flag=True)
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
):
    """
    Remove a dotkeep-managed file or directory and delete the symlink in your
    home directory.
    """
    success = delete_dotfile(path, push=push, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def status():
    """
    Show the status of your dotkeep repo (untracked, modified, staged), and
    dotfiles in $HOME not tracked by dotkeep.
    """
    status = get_repo_status()

    typer.secho("Status of dotkeep repository:", fg=typer.colors.WHITE)

    if not status["untracked"] and not status["modified"] and not status["staged"]:
        typer.secho("✓ No changes", fg=typer.colors.GREEN)
    else:
        if status["untracked"]:
            typer.secho("Untracked files:", fg=typer.colors.YELLOW)
            for file in status["untracked"]:
                typer.secho(f"  - {file}", fg=typer.colors.YELLOW)
        if status["modified"]:
            typer.secho("Modified files:", fg=typer.colors.YELLOW)
            for file in status["modified"]:
                typer.secho(f"  - {file}", fg=typer.colors.YELLOW)
        if status["staged"]:
            typer.secho("Staged files:", fg=typer.colors.YELLOW)
            for file in status["staged"]:
                typer.secho(f"  - {file}", fg=typer.colors.YELLOW)

    if status["unpushed"]:
        typer.secho("Unpushed changes:", fg=typer.colors.YELLOW)
        for file in status["unpushed"]:
            typer.secho(f"  - {file}", fg=typer.colors.YELLOW)

    if status["untracked_home_dotfiles"]:
        typer.secho(
            "Dotfiles in $HOME not tracked by dotkeep:", fg=typer.colors.MAGENTA
        )
        for f in status["untracked_home_dotfiles"]:
            typer.secho(f"  - {f}", fg=typer.colors.MAGENTA)


@app.command()
def list_files():
    """
    List all files currently tracked by dotkeep.
    """
    tracked_files = list_tracked_files()
    if not tracked_files:
        typer.secho("No files tracked by dotkeep.", fg=typer.colors.YELLOW)
        return

    typer.secho("Files tracked by dotkeep:", fg=typer.colors.WHITE)
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
):
    """
    Restore a dotfile or directory from the dotkeep repository to your home directory.
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
):
    """
    Pull the latest changes from the 'origin' remote into the local dotkeep repository.
    """
    success = pull_repo(quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def push(
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
):
    """
    Push all local commits to the 'origin' remote, if it exists.
    """
    success = push_repo(quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def watch():
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
def version():
    """Show dotkeep version."""
    typer.secho("dotkeep version 0.3.0", fg=typer.colors.GREEN)


@app.command()
def completion():
    """
    Show instructions for enabling shell completion.
    """
    typer.echo("Run: dotkeep --install-completion")


@app.command()
def diagnose():
    """
    Diagnose common dotkeep and git issues and print helpful advice.
    """
    from git import InvalidGitRepositoryError

    typer.secho("Running dotkeep diagnostics...\n", fg=typer.colors.WHITE, bold=True)

    # Check repo existence
    if not DOTKEEP_DIR.exists() or not WORK_TREE.exists():
        typer.secho("ERROR: dotkeep repo not initialized.", fg=typer.colors.RED)
        typer.secho("Run: dotkeep init", fg=typer.colors.YELLOW)
        return

    # Check if .git exists
    git_dir = WORK_TREE / ".git"
    if not git_dir.exists():
        typer.secho(
            "ERROR: No .git directory found in dotkeep repo.", fg=typer.colors.RED
        )
        typer.secho("Try re-initializing with: dotkeep init", fg=typer.colors.YELLOW)
        return

    # Try loading the repo
    try:
        repo = Repo(str(WORK_TREE))
    except InvalidGitRepositoryError:
        typer.secho(
            "ERROR: Invalid git repository in dotkeep repo.", fg=typer.colors.RED
        )
        return

    # Check for remotes
    remotes = list(repo.remotes)
    if not remotes:
        typer.secho("WARNING: No git remote set.", fg=typer.colors.YELLOW)
        typer.secho(
            "Set one with: git -C ~/.dotkeep/repo remote add origin <url>",
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
                f"Set upstream with: git -C ~/.dotkeep/repo branch "
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
            "WARNING: There are uncommitted changes in your dotkeep repo.",
            fg=typer.colors.YELLOW,
        )
        typer.secho("Run: dotkeep status", fg=typer.colors.YELLOW)
    else:
        typer.secho("✓ No uncommitted changes.", fg=typer.colors.GREEN)

    # Check tracked directories
    tracked_dirs_file = DOTKEEP_DIR / "tracked_dirs.json"
    if not tracked_dirs_file.exists() or not json.loads(
        tracked_dirs_file.read_text() or "[]"
    ):
        typer.secho("WARNING: No tracked directories found.", fg=typer.colors.YELLOW)
        typer.secho("Add one with: dotkeep add <directory>", fg=typer.colors.YELLOW)
    else:
        dirs = json.loads(tracked_dirs_file.read_text())
        typer.secho(f"✓ Tracked directories: {', '.join(dirs)}", fg=typer.colors.GREEN)

    typer.secho("\nDiagnosis complete.", fg=typer.colors.WHITE, bold=True)


# Configuration management commands
config_app = typer.Typer(help="Manage dotkeep configuration")
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
):
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
):
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
):
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
):
    """Remove a file pattern from include or exclude lists."""
    success = remove_file_pattern(pattern, pattern_type)
    if not success:
        raise typer.Exit(code=1)


@config_app.command("reset")
def config_reset(
    confirm: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")
    ] = False,
):
    """Reset configuration to defaults."""
    if not confirm:
        typer.confirm(
            "Are you sure you want to reset configuration to defaults?", abort=True
        )

    reset_config()


@config_app.command("list-patterns")
def config_list_patterns():
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
def config_help():
    """Show detailed help for configuration management."""
    typer.secho("Dotkeep Configuration Help", fg=typer.colors.WHITE, bold=True)
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
    typer.echo("  dotkeep config add-pattern '*.py'        # Track Python files")
    typer.echo("  dotkeep config add-pattern '.env*'       # Track environment files")
    typer.echo("  dotkeep config add-pattern '*.log' -t exclude  # Ignore log files")
    typer.echo(
        "  dotkeep config set search_settings.recursive false  "
        "# Disable recursive search"
    )
    typer.echo("  dotkeep config show file_patterns.include  # Show include patterns")

    typer.secho("\nDefault patterns include:", fg=typer.colors.CYAN)
    typer.echo("  Dotfiles (.*), config files (*.conf, *.config, *.cfg, *.ini)")
    typer.echo("  YAML/JSON (*.yaml, *.yml, *.json), TOML files (*.toml)")

    typer.secho("\nDefault exclusions:", fg=typer.colors.CYAN)
    typer.echo("  System files (.DS_Store, .cache), VCS (.git, .svn)")
    typer.echo("  Temporary files (*.log, *.tmp)")

    typer.secho("\nConfiguration is stored in:", fg=typer.colors.MAGENTA)
    typer.echo("  ~/.dotkeep/config.json")


if __name__ == "__main__":
    app()
