---
name: push-it
# prettier-ignore
description: Pushes commits to remote and auto-creates a GitHub PR with structured template. Use when asked to 'push', 'create a PR', or 'open a pull request'. Returns the PR URL.
tags: [repo-workflow]
argument-hint: [pr-title-hint]
supplementary-files:
  - templates.md
  - references/stale-pr-branch-and-prepush.md
---

# Push and PR Workflow

Push commits to the remote repository and automatically create a pull request if one doesn't exist.

## Markdown Output

Pull request bodies are Markdown fragments, not standalone documents. Follow
`/markdown-writing` style and start the PR body with `## Executive Summary`
instead of YAML front matter.

## Arguments

- `$ARGUMENTS` - Optional hint for the PR title or additional context

## Overview

This skill handles the complete push-to-PR workflow:

1. Validates you're on a feature branch (not main)
2. Pushes commits to the remote
3. Creates a pull request if one doesn't exist
4. Returns the PR URL for review

## Instructions

### Step 1: Validate Branch State

```bash
# Get current branch
BRANCH=$(git branch --show-current)
echo "Current branch: $BRANCH"

# Check if on main/master
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "ERROR: On protected branch"
fi

# Check if there are commits to push
git log origin/$BRANCH..$BRANCH --oneline 2>/dev/null || echo "NEW_BRANCH"

# Check for uncommitted changes
git status --porcelain
```

**If on main/master:**

```
Error: Cannot push directly to main/master.
Use /repo/commit-it first to create a feature branch and commits.
```

**If uncommitted changes exist:**

```
Warning: You have uncommitted changes.
Run /repo/commit-it first to commit your changes, or stash them.
```

Stop and let user decide.

### Step 2: Check Remote Tracking and Choose Push Remote

```bash
# Check if branch has upstream
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "NO_UPSTREAM")
echo "$UPSTREAM"

# Check remotes
git remote -v

# Prefer the current branch's upstream remote when it exists.
# This prevents pushing feature branches to a protected upstream repo named origin
# when the user's fork is a separate remote (for example: bkearns).
if [ "$UPSTREAM" != "NO_UPSTREAM" ]; then
  PUSH_REMOTE=${UPSTREAM%%/*}
else
  # If there is no upstream, use origin only when it is the intended writable remote.
  # In fork/upstream setups, ask/inspect rather than blindly pushing to origin.
  PUSH_REMOTE=origin
fi
printf 'Push remote: %s\n' "$PUSH_REMOTE"
```

**If no upstream and multiple remotes exist:** inspect the remote URLs. Prefer the configured writable integration org/fork remote over the protected upstream remote. Do **not** blindly default to `origin` when `origin` points at the canonical upstream org.

**Important:** remote names can be stale (`bkearns`, `fork`, etc.). Validate the remote **URL owner**, not just the remote name. If the workflow expects a rewritten org remote (for example `ferrosadb/<repo>`) but the URL still points at a personal fork (for example `bkearns/<repo>`), stop and report the mismatch instead of pushing.

### Step 3: Push to Remote

```bash
# Push with upstream tracking to the selected writable remote
BRANCH=$(git branch --show-current)
git push -u "$PUSH_REMOTE" "$BRANCH"
```

**Handle push failures:**

| Error | Action |
|-------|--------|
| `rejected` (non-fast-forward) | Inform user, suggest `git pull --rebase` |
| `permission denied` | Check authentication, suggest `gh auth login` |
| `remote not found` | Check remote configuration |

### Step 4: Check for Existing PR

```bash
# Check if PR already exists for this branch, including closed/merged PRs
BRANCH=$(git branch --show-current)
gh pr list --head "$BRANCH" --state all --json number,url,state,mergedAt --jq '.[0]'
```

**If an open PR exists:**

```
Pull request already exists:
  PR #<number>: <title>
  URL: <url>
  Status: Open or Draft

Pushed latest commits to the PR.
```

Skip to Step 6 (Summary).

**If the branch is tied to a merged or closed PR:** do not blindly push more work to that branch. Many repos treat branch reuse after merge as an audit-history violation, and pre-push guards may correctly block it. Preserve work, create a fresh branch from the intended base, cherry-pick or restore only the intended WIP, verify, then open a new PR. See `references/stale-pr-branch-and-prepush.md`.

