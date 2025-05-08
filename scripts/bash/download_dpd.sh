#!/bin/bash

# This script downloads the latest DPD files from GitHub and saves them to a specified directory.
# It also checks for an internet connection before proceeding with the download.

# Check for internet connection
if ! ping -c 1 google.com &> /dev/null; then
    echo "\033[0;31mError: No internet connection. Please check your network settings."
    exit 1
fi

echo "--- download_patimokkha Script Started at $(date) ---"

mkdir -p "$HOME/Downloads/DPDs"
cd "$HOME/Downloads/DPDs"

DPD_links=(
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-goldendict.zip"
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-kindle.epub"
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-kindle.mobi"
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-kobo.zip"
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-mdict.zip"
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-pdf.zip"
)

DPD_SBS_links=(
    "https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/download/dpd+sbs-goldendict.zip"
    "https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/download/dpd+sbs-mdict.zip"
)

DPD_RU_links=(
    "https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/download/ru-dpd-goldendict.zip"
    "https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/download/ru-dpd-kindle.epub"
    "https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/download/ru-dpd-kindle.mobi"
    "https://github.com/sasanarakkha/dpd-db-sbs/releases/latest/download/ru-dpd-mdict.zip"
)

# Loop through the list of links and download them
for link in "${DPD_links[@]}"; do
    echo "Downloading $link..."
    wget -q --show-progress "$link"
done
for link in "${DPD_SBS_links[@]}"; do
    echo "Downloading $link..."
    wget -q --show-progress "$link"
done
for link in "${DPD_RU_links[@]}"; do
    echo "Downloading $link..."
    wget -q --show-progress "$link"
done

# print success message
echo -e "\033[0;32mAll files downloaded successfully.\033[0m"


