# Python Toolchain — Install Reference

Install guide for every tool the `python` skill (SKILL.md, `static-perf.md`,
`references/external-data-e2e-seeding.md`, `references/duckdb-minio-s3-catalog.md`)
references. Use it to install a tool that isn't present rather than assuming it's
there or silently skipping a gate.

## Agent procedure (read first)

1. **Check before installing**: `command -v <tool>` (or the verify command in the
   tables). Only install what's missing.
2. **Match the project's toolchain.** Detect the manager from the repo: `uv.lock`
   → use `uv`; `poetry.lock` → `poetry`; bare `requirements*.txt` → `pip` in a
   venv; `pyproject.toml` `[tool.*]` blocks tell you whether it's ruff/black/mypy/
   pyright. Refuse to install deps without a lockfile (`skills/rules/safety.md`).
3. **No separate install needed** for these — they ship with CPython:
   **`venv`** (`python -m venv`), **`pip`**, **`pdb`** (`breakpoint()`),
   **`traceback`** / **`faulthandler`** modules. Don't install a third-party tool
   for something the stdlib already provides.
4. **Log every install** (fail-loud / observable-fallback, `skills/rules/safety.md`):
   say what was missing and what you installed; don't quietly degrade a CI gate to
   a no-op because a tool was absent.
5. **Don't auto-install commercial tools.** SonarQube (paid editions), commercial
   SCA/license scanners are licensed — use only if the project already configures
   them; otherwise use the free path (ruff, mypy, pip-audit, radon, pip-licenses)
   and say so.
6. **Prefer `pipx` for CLI tools** (ruff, mypy, pip-audit, radon, pip-licenses,
   py-spy, conan) — it isolates each tool in its own venv. Use **project-local
   installs** (`uv add --dev`, `pip install` inside the venv) for pytest/coverage/
   hypothesis so they share the project's environment and import path.

Detect the platform: `uname` (`Darwin`=macOS→Homebrew, `Linux`→`apt`/`dnf`/`pacman`).

## Interpreters, venv & package managers

| Tool | macOS (brew) | Debian/Ubuntu (apt) | Verify | Notes |
|------|--------------|---------------------|--------|-------|
| **CPython 3.x** | `brew install python@3.13` | `apt install python3 python3-venv python3-pip` | `python3 --version` | apt splits venv/pip into separate packages |
| **uv** (resolver + venv + runner) | `brew install uv` (or `curl -LsSf https://astral.sh/uv/install.sh \| sh`) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `uv --version` | manages Python versions too: `uv python install 3.13` |
| **pipx** (isolated CLI installs) | `brew install pipx` | `apt install pipx` | `pipx --version` | `pipx ensurepath` after install |
| **pip** | with Python | `apt install python3-pip` | `pip --version` | stdlib-adjacent; prefer `uv pip` / venv |
| **Poetry** (if project uses it) | `pipx install poetry` | `pipx install poetry` | `poetry --version` | only if `poetry.lock` present |
| **venv** | built into CPython | built into CPython | `python3 -m venv --help` | **no separate install** |

Fedora: `dnf install python3 python3-pip pipx`. Arch: `pacman -S python python-pip python-pipx uv`.

## Formatting & linting

| Tool | Install (pipx) | Verify | Notes |
|------|----------------|--------|-------|
| **ruff** (lint + format + import sort) | `pipx install ruff` (or `brew install ruff` / `uv tool install ruff`) | `ruff --version` | `ruff check .` + `ruff format .`; PERF rules: `ruff check --select PERF,B,C4,SIM` |
| **black** (formatter, if project pins it) | `pipx install black` | `black --version` | use only if repo doesn't use `ruff format` |
| **flake8** (legacy linter) | `pipx install flake8` | `flake8 --version` | only for existing flake8 projects |
| **perflint** (PERF anti-patterns) | `pipx install perflint` | `perflint --version` | optional, from `static-perf.md` |

## Type checking

| Tool | Install | Verify | Notes |
|------|---------|--------|-------|
| **mypy** | `pipx install mypy` | `mypy --version` | `mypy --strict`; add `pandas-stubs` for pandas |
| **pyright** | `pipx install pyright` (pulls a bundled Node) or `npm i -g pyright` | `pyright --version` | alternative to mypy |
| **pandas-stubs** | `uv add --dev pandas-stubs` / `pip install pandas-stubs` | n/a | install in the project env, not via pipx |

