#!/usr/bin/env bash
# .githooks/pre‑push
# Abort the push if Sourcery flags issues in the staged diff.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT" || exit 1

# Skip hook when no Python files are staged
if ! git diff --cached --name-only | grep -E '\.py$' >/dev/null; then
  exit 0
fi

echo "🔍 Running Sourcery review on staged changes…"
# Assumes Sourcery CLI is on PATH (pipx or virtualenv)
sourcery review .

EXIT_CODE=$?
if [ "$EXIT_CODE" -ne 0 ]; then
  echo '❌  Sourcery found problems. Push aborted.'
  exit "$EXIT_CODE"
fi

echo '✅  Sourcery passed. Proceeding with push.'
exit 0