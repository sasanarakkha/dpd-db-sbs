#!/bin/bash

# This script is used to check for new words in the database and compare them with the existing ones.
# It will also prompt the user to apply changes and backup the database.q

# --- Cross-platform spreadsheet viewer function ---
open_spreadsheet() {
    local file="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS: Try 'open' (default for .tsv files)
        open "$file" || echo "Could not open $file on macOS (no default app?)"
    else
        # Linux: Try LibreOffice, fallback to xdg-open
        if command -v libreoffice >/dev/null; then
            libreoffice "$file"
        else
            xdg-open "$file" || echo "Could not open $file (install LibreOffice?)"
        fi
    fi
}

# --- Backup prompt ---
while true; do
    echo -ne "\033[1;36mBackup all? (y/n): \033[0m"
    read yn
    case $yn in
        [Yy]* )
            scripts/backup/backup_all.py
            break;;
        * )
            break;;
    esac
done

# --- Colors ---
bold=$(tput bold)
yellow=$(tput setaf 3)
green=$(tput setaf 2)
red=$(tput setaf 1)
reset=$(tput sgr0)

echo "${bold}${yellow}Filter the list of words${reset}"

# --- Open files with cross-platform method ---
open_spreadsheet "shared_data/major_change_meaning_history.tsv"
scripts/work_with_csv/compare_changed_id.py

open_spreadsheet "db/backup_tsv/for_compare/added_another_meaning.tsv"
open_spreadsheet "db/backup_tsv/for_compare/changed_notes.tsv"

# --- User confirmation ---
read -p "${bold}${yellow}Did you apply all changes? (y/n): ${reset}" confirmation
if [ "$confirmation" == "y" ]; then
    cp -rf db/backup_tsv/dpd_headwords.tsv db/backup_tsv/for_compare/dpd_headwords.tsv
    echo "${bold}${green}The job is done${reset}"
else
    echo "${bold}${red}No changes applied. Exiting.${reset}"
fi

echo "${bold}${red}Please check out latest newly added words vib/sutta${reset}"
scripts/backup/backup_ru_sbs.py
scripts/work_with_csv/replace_new_id.py