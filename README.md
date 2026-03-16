# Plaud → Obsidian Transcript Sync

Automatically syncs your [Plaud](https://plaud.ai) recording transcripts and AI summaries to your Obsidian vault as markdown notes.

## What it does

- Fetches all your recordings from Plaud's API
- Downloads transcripts (with speaker labels and timestamps) and AI summaries
- Saves each recording as a clean Obsidian-compatible markdown note with YAML frontmatter
- Tracks what's already been synced so it only processes new recordings
- Can run on a schedule via macOS launchd (every hour)

## Output format

Each note is saved as `YYYY-MM-DD Title.md`:

```markdown
---
title: Meeting with Client
date: 2026-03-16
source: plaud
duration: 45:23
plaud_id: abc123
tags:
  - transcript
  - plaud
---

## Summary
AI-generated summary of the recording...

## Transcript
**Speaker 1** `00:00`
Hello, thanks for joining...

**Speaker 2** `00:15`
Thanks for having me...
```

## Setup

### 1. Install dependencies

```bash
cd /path/to/mcp-servers
pip install -r requirements.txt
```

### 2. Get your Plaud API token

1. Go to [web.plaud.ai](https://web.plaud.ai) and sign in
2. Open browser DevTools (Cmd+Option+I) → **Network** tab
3. Click on any request going to `api.plaud.ai`
4. Copy the **Authorization** header value (without the `Bearer ` prefix)

### 3. Configure

Copy the example env file and add your token:

```bash
cp .env.example .env
```

Edit `.env`:

```
PLAUD_TOKEN=your_token_here
OBSIDIAN_VAULT_PATH=/Users/rebeccalindert/Documents/Second Brain/Transcripts
```

### 4. Run manually

```bash
python sync_plaud_to_obsidian.py
```

Options:
- `--all` — Re-sync all transcripts (ignores sync state)
- `--limit 100` — Fetch more recordings (default: 50)

### 5. Run automatically (every hour)

Install the launchd service:

```bash
# Edit the plist if your paths differ, then:
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

## Token refresh

Plaud tokens may expire. If you see authentication errors, repeat step 2 to get a fresh token and update your `.env` file.
