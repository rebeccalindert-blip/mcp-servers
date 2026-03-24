#!/usr/bin/env python3
"""Obsidian Todo Sync — Sticky widget that shows your diary todos on screen.

Watches your Obsidian diary folder for changes and displays a floating
sticky-note widget with your incomplete (and completed) todo items.

Usage:
    python main.py                  # Show all diary todos
    python main.py --today          # Show only today's todos
    python main.py --vault PATH     # Override vault path
    python main.py --folder NAME    # Override diary folder name
"""
import argparse
import sys
import threading
from datetime import datetime
from pathlib import Path

from config import DIARY_FOLDER, DIARY_PATH, VAULT_PATH
from todo_parser import TodoItem, collect_todos, toggle_todo
from watcher import DiaryWatcher
from widget import StickyWidget


class ObsidianTodoApp:
    def __init__(self, diary_path: Path, today_only: bool = False):
        self.diary_path = diary_path
        self.today_only = today_only
        self.widget = StickyWidget(on_toggle=self._on_toggle)
        self._debounce_timer = None
        self._lock = threading.Lock()
        self._ignore_next_change = False

    def refresh(self):
        """Reload todos from disk and update the widget."""
        todos = collect_todos(self.diary_path, today_only=self.today_only)
        now = datetime.now().strftime("%H:%M:%S")
        self.widget.update_todos(todos)
        self.widget.set_status(f"Last updated: {now}  •  Watching {self.diary_path.name}/")

    def _on_toggle(self, todo: TodoItem):
        """Called when a checkbox is clicked in the widget.

        Writes the change back to the markdown file, then refreshes.
        """
        self._ignore_next_change = True
        if toggle_todo(todo):
            self.refresh()

    def _on_file_change(self):
        """Called by the file watcher (from a background thread).

        Debounces rapid changes and schedules UI update on the main thread.
        """
        # Skip refresh if we just wrote the file ourselves via toggle
        if self._ignore_next_change:
            self._ignore_next_change = False
            return

        with self._lock:
            if self._debounce_timer is not None:
                self.widget.root.after_cancel(self._debounce_timer)
            self._debounce_timer = self.widget.schedule(500, self.refresh)

    def run(self):
        if not self.diary_path.exists():
            print(f"Error: Diary path not found: {self.diary_path}")
            print(f"Make sure your Obsidian vault is at: {self.diary_path.parent}")
            print(f"And the diary folder '{self.diary_path.name}' exists inside it.")
            sys.exit(1)

        # Initial load
        self.refresh()

        # Start watching for changes
        watcher = DiaryWatcher(self.diary_path, self._on_file_change)
        watcher.start()
        print(f"Watching: {self.diary_path}")
        print("Sticky widget is running. Close the window or Ctrl+C to quit.")

        try:
            self.widget.run()
        except KeyboardInterrupt:
            pass
        finally:
            watcher.stop()


def main():
    parser = argparse.ArgumentParser(
        description="Show Obsidian diary todos in a sticky note widget"
    )
    parser.add_argument(
        "--today", action="store_true",
        help="Only show todos from today's daily note"
    )
    parser.add_argument(
        "--vault", type=str, default=None,
        help=f"Path to Obsidian vault (default: {VAULT_PATH})"
    )
    parser.add_argument(
        "--folder", type=str, default=None,
        help=f"Diary folder name within vault (default: {DIARY_FOLDER})"
    )
    args = parser.parse_args()

    vault = Path(args.vault) if args.vault else VAULT_PATH
    folder = args.folder or DIARY_FOLDER
    diary_path = vault / folder

    app = ObsidianTodoApp(diary_path, today_only=args.today)
    app.run()


if __name__ == "__main__":
    main()
