#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Pipestatus: Preserve exit status of the first command in a pipe to fail.
set -o pipefail

# move all decks on the server and GitHub

ANKI_CSVS_SRC_DIR="$HOME/Documents/dpd-db/temp/anki_csvs"
ANKI_DECKS_DIR="$HOME/Documents/dpd-db/temp/anki_decks"
FILESRV_DEST_BASE_DIR="$HOME/filesrv1/share1/Sharing between users/1 For Everyone/Software/Anki (learning tool)"
FILESRV_PAT_DIR="$HOME/filesrv1/share1/Sharing between users/16 For Pātimokkha Class/offline"
TEMP_PUSH_DEST_DIR="$HOME/Documents/sasanarakkha/study-tools/temp-push"

FAILURES=()

# Helper function to copy a single file, ensuring destination directory exists
safe_copy_file() {
    local src_file="$1"
    local dest_file="$2"

    if [ ! -f "$src_file" ]; then
        uv run tools/ask.py -p -c yellow "Warning: Source file '$src_file' not found. Skipping copy."
        return 0
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

if [ ! -d "$FILESRV_DEST_BASE_DIR" ]; then
    uv run tools/ask.py -p -c red "Error: Fileserver directory not found: $FILESRV_DEST_BASE_DIR. Stopping."
    exit 1
fi
if [ ! -d "$FILESRV_PAT_DIR" ]; then
    uv run tools/ask.py -p -c red "Error: Fileserver directory not found: $FILESRV_PAT_DIR. Stopping."
    exit 1
fi

uv run tools/ask.py -p "--- Processing CSV files ---"
cd "$ANKI_CSVS_SRC_DIR" || { uv run tools/ask.py -p -c red "Error: Could not cd to $ANKI_CSVS_SRC_DIR. Exiting."; exit 1; }

safe_copy_file "anki_patimokkha.csv" "$FILESRV_DEST_BASE_DIR/Pātimokkha Word By Word/patimokkha-word-by-word.csv" || true
safe_copy_file "anki_patimokkha.csv" "$TEMP_PUSH_DEST_DIR/patimokkha-word-by-word.csv" || true
safe_copy_file "anki_dps.csv" "$FILESRV_DEST_BASE_DIR/Пали Словарь Анки/ru-pali-vocab.csv" || true
safe_copy_file "anki_dps.csv" "$TEMP_PUSH_DEST_DIR/ru-pali-vocab.csv" || true
safe_copy_file "anki_sbs.csv" "$FILESRV_DEST_BASE_DIR/SBS Pāli-English Vocab/sbs-pd.csv" || true
safe_copy_file "anki_sbs.csv" "$TEMP_PUSH_DEST_DIR/sbs-pd.csv" || true
safe_copy_file "anki_dhp.csv" "$FILESRV_DEST_BASE_DIR/DHP Vocab/dhp-vocab.csv" || true
safe_copy_file "anki_dhp.csv" "$TEMP_PUSH_DEST_DIR/dhp-vocab.csv" || true
safe_copy_file "anki_parittas.csv" "$FILESRV_DEST_BASE_DIR/Parittas/parittas.csv" || true
safe_copy_file "anki_parittas.csv" "$TEMP_PUSH_DEST_DIR/parittas.csv" || true
safe_copy_file "anki_vibhanga.csv" "$FILESRV_DEST_BASE_DIR/Vibhanga/vibhanga.csv" || true
safe_copy_file "anki_vibhanga.csv" "$TEMP_PUSH_DEST_DIR/vibhanga.csv" || true
safe_copy_file "sbs_rus.csv" "$TEMP_PUSH_DEST_DIR/sbs-rus.csv" || true

uv run tools/ask.py -p "--- Processing APKG files ---"
cd "$ANKI_DECKS_DIR" || { uv run tools/ask.py -p -c red "Error: Could not cd to $ANKI_DECKS_DIR. Exiting."; exit 1; }

safe_copy_file "pali_patimokkha_word_by_word.apkg" "$FILESRV_DEST_BASE_DIR/Pātimokkha Word By Word/patimokkha-word-by-word.apkg" || true
safe_copy_file "pali_patimokkha_word_by_word.apkg" "$TEMP_PUSH_DEST_DIR/patimokkha-word-by-word.apkg" || true
safe_copy_file "/Users/deva/Documents/sasanarakkha/study-tools/temp/patimokkha.xlsx" "$FILESRV_PAT_DIR/Pātimokkha Word by Word.xlsx" || true
safe_copy_file "pali_slovar.apkg" "$FILESRV_DEST_BASE_DIR/Пали Словарь Анки/ru-pali-vocab.apkg" || true
safe_copy_file "pali_slovar.apkg" "$TEMP_PUSH_DEST_DIR/ru-pali-vocab.apkg" || true
safe_copy_file "sbs_pali_english_vocab.apkg" "$FILESRV_DEST_BASE_DIR/SBS Pāli-English Vocab/sbs-pali-english-vocab.apkg" || true
safe_copy_file "sbs_pali_english_vocab.apkg" "$TEMP_PUSH_DEST_DIR/sbs-pali-english-vocab.apkg" || true
safe_copy_file "pali_dhp_vocab.apkg" "$FILESRV_DEST_BASE_DIR/DHP vocab/dhp-vocab.apkg" || true
safe_copy_file "pali_dhp_vocab.apkg" "$TEMP_PUSH_DEST_DIR/dhp-vocab.apkg" || true
safe_copy_file "pali_parittas.apkg" "$FILESRV_DEST_BASE_DIR/Parittas/parittas.apkg" || true
safe_copy_file "pali_parittas.apkg" "$TEMP_PUSH_DEST_DIR/parittas.apkg" || true
safe_copy_file "Pali Patimokkha Memorizing.apkg" "$FILESRV_DEST_BASE_DIR/Pātimokkha Learning/pātimokkha learning.apkg" || true
safe_copy_file "Pali Patimokkha Memorizing.apkg" "$TEMP_PUSH_DEST_DIR/patimokkha-learning.apkg" || true
safe_copy_file "pali_bhikkhu_vibhanga.apkg" "$FILESRV_DEST_BASE_DIR/Vibhanga/vibhanga.apkg" || true
safe_copy_file "pali_bhikkhu_vibhanga.apkg" "$TEMP_PUSH_DEST_DIR/vibhanga.apkg" || true

if [ ${#FAILURES[@]} -eq 0 ]; then
    uv run tools/ask.py -p -c green "All files copied successfully."
else
    uv run tools/ask.py -p -c red "The following copies failed:"
    for f in "${FAILURES[@]}"; do
        uv run tools/ask.py -p -c red "  - $f"
    done
fi
