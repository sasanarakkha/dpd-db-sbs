#!/usr/bin/env bash

# making backup of db if it is first time today and open GUI

# Directory where backups are stored
BACKUP_DIR="db/backup_sbs_ru/"

# Get today's date
TODAY=$(date "+%Y-%m-%d")

# Check the modification date of a file (for example, dpd_headwords.tsv)
FILE_DATE=$(stat -c %y "${BACKUP_DIR}dpd_headwords.tsv" | cut -d' ' -f1)

# Check if backups for today exist in db/backup_tsv/
if [[ "$FILE_DATE" == "$TODAY" ]]; then
    echo "Backups for today already exist."
else
    scripts/export/backup_all_dps.py
fi

# Run the GUI script
gui/gui_main.py
