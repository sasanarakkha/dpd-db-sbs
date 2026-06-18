#!/usr/bin/env python3

"""Restore the SBS Anki collection from the most recent backup."""

import shutil
from pathlib import Path

from tools.configger import config_read
from tools.printer import printer as pr


def revert_to_latest_backup() -> bool:
    """Restore collection from the most recent backup. Returns True on success."""
    db_path = config_read("anki", "db_path_sbs")
    backup_dir = config_read("anki", "backup_path_sbs")

    if not db_path or not backup_dir:
        pr.red("db_path_sbs or backup_path_sbs not found in config.ini")
        return False

    backup_path = Path(backup_dir)
    if not backup_path.exists():
        pr.red(f"Backup directory not found: {backup_dir}")
        return False

    backups = sorted(backup_path.glob("collection_*.anki2"), reverse=True)
    if not backups:
        pr.red(f"No backups found in {backup_dir}")
        return False

    latest = backups[0]
    pr.green(f"restoring from {latest.name}")
    try:
        shutil.copy2(str(latest), db_path)
        pr.yes("collection restored")
        return True
    except OSError as e:
        pr.no("error")
        pr.red(f"Restore failed: {e}")
        return False


def main() -> None:
    pr.tic()
    if not revert_to_latest_backup():
        raise SystemExit(1)
    pr.toc()


if __name__ == "__main__":
    main()
