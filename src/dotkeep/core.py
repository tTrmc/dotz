import shutil
import os
from pathlib import Path
from git import Repo, GitCommandError
import typer
import json

HOME = Path.home()
DOTKEEP_DIR = HOME / ".dotkeep"
WORK_TREE = DOTKEEP_DIR / "repo"
TRACKED_DIRS_FILE = DOTKEEP_DIR / "tracked_dirs.json"

def ensure_repo():
    try:
        return Repo(str(WORK_TREE))
    except Exception:
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

def save_tracked_dir(dir_path: Path):
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
            
def remove_tracked_dir(dir_path: Path):
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

def init_repo(remote: str = "", quiet: bool = False):
    if DOTKEEP_DIR.exists():
        if not quiet:
            typer.secho("dotkeep already initialised at ~/.dotkeep", fg=typer.colors.YELLOW)
        return False

    if not quiet:
        typer.secho("Initialising dotkeep...", fg=typer.colors.WHITE)
    DOTKEEP_DIR.mkdir()
    WORK_TREE.mkdir()

    repo = Repo.init(str(WORK_TREE))
    repo.git.config("user.name", "dotkeep")
    repo.git.config("user.email", "dotkeep@example.com")
    repo.git.commit("--allow-empty", "-m", "Initial commit")
    if not quiet:
        typer.secho("✓ Created empty initial commit", fg=typer.colors.GREEN)

    if remote:
        repo.create_remote("origin", remote)
        if not quiet:
            typer.secho(
                "⚠️  If you are adding sensitive information, make sure your remote repository is private!",
                fg=typer.colors.RED,
                bold=True,
            )

    if not quiet:
        typer.secho("✓ Initialised dotkeep repository in ~/.dotkeep/repo", fg=typer.colors.GREEN)
    return True

