import typer
from typing_extensions import Annotated
from pathlib import Path
from git import Repo, NoSuchPathError

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
    repo = Repo.init(str(DOTKEEP_DIR), bare=True)
    WORK_TREE.mkdir()
    if remote:
        repo.create_remote("origin", remote)
    typer.secho("✓ Initialised dotkeep repository", fg=typer.colors.GREEN)

@app.command()
def add():
    test = ensure_repo()

if __name__ == "__main__":
    app()
