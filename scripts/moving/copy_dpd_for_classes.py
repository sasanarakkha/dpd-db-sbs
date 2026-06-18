#!/usr/bin/env python3

"""Copy tipitaka_pali.db, dpd goldendict folder, and bash script to the for_classes server folder."""

import shutil
import sys
from pathlib import Path

from tools.configger import config_read
from tools.printer import printer as pr


def safe_copy(src: Path, dest: Path) -> None:
    """Copy a file or directory to dest, overwriting any existing dest, logging the outcome."""
    try:
        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)
        pr.green(f"{src.name} copied successfully")
    except OSError as e:
        pr.red(f"Failed to copy {src.name}: {e}")


def main() -> None:
    pr.tic()

    pr.yellow_title("copying tipitaka_pali.db and dpd_goldendict_src")

    # Project structure (same logic)
    project_dir: Path = Path(__file__).resolve().parent.parent.parent
    deva_dir: Path = project_dir.parent.parent  # HOME

    # ---------- Source paths ----------

    # tipitaka db source
    tpr_db_path = config_read("tpr", "db_path")

    # dpd goldendict source folder
    share_dir: Path = project_dir / "exporter" / "share"
    dpd_goldendict_src: Path = share_dir / "dpd"

    # copying script
    bash_script: Path = project_dir / "scripts" / "bash" / "copy_tpr_db.sh"

    # ---------- Destination ----------

    dest_dir: Path = (
        deva_dir
        / "filesrv1"
        / "share1"
        / "Sharing between users"
        / "For A. Deva"
        / "for_classes"
    )

    if not dest_dir.exists():
        pr.no(f"destination not found: {dest_dir}")
        sys.exit(1)

    tasks: list[tuple[Path | None, Path]] = [
        (Path(tpr_db_path) if tpr_db_path else None, dest_dir / "tipitaka_pali.db"),
        (dpd_goldendict_src, dest_dir / "dpd"),
        (bash_script, dest_dir / bash_script.name),
    ]

    for src, dest in tasks:
        if src is None or not src.exists():
            pr.red(f"Missing source: {src}")
            continue
        safe_copy(src, dest)

    pr.toc()


if __name__ == "__main__":
    main()
