#!/bin/bash

# This script downloads the Pātimokkha Word by Word spreadsheet from Google Sheets and moves it to the fileserver if mounted.
# It also checks for internet connection and logs the output.

# Check for internet connection
if ! ping -c 1 google.com &> /dev/null; then
    echo "\033[0;31mError: No internet connection. Please check your network settings."
    exit 1
fi

# exec > >(tee "$HOME/logs/download_patimokkha.log") 2>&1

echo "--- download_patimokkha Script Started at $(date) ---"

# mkdir -p "$HOME/Downloads"
cd "$HOME/Downloads"

pat=("[Pātimokkha Word by Word](https://docs.google.com/spreadsheets/d/1rS-IlX4DvKmnBO58KON37eVnOZqwfkG-ot-zIjCuzH4/)")

# Loop through the list of per and extract the title and URL
for link in "${pat[@]}"; do
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


# Check if the fileserver is mounted
if [ -d "$HOME/filesrv1/share1/Sharing between users" ]; then

    echo "Moving folders to the fileserver"

    # Copy folders on the server
    cp -X -rf "$HOME/Downloads/Pātimokkha Word by Word.xlsx" "$HOME/filesrv1/share1/Sharing between users/16 For Pātimokkha Class/offline/Pātimokkha Word by Word.xlsx"

    echo "Pātimokkha copied to the fileserver"

else
    echo "Fileserver is not mounted. Skipping copying folders."
fi

