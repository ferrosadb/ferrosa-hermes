# GitHub Rulesets and Merge Queue Verification

Use this when hardening a GitHub repository with required checks, pull-request gates, or merge queue.

## Pattern

1. Create or update workflows first and run them on a PR.
2. Wait for the PR run to populate real check context names.
3. Use those exact job names in the ruleset required status checks.
4. Apply protection through the Rulesets API when using merge queue.
5. Read the ruleset back after creation or update.

## Useful commands

Inspect existing protection/rulesets:

```bash
gh api repos/OWNER/REPO/branches/main/protection || true
gh api repos/OWNER/REPO/rulesets --jq '.' || true
```

Watch a run and capture job names:

```bash
gh run list --branch BRANCH --limit 10 --json databaseId,workflowName,status,conclusion,url
gh run watch RUN_ID --exit-status
gh pr view PR_NUMBER --json statusCheckRollup \
  --jq '.statusCheckRollup[] | {name,status,conclusion}'
```

Read back a ruleset:

```bash
gh api repos/OWNER/REPO/rulesets/RULESET_ID \
  --jq '{id,name,enforcement,target,conditions,rules}'
```

## Important gotcha

If protection is implemented with GitHub Rulesets, the legacy branch protection endpoint can still return `404 Branch not protected`. That does not mean the branch is unprotected. Treat the ruleset readback as authoritative for ruleset-based protection, and verify behavior through PR merge state (`REVIEW_REQUIRED`, required checks, or merge-queue state).

## Required-check naming

Required status checks should match actual job context names, not guessed workflow names. Example contexts from a Rust CI workflow might be:

- `Format & Lint`
- `Build & Test`
- `Docs`
- `Dependency Advisories`
