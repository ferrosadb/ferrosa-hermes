# Nested docs repository snapshot pattern

Use this when the user asks to commit a documentation snapshot while working inside a workspace that contains nested repos.

## Trigger

- User says “commit all current docs”, “snapshot where we are”, or similar.
- Current shell may be inside a parent workspace with many cloned repos.
- Requested scope is documentation or another obvious subset.

## Safe sequence

```bash
cd /path/to/likely/docs/repo
git rev-parse --show-toplevel
git branch --show-current
git status --porcelain=v1
```

If the branch is `main` or `master`, create a branch before committing:

```bash
git checkout -b docs/snapshot-current-docs
```

Inspect scope without reading every file:

```bash
git diff --stat
git status --porcelain=v1
```

Stage only the requested docs scope:

```bash
git add README.md docs specs
```

Run pre-commit only when the repo has a config:

```bash
if command -v pre-commit >/dev/null 2>&1 && [ -f .pre-commit-config.yaml ]; then
  pre-commit run --files $(git diff --cached --name-only)
else
  echo 'pre-commit not run: command or .pre-commit-config.yaml missing'
fi
```

Commit and verify:

```bash
git commit -m "docs: snapshot current documentation"
git status --porcelain=v1
git log -1 --oneline --decorate
```

## Reporting

Report:

- repo root
- branch created/used
- commit hash and subject
- clean/dirty status
- file/change count from commit output
- whether pre-commit ran; if not, exact reason
- whether anything was pushed

## Pitfall

Do not run `git add .` from a parent workspace that contains many nested repos. It can stage submodule-like directory entries or unrelated untracked repositories instead of the intended docs snapshot.
