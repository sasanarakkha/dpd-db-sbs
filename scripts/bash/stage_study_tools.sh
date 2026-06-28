#!/bin/bash
# Stage generated Anki files to temp/study_tools_release/ with release-ready names.

set -u
set -o pipefail

DEST="temp/study_tools_release"
mkdir -p "$DEST"

# Source→destination mapping as colon-delimited pairs
mappings=(
    # CSVs from anki_csvs/
    "temp/anki_csvs/anki_patimokkha.csv:patimokkha-word-by-word.csv"
    "temp/anki_csvs/anki_dps.csv:ru-pali-vocab.csv"
    "temp/anki_csvs/anki_sbs.csv:sbs-pd.csv"
    "temp/anki_csvs/anki_dhp.csv:dhp-vocab.csv"
    "temp/anki_csvs/anki_parittas.csv:parittas.csv"
    "temp/anki_csvs/anki_vibhanga.csv:vibhanga.csv"
    "temp/anki_csvs/sbs_rus.csv:sbs-rus.csv"
    # CSVs from pali_class/
    "temp/anki_csvs/pali_class/class_all.csv:vocab-pali-class.csv"
    "temp/anki_csvs/pali_class/phonetic_class.csv:phonetic-pali-class.csv"
    "temp/anki_csvs/pali_class/roots_class.csv:roots-pali-class.csv"
    "temp/anki_csvs/pali_class/suttas_class.csv:suttas-advanced-pali-class.csv"
    "temp/anki_csvs/pali_class/common_roots.csv:common-roots.csv"
    "temp/anki_csvs/pali_class/ru_common_roots.csv:ru_common_roots.csv"
    # Grammar CSVs from pali_class/grammar/
    "temp/anki_csvs/pali_class/grammar/cl_sum_abbr.csv:grammar-pali-class-abbr.csv"
    "temp/anki_csvs/pali_class/grammar/cl_sum_gramm.csv:grammar-pali-class-gramm.csv"
    "temp/anki_csvs/pali_class/grammar/cl_sum_sandhi.csv:grammar-pali-class-sandhi.csv"
    "temp/anki_csvs/pali_class/grammar/ru_cl_sum_gramm.csv:ru_cl_sum_gramm.csv"
    # APKGs from anki_decks/
    "temp/anki_decks/pali_patimokkha_word_by_word.apkg:patimokkha-word-by-word.apkg"
    "temp/anki_decks/pali_slovar.apkg:ru-pali-vocab.apkg"
    "temp/anki_decks/sbs_pali_english_vocab.apkg:sbs-pali-english-vocab.apkg"
    "temp/anki_decks/pali_dhp_vocab.apkg:dhp-vocab.apkg"
    "temp/anki_decks/pali_parittas.apkg:parittas.apkg"
    "temp/anki_decks/pali_bhikkhu_vibhanga.apkg:vibhanga.apkg"
    "temp/anki_decks/grammar_pali_class.apkg:grammar-pali-class.apkg"
    "temp/anki_decks/phonetic_changes_pali_class.apkg:phonetic-pali-class.apkg"
    "temp/anki_decks/roots_pali_class.apkg:roots-pali-class.apkg"
    "temp/anki_decks/suttas_advanced_pali_class.apkg:suttas-advanced-pali-class.apkg"
    "temp/anki_decks/vocab_pali_class.apkg:vocab-pali-class.apkg"
    "temp/anki_decks/common_roots.apkg:common-roots.apkg"
)

for mapping in "${mappings[@]}"; do
    src="${mapping%%:*}"
    dest="$DEST/${mapping##*:}"
    if [ ! -f "$src" ]; then
        uv run tools/ask.py --print --color yellow "Warning: $src not found, skipping."
        continue
    fi
    cp -f "$src" "$dest"
done

uv run tools/ask.py --print --color green "Staging complete: $DEST"
