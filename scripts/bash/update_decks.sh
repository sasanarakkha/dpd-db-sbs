#!/bin/bash

# all for update of sbs-study-tools (https://sasanarakkha.github.io/study-tools/)

echo -e "\033[1;33m We are going to make various csv and push decks on the server. \033[0m"

cd "$HOME/Documents/dpd-db/"


while true; do
    echo -ne "\033[1;34m !IMPORTANT! did you apply all suggestions from feedback form?! \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            break;;
        * )
            break;;
    esac
done


while true; do
    echo -ne "\033[1;34m need to make latest csv for anki? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            uv run python db_tests/sbs_consistency_tests.py
            uv run python scripts/export/anki_csv.py
            break;;
        * )
            break;;
    esac
done


while true; do
    echo -ne "\033[1;34m need to push vocab for classes? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m pushing vocab for classes...\033[0m"
            uv run python scripts/change_in_db/class_relation.py
            uv run python scripts/export/vocab_abbrev_pali_course.py
            cd "$HOME/Documents/dpd-pali-courses"
            git-push
            break;;
        * )
            break;;
    esac
done

# grammar.xlsx - https://docs.google.com/spreadsheets/d/1KV5LmebIQpNyNKl03Pmo_Ti-LNW3IYWB6uc7OfGRGPU/

while true; do
    echo -ne "\033[1;34m need to make updated grammar.csv? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m generating grammar.csv...\033[0m"
            uv run bash scripts/bash/download_grammar.sh
            uv run python scripts/work_with_csv/anki_class_grammar.py
            break;;
        * )
            break;;
    esac
done


# Pātimokkha.xlsx - https://docs.google.com/spreadsheets/d/1rS-IlX4DvKmnBO58KON37eVnOZqwfkG-ot-zIjCuzH4/

while true; do
    # echo -e "\033[1;36m please download the latest Pātimokkha XLSX! \033[0m"
    echo -ne "\033[1;34m need to generate patimokkha.csv? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m generating patimokkha.csv...\033[0m"
            cd "$HOME/Documents/sasanarakkha/study-tools/"
            uv run bash scripts/download_patimokkha.sh
            cd "$HOME/Documents/dpd-db/"
            uv run python scripts/work_with_csv/xlsx2csv.py "$HOME/Documents/sasanarakkha/study-tools/temp/patimokkha.xlsx" "temp/patimokkha_word_by_word.csv" "analysis"
            uv run python scripts/work_with_csv/pat_for_anki.py
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -e "\033[1;36m please close Anki Desktop before updating! \033[0m"
    echo -ne "\033[1;34m need to update SBS Anki collection? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m updating SBS Anki collection...\033[0m"
            uv run python scripts/export/sbs_anki_updater.py
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -e "\033[1;36m open Anki Desktop to review the changes. \033[0m"
    echo -ne "\033[1;34m satisfied? --!close Anki before!--  (N = revert) (Y = save apkg) \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Nn]* )
            echo -e "\033[1;33m reverting to latest backup...\033[0m"
            uv run python scripts/export/sbs_anki_revert.py
            echo -e "\033[1;31m Reverted. Make corrections and re-run update_decks.sh.\033[0m"
            exit 0;;
        [Yy]* )
            echo -e "\033[1;33m saving apkg...\033[0m"
            uv run python scripts/export/sbs_anki_apkg.py
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -e "\033[1;36m please save all class anki decks! \033[0m"
    echo -ne "\033[1;34m need to move all classes? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m moving all classes...\033[0m"
            uv run bash scripts/bash/move_class.sh
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -ne "\033[1;34m need to update offline materials for classes? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m downloading and copying class materials...\033[0m"
            uv run bash scripts/bash/download_pali_classes.sh
            uv run python scripts/moving/unzip_classes_to_filesrv.py
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -e "\033[1;36m please save all other anki decks! \033[0m"
    echo -ne "\033[1;34m need to move all other decks? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m moving all other decks...\033[0m"
            uv run bash scripts/bash/move_decks.sh
            break;;
        * )
            break;;
    esac
done

STUDY_TOOLS_DIR="$HOME/Documents/sasanarakkha/study-tools"

while true; do
    echo -ne "\033[1;34m need to push individually on GitHub? \033[0m"
    read -n 1 -s answer
    echo
    if [[ $answer == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $answer in
        [Yy]* )
            while true; do
                echo -e "\033[1;33m Available assets:\033[0m"
                bash "$STUDY_TOOLS_DIR/scripts/upload_asset.sh"
                echo -ne "\033[1;34m Enter filename to upload (or press Enter to finish): \033[0m"
                read asset_name
                if [[ -z "$asset_name" ]]; then
                    break
                fi
                bash "$STUDY_TOOLS_DIR/scripts/upload_asset.sh" "$asset_name"
                echo
            done
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -ne "\033[1;34m need to push all on GitHub? \033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m pushing all...\033[0m"
            bash "$STUDY_TOOLS_DIR/scripts/upload.sh"
            break;;
        *  )
            break;;
    esac
done


echo -e "\033[1;32m what have to be done has been done! \033[0m"

echo -e "\033[1;32m ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ \033[0m"
