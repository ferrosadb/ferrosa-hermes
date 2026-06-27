---
name: ci-cd
description: CI/CD pipelines with GitHub Actions, immutable artifacts, quality gates, and safe deploys. Use when setting up CI/CD, configuring build pipelines, adding deployment automation, or troubleshooting failed builds.
tags: [tooling]
argument-hint: <init|update|validate> [--platform github|gitlab]
supplementary-files:
  - references/toolchain-install.md
---

Version date: 2026-03-02

## Before you start (memory-first)

Before reading files or grepping:
1. `ferrosa-memory.hybrid_search` on the task topic + key nouns in `$ARGUMENTS`
2. `ferrosa-memory.retrieve_skills_for_context` with tags `tech`, `tooling`, `ci-cd`
3. `ferrosa-memory.check_intentions` — act on any triggered intentions

On fallback, call `record_outcome` with `program_type="retrieval_miss"`. Escape-hatch tools: see `skills/quality/skill-dev-methodology-quality-gates.v2.md` § "ferrosa-memory Integration".

## Forge tools

| Step | frg command | What it does |
|------|-------------|--------------|
| 1 | `frg project-detect` | Detect runner (GHA / GitLab), pipeline file |
| 2 | `frg format-fix` | Apply formatter fixes the CI expects |
| 3 | `frg lint-dedup` | Dedup + summarise lint violations |
| 4 | `frg test-summary` | Summarise test results + coverage |
| 5 | `frg secret-scan` | Block leaked credentials |
| 6 | `frg deps-audit` | Audit dependency vulnerabilities |
| 7 | `frg merge-check` | Validate merge readiness before promotion |

Fallback: if forge is unavailable, use raw linters + test runners. Log the fallback (`skills/rules/safety.md`).

## Principles (Non-Negotiable)

1. **Artifacts are immutable** — A release is an immutable artifact plus a manifest. Never modify a published artifact.
2. **Block on fail** — Quality/security gates fail closed. No production promotion if any gate fails.
3. **12-factor config** — Runtime configuration via environment variables; code is deploy-agnostic.
4. **Fast loops, stable production** — Optimize for continuous deployment with high confidence.
5. **Traceable releases** — Every production deploy maps to a Git SHA + release ID + manifest.

## Release ID Format

Format: `YYYYMMDD-build<NN>-<shortsha>`

Example: `20260205-build03-a1b2c3d`

- `YYYYMMDD` — UTC date of build
- `buildNN` — Per-day monotonic sequence (01...N)
- `shortsha` — 7-character Git SHA

## Pipeline Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PR Pipeline   │────>│  Merge to Main  │────>│    Production   │
│  (Block-on-fail)│     │ (Build+Publish) │     │    (Deploy)     │
│                 │     │                 │     │                 │
│ - Lint          │     │ - Build artifact│     │ - Pull artifact │
│ - Typecheck     │     │ - Run gates     │     │ - Migrate DB    │
│ - Test          │     │ - Publish to    │     │ - Swap & verify │
│ - Format check  │     │   object store  │     │ - Health check  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
       GATE                   PACKAGE                 DEPLOY
