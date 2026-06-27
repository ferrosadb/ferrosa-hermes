---
name: instruct
# prettier-ignore
description: Create or refactor agent skills with progressive disclosure. Use when writing skills, restructuring skills for context efficiency, or creating subagents, rules, hooks, and workflows.
argument-hint: <description of what you want Claude to do>
supplementary-files:
  - examples.md
  - templates/skill.md
  - templates/workflow.md
  - templates/subagent.md
  - templates/rule.md
---

# Instruct: Create and Refactor Agent Skills

Create or refactor skills, subagents, rules, hooks, and workflows from a natural language description.

## Before you start (memory-first)

Before reading files or grepping for this skill's topic:
1. `ferrosa-memory.hybrid_search` on the task name and key nouns in `$ARGUMENTS`
2. `ferrosa-memory.retrieve_skills_for_context` with tags relevant to this skill's category
3. `ferrosa-memory.check_intentions` — act on any triggered intentions

If memory returns what you need, skip the discovery steps below. If you fall back to grep/find/read, call `record_outcome` with `program_type="retrieval_miss"` so the system learns.
```

The exact `retrieve_skills_for_context` tags should match the skill's category dir (e.g. `refactor` skill → tags include `task-level`, `refactor`).

#### 2. Forge tools mapping

A short table mapping each phase of the skill's workflow to the `frg` commands that replace raw Bash. Only list commands the skill actually uses; do **not** enumerate the whole forge catalog. Example:

```markdown
## Forge tools

Prefer these over raw Bash when the forge MCP server is available. They return structured JSON with `hint` fields on failure — cheaper and more reliable than parsing shell output.

| Step | frg command | What it replaces |
|------|-------------|------------------|
| Detect stack | `frg project-detect` | Hand-rolling `ls` + file-presence checks |
| Find smells | `frg smell-detect <path>` | grep for TODO + manual complexity review |
| ... | ... | ... |

