#!/bin/bash
# Push DPD artifacts to server and local destinations via interactive prompts.

ask_run() {
    local prompt="$1" msg="$2" cmd="$3"
    local answer
    answer=$(uv run tools/ask.py -c blue "$prompt ")
    if [ "$answer" = "y" ]; then
        uv run tools/ask.py --print -c yellow "$msg"
        eval "$cmd"
    fi
}

uv run tools/ask.py --print -c yellow "We are going to copy DPD to the server."

ask_run "Download DPD?" "Downloading DPD..." "scripts/bash/download_dpd.sh"
ask_run "RU-DPD to the server?" "Unzipping and copying ru-dpd." "scripts/moving/distribute.py unzip_rudpd_to_filesrv"
ask_run "DPD to the server?" "Unzipping and copying DPD..." "scripts/moving/distribute.py unzip_dpd_to_filesrv"
ask_run "DPD-SBS to the server?" "Unzipping and copying DPD-SBS..." "scripts/moving/distribute.py unzip_dpd_sbs_to_filesrv"
ask_run "Unzip to local goldendict?" "Unzipping to local goldendict..." "scripts/moving/distribute.py unzip_dpd_to_gd && scripts/bash/manual_update_mac_dict.sh"
ask_run "Unzip to local share?" "Unzipping to local share..." "scripts/moving/distribute.py unzip_dpd_to_share"
