#!/usr/bin/env bash
# Run the same checks CI runs, before you push.
set -e

# Auto-activate the local venv if present and not already active
if [ -z "${VIRTUAL_ENV:-}" ] && [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

echo "▶ ruff check..."
ruff check src tests

echo "▶ ruff format --check..."
ruff format --check src tests

echo "▶ pytest..."
pytest -q

echo "✅ All checks passed. Safe to commit and push."
