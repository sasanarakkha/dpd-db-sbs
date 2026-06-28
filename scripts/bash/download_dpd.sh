#!/bin/bash

# Downloads DPD/SBS/RU release artifacts from GitHub to ~/Downloads/DPDs/.
# SBS and RU groups are defined but commented out -- available for future activation.

ask_and_run() {
    local prompt="$1"
    shift
    local links=("$@")
    response=$(uv run python tools/ask.py "$prompt") || exit 1
    if [[ $response == "y" ]]; then
        for link in "${links[@]}"; do
            uv run tools/ask.py --print "Downloading $(basename "$link")..."
            curl -q -# -L -O "$link"
        done
    fi
}

# Check for internet connection
if ! ping -c 1 google.com &> /dev/null; then
    uv run tools/ask.py --print -c red "Error: No internet connection."
    exit 1
fi

mkdir -p "$HOME/Downloads/DPDs"
cd "$HOME/Documents/dpd-db"

DPD_links=(
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-goldendict.zip"
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-kindle.epub"
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-kindle.mobi"
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-kobo.zip"
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-mdict.zip"
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-pdf.zip"
    "https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd-apple.dictionary.zip"
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

ask_and_run "Download DPD files?" "${DPD_links[@]}"
# ask_and_run "Download SBS files?" "${DPD_SBS_links[@]}"
# ask_and_run "Download RU files?" "${DPD_RU_links[@]}"
cd "$HOME/Downloads/DPDs"


