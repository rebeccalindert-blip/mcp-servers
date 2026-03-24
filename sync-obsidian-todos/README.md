# Obsidian Todo Sync — Sticky Widget

A floating sticky-note widget for macOS that displays your Obsidian diary todos on screen. It watches your vault for changes and updates in real time.

## Setup

```bash
cd sync-obsidian-todos
pip3 install -r requirements.txt
```

## Usage

```bash
# Show all diary todos
python3 main.py

# Show only today's todos
python3 main.py --today

# Custom vault path
python3 main.py --vault "/path/to/vault" --folder "DIARY"
```

Or double-click `launch-todos.command` on macOS.

## Configuration

Edit `config.py` to change:
- Vault path and diary folder
- Widget size, colors, position, and opacity

You can also use environment variables:
- `OBSIDIAN_VAULT_PATH` — path to your vault
- `OBSIDIAN_DIARY_FOLDER` — name of the diary folder

## How it works

1. Parses `- [ ]` and `- [x]` checkbox items from `.md` files in your diary folder
2. Displays them in a draggable, always-on-top sticky note window
3. Watches for file changes and updates the widget instantly
