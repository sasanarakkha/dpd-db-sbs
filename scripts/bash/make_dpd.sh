#!/bin/bash

# This script builds dpd.db from scratch and export all dictionaries.

set -e

# Store the initial option value
CHOSEN_OPTION=""
git checkout sbs-ru

while true; do
    echo -ne "\033[1;36m Choose config: (1) DPD-SBS for the server; (2) DPD-SBS-RU for local use; (Enter) custom config\033[0m"
    read option
    case $option in
        [1]* )
            uv run python scripts/rus_exporter/config_github_server_dpd_sbs.py
            CHOSEN_OPTION="1"
            break;;
        [2]* )
            uv run python scripts/rus_exporter/config_github_local_dpd_sbs.py
            break;;
        * )
            break;;
    esac
done

echo "Config:"
python -c "from tools.configger import print_config_settings; print_config_settings(['dictionary', 'goldendict', 'exporter'])"

while true; do
    echo -ne "\033[1;36m generate_components?\033[0m"
    read yn
    case $yn in
        [Yy]* )
            uv run bash scripts/bash/generate_components.sh
            break;;
        * )
            break;;
    esac
done

# uv run python exporter/grammar_dict/grammar_dict.py

uv run python exporter/goldendict/main_sbs.py
# uv run python exporter/deconstructor/deconstructor_exporter.py

uv run python exporter/tpr/tpr_exporter_ru.py
# uv run python exporter/kindle/kindle_exporter.py

uv run python scripts/build/zip_goldendict_mdict.py

uv run python scripts/moving/distribute.py move_mdict

# If option 1 was selected, copy DPD-SBS
if [ "$CHOSEN_OPTION" == "1" ]; then
    uv run python scripts/moving/distribute.py copy_dpdsbs_from_share2sbs
fi

# If option 1 was not selected, return settings back to default
if [ "$CHOSEN_OPTION" != "1" ]; then
    uv run python scripts/rus_exporter/config_github_local_dpd_sbs.py
fi