**Fallback:** If forge is not available, use the raw commands referenced in each section below. Log the fallback — silent degradation is a bug (see `skills/rules/safety.md`).
```

Available `frg` commands at time of writing: `project-detect`, `project-summary`, `module-outline`, `smell-detect`, `doc-coverage`, `coverage-gate`, `concurrency-scan`, `dsm`, `dependency-tree`, `deps-audit`, `threat-scan`, `secret-scan`, `todo-extract`, `api-contract-diff`, `schema-diff`, `log-distill`, `log-monitor`, `merge-check`, `git-summary`, `mermaid-validate`, `find-definition`, `excerpt`, `glob`, `list`, `ingest`, `ingest-url`, `ingest-paper`, `fmem-skill-ingest`, `format-fix`, `lint-dedup`, `checklist-state`, `test-summary`, `tool-aliases`, `version`. Check `frg --help` before referencing a command — this list drifts.

### Progressive disclosure of tool detail

Tool-specific detail is **supplementary**, not inline. The SKILL.md body should say *which* `frg` command to run and *when* — the detailed flag reference, output schema, and failure modes belong in a supplementary file (e.g. `forge-reference.md`). This keeps SKILL.md under 300 lines and mirrors the ferrosa-memory guide's pattern: show the 90% path inline, defer the escape hatches to files Claude reads only when it hits a limit.

Mirror the same pattern for memory: inline the 4 tools from `MEMORY_GUIDE.md` (`hybrid_search`, `smart_ingest`, `create_edge`, `check_intentions`); defer `recursive_explore`, `spread_activation`, `find_memory_chain`, `query_derived`, `run_consolidation` to a supplementary file that's loaded only when the 4-tool path runs out.

### Supplementary file standards

1. **One level deep only.** SKILL.md references supplementary files. Supplementary files must NOT reference other supplementary files.
2. **Add a Contents section** to every supplementary file over 100 lines. Claude may partially read files — a TOC lets it navigate without reading everything.
3. **Use forward slashes** in all file paths (never backslashes).
4. **Name files descriptively:** `form-validation-rules.md`, not `doc2.md`
5. **Organize by domain** when a skill has multiple distinct domains:
   ```
   skill-name/
   ├── SKILL.md
   └── reference/
       ├── finance.md        # Revenue, billing metrics
       ├── sales.md          # Pipeline, accounts
       └── product.md        # API usage, features
   ```
6. **Bundled executable scripts** are for running, not reading. Make clear: "Run `script.py`" (execute) vs "See `algorithm.py`" (read as reference).

### Refactoring existing skills

When `$ARGUMENTS` mentions refactoring an existing skill:

1. **Check line count.** If over 500 lines, identify content to extract:
   - CLI command reference catalogs → `<name>-cli-reference.md` or `<name>-reference.md`
   - Per-provider sections (AWS/GCP/Azure) → `aws-patterns.md`, `gcp-patterns.md`, `azure-patterns.md`
   - Code pattern catalogs → `<name>-patterns.md`
   - Templates and examples → `templates/` directory
   - Validation/verification scripts → `scripts/` directory

2. **Check description length.** If over 250 characters, rewrite following frontmatter standards above.

3. **Check for argument-hint.** Add if missing. Format: `<required> [optional] [--flag <value>]`

4. **Create the supplementary files** with a Contents section at the top.

5. **Rewrite SKILL.md** to reference the supplementary files, keeping it under 500 lines (ideally under 300).

6. **Update frontmatter** to list all supplementary files in the `supplementary-files` field.

7. **Add the memory-first preamble and forge tools mapping** if missing (see "Required integration points" above). These are required sections for every skill — older skills predate the standard and need backfilling during refactor.

8. **Re-ingest into ferrosa-memory** after edits: `frg fmem-skill-ingest --root <research>/skills --filter <skill-name>`. The content hash makes this idempotent.

### Step 3: Use the Appropriate Template

For each component type, see the templates directory:

| Template | Location | Use For |
|----------|----------|---------|
| Skill | `templates/skill.md` in this skill folder | All skills (default) |
| Workflow | `templates/workflow.md` in this skill folder | Multi-step orchestrations |
| Subagent | `templates/subagent.md` in this skill folder | Isolated specialist execution |
| Rule | `templates/rule.md` in this skill folder | Always-on constraints |

For detailed examples, see `examples.md` in this skill folder.

### Step 4: Create the Component

1. **Analyze** `$ARGUMENTS` to determine component type
2. **If refactoring:** identify extraction targets per the refactoring guidelines above
3. **Generate** the component using the appropriate template
4. **Write** all files (SKILL.md and any supplementary files)
5. **Verify** SKILL.md is under 500 lines, description under 250 chars
6. **Explain** what was created and how to use it

### File Locations

```
.claude/
├── skills/
│   ├── repo/[name]/SKILL.md     # Repo-level skills
│   ├── project/[name]/SKILL.md  # Project-level skills
│   └── workflow/[name]/SKILL.md # Multi-step workflows
├── agents/[name].md             # Isolated subagents
└── rules/[name].md              # Always-on rules
```

### Multi-Agent Directory Conventions

Skills should be discoverable by Claude Code, OpenCode, and Codex. Place skills in the canonical `skills/` directory with proper `SKILL.md` frontmatter. Use `/warp` to link them into project-specific agent directories:

- `.claude/skills/<name>` — Claude Code discovery
- `.opencode/skills/<name>` — OpenCode discovery
- `.agents/skills/<name>` — Codex/AGENTS discovery

## Markdown Output

Generated skills, workflows, rules, and agent documents are Markdown documents.
Invoke and follow `/markdown-writing`, including `executive_summary` front
matter when the target format permits extra metadata. For `SKILL.md`, preserve
required skill front matter and avoid adding unsupported keys if the runtime
would reject them.

## Arguments

- `$ARGUMENTS` — Description of what you want Claude to create or refactor

## Core Principles

### Concise is key

The context window is a shared resource. Only add context the model does not already know:
- Does Claude really need this explanation? If yes, include it. If not, remove it.
- Every token in the frontmatter is **always in context**. Every token in SKILL.md is in context **when the skill is loaded**.
- Supplementary files are **only in context when explicitly read**. This is the primary progressive disclosure mechanism.

### Degrees of freedom

Match instruction specificity to task fragility:
- **Low freedom** (exact commands): database migrations, destructive operations, deployment steps
- **Medium freedom** (pseudocode with parameters): report generation, data transformations, configuration
- **High freedom** (text-based instructions): code reviews, analysis, creative tasks

### Progressive disclosure structure

```
Level 1: Frontmatter (always in context) — name, description, argument-hint
Level 2: SKILL.md body (in context when skill is loaded) — workflow, decisions, key patterns
Level 3: Supplementary files (only in context when explicitly read) — catalogs, templates, reference
```

**Rule:** Keep SKILL.md under 500 lines. Keep description under 250 characters. Reference supplementary files for detailed content.

## Step 1: Determine Component Type

| Type | Location | Create When Request Mentions... |
|------|----------|--------------------------------|
| **Skill** | `<name>/SKILL.md` | "guidelines", "best practices", "slash command", "auto-apply", "context for" |
| **Workflow** | `<name>/SKILL.md` | "pipeline", "end-to-end", "multi-step", "orchestrate", "chain skills" |
| **Subagent** | `.claude/agents/[name].md` | "reviewer", "specialist", "expert", "analyst", "isolated context" |
| **Rule** | `.claude/rules/[name].md` | "always", "never", "require", "enforce", "standard" |
| **Hook** | `settings.json` | "on save", "before edit", "after commit", "trigger" |

> Skills are the recommended way to create both auto-invoked context AND manual slash commands.

## Step 2: Apply Skill Authoring Standards

### Frontmatter standards

```yaml
---
name: kebab-case-name
# prettier-ignore
description: Concise WHAT + WHEN in 3rd person. Under 250 characters. Includes trigger keywords for discovery.
argument-hint: <mode> [options]
supplementary-files:
  - reference-catalog.md
  - templates/example-template.md
