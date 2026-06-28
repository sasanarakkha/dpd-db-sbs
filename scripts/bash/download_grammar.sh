#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Script: download_grammar.sh
# Downloads the grammar spreadsheet from Google Sheets as .xlsx

ask() { uv run "$REPO_ROOT/tools/ask.py" --print "$@"; }

# Check for internet connection using HTTP (more reliable than ICMP ping)
if ! curl -sS --head https://google.com > /dev/null 2>&1; then
    ask -c red "Error: No internet connection. Please check your network settings."
    exit 1
fi

ask -c cyan "--- download_grammar Script Started at $(date) ---"

# Ensure temp directory exists
mkdir -p "$REPO_ROOT/temp"

grammar_url="https://docs.google.com/spreadsheets/d/1-iNYm9R86162zFzLd9kraEqNP7DpAFczFMPTVttJSrs"
title="grammar"
output="$REPO_ROOT/temp/$title.xlsx"

# Download xlsx export using a browser User-Agent
curl -L -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
    "$grammar_url/export?format=xlsx" -o "$output"

# Check if the downloaded file exists
if [ ! -f "$output" ]; then
    ask -c red "Error: $title.xlsx not available at $grammar_url"
    exit 1
fi

# Validate that the downloaded file is a Zip archive (Excel files are Zips)
# This prevents processing HTML login pages as Excel files
file_info=$(file "$output")
if [[ "$file_info" != *"Zip archive data"* ]] && [[ "$file_info" != *"Microsoft Excel 2007+"* ]]; then
    ask -c red "Error: Downloaded file is not a valid Excel file."
    ask -c red "It appears to be: $file_info"
    ask -c red "This usually means the Google Sheet is invalid or not public."
    ask -c red "Please ensure the Sheet is shared as 'Anyone with the link can view'."
    ask -c red "URL: $grammar_url"
    exit 1
fi

ask -c green "Downloaded: $title.xlsx"
ask -c green "Folder: $REPO_ROOT/temp"

