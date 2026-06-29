#!/bin/bash

# Copy DPD-SBS and RU-DPD to the server via distribute.py subcommands.

ask_and_run() {
    local prompt="$1" action="$2"
    response=$(uv run tools/ask.py "$prompt") || exit 1
    if [[ $response == "y" ]]; then
        uv run python3 scripts/moving/distribute.py "$action"
    fi
}

ask_and_run "DPD-SBS to the server?" "copy_dpdsbs_from_sbs2filesrv"
ask_and_run "RU-DPD to the server?" "copy_rudpd_from_share2filesrv"
