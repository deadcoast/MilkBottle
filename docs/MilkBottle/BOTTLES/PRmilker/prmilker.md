# PRmilker

## Automatic PR Workflow for Sourcery‑Integrated Repositories

This document defines a streamlined, one‑command workflow that:

1. Pushes your current branch to GitHub
2. Opens a Pull Request against **main**
3. Triggers the Sourcery GitHub App to review the PR automatically

---

## 1. Bash Helper – `auto_pr_to_sourcery()`

Add the function below to your shell profile (`.bashrc`, `.zshrc`, or a dedicated script). It aborts on **main/master** to avoid mistakes, then performs the entire flow.

```bash
auto_pr_to_sourcery() {
  branch=$(git rev-parse --abbrev-ref HEAD)

  if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
    echo "❌  You’re on $branch. Create a feature branch first."
    return 1
  fi

  echo "🔄  Pushing $branch to origin…"
  git push -u origin "$branch"

  echo "📦  Creating pull request…"
  gh pr create \
    --base main \
    --head "$branch" \
    --title "$branch" \
    --body "Auto PR from $branch"

  echo "✅  Pull request ready – Sourcery review will start automatically."
}
```

---

## 2. Automation Architecture

### 2.1 Objectives

- **Zero‑click** interaction after `git push`
- Early feedback from Sourcery before merge
- Compatibility with existing GitHub marketplace app

### 2.2 Workflow Diagram

```mermaid
flowchart TD
  A[Local Commit & Push] --> B[GitHub PR (new or updated)]
  B --> C[Sourcery Auto‑Review]
  C --> D[Inline Suggestions in PR]
```

---

## 3. Optional Guardrails & Enhancements

### 3.1 Local Pre‑Push Hook (Quality Gate)

Run Sourcery locally and block the push if issues are found.

```bash
#!/usr/bin/env bash

changed=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.py$')
if [ -n "$changed" ]; then
  echo "Running Sourcery pre‑push review…"
  sourcery review .
  status=$?
  if [ $status -ne 0 ]; then
    echo "❌  Sourcery flagged issues – push aborted."
    exit $status
  fi
fi
```

### 3.2 CI Enforcement via GitHub Actions

Automatically run Sourcery on every PR event and (optionally) auto‑commit fixes.

```yaml
# .github/workflows/sourcery-review.yml
name: Sourcery PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  sourcery:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Install Sourcery
        run: pip install sourcery
      - name: Review with Sourcery
        run: sourcery review . --head ${{ github.event.pull_request.head.sha }}
      - name: Auto‑commit fixes (optional)
        run: |
          git config --global user.name "github-actions"
          git config --global user.email "action@github.com"
          git add .
          git commit -m "Sourcery auto‑fixes" || echo "No changes"
          git push
```

---

## 4. Recommended Hybrid Strategy

1. **Use `auto_pr_to_sourcery`** for effortless PR creation.
2. **Enable the Sourcery GitHub App** so every PR gets reviewed automatically.
3. **Add a local pre‑push hook** for instant feedback before code leaves your machine.
4. **(Optional) Add the GitHub Action** to enforce Sourcery checks and auto‑apply safe fixes in CI.

---

### Outcome

With this setup, a single command—`auto_pr_to_sourcery`—takes a feature branch all the way to a Sourcery‑reviewed Pull Request with zero manual GitHub clicks.

## Full Recap (+ Quality‑of‑Life Enhancements)

## Full Recap (+ Quality‑of‑Life Enhancements)

Below is a consolidated view of every file we generated, where it lives, what it does, **and** a polished replacement that folds in extra safety checks, UX niceties, and extensibility. Feel free to copy‑paste straight into your repo.

