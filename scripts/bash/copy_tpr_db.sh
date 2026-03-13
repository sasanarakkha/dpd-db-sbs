#!/bin/bash

# directory where this script lives (Finder-safe)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---------- Sources (next to script) ----------
SRC_DB="$SCRIPT_DIR/tipitaka_pali.db"
SRC_DPD_DIR="$SCRIPT_DIR/dpd"

# ---------- Destinations ----------
DEST_DB="$HOME/Library/Containers/org.americanmonk.tpp/Data/Library/Application Support/org.americanmonk.tpp/tipitaka_pali.db"
DEST_DPD_DIR="$HOME/Documents/GoldenDict/dpd"

# ---------- Checks ----------
if [ ! -f "$SRC_DB" ]; then
    echo "❌ Missing source file: $SRC_DB"
    exit 1
fi

if [ ! -d "$SRC_DPD_DIR" ]; then
    echo "❌ Missing source folder: $SRC_DPD_DIR"
    exit 1
fi

# ---------- Ensure destinations ----------
mkdir -p "$(dirname "$DEST_DB")"
mkdir -p "$(dirname "$DEST_DPD_DIR")"

# ---------- Copy DB ----------
if cp -f "$SRC_DB" "$DEST_DB"; then
    echo "✅ tipitaka_pali.db copied successfully to $DEST_DB"
else
    echo "❌ Failed to copy tipitaka_pali.db"
fi

# ---------- Replace dpd folder ----------
if [ -d "$DEST_DPD_DIR" ]; then
    rm -rf "$DEST_DPD_DIR"
fi

if cp -R "$SRC_DPD_DIR" "$DEST_DPD_DIR"; then
    echo "✅ dpd folder replaced successfully in $DEST_DPD_DIR"
else
    echo "❌ Failed to copy dpd folder"
fi
