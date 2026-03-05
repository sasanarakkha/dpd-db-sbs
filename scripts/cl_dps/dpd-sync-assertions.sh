#!/bin/bash
set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 <PREV_SHA>"
    exit 1
fi

PREV_SHA=$1

echo "=================================================="
echo "🛡️  RUNNING POST-SYNC ASSERTIONS AND CHECKS"
echo "=================================================="

# 1. Raw File Diff Summary
echo "📊 Diff Summary (since $PREV_SHA):"
git diff --stat "$PREV_SHA"
echo ""

# 2. DB Schema Checks
echo "🗄️ Checking for DB Schema changes..."
if git diff --name-only "$PREV_SHA" | grep -q "db/models.py"; then
    echo "⚠️  WARNING: db/models.py was modified in this sync!"
    echo "   Ensure local SBS and Russian schema extensions are intact and compatible."
else
    echo "✅ No DB schema changes detected."
fi
echo ""

# 3. New Upstream Templates Check
echo "📄 Checking for new upstream templates..."
NEW_TEMPLATES=$(git diff --name-only --diff-filter=A "$PREV_SHA" | grep "templates/" || true)
if [ -n "$NEW_TEMPLATES" ]; then
    echo "⚠️  WARNING: New upstream templates detected:"
    echo "$NEW_TEMPLATES"
    echo "   Ensure shadow copies (e.g. ru_templates, sbs_templates) are created if needed."
else
    echo "✅ No new upstream templates detected."
fi
echo "=================================================="
