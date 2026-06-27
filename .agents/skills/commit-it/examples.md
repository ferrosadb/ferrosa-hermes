# Commit Skill Examples

Examples and edge case handling for the smart commit workflow.

## Contents

- [Basic Examples](#basic-examples)
- [Changeset Decision Tree](#changeset-decision-tree)
- [Handling Edge Cases](#handling-edge-cases)
- [Commit Summary Template](#commit-summary-template)
- [Changeset Grouping Examples](#changeset-grouping-examples)
- [Conventional Commit Reference](#conventional-commit-reference)

## Basic Examples

### Simple single-feature commit

```
/repo/commit-it add login functionality
```

Creates: `feat(auth): add login functionality`

### Multiple related changes

```
/repo/commit-it
```

Analyzes all changes and creates multiple organized commits.

### Fix mode

```
/repo/commit-it fix the validation bug
```

Creates branch `fix/validation-bug` and commits with `fix:` prefix.

## Changeset Decision Tree

Use this to decide how to group changes:

```
Are all changes related to one feature/fix?
+-- Yes -> Single commit
+-- No -> Multiple commits
    +-- Group by component/module
    +-- Separate tests from implementation
    +-- Separate docs from code
    +-- Separate config changes
```

## Handling Edge Cases

### No Changes

```
No changes detected. Nothing to commit.
```

### Only Untracked Files

```bash
git status --porcelain | grep "^??"
```

Ask user which untracked files to include.

### Merge Conflicts

```bash
git status | grep "Unmerged paths"
```

If conflicts exist, inform user and stop - don't auto-commit conflicted files.

### Large Number of Files

If > 20 files changed, summarize by directory/type and ask for confirmation before grouping.

### Pre-commit Keeps Failing

If pre-commit fails 3+ times on same file:

1. Show the specific error
1. Ask user if they want to skip that hook temporarily
1. Never use `--no-verify`

## Commit Summary Template

After completing all commits, provide a summary:

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

Ready to push with: /repo/push
```

## Changeset Grouping Examples

### Example 1: Feature with Tests

Files changed:

- `src/auth/service.py`
- `src/auth/schemas.py`
- `tests/test_auth.py`
- `docs/auth.md`

Changesets:

1. `feat(auth): add authentication service` - service.py, schemas.py
1. `test(auth): add authentication tests` - test_auth.py
1. `docs(auth): document authentication` - auth.md

### Example 2: Refactoring Across Modules

Files changed:

- `src/api/users.py`
- `src/api/items.py`
- `src/models/user.py`
- `src/models/item.py`

Changesets (grouped by type of change):

1. `refactor(api): standardize error handling` - users.py, items.py
1. `refactor(models): add validation methods` - user.py, item.py

### Example 3: Config + Dependencies

Files changed:

- `pyproject.toml`
- `uv.lock`
- `.pre-commit-config.yaml`

Single changeset:

1. `chore: update dependencies and pre-commit config`

## Conventional Commit Reference

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(auth): add OAuth2 login` |
| `fix` | Bug fix | `fix(api): handle null response` |
| `docs` | Documentation | `docs: update API reference` |
| `style` | Formatting | `style: fix indentation` |
| `refactor` | Code restructure | `refactor: extract helper function` |
| `perf` | Performance | `perf(db): add query index` |
| `test` | Tests | `test: add unit tests for parser` |
| `chore` | Maintenance | `chore: update dependencies` |
