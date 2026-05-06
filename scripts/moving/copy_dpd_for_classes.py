#!/usr/bin/env python3

# copy tipitaka_pali.db, dpd goldendict folder, and bash script to the for_classes server folder.

import sys
from pathlib import Path
import shutil
from tools.printer import printer as pr
from tools.configger import config_read


pr.tic()

print("\033[1;33m copying tipitaka_pali.db and dpd_goldendict_src \033[0m")

# Project structure (same logic)
project_dir: Path = Path.cwd()
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

tp_db_dest: Path = dest_dir / "tipitaka_pali.db"
dpd_goldendict_dest: Path = dest_dir / "dpd"

if not dest_dir.exists():
    pr.no(f"destination not found: {dest_dir}")
    sys.exit(1)

# ---------- Copy tipitaka db ----------

if tpr_db_path:
    shutil.copy2(tpr_db_path, tp_db_dest)
    print("\033[1;32m tipitaka_pali.db copied successfully \033[0m")
else:
    print(f"\033[1;31m Missing tipitaka db: {tpr_db_path} \033[0m")

# ---------- Copy dpd goldendict folder ----------

if dpd_goldendict_src.exists():
    if dpd_goldendict_dest.exists():
        shutil.rmtree(dpd_goldendict_dest)
    shutil.copytree(dpd_goldendict_src, dpd_goldendict_dest)
    print("\033[1;32m dpd_goldendict_src folder copied successfully \033[0m")
else:
    print(f"\033[1;31m Missing dpd_goldendict_src folder: {dpd_goldendict_src} \033[0m")

# ----------  Copy bash script ----------

if bash_script.exists():
    shutil.copy2(bash_script, dest_dir)
    print("\033[1;32m bash script copied successfully \033[0m")
else:
    print(f"\033[1;31m Missing bash script: {bash_script} \033[0m")

pr.toc()