| Path                                                                   | Purpose                                          | Key QoL Upgrades                                                                                                                                    |
| ---------------------------------------------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scripts/pr_check.sh`                                                  | One‑shot environment validator                   |  • Detects dirty working tree<br>• Auto‑detects default branch (no hard‑coded `main`)<br>• Colourful pass/fail output                               |
| `.githooks/pre‑push`                                                   | Local guardrail — blocks bad pushes              |  • Runs only when Python files changed<br>• Graceful fallback if Sourcery CLI missing<br>• Uses `--patch` to restrict analysis to staged diff       |
| `shell/auto_pr_to_sourcery.sh` (_sourced in `~/.zshrc` / `~/.bashrc`_) | One‑command helper: push → PR → trigger Sourcery |  • `AUTO_PR_BASE` env var overrides default branch<br>• Adds “Sourcery‑Auto” label to PR<br>• Opens PR in browser unless `--no-browser` flag passed |
| `.github/workflows/sourcery-review.yml`                                | CI enforcement                                   |  • Concurrency group to cancel superseded runs<br>• Caches `pip` deps for speed<br>• Uploads Sourcery JSON report as artifact + PR summary comment  |
| `README.md` snippet                                                    | Developer guide                                  |  • Troubleshooting tips & FAQ<br>• Quick‑link to enable Git hooks on clone (`core.hooksPath`)                                                       |
| `docs/Hybrid‑Workflow‑Roadmap.md`                                      | Living checklist                                 |  • Final status table with ✅ marks and links to files                                                                                              |

# Hybrid Sourcery Workflow — Minimal Tasklist

| #   | Task                                                          | Output Artifact    | Status     |
| --- | ------------------------------------------------------------- | ------------------ | ---------- |
| 1   | Confirm prerequisites (✔ `gh`, Sourcery app, non‑main branch) | optional checklist | ⏳ pending |
| 2   | Add                                                           |                    |            |

| **local **\`\`** hook** to run Sourcery and block bad code | `.githooks/pre‑push` shell script                        | ✅ completed                            |            |
| ---------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------- | ---------- |
| 3                                                          | Add Bash helper `auto_pr_to_sourcery()` to shell profile | function snippet                        | ⏳ pending |
| 4                                                          | Add GitHub Action workflow for PR reviews                | `.github/workflows/sourcery-review.yml` | ⏳ pending |
| 5                                                          | (Optional) Setup‑verification script                     | `scripts/check_prereqs.sh`              | ⏳ pending |

---

## Task 2 — Local `pre‑push` Hook **(Completed)**

**Install**

1. Place the script below at \`\`.
2. Make it executable: `chmod +x .githooks/pre‑push`.
3. Point Git to the custom hooks dir: `git config core.hooksPath .githooks`.

```bash
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
```

Hook now enforces Sourcery standards **before** code reaches the remote—completing Task 2.

## Task 3 — Bash Helper `auto_pr_to_sourcery()` **(Completed)**

Drop the function below into your shell profile (`~/.zshrc`, `~/.bashrc`, or a shared script in your dotfiles). It:

1. Checks you aren’t on `main`/`master`.
2. Ensures the branch has commits that aren’t yet on origin.
3. Pushes the branch upstream (creating the remote if needed).
4. Opens a Pull Request against `main` via the GitHub CLI.
5. Relies on the Sourcery GitHub App to auto‑review the PR.

```bash
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
```

**Installation**

1. Copy the block into your preferred rc‑file.
2. Reload your shell: `source ~/.zshrc` (or equivalent).

**Usage**

```bash
auto_pr_to_sourcery
```

The command is idempotent—re‑running on the same branch simply opens the existing PR.

---

```yaml
name: Sourcery Review CI

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  sourcery:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Sourcery CLI
        run: pip install --upgrade sourcery

      - name: Run Sourcery review on diff
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} # default token; ensures PR inline comments
        run: |
          # Review only the diff between PR HEAD and merge base (target branch)
          sourcery review . \
            --head "${{ github.event.pull_request.head.sha }}" \
            --base "${{ github.event.pull_request.base.sha }}"

      # Optional: auto‑commit Sourcery suggestions back to the PR branch
      - name: Commit auto‑fixes (if any)
        if: ${{ success() }}
        run: |
          git config --global user.name "github-actions"
          git config --global user.email "action@github.com"
          git add -A
          git diff --cached --quiet && echo "No Sourcery fixes to commit." || {
            git commit -m "style: apply Sourcery fixes";
            git push;
          }
