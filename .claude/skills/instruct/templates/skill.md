# Skill Template

Copy and customize this template for new skills.

```markdown
---
name: [kebab-case-name]
# prettier-ignore
description: [WHAT the skill does + WHEN to use it. 3rd person. Under 250 chars. Front-load trigger keywords.]
argument-hint: <mode> [options]
supplementary-files:
  - [reference-catalog.md]
  - [templates/example.md]
---

# [Skill Title]

[One sentence describing what this skill does and when to use it]

## Arguments

- `$ARGUMENTS` — Mode and options (see argument-hint)

## When to Use

[2-3 sentences matching the description. Include trigger scenarios that help discovery.]

## Instructions

### Step 1: [Name]

[High-level instructions. Reference supplementary files for details:]

- CLI reference → See `reference-catalog.md` in this skill folder
- Pattern examples → See `patterns.md` in this skill folder

### Step 2: [Name]

[Instructions continue. Use conditional branching for modes:]

**If mode X:** Follow the X workflow below.
**If mode Y:** Follow the Y workflow below.

## Progress Checklist

For complex workflows, copy and track progress:

```
Task Progress:
- [ ] Step 1: ...
- [ ] Step 2: ...
- [ ] Step 3: ...
```

## Notes

- [Key gotcha 1]
- [Key gotcha 2]
```

## Progressive Disclosure Guidelines

### SKILL.md body (always loaded when skill is invoked)

**Target size:** Under 500 lines (under 300 for optimal performance)

Keep in SKILL.md:
- Purpose and when-to-use triggers
- Step-by-step workflow and decision logic
- Key patterns that Claude won't know
- References to supplementary files

Move to supplementary files:
- CLI command catalogs (gcloud, az, aws)
- Per-provider sections (AWS/GCP/Azure patterns)
- Code pattern catalogs (language-specific idioms)
- Full templates and boilerplate
- Verification scripts and examples

### Supplementary files (loaded only when referenced)

Structure supplementary files with a Contents section if over 100 lines:

```markdown
# Reference Catalog Title

## Contents

- Section 1: Brief description
- Section 2: Brief description
- Section 3: Brief description

## Section 1

Content...
```

### Description guidelines

The `description` field is the most important line — it's always in context and determines when the skill is discovered.

**Good descriptions (3rd person, WHAT + WHEN, under 250 chars):**

```
description: Deploy Elixir/Phoenix on Fly.io with releases and clustering. Use when deploying, configuring CI/CD, or debugging production BEAM systems on Fly.io.

description: Rust with ownership, borrow checker, and cargo. Use when writing Rust code, managing memory safety, or debugging Rust applications.

description: Systematic FMEA for identifying failure modes and rating severity. Use when designing distributed systems, testing resilience, or before shipping critical features.
```

**Bad descriptions:**

```
description: DevOps for Elixir/Phoenix on Fly.io — deployment, releases, Tigris object storage, clustering.
(Missing WHEN trigger, not 3rd person)

description: I can help you deploy to Fly.io. You should use this when deploying Elixir.
(First and second person)

description: FMEA
(Too vague, no trigger keywords)
```

### One level of referencing

SKILL.md references supplementary files. Supplementary files must NOT reference other supplementary files. Keep references one level deep:

**Good:**
```
SKILL.md → See `aws-cli-reference.md`
SKILL.md → See `gcp-cli-reference.md`
```

**Bad:**
```
SKILL.md → See `advanced.md`
advanced.md → See `details.md`   ← Too deep, Claude may not follow
```
