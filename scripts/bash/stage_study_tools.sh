#!/bin/bash

# Stage generated Anki files to temp/study_tools_release/ with release-ready names.

set -u
set -o pipefail

ANKI_CSVS="temp/anki_csvs"
PALI_CLASS_CSVS="temp/anki_csvs/pali_class"
ANKI_DECKS="temp/anki_decks"
DEST="temp/study_tools_release"

mkdir -p "$DEST"

safe_copy_file() {
    local src="$1"
    local dest="$2"
    if [ ! -f "$src" ]; then
        echo "Warning: $src not found, skipping."
        return 0
    fi
    cp -f "$src" "$dest"
    echo "Copied $src → $dest"
}

# CSVs from anki_csvs/
safe_copy_file "$ANKI_CSVS/anki_patimokkha.csv"  "$DEST/patimokkha-word-by-word.csv"
safe_copy_file "$ANKI_CSVS/anki_dps.csv"          "$DEST/ru-pali-vocab.csv"
safe_copy_file "$ANKI_CSVS/anki_sbs.csv"          "$DEST/sbs-pd.csv"
safe_copy_file "$ANKI_CSVS/anki_dhp.csv"          "$DEST/dhp-vocab.csv"
safe_copy_file "$ANKI_CSVS/anki_parittas.csv"     "$DEST/parittas.csv"
safe_copy_file "$ANKI_CSVS/anki_vibhanga.csv"     "$DEST/vibhanga.csv"
safe_copy_file "$ANKI_CSVS/sbs_rus.csv"           "$DEST/sbs-rus.csv"

# CSVs from pali_class/
safe_copy_file "$PALI_CLASS_CSVS/class_all.csv"       "$DEST/vocab-pali-class.csv"
safe_copy_file "$PALI_CLASS_CSVS/phonetic_class.csv"  "$DEST/phonetic-pali-class.csv"
safe_copy_file "$PALI_CLASS_CSVS/roots_class.csv"     "$DEST/roots-pali-class.csv"
safe_copy_file "$PALI_CLASS_CSVS/suttas_class.csv"    "$DEST/suttas-advanced-pali-class.csv"
safe_copy_file "$PALI_CLASS_CSVS/common_roots.csv"    "$DEST/common-roots.csv"
safe_copy_file "$PALI_CLASS_CSVS/ru_common_roots.csv" "$DEST/ru_common_roots.csv"

# Grammar CSVs from pali_class/grammar/
safe_copy_file "$PALI_CLASS_CSVS/grammar/cl_sum_abbr.csv"    "$DEST/grammar-pali-class-abbr.csv"
safe_copy_file "$PALI_CLASS_CSVS/grammar/cl_sum_gramm.csv"   "$DEST/grammar-pali-class-gramm.csv"
safe_copy_file "$PALI_CLASS_CSVS/grammar/cl_sum_sandhi.csv"  "$DEST/grammar-pali-class-sandhi.csv"
safe_copy_file "$PALI_CLASS_CSVS/grammar/ru_cl_sum_gramm.csv" "$DEST/ru_cl_sum_gramm.csv"

# APKGs from anki_decks/
safe_copy_file "$ANKI_DECKS/pali_patimokkha_word_by_word.apkg"  "$DEST/patimokkha-word-by-word.apkg"
safe_copy_file "$ANKI_DECKS/pali_slovar.apkg"                    "$DEST/ru-pali-vocab.apkg"
safe_copy_file "$ANKI_DECKS/sbs_pali_english_vocab.apkg"        "$DEST/sbs-pali-english-vocab.apkg"
safe_copy_file "$ANKI_DECKS/pali_dhp_vocab.apkg"                "$DEST/dhp-vocab.apkg"
safe_copy_file "$ANKI_DECKS/pali_parittas.apkg"                 "$DEST/parittas.apkg"
safe_copy_file "$ANKI_DECKS/pali_bhikkhu_vibhanga.apkg"         "$DEST/vibhanga.apkg"
safe_copy_file "$ANKI_DECKS/grammar_pali_class.apkg"            "$DEST/grammar-pali-class.apkg"
safe_copy_file "$ANKI_DECKS/phonetic_changes_pali_class.apkg"   "$DEST/phonetic-pali-class.apkg"
safe_copy_file "$ANKI_DECKS/roots_pali_class.apkg"              "$DEST/roots-pali-class.apkg"
safe_copy_file "$ANKI_DECKS/suttas_advanced_pali_class.apkg"    "$DEST/suttas-advanced-pali-class.apkg"
safe_copy_file "$ANKI_DECKS/vocab_pali_class.apkg"              "$DEST/vocab-pali-class.apkg"
safe_copy_file "$ANKI_DECKS/common_roots.apkg"                  "$DEST/common-roots.apkg"

echo "Staging complete: $DEST"
