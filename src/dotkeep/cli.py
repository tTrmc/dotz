import typer
from typing_extensions import Annotated
from pathlib import Path
from .core import add_dotfile, init_repo, delete_dotfile, restore_dotfile, pull_repo, push_repo, get_repo_status, list_tracked_files
from .watcher import main as watcher_main
import json
from git import Repo

app = typer.Typer(help="dotkeep - a Git-backed dot-files manager")

HOME = Path.home()
DOTKEEP_DIR = HOME / ".dotkeep"
WORK_TREE = DOTKEEP_DIR / "repo"

@app.command()
def init(
    remote: Annotated[
        str,
        typer.Option(help="Optional remote URL to add as origin (SSH or HTTPS).")
    ] = ""
):
    """
    Initialize a new dotkeep repository by placing the .git folder in ~/.dotkeep/repo.
    If ~/.dotkeep already exists with a .git folder at the top level, please remove or rename it first.
    """
    success = init_repo(remote=remote, quiet=False)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def add(
    path: Annotated[
        Path,
        typer.Argument(help="Path to dotfile or directory (relative to your home directory)")
    ],
    push: Annotated[
        bool,
        typer.Option("--push", "-p", help="Push commit to origin", is_flag=True)
    ] = False,
    recursive: Annotated[
        bool,
        typer.Option("--recursive/--no-recursive", help="Recursively add dotfiles in subdirectories", is_flag=True)
    ] = True,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
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
        bool,
        typer.Option("--push", "-p", help="Push commit to origin", is_flag=True)
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
    ] = False,
):
    """Remove a dotkeep-managed file or directory and delete the symlink in your home directory."""
    success = delete_dotfile(path, push=push, quiet=quiet)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def status():
    """Show the status of your dotkeep repo (untracked, modified, staged), and dotfiles in $HOME not tracked by dotkeep."""
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
        typer.secho("Dotfiles in $HOME not tracked by dotkeep:", fg=typer.colors.MAGENTA)
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
        typer.Argument(help="Path to dotfile or directory (relative to your home directory)")
    ],
    push: Annotated[
        bool,
        typer.Option("--push", "-p", help="Push commit to origin", is_flag=True)
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
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
        bool,
        typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
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
        bool,
        typer.Option("--quiet", "-q", help="Suppress output", is_flag=True)
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
    typer.secho("dotkeep version 0.2.0", fg=typer.colors.GREEN)
    
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
        typer.secho("❌ dotkeep repo not initialized.", fg=typer.colors.RED)
        typer.secho("Run: dotkeep init", fg=typer.colors.YELLOW)
        return

    # Check if .git exists
    git_dir = WORK_TREE / ".git"
    if not git_dir.exists():
        typer.secho("❌ No .git directory found in dotkeep repo.", fg=typer.colors.RED)
        typer.secho("Try re-initializing with: dotkeep init", fg=typer.colors.YELLOW)
        return

    # Try loading the repo
    try:
        repo = Repo(str(WORK_TREE))
    except InvalidGitRepositoryError:
        typer.secho("❌ Invalid git repository in dotkeep repo.", fg=typer.colors.RED)
        return

    # Check for remotes
    remotes = list(repo.remotes)
    if not remotes:
        typer.secho("⚠️  No git remote set.", fg=typer.colors.YELLOW)
        typer.secho("Set one with: git -C ~/.dotkeep/repo remote add origin <url>", fg=typer.colors.YELLOW)
    else:
        typer.secho(f"✓ Remote(s) found: {', '.join(r.name for r in remotes)}", fg=typer.colors.GREEN)

    # Check for tracking branch
    try:
        branch = repo.active_branch
        tracking = branch.tracking_branch()
        if tracking is None:
            typer.secho(f"⚠️  Branch '{branch.name}' is not tracking a remote branch.", fg=typer.colors.YELLOW)
            typer.secho(f"Set upstream with: git -C ~/.dotkeep/repo branch --set-upstream-to=origin/{branch.name} {branch.name}", fg=typer.colors.YELLOW)
        else:
            typer.secho(f"✓ Branch '{branch.name}' is tracking '{tracking}'", fg=typer.colors.GREEN)
    except Exception:
        typer.secho("⚠️  Could not determine active branch or tracking info.", fg=typer.colors.YELLOW)

    # Check for uncommitted changes
    if repo.is_dirty(untracked_files=True):
        typer.secho("⚠️  There are uncommitted changes in your dotkeep repo.", fg=typer.colors.YELLOW)
        typer.secho("Run: dotkeep status", fg=typer.colors.YELLOW)
    else:
        typer.secho("✓ No uncommitted changes.", fg=typer.colors.GREEN)

    # Check tracked directories
    tracked_dirs_file = DOTKEEP_DIR / "tracked_dirs.json"
    if not tracked_dirs_file.exists() or not json.loads(tracked_dirs_file.read_text() or "[]"):
        typer.secho("⚠️  No tracked directories found.", fg=typer.colors.YELLOW)
        typer.secho("Add one with: dotkeep add <directory>", fg=typer.colors.YELLOW)
    else:
        dirs = json.loads(tracked_dirs_file.read_text())
        typer.secho(f"✓ Tracked directories: {', '.join(dirs)}", fg=typer.colors.GREEN)

    typer.secho("\nDiagnosis complete.", fg=typer.colors.WHITE, bold=True)


if __name__ == "__main__":
    app()