#!/bin/bash

# --- CONFIGURATION ---
DICT_NAME="Digital-Pali-Dictionary.dictionary"
DEST_DIR="$HOME/Library/Dictionaries"
TARGET_DICT_PATH="$DEST_DIR/$DICT_NAME"

# Option 1 Source: The unzipped folder path
SRC_FOLDER="$HOME/Downloads/DPDs/$DICT_NAME/Contents"

# Option 2 Source: The zip file path
ZIP_FILENAME="dpd-apple.dictionary.zip"
ZIP_PATH="$HOME/Downloads/DPDs/$ZIP_FILENAME"
# ---------------------

# Helper function to close Dictionary app to prevent lock issues
function close_dictionary_app() {
    if pgrep -x "Dictionary" > /dev/null; then
        echo "📖 Closing Dictionary app to perform updates..."
        killall Dictionary
        sleep 1
    fi
}

# Helper function to refresh the dictionary cache
function refresh_dict() {
    echo "♻️  Touching dictionary to trigger system refresh..."
    touch "$TARGET_DICT_PATH"
    echo "✅ Update Complete!"
    echo "   You can now open the Dictionary app."
}

clear
echo "============================================"
echo "   Digital Pāli Dictionary Updater (DPD)"
echo "============================================"
echo "1) Copy & Replace 'Contents' from Downloads folder"
echo "   (Source: $SRC_FOLDER)"
echo ""
echo "2) Unpack '$ZIP_FILENAME' from Downloads"
echo "   (Source: $ZIP_PATH)"
echo "============================================"
read -p "Select an option [1 or 2]: " choice

case $choice in
    1)
        # OPTION 1: Copy from Folder
        if [ -d "$SRC_FOLDER" ]; then
            close_dictionary_app
            
            echo "📂 Removing old Contents..."
            # Remove the old Contents to ensure no stale files remain
            rm -rf "$TARGET_DICT_PATH/Contents"
            
            echo "📂 Copying new Contents..."
            # Ensure target directory exists (just in case)
            mkdir -p "$TARGET_DICT_PATH"
            cp -R "$SRC_FOLDER" "$TARGET_DICT_PATH/"
            
            refresh_dict
        else
            echo "❌ Error: Source folder not found at:"
            echo "   $SRC_FOLDER"
        fi
        ;;

    2)
        # OPTION 2: Unzip from Archive
        if [ -f "$ZIP_PATH" ]; then
            close_dictionary_app
            
            echo "📦 Unzipping $ZIP_FILENAME..."
            # -o overwrites without asking, -d specifies destination
            unzip -o "$ZIP_PATH" -d "$DEST_DIR"
            
            refresh_dict
        else
            echo "❌ Error: Zip file not found at:"
            echo "   $ZIP_PATH"
        fi
        ;;

    *)
        echo "❌ Invalid selection."
        ;;
esac