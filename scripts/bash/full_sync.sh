#!/bin/bash

# Synchronize the local branch from the configured upstream ref while restoring protected local files.

set -euo pipefail # Exit on error, treat unset variables as error, pipeline fails on first error

# Non-interactive script to synchronize sbs-ru branch from as_upstream,
# using selective sync to preserve DPS-specific customizations.

PROJECT_DIR="$(pwd)"
DATE=$(date +"%d-%m")
COMMIT_MESSAGE_PREFIX="sync: "
COMMIT_MESSAGE_SUFFIX=" from accepted upstream ref ($DATE)"
TARGET_UPSTREAM_REF="$(uv run python3 kamma/upstream_sync/scripts/sync_runtime.py print-target-ref)"

echo "ℹ️ Project directory: $PROJECT_DIR"
echo "ℹ️ Target upstream ref: $TARGET_UPSTREAM_REF"

# Optional: verify manifest before sync (skip if no thread_dir provided)
if [ -n "${1:-}" ] && [ -f "$1/prep_manifest.json" ]; then
    echo "ℹ️ Verifying prep manifest from $1..."
    if uv run python3 kamma/upstream_sync/scripts/sync_runtime.py verify-manifest "$1"; then
        echo "✅ Prep manifest verified."
    else
        echo "⚠️ Prep manifest verification failed. Proceeding anyway..."
    fi
fi

# Read exclusions dynamically from kamma/upstream_sync/registry.json
echo "ℹ️ Reading exclusions from kamma/upstream_sync/registry.json..."
EXCLUDE_FILES=()
while IFS= read -r line; do
    EXCLUDE_FILES+=("$line")
done < <(uv run python3 kamma/upstream_sync/scripts/sync_runtime.py print-exclusions)

# Check if we successfully got exclusions
if [ ${#EXCLUDE_FILES[@]} -eq 0 ]; then
    echo "⚠️ Warning: No exclusions found or failed to parse registry."
else
    echo "✅ Loaded ${#EXCLUDE_FILES[@]} exclusions."
fi

# Update as_upstream branch
echo "ℹ️ Updating as_upstream branch to match $TARGET_UPSTREAM_REF..."
git checkout as_upstream || exit 1
git fetch upstream || exit 1
git reset --hard "$TARGET_UPSTREAM_REF" || exit 1

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

# Commit message
COMMIT_MESSAGE="${COMMIT_MESSAGE_PREFIX}selective update${COMMIT_MESSAGE_SUFFIX}"

echo "✅ Done! Please commit with message: $COMMIT_MESSAGE"