```

### Task 2 complete — local **`pre‑push`** hook script is ready and the roadmap is updated.

Next up (Task 3): the `auto_pr_to_sourcery()` bash helper. Let me know when to proceed.

---

## Task 3 — Bash Helper `auto_pr_to_sourcery()` **(Completed)**

Drop the function below into your shell profile (`~/.zshrc`, `~/.bashrc`, or a shared script in your dotfiles). It:

1. Checks you aren’t on `main`/`master`.
2. Ensures the branch has commits that aren’t yet on origin.
3. Pushes the branch upstream (creating the remote if needed).
4. Opens a Pull Request against `main` via the GitHub CLI.
5. Relies on the Sourcery GitHub App to auto‑review the PR.

```bash
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
```

**Installation**

1. Copy the block into your preferred rc‑file.
2. Reload your shell: `source ~/.zshrc` (or equivalent).

**Usage**

```bash
auto_pr_to_sourcery
```

The command is idempotent—re‑running on the same branch simply opens the existing PR.

---

### Task 3 is now fully implemented in the canvas as **“Task 3 — Bash Helper `auto_pr_to_sourcery()`.”**

Review the code, add it to your shell profile, and we’ll move on to Task 4 (GitHub Action workflow) when you’re ready.

---

```bash
name: Sourcery Review CI

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  sourcery:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Sourcery CLI
        run: pip install --upgrade sourcery

      - name: Run Sourcery review on diff
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # default token; ensures PR inline comments
        run: |
          # Review only the diff between PR HEAD and merge base (target branch)
          sourcery review . \
            --head "${{ github.event.pull_request.head.sha }}" \
            --base "${{ github.event.pull_request.base.sha }}"

      # Optional: auto‑commit Sourcery suggestions back to the PR branch
      - name: Commit auto‑fixes (if any)
        if: ${{ success() }}
        run: |
          git config --global user.name "github-actions"
          git config --global user.email "action@github.com"
          git add -A
          git diff --cached --quiet && echo "No Sourcery fixes to commit." || {
            git commit -m "style: apply Sourcery fixes";
            git push;
          }
```

### Task 4 complete — GitHub Action **`sourcery-review.yml`** is ready in the canvas.

Once this is committed to `.github/workflows/`, every PR will automatically run Sourcery in CI.

---

### 1 ⃣ `scripts/pr_check.sh`  (updated)

```bash
#!/usr/bin/env bash
# -----------------------------------------------------------
# Hybrid Sourcery Workflow – prerequisite checker
# -----------------------------------------------------------

# 1. Verifies you are _not_ on main / master.
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

```

---

### 2 ⃣ `.githooks/pre‑push`  (updated)

```bash
#!/usr/bin/env bash
# Run Sourcery on staged Python changes; block push on issues.

set -euo pipefail
files_changed=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.py$' || true)
[[ -z "$files_changed" ]] && exit 0  # nothing to review

if ! command -v sourcery &>/dev/null; then
  echo "⚠️  Sourcery CLI not found – skipping pre‑push check."
  exit 0
fi

echo "🔮  Running Sourcery review on staged diff…"
if ! git diff --cached | sourcery review --patch - ; then
  echo "❌  Sourcery flagged issues. Commit fixes or use --no-verify to bypass."
  exit 1
fi
echo "✅  Sourcery passed."
```

_Enable it once per repo:_

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-push
```

---

### 3 ⃣ `shell/auto_pr_to_sourcery.sh`  (updated)

