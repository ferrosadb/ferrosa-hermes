# Instruct Skill Examples

Quick examples showing how to create each component type.

## Contents

- [Skill Examples](#skill-examples)
- [Workflow Examples](#workflow-examples)
- [Subagent Examples](#subagent-examples)
- [Rule Examples](#rule-examples)
- [Hook Examples](#hook-examples)
- [Subskill Examples](#subskill-examples)

## Skill Examples

### Security Reviewer (Auto-invoked)

**Request:** "Create a code reviewer for security"

```markdown
---
name: security-reviewer
# prettier-ignore
description: Reviews code for security vulnerabilities. Auto-activates when reviewing PRs or security-sensitive files.
---

# Security Review Guidelines

## When to Apply
- Pull request reviews
- Files handling authentication, authorization, or user input
- Database queries and API endpoints

## Key Checks
1. Input validation and sanitization
1. SQL injection prevention
1. XSS protection
1. Authentication/authorization logic
1. Sensitive data exposure
```

### React Guidelines (Auto-invoked)

**Request:** "Best practices for React components"

```markdown
---
name: react-guidelines
# prettier-ignore
description: React component best practices. Activates when working on .tsx/.jsx files.
---

# React Guidelines

## Component Structure
- Use functional components with hooks
- Keep components small and focused
- Extract logic to custom hooks

## State Management
- Prefer local state when possible
- Use context for shared state
- Consider external stores for complex state
```

### Test Runner (User-invoked only)

**Request:** "A command to run tests"

```markdown
---
name: test
# prettier-ignore
description: Run test suite with coverage
disable-model-invocation: true
argument-hint: [test-pattern]
---

# Run Tests

Run the test suite for: $ARGUMENTS

## Steps
1. Detect test framework (pytest, jest, etc.)
1. Run tests matching pattern if provided
1. Report results with coverage summary
```

## Workflow Examples

### Ship It Pipeline

**Request:** "A pipeline to test, lint, and deploy"

```markdown
---
name: ship-it
# prettier-ignore
description: End-to-end deployment workflow. Chains: test, lint, build, deploy.
argument-hint: [environment]
disable-model-invocation: true
---

# Ship It

Complete deployment pipeline for $ARGUMENTS environment.

## Steps

### Step 1: Run Tests
Run full test suite. Stop if any tests fail.

### Step 2: Lint Code
Run linters and formatters. Auto-fix where possible.

### Step 3: Build
Create production build artifacts.

### Step 4: Deploy
Deploy to specified environment with rollback capability.

## Error Handling
- Test failure: Stop immediately, report failures
- Lint failure: Attempt auto-fix, then re-check
- Build failure: Clean and retry once
- Deploy failure: Automatic rollback
```

## Subagent Examples

### Code Reviewer

**Request:** "Create an expert code reviewer"

```markdown
---
name: code-reviewer
# prettier-ignore
description: Expert code reviewer. Use proactively for PR reviews.
tools: Read, Grep, Glob
model: sonnet
---

You are an expert code reviewer focused on code quality and best practices.

## When Invoked
1. Read the changed files
1. Analyze for issues (bugs, style, performance)
1. Provide specific, actionable feedback
1. Summarize findings with severity levels

## Key Practices
- Be constructive and specific
- Suggest improvements, not just criticisms
- Focus on significant issues over nitpicks

## Output Format
## Review Summary
- **Critical**: [count] issues
- **Suggestions**: [count] items

## Issues
[Detailed findings with file:line references]

## Constraints
- Do not modify files
- Focus on the diff, not entire codebase
```

## Rule Examples

### TypeScript Strict Mode

**Request:** "Always use TypeScript strict mode"

```markdown
# TypeScript Rules

## Strict Mode Required

Enable strict mode in all TypeScript projects.

### Do
- Set `"strict": true` in tsconfig.json
- Address all type errors before committing
- Use explicit types for function parameters

### Don't
- Use `any` type without justification
- Disable strict checks with comments
- Ignore type errors

### Rationale
Strict mode catches bugs at compile time and improves code quality.
```

## Hook Examples

### Block Dangerous Commands

**Request:** "Prevent dangerous git commands"

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "if echo \"$TOOL_INPUT\" | grep -qE 'git (push --force|reset --hard|clean -fd)'; then echo 'Blocked dangerous git command'; exit 1; fi"
          }
        ]
      }
    ]
  }
}
```

### Auto-lint on Edit

**Request:** "Run linter after file edits"

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "pre-commit run --files \"$TOOL_INPUT_FILE_PATH\" 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

## Subskill Examples

### Parent Skill with Subskills

```markdown
---
name: try-it
# prettier-ignore
description: Run and test the current project. Detects project type and runs appropriate commands.
argument-hint: [test-description]
disable-model-invocation: true
subskills:
  - try-mcp-with-inspector
---
```

### Child Subskill

```markdown
---
name: try-mcp-with-inspector
# prettier-ignore
description: Discover and test MCP servers using the MCP Inspector with Streamable HTTP.
argument-hint: [url]
disable-model-invocation: true
parent-skill: try-it
---
```
