import typer
import shutil
import os
from typing_extensions import Annotated
from pathlib import Path
from git import Repo, NoSuchPathError, GitCommandError
from .watcher import main as watcher_main

app = typer.Typer(help="dotkeep - a Git-backed dot-files manager")

HOME = Path.home()
DOTKEEP_DIR = HOME / ".dotkeep"
WORK_TREE = DOTKEEP_DIR / "repo"


def ensure_repo():
    """Return a Repo object or show an error if not initialized."""
    try:
        return Repo(str(WORK_TREE))
    except NoSuchPathError:
        typer.secho(
            "Error: dotkeep repository not initialized. Run `dotkeep init` first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)


def count_files_in_directory(path):
    """Count all files recursively in a directory."""
    if path.is_file():
        return 1
    elif path.is_dir():
        count = 0
        for item in path.rglob('*'):
            if item.is_file():
                count += 1
        return count
    return 0


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
    if DOTKEEP_DIR.exists():
        typer.secho("dotkeep already initialised at ~/.dotkeep", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    typer.secho("Initialising dotkeep...", fg=typer.colors.WHITE)
    DOTKEEP_DIR.mkdir()
    WORK_TREE.mkdir()

    # Initialize Git directly in ~/.dotkeep/repo
    repo = Repo.init(str(WORK_TREE))

    # Set user.name and user.email for initial commit
    repo.git.config("user.name", "dotkeep")
    repo.git.config("user.email", "dotkeep@example.com")

    # Create empty initial commit
    repo.git.commit("--allow-empty", "-m", "Initial commit")
    typer.secho("✓ Created empty initial commit", fg=typer.colors.GREEN)

    # Optionally set a remote
    if remote:
        repo.create_remote("origin", remote)

    typer.secho("✓ Initialised dotkeep repository in ~/.dotkeep/repo", fg=typer.colors.GREEN)


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
    repo = ensure_repo()
    src = (HOME / path).expanduser()

    if not src.exists():
        typer.secho(f"Error: {src} not found.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel

    # Ensure parent directories exist in the repo
    dest.parent.mkdir(parents=True, exist_ok=True)

    if src.is_file():
        # Handle single file (existing behavior)
        shutil.copy2(src, dest)
        
        # Stage the file
        tracked_path = dest.relative_to(WORK_TREE).as_posix()
        repo.index.add([tracked_path])
        repo.index.commit(f"Add {rel}")

        # Replace original with symlink
        src.unlink()
        src.symlink_to(dest)
        typer.secho(f"✓ Added {rel}", fg=typer.colors.GREEN)

    elif src.is_dir():
        # Handle directory - copy entire directory and create directory symlink
        if dest.exists():
            shutil.rmtree(dest)
        
        # Copy the entire directory tree
        shutil.copytree(src, dest)
        
        # Count files for commit message
        file_count = count_files_in_directory(dest)
        
        # Stage all files in the directory
        tracked_path = dest.relative_to(WORK_TREE).as_posix()
        repo.index.add([tracked_path])
        
        # Create commit message
        if file_count == 1:
            commit_msg = f"Add {rel} (1 file)"
        else:
            commit_msg = f"Add {rel} ({file_count} files)"
        
        repo.index.commit(commit_msg)

        # Replace original directory with symlink
        shutil.rmtree(src)
        src.symlink_to(dest)
        
        # Display success message
        if file_count == 0:
            typer.secho(f"✓ Added {rel} (empty directory)", fg=typer.colors.GREEN)
        elif file_count == 1:
            typer.secho(f"✓ Added {rel} (1 file)", fg=typer.colors.GREEN)
        else:
            typer.secho(f"✓ Added {rel} ({file_count} files)", fg=typer.colors.GREEN)

    else:
        # Handle special files (symlinks, etc.)
        typer.secho(f"Error: {src} is not a regular file or directory.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # Optionally push
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
        typer.Argument(help="Path to dotfile or directory (relative to your home directory)")
    ],
    push: Annotated[
        bool,
        typer.Option("--push", "-p", help="Push commit to origin", is_flag=True)
    ] = False
):
    """Remove a dotkeep-managed file or directory and delete the symlink in your home directory."""
    repo = ensure_repo()
    src = (HOME / path).expanduser()

    # Ensure it is a symlink
    if not src.is_symlink():
        typer.secho(
            f"Error: {src} is not a symlink managed by dotkeep.",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit(code=1)

    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel

    if not dest.exists():
        typer.secho(
            f"Error: {dest} does not exist in the dotkeep repository.",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit(code=1)

    # Remove symlink and file/directory in repo
    src.unlink()
    
    if dest.is_file():
        dest.unlink()
        # Remove single file from git index
        tracked_path = dest.relative_to(WORK_TREE).as_posix()
        repo.index.remove([tracked_path])
    elif dest.is_dir():
        shutil.rmtree(dest)
        # Remove directory from git index
        tracked_path = dest.relative_to(WORK_TREE).as_posix()
        repo.index.remove([tracked_path], r=True)  # Recursive removal for directories

    repo.index.commit(f"Remove {rel}")
    typer.secho(f"✓ Removed {rel}", fg=typer.colors.GREEN)

    # Optionally push
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
    """Show the status of your dotkeep repo (untracked, modified, staged), and dotfiles in $HOME not tracked by dotkeep."""
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

    # Get all files in $HOME that start with '.' and are files (not directories)
    home_dotfiles = [f for f in os.listdir(HOME) if f.startswith('.') and (HOME / f).is_file()]
    # Get tracked files (relative to WORK_TREE)
    tracked_files = set(repo.git.ls_files().splitlines())
    # Only consider dotfiles in $HOME that are not tracked by dotkeep
    untracked_home_dotfiles = [f for f in home_dotfiles if f not in tracked_files]
    if untracked_home_dotfiles:
        typer.secho("Dotfiles in $HOME not tracked by dotkeep:", fg=typer.colors.MAGENTA)
        for f in untracked_home_dotfiles:
            typer.secho(f"  - {f}", fg=typer.colors.MAGENTA)


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
    repo = ensure_repo()
    src = (HOME / path).expanduser()
    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel

    # Check if the file/directory is tracked (exists in the repo)
    if not dest.exists():
        typer.secho(
            f"Error: {rel} is not tracked by dotkeep.",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit(code=1)

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
    typer.secho(f"✓ Restored {rel}", fg=typer.colors.GREEN)


@app.command()
def pull():
    """
    Pull the latest changes from the 'origin' remote into the local dotkeep repository.
    """
    repo = ensure_repo()
    # Check if 'origin' remote exists
    if "origin" not in [r.name for r in repo.remotes]:
        typer.secho(
            "Error: No 'origin' remote found. Please set one with `dotkeep init --remote <URL>` or `git remote add origin <URL>`.",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit()

    origin = repo.remote("origin")
    try:
        origin.pull()
        typer.secho("✓ Pulled latest changes from origin", fg=typer.colors.GREEN)
    except GitCommandError as e:
        typer.secho(f"Error pulling from origin: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit()
    
@app.command()
def push():
    """
    Push all local commits to the 'origin' remote, if it exists.
    """
    repo = ensure_repo()

    # Make sure there is an 'origin' remote
    if "origin" not in [r.name for r in repo.remotes]:
        typer.secho(
            "Error: No 'origin' remote found. Please set one with `dotkeep init --remote <URL>` or `git remote add origin <URL>`.",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit()

    # Attempt to push the current branch
    origin = repo.remote("origin")
    branch = repo.active_branch.name
    try:
        result = origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
        # Check if any push results had errors
        if any(r.flags & r.ERROR for r in result):
            for r in result:
                if r.flags & r.ERROR:
                    typer.secho(
                        f"Error pushing to origin: {r.summary}",
                        fg=typer.colors.RED,
                        err=True
                    )
            raise typer.Exit()
        typer.secho("✓ Pushed local commits to origin", fg=typer.colors.GREEN)
    except GitCommandError as e:
        typer.secho(f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit()
    
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