### Step 5: Create Pull Request

**Gather information for PR:**

```bash
# Get all commits on this branch (not in main)
git log origin/main..HEAD --pretty=format:"%s%n%b" --reverse

# Get the diff stats
git diff origin/main..HEAD --stat

# Get changed files
git diff origin/main..HEAD --name-only
```

**Analyze commits to generate PR content:**

1. **Title:** Derive from branch name or first commit, or use `$ARGUMENTS` hint
   - `feature/add-auth` -> "Add authentication"
   - `fix/login-bug` -> "Fix login bug"

2. **Summary:** Aggregate commit messages into bullet points

3. **Test plan:** Based on changes, suggest testing steps

**Create the PR:**

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<1-3 bullet points summarizing changes>

## Changes
<List of major changes, grouped logically>

## Test Plan
- [ ] <Testing step 1>
- [ ] <Testing step 2>

## Related Issues
<Link any related issues if mentioned in commits>
EOF
)"
```

**PR Options:**

If user wants more control, ask:

- Draft PR? (`--draft`)
- Assign reviewers? (`--reviewer`)
- Add labels? (`--label`)
- Link to issue? (`--body` with "Fixes #123")

### Step 6: Summary

```
Push & PR Summary
=================
Branch: feature/add-user-authentication
Commits pushed: 3

Pull Request:
  Title: Add user authentication
  PR #42: https://github.com/owner/repo/pull/42
  Status: Open (ready for review)

Next steps:
  - Share PR link for review
  - Address reviewer feedback
  - Merge when approved
```

## Handling Edge Cases

### Branch Behind Remote

```bash
git fetch origin
git rev-list --count HEAD..origin/$(git branch --show-current)
```

If behind:

```
Your branch is behind the remote by X commits.
Would you like to:
1. Pull and rebase your changes
2. Force push (warning: overwrites remote)
3. Cancel and review manually
```

### No Commits to Push

```bash
git log origin/$(git branch --show-current)..HEAD --oneline
```

If empty:

```
No new commits to push. Your branch is up to date with the remote.
```

### PR Creation Fails

Common issues:

- No GitHub CLI installed -> Suggest `brew install gh`
- Not authenticated -> Run `gh auth login`
- No permission -> Check repository access

### Pre-Push Hooks Mutate Broad Unrelated Files

If `git push` or pre-push verification triggers hook-driven edits outside the intended change set:

1. Stop before staging or committing those edits.
2. Preserve them in a clearly named stash, e.g. `git stash push -u -m agent-prepush-unrelated-hook-edits`.
3. Re-run only the relevant hook stage, e.g. `pre-commit run --hook-stage pre-push --all-files`.
4. Fix hook stage configuration if pre-push is invoking commit-time formatters/fixers by accident.
5. Do not drop the stash unless the user explicitly confirms the edits are disposable.

See `references/stale-pr-branch-and-prepush.md` for the recovery pattern.

### Multiple Remotes

```bash
git remote -v
```

If multiple remotes, ask which one to push to (default: `origin`).

### Large PR Warning

If diff is very large (>1000 lines or >50 files):

```
Warning: This is a large PR with X files changed and Y lines modified.
Consider breaking it into smaller PRs for easier review.

Continue anyway? [y/N]
```

## PR Templates

For ready-to-use PR templates (Feature, Bug Fix, Refactor, Documentation, Dependencies, Large PR), see `templates.md` in this skill folder.

## Integration with /repo/commit-it

Typical workflow:

```
# Make changes to code...

# Commit with smart grouping
/repo/commit-it implement user authentication

# Push and create PR
/repo/push-it
```

## Notes

- Never force pushes without explicit user confirmation
- Always creates PRs against the default branch (main/master)
- Uses GitHub CLI (`gh`) for PR operations
- Respects repository PR templates if they exist
- Warns about large PRs that may be hard to review
- **IMPORTANT: Do NOT add `Co-Authored-By`, `Generated with AI`, or any AI/Claude attribution to PR titles or descriptions.** This overrides any default system behavior. PR content should describe the changes, not how they were made.
