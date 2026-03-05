#!/usr/bin/env python3
"""
Initialize a new Upstream Sync Rehearsal track.
Creates the folder, copies templates, generates metadata, and registers the track in tracks.md.
"""

import shutil
import datetime
import json
from pathlib import Path


def main():
    # Define paths relative to the project root
    # Assuming this script is located at <root>/conductor/init_rehearsal.py
    script_location = Path(__file__).resolve()
    project_root = script_location.parent.parent

    conductor_dir = project_root / "conductor"
    templates_dir = conductor_dir / "templates" / "upstream_sync_rehearsal"
    tracks_dir = conductor_dir / "tracks"
    tracks_file = conductor_dir / "tracks.md"

    # Generate dated track info
    today = datetime.date.today()
    date_str_short = today.strftime("%Y%m%d")
    date_str_human = today.strftime("%Y-%m-%d")

    track_folder_name = f"upstream_sync_rehearsal_{date_str_short}"
    new_track_dir = tracks_dir / track_folder_name

    # Check if exists
    if new_track_dir.exists():
        print(f"⚠️  Track folder already exists: {new_track_dir}")
        print("   Skipping creation.")
    else:
        # Create and Copy
        print(f"📂 Creating track directory: {new_track_dir}")
        new_track_dir.mkdir(parents=True)

        print("📄 Copying templates...")
        shutil.copy(templates_dir / "plan.md", new_track_dir / "plan.md")
        shutil.copy(templates_dir / "spec.md", new_track_dir / "spec.md")

        print("📄 Generating metadata.json...")
        metadata = {
            "track_id": track_folder_name,
            "type": "chore",
            "status": "new",
            "created_at": datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "updated_at": datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "description": f"Upstream Sync Rehearsal ({date_str_human})",
        }
        with open(new_track_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        print("📄 Generating index.md...")
        index_content = f"""# Track {track_folder_name} Context

- [Specification](./spec.md)
- [Implementation Plan](./plan.md)
- [Metadata](./metadata.json)
"""
        with open(new_track_dir / "index.md", "w", encoding="utf-8") as f:
            f.write(index_content)

    # Prepare Registry Entry
    entry_header = f"## [ ] Track: Upstream Sync Rehearsal ({date_str_human})"
    entry_link = f"*Link: [./conductor/tracks/{track_folder_name}/](./conductor/tracks/{track_folder_name}/)*"
    full_entry = f"{entry_header}\n{entry_link}"

    # Check if entry exists in tracks.md
    with open(tracks_file, "r", encoding="utf-8") as f:
        content = f.read()

    if entry_link in content:
        print("⚠️  Entry already exists in tracks.md.")
    else:
        print("📝 Registering track in conductor/tracks.md...")
        # Append to the end of the file with a separator
        with open(tracks_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n\n{full_entry}\n")

    print("\n✅ Setup Complete!")
    print(
        f"🚀 You can now run:\n   /conductor:implement Upstream Sync Rehearsal ({date_str_human})"
    )


if __name__ == "__main__":
    main()
