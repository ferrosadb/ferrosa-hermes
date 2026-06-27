# Workflow Template

Copy and customize this template for multi-step workflow skills.

```markdown
---
name: [workflow-name]
# prettier-ignore
description: [End-to-end workflow for X]. Chains: [step1], [step2], [step3].
argument-hint: [required arguments]
disable-model-invocation: true
---

# [Workflow Name]

[One sentence describing the complete workflow]

## Arguments

- `$ARGUMENTS` - [What the user provides and format expected]

## Overview

This workflow automates:
1. [First major phase]
1. [Second major phase]
1. [Third major phase]

## Prerequisites

- [Required tool/dependency 1]
- [Required tool/dependency 2]
- [Required state/condition]

## Steps

### Step 1: [Phase Name]

**Goal:** [What this step accomplishes]

**Actions:**
1. [Specific action]
1. [Specific action]

**Success criteria:** [How to know this step succeeded]

**On failure:** [What to do if this step fails]

### Step 2: [Phase Name]

**Goal:** [What this step accomplishes]

**Actions:**
1. [Specific action]
1. [Specific action]

**Success criteria:** [How to know this step succeeded]

**On failure:** [What to do if this step fails]

### Step 3: [Phase Name]

**Goal:** [What this step accomplishes]

**Actions:**
1. [Specific action]
1. [Specific action]

**Success criteria:** [How to know this step succeeded]

**On failure:** [What to do if this step fails]

## Error Handling

| Error | Recovery Action |
|-------|-----------------|
| [Error type 1] | [What to do] |
| [Error type 2] | [What to do] |
| [Error type 3] | [What to do] |

## Rollback Procedures

If the workflow fails partway through:
1. [Rollback step 1]
1. [Rollback step 2]

## Completion Summary

When all steps succeed, report:

[Workflow Name] Summary

Status: [Success/Partial/Failed]

Steps completed:

Artifacts:

- [Output 1]
- [Output 2]

Next steps:

- [What user should do next]

## Examples

### [Common use case 1]

/workflow-name [arguments]

[Description of what happens]

### [Common use case 2]

/workflow-name [different arguments]

[Description of what happens]

## Related Skills

- `/skill-1` - [How it relates]
- `/skill-2` - [How it relates]
```
