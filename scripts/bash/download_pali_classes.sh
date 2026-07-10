#!/bin/bash

# This script downloads the latest Pali Classes files from GitHub and saves them to a specified directory.
# It also checks for an internet connection before proceeding with the download.

ASK_PY="$HOME/Documents/dpd-db/tools/ask.py"

# Check for internet connection
if ! ping -c 1 google.com &> /dev/null; then
    uv run "$ASK_PY" -p -c red "Error: No internet connection. Please check your network settings."
    exit 1
fi

uv run "$ASK_PY" --print "--- download_pali_classes Script Started at $(date) ---"

mkdir -p "$HOME/Downloads/Pali_classes"
cd "$HOME/Downloads/Pali_classes"

Class_links=(
    "https://github.com/digitalpalidictionary/dpd-pali-courses/releases/latest/download/beginner_pali_course_exercises_docx.zip"
    "https://github.com/digitalpalidictionary/dpd-pali-courses/releases/latest/download/beginner_pali_course_pdfs.zip"
    "https://github.com/digitalpalidictionary/dpd-pali-courses/releases/latest/download/intermediate_pali_course_exercises_docx.zip"
    "https://github.com/digitalpalidictionary/dpd-pali-courses/releases/latest/download/intermediate_pali_course_pdfs.zip"
    "https://github.com/digitalpalidictionary/dpd-pali-courses/releases/latest/download/website_offline.zip"
)

# Loop through the list of links and download them
for link in "${Class_links[@]}"; do
    uv run "$ASK_PY" --print "Downloading $link..."
    curl -q -# -L -O "$link"
done

# print success message
uv run "$ASK_PY" -p -c green "All files downloaded successfully."
