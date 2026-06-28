#!/bin/bash

# Push generated vocabulary files in the DPD Pali courses repository.

set -euo pipefail

COURSES_DIR="$HOME/Documents/dpd-pali-courses"
GENERATED_PATHS=(
    "docs/generated/vocab"
    "docs/generated/abbreviations.md"
)

cd "$COURSES_DIR"

git status --short -- "${GENERATED_PATHS[@]}"

if ! git diff --quiet -- "${GENERATED_PATHS[@]}"; then
    git add -- "${GENERATED_PATHS[@]}"
    git commit -m "update pali course vocab" -- "${GENERATED_PATHS[@]}"
    git push
fi
