#!/usr/bin/env python3

# copy rudpd from download folder to the fileserver. And copy mdx and kindl versions as well. 

import sys
from pathlib import Path
from datetime import date
import shutil
from tools.printer import printer as pr

pr.tic()

today: date = date.today()

# Print completion message in green color
print("\033[1;33m from Share/ \033[0m")

# Paths determined from the current working directory (project root)
project_dir: Path = Path.cwd()
deva_dir: Path = project_dir.parent.parent

# Source directory for ru-dpd files
share_dir: Path = project_dir / "exporter" / "share"

# Destination directories on the fileserver
software_dir: Path = deva_dir / "filesrv1" / "share1" / "Sharing between users" / "1 For Everyone" / "Software"
gd_dir: Path = software_dir / "Golden Dictionary" / "Optional"
md_dir: Path = software_dir / "MDict" / "ru-dpd"
kd_dir: Path = software_dir / "Ebook Readers Dictionary"

# Source file paths
dpd_goldendict_src: Path = share_dir / "ru-dpd"
dpd_mdict_src_mdx: Path = share_dir / "ru-dpd-mdict.mdx"
dpd_mdict_src_mdd: Path = share_dir / "ru-dpd-mdict.mdd"

for dest in [gd_dir, md_dir]:
    if not dest.exists():
        pr.no(f"destination not found: {dest}")
        sys.exit(1)

# dpd_goldendict copy folder to the specified directory
if dpd_goldendict_src.exists():
   # Copy the dpd folder to the Golden Dictionary directory
   # Remove existing destination folder if it exists to ensure a clean copy
   destination_path = gd_dir / dpd_goldendict_src.name
   if destination_path.exists():
      shutil.rmtree(destination_path)
   shutil.copytree(dpd_goldendict_src, destination_path)
   # Print completion message in green color
   print("\033[1;32m ru-dpd folder has been copied to the server folder \033[0m")
else:
   print(f"\033[1;31m {dpd_goldendict_src} is missing. Cannot proceed with copying. \033[0m")

# dpd_mdict copy files to the specified directory
if dpd_mdict_src_mdx.exists() and dpd_mdict_src_mdd.exists():
   # Copy the specific MDict files
   shutil.copy2(dpd_mdict_src_mdx, md_dir)
   shutil.copy2(dpd_mdict_src_mdd, md_dir)
   # Print completion message in green color
   print("\033[1;32m dpd-mdict.mdx and dpd-mdict.mdd have been copied to the server folder \033[0m")
else:
   if not dpd_mdict_src_mdx.exists():
      print(f"\033[1;31m {dpd_mdict_src_mdx} is missing. Cannot proceed with copying. \033[0m")
   if not dpd_mdict_src_mdd.exists():
      print(f"\033[1;31m {dpd_mdict_src_mdd} is missing. Cannot proceed with copying. \033[0m")

pr.toc()