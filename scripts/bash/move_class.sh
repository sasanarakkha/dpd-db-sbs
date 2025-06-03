#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Pipestatus: Preserve exit status of the first command in a pipe to fail.
set -o pipefail

# move all class materials on the server and GitHub

DOWNLOADS_DIR="$HOME/Downloads"
ANKI_CSVS_SRC_BASE_DIR="$HOME/Documents/dpd-db/anki_csvs"
PALI_CLASS_CSVS_SRC_DIR="$ANKI_CSVS_SRC_BASE_DIR/pali_class"
TEMP_PUSH_DEST_DIR="$HOME/Documents/sasanarakkha/study-tools/temp-push"
FILESRV_BASE_DEST_DIR="$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks"
FILESRV_CSVS_DEST_DIR="$FILESRV_BASE_DEST_DIR/csvs"

# Helper function to copy a single file, ensuring destination directory exists
safe_copy_file() {
    local src_file="$1"
    local dest_file="$2"
    local cp_options="${3:--f}" # Default to -f, can pass e.g. "-X -f" or "-rf"

    if [ ! -f "$src_file" ]; then
        echo "Warning: Source file '$src_file' not found. Skipping copy."
        return 0 # Continue script execution, but indicate non-fatal issue
    fi
    
    local dest_dir
    dest_dir=$(dirname "$dest_file")
    if ! mkdir -p "$dest_dir"; then
        echo "Error: Could not create destination directory '$dest_dir'. Skipping copy of '$src_file'."
        return 1 # This will cause script to exit due to set -e
    fi

    if cp $cp_options "$src_file" "$dest_file"; then
        echo "Successfully copied '$src_file' to '$dest_file'."
    else
        echo "Error: Failed to copy '$src_file' to '$dest_file'. Please check permissions and paths."
        return 1 # This will cause script to exit
    fi
}

# Helper function to move a single file, ensuring destination directory exists
safe_move_file() {
    local src_file="$1"
    local dest_file="$2"
    local mv_options="${3:--f}" # Default to -f, can pass e.g. "-X -f"

    if [ ! -f "$src_file" ]; then
        echo "Warning: Source file '$src_file' not found. Skipping move."
        return 0 # Continue script execution
    fi

    local dest_dir
    dest_dir=$(dirname "$dest_file")
    if ! mkdir -p "$dest_dir"; then
        echo "Error: Could not create destination directory '$dest_dir'. Skipping move of '$src_file'."
        return 1 # This will cause script to exit
    fi

    if mv $mv_options "$src_file" "$dest_file"; then
        echo "Successfully moved '$src_file' to '$dest_file'."
    else
        echo "Error: Failed to move '$src_file' to '$dest_file'. Please check permissions and paths."
        return 1 # This will cause script to exit
    fi
}

# Helper function to copy directory contents (recursive)
safe_copy_dir_contents() {
    local src_dir="$1"
    local dest_dir="$2"
    local cp_options="${3:--rf}" # Default to -rf, can pass e.g. "-X -rf"

    if [ ! -d "$src_dir" ]; then
        echo "Warning: Source directory '$src_dir' not found. Skipping copy of its contents."
        return 0 # Continue script execution
    fi
    
    if [ -z "$(ls -A "$src_dir" 2>/dev/null)" ]; then # Added 2>/dev/null to suppress ls error if dir is unreadable
        echo "Info: Source directory '$src_dir' is empty or not accessible. Nothing to copy."
        return 0
    fi

    if ! mkdir -p "$dest_dir"; then
        echo "Error: Could not create destination directory '$dest_dir'. Skipping copy of '$src_dir' contents."
        return 1 # This will cause script to exit
    fi
    
    # The trailing slash on src_dir with * ensures contents are copied, not the dir itself.
    # The trailing slash on dest_dir ensures it's treated as a directory.
    if cp $cp_options "${src_dir}/"* "$dest_dir/"; then
        echo "Successfully copied contents of '$src_dir' to '$dest_dir'."
    else
        echo "Error: Failed to copy contents of '$src_dir' to '$dest_dir'. Check permissions, especially for creating subdirectories like 'grammar' in the destination."
        return 1 # This will cause script to exit
    fi
}

