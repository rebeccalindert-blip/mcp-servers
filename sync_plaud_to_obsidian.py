#!/usr/bin/env python3
"""
Sync Plaud transcripts from Google Drive to Obsidian vault.

Watches a Google Drive folder (synced locally via Drive for Desktop) for
markdown files exported by Plaud via Zapier. Adds YAML frontmatter and
copies them to your Obsidian vault's Transcripts folder.

Usage:
    python sync_plaud_to_obsidian.py              # One-time sync
    python sync_plaud_to_obsidian.py --watch      # Watch for new files continuously
    python sync_plaud_to_obsidian.py --all        # Re-sync all files
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SOURCE_DIR = Path(
    "/Users/rebeccalindert/Library/CloudStorage/"
    "GoogleDrive-bec@lindertco.com.au/My Drive/PLAUD Recordings"
)
OBSIDIAN_DIR = Path(
    "/Users/rebeccalindert/Documents/Second Brain/Transcripts"
)
SYNC_STATE_FILE = Path(__file__).parent / ".sync_state.json"


def load_sync_state():
    """Load dict of already-synced files: {filename: content_hash}."""
    if SYNC_STATE_FILE.exists():
        return json.loads(SYNC_STATE_FILE.read_text())
    return {}


def save_sync_state(state):
    """Persist sync state."""
    SYNC_STATE_FILE.write_text(json.dumps(state, indent=2))


def content_hash(text):
    """Return a short hash of file content for change detection."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def has_frontmatter(text):
    """Check if the markdown already has YAML frontmatter."""
    return text.strip().startswith("---")


def extract_title(filepath, text):
    """Extract a title from the file content or filename."""
    # Try first heading
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("# ").strip()

    # Fall back to filename without extension
    return filepath.stem


def extract_date(filepath):
    """Try to extract a date from the filename, fall back to file mtime."""
    # Common patterns: "2026-03-16 Meeting", "20260316_Meeting"
    match = re.match(r"(\d{4}[-_]?\d{2}[-_]?\d{2})", filepath.stem)
    if match:
        date_str = match.group(1).replace("_", "-")
        # Ensure dashes
        if "-" not in date_str:
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str

    # Fall back to file modification time
    mtime = filepath.stat().st_mtime
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")


def extract_summary_and_transcript(text):
    """Split content into summary and transcript sections if identifiable."""
    # Remove existing heading if present (we'll restructure)
    lines = text.strip().splitlines()

    # Skip a leading title heading
    if lines and lines[0].strip().startswith("# "):
        lines = lines[1:]

    content = "\n".join(lines).strip()

    # Check if it already has ## Summary / ## Transcript sections
    if "## Summary" in content and "## Transcript" in content:
        return content

    # Check if there's a clear summary block (often at the top, before transcript)
    # Plaud exports typically have summary then transcript with speaker labels
    # Look for speaker patterns like "Speaker 1:", "**Speaker 1**", "[Speaker 1]"
    speaker_pattern = re.compile(
        r"^(\*\*[^*]+\*\*|Speaker \d+|\[[^\]]+\])\s*[:\-]?\s*", re.MULTILINE
    )
    speaker_matches = list(speaker_pattern.finditer(content))

    if speaker_matches:
        # Everything before first speaker label is likely the summary
        first_speaker_pos = speaker_matches[0].start()
        summary_text = content[:first_speaker_pos].strip()
        transcript_text = content[first_speaker_pos:].strip()

        parts = []
        parts.append("## Summary")
        parts.append("")
        parts.append(summary_text if summary_text else "*No summary available.*")
        parts.append("")
        parts.append("## Transcript")
        parts.append("")
        parts.append(transcript_text)
        return "\n".join(parts)

    # No clear structure — put everything under Transcript
    parts = []
    parts.append("## Summary")
    parts.append("")
    parts.append("*No summary available.*")
    parts.append("")
    parts.append("## Transcript")
    parts.append("")
    parts.append(content)
    return "\n".join(parts)


def process_file(filepath):
    """Read a Plaud markdown file and return Obsidian-formatted content."""
    text = filepath.read_text(encoding="utf-8")

    # If it already has frontmatter, just return as-is
    if has_frontmatter(text):
        return text

    title = extract_title(filepath, text)
    date = extract_date(filepath)
    body = extract_summary_and_transcript(text)

    frontmatter = f"""---
title: "{title}"
date: {date}
source: plaud
tags:
  - transcript
  - plaud
---"""

    return f"{frontmatter}\n\n{body}\n"


def sanitize_filename(name):
    """Remove characters that are problematic in filenames."""
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:200]


def sync_once(source_dir, obsidian_dir, state, force_all=False):
    """Scan source dir and sync new/changed files to Obsidian."""
    if not source_dir.exists():
        print(f"Error: Source folder not found: {source_dir}")
        print("Make sure Google Drive for Desktop is running and the folder exists.")
        sys.exit(1)

    obsidian_dir.mkdir(parents=True, exist_ok=True)

    txt_files = sorted(source_dir.glob("*.txt"))
    if not txt_files:
        print("No text files found in source folder.")
        return 0

    new_count = 0
    for filepath in txt_files:
        file_key = filepath.name
        file_hash = content_hash(filepath.read_text(encoding="utf-8"))

        # Skip if already synced and unchanged
        if not force_all and state.get(file_key) == file_hash:
            continue

        print(f"  Processing: {filepath.name}")

        try:
            formatted = process_file(filepath)
        except Exception as e:
            print(f"  Error processing {filepath.name}: {e}")
            continue

        # Save to Obsidian vault as .md
        dest = obsidian_dir / (filepath.stem + ".md")
        dest.write_text(formatted, encoding="utf-8")

        state[file_key] = file_hash
        new_count += 1
        print(f"  → Saved: {dest.name}")

    return new_count


def main():
    parser = argparse.ArgumentParser(
        description="Sync Plaud transcripts from Google Drive to Obsidian"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch for new files continuously (checks every 60s)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Watch interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Re-sync all files (ignore sync state)",
    )
    args = parser.parse_args()

    print(f"Source:      {SOURCE_DIR}")
    print(f"Destination: {OBSIDIAN_DIR}")
    print()

    state = {} if args.all else load_sync_state()

    if args.watch:
        print(f"Watching for new files every {args.interval}s (Ctrl+C to stop)...")
        print()
        try:
            while True:
                new_count = sync_once(SOURCE_DIR, OBSIDIAN_DIR, state, force_all=False)
                if new_count > 0:
                    save_sync_state(state)
                    print(f"  Synced {new_count} file(s)")
                    print()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped watching.")
            save_sync_state(state)
    else:
        new_count = sync_once(SOURCE_DIR, OBSIDIAN_DIR, state, force_all=args.all)
        save_sync_state(state)
        total = len(state)
        print()
        print(f"Done! Synced {new_count} new/changed file(s). {total} total tracked.")


if __name__ == "__main__":
    main()