def add_dotfile(path: Path, push: bool = False, quiet: bool = False, recursive: bool = True):
    """
    Add a file or directory to dotkeep, then symlink it in your home directory.
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
        if recursive:
            dotfiles = [item for item in src.rglob("*") if item.is_file() and item.name.startswith(".")]
        else:
            dotfiles = [item for item in src.iterdir() if item.is_file() and item.name.startswith(".")]
        if not dotfiles:
            if not quiet:
                typer.secho(f"No dotfiles found in {rel}.", fg=typer.colors.YELLOW)
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
            typer.secho(f"✓ Added {len(dotfiles)} dotfiles from {rel}", fg=typer.colors.GREEN)

    else:
        if not quiet:
            typer.secho(f"Error: {src} is not a regular file or directory.", fg=typer.colors.RED, err=True)
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
                            err=True
                        )
                return False
            if not quiet:
                typer.secho("✓ Pushed to origin", fg=typer.colors.GREEN)
        except GitCommandError as e:
            if not quiet:
                typer.secho(f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True)
            return False
    return True

def delete_dotfile(path: Path, push: bool = False, quiet: bool = False):
    repo = ensure_repo()
    src = (HOME / path).expanduser()

    if not src.is_symlink():
        if not quiet:
            typer.secho(
                f"Error: {src} is not a symlink managed by dotkeep.",
                fg=typer.colors.RED,
                err=True
            )
        return False

    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel

    if not dest.exists():
        if not quiet:
            typer.secho(
                f"Error: {dest} does not exist in the dotkeep repository.",
                fg=typer.colors.RED,
                err=True
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
                            err=True
                        )
                return False
            if not quiet:
                typer.secho("✓ Pushed to origin", fg=typer.colors.GREEN)
        except GitCommandError as e:
            if not quiet:
                typer.secho(f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True)
            return False
    return True

def restore_dotfile(path: Path, quiet: bool = False, push: bool = False):
    src = (HOME / path).expanduser()
    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel

    # Check if the file/directory is tracked (exists in the repo)
    if not dest.exists():
        if not quiet:
            typer.secho(
                f"Error: {rel} is not tracked by dotkeep.",
                fg=typer.colors.RED,
                err=True
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
                            err=True
                        )
                return False
            if not quiet:
                typer.secho("✓ Pushed to origin", fg=typer.colors.GREEN)
        except GitCommandError as e:
            if not quiet:
                typer.secho(f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True)
            return False
    return True

def pull_repo(quiet: bool = False):
    repo = ensure_repo()
    # Check if 'origin' remote exists
    if "origin" not in [r.name for r in repo.remotes]:
        if not quiet:
            typer.secho(
                "Error: No 'origin' remote found. Please set one with `dotkeep init --remote <URL>` or `git remote add origin <URL>`.",
                fg=typer.colors.RED,
                err=True
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
                "Run: git -C ~/.dotkeep/repo branch --set-upstream-to=origin/<branch> <branch>",
                fg=typer.colors.RED,
                err=True
            )
        elif "divergent branches" in msg.lower() or "need to specify how to reconcile divergent branches" in msg.lower():
            typer.secho(
                "Error: Local and remote branches have diverged.\n"
                "You need to reconcile them. Try one of the following:\n"
                "  git -C ~/.dotkeep/repo pull --rebase\n"
                "  git -C ~/.dotkeep/repo pull --no-rebase\n"
                "  git -C ~/.dotkeep/repo pull --ff-only",
                fg=typer.colors.RED,
                err=True
            )
        else:
            typer.secho(f"Error pulling from origin: {e}", fg=typer.colors.RED, err=True)
        return False
    
def push_repo(quiet: bool = False):
    repo = ensure_repo()

    # Make sure there is an 'origin' remote
    if "origin" not in [r.name for r in repo.remotes]:
        if not quiet:
            typer.secho(
                "Error: No 'origin' remote found. Please set one with `dotkeep init --remote <URL>` or `git remote add origin <URL>`.",
                fg=typer.colors.RED,
                err=True
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
                typer.secho(f"✓ Set upstream tracking branch to origin/{branch}", fg=typer.colors.GREEN)
        # Check for push errors
        if any(r.flags & r.ERROR for r in result):
            for r in result:
                if r.flags & r.ERROR and not quiet:
                    summary = r.summary.lower()
                    if "non-fast-forward" in summary or "rejected" in summary:
                        typer.secho(
                            "Error: Push rejected (non-fast-forward). You may need to pull first:\n"
                            "  git -C ~/.dotkeep/repo pull --rebase\n"
                            "Or resolve conflicts and try again.",
                            fg=typer.colors.RED,
                            err=True
                        )
                    else:
                        typer.secho(
                            f"Error pushing to origin: {r.summary}",
                            fg=typer.colors.RED,
                            err=True
                        )
            return False
        if not quiet:
            typer.secho("✓ Pushed local commits to origin", fg=typer.colors.GREEN)
        return True
    except GitCommandError as e:
        msg = str(e)
        if "no upstream branch" in msg.lower() or "no tracking information" in msg.lower():
            typer.secho(
                "Error: No upstream branch set for this branch.\n"
                "Run: git -C ~/.dotkeep/repo branch --set-upstream-to=origin/<branch> <branch>",
                fg=typer.colors.RED,
                err=True
            )
        else:
            typer.secho(f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True)
        return False
    
def get_repo_status():
    repo = ensure_repo()
    untracked = list(repo.untracked_files)
    modified = [item.a_path for item in repo.index.diff(None)]
    staged = [item.a_path for item in repo.index.diff("HEAD")]

    # Unpushed changes
    unpushed = []
    if "origin" in [r.name for r in repo.remotes]:
        branch = repo.active_branch.name
        remote_branch = f"origin/{branch}"
        try:
            unpushed = [diff_item.a_path for diff_item in repo.index.diff(remote_branch)]
        except Exception:
            pass

    # Dotfiles in $HOME not tracked by dotkeep
    home_dotfiles = [f for f in os.listdir(HOME) if f.startswith('.') and (HOME / f).is_file()]
    tracked_files = set(repo.git.ls_files().splitlines())
    untracked_home_dotfiles = [f for f in home_dotfiles if f not in tracked_files]

    return {
        "untracked": untracked,
        "modified": modified,
        "staged": staged,
        "unpushed": unpushed,
        "untracked_home_dotfiles": untracked_home_dotfiles,
    }
    
def list_tracked_files():
    repo = ensure_repo()
    return repo.git.ls_files().splitlines()