cd "$DOWNLOADS_DIR" || { echo "Error: Could not cd to $DOWNLOADS_DIR. Exiting."; exit 1; }

echo "--- Processing APKG files ---"
safe_copy_file "Vocab Pali Class.apkg" "$TEMP_PUSH_DEST_DIR/vocab-pali-class.apkg"
safe_move_file "Vocab Pali Class.apkg" "$FILESRV_BASE_DEST_DIR/Vocab Pali Class.apkg" "-f"
safe_copy_file "Grammar Pali Class.apkg" "$TEMP_PUSH_DEST_DIR/grammar-pali-class.apkg"
safe_move_file "Grammar Pali Class.apkg" "$FILESRV_BASE_DEST_DIR/Grammar Pali Class.apkg" "-f"
safe_copy_file "Roots Pali Class.apkg" "$TEMP_PUSH_DEST_DIR/roots-pali-class.apkg"
safe_move_file "Roots Pali Class.apkg" "$FILESRV_BASE_DEST_DIR/Roots Pali Class.apkg" "-f"
safe_copy_file "Phonetic Changes Pali Class.apkg" "$TEMP_PUSH_DEST_DIR/phonetic-pali-class.apkg"
safe_move_file "Phonetic Changes Pali Class.apkg" "$FILESRV_BASE_DEST_DIR/Phonetic Changes Pali Class.apkg" "-f"
safe_copy_file "Common Roots Pali Class.apkg" "$TEMP_PUSH_DEST_DIR/common-roots-pali-class.apkg"
safe_move_file "Common Roots Pali Class.apkg" "$FILESRV_BASE_DEST_DIR/Common Roots Pali Class.apkg" "-f"
safe_copy_file "Suttas Advanced Pali Class.apkg" "$TEMP_PUSH_DEST_DIR/suttas-advanced-pali-class.apkg"
safe_move_file "Suttas Advanced Pali Class.apkg" "$FILESRV_BASE_DEST_DIR/Suttas Advanced Pali Class.apkg" "-f"
echo "APKG processing - done"

echo "--- Processing CSV files ---"
# Copy all files and subdirectories from pali_class source to fileserver csvs destination
safe_copy_dir_contents "$PALI_CLASS_CSVS_SRC_DIR" "$FILESRV_CSVS_DEST_DIR" "-X -rf"

# Copy specific CSV files to temp-push directory
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/class_all.csv" "$TEMP_PUSH_DEST_DIR/vocab-pali-class.csv" "-rf"
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/phonetic_class.csv" "$TEMP_PUSH_DEST_DIR/phonetic-pali-class.csv" "-rf"
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/roots_class.csv" "$TEMP_PUSH_DEST_DIR/roots-pali-class.csv" "-rf"
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/suttas_class.csv" "$TEMP_PUSH_DEST_DIR/suttas-advanced-pali-class.csv" "-rf"

# Copy grammar CSV files
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/grammar/cl_sum_abbr.csv" "$TEMP_PUSH_DEST_DIR/grammar-pali-class-abbr.csv" "-rf"
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/grammar/cl_sum_gramm.csv" "$TEMP_PUSH_DEST_DIR/grammar-pali-class-gramm.csv" "-rf"
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/grammar/cl_sum_sandhi.csv" "$TEMP_PUSH_DEST_DIR/grammar-pali-class-sandhi.csv" "-rf"

# cp -f "$HOME/Documents/dps/csv-for-anki/abbr.xlsx" "$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks/abbreviations.xlsx"

echo "CSV processing for Anki - done"
echo "--- Script finished ---"
