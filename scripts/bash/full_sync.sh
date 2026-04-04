#!/bin/bash

set -euo pipefail # Exit on error, treat unset variables as error, pipeline fails on first error

# Non-interactive script to synchronize sbs-ru branch from as_upstream,
# using selective sync to preserve DPS-specific customizations.

PROJECT_DIR="$(pwd)"
DATE=$(date +"%d-%m")
COMMIT_MESSAGE_PREFIX="sync: "
COMMIT_MESSAGE_SUFFIX=" from as_upstream ($DATE)"

echo "ℹ️ Project directory: $PROJECT_DIR"

# Read exclusions dynamically from kamma/upstream_sync/registry.json
echo "ℹ️ Reading exclusions from kamma/upstream_sync/registry.json..."
export PROJECT_DIR
EXCLUDE_FILES=()
while IFS= read -r line; do
    EXCLUDE_FILES+=("$line")
done < <(python3 -c '
import json, os, sys
registry_path = os.path.join(os.environ["PROJECT_DIR"], "kamma/upstream_sync/registry.json")
sys.path.insert(0, os.environ["PROJECT_DIR"])
from kamma.upstream_sync.registry_helper import get_modified_upstream_paths
data = json.load(open(registry_path))
paths = get_modified_upstream_paths(data) + data["no_sync_files"]
print("\n".join(paths))
')

# Check if we successfully got exclusions
if [ ${#EXCLUDE_FILES[@]} -eq 0 ]; then
    echo "⚠️ Warning: No exclusions found or failed to parse registry."
else
    echo "✅ Loaded ${#EXCLUDE_FILES[@]} exclusions."
fi

# Update as_upstream branch
echo "ℹ️ Updating as_upstream branch to match upstream/main..."
git checkout as_upstream || exit 1
git fetch upstream || exit 1
git reset --hard upstream/main || exit 1

# Switch to sbs-ru and sync
echo "ℹ️ Switching to sbs-ru branch..."
git checkout sbs-ru || exit 1
SBR_RU_ORIGINAL_SHA=$(git rev-parse HEAD) # Capture SHA of sbs-ru before modifications

echo "🔄 Performing Automated Selective Sync from as_upstream to sbs-ru..."

echo "  ➡️ Performing full checkout from as_upstream..."
git checkout as_upstream -- . || exit 1

echo "  ➡️ Restoring excluded files from sbs-ru state ($SBR_RU_ORIGINAL_SHA)..."
for EXCLUDED_FILE in "${EXCLUDE_FILES[@]}"; do
    # Skip empty lines
    [ -z "$EXCLUDED_FILE" ] && continue
    
    echo "    - Processing excluded file: $EXCLUDED_FILE"
    
    # Check if file existed in original sbs-ru state
    if git rev-parse --verify "${SBR_RU_ORIGINAL_SHA}:${EXCLUDED_FILE}" >/dev/null 2>&1; then
        echo "      Restoring $EXCLUDED_FILE from $SBR_RU_ORIGINAL_SHA..."
        git restore --source="$SBR_RU_ORIGINAL_SHA" --staged --worktree "$EXCLUDED_FILE" || \
            echo "      ⚠️ Warning: Failed to restore $EXCLUDED_FILE."
    else
        # File did not exist in sbs-ru
        if [ -e "$EXCLUDED_FILE" ]; then 
            echo "      $EXCLUDED_FILE did not exist in $SBR_RU_ORIGINAL_SHA, removing it (added by as_upstream)."
            git rm -r --cached --ignore-unmatch "$EXCLUDED_FILE" >/dev/null 2>&1
            rm -rf "$EXCLUDED_FILE"
        fi
    fi
done

# Run any assertions if they exist
if [ -f "$PROJECT_DIR/scripts/bash/dpd-sync-assertions.sh" ]; then
    echo "ℹ️ Running sync assertions..."
    bash "$PROJECT_DIR/scripts/bash/dpd-sync-assertions.sh" "$SBR_RU_ORIGINAL_SHA" || echo "⚠️ Assertions failed, but continuing..."
fi

# Staging all changes
echo "  ➕ Staging all changes..."
git add . || exit 1

# Commit changes
COMMIT_MESSAGE="${COMMIT_MESSAGE_PREFIX}selective update${COMMIT_MESSAGE_SUFFIX}"
echo "📝 Committing changes to sbs-ru..."
if git diff --staged --quiet; then
    echo "✅ No changes to commit. Branch is already up-to-date with selective sync."
else
    git commit -m "$COMMIT_MESSAGE" || { 
        echo "❌ Commit failed."
        exit 1
    }
    echo "✅ Done! Commited: $COMMIT_MESSAGE"
fi
