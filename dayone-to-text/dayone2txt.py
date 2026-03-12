#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import re

def main():
    if len(sys.argv) != 2:
        print("Usage: python json_to_txt.py <output_dir_name>")
        sys.exit(1)

    out_dir_name = sys.argv[1]
    out_dir = Path.cwd() / out_dir_name
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = Path.cwd() / "Journal.json"
    if not json_path.exists():
        print(f"Journal.json not found in {Path.cwd()}")
        sys.exit(1)

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    if not entries:
        print("No entries found in Journal.json")
        sys.exit(0)

    # Group entries by date (YYYY-MM-DD)
    entries_by_date = {}
    for entry in entries:
        text = entry.get("text", "")
        creation = entry.get("creationDate")
        if not creation:
            continue

        # Parse date
        try:
            dt = datetime.fromisoformat(creation.replace("Z", "+00:00"))
            date_key = dt.strftime("%Y-%m-%d")
        except:
            date_key = creation[:10]

        # Remove Day One moment links
        clean_text = re.sub(r'!\[\]\(dayone-moment://[a-f0-9\-]+\)', '', text).rstrip()

        # Get location if exists
        location = ""
        if "location" in entry and entry["location"]:
            loc = entry["location"]
            place_name = loc.get("placeName", "")
            if place_name:
                location = place_name

        entries_by_date.setdefault(date_key, []).append({
            "text": clean_text,
            "location": location
        })

    # Write files
    files_written = 0
    for date_key, day_entries in sorted(entries_by_date.items()):
        file_name = f"{date_key}.txt"
        out_path = out_dir / file_name

        with out_path.open("w", encoding="utf-8") as out_f:
            # First line: date
            out_f.write(date_key + "\n")
            
            # Each entry separated by blank line
            for i, entry_data in enumerate(day_entries, 1):
                # Entry content
                out_f.write(entry_data["text"])
                
                # Location at end of content (if any)
                if entry_data["location"]:
                    out_f.write(f"\n\n--- Location: {entry_data['location']} ---")
                
                # Blank line separator (except for last entry)
                if i < len(day_entries):
                    out_f.write("\n\n")
            
            files_written += 1

    print(f"✅ Done. Wrote {files_written} files to {out_dir}")
    print(f"📅 {len(entries_by_date)} unique dates processed")

if __name__ == "__main__":
    main()
