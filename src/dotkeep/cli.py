import typer
from typing_extensions import Annotated
from pathlib import Path
from .core import add_dotfile, init_repo, delete_dotfile, restore_dotfile, pull_repo, push_repo, get_repo_status, list_tracked_files
from .watcher import main as watcher_main

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
    ] = False
):
    """Add a file or directory to dotkeep, then symlink it in your home directory."""
    success = add_dotfile(path, push=push, quiet=False)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def delete(
    path: Annotated[Path, ...],
    push: Annotated[bool, ...] = False
):
    """Remove a dotkeep-managed file or directory and delete the symlink in your home directory."""
    success = delete_dotfile(path, push=push, quiet=False)
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
    ]
):
    """
    Restore a dotfile or directory from the dotkeep repository to your home directory.
    Overwrites any existing file or symlink at that location.
    """
    success = restore_dotfile(path, quiet=False)
    if not success:
        raise typer.Exit(code=1)


@app.command()
def pull():
    """
    Pull the latest changes from the 'origin' remote into the local dotkeep repository.
    """
    success = pull_repo(quiet=False)
    if not success:
        raise typer.Exit(code=1)
    
@app.command()
def push():
    """
    Push all local commits to the 'origin' remote, if it exists.
    """
    success = push_repo(quiet=False)
    if not success:
        raise typer.Exit(code=1)
    
@app.command()
def watch():
    """
    Start watching for changes in your home directory and automatically add new dotfiles.
    """
    typer.secho("Starting watcher...", fg=typer.colors.WHITE)
    try:
        watcher_main()
    except KeyboardInterrupt:
        typer.secho("Watcher stopped.", fg=typer.colors.YELLOW)
        raise typer.Exit()


if __name__ == "__main__":
    app()