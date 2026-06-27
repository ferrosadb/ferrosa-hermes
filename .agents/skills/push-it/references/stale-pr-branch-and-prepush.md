# Stale PR Branch and Pre-Push Hook Notes

Use this when a push/PR workflow encounters a branch whose existing GitHub PR is already merged or closed, or when local hooks mutate files during push verification.

## Stale or merged PR branch

Symptom:

- `gh pr list --head <branch> --state all` shows the branch is attached to a merged or closed PR.
- Repository pre-push guards may reject reusing the branch name because it would obscure audit history or reopen the wrong review context.

Preferred recovery:

1. Preserve current work first:
   - `git status --porcelain`
   - `git stash push -u -m <clear-name>` if needed, or commit to a temporary local branch.
2. Fetch the current base:
   - `git fetch --all --prune`
3. Create a fresh, reviewable PR branch from the intended upstream base:
   - `git switch -c <new-topic-branch> origin/main`
4. Bring over only the intended WIP commits or patch:
   - `git cherry-pick <commit-range>` or `git restore --source <old-branch> -- <paths>`
5. Verify with the repo's local CI-equivalent commands.
6. Push the fresh branch and create a new PR.

Do not force-push or reuse a branch that is already tied to a merged/closed PR unless the user explicitly asks and the repository policy allows it.

## Hook-stage scoping

When running local hooks as pre-push verification, prefer the exact hook stage:

- `pre-commit run --hook-stage pre-push --all-files`

Do not use an all-stages/all-hooks run as a substitute for pre-push if it triggers unrelated commit-time fixers. If a hook run mutates broad unrelated files, preserve those edits in a named stash before continuing, then fix the hook configuration or run scope.

## Shell compatibility in repo hooks

If a repository hook script is intended to run on macOS system Bash, keep Bash 3 compatibility unless the repo explicitly requires newer Bash. Avoid Bash 4-only constructs such as associative arrays in portable hook scripts.
