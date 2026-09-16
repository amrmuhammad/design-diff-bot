#!/usr/bin/env bash
# Run the same checks CI runs, before you push.
set -e

echo "▶ ruff check..."
ruff check src tests

echo "▶ ruff format --check..."
ruff format --check src tests

echo "▶ pytest..."
pytest -q

echo "✅ All checks passed. Safe to commit and push."
