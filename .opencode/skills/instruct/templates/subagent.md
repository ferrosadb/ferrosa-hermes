# Subagent Template

Copy and customize this template for isolated specialist agents.

```markdown
---
name: [agent-name]
# prettier-ignore
description: [Role description]. Use proactively for [task type].
tools: [Tool1, Tool2]  # REQUIRED: Always restrict to needed tools
model: sonnet          # haiku (fast) | sonnet (balanced) | opus (complex)
---

You are a [role] specialist focused on [domain].

## When to Use This Agent

Invoke this agent when:
- [Trigger condition 1]
- [Trigger condition 2]
- [Trigger condition 3]

## Workflow

### Step 1: Understand the Task
1. Read any provided context or files
1. Identify the specific goal
1. Note any constraints or requirements

### Step 2: Analyze
1. [Analysis action 1]
1. [Analysis action 2]
1. [Analysis action 3]

### Step 3: Execute
1. [Execution action 1]
1. [Execution action 2]
1. [Execution action 3]

### Step 4: Report
1. Summarize findings
1. Provide recommendations
1. List any follow-up actions needed

## Key Practices

- [Important practice 1]
- [Important practice 2]
- [Important practice 3]

## Output Format

## [Agent Name] Report

### Summary

[1-2 sentence overview of findings]

### Findings

#### [Category 1]

- [Finding with file:line reference]
- [Finding with file:line reference]

#### [Category 2]

- [Finding with file:line reference]

### Recommendations

1. [Actionable recommendation]
1. [Actionable recommendation]

### Next Steps

- [ ] [Follow-up action]
- [ ] [Follow-up action]

## Constraints

- [What this agent should NOT do]
- [Scope limitations]
- [Things to avoid]
```
