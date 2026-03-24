"""Parse Obsidian markdown files for todo items."""
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional


@dataclass
class TodoItem:
    text: str
    done: bool
    source_file: str
    line_number: int
    source_dir: Optional[str] = None
    heading: Optional[str] = None


def parse_todos_from_file(filepath: Path) -> list[TodoItem]:
    """Extract todo items (- [ ] and - [x]) from a markdown file."""
    todos = []
    current_heading = None

    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []

    for i, line in enumerate(lines, start=1):
        # Track headings for context
        heading_match = re.match(r"^#{1,6}\s+(.+)", line)
        if heading_match:
            current_heading = heading_match.group(1).strip()
            continue

        # Match todo items: - [ ] or - [x] or - [X]
        todo_match = re.match(r"^\s*-\s+\[([ xX])\]\s+(.+)", line)
        if todo_match:
            done = todo_match.group(1).lower() == "x"
            text = todo_match.group(2).strip()
            todos.append(TodoItem(
                text=text,
                done=done,
                source_file=filepath.name,
                line_number=i,
                source_dir=str(filepath.parent),
                heading=current_heading,
            ))

    return todos


def get_today_filename() -> str:
    """Return today's date in common Obsidian daily note formats."""
    return date.today().strftime("%Y-%m-%d")


def collect_todos(diary_path: Path, today_only: bool = False) -> list[TodoItem]:
    """Collect todos from diary markdown files.

    If today_only is True, only parse today's daily note.
    Otherwise, parse all .md files and sort by most recent first.
    """
    if not diary_path.exists():
        return []

    if today_only:
        today = get_today_filename()
        candidates = list(diary_path.glob(f"*{today}*.md"))
    else:
        candidates = sorted(
            diary_path.glob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    all_todos = []
    for filepath in candidates:
        all_todos.extend(parse_todos_from_file(filepath))

    return all_todos


def get_incomplete_todos(diary_path: Path, today_only: bool = False) -> list[TodoItem]:
    """Return only incomplete todos."""
    return [t for t in collect_todos(diary_path, today_only) if not t.done]


def toggle_todo(todo: TodoItem) -> bool:
    """Toggle a todo item's done state in its source markdown file.

    Reads the file, flips `- [ ]` to `- [x]` (or vice versa) on the
    exact line, and writes the file back. Returns True on success.
    """
    if not todo.source_dir:
        return False

    filepath = Path(todo.source_dir) / todo.source_file

    try:
        lines = filepath.read_text(encoding="utf-8").splitlines(keepends=True)
    except (OSError, UnicodeDecodeError):
        return False

    idx = todo.line_number - 1  # 0-based index
    if idx < 0 or idx >= len(lines):
        return False

    line = lines[idx]

    if todo.done:
        # Mark as incomplete: [x] or [X] → [ ]
        new_line = re.sub(r"\[([xX])\]", "[ ]", line, count=1)
    else:
        # Mark as done: [ ] → [x]
        new_line = re.sub(r"\[ \]", "[x]", line, count=1)

    if new_line == line:
        return False  # Nothing changed — line didn't match

    lines[idx] = new_line
    filepath.write_text("".join(lines), encoding="utf-8")
    return True
