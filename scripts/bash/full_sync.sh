#!/bin/bash

# DEPRECATED: This script is now a wrapper around kamma/upstream_sync/scripts/execute_sync.py
# Please use the Python script directly if possible.

set -euo pipefail

PROJECT_DIR="$(pwd)"
THREAD_DIR="${1:-}"

echo "⚠️  This bash script is deprecated. Forwarding to execute_sync.py..."
echo ""

if [ -n "$THREAD_DIR" ]; then
    uv run python3 kamma/upstream_sync/scripts/execute_sync.py "$THREAD_DIR"
else
    uv run python3 kamma/upstream_sync/scripts/execute_sync.py
fi
