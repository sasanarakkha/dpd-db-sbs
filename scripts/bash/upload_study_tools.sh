#!/bin/bash
#
# Create or append to a sasanarakkha/study-tools GitHub release and upload assets.
#
# Called by .github/workflows/anki_release.yml after stage_study_tools.sh.
# If the latest release already contains our assets, a new release tag is created.
# Otherwise, assets are appended to the latest release (handles CI retry mid-upload).
#

set -eu
set -o pipefail

REPO="sasanarakkha/study-tools"
ASSET_DIR="temp/study_tools_release"

LATEST_TAG=$(gh release list --repo "$REPO" --limit 1 --json tagName --jq '.[0].tagName' 2>/dev/null || echo "")

# CREATE_NEW=true  → latest release is complete → create fresh tag
# CREATE_NEW=false → latest release is missing assets → append to it
CREATE_NEW=true
if [ -n "$LATEST_TAG" ]; then
    FIRST_ASSET=$(uv run python scripts/export/for_release.py | awk '{print $1}')
    EXISTING=$(gh release view "$LATEST_TAG" --repo "$REPO" --json assets \
               --jq '.assets[].name' 2>/dev/null || echo "")
    if ! echo "$EXISTING" | grep -qx "$FIRST_ASSET"; then
        CREATE_NEW=false
    fi
fi

if [ "$CREATE_NEW" = true ]; then
    TAG="artifacts-$(date -u +'%d.%m.%Y_%H-%M-%S')"
    NAME="Build $(date -u +'%d.%m.%Y %H:%M') UTC"
    uv run tools/ask.py --print -c green "Creating new release: $NAME (tag: $TAG)"
    gh release create "$TAG" --repo "$REPO" --title "$NAME" --draft
else
    TAG="$LATEST_TAG"
    uv run tools/ask.py --print -c yellow "Appending to existing release: $TAG"
fi

for asset in $(uv run python scripts/export/for_release.py); do
    full_path="$ASSET_DIR/$asset"
    if [ ! -f "$full_path" ]; then
        uv run tools/ask.py --print -c red "Warning: $full_path not found, skipping."
        continue
    fi
    uv run tools/ask.py --print "--> Uploading $asset"
    gh release upload "$TAG" "$full_path" --repo "$REPO" --clobber
done

uv run tools/ask.py --print -c green "Done. https://github.com/$REPO/releases/tag/$TAG"
