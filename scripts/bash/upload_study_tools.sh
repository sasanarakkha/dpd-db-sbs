#!/bin/bash

# Conditionally create or append to a sasanarakkha/study-tools release, then upload all assets.

set -u
set -o pipefail

REPO="sasanarakkha/study-tools"
ASSET_DIR="temp/study_tools_release"

LATEST_TAG=$(gh release list --repo "$REPO" --limit 1 --json tagName --jq '.[0].tagName' 2>/dev/null || echo "")

CREATE_NEW=true
if [ -n "$LATEST_TAG" ]; then
    FIRST_ASSET=$(uv run python scripts/bash/for_release.py | awk '{print $1}')
    EXISTING=$(gh release view "$LATEST_TAG" --repo "$REPO" --json assets \
               --jq '.assets[].name' 2>/dev/null || echo "")
    if ! echo "$EXISTING" | grep -qx "$FIRST_ASSET"; then
        CREATE_NEW=false
    fi
fi

if [ "$CREATE_NEW" = true ]; then
    TAG="artifacts-$(date -u +'%d.%m.%Y_%H-%M-%S')"
    NAME="Build $(date -u +'%d.%m.%Y %H:%M') UTC"
    echo "Creating new release: $NAME (tag: $TAG)"
    gh release create "$TAG" --repo "$REPO" --title "$NAME" --draft
else
    TAG="$LATEST_TAG"
    echo "Appending to existing release: $TAG"
fi

for asset in $(uv run python scripts/bash/for_release.py); do
    full_path="$ASSET_DIR/$asset"
    if [ ! -f "$full_path" ]; then
        echo "Warning: $full_path not found, skipping."
        continue
    fi
    echo "--> Uploading $asset"
    gh release upload "$TAG" "$full_path" --repo "$REPO" --clobber
done

echo "Done. https://github.com/$REPO/releases/tag/$TAG"
