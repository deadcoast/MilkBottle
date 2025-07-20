#!/usr/bin/env bash
# pr_check.sh – Ensure environment is ready for the hybrid Sourcery workflow.
# -----------------------------------------------------------
# 1. Verifies you are **not** on main / master.
# 2. Confirms GitHub CLI is authenticated.
# 3. Checks Sourcery GitHub App is installed for this repo.
# 4. Warns if the current branch has no un‑pushed commits.

set -euo pipefail

RED="\033[0;31m"
GRN="\033[0;32m"
YEL="\033[0;33m"
NC="\033[0m"

info()  { printf "${GRN}✔ %s${NC}\n" "$1"; }
warn()  { printf "${YEL}⚠ %s${NC}\n" "$1"; }
error() { printf "${RED}✖ %s${NC}\n" "$1"; exit 1; }

# 1 — Branch guard
branch=$(git rev-parse --abbrev-ref HEAD)
if [[ "$branch" == "main" || "$branch" == "master" ]]; then
  error "You are on $branch. Switch to a feature branch before creating a PR."
else
  info "On branch: $branch"
fi

# 2 — GitHub CLI auth check
if ! gh auth status &>/dev/null; then
  error "GitHub CLI auth failed. Run 'gh auth login' and try again."
else
  info "GitHub CLI authenticated."
fi

# 3 — Sourcery App installation check
owner_repo=$(git config --get remote.origin.url | sed -E 's#.*github.com[/:]([^/]+/[^/.]+).*#\1#')
if ! gh api "/repos/$owner_repo/installation" &>/dev/null; then
  warn "Sourcery GitHub App does not appear installed on this repo. PR review will not trigger." 
else
  info "Sourcery GitHub App detected."
fi

# 4 — Unpushed commits check
if git diff --quiet origin/"$branch".."$branch"; then
  warn "No new commits to push for branch '$branch'."
else
  info "Branch has unpushed commits. Ready to push."
fi

printf "\n${GRN}Environment looks good. You can now run 'auto_pr_to_sourcery'.${NC}\n"
