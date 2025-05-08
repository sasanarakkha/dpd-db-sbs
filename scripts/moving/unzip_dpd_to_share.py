#!/usr/bin/env python3

# unzip dpd-deconstructor and dpd-grammar and variants from download folder to the share dir
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

# Destination directory within the project
share_dir: Path = project_dir / "exporter" / "share"

# Source file paths
dpd_goldendict_src: Path = downloads_dir / "dpd-goldendict.zip"
dpd_mdict_src: Path = downloads_dir / "dpd-mdict.zip"


if dpd_goldendict_src.exists():
    with ZipFile(dpd_goldendict_src, 'r') as zipObj:
        members: list[str] = zipObj.namelist()
        members_to_extract: list[str] = [
            m for m in members 
            if m.startswith('dpd-deconstructor/') or \
                m.startswith('dpd-grammar/') or \
                m.startswith('dpd-variants/')
        ]
        zipObj.extractall(share_dir, members=members_to_extract)
    print("\033[1;32m gdict deconstructor and grammar and variants has been unpacked to share folder \033[0m")
else:
    print(f"\033[1;31m {dpd_goldendict_src} is missing. Cannot proceed with unpacking. \033[0m")


if dpd_mdict_src.exists():
    with ZipFile(dpd_mdict_src, 'r') as zipObj:
        members: list[str] = zipObj.namelist()
        files_to_extract: list[str] = [
            'dpd-grammar-mdict.mdx',
            'dpd-grammar-mdict.mdd',
            'dpd-deconstructor-mdict.mdd',
            'dpd-deconstructor-mdict.mdx',
            'dpd-variants-mdict.mdx',
            'dpd-variants-mdict.mdd',
        ]
        members_to_extract: list[str] = [m for m in members if m in files_to_extract]
        zipObj.extractall(share_dir, members=members_to_extract)
    print("\033[1;32m mdict deconstructor and grammar and variants has been unpacked to share \033[0m")
else:
    print(f"\033[1;31m {dpd_mdict_src} is missing. Cannot proceed with unpacking. \033[0m")
