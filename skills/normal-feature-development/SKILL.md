---
name: normal-feature-development
description: Normal small feature development workflow. Use for ordinary implementation, refactor, or bug-fix work that needs code exploration, a simple approach decision, scoped edits, and verification without starting subAgents.
---

# Normal Small Feature Development

Use this Skill for small to medium implementation, refactor, or bug-fix work where the change should stay direct and scoped.

## Workflow

1. Explore first: read relevant code, tests, conventions, and ownership boundaries. Prefer `rg`, `rg --files`, `git status`, and focused file reads.
2. Decide the simplest workable approach. If the implementation is not obvious, compare 2-3 options briefly with scope, trade-offs, and hard points.
3. Implement with focused edits that follow existing patterns. Avoid broad refactors unless they are required for the change.
4. Verify with the narrowest useful checks first, then broader tests when the touched surface justifies them.
5. Close with the approach used, files changed, verification results, and any skipped checks.

## Guardrails

- Do not start subAgents as part of this Skill.
- Do not turn a small change into a heavyweight design process.
- If the change becomes large or risky, pause to state the new scope and choose a more appropriate workflow.