## Tests, property testing & coverage

| Tool | Install (project env) | Verify | Notes |
|------|-----------------------|--------|-------|
| **pytest** | `uv add --dev pytest` / `pip install pytest` | `pytest --version` | |
| **pytest-cov** | `uv add --dev pytest-cov` / `pip install pytest-cov` | `pytest --cov --version` | wraps coverage.py |
| **coverage.py** | `uv add --dev coverage` / `pip install coverage` | `coverage --version` | usually pulled by pytest-cov |
| **hypothesis** (property testing) | `uv add --dev hypothesis` / `pip install hypothesis` | `python -c "import hypothesis"` | |

(These go in the project environment so they share its import path — not `pipx`.)

## Complexity

| Tool | Install (pipx) | Verify | Notes |
|------|----------------|--------|-------|
| **radon** (cyclomatic complexity) | `pipx install radon` | `radon --version` | `radon cc -s -n C .` |
| **lizard** (alt, multi-language CC) | `pipx install lizard` | `lizard --version` | `lizard --CCN 15` |
| **pylint** (CC + design checks) | `pipx install pylint` | `pylint --version` | `--enable=R0915,W0631`; heavier than ruff |

## Supply chain / advisories / licenses

| Tool | Install (pipx) | Verify | Notes |
|------|----------------|--------|-------|
| **pip-audit** | `pipx install pip-audit` | `pip-audit --version` | `pip-audit --strict`; `uv run pip-audit --strict` in uv projects |
| **pip-licenses** | `pipx install pip-licenses` | `pip-licenses --version` | `--fail-on='GPL.*;AGPL.*;BUSL.*;CC-BY-NC.*'` |

## Debugging & profiling

| Tool | Install | Verify | Notes |
|------|---------|--------|-------|
| **pdb** | built into CPython | `python -m pdb --help` | **no separate install** — `breakpoint()` |
| **ipdb** | `pipx install ipdb` or `uv add --dev ipdb` | `python -c "import ipdb"` | IPython-powered pdb |
| **debugpy** | `uv add --dev debugpy` / `pip install debugpy` | `python -c "import debugpy"` | VS Code / DAP, remote-capable |
| **pudb** | `pipx install pudb` | `python -c "import pudb"` | full-screen TUI debugger |
| **py-spy** (sampling profiler) | `pipx install py-spy` | `py-spy --version` | no code changes; profile a running PID |
| **objgraph** | `uv add --dev objgraph` / `pip install objgraph` | `python -c "import objgraph"` | object reference graphs (needs graphviz `dot`) |

## Docs

| Tool | Install (pipx) | Verify | Notes |
|------|----------------|--------|-------|
| **Sphinx** | `pipx install sphinx` | `sphinx-build --version` | autodoc for API docs |
| **pdoc** | `pipx install pdoc` | `pdoc --version` | lighter alternative to Sphinx |

## Data / external-data references (optional)

Only needed for the `references/duckdb-minio-s3-catalog.md` and
`references/external-data-e2e-seeding.md` smoke paths:

| Tool | Install | Verify | Notes |
|------|---------|--------|-------|
| **DuckDB** (Python) | `uv add duckdb` / `pip install duckdb` | `python -c "import duckdb"` | `httpfs` extension installed at runtime |
| **PyArrow** | `uv add pyarrow` / `pip install pyarrow` | `python -c "import pyarrow"` | S3 filesystem for Parquet writes |
| **Docker + Compose** | see `skills/tech/docker-dev` | `docker compose version` | local MinIO/S3 smoke test |

## One-shot baseline bootstrap

The everyday Python gate set (format/lint/typecheck/complexity/audit CLIs via
pipx; test deps go in the project env):

```bash
# macOS
brew install python@3.13 pipx uv
pipx ensurepath
pipx install ruff mypy radon pip-audit pip-licenses py-spy

# Debian/Ubuntu
sudo apt update && sudo apt install -y python3 python3-venv python3-pip pipx
curl -LsSf https://astral.sh/uv/install.sh | sh        # uv
pipx ensurepath
pipx install ruff mypy radon pip-audit pip-licenses py-spy
```

Then, inside the project (uv example):

```bash
uv sync                              # or: python -m venv .venv && . .venv/bin/activate && pip install -e .[dev]
uv add --dev pytest pytest-cov hypothesis
```
