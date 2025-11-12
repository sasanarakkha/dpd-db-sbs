#!/usr/bin/env python3

# copy dpd-sbs golden dict, mdict from Download to the fileserver.   

from pathlib import Path
from datetime import date
import shutil
from zipfile import ZipFile
from tools.printer import printer as pr

pr.tic()

today: date = date.today()


# Print completion message in green color
print("\033[1;33m from Share/ \033[0m")

project_dir: Path = Path.cwd()  # e.g., /Users/deva/Documents/dpd-db
deva_dir: Path = project_dir.parent.parent  # e.g., /Users/deva

# Destination directory within the project
share_sbs_dir: Path = project_dir / "exporter" / "share" / "SBS"

software_dir: Path = deva_dir / "filesrv1" / "share1" / "Sharing between users" / "1 For Everyone" / "Software"
gd_dir: Path = software_dir / "Golden Dictionary" / "Default"

md_dir: Path = software_dir / "MDict" / "dpd"
kd_dir: Path = software_dir / "Ebook Readers Dictionary"

dpd_zip_src: Path = share_sbs_dir / "dpd.zip"
dpd_mdict_src_mdx: Path = share_sbs_dir / "dpd-mdict.mdx"
dpd_mdict_src_mdd: Path = share_sbs_dir / "dpd-mdict.mdd"

# unzip dpd
if dpd_zip_src.exists():
   # Unzip to the specified directory
   destination_path = gd_dir / "dpd"
   with ZipFile(dpd_zip_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(destination_path)
   # Print completion message in green color
   print("\033[1;32m dpd_zip_src has been unpacked to the server folder \033[0m")
else:
   print(f"\033[1;31m {dpd_zip_src} is missing. Cannot proceed with unziping. \033[0m")


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