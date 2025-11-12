#!/usr/bin/env python3

# copy dpd_goldendict_src, dpd_mdict_src_mdx and dpd_mdict_src_mdd to share_dir / "SBS"

from pathlib import Path
from datetime import date
import shutil
from tools.printer import printer as pr

pr.tic()

today: date = date.today()

# Print completion message in green color
print("\033[1;33m from Share/ \033[0m")

project_dir: Path = Path.cwd()  # e.g., /Users/deva/Documents/dpd-db
deva_dir: Path = project_dir.parent.parent  # e.g., /Users/deva

# Destination directory within the project
share_dir: Path = project_dir / "exporter" / "share"
sbs_dir: Path = share_dir / "SBS"
sbs_dir.mkdir(parents=True, exist_ok=True)

dpd_goldendict_src: Path = share_dir / "dpd"
dpd_mdict_src_mdx: Path = share_dir / "dpd-mdict.mdx"
dpd_mdict_src_mdd: Path = share_dir / "dpd-mdict.mdd"


# dpd_goldendict copy folder to the specified directory
if dpd_goldendict_src.exists():
   # Copy the dpd folder to the SBS directory
   destination_path = sbs_dir / dpd_goldendict_src.name
   if destination_path.exists():
      shutil.rmtree(destination_path)
   shutil.copytree(str(dpd_goldendict_src), str(destination_path))
   # Print completion message in green color
   print("\033[1;32m dpd folder has been copied to the SBS folder \033[0m")

   # Archive the copied folder
   archive_source_path = destination_path
   archive_base_name = sbs_dir / "dpd"
   shutil.make_archive(str(archive_base_name), 'zip', str(archive_source_path))
   print(f"\033[1;32m {archive_base_name}.zip has been created in the share folder \033[0m")
else:
   print(f"\033[1;31m {dpd_goldendict_src} is missing. Cannot proceed with copying. \033[0m")

# dpd_mdict copy files to the specified directory
if dpd_mdict_src_mdx.exists() and dpd_mdict_src_mdd.exists():
   # Copy the specific MDict files
   shutil.copy2(str(dpd_mdict_src_mdx), str(sbs_dir))
   shutil.copy2(str(dpd_mdict_src_mdd), str(sbs_dir))
   # Print completion message in green color
   print("\033[1;32m dpd-mdict.mdx and dpd-mdict.mdd have been copied to the SBS folder \033[0m")
else:
   if not dpd_mdict_src_mdx.exists():
      print(f"\033[1;31m {dpd_mdict_src_mdx} is missing. Cannot proceed with copying. \033[0m")
   if not dpd_mdict_src_mdd.exists():
      print(f"\033[1;31m {dpd_mdict_src_mdd} is missing. Cannot proceed with copying. \033[0m")

pr.toc()
