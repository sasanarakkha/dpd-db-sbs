#!/bin/bash

# This script downloads the latest Pali Classes files from GitHub and saves them to a specified directory.
# It also checks for an internet connection before proceeding with the download.

# Check for internet connection
if ! ping -c 1 google.com &> /dev/null; then
    echo "\033[0;31mError: No internet connection. Please check your network settings."
    exit 1
fi

echo "--- download_pali_classes Script Started at $(date) ---"

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
    echo "Downloading $link..."
    curl -q -# -L -O "$link"
done

# print success message
echo -e "\033[0;32mAll files downloaded successfully.\033[0m"
