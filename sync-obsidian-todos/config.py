"""Configuration for the Obsidian Todo Sync sticky widget."""
import os
from pathlib import Path

# Path to your Obsidian vault
VAULT_PATH = Path(os.environ.get(
    "OBSIDIAN_VAULT_PATH",
    os.path.expanduser("~/Documents/Second Brain")
))

# Subfolder within the vault where diary/daily notes live
DIARY_FOLDER = os.environ.get("OBSIDIAN_DIARY_FOLDER", "DIARY")

# Full path to diary directory
DIARY_PATH = VAULT_PATH / DIARY_FOLDER

# Widget appearance
WIDGET_WIDTH = 380
WIDGET_HEIGHT = 500
WIDGET_BG = "#FFF9C4"        # Sticky-note yellow
WIDGET_HEADER_BG = "#FFD600"  # Darker yellow header
WIDGET_TEXT_COLOR = "#333333"
WIDGET_DONE_COLOR = "#999999"
WIDGET_FONT_FAMILY = "Helvetica Neue"
WIDGET_FONT_SIZE = 13
WIDGET_TITLE = "Obsidian Todos"
WIDGET_OPACITY = 0.95

# Position on screen (pixels from top-right corner)
WIDGET_MARGIN_RIGHT = 30
WIDGET_MARGIN_TOP = 30
