#!/usr/bin/env python3
"""
Sync Plaud transcripts to Obsidian vault as markdown notes.

Fetches recordings from your Plaud account, downloads their transcripts
and summaries, and saves them as Obsidian-compatible markdown files
in your iCloud-synced vault.

Usage:
    python sync_plaud_to_obsidian.py          # Sync new transcripts
    python sync_plaud_to_obsidian.py --all    # Re-sync all transcripts
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PLAUD_TOKEN = os.getenv("PLAUD_TOKEN")
OBSIDIAN_VAULT_PATH = os.getenv(
    "OBSIDIAN_VAULT_PATH",
    "/Users/rebeccalindert/Documents/Second Brain/Transcripts",
)
SYNC_STATE_FILE = Path(__file__).parent / ".sync_state.json"


def get_client():
    """Initialize and return a PlaudClient."""
    if not PLAUD_TOKEN:
        print("Error: PLAUD_TOKEN not set.")
        print("1. Go to web.plaud.ai and sign in")
        print("2. Open DevTools → Network tab")
        print("3. Find any request to api.plaud.ai")
        print("4. Copy the Authorization header value (without 'Bearer ' prefix)")
        print("5. Set it in your .env file as PLAUD_TOKEN=<token>")
        sys.exit(1)

    from plaud import PlaudClient

    return PlaudClient(token=PLAUD_TOKEN)


def load_sync_state():
    """Load the set of already-synced recording IDs."""
    if SYNC_STATE_FILE.exists():
        data = json.loads(SYNC_STATE_FILE.read_text())
        return set(data.get("synced_ids", []))
    return set()


def save_sync_state(synced_ids):
    """Persist the set of synced recording IDs."""
    SYNC_STATE_FILE.write_text(
        json.dumps({"synced_ids": sorted(synced_ids)}, indent=2)
    )


def sanitize_filename(name):
    """Remove characters that are problematic in filenames."""
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:200]  # cap length


def format_timestamp(ms):
    """Convert milliseconds to HH:MM:SS format."""
    total_seconds = int(ms / 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def format_date(recording):
    """Extract a date string from the recording's created_at field."""
    created = getattr(recording, "created_at", None)
    if created:
        if isinstance(created, (int, float)):
            dt = datetime.fromtimestamp(created / 1000, tz=timezone.utc)
        elif isinstance(created, str):
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                dt = datetime.now(tz=timezone.utc)
        elif isinstance(created, datetime):
            dt = created
        else:
            dt = datetime.now(tz=timezone.utc)
    else:
        dt = datetime.now(tz=timezone.utc)
    return dt.strftime("%Y-%m-%d"), dt.strftime("%Y-%m-%d %H:%M")


def build_markdown(recording, transcript, summary):
    """Build an Obsidian-compatible markdown note from Plaud data."""
    date_short, date_long = format_date(recording)
    title = getattr(recording, "filename", "Untitled Recording") or "Untitled Recording"
    title = title.replace(".wav", "").replace(".mp3", "").strip()
    duration = getattr(recording, "duration_display", "")

    # --- Frontmatter ---
    lines = [
        "---",
        f"title: {title}",
        f"date: {date_short}",
        "source: plaud",
        f"duration: {duration}",
        f"plaud_id: {recording.id}",
        "tags:",
        "  - transcript",
        "  - plaud",
        "---",
        "",
    ]

    # --- Summary ---
    lines.append("## Summary")
    lines.append("")
    if summary:
        content = getattr(summary, "content", None) or str(summary)
        lines.append(content.strip())
    else:
        lines.append("*No summary available.*")
    lines.append("")

    # --- Transcript ---
    lines.append("## Transcript")
    lines.append("")
    if transcript and hasattr(transcript, "segments") and transcript.segments:
        current_speaker = None
        for seg in transcript.segments:
            speaker = getattr(seg, "speaker", "Unknown")
            text = getattr(seg, "text", "").strip()
            timestamp = format_timestamp(getattr(seg, "start_time_ms", 0))

            if speaker != current_speaker:
                current_speaker = speaker
                lines.append(f"**{speaker}** `{timestamp}`")
                lines.append(text)
                lines.append("")
            else:
                lines.append(f"`{timestamp}` {text}")
                lines.append("")
    else:
        lines.append("*No transcript available.*")
    lines.append("")

    # --- Metadata footer ---
    lines.append("---")
    lines.append(f"*Synced from Plaud on {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")

    return "\n".join(lines)


def sync_recording(client, recording, vault_path):
    """Fetch transcript + summary for a recording and save as markdown."""
    rec_id = recording.id
    title = getattr(recording, "filename", "Untitled") or "Untitled"
    title = title.replace(".wav", "").replace(".mp3", "").strip()
    date_short, _ = format_date(recording)

    # Fetch transcript and summary
    transcript = None
    summary = None

    try:
        transcript = client.transcriptions.get(rec_id)
    except Exception as e:
        print(f"  Warning: Could not fetch transcript for '{title}': {e}")

    try:
        summary = client.transcriptions.get_summary(rec_id)
    except Exception as e:
        print(f"  Warning: Could not fetch summary for '{title}': {e}")

    if not transcript and not summary:
        print(f"  Skipping '{title}' — no transcript or summary available")
        return False

    # Build markdown
    md_content = build_markdown(recording, transcript, summary)

    # Save to vault
    safe_title = sanitize_filename(title)
    filename = f"{date_short} {safe_title}.md"
    filepath = vault_path / filename

    filepath.write_text(md_content, encoding="utf-8")
    print(f"  Saved: {filename}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Sync Plaud transcripts to Obsidian")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Re-sync all transcripts (ignore sync state)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max number of recordings to fetch (default: 50)",
    )
    args = parser.parse_args()

    # Ensure output directory exists
    vault_path = Path(OBSIDIAN_VAULT_PATH)
    vault_path.mkdir(parents=True, exist_ok=True)

    print(f"Obsidian vault path: {vault_path}")
    print()

    # Initialize client
    client = get_client()

    # Load sync state
    synced_ids = set() if args.all else load_sync_state()

    # Fetch recordings
    print("Fetching recordings from Plaud...")
    recordings = client.recordings.list(limit=args.limit)
    print(f"Found {len(recordings)} recording(s)")
    print()

    new_count = 0
    skip_count = 0

    for rec in recordings:
        if rec.id in synced_ids:
            skip_count += 1
            continue

        title = getattr(rec, "filename", rec.id) or rec.id
        print(f"Processing: {title}")

        if sync_recording(client, rec, vault_path):
            synced_ids.add(rec.id)
            new_count += 1

    # Save sync state
    save_sync_state(synced_ids)

    print()
    print(f"Done! Synced {new_count} new transcript(s), skipped {skip_count} already synced.")


if __name__ == "__main__":
    main()
