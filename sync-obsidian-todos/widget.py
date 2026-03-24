"""Sticky note widget that displays Obsidian todos on screen."""
import tkinter as tk
from tkinter import font as tkfont

from config import (
    WIDGET_BG,
    WIDGET_DONE_COLOR,
    WIDGET_FONT_FAMILY,
    WIDGET_FONT_SIZE,
    WIDGET_HEADER_BG,
    WIDGET_HEIGHT,
    WIDGET_MARGIN_RIGHT,
    WIDGET_MARGIN_TOP,
    WIDGET_OPACITY,
    WIDGET_TEXT_COLOR,
    WIDGET_TITLE,
    WIDGET_WIDTH,
)
from todo_parser import TodoItem


class StickyWidget:
    """A floating sticky-note style window showing todo items."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WIDGET_TITLE)
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes("-topmost", True)  # Always on top
        self.root.attributes("-alpha", WIDGET_OPACITY)

        # Position: top-right corner
        screen_w = self.root.winfo_screenwidth()
        x = screen_w - WIDGET_WIDTH - WIDGET_MARGIN_RIGHT
        y = WIDGET_MARGIN_TOP
        self.root.geometry(f"{WIDGET_WIDTH}x{WIDGET_HEIGHT}+{x}+{y}")

        self._build_ui()
        self._add_drag_support()

    def _build_ui(self):
        # Header bar
        self.header = tk.Frame(self.root, bg=WIDGET_HEADER_BG, height=36)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)

        self.title_label = tk.Label(
            self.header,
            text=f"  {WIDGET_TITLE}",
            bg=WIDGET_HEADER_BG,
            fg=WIDGET_TEXT_COLOR,
            font=(WIDGET_FONT_FAMILY, WIDGET_FONT_SIZE, "bold"),
            anchor="w",
        )
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.count_label = tk.Label(
            self.header,
            text="",
            bg=WIDGET_HEADER_BG,
            fg=WIDGET_TEXT_COLOR,
            font=(WIDGET_FONT_FAMILY, WIDGET_FONT_SIZE - 2),
        )
        self.count_label.pack(side=tk.RIGHT, padx=8)

        # Close button
        close_btn = tk.Label(
            self.header,
            text=" \u2715 ",
            bg=WIDGET_HEADER_BG,
            fg="#666",
            font=(WIDGET_FONT_FAMILY, WIDGET_FONT_SIZE),
            cursor="hand2",
        )
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self.root.destroy())

        # Scrollable content area
        container = tk.Frame(self.root, bg=WIDGET_BG)
        container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(container, bg=WIDGET_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=WIDGET_BG)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Status bar
        self.status = tk.Label(
            self.root,
            text="Watching for changes...",
            bg=WIDGET_HEADER_BG,
            fg="#666",
            font=(WIDGET_FONT_FAMILY, WIDGET_FONT_SIZE - 3),
            anchor="w",
            padx=8,
        )
        self.status.pack(fill=tk.X)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _add_drag_support(self):
        """Allow dragging the widget by the header."""
        self._drag_x = 0
        self._drag_y = 0

        def start_drag(event):
            self._drag_x = event.x
            self._drag_y = event.y

        def do_drag(event):
            x = self.root.winfo_x() + event.x - self._drag_x
            y = self.root.winfo_y() + event.y - self._drag_y
            self.root.geometry(f"+{x}+{y}")

        for w in (self.header, self.title_label):
            w.bind("<Button-1>", start_drag)
            w.bind("<B1-Motion>", do_drag)

    def update_todos(self, todos: list[TodoItem]):
        """Refresh the widget with a new list of todos."""
        # Clear existing items
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        incomplete = [t for t in todos if not t.done]
        done = [t for t in todos if t.done]

        self.count_label.config(text=f"{len(incomplete)} remaining  ")

        if not todos:
            empty_label = tk.Label(
                self.scroll_frame,
                text="\nNo todos found.\n\nAdd tasks to your Obsidian diary\nusing - [ ] syntax",
                bg=WIDGET_BG,
                fg="#999",
                font=(WIDGET_FONT_FAMILY, WIDGET_FONT_SIZE),
                justify=tk.CENTER,
            )
            empty_label.pack(pady=30, padx=20)
            return

        current_heading = None

        # Show incomplete todos first
        for todo in incomplete:
            if todo.heading and todo.heading != current_heading:
                current_heading = todo.heading
                heading_label = tk.Label(
                    self.scroll_frame,
                    text=todo.heading,
                    bg=WIDGET_BG,
                    fg=WIDGET_TEXT_COLOR,
                    font=(WIDGET_FONT_FAMILY, WIDGET_FONT_SIZE - 1, "bold"),
                    anchor="w",
                )
                heading_label.pack(fill=tk.X, padx=12, pady=(10, 2))

            self._add_todo_row(todo)

        # Separator if there are completed items
        if done and incomplete:
            sep = tk.Frame(self.scroll_frame, bg="#ddd", height=1)
            sep.pack(fill=tk.X, padx=12, pady=8)
            done_header = tk.Label(
                self.scroll_frame,
                text=f"Completed ({len(done)})",
                bg=WIDGET_BG,
                fg=WIDGET_DONE_COLOR,
                font=(WIDGET_FONT_FAMILY, WIDGET_FONT_SIZE - 2),
                anchor="w",
            )
            done_header.pack(fill=tk.X, padx=12)

        for todo in done:
            self._add_todo_row(todo)

    def _add_todo_row(self, todo: TodoItem):
        row = tk.Frame(self.scroll_frame, bg=WIDGET_BG)
        row.pack(fill=tk.X, padx=12, pady=2)

        checkbox = "\u2611" if todo.done else "\u2610"
        fg = WIDGET_DONE_COLOR if todo.done else WIDGET_TEXT_COLOR

        cb_label = tk.Label(
            row,
            text=checkbox,
            bg=WIDGET_BG,
            fg=fg,
            font=(WIDGET_FONT_FAMILY, WIDGET_FONT_SIZE + 2),
        )
        cb_label.pack(side=tk.LEFT)

        text = todo.text
        if todo.done:
            # Strikethrough effect not native in tk, use color to indicate
            pass

        text_label = tk.Label(
            row,
            text=text,
            bg=WIDGET_BG,
            fg=fg,
            font=(WIDGET_FONT_FAMILY, WIDGET_FONT_SIZE),
            anchor="w",
            wraplength=WIDGET_WIDTH - 60,
            justify=tk.LEFT,
        )
        text_label.pack(side=tk.LEFT, padx=4)

        # Source file tooltip
        source = tk.Label(
            row,
            text=todo.source_file.replace(".md", ""),
            bg=WIDGET_BG,
            fg="#bbb",
            font=(WIDGET_FONT_FAMILY, WIDGET_FONT_SIZE - 4),
        )
        source.pack(side=tk.RIGHT)

    def set_status(self, text: str):
        self.status.config(text=f"  {text}")

    def schedule(self, ms: int, callback):
        """Schedule a callback on the Tk event loop."""
        self.root.after(ms, callback)

    def run(self):
        self.root.mainloop()
