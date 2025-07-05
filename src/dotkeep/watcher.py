import json
import os
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .core import add_dotfile, ensure_repo, get_home_dir, load_config, matches_patterns


def get_watcher_paths(home_dir=None):
    """Get watcher-related paths based on home directory."""
    if home_dir is None:
        home_dir = get_home_dir()

    dotkeep_dir = home_dir / ".dotkeep"

    return {
        "home": home_dir,
        "dotkeep_dir": dotkeep_dir,
    }


# Global paths - can be overridden for testing
_paths = get_watcher_paths()
HOME = _paths["home"]
DOTKEEP_DIR = _paths["dotkeep_dir"]


def update_watcher_paths(home_dir=None):
    """Update global watcher paths. Useful for testing."""
    global HOME, DOTKEEP_DIR
    paths = get_watcher_paths(home_dir)
    HOME = paths["home"]
    DOTKEEP_DIR = paths["dotkeep_dir"]


def is_in_tracked_directory(relative_path: Path) -> bool:
    """
    Return True if 'relative_path' (inside HOME) is under a directory already tracked by dotkeep.
    """
    repo = ensure_repo()
    tracked_items = set(repo.git.ls_files().splitlines())
    # Walk up through all parents. If any parent is tracked (i.e., was added as a directory), return True.
    parts = list(relative_path.parts)
    for i in range(len(parts)):
        check_subpath = Path(*parts[: i + 1]).as_posix()
        if check_subpath in tracked_items:
            return True
    return False


def get_tracked_dirs():
    tracked_file = DOTKEEP_DIR / "tracked_dirs.json"
    if not tracked_file.exists():
        return []
    with open(tracked_file, "r") as f:
        return json.load(f)


class DotkeepEventHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.config = load_config()

    def should_track_file(self, filename):
        """Check if a file should be tracked based on current configuration."""
        include_patterns = self.config["file_patterns"]["include"]
        exclude_patterns = self.config["file_patterns"]["exclude"]
        case_sensitive = self.config["search_settings"]["case_sensitive"]

        return matches_patterns(
            filename, include_patterns, exclude_patterns, case_sensitive
        )

    def on_created(self, event):
        if event.is_directory:
            return
        # Ignore symlink creations (second event)
        if os.path.islink(event.src_path):
            return

        filename = os.path.basename(event.src_path)
        if self.should_track_file(filename):
            # Convert the file's path to something relative to HOME
            home_path = Path(str(event.src_path)).relative_to(Path.home())
            # Check if this file is already in a tracked directory structure
            if not is_in_tracked_directory(home_path):
                # Automatically add the new file
                add_dotfile(home_path, push=False, quiet=True)
                print(f"Auto-added config file: {event.src_path}")

    def on_modified(self, event):
        # Reload config when it changes to pick up new patterns
        if str(event.src_path).endswith("config.json") and ".dotkeep" in str(
            event.src_path
        ):
            self.config = load_config()
            print("Configuration reloaded")


def main():
    observer = Observer()
    event_handler = DotkeepEventHandler()
    tracked_dirs = get_tracked_dirs()
    if not tracked_dirs:
        print("No tracked directories. Add one with dotkeep add <dir>")
        return
    for d in tracked_dirs:
        observer.schedule(event_handler, d, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
