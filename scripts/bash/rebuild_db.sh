#!/bin/bash

set -e
test -e dpd.db || touch dpd.db

git checkout sbs-ru

answer=$(uv run tools/ask.py -c cyan "Backup Ru and SBS tables? [y/n] ")
if [ "$answer" = "y" ]; then
    db/backup_tsv/backup_dps.py
fi

answer=$(uv run tools/ask.py -c cyan "Replace id in DPS backup files from additions_added.json? [y/n] ")
if [ "$answer" = "y" ]; then
    scripts/work_with_csv/additions_processor.py
fi

answer=$(uv run tools/ask.py -c cyan "Rebuild db from db/backup_tsv? [y/n] ")
if [ "$answer" = "y" ]; then
    scripts/build/db_rebuild_from_tsv.py
    scripts/change_in_db/apply_all_additions.py
    scripts/build/db_rebuild_from_tsv_dps.py
    db/bold_definitions/update_bold_definitions_db.py
    scripts/bash/generate_components.sh
    db/rpd/rpd_to_lookup.py
    db/tpd/tpd_to_lookup.py
    uv run python3 -c "from tools.configger import config_update; config_update('regenerate', 'db_rebuild', 'no')"
    scripts/other/add_combined_view.py
    scripts/change_in_db/apply_all_corrections.py
    scripts/change_in_db/update_yojana_km.py
    exporter/goldendict/main_sbs.py
fi
