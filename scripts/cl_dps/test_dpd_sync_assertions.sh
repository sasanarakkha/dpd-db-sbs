#!/bin/bash
set -euo pipefail

# Test script for dpd-sync-assertions.sh
# Expected output:
# 1. Shows a diff summary
# 2. Shows a warning for db/models.py
# 3. Shows a warning for a new template

echo "Setting up mock changes..."
PREV_SHA=$(git rev-parse HEAD)

# Create a temporary file to mock a schema change
echo "# mock change" >> db/models.py

# Create a mock template
mkdir -p exporter/goldendict/templates/
touch exporter/goldendict/templates/mock_template.html

git add db/models.py exporter/goldendict/templates/mock_template.html
git commit -m "chore(test): mock changes for testing assertions"

echo "Running assertions..."
bash scripts/cl_dps/dpd-sync-assertions.sh "$PREV_SHA"

echo "Cleaning up mock changes..."
git reset --hard HEAD^

echo "Test complete!"
