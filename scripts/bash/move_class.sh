#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Pipestatus: Preserve exit status of the first command in a pipe to fail.
set -o pipefail

# move all class materials on the server and GitHub

ANKI_DECKS_DIR="$HOME/Documents/dpd-db/temp/anki_decks"
ANKI_CSVS_SRC_BASE_DIR="$HOME/Documents/dpd-db/temp/anki_csvs"
PALI_CLASS_CSVS_SRC_DIR="$ANKI_CSVS_SRC_BASE_DIR/pali_class"
TEMP_PUSH_DEST_DIR="$HOME/Documents/sasanarakkha/study-tools/temp-push"
FILESRV_BASE_DEST_DIR="$HOME/filesrv1/share1/Sharing between users/13 For Pāli class/Anki Decks"
FILESRV_CSVS_DEST_DIR="$FILESRV_BASE_DEST_DIR/csvs"

FAILURES=()

# Helper function to copy a single file, ensuring destination directory exists
safe_copy_file() {
    local src_file="$1"
    local dest_file="$2"

    if [ ! -f "$src_file" ]; then
        uv run tools/ask.py -p -c yellow "Warning: Source file '$src_file' not found. Skipping copy."
        return 0 # Continue script execution
    fi
    
    local dest_dir
    dest_dir=$(dirname "$dest_file")
    if [ ! -d "$dest_dir" ]; then
        uv run tools/ask.py -p -c red "Error: Destination directory '$dest_dir' does not exist. Stopping."
        exit 1
    fi

    # Switched to rsync for potentially better handling of metadata with network shares on macOS.
    # The --times flag preserves modification times.
    # --no-perms, --no-owner, --no-group prevent rsync from trying to set these on the destination,
    # which can cause "Operation not permitted" errors on some network shares.
    if ! rsync --times --no-perms --no-owner --no-group "$src_file" "$dest_file"; then
        uv run tools/ask.py -p -c red "Error: Failed to copy '$src_file' to '$dest_file'."
        FAILURES+=("$src_file → $dest_file")
        return 1
    fi
    return 0
}

# Helper function to copy directory contents (recursive)
safe_copy_dir_contents() {
    local src_dir="$1"
    local dest_dir="$2"

    if [ ! -d "$src_dir" ]; then
        uv run tools/ask.py -p -c yellow "Warning: Source directory '$src_dir' not found. Skipping copy of its contents."
        return 0 # Continue script execution
    fi
    
    if [ -z "$(ls -A "$src_dir" 2>/dev/null)" ]; then
        return 0
    fi

    if [ ! -d "$dest_dir" ]; then
        uv run tools/ask.py -p -c red "Error: Destination directory '$dest_dir' does not exist. Stopping."
        exit 1
    fi
    
    # Using rsync to copy directory contents.
    # -r: recursive
    # --times: preserve modification times
    # --no-perms, --no-owner, --no-group: avoid permission issues on network shares
    # The trailing slash on "${src_dir}/" ensures rsync copies the *contents* of the source directory.
    if ! rsync -r --times --no-perms --no-owner --no-group --exclude '.DS_Store' "${src_dir}/" "$dest_dir/"; then
        uv run tools/ask.py -p -c red "Error: Failed to copy contents of '$src_dir' to '$dest_dir'."
        FAILURES+=("$src_dir/ → $dest_dir/")
        return 1
    fi
    return 0
}

if [ ! -d "$FILESRV_BASE_DEST_DIR" ]; then
    uv run tools/ask.py -p -c red "Error: Fileserver directory not found: $FILESRV_BASE_DEST_DIR. Stopping."
    exit 1
fi
if [ ! -d "$FILESRV_CSVS_DEST_DIR" ]; then
    uv run tools/ask.py -p -c red "Error: Fileserver directory not found: $FILESRV_CSVS_DEST_DIR. Stopping."
    exit 1
fi

cd "$ANKI_DECKS_DIR" || { uv run tools/ask.py -p -c red "Error: Could not cd to $ANKI_DECKS_DIR. Exiting."; exit 1; }

