# Rule Template

Copy and customize this template for always-on rules.

```markdown
# [Rule Category]

Rules for [what area/domain this covers].

## [Specific Rule Name]

[One-sentence summary of what this rule enforces]

### Do

- [Required behavior 1]
- [Required behavior 2]
- [Required behavior 3]

### Don't

- [Prohibited behavior 1]
- [Prohibited behavior 2]
- [Prohibited behavior 3]

### Rationale

[Why this rule exists and what problems it prevents]

### Examples

**Good:**
```[language]
[Code or behavior example that follows the rule]
```

**Bad:**

```[language]
[Code or behavior example that violates the rule]
```

---

## [Another Rule Name]

[One-sentence summary]

### Do

- [Required behavior]

### Don't

- [Prohibited behavior]

### Rationale

[Why this rule exists]

```

## Rule Placement

| Location | Scope |
|----------|-------|
| `~/.claude/rules/` | Global (all projects) |
| `.claude/rules/` | Project-specific |

## Best Practices for Rules

1. **Be specific** - Vague rules are hard to follow
1. **Include rationale** - Helps understand the "why"
1. **Provide examples** - Show good and bad patterns
1. **Keep focused** - One concept per rule file
1. **Use actionable language** - "Do X" not "Try to X"
