#!/bin/bash

# This script creates a backup of important files to fileserver

# Enable debugging
set -x

# --- Create a temporary exclude file ---
EXCLUDE_FILE=$(mktemp) || { echo "Failed to create temp file"; exit 1; }

cat > "$EXCLUDE_FILE" <<EOF
Cline
dpd-db/
devamitta.github.io/
DiffText/
large-language-model-project/
patimokkha_dict/
utilities/
word-frequency/
sasanarakkha/
output/
Zoom/
*Games
__pycache__
.gitignore
.stignore
.git
__init__.py
.__init__.py
uv
.venv/
.vscode
.stfolder/
.obsidian
20*.png
.DS_Store
EOF

# --- Resolve absolute paths (macOS & Linux compatible) ---
resolve_path() {
    local path="$1"
    # Try 'realpath' first (Linux)
    if command -v realpath >/dev/null; then
        realpath "$path"
    # Fallback to 'readlink -f' (some Linux)
    elif command -v readlink >/dev/null; then
        readlink -f "$path"
    # macOS fallback (no realpath/readlink -f)
    else
        cd "$path" && pwd
    fi
}

# Resolve paths
DOC_DIR=$(resolve_path "$HOME/Documents") || { echo "Failed to resolve DOC_DIR"; exit 1; }
# BACKUP_DIR=$(resolve_path "$HOME/backups") || { echo "Failed to resolve BACKUP_DIR"; exit 1; }
DEST_DIR=$(resolve_path "$HOME/filesrv1/share1/devamitta/") || { echo "Failed to resolve DEST_DIR"; exit 1; }

# --- Run rsync for each folder ---
rsync -azxi \
    --no-links \
    --exclude-from="$EXCLUDE_FILE" \
    --progress \
    --stats \
    "$DOC_DIR/" "$DEST_DIR/Documents/" || { echo "rsync failed for Documents"; exit 1; }

# rsync -azxi \
#     --no-links \
#     --exclude-from="$EXCLUDE_FILE" \
#     --progress \
#     --stats \
#     "$BACKUP_DIR/" "$DEST_DIR/backups/" || { echo "rsync failed for backups"; exit 1; }

# --- Cleanup ---
rm "$EXCLUDE_FILE" || { echo "Failed to delete temp file"; exit 1; }
exit 0