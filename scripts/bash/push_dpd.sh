#!/bin/bash

# This script is used to copy DPD files to the server.
# It first checks if the user wants to mount the fileserver, then downloads DPD files,
# and finally unzips and copies the files to the appropriate directories.

cd "$HOME/Documents/dpd-db"

echo -e "\033[1;33m We are going to copy DPD to the server. \033[0m"

# Ask to download DPD
while true; do
    echo -ne "\033[1;34m Do you want to download DPD? \033[0m"
    read -n 1 -s yn
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m Downloading DPD...\033[0m"
            uv bash run scripts/bash/download_dpd.sh
            break;;
        * )
            break;;
    esac
done

# Ask to push RU DPD
while true; do
    echo -ne "\033[1;34m RU-DPD to the server?\033[0m"
    read -n 1 -s yn
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m Unzipping and copying ru-dpd.\033[0m"
            uv python run scripts/moving/unzip_rudpd_to_filesrv.py
            break;;
        * )
            break;;
    esac
done

# Ask to push DPD
while true; do
    echo -ne "\033[1;34m DPD to the server? \033[0m"
    read yn
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m Unzipping and copying DPD...\033[0m"
            uv python run scripts/moving/unzip_dpd_to_filesrv.py
            break;;
        * )
            break;;
    esac
done

# Ask to push DPD-SBS
while true; do
    echo -ne "\033[1;34m DPD-SBS to the server? \033[0m"
    read -n 1 -s yn
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m Unzipping and copying DPD-SBS...\033[0m"
            uv python run scripts/moving/unzip_dpd_sbs_to_filesrv.py
            break;;
        * )
            break;;
    esac
done

# Ask to unzip to local goldendict
while true; do
    echo -ne "\033[1;34m Unzip to local goldendict? \033[0m"
    read -n 1 -s yn
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m Unzipping to local goldendict...\033[0m"
            uv python run scripts/moving/unzip_dpd_to_gd.py
            break;;
        * )
            break;;
    esac
done

# Ask to unzip to local share
while true; do
    echo -ne "\033[1;34m Unzip to local share? \033[0m"
    read -n 1 -s yn
    if [[ $yn == "q" ]]; then
        echo -e "\n\033[1;31m Aborted by user.\033[0m"
        exit 1
    fi
    case $yn in
        [Yy]* )
            echo -e "\033[1;33m Unzipping to local share...\033[0m"
            uv python run scripts/moving/unzip_dpd_to_share.py
            break;;
        * )
            break;;
    esac
done
