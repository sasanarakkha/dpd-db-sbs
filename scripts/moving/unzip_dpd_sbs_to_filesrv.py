#!/usr/bin/env python3

# unzip dpd-sbs golden dict, mdict from Download to the fileserver.   

from pathlib import Path
from datetime import date
from zipfile import ZipFile

today: date = date.today()

# Print completion message in green color
print("\033[1;33m from Downloads/ \033[0m")

project_dir: Path = Path.cwd()  # e.g., /Users/deva/Documents/dpd-db
deva_dir: Path = project_dir.parent.parent  # e.g., /Users/deva
downloads_dir: Path = deva_dir / "Downloads" / "DPDs" # e.g., /Users/deva/Downloads/DPDs

software_dir: Path = deva_dir / "filesrv1" / "share1" / "Sharing between users" / "1 For Everyone" / "Software"
gd_dir: Path = software_dir / "Golden Dictionary" / "Default"

md_dir: Path = software_dir / "MDict" / "dpd"

dpd_goldendict_src: Path = downloads_dir / "dpd+sbs-goldendict.zip"
dpd_mdict_src: Path = downloads_dir / "dpd+sbs-mdict.zip"

# dpd_goldendict unzip to the specified directory
if dpd_goldendict_src.exists():
   # Unzip dpd_goldendict to the specified directory
   with ZipFile(dpd_goldendict_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(gd_dir)
   # Print completion message in green color
   print("\033[1;32m dpd+sbs-goldendict.zip has been unpacked to the server folder \033[0m")
else:
   print(f"\033[1;31m {dpd_goldendict_src} is missing. Cannot proceed with unziping. \033[0m")

# dpd_mdict unzip to the specified directory
if dpd_mdict_src.exists():
   # Unzip dpd_mdict to the specified directory
   with ZipFile(dpd_mdict_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(md_dir)
   # Print completion message in green color
   print("\033[1;32m dpd+sbs-mdict.zip has been unpacked to the server folder \033[0m")
else:
   print(f"\033[1;31m {dpd_mdict_src} is missing. Cannot proceed with unziping. \033[0m")
