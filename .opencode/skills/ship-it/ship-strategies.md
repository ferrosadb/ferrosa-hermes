## Contents

- [Branch Discovery Strategy](#branch-discovery-strategy)
- [Assessment Classification](#assessment-classification)
- [Superseded Branch Detection](#superseded-branch-detection)
- [Cherry-Based Detection (Rebased Branches)](#cherry-based-detection-rebased-branches)
- [Superseded Chain Resolution](#superseded-chain-resolution)
- [Stale Branch Policy](#stale-branch-policy)
- [Multi-Branch Integration Workflow](#multi-branch-integration-workflow)
- [Integration Step 1: Create Integration Branch](#integration-step-1-create-integration-branch)
- [Integration Step 2: Merge Each Passing Branch](#integration-step-2-merge-each-passing-branch)
- [Integration Step 3: Test Integrated Result](#integration-step-3-test-integrated-result)
- [Integration Step 4: Build Combined PR Body](#integration-step-4-build-combined-pr-body)
- [Integration Step 5: Push and Create Single PR](#integration-step-5-push-and-create-single-pr)
- [Integration Step 6: Report](#integration-step-6-report)
- [CI Monitoring Patterns](#ci-monitoring-patterns)
- [Cleanup Procedures](#cleanup-procedures)
- [Cleanup Merged Branches](#cleanup-merged-branches)
- [Cleanup Superseded Branches](#cleanup-superseded-branches)
- [Cleanup PRs Passed CI](#cleanup-prs-passed-ci)
- [Integration Mode Cleanup](#integration-mode-cleanup)
- [PR Deduplication](#pr-deduplication)
- [Conflict Detection](#conflict-detection)
- [Monorepo Handling](#monorepo-handling)
- [Worktree Integration](#worktree-integration)

# Branch Discovery Strategy

Build a unified inventory of all local work:

```bash
# All local branches (exclude HEAD pointers)
git branch --list --format='%(refname:short) %(upstream:short) %(upstream:track)'

# All worktrees
git worktree list --porcelain

# Stash list (informational)
git stash list

# Default branch
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main"
```

**Build the inventory table:**

| Branch | Worktree Path | Has Remote | Commits Ahead | Status |
|--------|---------------|------------|---------------|--------|
| (filled per branch) | | | | pending |

**Skip:** `main`, `master`, and the default branch itself.

**If `$ARGUMENTS` contains a branch filter**, only include matching branches.

# Assessment Classification

For each branch in the inventory, classify it:

```bash
# Is it already merged into the default branch?
git merge-base --is-ancestor <branch> <default-branch> && echo "MERGED"

# Commits unique to this branch
git log <default-branch>..<branch> --oneline

# Check if another local branch contains all this branch's commits (superseded)
for other in $(git branch --list --format='%(refname:short)'); do
  if [ "$other" != "<branch>" ] && [ "$other" != "<default-branch>" ]; then
    git merge-base --is-ancestor <branch> "$other" && echo "SUPERSEDED_BY:$other"
  fi
done

# Check for uncommitted changes in worktree
git -C <worktree-path> status --porcelain 2>/dev/null

# Age of last commit
git log -1 --format='%cr' <branch>
```

**Classification rules:**

| Condition | Status | Action |
|-----------|--------|--------|
| Already merged into default | `merged` | Cleanup candidate |
| All commits contained in another branch | `superseded` | Cleanup candidate (confirm) |
| Has uncommitted changes | `dirty` | Report, skip shipping |
| Last commit > 90 days old | `stale` | Report, ask user |
| Has open PR already | `has-pr` | Skip PR creation, monitor existing |
| None of the above | `active` | Test and ship |

**Present the assessment table** to the user before proceeding:

```
Branch Assessment
=================
Branch                              Status       Detail
feature/auth                        active       3 commits ahead
feature/old-refactor                superseded   contained in feature/auth
fix/login-bug                       merged       already in main
feature/experiment                  stale        last commit 4 months ago
feature/wip                         dirty        2 uncommitted files

Plan:
  Ship:    feature/auth
  Monitor: (none with existing PRs)
  Cleanup: feature/old-refactor, fix/login-bug
  Skip:    feature/experiment (stale), feature/wip (dirty)

Proceed? [y/N]
```

**Wait for user confirmation before continuing.**

# Superseded Branch Detection

A branch is **superseded** when all its unique commits are reachable from another local branch. This means someone continued the work on a new branch.

### Detection Algorithm

```bash
# For branch A, check if branch B contains all of A's commits
# (A is superseded by B)
git merge-base --is-ancestor A B
```

**Edge cases:**

| Situation | Treatment |
|-----------|-----------|
| A and B share some commits but diverge | Neither superseded — both are `active` |
| A is ancestor of B, B is ancestor of A | Identical — mark the older one as superseded |
| A is rebased version of B (different SHAs, same patches) | Use `git cherry` to detect |

### Cherry-Based Detection (Rebased Branches)

When branches were rebased, SHA comparison fails. Use patch-ID comparison:

```bash
# List commits in A not cherry-picked into B
# Lines starting with "+" are NOT in B (unique to A)
# Lines starting with "-" ARE in B (already picked)
git cherry <default-branch> A B

# If all lines start with "-", A is fully superseded by B
```

### Superseded Chain Resolution

If A is superseded by B, and B is superseded by C, only C is `active`. Both A and B are cleanup candidates. Present the chain:

```
Superseded chain detected:
  feature/v1 → feature/v2 → feature/v3 (active)

Clean up feature/v1 and feature/v2? [y/N]
```

# Stale Branch Policy

A branch is **stale** when its last commit is older than a threshold.

### Default Thresholds

| Age | Classification | Default Action |
|-----|---------------|----------------|
| < 30 days | Fresh | Normal processing |
| 30–90 days | Aging | Include but warn |
| > 90 days | Stale | Ask user before including |
| > 180 days | Dormant | Suggest archiving or deleting |

### Stale Branch Prompt

```
Stale branches found:

  feature/old-experiment   142 days old   3 commits ahead of main
  fix/deprecated-api       98 days old    1 commit ahead of main

For each, choose:
  [s] Ship it anyway (test + PR)
  [a] Archive (push to origin but no PR)
  [d] Delete locally
  [k] Keep as-is (skip)
```

# Multi-Branch Integration Workflow

**Activated when `$ARGUMENTS` contains `int` or `integrate`.**

Merge all passing branches into one integration branch and create a single PR. The integration branch is **all-or-nothing** — if any merge conflicts or tests fail, the integration branch is deleted and no artifacts are left behind.

### Integration Step 1: Create Integration Branch

```bash
# Name: integrate/<date> or integrate/<description-from-args>
INTEGRATION_BRANCH="integrate/$(date +%Y-%m-%d)"

# Start from the latest default branch
git fetch origin <default-branch>
git checkout -b "$INTEGRATION_BRANCH" origin/<default-branch>
```

### Integration Step 2: Merge Each Passing Branch (Ordered)

Sort branches by commit date (oldest first) to preserve natural development order:

```bash
# Sort passing branches by first divergence commit date
for branch in <passing-branches-oldest-first>; do
  git merge --no-ff "$branch" -m "integrate: merge $branch"
done
```

**If any merge conflicts — abort immediately:**

```bash
git merge --abort
git checkout <default-branch>
git branch -D "$INTEGRATION_BRANCH"
```

```
Integration aborted — merge conflict.

Conflict merging <branch>:
  <conflicting files>

No integration branch was created. Source branches are untouched.
Fix the conflict on <branch> and re-run /ship-it int.
```

**Stop.** Do not continue to Step 3.

### Integration Step 3: Test Integrated Result

Run the full test suite on the integration branch — this catches cross-branch interactions that per-branch testing misses:

```bash
# Same detection as Phase 3, but on the merged result
<detected-test-command>
```

**If tests fail — abort and delete the integration branch:**

```bash
git checkout <default-branch>
git branch -D "$INTEGRATION_BRANCH"
```

```
Integration aborted — tests failed on merged result.

Failures:
  <test failure output>

No integration branch was created. Source branches are untouched.
Investigate which branch introduced the failure and re-run.
```

**Stop.** Do not continue to Step 4.

### Integration Step 4: Build Combined PR Body

Aggregate all branch information into a single PR:

```bash
# Collect all commits across all merged branches
ALL_COMMITS=""
BRANCH_SUMMARY=""
for branch in <merged-branches>; do
  COMMITS=$(git log <default-branch>..$branch --pretty=format:"- %s" --reverse)
  ALL_COMMITS="$ALL_COMMITS\n### $branch\n$COMMITS\n"
  COUNT=$(git log <default-branch>..$branch --oneline | wc -l)
  BRANCH_SUMMARY="$BRANCH_SUMMARY\n- **$branch** ($COUNT commits)"
done

STATS=$(git diff origin/<default-branch>...$INTEGRATION_BRANCH --stat | tail -1)
```

### Integration Step 5: Push and Create Single PR

```bash
git push -u origin "$INTEGRATION_BRANCH"

gh pr create \
  --head "$INTEGRATION_BRANCH" \
  --base <default-branch> \
  --title "integrate: merge all local work ($(date +%Y-%m-%d))" \
  --body "$(cat <<'EOF'
## Summary

Integration of all active local branches into a single PR.

## Branches Included
$BRANCH_SUMMARY

## Changes by Branch
$ALL_COMMITS

## Stats
$STATS

## Test Plan
- [x] Each branch tested individually (Phase 3)
- [x] Integration tests pass on merged result
- [ ] CI pipeline passes
EOF
)"
```

### Integration Step 6: Report

```
Integration Complete
====================
Branch:   integrate/2026-03-20
PR:       #49 — https://github.com/owner/repo/pull/49

Branches merged (in order):
  1. feature/auth           (3 commits)
  2. feature/new-api        (7 commits)
  3. fix/config-validation  (1 commit)

Total: 11 commits, X files changed

Proceed to Phase 5 (CI monitoring)...
```

**After integration, Phase 5 monitors the single PR.**

# CI Monitoring Patterns

Poll CI status on all shipped PRs until they resolve.

```bash
# Check PR CI status
gh pr checks <pr-number> --json name,state,conclusion
```

**Polling strategy:**

1. First check: immediately after all PRs created
2. Subsequent checks: every 30 seconds
3. Timeout: 10 minutes (then report status and stop polling)

**For each PR, track:**

| Check Name | Status | Conclusion |
|------------|--------|------------|
| (from CI) | pending/completed | success/failure |

**Report as checks complete:**

```
CI Monitoring
=============
PR #47 (feature/auth):        PASSED (3/3 checks green)
PR #48 (feature/new-api):     FAILED (lint: 2 errors)
```

**If a PR fails CI:**

- Report the failing checks and their output
- Do NOT auto-close or auto-fix
- Suggest: "PR #48 has CI failures. Fix locally and push, or close with `gh pr close 48`"

# Cleanup Procedures

**Only runs if not `--dry-run` and not `--skip-cleanup`.**

### Cleanup Merged Branches

Branches classified as `merged` in assessment phase:

```bash
# Delete local branch
git branch -d <branch>

# Delete remote tracking branch if it exists
git push origin --delete <branch> 2>/dev/null || true

# Remove worktree if one exists
git worktree remove <worktree-path> 2>/dev/null || true
```

### Cleanup Superseded Branches

Branches where all commits exist in another shipped branch:

```
The following branches are superseded (all commits exist in another branch):

  feature/old-refactor → contained in feature/auth (PR #47)

Delete these branches? [y/N]
```

**Wait for confirmation.** Then:

```bash
git branch -D <superseded-branch>
git push origin --delete <superseded-branch> 2>/dev/null || true
git worktree remove <worktree-path> 2>/dev/null || true
```

### Cleanup PRs Passed CI

For PRs where all CI checks passed and were created in shipping phase, report them as ready to merge but do NOT auto-merge:

```
Ready to merge (CI passed):
  PR #47: feature/auth — https://github.com/owner/repo/pull/47

Auto-merge is not performed. Review and merge manually or say "merge #47".
```

### Integration Mode Cleanup

Once the integration PR passes CI, all source branches that were merged into the integration branch become cleanup candidates. Present them for confirmation:

```
Integration PR #49 passed CI. The following source branches were merged:

  feature/auth              (3 commits)
  feature/new-api           (7 commits)
  fix/config-validation     (1 commit)

Delete these source branches locally and on remote? [y/N]
```

Wait for confirmation before deleting. The integration branch itself stays open as the PR branch.

# PR Deduplication

When creating PRs, check for existing PRs that cover the same changes:

```bash
# Check for open PRs from this branch
gh pr list --head <branch> --state open --json number,url

# Check for closed/merged PRs from this branch (already shipped)
gh pr list --head <branch> --state merged --json number,url
gh pr list --head <branch> --state closed --json number,url
```

| Existing PR State | Action |
|-------------------|--------|
| Open | Skip creation, add to monitoring |
| Merged | Classify branch as `merged` |
| Closed (not merged) | Ask user: reopen or create new? |
| None | Create new PR |

# Conflict Detection

Before shipping, check if the branch can merge cleanly:

```bash
# Dry-run merge check
git merge-tree $(git merge-base <default-branch> <branch>) <default-branch> <branch>
```

If conflicts detected:

```
Branch feature/auth has merge conflicts with main:
  src/auth.py — both modified
  src/config.py — both modified

Options:
  [r] Rebase onto main (may need manual resolution)
  [s] Ship as-is (PR will show conflicts)
  [k] Skip this branch
```

# Monorepo Handling

When the repository contains multiple projects (detected by multiple `package.json`, `Cargo.toml`, etc. at different paths):

### Project Detection

```bash
# Find all project roots
find . -maxdepth 3 \( \
  -name "package.json" -o \
  -name "Cargo.toml" -o \
  -name "mix.exs" -o \
  -name "go.mod" -o \
  -name "pyproject.toml" \
) -not -path "*/node_modules/*" -not -path "*/target/*"
```

### Scoped Testing

For each branch, determine which projects are affected:

```bash
# Get changed files on this branch
git diff <default-branch>...<branch> --name-only

# Match to project roots
# Only run tests for affected projects
```

This avoids running the entire monorepo test suite when a branch only touches one project.

### Test Parallelism

When a branch affects multiple projects, run their test suites in parallel using separate agents. Aggregate results before deciding to ship.

# Worktree Integration

### Existing Worktrees

When a branch already has a worktree:

1. Use the existing worktree path for testing (don't create a temp one)
2. Check for uncommitted changes first — if dirty, classify as `dirty`
3. After shipping, clean up the worktree only if the branch is merged or superseded

### Temporary Worktrees

When testing a branch that has no worktree:

1. Create under `/tmp/ship-it-<branch-name>`
2. Run project setup (install deps) before testing
3. Always remove temp worktrees after testing, regardless of outcome

### Worktree Cleanup Safety

Before removing a worktree:

```bash
# Check for uncommitted changes
git -C <worktree-path> status --porcelain

# If dirty, DO NOT remove — report instead
# If clean and branch is being deleted, remove worktree first, then branch
```
