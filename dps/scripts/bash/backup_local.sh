#!/bin/bash

# --- Create a temporary exclude file ---
EXCLUDE_FILE=$(mktemp) || { echo "Failed to create temp file"; exit 1; }

cat > "$EXCLUDE_FILE" <<EOF
.git/
dpd.db
.venv/
.vscode/
__init__.py
.__init__.py
output/
share/
resources/
__pycache__/
EOF

# --- Define relative paths ---
BACKUP_DIR_REL="../../../../../backups/"
SOURCE_DIR_REL="../../.."

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

SOURCE_DIR=$(resolve_path "$SOURCE_DIR_REL") || { echo "Failed to resolve SOURCE_DIR"; exit 1; }
BACKUP_DIR=$(resolve_path "$BACKUP_DIR_REL") || { echo "Failed to resolve BACKUP_DIR"; exit 1; }

# --- Ensure backup directory exists ---
mkdir -p "$BACKUP_DIR" || { echo "Failed to create backup dir"; exit 1; }

# --- Logging ---
echo "------ Backup Started at $(date) ------"
echo "Source: $SOURCE_DIR_REL → $SOURCE_DIR"
echo "Backup: $BACKUP_DIR_REL → $BACKUP_DIR"
echo ""

# --- Run rsync ---
rsync -azxi \
    --no-links \
    --exclude-from="$EXCLUDE_FILE" \
    --info=progress2 \
    --stats \
    "$SOURCE_DIR/" "$BACKUP_DIR" || { echo "rsync failed"; exit 1; }

echo ""
echo "------ Backup Ended at $(date) ------"

# --- Cleanup ---
rm "$EXCLUDE_FILE" || { echo "Failed to delete temp file"; exit 1; }
exit 0