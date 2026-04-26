#!/bin/bash

# build dpd.db from scratch or update existing one using backup_tsv with additions and corrections and making goldendict 

set -e
test -e dpd.db || touch dpd.db

# git fetch

git checkout sbs-ru

# git checkout origin/main -- db/backup_tsv/dpd_headwords.tsv

# git checkout origin/main -- db/backup_tsv/dpd_roots.tsv

while true; do
    echo -ne "\033[1;36m Backup Ru and SBS tables\033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            scripts/backup/backup_dps.py
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -ne "\033[1;36m Replace id in DPS backup files from additions_added.json?\033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            scripts/work_with_csv/additions_processor.py
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -ne "\033[1;36m Rebuild db from db/backup_tsv?\033[0m"
    read -n 1 -s yn
    echo
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            # build dpd.db from scratch using backup_tsv
            scripts/build/db_rebuild_from_tsv.py
            scripts/change_in_db/apply_all_additions.py
            scripts/build/db_rebuild_from_tsv_dps.py
            db/bold_definitions/update_bold_definitions_db.py
            scripts/bash/generate_components.sh
            db/rpd/rpd_to_lookup.py
            db/tpd/tpd_to_lookup.py
            # After setting db_rebuild to "yes" in db_rebuild_from_tsv.py, we change it back after the bash is done.
            python -c "from tools.configger import config_update; config_update('regenerate', 'db_rebuild', 'no')"
            scripts/other/add_combined_view.py
            scripts/change_in_db/apply_all_corrections.py
            exporter/goldendict/main_sbs.py
            break;;
        * )
            break;;
    esac
done


# while true; do
#     echo -ne "\033[1;36m Make dpd?\033[0m"
#     read -n 1 -s yn
#     echo
#     if [[ $yn == "q" ]]; then
#         echo -e "\n\033[1;31m Aborted by user.\033[0m"
#         exit 1
#     fi
#     case $yn in
#         [Yy]* )
#             exporter/goldendict/main.py
#             break;;
#         * )
#             break;;
#     esac
# done
