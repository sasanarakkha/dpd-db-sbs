#!/usr/bin/env python3

# unzip pali classes from Download to the fileserver.

import sys
from datetime import date
from pathlib import Path
from zipfile import ZipFile

from tools.printer import printer as pr

pr.tic()

today: date = date.today()

# Print completion message in green color
print("\033[1;33m from Downloads/ \033[0m")

project_dir: Path = Path.cwd()  # e.g., /Users/deva/Documents/dpd-db
deva_dir: Path = project_dir.parent.parent  # e.g., /Users/deva
downloads_dir: Path = (
    deva_dir / "Downloads" / "Pali_classes"
)  # e.g., /Users/deva/Downloads/Pali_classes

materials_dir: Path = (
    deva_dir
    / "filesrv1"
    / "share1"
    / "Sharing between users"
    / "13 For Pāli class"
    / "offline materials"
)
beginner_dir: Path = materials_dir / "beginner"
intermediate_dir: Path = materials_dir / "intermediate"

beginner_docs_src: Path = downloads_dir / "beginner_pali_course_exercises_docx.zip"
beginner_pdfs_src: Path = downloads_dir / "beginner_pali_course_pdfs.zip"
intermediate_docs_src: Path = (
    downloads_dir / "intermediate_pali_course_exercises_docx.zip"
)
intermediate_pdfs_src: Path = downloads_dir / "intermediate_pali_course_pdfs.zip"

for dest in [beginner_dir, intermediate_dir]:
    if not dest.exists():
        pr.no(f"destination not found: {dest}")
        sys.exit(1)

# unzip beginner
if beginner_docs_src.exists():
    # Unzip to the specified directory
    with ZipFile(beginner_docs_src, "r") as zipObj:
        # Extract all the contents of zip file in current directory
        zipObj.extractall(beginner_dir)
    # Print completion message in green color
    print("\033[1;32m beginner_docs_src has been unpacked to the server folder \033[0m")
else:
    print(
        f"\033[1;31m {beginner_docs_src} is missing. Cannot proceed with unziping. \033[0m"
    )

if beginner_pdfs_src.exists():
    # Unzip to the specified directory
    with ZipFile(beginner_pdfs_src, "r") as zipObj:
        # Extract all the contents of zip file in current directory
        zipObj.extractall(beginner_dir)
    # Print completion message in green color
    print("\033[1;32m beginner_pdfs_src has been unpacked to the server folder \033[0m")
else:
    print(
        f"\033[1;31m {beginner_pdfs_src} is missing. Cannot proceed with unziping. \033[0m"
    )

# unzip intermediate
if intermediate_docs_src.exists():
    # Unzip to the specified directory
    with ZipFile(intermediate_docs_src, "r") as zipObj:
        # Extract all the contents of zip file in current directory
        zipObj.extractall(intermediate_dir)
    # Print completion message in green color
    print(
        "\033[1;32m intermediate_docs_src has been unpacked to the server folder \033[0m"
    )
else:
    print(
        f"\033[1;31m {intermediate_docs_src} is missing. Cannot proceed with unziping. \033[0m"
    )

if intermediate_pdfs_src.exists():
    # Unzip to the specified directory
    with ZipFile(intermediate_pdfs_src, "r") as zipObj:
        # Extract all the contents of zip file in current directory
        zipObj.extractall(intermediate_dir)
    # Print completion message in green color
    print(
        "\033[1;32m intermediate_pdfs_src has been unpacked to the server folder \033[0m"
    )
else:
    print(
        f"\033[1;31m {intermediate_pdfs_src} is missing. Cannot proceed with unziping. \033[0m"
    )

pr.toc()
