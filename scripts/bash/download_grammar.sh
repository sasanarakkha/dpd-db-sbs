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

grammar=("[grammar](https://docs.google.com/spreadsheets/d/1-iNYm9R86162zFzLd9kraEqNP7DpAFczFMPTVttJSrs/edit?usp=sharing)")

# Loop through the list of grammar and extract the title and URL
for link in "${grammar[@]}"; do
    # Extract title from within square brackets
    title=$(echo "$link" | sed -n 's/\[\([^]]*\)\].*/\1/p')
    # Extract URL from within parentheses
    url=$(echo "$link" | sed -n 's/.*(\(https:[^)]*\)).*/\1/p' | sed 's/\/edit.*//')

    # Generate and execute the curl command with the formatted title, using a browser User-Agent
    curl -L -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" "$url/export?format=xlsx" -o "$title.xlsx"

    # Check if the downloaded file exists
    if [ ! -f "$title.xlsx" ]; then
        echo "\033[0;31mError: $title.xlsx not available at $url\033[0m"
        exit 1
    fi

    # Validate that the downloaded file is a Zip archive (Excel files are Zips)
    # This prevents processing HTML login pages as Excel files
    file_info=$(file "$title.xlsx")
    if [[ "$file_info" != *"Zip archive data"* ]]; then
        echo "\033[0;31mError: Downloaded file is not a valid Excel file.\033[0m"
        echo "It appears to be: $file_info"
        echo "This usually means the Google Sheet is invalid or not public."
        echo "Please ensure the Sheet is shared as 'Anyone with the link can view'."
        echo "URL: $url"
        # Optional: Print first few lines if it's text to show the error
        head -n 5 "$title.xlsx"
        exit 1
    fi
done



