#!/usr/bin/env python3

# unzip dpd from download folder to the goldendict dir.

from pathlib import Path
from datetime import date
from zipfile import ZipFile

today: date = date.today()

# Print completion message in yellow color
print("\033[1;33m from Downloads/ \033[0m")

# Paths determined from the current working directory (project root)
project_dir: Path = Path.cwd()
deva_dir: Path = project_dir.parent.parent

# Source directory for DPD downloads
# Assuming "DPDs" subfolder for consistency. Change if incorrect for this script.
downloads_dir: Path = deva_dir / "Downloads" / "DPDs" 

# Destination directories
goldendict_dir: Path = deva_dir / "Documents" / "GoldenDict"
sync_mdict_dir: Path = deva_dir / "Mdict"

# Source file paths
dpd_goldendict_src: Path = downloads_dir / "dpd-goldendict.zip"
dpd_mdict_src: Path = downloads_dir / "dpd-mdict.zip"


if dpd_goldendict_src.exists():
    with ZipFile(dpd_goldendict_src, 'r') as zipObj:
        zipObj.extractall(goldendict_dir)
    print("\033[1;32m dpd_goldendict.zip has been unpacked locally \033[0m")
else:
    print(f"\033[1;31m {dpd_goldendict_src} is missing. Cannot proceed with unpacking. \033[0m")


if dpd_mdict_src.exists():
    with ZipFile(dpd_mdict_src, 'r') as zipObj:
        zipObj.extractall(sync_mdict_dir)
    print("\033[1;32m dpd_mdict.zip has been unpacked to MDict folder, please Sync \033[0m")
else:
    print(f"\033[1;31m {dpd_mdict_src} is missing. Cannot proceed with unpacking. \033[0m")
