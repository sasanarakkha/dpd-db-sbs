#!/usr/bin/env python3

# unzip dpd golden dict, mdict and pdf from local folder Download to the fileserver. And copy kindle and kobo versions as well. 

from pathlib import Path
from datetime import date
from zipfile import ZipFile

import shutil

today: date = date.today()

# Print completion message in green color
print("\033[1;33m from Downloads/ \033[0m")

project_dir: Path = Path.cwd()  # e.g., /Users/deva/Documents/dpd-db
deva_dir: Path = project_dir.parent.parent  # e.g., /Users/deva
downloads_dir: Path = deva_dir / "Downloads" / "DPDs" # e.g., /Users/deva/Downloads/DPDs

software_dir: Path = deva_dir / "filesrv1" / "share1" / "Sharing between users" / "1 For Everyone" / "Software"
gd_dir: Path = software_dir / "Golden Dictionary" / "Default"

md_dir: Path = software_dir / "MDict" / "dpd"
kd_dir: Path = software_dir / "Ebook Readers Dictionary"

dpd_goldendict_src: Path = downloads_dir / "dpd-goldendict.zip"
dpd_mdict_src: Path = downloads_dir / "dpd-mdict.zip"
dpd_kindle_mobi_src: Path = downloads_dir / "dpd-kindle.mobi"
dpd_kindle_mobi_dest: Path = kd_dir / "dpd-kindle.mobi"
dpd_kindle_epub_src: Path = downloads_dir / "dpd-kindle.epub"
dpd_kindle_epub_dest: Path = kd_dir / "dpd-kindle.epub"
dpd_kobo_src: Path = downloads_dir / "dpd-kobo.zip"
dpd_kobo_dest: Path = kd_dir / "dpd-kobo.zip"
dpd_pdf_src: Path = downloads_dir / "dpd-pdf.zip"

# dpd_goldendict unzip to the specified directory
if dpd_goldendict_src.exists():
   # Unzip dpd_goldendict to the specified directory
   with ZipFile(dpd_goldendict_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(gd_dir)
   # Print completion message in green color
   print("\033[1;32m dpd_goldendict.zip has been unpacked to the server folder \033[0m")
else:
   print(f"\033[1;31m {dpd_goldendict_src} is missing. Cannot proceed with unziping. \033[0m")

# dpd_mdict unzip to the specified directory
if dpd_mdict_src.exists():
   # Unzip dpd_mdict to the specified directory
   with ZipFile(dpd_mdict_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(md_dir)
   # Print completion message in green color
   print("\033[1;32m dpd_mdict.zip has been unpacked to the server folder \033[0m")
else:
   print(f"\033[1;31m {dpd_mdict_src} is missing. Cannot proceed with unziping. \033[0m")

# dpd_kindle mobi move to the specified directory
if dpd_kindle_mobi_src.exists():
   shutil.move(dpd_kindle_mobi_src, dpd_kindle_mobi_dest)
   print("\033[1;32m dpd_kindle.mobi moved to the server \033[0m")
else:
   print(f"\033[1;31m {dpd_kindle_mobi_src} is missing. Cannot proceed with moving. \033[0m")

# dpd_kindle epub move to the specified directory
if dpd_kindle_epub_src.exists():
   shutil.move(dpd_kindle_epub_src, dpd_kindle_epub_dest)
   print("\033[1;32m dpd_kindle.epub moved to the server \033[0m")
else:
   print(f"\033[1;31m {dpd_kindle_epub_src} is missing. Cannot proceed with moving. \033[0m")

# dpd_kobo move to the specified directory
if dpd_kobo_src.exists():
   shutil.move(dpd_kobo_src, dpd_kobo_dest)
   print("\033[1;32m dpd-kobo.zip moved to the server \033[0m")
else:
   print(f"\033[1;31m {dpd_kobo_src} is missing. Cannot proceed with moving. \033[0m")

# dpd_pdf unzip to the specified directory
if dpd_pdf_src.exists():
   # Unzip dpd_pdf to the specified directory
   with ZipFile(dpd_pdf_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(kd_dir)
   # Print completion message in green color
   print("\033[1;32m dpd_pdf.zip has been unpacked to the server folder \033[0m")
else: 
   print(f"\033[1;31m {dpd_pdf_src} is missing. Cannot proceed with unziping. \033[0m")