uv run tools/ask.py -p "--- Processing APKG files ---"
safe_copy_file "vocab_pali_class.apkg" "$TEMP_PUSH_DEST_DIR/vocab-pali-class.apkg" || true
safe_copy_file "vocab_pali_class.apkg" "$FILESRV_BASE_DEST_DIR/Vocab Pali Class.apkg" || true
safe_copy_file "grammar_pali_class.apkg" "$TEMP_PUSH_DEST_DIR/grammar-pali-class.apkg" || true
safe_copy_file "grammar_pali_class.apkg" "$FILESRV_BASE_DEST_DIR/Grammar Pali Class.apkg" || true
safe_copy_file "roots_pali_class.apkg" "$TEMP_PUSH_DEST_DIR/roots-pali-class.apkg" || true
safe_copy_file "roots_pali_class.apkg" "$FILESRV_BASE_DEST_DIR/Roots Pali Class.apkg" || true
safe_copy_file "phonetic_changes_pali_class.apkg" "$TEMP_PUSH_DEST_DIR/phonetic-pali-class.apkg" || true
safe_copy_file "phonetic_changes_pali_class.apkg" "$FILESRV_BASE_DEST_DIR/Phonetic Changes Pali Class.apkg" || true
safe_copy_file "common_roots.apkg" "$TEMP_PUSH_DEST_DIR/common-roots.apkg" || true
safe_copy_file "common_roots.apkg" "$FILESRV_BASE_DEST_DIR/Common Roots.apkg" || true
safe_copy_file "suttas_advanced_pali_class.apkg" "$TEMP_PUSH_DEST_DIR/suttas-advanced-pali-class.apkg" || true
safe_copy_file "suttas_advanced_pali_class.apkg" "$FILESRV_BASE_DEST_DIR/Suttas Advanced Pali Class.apkg" || true

uv run tools/ask.py -p "--- Processing CSV files ---"
# Copy all files and subdirectories from pali_class source to fileserver csvs destination
safe_copy_dir_contents "$PALI_CLASS_CSVS_SRC_DIR" "$FILESRV_CSVS_DEST_DIR" || true

# Copy specific CSV files to temp-push directory
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/class_all.csv" "$TEMP_PUSH_DEST_DIR/vocab-pali-class.csv" || true
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/phonetic_class.csv" "$TEMP_PUSH_DEST_DIR/phonetic-pali-class.csv" || true
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/roots_class.csv" "$TEMP_PUSH_DEST_DIR/roots-pali-class.csv" || true
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/suttas_class.csv" "$TEMP_PUSH_DEST_DIR/suttas-advanced-pali-class.csv" || true
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/common_roots.csv" "$TEMP_PUSH_DEST_DIR/common-roots.csv" || true
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/ru_common_roots.csv" "$TEMP_PUSH_DEST_DIR/ru-common-roots.csv" || true

# Copy grammar CSV files
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/grammar/cl_sum_abbr.csv" "$TEMP_PUSH_DEST_DIR/grammar-pali-class-abbr.csv" || true
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/grammar/cl_sum_gramm.csv" "$TEMP_PUSH_DEST_DIR/grammar-pali-class-gramm.csv" || true
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/grammar/cl_sum_sandhi.csv" "$TEMP_PUSH_DEST_DIR/grammar-pali-class-sandhi.csv" || true
safe_copy_file "$PALI_CLASS_CSVS_SRC_DIR/grammar/ru_cl_sum_gramm.csv" "$TEMP_PUSH_DEST_DIR/ru-grammar-pali-class-gramm.csv" || true

if [ ${#FAILURES[@]} -eq 0 ]; then
    uv run tools/ask.py -p -c green "All files copied successfully."
else
    uv run tools/ask.py -p -c red "The following copies failed:"
    for f in "${FAILURES[@]}"; do
        uv run tools/ask.py -p -c red "  - $f"
    done
fi
