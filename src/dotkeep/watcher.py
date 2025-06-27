import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_PATH = str(Path.home())  # Note: add functionality to specify another path

class DotkeepEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            if str(filename).startswith('.'):
                # Handle new dotfile creation here
                print(f"Dotfile created: {event.src_path}")

def main():
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