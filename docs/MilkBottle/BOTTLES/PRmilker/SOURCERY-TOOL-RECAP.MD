# Full Recap (+ Quality-of-Life Enhancements)

Below is a consolidated view of every file we generated, where it lives, what it does, and a polished replacement that folds in extra safety checks, UX niceties, and extensibility. Feel free to copy‑paste straight into your repo.

## Path Purpose Key QoL Upgrades

- scripts/pr_check.sh One‑shot environment validator • Detects dirty working tree
- Auto‑detects default branch (no hard‑coded main)
- Colourful pass/fail output
- .githooks/pre‑push Local guardrail — blocks bad pushes • Runs only when Python files changed
- Graceful fallback if Sourcery CLI missing
- Uses --patch to restrict analysis to staged diff
- shell/auto_pr_to_sourcery.sh (sourced in ~/.zshrc / ~/.bashrc) One‑command helper: push → PR → trigger Sourcery • AUTO_PR_BASE env var overrides default branch
- Adds “Sourcery‑Auto” label to PR
- Opens PR in browser unless --no-browser flag passed
- .github/workflows/sourcery-review.yml CI enforcement • Concurrency group to cancel superseded runs
- Caches pip deps for speed
- Uploads Sourcery JSON report as artifact + PR summary comment
- README.md snippet Developer guide • Troubleshooting tips & FAQ
- Quick‑link to enable Git hooks on clone (core.hooksPath)
- docs/Hybrid‑Workflow‑Roadmap.md Living checklist • Final status table with ✅ marks and links to files

## 1 ⃣ scripts/pr_check.sh (updated)

```bash
#!/usr/bin/env bash

# -----------------------------------------------------------

# Hybrid Sourcery Workflow – prerequisite checker

# -----------------------------------------------------------

set -euo pipefail
RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[1;33m'; NC='\033[0m'

default_branch=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null \
                  | sed 's@^refs/remotes/origin/@@' || echo main)
current_branch=$(git rev-parse --abbrev-ref HEAD)

dirty=$(git status --porcelain)
gh auth status &>/dev/null && gh_ok=$? || gh_ok=$?
sourcery_ok=$(gh api repos/${GITHUB_REPOSITORY:-$(git config remote.origin.url | sed -E 's@._github.com[:/](._)\.git@\1@')}/installation 2>/dev/null || true)

echo -e "${YLW}🔍  Running environment checks...${NC}"

[[-n "$dirty"]] && { echo -e "${RED}✖ Working tree is dirty. Commit or stash first.${NC}"; exit 1; }
[["$current_branch" == "$default_branch"]] && { echo -e "${RED}✖ You are on $default_branch — create a feature branch.${NC}"; exit 1; }
[[$gh_ok -ne 0]] && { echo -e "${RED}✖ GitHub CLI not authenticated (${YLW}gh auth login${RED}).${NC}"; exit 1; }
[[-z "$sourcery_ok"]] && { echo -e "${RED}✖ Sourcery GitHub App not installed for this repo.${NC}"; exit 1; }

echo -e "${GRN}✔ All checks passed.${NC}"
```

## 2 ⃣ .githooks/pre‑push (updated)

```bash
#!/usr/bin/env bash

# Run Sourcery on staged Python changes; block push on issues.

set -euo pipefail
files_changed=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.py$' || true)
[[-z "$files_changed"]] && exit 0 # nothing to review

if ! command -v sourcery &>/dev/null; then
echo "⚠️ Sourcery CLI not found – skipping pre‑push check."
exit 0
fi

echo "🔮 Running Sourcery review on staged diff…"
if ! git diff --cached | sourcery review --patch - ; then
echo "❌ Sourcery flagged issues. Commit fixes or use --no-verify to bypass."
exit 1
fi
echo "✅ Sourcery passed."
```

Enable it once per repo:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-push
```

## 3 ⃣ shell/auto_pr_to_sourcery.sh (updated)

```bash
auto_pr_to_sourcery() {
local default_branch base branch
default_branch=$(git symbolic-ref --quiet refs/remotes/origin/HEAD \
                    | sed 's@^refs/remotes/origin/@@') || default_branch=main
  base="${AUTO_PR_BASE:-$default_branch}"
  branch=$(git symbolic-ref --short HEAD)

if [["$branch" == "$base"]]; then
echo "❌ You’re on $base. Checkout a feature branch first."
return 1
fi

if ! git diff --quiet --exit-code; then
echo "💾 Committing unstaged changes..."
git add -A && git commit -m 'WIP: Auto‑commit before PR'
fi

echo "🚀 Pushing $branch..."
  git push -u origin "$branch"

echo "📝 Creating Pull Request..."
gh pr create \
 --base "$base" \
      --head "$branch" \
 --title "${branch//-/ }" \
 --label "Sourcery‑Auto" \
 --body "Automated PR via \`auto_pr_to_sourcery\`"

[["$1" == "--no-browser"]] || gh pr view --web
}
```

Add to ~/.zshrc or ~/.bashrc, then source the file.

## 4 ⃣ .github/workflows/sourcery-review.yml (updated)

```yaml
name: Sourcery Review

on:
pull_request:
types: [opened, synchronize, reopened]

jobs:
review:
runs-on: ubuntu-latest
concurrency:
group: sourcery-${{ github.head_ref }}
cancel-in-progress: true

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }

      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
          restore-keys: ${{ runner.os }}-pip-

      - run: pip install --upgrade sourcery

      - name: Run Sourcery
        id: sourcery
        run: |
          sourcery review . --head ${{ github.event.pull_request.head.sha }} \
            | tee sourcery.json
          echo "exit_code=$?" >> "$GITHUB_OUTPUT"

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: sourcery-report
          path: sourcery.json

      - name: PR comment summary
        if: steps.sourcery.outputs.exit_code != '0'
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          message: |
            🛠 **Sourcery Suggestions**
            The Sourcery CLI flagged issues—see the PR Checks tab or attached JSON report.

```

## 5 ⃣ README Insert (updated)

````markdown
### 🚀 Hybrid Sourcery Workflow

| Stage          | What happens                                          | File/Command                            |
| -------------- | ----------------------------------------------------- | --------------------------------------- |
| Local check    | `./scripts/pr_check.sh` verifies tools & branch       | `scripts/pr_check.sh`                   |
| Pre‑push guard | Sourcery reviews staged diff, blocks on issues        | `.githooks/pre‑push`                    |
| One‑command PR | Push branch, open PR, label & trigger review          | `auto_pr_to_sourcery`                   |
| CI safety net  | Sourcery re‑reviews every PR update in GitHub Actions | `.github/workflows/sourcery-review.yml` |

> **Tip:** After cloning, run `git config core.hooksPath .githooks` once to activate hooks.

#### Common issues

| Symptom                 | Fix                                                       |
| ----------------------- | --------------------------------------------------------- |
| _“gh: no auth token”_   | `gh auth login` and choose HTTPS w/ pat                   |
| _Pre‑push skips review_ | Ensure Sourcery CLI is installed (`pip install sourcery`) |

```bash
# Copy each file into your repo at the indicated paths.
# chmod +x any shell scripts / hooks.
# On first clone, run:
git config core.hooksPath .githooks
```
````
