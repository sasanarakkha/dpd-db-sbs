#!/bin/bash

# This script downloads the grammar spreadsheet from Google Sheets 
# It also checks for internet connection and logs the output.

# Check for internet connection
if ! ping -c 1 google.com &> /dev/null; then
    echo "\033[0;31mError: No internet connection. Please check your network settings."
    exit 1
fi

# exec > >(tee "$HOME/logs/download_grammar.log") 2>&1

echo "--- download_grammar Script Started at $(date) ---"

# mkdir -p "$HOME/Downloads"
cd "$HOME/Downloads"

grammar=("[grammar](https://docs.google.com/spreadsheets/d/1KV5LmebIQpNyNKl03Pmo_Ti-LNW3IYWB6uc7OfGRGPU/)")

# Loop through the list of grammar and extract the title and URL
for link in "${grammar[@]}"; do
    # Extract title from within square brackets
    title=$(echo "$link" | sed -n 's/\[\([^]]*\)\].*/\1/p')
    # Extract URL from within parentheses
    url=$(echo "$link" | sed -n 's/.*(\(https:[^)]*\)).*/\1/p' | sed 's/\/$//')

    # Generate and execute the curl command with the formatted title
    curl -L "$url/export?format=xlsx" -o "$title.xlsx"

    # Check if the downloaded file exists
    if [ ! -f "$title.xlsx" ]; then
        echo "\033[0;31mError: $title.xlsx not available at $url\033[0m"
        exit 1
    fi
done



