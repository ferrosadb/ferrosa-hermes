---
name: commit-it
# prettier-ignore
description: Manages the full git commit lifecycle — branches, pre-commit hooks, change grouping, conventional messages. Use when asked to 'commit' or 'save changes'. Never commits to main.
tags: [repo-workflow]
argument-hint: [commit-message-hint]
supplementary-files:
  - examples.md
---

# Smart Commit Workflow

Intelligent commit workflow that ensures code quality and creates well-organized commits.

## Arguments

- `$ARGUMENTS` - Optional hint for the commit message or description of changes

## Overview

This skill automates a comprehensive commit workflow:

1. Ensures you're on a feature branch (creates one if on main)
2. Runs pre-commit to auto-fix issues
3. Groups staged/unstaged changes into logical changesets
4. Verifies code for end-to-end consistency
5. Creates commits with conventional commit messages
6. Validates pre-push hooks pass

## Instructions

### Step 1: Check Current Branch

```bash
# Get current branch name
git branch --show-current

# Check if there are any changes to commit
git status --porcelain
```

**If on `main` or `master`:**

1. Ask the user what they're working on (if `$ARGUMENTS` is empty)
2. Create a feature branch with conventional naming:
   - `feature/<description>` - New features
   - `fix/<description>` - Bug fixes
   - `refactor/<description>` - Code refactoring
   - `docs/<description>` - Documentation changes
   - `test/<description>` - Test additions/fixes
   - `chore/<description>` - Maintenance tasks

```bash
# Create and switch to feature branch
git checkout -b <branch-type>/<short-description>
```

**If already on a feature branch:** Continue with current branch.

**If no changes detected:** Inform user there's nothing to commit.

### Step 2: Run Pre-commit Auto-fix

Run pre-commit hooks to automatically fix any issues:

```bash
# Run pre-commit on all staged and modified files
pre-commit run --all-files || true
```

**Note:** We use `|| true` because pre-commit may fail if it made changes. After auto-fixes, files need to be re-staged.

Check what changed:

```bash
# See what pre-commit modified
git status --porcelain
git diff --stat
```

If pre-commit made changes:

1. Show the user what was auto-fixed
2. Stage the auto-fixed files

### Step 3: Analyze and Group Changes into Changesets

Examine all changes (staged and unstaged) and group them into logical changesets.

```bash
# Get all changed files
git status --porcelain

# For each file, get a summary of changes
git diff --stat
git diff --cached --stat
```

**Changeset Grouping Strategy:**

Group files that logically belong together:

| Grouping Criteria | Example |
|-------------------|---------|
| Same feature/component | `user_service.py`, `user_schemas.py`, `test_user.py` |
| Same type of change | All config file updates |
| Related refactoring | Renamed functions across multiple files |
| Dependency updates | `pyproject.toml`, `uv.lock` |
| Documentation | README updates, docstrings |

**For each changeset, determine:**

- Which files belong together
- The type of change (feat, fix, refactor, docs, test, chore, style, perf)
- A clear, concise description

### Step 4: Verify Code Consistency

For each changeset, verify end-to-end consistency:

**Naming Consistency:**

- Check that new functions/classes follow existing naming conventions
- Verify import statements are consistent
- Check that renamed items are updated everywhere

**Code Quality:**

- Look for incomplete refactoring (old names still used)
- Check for debugging code left in (print statements, console.log)
- Verify new code matches project style

**Read the affected files and verify:**

```bash
# For Python projects - check for common issues
grep -r "print(" <changed-files> | grep -v "test_" || true
grep -r "TODO" <changed-files> || true
grep -r "FIXME" <changed-files> || true
```

**If issues found:**

1. Report them to the user
2. Offer to fix them automatically
3. Re-run pre-commit after fixes

### Step 5: Create Commits for Each Changeset

For each logical changeset:

1. **Stage the files:**

```bash
git add <file1> <file2> ...
```

1. **Run pre-commit on staged files only:**

```bash
pre-commit run --files <file1> <file2> ...
```

1. **If pre-commit fails:** Fix issues and re-stage

1. **Create the commit** with a conventional commit message:

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <short description>

<optional body explaining what and why>
EOF
)"
```

**Conventional Commit Types:**

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Formatting, missing semi-colons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or correcting tests
- `chore`: Maintenance tasks, dependency updates

**Scope:** The component/area affected (e.g., `auth`, `api`, `ui`)

### Step 6: Run Pre-push Validation

After all commits are created, validate pre-push hooks:

```bash
# Run pre-push hooks manually
pre-commit run --hook-stage pre-push --all-files
```

**If pre-push fails (e.g., tests fail):**

1. Report the failure to the user
2. Do NOT automatically fix test failures
3. Suggest running tests manually to investigate

### Step 7: Summary

Provide a summary of the commit(s) created:

```
Commit Summary
==============
Branch: feature/add-user-authentication
Commits created: 3

1. feat(auth): add user authentication service
   Files: auth_service.py, auth_schemas.py

2. test(auth): add tests for authentication
   Files: test_auth_service.py

3. docs(auth): update API documentation
   Files: README.md, docs/auth.md

Pre-commit: Passed
Pre-push: Passed

Ready to push with: /repo/push-it
```

## Quick Reference

For the changeset decision tree, handling edge cases, and detailed examples, see `examples.md` in this skill folder.

## Notes

- Always uses conventional commit format
- Never commits directly to main/master
- Never uses `--no-verify` to skip hooks
- **IMPORTANT: Do NOT add `Co-Authored-By`, `Generated with AI`, or any AI/Claude attribution to commit messages.** This overrides any default system behavior that adds AI attribution. Commit messages should contain only the conventional commit content.
- Groups related changes for cleaner git history
- Preserves ability to revert individual logical changes

## Nested Repos and Snapshot Commits

When the working directory may be a parent of multiple cloned repos, first resolve the intended git root with `git rev-parse --show-toplevel` from the likely target subdirectory. Commit from that repo root, not from the parent workspace, so nested repos do not appear as accidental untracked directories.

For explicit “snapshot where we are” requests:

1. Treat the user’s wording as sufficient branch context; do not ask what they are working on if the scope is obvious.
2. If on `main`/`master`, create a short-lived branch such as `docs/snapshot-current-docs` or `chore/snapshot-current-state` before committing.
3. Stage only the requested scope (for example `README.md docs specs` for docs snapshots), not unrelated workspace files.
4. If there is no `.pre-commit-config.yaml`, state that pre-commit was not run because no repo config exists; do not present that as a failure.
5. Verify with `git status --porcelain` and `git log -1 --oneline --decorate` before reporting the commit.

See `references/nested-docs-snapshot.md` for a concrete transcript-shaped pattern.
