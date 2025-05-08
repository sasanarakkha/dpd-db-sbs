#!/bin/bash

# This script exports the RU DPD.

set -e

git checkout sbs-ru

python -c "from tools.configger import config_update; config_update('exporter', 'language', 'ru')"
python -c "from tools.configger import config_update; config_update('dictionary', 'link_url', 'https://find.dhamma.gift/bw/')"

python -c "from tools.configger import print_config_settings; print_config_settings(['dictionary', 'goldendict', 'exporter'])"

while true; do
    echo -ne "\033[1;36m generate_components?\033[0m"
    read yn
    case $yn in
        [Yy]* )
            scripts/bash/generate_components.sh
            break;;
        * )
            scripts/build/families_to_json.py
            break;;
    esac
done

echo "exporting RU DPD"

exporter/grammar_dict/grammar_dict.py

exporter/goldendict/main.py

exporter/deconstructor/deconstructor_exporter.py

exporter/kindle/kindle_exporter.py

scripts/rus_exporter/ru_zip_goldendict_mdict.py

# scripts/moving/move_mdict_ru.py

python -c "from tools.configger import config_update; config_update('exporter', 'language', 'en')"
python -c "from tools.configger import config_update; config_update('dictionary', 'link_url', 'http://filesrv1:8083/')"
python -c "from tools.configger import config_update; config_update('exporter', 'make_ebook', 'no')"
python -c "from tools.configger import config_update; config_update('exporter', 'make_deconstructor', 'no')"
python -c "from tools.configger import config_update; config_update('exporter', 'make_grammar', 'no')"



git checkout -- pyproject.toml

git checkout -- db/sanskrit/root_families_sanskrit.tsv

git checkout -- shared_data/changed_templates


