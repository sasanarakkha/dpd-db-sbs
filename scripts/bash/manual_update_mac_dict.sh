#!/bin/bash
# Update the DPD Mac Dictionary by unzipping the archive from the Downloads folder.
set -e

# --- CONFIGURATION ---
DICT_NAME="Digital-Pali-Dictionary.dictionary"
DEST_DIR="$HOME/Library/Dictionaries"
TARGET_DICT_PATH="$DEST_DIR/$DICT_NAME"

# Zip file path
ZIP_FILENAME="dpd-apple.dictionary.zip"
ZIP_PATH="$HOME/Downloads/DPDs/$ZIP_FILENAME"
# ---------------------

# Helper function to close Dictionary app to prevent lock issues
function close_dictionary_app() {
    if pgrep -x "Dictionary" > /dev/null; then
        uv run tools/ask.py --print -c yellow "Closing Dictionary app to perform updates..."
        killall Dictionary
        sleep 1
    fi
}

# Helper function to refresh the dictionary cache
function refresh_dict() {
    uv run tools/ask.py --print "Touching dictionary to trigger system refresh..."
    touch "$TARGET_DICT_PATH"
    uv run tools/ask.py --print -c green "Update complete. You can now open the Dictionary app."
}

# Check if the zip file exists and proceed with the update
if [ -f "$ZIP_PATH" ]; then
    close_dictionary_app

    uv run tools/ask.py --print -c yellow "Unzipping $ZIP_FILENAME..."
    # -o overwrites without asking, -d specifies destination
    unzip -o "$ZIP_PATH" -d "$DEST_DIR"

    refresh_dict
else
    uv run tools/ask.py --print -c red "Error: Zip file not found at:"
    uv run tools/ask.py --print -c red "   $ZIP_PATH"
fi