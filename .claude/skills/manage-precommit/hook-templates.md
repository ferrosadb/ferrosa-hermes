# Pre-commit Hook Templates

YAML configuration templates for different project types.

## Contents

- [General Hooks (Always Include)](#general-hooks-always-include)
- [Python Project Hooks](#python-project-hooks)
- [Frontend Project Hooks (Next.js/Vite)](#frontend-project-hooks-nextjsvite)
- [Elixir Project Hooks](#elixir-project-hooks)
- [Rust Project Hooks](#rust-project-hooks)
- [Go Project Hooks](#go-project-hooks)
- [JavaScript / TypeScript Project Security Hooks](#javascript--typescript-project-security-hooks)
- [Markdown Linting](#markdown-linting)
- [Codespell (Typo Detection)](#codespell-typo-detection)
- [YAML Formatting](#yaml-formatting)
- [Shell Scripts](#shell-scripts)
- [Commit Message Convention](#commit-message-convention)
- [Pre-push Test Hooks](#pre-push-test-hooks)
- [Full Config Header Template](#full-config-header-template)

## General Hooks (Always Include)

```yaml
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-added-large-files
        args: [--maxkb=500]
      - id: check-merge-conflict
      - id: check-byte-order-marker
      - id: check-case-conflict
      - id: check-executables-have-shebangs
      - id: check-json
      - id: check-yaml
        args: [--allow-multiple-documents]
      - id: check-toml
      - id: detect-private-key
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: mixed-line-ending
      - id: no-commit-to-branch
        args:
          - --pattern
          - '^(?!((ci|chore|docs|feature|fix|refactor|test)\/[a-zA-Z0-9\-]+)$).*'
      - id: check-shebang-scripts-are-executable

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ["--exclude-files", ".*\\.ipynb", "--exclude-files", ".*\\.lock"]
```

## Python Project Hooks

For a Python project at `<project-path>`:

```yaml
  # ===========================================================================
  # Python: <project-name>
  # ===========================================================================
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-ast
        files: ^<project-path>/.*\.py$
      - id: check-docstring-first
        files: ^<project-path>/.*\.py$
      - id: debug-statements
        files: ^<project-path>/.*\.py$

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.2
    hooks:
      - id: ruff
        args: [--fix]
        files: ^<project-path>/.*\.py$
      - id: ruff-format
        files: ^<project-path>/.*\.py$

  - repo: local
    hooks:
      - id: mypy-<project-name>
        name: mypy (<project-name>)
        entry: bash -c 'cd <project-path> && uv run mypy .'
        language: system
        files: ^<project-path>/.*\.py$
        pass_filenames: false

  - repo: https://github.com/asottile/pyupgrade
    rev: v3.19.0
    hooks:
      - id: pyupgrade
        args: [--py312-plus]
        files: ^<project-path>/.*\.py$

  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.0
    hooks:
      - id: bandit
        args: [-r, --skip=B101]
        files: ^<project-path>/.*\.py$
        exclude: '.*/tests/.*\.py$'

  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.5.14
    hooks:
      - id: uv-lock
        name: uv-lock (<project-name>)
        files: ^<project-path>/pyproject\.toml$
        args: [--directory=<project-path>]

  - repo: local
    hooks:
      # Pre-commit: advisory check
      - id: pip-audit-<project-name>
        name: pip-audit (<project-name>)
        entry: bash -c 'cd <project-path> && uv run pip-audit -r requirements.txt'
        language: system
        files: ^<project-path>/requirements.*\.txt$|^<project-path>/pyproject\.toml$
        pass_filenames: false

      # Pre-push: strict mode — non-zero exit on any advisory
      - id: pip-audit-strict-<project-name>
        name: pip-audit strict (<project-name>)
        stages: [pre-push]
        entry: bash -c 'cd <project-path> && uv run pip-audit --strict'
        language: system
        files: ^<project-path>/requirements.*\.txt$|^<project-path>/pyproject\.toml$
        pass_filenames: false
```

## Frontend Project Hooks (Next.js/Vite)

For a frontend project at `<project-path>`:

```yaml
  # ===========================================================================
  # Frontend: <project-name>
  # ===========================================================================
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        files: ^<project-path>/.*\.(ts|tsx|js|jsx|css|scss|json|md)$
        exclude: ^<project-path>/(node_modules|\.next|dist|build|package-lock\.json)/
        additional_dependencies:
          - prettier@3.4.2

  - repo: local
    hooks:
      - id: eslint-<project-name>
        name: eslint (<project-name>)
        entry: bash -c 'cd <project-path> && npm run lint'
        language: system
        files: ^<project-path>/.*\.(ts|tsx|js|jsx)$
        pass_filenames: false
```

## Elixir Project Hooks

For an Elixir project at `<project-path>`:

```yaml
  # ===========================================================================
  # Elixir: <project-name>
  # ===========================================================================
  - repo: local
    hooks:
      - id: mix-format-<project-name>
        name: mix format (<project-name>)
        entry: bash -c 'cd <project-path> && mix format --check-formatted'
        language: system
        files: ^<project-path>/.*\.(ex|exs)$
        pass_filenames: false

      - id: mix-compile-<project-name>
        name: mix compile (<project-name>)
        entry: bash -c 'cd <project-path> && mix compile --warnings-as-errors'
        language: system
        files: ^<project-path>/.*\.(ex|exs)$
        pass_filenames: false

      # Security: fast built-in hex advisory check (no network on subsequent runs)
      - id: mix-hex-audit-<project-name>
        name: mix hex.audit (<project-name>)
        entry: bash -c 'cd <project-path> && mix hex.audit'
        language: system
        files: ^<project-path>/mix\.(exs|lock)$
        pass_filenames: false

      # Security: full mix_audit scan on push (requires mix_audit dep)
      - id: mix-audit-<project-name>
        name: mix audit (<project-name>)
        stages: [pre-push]
        entry: bash -c 'cd <project-path> && mix audit --strict'
        language: system
        files: ^<project-path>/mix\.(exs|lock)$
        pass_filenames: false
```

Prerequisites for `mix audit`: add `{:mix_audit, "~> 2.0", only: [:dev], runtime: false}` to `mix.exs`.

## Rust Project Hooks

For a Rust project at `<project-path>`:

```yaml
  # ===========================================================================
  # Rust: <project-name>
  # ===========================================================================
  - repo: local
    hooks:
      - id: cargo-fmt-<project-name>
        name: cargo fmt (<project-name>)
        entry: bash -c 'cd <project-path> && cargo fmt -- --check'
        language: system
        files: ^<project-path>/.*\.rs$
        pass_filenames: false

      - id: cargo-clippy-<project-name>
        name: cargo clippy (<project-name>)
        entry: bash -c 'cd <project-path> && cargo clippy -- -D warnings'
        language: system
        files: ^<project-path>/.*\.rs$
        pass_filenames: false

      # Security: fast offline advisory + license policy check on every commit
      - id: cargo-deny-<project-name>
        name: cargo deny (<project-name>)
        entry: bash -c 'cd <project-path> && cargo deny check advisories licenses'
        language: system
        files: ^<project-path>/Cargo\.(toml|lock)$
        pass_filenames: false

      # Security: full advisory database scan on push (requires network, ~2s)
      - id: cargo-audit-<project-name>
        name: cargo audit (<project-name>)
        stages: [pre-push]
        entry: bash -c 'cd <project-path> && cargo audit --deny warnings'
        language: system
        files: ^<project-path>/Cargo\.lock$
        pass_filenames: false
```

Prerequisites: `cargo install cargo-deny cargo-audit`. The `deny.toml` config file must exist at `<project-path>/deny.toml` — run `cargo deny init` to generate a sensible default. See `rust.skill.md` for the recommended `deny.toml` starting configuration.

## Go Project Hooks

For a Go project at `<project-path>`:

```yaml
  # ===========================================================================
  # Go: <project-name>
  # ===========================================================================
  - repo: local
    hooks:
      - id: go-fmt-<project-name>
        name: gofmt (<project-name>)
        entry: bash -c 'cd <project-path> && gofmt -l -d . | (! grep .)'
        language: system
        files: ^<project-path>/.*\.go$
        pass_filenames: false

      - id: go-vet-<project-name>
        name: go vet (<project-name>)
        entry: bash -c 'cd <project-path> && go vet ./...'
        language: system
        files: ^<project-path>/.*\.go$
        pass_filenames: false

      # Security: call-graph-aware vulnerability scan (Go Vulnerability Database)
      - id: govulncheck-<project-name>
        name: govulncheck (<project-name>)
        entry: bash -c 'cd <project-path> && govulncheck ./...'
        language: system
        files: ^<project-path>/.*\.go$|^<project-path>/go\.(mod|sum)$
        pass_filenames: false
```

Prerequisites: `go install golang.org/x/vuln/cmd/govulncheck@latest`

## JavaScript / TypeScript Project Security Hooks

For a Node.js or TypeScript project at `<project-path>`:

```yaml
  - repo: local
    hooks:
      # Pre-commit: advisory check (HIGH/CRITICAL only)
      - id: npm-audit-<project-name>
        name: npm audit (<project-name>)
        entry: bash -c 'cd <project-path> && npm audit --audit-level=high'
        language: system
        files: ^<project-path>/package(-lock)?\.json$
        pass_filenames: false

      # Pre-push: strict mode with audit-ci
      - id: audit-ci-<project-name>
        name: audit-ci (<project-name>)
        stages: [pre-push]
        entry: bash -c 'cd <project-path> && npx audit-ci --high'
        language: system
        files: ^<project-path>/package(-lock)?\.json$
        pass_filenames: false
```

## Markdown Linting

```yaml
  # ===========================================================================
  # Markdown linting
  # ===========================================================================
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.43.0
    hooks:
      - id: markdownlint
        args: [--fix, --disable=MD013, --disable=MD040, --disable=MD024, --disable=MD036, --disable=MD041]
        exclude: node_modules/
```

## Codespell (Typo Detection)

```yaml
  # ===========================================================================
  # Codespell (typo detection)
  # ===========================================================================
  - repo: https://github.com/codespell-project/codespell
    rev: v2.3.0
    hooks:
      - id: codespell
        exclude: '(node_modules/|package-lock\.json|\.lock$)'
```

## YAML Formatting

```yaml
  # ===========================================================================
  # YAML formatting
  # ===========================================================================
  - repo: https://github.com/jumanjihouse/pre-commit-hook-yamlfmt
    rev: 0.2.3
    hooks:
      - id: yamlfmt
        args:
          - --mapping=2
          - --sequence=4
          - --offset=2
          - --implicit_start
          - --preserve-quotes
        exclude: '(templates/.*\.yaml$|\.github/workflows/.*\.yaml$)'
```

## Shell Scripts

```yaml
  # ===========================================================================
  # Shell scripts
  # ===========================================================================
  - repo: https://github.com/pecigonzalo/pre-commit-shfmt
    rev: v2.2.0
    hooks:
      - id: shell-fmt-docker
        name: shfmt
        args:
          - --indent=2
          - --binary-next-line
          - --case-indent
          - --space-redirects
        files: \.sh$
```

## Commit Message Convention

```yaml
  # ===========================================================================
  # Commit message convention
  # ===========================================================================
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v4.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
```

## Pre-push Test Hooks

For Python projects with tests:

```yaml
  # ===========================================================================
  # Pre-push: Tests
  # ===========================================================================
  - repo: local
    hooks:
      - id: pytest-<project-name>
        name: pytest (<project-name>)
        stages: [pre-push]
        entry: bash -c 'cd <project-path> && uv run pytest -x -q; ret=$?; [ $ret -eq 5 ] && exit 0 || exit $ret'
        language: system
        files: ^<project-path>/.*\.py$
        pass_filenames: false
```

For Elixir projects with tests:

```yaml
  - repo: local
    hooks:
      - id: mix-test-<project-name>
        name: mix test (<project-name>)
        stages: [pre-push]
        entry: bash -c 'cd <project-path> && mix test'
        language: system
        files: ^<project-path>/.*\.(ex|exs)$
        pass_filenames: false
```

## Full Config Header Template

```yaml
# =============================================================================
# Monorepo - Pre-commit Configuration
# =============================================================================
# Auto-generated by /repo/manage-precommit skill
# Detected projects: [list detected projects]
# Last updated: [date]
# =============================================================================

default_install_hook_types:
  - pre-commit
  - pre-push
  - commit-msg

default_language_version:
  python: python3.12

repos:
  # [Insert hooks from above templates]
```
