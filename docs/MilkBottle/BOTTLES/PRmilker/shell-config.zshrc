# ---   auto_pr_to_sourcery()  ---------------------------------------------
auto_pr_to_sourcery() {
  set -euo pipefail

  # Detect current branch
  local branch
  branch=$(git rev-parse --abbrev-ref HEAD)

  # Guardrails
  if [[ "$branch" == "main" || "$branch" == "master" ]]; then
    echo "❌  Refusing to create a PR from the $branch branch. Checkout a feature branch first." >&2
    return 1
  fi

  # Ensure there are commits to push
  if git diff --quiet origin/"$branch"..HEAD 2>/dev/null; then
    echo "ℹ️  No new commits to push for $branch. Aborting." >&2
    return 0
  fi

  echo "🔄  Pushing '$branch' to origin…"
  git push -u origin "$branch"

  # Create PR if one doesn’t already exist
  if gh pr view "$branch" --json number >/dev/null 2>&1; then
    echo "ℹ️  Pull Request already exists for $branch. Opening it in the browser…"
    gh pr view --web "$branch"
  else
    echo "📦  Creating Pull Request…"
    gh pr create \
      --base main \
      --head "$branch" \
      --title "${branch//-/ }" \
      --body "Automated PR from \`$branch\` using \`auto_pr_to_sourcery\`."
  fi

  echo "✅  Pull Request ready. Sourcery will review automatically."
}
# ---------------------------------------------------------------------------