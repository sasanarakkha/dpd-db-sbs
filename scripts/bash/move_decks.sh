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

# Helper function to copy a single file, ensuring destination directory exists
safe_copy_file() {
    local src_file="$1"
    local dest_file="$2"
    local cp_options="${3:--f}" # Default to -f, can pass e.g. "-X -f"

    if [ ! -f "$src_file" ]; then
        echo "Warning: Source file '$src_file' not found. Skipping copy."
        return 0
    fi
    
    local dest_dir
    dest_dir=$(dirname "$dest_file")
    if ! mkdir -p "$dest_dir"; then
        echo "Error: Could not create destination directory '$dest_dir'. Skipping copy of '$src_file'."
        return 1
    fi

    # Switched to rsync for potentially better handling of metadata with network shares on macOS.
    # The --times flag preserves modification times.
    # --no-perms, --no-owner, --no-group prevent rsync from trying to set these on the destination,
    # which can cause "Operation not permitted" errors on some network shares.
    if rsync --times --no-perms --no-owner --no-group "$src_file" "$dest_file"; then
        echo "Successfully copied '$src_file' to '$dest_file'."
    else
        echo "Error: Failed to copy '$src_file' to '$dest_file'. Please check permissions and paths."
        return 1
    fi
}

echo "--- Processing CSV files ---"
cd "$ANKI_CSVS_SRC_DIR" || { echo "Error: Could not cd to $ANKI_CSVS_SRC_DIR. Exiting."; exit 1; }

safe_copy_file "anki_patimokkha.csv" "$FILESRV_DEST_BASE_DIR/Pātimokkha Word By Word/patimokkha-word-by-word.csv" "-X -f"
safe_copy_file "anki_patimokkha.csv" "$TEMP_PUSH_DEST_DIR/patimokkha-word-by-word.csv" "-X -f"
safe_copy_file "anki_dps.csv" "$FILESRV_DEST_BASE_DIR/Пали Словарь Анки/ru-pali-vocab.csv" "-X -f"
safe_copy_file "anki_dps.csv" "$TEMP_PUSH_DEST_DIR/ru-pali-vocab.csv" "-X -f"
safe_copy_file "anki_sbs.csv" "$FILESRV_DEST_BASE_DIR/SBS Pāli-English Vocab/sbs-pd.csv" "-X -f"
safe_copy_file "anki_sbs.csv" "$TEMP_PUSH_DEST_DIR/sbs-pd.csv" "-X -f"
safe_copy_file "anki_dhp.csv" "$FILESRV_DEST_BASE_DIR/DHP Vocab/dhp-vocab.csv" "-X -f"
safe_copy_file "anki_dhp.csv" "$TEMP_PUSH_DEST_DIR/dhp-vocab.csv" "-X -f"
safe_copy_file "anki_parittas.csv" "$FILESRV_DEST_BASE_DIR/Parittas/parittas.csv" "-X -f"
safe_copy_file "anki_parittas.csv" "$TEMP_PUSH_DEST_DIR/parittas.csv" "-X -f"
safe_copy_file "anki_vibhanga.csv" "$FILESRV_DEST_BASE_DIR/Vibhanga/vibhanga.csv" "-X -f"
safe_copy_file "anki_vibhanga.csv" "$TEMP_PUSH_DEST_DIR/vibhanga.csv" "-X -f"
safe_copy_file "sbs_rus.csv" "$TEMP_PUSH_DEST_DIR/sbs-rus.csv" "-X -f"

echo "CSV processing - done"

echo "--- Processing APKG files ---"
cd "$ANKI_DECKS_DIR" || { echo "Error: Could not cd to $ANKI_DECKS_DIR. Exiting."; exit 1; }

safe_copy_file "pali_patimokkha_word_by_word.apkg" "$FILESRV_DEST_BASE_DIR/Pātimokkha Word By Word/patimokkha-word-by-word.apkg" "-X -f"
safe_copy_file "pali_patimokkha_word_by_word.apkg" "$TEMP_PUSH_DEST_DIR/patimokkha-word-by-word.apkg"
safe_copy_file "/Users/deva/Documents/sasanarakkha/study-tools/temp/patimokkha.xlsx" "$FILESRV_PAT_DIR/Pātimokkha Word by Word.xlsx" "-X -f"
safe_copy_file "pali_slovar.apkg" "$FILESRV_DEST_BASE_DIR/Пали Словарь Анки/ru-pali-vocab.apkg" "-X -f"
safe_copy_file "pali_slovar.apkg" "$TEMP_PUSH_DEST_DIR/ru-pali-vocab.apkg" "-X -f"
safe_copy_file "sbs_pali_english_vocab.apkg" "$FILESRV_DEST_BASE_DIR/SBS Pāli-English Vocab/sbs-pali-english-vocab.apkg" "-X -f"
safe_copy_file "sbs_pali_english_vocab.apkg" "$TEMP_PUSH_DEST_DIR/sbs-pali-english-vocab.apkg" "-X -f"
safe_copy_file "pali_dhp_vocab.apkg" "$FILESRV_DEST_BASE_DIR/DHP vocab/dhp-vocab.apkg" "-X -f"
safe_copy_file "pali_dhp_vocab.apkg" "$TEMP_PUSH_DEST_DIR/dhp-vocab.apkg" "-X -f"
safe_copy_file "pali_parittas.apkg" "$FILESRV_DEST_BASE_DIR/Parittas/parittas.apkg" "-X -f"
safe_copy_file "pali_parittas.apkg" "$TEMP_PUSH_DEST_DIR/parittas.apkg" "-X -f"
safe_copy_file "Pali Patimokkha Memorizing.apkg" "$FILESRV_DEST_BASE_DIR/Pātimokkha Learning/pātimokkha learning.apkg" "-X -f"
safe_copy_file "Pali Patimokkha Memorizing.apkg" "$TEMP_PUSH_DEST_DIR/patimokkha-learning.apkg" "-X -f"
safe_copy_file "pali_bhikkhu_vibhanga.apkg" "$FILESRV_DEST_BASE_DIR/Vibhanga/vibhanga.apkg" "-X -f"
safe_copy_file "pali_bhikkhu_vibhanga.apkg" "$TEMP_PUSH_DEST_DIR/vibhanga.apkg" "-X -f"

# safe_copy_file "Ñāṇatiloka Dictionary.apkg" "$FILESRV_DEST_BASE_DIR/Ñāṇatiloka Dictionary/nanatiloka-dictionary.apkg" "-X -f"
# safe_copy_file "Ñāṇatiloka Dictionary.apkg" "$TEMP_PUSH_DEST_DIR/nanatiloka-dictionary.apkg" "-X -f"
# safe_copy_file "Sutta Q&A.apkg" "$FILESRV_DEST_BASE_DIR/Sutta Q&A/sutta-q-a.apkg" "-X -f"
# safe_copy_file "Sutta Q&A.apkg" "$TEMP_PUSH_DEST_DIR/sutta-q-a.apkg" "-X -f"

# safe_copy_file "$FILESRV_DEST_BASE_DIR/Reading common pali phrases/reading-common-pali-phrases.apkg" "$TEMP_PUSH_DEST_DIR/reading-common-pali-phrases.apkg" "-X -f"
# safe_copy_file "$FILESRV_DEST_BASE_DIR/Reading common pali phrases/reading-common-pali-phrases.csv" "$TEMP_PUSH_DEST_DIR/reading-common-pali-phrases.csv" "-X -f"

echo "APKG processing - done"

echo "Anki decks and csv of SBS-PED ; PAT ; DHP ; DPS ; Pāli Parittas moved for share"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "the job is done"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "--- Script finished ---"
