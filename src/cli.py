import typer
import shutil
from typing_extensions import Annotated
from pathlib import Path
from git import Repo, NoSuchPathError, GitCommandError

app = typer.Typer(help="dotkeep – a Git-backed dot-files manager")

HOME = Path.home()
DOTKEEP_DIR = HOME / ".dotkeep"
WORK_TREE   = DOTKEEP_DIR / "repo"

def ensure_repo():
    try:
        return Repo(str(DOTKEEP_DIR))
    except NoSuchPathError:
        typer.secho("Error: dotkeep repository not initialized. Run `dotkeep init` first.",
                    fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

@app.command()
def init(remote: Annotated[str, typer.Option(help="Optional remote URL to add as origin (SSH or HTTPS).")] = ""):
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
def add(path: Annotated[Path, typer.Argument(help="Path to dotfile (relative to your home directory)")], push: Annotated[bool, typer.Option("--push", "-p", help="Push commit to origin")]):
    repo = ensure_repo()
    src = (HOME / path).expanduser()
    if not src.exists():
        typer.secho(f"Error: {src} not found.", fg=typer.colors.RED, err=True)
        raise typer.Exit()

    rel = src.relative_to(HOME)
    dest = WORK_TREE / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    repo.index.add([str(dest)])
    repo.index.commit(f"Add {rel}")
    src.unlink()
    src.symlink_to(dest)
    typer.secho(f"✓ Added {rel}", fg=typer.colors.GREEN)

    if push:
        try:
            origin = repo.remote("origin")
            branch = repo.active_branch.name
            origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
            typer.secho("✓ Pushed to origin", fg=typer.colors.GREEN)
        except GitCommandError as e:
            typer.secho(f"Error pushing to origin: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit()

if __name__ == "__main__":
    app()
