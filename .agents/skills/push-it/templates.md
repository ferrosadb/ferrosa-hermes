# Push Skill PR Templates

Ready-to-use PR templates for different types of changes.

## Contents

- [Feature PR Template](#feature-pr-template)
- [Bug Fix PR Template](#bug-fix-pr-template)
- [Refactor PR Template](#refactor-pr-template)
- [Documentation PR Template](#documentation-pr-template)
- [Dependencies Update PR Template](#dependencies-update-pr-template)
- [Large PR Template](#large-pr-template)
- [How to Use Templates](#how-to-use-templates)

## Feature PR Template

```markdown
## Summary
- Add <feature description>
- Implement <key functionality>

## Changes
- `path/to/file.py`: Added new service
- `path/to/test.py`: Added tests

## Test Plan
- [ ] Run unit tests
- [ ] Manual testing of feature
- [ ] Verify no regressions
```

## Bug Fix PR Template

```markdown
## Summary
- Fix <bug description>
- Root cause: <explanation>

## Changes
- `path/to/file.py`: Fixed condition that caused bug

## Test Plan
- [ ] Verify bug is fixed
- [ ] Run regression tests
- [ ] Test edge cases

## Related Issues
Fixes #<issue-number>
```

## Refactor PR Template

```markdown
## Summary
- Refactor <component/area>
- No functional changes

## Changes
- Renamed X to Y for clarity
- Extracted common logic to utility
- Updated imports across codebase

## Test Plan
- [ ] All existing tests pass
- [ ] No behavioral changes
```

## Documentation PR Template

```markdown
## Summary
- Update documentation for <area>
- Add/improve <specific content>

## Changes
- `docs/file.md`: Added section on X
- `README.md`: Updated installation instructions

## Review Notes
- No code changes
- Documentation only
```

## Dependencies Update PR Template

```markdown
## Summary
- Update project dependencies
- Security patches / version bumps

## Changes
- `pyproject.toml`: Updated dependency versions
- `uv.lock`: Regenerated lockfile

## Test Plan
- [ ] All tests pass with new dependencies
- [ ] No breaking changes in updated packages
- [ ] Security advisories addressed

## Dependency Changes
| Package | Old Version | New Version |
|---------|-------------|-------------|
| package1 | 1.0.0 | 1.1.0 |
| package2 | 2.0.0 | 2.0.1 |
```

## Large PR Template

For PRs with significant changes (>500 lines or >20 files):

```markdown
## Summary
<High-level description of the change>

## Motivation
<Why this change is needed>

## Changes Overview

### <Area 1>
- <Change description>
- <Change description>

### <Area 2>
- <Change description>

### <Area 3>
- <Change description>

## Architecture Decisions
- <Decision 1 and rationale>
- <Decision 2 and rationale>

## Test Plan
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing checklist:
  - [ ] <Scenario 1>
  - [ ] <Scenario 2>

## Migration Notes
<If applicable, describe any migration steps>

## Screenshots
<If UI changes, include before/after screenshots>

## Related PRs / Issues
- #<related-pr-number>
- Fixes #<issue-number>
```

## How to Use Templates

When creating a PR, the `/repo/push-it` skill will:

1. Analyze your commits to determine PR type
1. Select the appropriate template
1. Fill in details from commit messages and changed files
1. Present for review before creating

You can override by specifying intent in arguments:

```
/repo/push-it This is a security fix for CVE-123
```
