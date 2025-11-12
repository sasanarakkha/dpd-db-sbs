#!/bin/bash

# This script exports the RU DPD.

set -e

git checkout sbs-ru

while true; do
    echo -ne "\033[1;36m Choose config: (1) RUS-DPD for the server; (Esc) custom config\033[0m"
    read option
    case $option in
        [1]* )
            uv run python scripts/rus_exporter/config_github_release_dpd_rus.py
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
            uv run python scripts/build/families_to_json_ru.py
            break;;
    esac
done

echo "exporting RU DPD"

uv run python exporter/grammar_dict/grammar_dict_ru.py

uv run python exporter/goldendict/main_ru.py

uv run python exporter/deconstructor/deconstructor_exporter_ru.py

uv run python exporter/kindle/kindle_exporter_ru.py

uv run python scripts/rus_exporter/ru_zip_goldendict_mdict.py

uv run python scripts/moving/move_mdict_ru.py

uv run python scripts/rus_exporter/config_github_local_dpd_sbs.py

git checkout -- pyproject.toml

git checkout -- db/sanskrit/root_families_sanskrit.tsv

git checkout -- shared_data/changed_templates
