#!/usr/bin/env python3

# unzip rudpd from download folder to the fileserver. And copy mdx and kindl versions as well. 

from pathlib import Path
from datetime import date
from zipfile import ZipFile
import shutil

today: date = date.today()

# Print completion message in green color
print("\033[1;33m from dpd-db/exporter/share/ \033[0m")

# Paths determined from the current working directory (project root)
project_dir: Path = Path.cwd()
deva_dir: Path = project_dir.parent.parent

# Source directory for ru-dpd files
downloads_dir: Path = deva_dir / "Downloads" / "DPDs" # e.g., /Users/deva/Downloads/DPDs

# Destination directories on the fileserver
software_dir: Path = deva_dir / "filesrv1" / "share1" / "Sharing between users" / "1 For Everyone" / "Software"
gd_dir: Path = software_dir / "Golden Dictionary" / "Optional"
md_dir: Path = software_dir / "MDict" / "ru-dpd"
kd_dir: Path = software_dir / "Ebook Readers Dictionary"

# Source file paths
dpd_src: Path = downloads_dir / "ru-dpd-goldendict.zip"
dpd_mdict_src: Path = downloads_dir / "ru-dpd-mdict.zip"
dpd_kindle_mobi_src: Path = downloads_dir / "ru-dpd-kindle.mobi"
dpd_kindle_epub_src: Path = downloads_dir / "ru-dpd-kindle.epub"

# Destination file paths for Kindle files
dpd_kindle_mobi_dest: Path = kd_dir / "ru-dpd-kindle.mobi"
dpd_kindle_epub_dest: Path = kd_dir / "ru-dpd-kindle.epub"

# Unzip ru-dpd-goldendict
if dpd_src.exists():
   with ZipFile(dpd_src, 'r') as zipObj:
      zipObj.extractall(gd_dir)
   print("\033[1;32m ru-dpd-goldendict.zip has been unpacked to the server folder \033[0m")
else:
   print(f"\033[1;31m {dpd_src} is missing. Cannot proceed with unpacking. \033[0m") # Changed "moving" to "unpacking" for clarity

# Unzip ru-dpd-mdict
if dpd_mdict_src.exists():
   with ZipFile(dpd_mdict_src, 'r') as zipObj:
      zipObj.extractall(md_dir)
   print("\033[1;32m ru-dpd-mdict.zip has been unpacked to the server folder \033[0m")
else:
   print(f"\033[1;31m {dpd_mdict_src} is missing. Cannot proceed with unpacking. \033[0m") # Changed "moving" to "unpacking"

# Copy ru-dpd-kindle.mobi
if dpd_kindle_mobi_src.exists():
   shutil.copy2(dpd_kindle_mobi_src, dpd_kindle_mobi_dest)
   print("\033[1;32m ru-dpd-kindle.mobi copied to the server \033[0m")
else:
   print(f"\033[1;31m {dpd_kindle_mobi_src} is missing. Cannot proceed with copying. \033[0m") # Changed "moving" to "copying"

# Copy ru-dpd-kindle.epub
if dpd_kindle_epub_src.exists():
   shutil.copy2(dpd_kindle_epub_src, dpd_kindle_epub_dest)
   print("\033[1;32m ru-dpd-kindle.epub copied to the server \033[0m")
else:
   print(f"\033[1;31m {dpd_kindle_epub_src} is missing. Cannot proceed with copying. \033[0m") # Changed "moving" to "copying"




