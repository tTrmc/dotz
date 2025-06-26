import typer
import shutil
import os
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
        return Repo(str(WORK_TREE))
    except NoSuchPathError:
        typer.secho(
            "Error: dotkeep repository not initialized. Run `dotkeep init` first.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)


def copy_file_or_directory(src_path, dest_path, repo, added_files):
    """
    Recursively copy files or directories and track them in git.
    Returns a list of relative paths that were added.
    """
    if src_path.is_file():
        # Handle single file
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest_path)
        
        # Stage the file
        tracked_path = dest_path.relative_to(WORK_TREE).as_posix()
        repo.index.add([tracked_path])
        added_files.append(src_path.relative_to(HOME))
        
    elif src_path.is_dir():
        # Handle directory recursively
        dest_path.mkdir(parents=True, exist_ok=True)
        
        # Process all items in the directory
        for item in src_path.iterdir():
            if item.name.startswith('.git'):
                # Skip .git directories to avoid conflicts
                continue
                
            item_dest = dest_path / item.name
            copy_file_or_directory(item, item_dest, repo, added_files)
    else:
        # Handle special files (symlinks, etc.) - skip them with a warning
        rel_path = src_path.relative_to(HOME)
        typer.secho(f"Warning: Skipping {rel_path} (not a regular file or directory)", 
                   fg=typer.colors.YELLOW)


def create_symlinks(src_path, dest_path):
    """
    Create symlinks for files or directories.
    For directories, create the directory structure and symlink individual files.
    """
    if dest_path.is_file():
        # Single file - create symlink
        if src_path.exists() or src_path.is_symlink():
            src_path.unlink()
        src_path.symlink_to(dest_path)
        
    elif dest_path.is_dir():
        # Directory - create directory structure and symlink files
        if src_path.exists() and not src_path.is_dir():
            # If src exists but is not a directory, remove it
            src_path.unlink()
        
        # Create the directory structure
        src_path.mkdir(parents=True, exist_ok=True)
        
        # Recursively create symlinks for all files
        for item in dest_path.rglob('*'):
            if item.is_file():
                rel_path = item.relative_to(dest_path)
                src_item = src_path / rel_path
                
                # Create parent directories if needed
                src_item.parent.mkdir(parents=True, exist_ok=True)
                
                # Remove existing file/symlink if present
                if src_item.exists() or src_item.is_symlink():
                    src_item.unlink()
                
                # Create symlink
                src_item.symlink_to(item)


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
    
    # List to track all added files for commit message
    added_files = []

    # Copy files/directories to the dotkeep repo
    copy_file_or_directory(src, dest, repo, added_files)

    # Create appropriate commit message
    if len(added_files) == 1:
        commit_msg = f"Add {added_files[0]}"
    else:
        commit_msg = f"Add {rel} ({len(added_files)} files)"

    # Commit the changes
    repo.index.commit(commit_msg)

    # Replace original with symlink(s)
    create_symlinks(src, dest)

    # Display success message
    if len(added_files) == 1:
        typer.secho(f"✓ Added {added_files[0]}", fg=typer.colors.GREEN)
    else:
        typer.secho(f"✓ Added {rel} ({len(added_files)} files)", fg=typer.colors.GREEN)
        # Optionally list the files
        if len(added_files) <= 10:  # Don't spam for large directories
            for file_path in added_files:
                typer.secho(f"  - {file_path}", fg=typer.colors.WHITE)
        else:
            typer.secho(f"  (and {len(added_files) - 10} more files)", fg=typer.colors.WHITE)

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

    # Remove symlink and file in repo
    src.unlink()
    dest.unlink()

    # Remove from git index using path relative to WORK_TREE
    tracked_path = dest.relative_to(WORK_TREE).as_posix()
    repo.index.remove([tracked_path])
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
        typer.Argument(help="Path to dotfile (relative to your home directory)")
    ]
):
    """
    Restore a dotfile from the dotkeep repository to your home directory.
    Overwrites any existing file or symlink at that location.
    """
    repo = ensure_repo()
    src = (HOME / path).expanduser()
    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel

    # Check if the file is tracked (exists in the repo)
    tracked_files = repo.git.ls_files().splitlines()
    tracked_path = dest.relative_to(WORK_TREE).as_posix()
    if tracked_path not in tracked_files:
        typer.secho(
            f"Error: {rel} is not tracked by dotkeep.",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit(code=1)

    # Check if the repo copy exists
    if not dest.exists():
        typer.secho(
            f"Error: {dest} does not exist in the dotkeep repository.",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit(code=1)

    # If there's already something at src, remove it
    if src.is_symlink() or src.exists():
        src.unlink()

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


if __name__ == "__main__":
    app()