```bash
auto_pr_to_sourcery() {
  local default_branch base branch
  default_branch=$(git symbolic-ref --quiet refs/remotes/origin/HEAD \
                    | sed 's@^refs/remotes/origin/@@') || default_branch=main
  base="${AUTO_PR_BASE:-$default_branch}"
  branch=$(git symbolic-ref --short HEAD)

  if [[ "$branch" == "$base" ]]; then
    echo "❌  You’re on $base. Checkout a feature branch first."
    return 1
  fi

  if ! git diff --quiet --exit-code; then
    echo "💾  Committing unstaged changes..."
    git add -A && git commit -m 'WIP: Auto‑commit before PR'
  fi

  echo "🚀  Pushing $branch..."
  git push -u origin "$branch"

  echo "📝  Creating Pull Request..."
  gh pr create \
      --base "$base" \
      --head "$branch" \
      --title "${branch//-/ }" \
      --label "Sourcery‑Auto" \
      --body "Automated PR via \`auto_pr_to_sourcery\`"

  [[ "$1" == "--no-browser" ]] || gh pr view --web
}
```

Add to `~/.zshrc` or `~/.bashrc`, then `source` the file.

---

### 4 ⃣ `.github/workflows/sourcery-review.yml`  (updated)

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
        with: { python-version: "3.12" }

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

---

### 5 ⃣ README Insert  (updated)

```markdown
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
| _“gh: no auth token”_   | `gh auth login` and choose HTTPS w/ pat                   |
| _Pre‑push skips review_ | Ensure Sourcery CLI is installed (`pip install sourcery`) |
```

---

### What’s Next?

1. **Copy each file** into your repo at the indicated paths.
2. `chmod +x` any shell scripts / hooks.
3. On first clone, run `git config core.hooksPath .githooks`.
4. Enjoy zero‑touch, continuously‑reviewed PRs!

Feel free to ask for more tweaks or extra tooling (e.g., Slack/Discord PR notifications, automatic changelog generation, etc.).

---

# Hybrid Sourcery Workflow — Minimal Tasklist

| #   | Task                                                          | Output Artifact    | Status     |
| --- | ------------------------------------------------------------- | ------------------ | ---------- |
| 1   | Confirm prerequisites (✔ `gh`, Sourcery app, non‑main branch) | optional checklist | ⏳ pending |
| 2   | Add                                                           |                    |            |

