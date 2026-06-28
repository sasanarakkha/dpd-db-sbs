#!/bin/bash

# Orchestrate the full SBS Anki deck update workflow.

PROJECT_DIR="$HOME/Documents/dpd-db"

cd "$PROJECT_DIR"

uv run python "$PROJECT_DIR/tools/ask.py" "!IMPORTANT! did you apply all suggestions from feedback form?!" > /dev/null || exit 1


response=$(uv run python "$PROJECT_DIR/tools/ask.py" "need to make latest csv for anki?") || exit 1
if [[ $response == "y" ]]; then
    uv run python scripts/change_in_db/source_cleanup.py
    uv run python scripts/change_in_db/example_cleanup.py
    uv run python scripts/change_in_db/update_sbs_chants_in_db.py
    if ! uv run python db_tests/sbs_consistency_tests.py; then
        uv run "$PROJECT_DIR/tools/ask.py" --print -c red "SBS consistency tests FAILED. Aborting before anki_csv.py."
        exit 1
    fi
    uv run python scripts/export/anki_csv.py
fi


response=$(uv run python "$PROJECT_DIR/tools/ask.py" "need to push vocab for classes?") || exit 1
if [[ $response == "y" ]]; then
    uv run python scripts/change_in_db/class_relation.py
    uv run python scripts/export/vocab_abbrev_pali_course.py
    bash "$PROJECT_DIR/scripts/bash/pali_vocab_push.sh" || exit 1
    cd "$PROJECT_DIR"
fi

# grammar.xlsx - https://docs.google.com/spreadsheets/d/1KV5LmebIQpNyNKl03Pmo_Ti-LNW3IYWB6uc7OfGRGPU/

response=$(uv run python "$PROJECT_DIR/tools/ask.py" "need to make updated grammar.csv?") || exit 1
if [[ $response == "y" ]]; then
    uv run bash scripts/bash/download_grammar.sh
    uv run python scripts/work_with_csv/anki_class_grammar.py
fi


# Pātimokkha.xlsx - https://docs.google.com/spreadsheets/d/1rS-IlX4DvKmnBO58KON37eVnOZqwfkG-ot-zIjCuzH4/

response=$(uv run python "$PROJECT_DIR/tools/ask.py" "need to generate patimokkha.csv?") || exit 1
if [[ $response == "y" ]]; then
    cd "$HOME/Documents/sasanarakkha/study-tools/"
    env -u VIRTUAL_ENV uv run bash scripts/download_patimokkha.sh
    cd "$HOME/Documents/dpd-db/"
    uv run python scripts/work_with_csv/xlsx2csv.py "$HOME/Documents/sasanarakkha/study-tools/temp/patimokkha.xlsx" "temp/patimokkha_word_by_word.csv" "analysis"
    uv run python scripts/work_with_csv/pat_for_anki.py
fi

uv run python "$PROJECT_DIR/tools/ask.py" "please close Anki Desktop before updating!" > /dev/null || exit 1
response=$(uv run python "$PROJECT_DIR/tools/ask.py" "need to update SBS Anki collection?") || exit 1
if [[ $response == "y" ]]; then
    uv run python scripts/export/sbs_anki_fields_check.py || exit 1
    uv run python scripts/export/sbs_anki_updater.py
    uv run python scripts/export/sbs_anki_templates.py
fi

uv run python "$PROJECT_DIR/tools/ask.py" "open Anki Desktop to review the changes." > /dev/null || exit 1
response=$(uv run python "$PROJECT_DIR/tools/ask.py" "satisfied? --!close Anki before!--  (N = revert) (Y = save apkg)") || exit 1
case $response in
    y)
        uv run python scripts/export/sbs_anki_apkg.py
        ;;
    n)
        uv run python scripts/export/sbs_anki_revert.py
        uv run python "$PROJECT_DIR/tools/ask.py" "Reverted. Make corrections and re-run update_decks.sh." > /dev/null || exit 1
        exit 0
        ;;
esac

response=$(uv run python "$PROJECT_DIR/tools/ask.py" "need to move all classes?") || exit 1
if [[ $response == "y" ]]; then
    uv run bash scripts/bash/move_class.sh
fi

response=$(uv run python "$PROJECT_DIR/tools/ask.py" "need to update offline materials for classes?") || exit 1
if [[ $response == "y" ]]; then
    uv run bash scripts/bash/download_pali_classes.sh
    uv run python scripts/moving/distribute.py unzip_classes_to_filesrv
fi
response=$(uv run python "$PROJECT_DIR/tools/ask.py" "need to move all other decks?") || exit 1
if [[ $response == "y" ]]; then
    uv run bash scripts/bash/move_decks.sh
fi

STUDY_TOOLS_DIR="$HOME/Documents/sasanarakkha/study-tools"

response=$(uv run python "$PROJECT_DIR/tools/ask.py" "need to push individually on GitHub?") || exit 1
if [[ $response == "y" ]]; then
    while true; do
        uv run "$PROJECT_DIR/tools/ask.py" --print "Available assets:"
        bash "$STUDY_TOOLS_DIR/scripts/upload_asset.sh"
        uv run "$PROJECT_DIR/tools/ask.py" --print "Enter filename to upload (or press Enter to finish):"
        read asset_name
        if [[ -z "$asset_name" ]]; then
            break
        fi
        bash "$STUDY_TOOLS_DIR/scripts/upload_asset.sh" "$asset_name"
    done
fi

response=$(uv run python "$PROJECT_DIR/tools/ask.py" "need to push all on GitHub?") || exit 1
if [[ $response == "y" ]]; then
    bash "$STUDY_TOOLS_DIR/scripts/upload.sh"
fi

uv run "$PROJECT_DIR/tools/ask.py" --print -c green "what have to be done has been done!"
uv run "$PROJECT_DIR/tools/ask.py" --print -c green "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
