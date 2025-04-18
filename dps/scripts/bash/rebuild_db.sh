#!/usr/bin/env bash

# build dpd.db from scratch or update existing one using backup_tsv with additions and corrections and making goldendict 

set -e
test -e dpd.db || touch dpd.db

# git fetch

git checkout sbs-ru

# git checkout origin/main -- db/backup_tsv/dpd_headwords.tsv

# git checkout origin/main -- db/backup_tsv/dpd_roots.tsv

while true; do
    echo -ne "\033[1;36m Backup Ru and SBS tables and copy them to db/backup_tsv?\033[0m"
    read yn
    case $yn in
        [Yy]* )
            dps/scripts/export_from_db/backup_all_dps.py
            FILENAMES=("sbs.tsv" "russian.tsv" "ru_roots.tsv")
            for file in "${FILENAMES[@]}"; do
                cp -rf ./dps/backup/$file ./db/backup_tsv/$file
            done
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -ne "\033[1;36m Copy all from dps_backup to db/backup_tsv?\033[0m"
    read yn
    case $yn in
        [Yy]* )
            FILENAMES=("dpd_headwords.tsv" "dpd_roots.tsv" "sbs.tsv" "russian.tsv" "ru_roots.tsv")
            for file in "${FILENAMES[@]}"; do
                cp -rf ./dps/backup/$file ./db/backup_tsv/$file
            done
            break;;
        * )
            break;;
    esac
done

while true; do
    echo -ne "\033[1;36m Rebuild db from db/backup_tsv?\033[0m"
    read yn
    case $yn in
        [Yy]* )
            # build dpd.db from scratch using backup_tsv
            scripts/build/db_rebuild_from_tsv.py
            db/bold_definitions/update_bold_definitions_db.py
            dps/scripts/change_in_db/dps_add_additions_to_db.py
            scripts/bash/generate_components.sh
            # After setting db_rebuild to "yes" in db_rebuild_from_tsv.py, we change it back after the bash is done.
            python -c "from tools.configger import config_update; config_update('regenerate', 'db_rebuild', 'no')"
            dps/scripts/other/add_combined_view.py
            dps/scripts/change_in_db/apply_all_corrections.py
            exporter/goldendict/main.py
            git checkout -- pyproject.toml
            git checkout -- db/backup_tsv/dpd_headwords.tsv
            git checkout -- db/sanskrit/root_families_sanskrit.tsv
            git checkout -- exporter/goldendict/javascript/family_compound_json.js
            git checkout -- exporter/goldendict/javascript/family_idiom_json.js
            git checkout -- exporter/goldendict/javascript/family_root_json.js
            git checkout -- exporter/goldendict/javascript/family_set_json.js
            git checkout -- exporter/goldendict/javascript/family_word_json.js
            git checkout -- shared_data/changed_templates
            break;;
        * )
            break;;
    esac
done


# while true; do
#     echo -ne "\033[1;36m Make dpd?\033[0m"
#     read yn
#     case $yn in
#         [Yy]* )
#             exporter/goldendict/main.py
#             break;;
#         * )
#             break;;
#     esac
# done
