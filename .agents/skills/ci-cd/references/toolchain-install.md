# CI/CD Toolchain — Install Reference

Install guide for every tool the `ci-cd` skill (SKILL.md) names. Use it to install a
missing tool rather than silently skipping a gate (`skills/rules/safety.md` — fail loud,
never fake a green gate by no-op'ing it).

## Agent procedure (read first)

1. **Check before installing**: `command -v <tool>` (or the verify command). Only install
   what's missing.
2. **Prefer the project's existing tools.** If the repo already pins a runner-side action,
   a `pre-commit` config, or language-native linters, use those — don't introduce a parallel
   stack. Most CI tooling runs **inside the runner** (GitHub Actions / GitLab CI) via
   `uses:`/`image:`, not as host installs; install locally only to reproduce a gate.
3. **Language linters/test tools live in their own skills.** `ruff`/`mypy`, `cargo`,
   `golangci-lint`, `mix`, `eslint`/`tsc`, etc. are installed per `skills/tech/<lang>/`.
   This file covers the **CI-orchestration** layer (runners, hooks, secret/dep scanners,
   spec validators).
4. **Log every install** (`skills/rules/safety.md`): say what was missing and what you
   installed. Never quietly degrade a security/quality gate to a no-op because a tool was absent.
5. **Don't auto-install heavy/daemon tooling silently.** Self-hosted `gitlab-runner` and Docker
   itself run as a service/daemon (see `docker-dev`); note them as deliberate setup, not a
   throwaway CLI install.

Detect the platform: `uname` (`Darwin`=macOS→Homebrew, `Linux`→`apt`/`dnf`/`pacman`).
`pipx` is preferred over `pip install --user` for Python CLI tools; `npm i -g` (or `npx`)
for the Node-based spec validators.

## Runner / pipeline tooling

| Tool | macOS (brew) | Debian/Ubuntu (apt) | Verify | Notes |
|------|--------------|---------------------|--------|-------|
| **gh** (GitHub CLI) | `brew install gh` | `apt install gh` (or GitHub apt repo) | `gh --version` | for PR checks, required-status-check setup, `gh run` |
| **act** (run GitHub Actions locally) | `brew install act` | `curl -fsSL https://raw.githubusercontent.com/nektos/act/master/install.sh \| sudo bash` | `act --version` | needs Docker running |
| **pre-commit** | `brew install pre-commit` (or `pipx install pre-commit`) | `pipx install pre-commit` | `pre-commit --version` | see `skills/task-level/repo/manage-precommit/` |
| **glab** (GitLab CLI) | `brew install glab` | download release / `apt` repo | `glab --version` | optional, GitLab projects |
| **gitlab-runner** (self-hosted) | `brew install gitlab-runner` | GitLab apt repo (`curl -L .../script.deb.sh \| sudo bash` then `apt install gitlab-runner`) | `gitlab-runner --version` | runs as a **service**; only for self-hosted CI |

## Security gates (Step 4)

| Tool | macOS (brew) | Debian/Ubuntu (apt) | Verify | Notes |
|------|--------------|---------------------|--------|-------|
| **gitleaks** (secret scan) | `brew install gitleaks` | `apt install gitleaks` (or release binary) | `gitleaks version` | `gitleaks detect --source .`; container: `zricethezav/gitleaks` |
| **trufflehog** (secret scan, alt) | `brew install trufflehog` | `curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh \| sudo sh -s -- -b /usr/local/bin` | `trufflehog --version` | verified-secret scanning |
| **detect-secrets** (secret scan, alt) | `pipx install detect-secrets` | `pipx install detect-secrets` | `detect-secrets --version` | Yelp; pre-commit-friendly |
| **syft** (SBOM) | `brew install syft` | `curl -sSfL https://get.anchore.io/syft \| sh -s -- -b /usr/local/bin` | `syft version` | `syft scan dir:. -o cyclonedx-json=sbom.json` |
| **grype** (advisories) | `brew install grype` | `curl -sSfL https://get.anchore.io/grype \| sh -s -- -b /usr/local/bin` | `grype version` | `grype sbom:sbom.json --fail-on high` |
| **cyclonedx-cli** (SBOM, alt) | `brew install cyclonedx-cli` | release binary | `cyclonedx-cli --version` | CycloneDX manipulation |

Dependency-audit tools (`npm audit`, `cargo audit`, `pip-audit`, `mix deps.audit`) ship with /
install via their language toolchains — see the relevant `skills/tech/<lang>/`.

## OpenAPI / contract validation (Step 4 & Step 6)

| Tool | Install | Verify | Notes |
|------|---------|--------|-------|
| **@scalar/openapi-parser** | `npx @scalar/openapi-parser validate <spec>` (no global install needed) | `npx @scalar/openapi-parser --help` | the validator the skill names |
| **@redocly/cli** | `npm i -g @redocly/cli` | `redocly --version` | `redocly lint <spec>`; needs Node ≥ 22.12 |
| **@stoplight/spectral-cli** | `npm i -g @stoplight/spectral-cli` | `spectral --version` | `spectral lint <spec>`; ~6.16 (2026) |

(See `skills/tech/semver-api/references/toolchain-install.md` for the deeper API-contract
diff/version toolset — `openapi-diff`, `buf`, `cargo-semver-checks`, etc.)

## One-shot baseline bootstrap

The everyday CI-orchestration set (language linters/test tools come from their own skills):

```bash
# macOS
brew install gh act pre-commit gitleaks syft grype
npm i -g @redocly/cli @stoplight/spectral-cli

# Debian/Ubuntu
sudo apt update && sudo apt install -y gh gitleaks
pipx install pre-commit
curl -fsSL https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
curl -sSfL https://get.anchore.io/syft  | sudo sh -s -- -b /usr/local/bin
curl -sSfL https://get.anchore.io/grype | sudo sh -s -- -b /usr/local/bin
npm i -g @redocly/cli @stoplight/spectral-cli
```

Fedora: swap `apt` for `dnf` (`gh`, `gitleaks` where packaged; else use the release scripts).
Arch: `pacman -S github-cli act` (gitleaks/pre-commit via AUR or pipx).

Verify versions noted here against upstream (`act`, `gitleaks`, `spectral`, `@redocly/cli`,
`syft`/`grype`) — pin versions for reproducible CI. Flag any drift you observe.
