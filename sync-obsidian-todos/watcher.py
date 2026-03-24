"""File watcher that monitors the Obsidian diary folder for changes."""
import threading
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class DiaryChangeHandler(FileSystemEventHandler):
    """Triggers a callback when .md files change in the diary folder."""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            self.callback()

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            self.callback()

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            self.callback()


class DiaryWatcher:
    """Watches the diary directory and calls on_change when files update."""

    def __init__(self, diary_path: Path, on_change):
        self.diary_path = diary_path
        self.on_change = on_change
        self.observer = Observer()

    def start(self):
        handler = DiaryChangeHandler(self.on_change)
        self.observer.schedule(handler, str(self.diary_path), recursive=True)
        thread = threading.Thread(target=self.observer.start, daemon=True)
        thread.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
