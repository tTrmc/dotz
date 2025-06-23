import typer
import shutil
from typing_extensions import Annotated
from pathlib import Path
from git import Repo, NoSuchPathError, GitCommandError

app = typer.Typer(help="dotkeep - a Git-backed dot-files manager")

HOME = Path.home()
DOTKEEP_DIR = HOME / ".dotkeep"
WORK_TREE = DOTKEEP_DIR / "repo"


def ensure_repo():
    """Return a Repo object or show an error if not initialized."""
    try:
        return Repo(str(DOTKEEP_DIR))
    except NoSuchPathError:
        typer.secho(
            "Error: dotkeep repository not initialized. Run `dotkeep init` first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)


@app.command()
def init(
    remote: Annotated[
        str,
        typer.Option(help="Optional remote URL to add as origin (SSH or HTTPS).")
    ] = ""
):
    """Initialize a new dotkeep repository."""
    if DOTKEEP_DIR.exists():
        typer.secho("dotkeep already initialised at ~/.dotkeep", fg=typer.colors.YELLOW)
        raise typer.Exit()

    typer.secho("Initialising...", fg=typer.colors.WHITE)
    DOTKEEP_DIR.mkdir()
    repo = Repo.init(str(DOTKEEP_DIR))
    WORK_TREE.mkdir()
    if remote:
        repo.create_remote("origin", remote)
    typer.secho("✓ Initialised dotkeep repository", fg=typer.colors.GREEN)


@app.command()
def add(
    path: Annotated[
        Path,
        typer.Argument(help="Path to dotfile (relative to your home directory)")
    ],
    push: Annotated[
        bool,
        typer.Option("--push", "-p", help="Push commit to origin", is_flag=True)
    ] = False
):
    """Add a file to dotkeep, then symlink it in your home directory."""
    repo = ensure_repo()
    src = (HOME / path).expanduser()

    if not src.exists():
        typer.secho(f"Error: {src} not found.", fg=typer.colors.RED, err=True)
        raise typer.Exit()

    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Copy the file to the dotkeep repo
    shutil.copy2(src, dest)

    # Stage and commit
    repo.index.add([str(dest)])
    repo.index.commit(f"Add {rel}")

    # Replace original with symlink
    src.unlink()
    src.symlink_to(dest)

    typer.secho(f"✓ Added {rel}", fg=typer.colors.GREEN)

    if push:
        try:
            origin = repo.remote("origin")
            branch = repo.active_branch.name
            result = origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
            # Check push result for errors
            if any(r.flags & r.ERROR for r in result):
                for r in result:
                    if r.flags & r.ERROR:
                        typer.secho(
                            f"Error pushing to origin: {r.summary}",
                            fg=typer.colors.RED,
                            err=True
                        )
                raise typer.Exit()
            typer.secho("✓ Pushed to origin", fg=typer.colors.GREEN)
        except GitCommandError as e:
            typer.secho(f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit()


@app.command()
def delete(
    path: Annotated[
        Path,
        typer.Argument(help="Path to dotfile (relative to your home directory)")
    ],
    push: Annotated[
        bool,
        typer.Option("--push", "-p", help="Push commit to origin", is_flag=True)
    ] = False
):
    """Remove a dotkeep-managed file and delete the symlink in your home directory."""
    repo = ensure_repo()
    src = (HOME / path).expanduser()

    # Ensure it is a symlink
    if not src.is_symlink():
        typer.secho(
            f"Error: {src} is not a symlink managed by dotkeep.",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit()

    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel

    if not dest.exists():
        typer.secho(
            f"Error: {dest} does not exist in the dotkeep repository.",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit()

    # Remove symlink and file in repo
    src.unlink()
    dest.unlink()

    # Remove from git index and commit
    repo.index.remove([str(dest)])
    repo.index.commit(f"Remove {rel}")

    typer.secho(f"✓ Removed {rel}", fg=typer.colors.GREEN)

    if push:
        try:
            origin = repo.remote("origin")
            branch = repo.active_branch.name
            result = origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
            # Check push result for errors
            if any(r.flags & r.ERROR for r in result):
                for r in result:
                    if r.flags & r.ERROR:
                        typer.secho(
                            f"Error pushing to origin: {r.summary}",
                            fg=typer.colors.RED,
                            err=True
                        )
                raise typer.Exit()
            typer.secho("✓ Pushed to origin", fg=typer.colors.GREEN)
        except GitCommandError as e:
            typer.secho(f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit()


@app.command()
def status():
    """Show the status of your dotkeep repo (untracked, modified, staged)."""
    repo = ensure_repo()
    untracked = list(repo.untracked_files)
    modified = [item.a_path for item in repo.index.diff(None)]
    staged = [item.a_path for item in repo.index.diff("HEAD")]

    typer.secho("Status of dotkeep repository:", fg=typer.colors.WHITE)

    if not untracked and not modified and not staged:
        typer.secho("✓ No changes", fg=typer.colors.GREEN)
    else:
        if untracked:
            typer.secho("Untracked files:", fg=typer.colors.YELLOW)
            for file in untracked:
                typer.secho(f"  - {file}", fg=typer.colors.YELLOW)
        if modified:
            typer.secho("Modified files:", fg=typer.colors.YELLOW)
            for file in modified:
                typer.secho(f"  - {file}", fg=typer.colors.YELLOW)
        if staged:
            typer.secho("Staged files:", fg=typer.colors.YELLOW)
            for file in staged:
                typer.secho(f"  - {file}", fg=typer.colors.YELLOW)

    # Show files that have not been pushed to the remote, if available
    if "origin" in [r.name for r in repo.remotes]:
        branch = repo.active_branch.name
        remote_branch = f"origin/{branch}"
        # Attempt to diff HEAD with origin/branch
        try:
            unpushed_diff = repo.index.diff(remote_branch)
            if unpushed_diff:
                typer.secho("Unpushed changes:", fg=typer.colors.YELLOW)
                for diff_item in unpushed_diff:
                    typer.secho(f"  - {diff_item.a_path}", fg=typer.colors.YELLOW)
        except:
            # If remote branch does not exist or cannot be reached, do nothing
            pass

@app.command()
def list_files():
    """
    List all files currently tracked by dotkeep.
    """
    repo = ensure_repo()
    tracked_files = repo.git.ls_files().splitlines()
    if not tracked_files:
        typer.secho("No files tracked by dotkeep.", fg=typer.colors.YELLOW)
        return

    typer.secho("Files tracked by dotkeep:", fg=typer.colors.WHITE)
    for f in tracked_files:
        typer.secho(f"  - {f}", fg=typer.colors.YELLOW)


if __name__ == "__main__":
    app()