#!/bin/bash

# This script is used to make the Patimokkha csv file for Anki.

echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

uv run python scripts/work_with_csv/xlsx2csv.py "$HOME/Downloads/Pātimokkha Word by Word.xlsx" "temp/patimokkha_word_by_word.csv" "analysis"

uv run python scripts/work_with_csv/pat_for_anki.py

echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"

uv run python scripts/other/patimokkha_dict.py

cd "$HOME/Documents/sasanarakkha/study-tools"

git-push

