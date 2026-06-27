---
name: new-project
# prettier-ignore
description: Scaffolds a new project with best-practice structure. Use when starting a project, creating an app, or initializing a codebase. Supports Python, Elixir, Rust, Go, and Node/TypeScript.
tags: [repo-workflow]
argument-hint: <project-name> [description]
supplementary-files:
  - language-scaffolds.md
  - references/partner-industrial-prototype.md
---

# New Project

Initialize a new project in this repository.

## Markdown Output

Generated project documentation such as `CLAUDE.md`, `README.md`, and docs under
`specs/` must follow `/markdown-writing`, including `executive_summary` front
matter when the target document format permits it.

## Arguments

- `$ARGUMENTS` - The project name (required) and optional description

## Instructions

### Fast partner prototype mode

If the user specifies a stack, repo location, privacy/org target, and a demo thesis, act on those defaults instead of asking generic scaffold questions. For partner demos and exploratory prototypes, prefer a verified vertical slice over exhaustive upfront structure:

- Initialize the repo and remote with the requested visibility/org before broad implementation.
- Scaffold the named stack directly (for example Phoenix/Elixir when stated).
- Add containerized service boundaries for named dependencies such as databases or object storage.
- Implement one end-to-end UI/API path that makes the thesis visible.
- Add minimal adapter modules around external services, with feature flags or safe demo fallbacks if live integration is not yet required.
- Write concise blueprint/spec artifacts after the slice exists, reflecting real code plus open decisions.
- Verify with project-native tests and a container/dev run command before reporting completion.

Avoid stopping after a plan when the user asked to "build the repo" or emphasized working slices.

1. **Parse arguments** from `$ARGUMENTS`:
   - Extract the project name (first word/argument)
   - Extract optional description (remaining text)
   - If no project name provided, ask the user for one

2. **Determine the working directory**:
   - Use the current working directory (`pwd`) as the project root
   - All project creation commands run from this directory

3. **Ask language/framework**:
   - **Python** — using `uv` (library, application, or FastAPI backend)
   - **Elixir/Phoenix** — using `mix phx.new`
   - **Rust** — using `cargo init`
   - **Go** — using `go mod init`
   - **Node.js/TypeScript** — using `npm init`

4. **Ask project scope**:
   - **Backend-only**: Single language/framework project
   - **Full-stack**: Backend + Frontend (Next.js or Vite with shadcn)

5. **If full-stack, ask frontend preference**:
   - **Next.js** (default)
   - **Vite**

6. **If Python backend-only, determine library vs application**:
   - **Library**: Reusable Python package (published/imported by other projects)
   - **Application**: Standalone executable Python program or FastAPI service
   - If unclear from the project name/description, ask the user which type

7. **Create the project** based on selections. See `language-scaffolds.md` in this skill folder for per-language scaffolding instructions and full-stack project structures.

8. **Create CLAUDE.md** inside the project folder (see below).

9. **Provide summary** of what was created and how to run the project.

---

## Full-stack Project Layout

Create the project directory with `backend/` and `frontend/` subdirectories:

```
<project-name>/
├── backend/
└── frontend/
```

See `language-scaffolds.md` in this skill folder for backend and frontend scaffolding commands, project structures, and proxy configuration.

## CLAUDE.md Generation

Create a `CLAUDE.md` file inside the project root containing:

- **Project overview** — purpose, problem being solved, key design decisions
- **Development workflows** — how to start dev servers (both backend and frontend for full-stack), run tests, build for production
- **Project-specific conventions** — naming patterns, folder layout, anything non-obvious
- **Dependencies** — notable external services, environment variables, or prerequisites
