#!/bin/bash

uv run python scripts/export/backup_corrections_additions.py

while true; do
    echo -ne "\033[1;34m need to push on GitHub? \033[0m"
    read yn
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m pushing all...\033[0m"
            git push
            break;;
        *  )
            break;;
    esac
done


# export VISUAL=nano 
# crontab -e 