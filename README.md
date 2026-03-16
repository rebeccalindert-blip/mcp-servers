# Plaud → Obsidian Transcript Sync

Automatically syncs Plaud recording transcripts from Google Drive to your Obsidian vault as properly formatted markdown notes.

## How it works

```
Plaud app → Zapier → Google Drive → this script → Obsidian vault
```

1. Plaud records and transcribes your audio
2. Zapier exports the transcript as a markdown file to Google Drive
3. Google Drive for Desktop syncs it locally
4. This script picks up new files, adds YAML frontmatter, and copies them to your Obsidian vault

## Output format

Each note gets Obsidian-compatible YAML frontmatter:

```markdown
---
title: "Meeting with Client"
date: 2026-03-16
source: plaud
tags:
  - transcript
  - plaud
---

## Summary
AI-generated summary of the recording...

## Transcript
**Speaker 1** Hello, thanks for joining...

**Speaker 2** Thanks for having me...
```

## Setup

### Prerequisites

- Python 3.10+
- [Google Drive for Desktop](https://www.google.com/drive/download/) installed and syncing
- Zapier automation exporting Plaud transcripts as markdown to Google Drive

### Paths (pre-configured)

| What | Path |
|------|------|
| Google Drive source | `/Users/rebeccalindert/Library/CloudStorage/GoogleDrive-bec@lindertco.com.au/My Drive/PLAUD Recordings` |
| Obsidian vault dest | `/Users/rebeccalindert/Documents/Second Brain/Transcripts` |

To change these, edit the `SOURCE_DIR` and `OBSIDIAN_DIR` variables at the top of `sync_plaud_to_obsidian.py`.

## Usage

### One-time sync

```bash
python sync_plaud_to_obsidian.py
```

### Re-sync everything

```bash
python sync_plaud_to_obsidian.py --all
```

### Watch mode (continuous)

```bash
python sync_plaud_to_obsidian.py --watch
python sync_plaud_to_obsidian.py --watch --interval 30  # check every 30s
```

### Auto-run every hour (launchd)

```bash
cp com.plaud.obsidian-sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.plaud.obsidian-sync.plist
```

To stop:

```bash
launchctl unload ~/Library/LaunchAgents/com.plaud.obsidian-sync.plist
```

Check logs:

```bash
tail -f /tmp/plaud-obsidian-sync.log
```

## No dependencies

Uses only the Python standard library — no `pip install` needed.
