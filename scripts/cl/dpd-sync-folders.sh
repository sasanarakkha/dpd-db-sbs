#!/bin/bash

PROJECT_DIR="$HOME/Documents/dpd-db"
FOLDERS=(
    db_tests
    db_tests_gui
    docs
    go_modules
    gui2
    scripts
)
FILES=(
    .clinerules
    .gitattributes
    .gitignore
    .gitmodules
    go.mod
    go.sum
    mkdocs.yaml
    pyproject.toml
    README.md
)

EXCLUDE_FOLDERS=(
    scripts/cl
)
EXCLUDE_FILES=( ) # Add files to exclude here

cd "$PROJECT_DIR" || exit 1

# Update as_upstream branch
git checkout as_upstream || exit 1
git pull origin as_upstream || exit 1
git fetch upstream || exit 1
git reset --hard upstream/main || exit 1

# Switch to sbs-ru and sync
git checkout sbs-ru || exit 1

echo "🔄 Syncing folders (with exceptions):"
# Handle 'scripts' folder with exclusion
echo "  - scripts (excluding cl)"
# Instead of hardcoding the exception for "scripts", use the EXCLUDE lists
for FOLDER in "${FOLDERS[@]}"; do
    EXCLUDE=false
    for EXCLUDE_FOLDER in "${EXCLUDE_FOLDERS[@]}"; do
        if [[ "$FOLDER" == "$(dirname "$EXCLUDE_FOLDER")" && "$EXCLUDE_FOLDER" != "$FOLDER" ]]; then
            EXCLUDE=true
            break
        fi
    done

    if [[ "$EXCLUDE" == "true" ]]; then
        echo "  - $FOLDER (excluding $(basename "$EXCLUDE_FOLDER"))"
        rsync -av --delete --exclude="$(basename "$EXCLUDE_FOLDER")" "$(git rev-parse --show-toplevel)/$FOLDER/" "$PROJECT_DIR/$FOLDER/"
    else
        echo "  - $FOLDER"
        git checkout as_upstream -- "$FOLDER" || exit 1
    fi
done

#Sync files, with exclusion
for FILE in "${FILES[@]}"; do
    echo "  - $FILE"
    git checkout as_upstream -- "$FILE" || exit 1
done

# Commit changes with date
DATE=$(date +"%d-%m")
git add "${FOLDERS[@]}" "${FILES[@]}" || exit 1
git commit -m "sync: update from as_upstream ($DATE)" || exit 1

echo "✅ Done!"