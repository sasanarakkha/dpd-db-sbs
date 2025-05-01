#!/usr/bin/env bash

# update data in dpd.db from from backup_tsv with additions and corrections

set -e

git fetch

git checkout origin/main -- db/backup_tsv/dpd_headwords.tsv

git checkout origin/main -- db/backup_tsv/dpd_roots.tsv

scripts/backup_all_dps.py

# Define filenames
FILENAMES=("sbs.tsv" "russian.tsv" "ru_roots.tsv")

# Copy files from db/backup_sbs_ru/ to db/backup_tsv/
for file in "${FILENAMES[@]}"; do
    cp -rf ./db/backup_sbs_ru/$file ./db/backup_tsv/$file
done

# scripts/move_new_words.py

scripts/db_update_from_tsv.py

python -c "from gui.corrections_check_feedback import apply_all_suggestions; apply_all_suggestions()"

mkdpd.sh

git checkout -- pyproject.toml

git checkout -- db/backup_tsv/dpd_headwords.tsv