---
```

**Description rules:**
- Write in 3rd person ("Creates", not "Create" or "I can create")
- Include WHAT the skill does AND WHEN to use it
- Front-load trigger keywords for better skill matching
- Keep under 250 characters (hard cap 1024, but shorter is better)
- Never use first person ("I can") or second person ("You can use this")

**Good:** `Deploy Elixir/Phoenix on Fly.io with releases and clustering. Use when deploying, configuring CI/CD, or debugging production BEAM systems on Fly.io.`

**Bad:** `DevOps for Elixir/Phoenix on Fly.io — deployment, releases, Tigris object storage, clustering.` (Missing WHEN trigger, not 3rd person)

**Bad:** `I can help you deploy to Fly.io. You should use this when deploying Elixir.` (First and second person)

### SKILL.md body standards

**Target size:** under 500 lines. Under 300 lines for optimal performance.

**Structure:**
1. One-sentence purpose
2. Arguments section
3. When to Use section (matches frontmatter description)
4. Instructions section with numbered steps
5. For complex workflows: copyable checklist that Claude can track progress against
6. References to supplementary files using: `See <filename> in this skill folder.`

**Avoid in SKILL.md:**
- Lengthy CLI command catalogs → move to supplementary `reference.md`
- Per-provider/per-language sections → move to supplementary `patterns.md`
- Full templates → move to supplementary `templates/`
- Verification scripts → move to supplementary `scripts/`

### Supplementary file standards

1. **One level deep only.** SKILL.md references supplementary files. Supplementary files must NOT reference other supplementary files.
2. **Add a Contents section** to every supplementary file over 100 lines. Claude may partially read files — a TOC lets it navigate without reading everything.
3. **Use forward slashes** in all file paths (never backslashes).
4. **Name files descriptively:** `form-validation-rules.md`, not `doc2.md`
5. **Organize by domain** when a skill has multiple distinct domains:
   ```
   skill-name/
   ├── SKILL.md
   └── reference/
       ├── finance.md        # Revenue, billing metrics
       ├── sales.md          # Pipeline, accounts
       └── product.md        # API usage, features
   ```
6. **Bundled executable scripts** are for running, not reading. Make clear: "Run `script.py`" (execute) vs "See `algorithm.py`" (read as reference).

### Refactoring existing skills

When `$ARGUMENTS` mentions refactoring an existing skill:

1. **Check line count.** If over 500 lines, identify content to extract:
   - CLI command reference catalogs → `<name>-cli-reference.md` or `<name>-reference.md`
   - Per-provider sections (AWS/GCP/Azure) → `aws-patterns.md`, `gcp-patterns.md`, `azure-patterns.md`
   - Code pattern catalogs → `<name>-patterns.md`
   - Templates and examples → `templates/` directory
   - Validation/verification scripts → `scripts/` directory

2. **Check description length.** If over 250 characters, rewrite following frontmatter standards above.

3. **Check for argument-hint.** Add if missing. Format: `<required> [optional] [--flag <value>]`

4. **Create the supplementary files** with a Contents section at the top.

5. **Rewrite SKILL.md** to reference the supplementary files, keeping it under 500 lines (ideally under 300).

6. **Update frontmatter** to list all supplementary files in the `supplementary-files` field.

## Step 3: Use the Appropriate Template

For each component type, see the templates directory:

| Template | Location | Use For |
|----------|----------|---------|
| Skill | `templates/skill.md` in this skill folder | All skills (default) |
| Workflow | `templates/workflow.md` in this skill folder | Multi-step orchestrations |
| Subagent | `templates/subagent.md` in this skill folder | Isolated specialist execution |
| Rule | `templates/rule.md` in this skill folder | Always-on constraints |

For detailed examples, see `examples.md` in this skill folder.

## Step 4: Create the Component

1. **Analyze** `$ARGUMENTS` to determine component type
2. **If refactoring:** identify extraction targets per the refactoring guidelines above
3. **Generate** the component using the appropriate template
4. **Write** all files (SKILL.md and any supplementary files)
5. **Verify** SKILL.md is under 500 lines, description under 250 chars
6. **Explain** what was created and how to use it

### File Locations

```
.claude/
├── skills/
│   ├── repo/[name]/SKILL.md     # Repo-level skills
│   ├── project/[name]/SKILL.md  # Project-level skills
│   └── workflow/[name]/SKILL.md # Multi-step workflows
├── agents/[name].md             # Isolated subagents
└── rules/[name].md              # Always-on rules
```

### Multi-Agent Directory Conventions

Skills should be discoverable by Claude Code, OpenCode, and Codex. Place skills in the canonical `skills/` directory with proper `SKILL.md` frontmatter. Use `/warp` to link them into project-specific agent directories:

- `.claude/skills/<name>` — Claude Code discovery
- `.opencode/skills/<name>` — OpenCode discovery
- `.agents/skills/<name>` — Codex/AGENTS discovery
