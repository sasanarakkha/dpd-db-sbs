#!/bin/bash

# Push generated vocabulary files in the DPD Pali courses repository.

set -euo pipefail

COURSES_DIR="$HOME/Documents/dpd-pali-courses"
GENERATED_PATHS=(
    "docs/generated/vocab"
    "docs/generated/abbreviations.md"
)

cd "$COURSES_DIR"

if [[ -z "$(git status --porcelain -- "${GENERATED_PATHS[@]}")" ]]; then
    echo "No generated vocab changes to push."
    exit 0
fi

git status --short -- "${GENERATED_PATHS[@]}"
git add -- "${GENERATED_PATHS[@]}"

if git diff --cached --quiet -- "${GENERATED_PATHS[@]}"; then
    echo "No generated vocab changes to commit."
    exit 0
fi

git commit -m "update pali course vocab" -- "${GENERATED_PATHS[@]}"
git push