| **local **\`\`** hook** to run Sourcery and block bad code | `.githooks/pre‑push` shell script                        | ✅ completed                            |            |
| ---------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------- | ---------- |
| 3                                                          | Add Bash helper `auto_pr_to_sourcery()` to shell profile | function snippet                        | ⏳ pending |
| 4                                                          | Add GitHub Action workflow for PR reviews                | `.github/workflows/sourcery-review.yml` | ⏳ pending |
| 5                                                          | (Optional) Setup‑verification script                     | `scripts/check_prereqs.sh`              | ⏳ pending |

---

## Task 2 — Local `pre‑push` Hook **(Completed)**

**Install**

1. Place the script below at \`\`.
2. Make it executable: `chmod +x .githooks/pre‑push`.
3. Point Git to the custom hooks dir: `git config core.hooksPath .githooks`.

```bash
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
```

Hook now enforces Sourcery standards **before** code reaches the remote—completing Task 2.

Here’s a **single‑file, copy‑ready Python CLI** you can drop into your repo (e.g. `tools/prmilker.py`) and run with `python tools/prmilker.py`.
It bundles every option we discussed into an interactive menu—no extra dependencies beyond the standard library.

```python
#!/usr/bin/env python3
"""
sourcery_cli.py
────────────────
Interactive CLI to manage a Sourcery‑integrated workflow.

Menu options
1. Push current branch and open Pull Request (auto‑PR)
2. Run local Sourcery review on staged diff (pre‑push guard)
3. Run environment check (gh auth, branch safety, Sourcery app)
4. Quit
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# ───────────────── helpers ──────────────────


def sh(cmd: str, check: bool = True, capture: bool = False) -> str:
    """Run shell command and return stdout (if capture=True)."""
    kwargs = dict(shell=True, check=check)
    if capture:
        kwargs.update(text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = subprocess.run(cmd, **kwargs)
    return result.stdout.strip() if capture else ""


def default_branch() -> str:
    ref = sh(
        "git symbolic-ref --quiet refs/remotes/origin/HEAD",
        check=False,
        capture=True,
    )
    return ref.rsplit("/", 1)[-1] if ref else "main"


def current_branch() -> str:
    return sh("git symbolic-ref --short HEAD", capture=True)


def is_dirty() -> bool:
    return bool(sh("git status --porcelain", capture=True))


def pause():
    input("\nPress ⏎ to continue…")


# ───────────────── tasks ─────────────────────


def env_check():
    ok = True
    base = default_branch()
    branch = current_branch()

    if branch == base:
        print(f"✖  You’re on {base}. Checkout a feature branch first.")
        ok = False
    if is_dirty():
        print("✖  Working tree is dirty. Commit or stash changes.")
        ok = False

    if sh("gh auth status", check=False) != "":
        pass  # gh is authenticated
    else:
        print("✖  GitHub CLI not authenticated. Run: gh auth login")
        ok = False

    repo = sh(
        "git config --get remote.origin.url", capture=True
    ).removesuffix(".git").split("github.com")[-1].lstrip(":/")
    sourcery = sh(f"gh api repos/{repo}/installation", check=False)
    if not sourcery:
        print("✖  Sourcery GitHub App not installed on this repo.")
        ok = False

    print("✔  All environment checks passed." if ok else "‼  Fix issues above.")
    pause()


def pre_push_guard():
    if not Path(".git").exists():
        print("✖  Run this inside a Git repo.")
        return
    if sh("command -v sourcery", check=False) == "":
        print("⚠  Sourcery CLI not found; install with pip if you want local checks.")
        return

    staged = sh(
        "git diff --cached --name-only --diff-filter=ACMR | grep -E '\\.py$' || true",
        capture=True,
    )
    if not staged:
        print("✓  No staged Python files → nothing to review.")
        pause()
        return

    print("🔮  Running Sourcery on staged diff…")
    diff = sh("git diff --cached", capture=True)
    proc = subprocess.run(
        ["sourcery", "review", "--patch", "-"],
        input=diff.encode(),
        text=False,
    )
    if proc.returncode == 0:
        print("  Sourcery passed.")
    else:
        print("  Sourcery flagged issues. Amend commit or bypass with --no-verify.")
    pause()


def auto_pr(open_browser: bool = True):
    base = default_branch()
    branch = current_branch()

    if branch == base:
        print(f"✖  You’re on {base}. Checkout a feature branch first.")
        pause()
        return

    if is_dirty():
        print("  Committing unstaged changes…")
        sh('git add -A && git commit -m "Auto‑commit before PR"')

    print(f"  Pushing {branch}…")
    sh(f"git push -u origin {branch}")

    print("  Creating Pull Request…")
    cmd = (
        f'gh pr create --base "{base}" --head "{branch}" '
        f'--title "{branch.replace("-", " ")}" '
        f'--label "sourcery" '
        f'--body "Automated PR from `{branch}`"'
    )
    sh(cmd)
    if open_browser:
        sh("gh pr view --web")
    pause()


# ───────────────── menu ──────────────────────


def menu():
    actions = {
        "1": ("Push branch & open PR", auto_pr),
        "2": ("Run local Sourcery review (pre‑push)", pre_push_guard),
        "3": ("Env checker", env_check),
        "4": ("Quit", sys.exit),
    }
    while True:
        print(
            "\n=== Sourcery Workflow CLI ===\n"
            "1. Push branch & open PR\n"
            "2. Run local Sourcery review (pre‑push)\n"
            "3. Env checker\n"
            "4. Quit"
        )
        choice = input("> ").strip()
        action = actions.get(choice)
        if action:
            action[1]()  # run the selected function
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n  Exiting.")
```

**Usage**

```bash
python tools/sourcery_cli.py
```

When the menu appears, hit **1** to push & PR, **2** for a quick local Sourcery diff review, **3** for a health check, **4** to quit. Nothing else touches your workflow unless you choose it.
