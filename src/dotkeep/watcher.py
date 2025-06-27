import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .core import add_dotfile, ensure_repo

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

class DotkeepEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)
        if str(filename).startswith("."):
            # Convert the file's path to something relative to HOME
            home_path = Path(str(event.src_path)).relative_to(Path.home())
            # Check if it's under a tracked directory
            if is_in_tracked_directory(home_path):
                # Automatically add the new dotfile
                add_dotfile(home_path, push=False, quiet=True)
                print(f"Auto-added dotfile: {event.src_path}")
            else:
                print(f"Dotfile not in a tracked directory: {event.src_path}")

def main():
    WATCH_PATH = str(Path.home())  # Set the path to watch
    observer = Observer()
    event_handler = DotkeepEventHandler()
    observer.schedule(event_handler, WATCH_PATH, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()