```

## Instructions

### Step 1: Detect runner and pipeline file

Identify the platform (GitHub Actions, GitLab CI, CircleCI, Buildkite) and locate the pipeline definition (`.github/workflows/*.yml`, `.gitlab-ci.yml`, etc.). Confirm which branches trigger which stages.

**Toolchain check.** Before running any gate locally, confirm the tools it needs are installed (`command -v gh`, `command -v gitleaks`, `npx @redocly/cli --version`, etc.). If one is missing, install it from **`references/toolchain-install.md`** (check-then-install; prefer the project's existing stack) and log the install — never silently skip a security/quality gate because a tool is absent (`skills/rules/safety.md`).

### Step 2: Format/lint stage

PR pipeline gates — all must pass before merge. Configure as required status checks.

Language-specific format + lint:

**Elixir/Phoenix:**
```bash
mix compile --warnings-as-errors
mix format --check-formatted
mix credo --strict
```

**Python:**
```bash
ruff check .
ruff format --check .
mypy .
```

**Rust:**
```bash
cargo fmt -- --check
cargo clippy -- -D warnings
```

**Go:**
```bash
gofmt -l .
go vet ./...
golangci-lint run
```

**TypeScript/Node.js:**
```bash
npx eslint .
npx tsc --noEmit
npx prettier --check .
```

### Step 3: Build and test stage

Run the full test suite with coverage. Every language skill declares the minimum gate (see `skills/tech/<lang>.skill.md`).

```bash
mix test && mix coveralls      # Elixir
pytest --cov --cov-fail-under=80  # Python
cargo test                      # Rust
go test ./...                   # Go
npm test                        # Node
```

Build artifacts inside Docker for reproducible environments:

```bash
docker compose run --rm app make ci
```

### Step 4: Security stage

Universal gates:
- **Secret detection** — gitleaks, trufflehog, or detect-secrets
- **Dependency audit** — npm audit, cargo audit, pip-audit, mix deps.audit
- **Dependency license gates** — do not silently broaden allowlists to make CI green. Identify the exact crate/license/reverse dependency path first; if incompatible or ambiguous, rework/remove/feature-gate the dependent function. See `references/dependency-license-gate-triage.md`.
- **SBOM generation** — syft / cyclonedx for supply-chain tracking
- **OpenAPI spec validation** — if the component exposes an API (`npx @scalar/openapi-parser validate openapi/openapi.yaml`)
- **Changeset present** — PRs that change behavior must include a changeset describing the semver bump (patch/minor/major)

### Step 5: Coverage gate

Enforce the complexity-coupled coverage policy from each language skill:
- 80% baseline coverage on new/changed code
- CC ≥ 15 → 90% coverage + documentation
- CC ≥ 25 → refactor plan required

Post coverage delta and cyclomatic complexity hotspots as a PR comment. Fail the gate on regression.

### Step 6: Deploy gate

On merge to main, build + package + publish:

1. Apply pending changesets: bump component versions (Semantic Versioning 2.0.0), update changelogs
2. Compute `release_id` (fetch day's build counter from state store)
3. Build artifacts in Docker (reproducible environment)
4. Run full CI gate suite
5. Verify OpenAPI spec `info.version` matches component version
6. Create manifest with gate results, checksums, and component version
7. Publish artifact + manifest to object store
8. Git tag: `{component}@{version}` (e.g., `backend@2.3.1`)
9. Update state: set `desired_release` pointer

Production deploy:
1. Check deploy pause flag — abort if set
2. Pull artifact from object store
3. Run database migrations (BEFORE starting new code)
4. Deploy using rename-and-swap (see Safety Rules)
5. Health-check ALL services
6. On failure: auto-rollback, pause deploy train

## Manifest Schema

```json
{
  "service": "<app-name>",
  "version": "<semver>",
  "release_id": "<YYYYMMDD-buildNN-shortsha>",
  "git_sha": "<full-sha>",
  "build_timestamp_utc": "<ISO-8601>",
  "artifact_uris": ["releases/<release_id>/artifact/<app>-release.tar.gz"],
  "checksums": { "sha256": "<hash>" },
  "gates": {
    "compile": "pass|fail",
    "format": "pass|fail",
    "lint": "pass|fail",
    "typecheck": "pass|fail",
    "tests": "pass|fail",
    "coverage": "pass|fail"
  },
  "promotion_history": [
    {"env": "production", "time": "<ISO-8601>", "actor": "<manual|ci>"}
  ]
}
```

## Object Store Layout

```
<app>-releases/
├── releases/
│   └── <release_id>/
│       ├── artifact/              # Immutable release tarball
│       └── manifest.json          # Build metadata, gates, checksums
├── state.json                     # Current/desired/previous release pointers
└── controls/
    └── prod_pause                 # Global deploy-train stop flag
```

## Deploy Commands (Template)

```bash
./build.sh          # Docker-based build, outputs tarballs
./publish.sh        # Upload artifacts + manifest to object store
./deploy.sh latest  # Pull artifact, migrate, swap, verify
./ship.sh           # All-in-one: build -> publish -> deploy
./status.sh         # Current release + health check
./rollback.sh       # Revert to previous release
./pause.sh "reason" # Block all deploys
./unpause.sh        # Resume deployments
```

## Safety Rules (From Production Incidents)

1. **Never install dependencies on production machines.** They're too small, it takes too long, and it leaves broken state on failure.
2. **Never delete production directories before verifying new code.** Use rename-and-swap.
3. **Health checks MUST verify ALL services.** A passing `/health` endpoint doesn't mean the frontend is serving.
4. **Never force push** — always go through the build -> publish -> deploy pipeline.
5. **Respect train pause** — investigate the reason first.
6. **Test locally first** — verify in Docker before deploying.
7. **Verify after deploy** — always run the post-deploy verification checklist.
8. **Use CI for production fixes** — not manual SSH.

## Migration Safety

- Scan migration files for destructive operations (`DROP TABLE`, `DROP COLUMN`, `TRUNCATE`)
- Abort with warning if destructive ops detected; require `--force-destructive` to override
- Always run migrations BEFORE starting the new application code
- Migrations must be backwards-compatible (old code must work with new schema during rollout)

## GitHub Rulesets and Merge Queue

When hardening a GitHub repository, create/update workflows first, open a PR, and wait for the run to populate real job context names. Use those exact context names in required status checks; do not guess from workflow names.

If using GitHub Rulesets for merge queue or branch policy, verify with the Rulesets API after mutation. The older branch-protection endpoint may still return `404 Branch not protected` even though an active ruleset protects the branch. See `references/github-rulesets-merge-queue.md` for commands and readback checks.

## GitHub Actions Example

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]

jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build & Test
        run: docker compose run --rm app make ci
      - name: Secret Detection
        run: gitleaks detect --source .

  deploy:
    needs: gate
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Release
        run: ./build.sh
      - name: Publish
        run: ./publish.sh
      - name: Deploy
        run: ./deploy.sh latest
```

## Post-Deploy Verification Template

```bash
curl -sf https://<domain>/health | jq .
curl -sI https://<domain>/ | head -1
# flyctl status -a <app-name>
# kubectl get pods
# aws ecs describe-services
# Compare deployed SHA to expected SHA
```
