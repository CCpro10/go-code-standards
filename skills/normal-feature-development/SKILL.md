---
name: normal-feature-development
description: Normal small feature development workflow. Use for ordinary implementation, refactor, or bug-fix work that needs code exploration, user-visible方案 comparison and decision points, scoped edits after user confirmation, and verification without starting subAgents.
---

# Normal Small Feature Development

Use this Skill for small to medium implementation, refactor, or bug-fix work where the change should stay direct and scoped.

## Workflow

1. Explore first: read relevant code, tests, conventions, and ownership boundaries. Prefer `rg`, `rg --files`, `git status`, and focused file reads.
2. Before editing code, expose the decision to the user: summarize 2-3 viable方案 with touched scope, benefits, trade-offs, hard points, and key decision points. If only one方案 is realistic, say why and ask for confirmation.
3. Wait for the user to choose or approve a方案. Do not modify files before that decision.
4. Implement the chosen方案 with focused edits that follow existing patterns. Avoid broad refactors unless they are required for the change.
5. Verify with the narrowest useful checks first, then broader tests when the touched surface justifies them.
6. Close with the chosen方案, files changed, verification results, and any skipped checks.

## Guardrails

- Do not start subAgents as part of this Skill.
- Do not turn a small change into a heavyweight design process.
- Do not skip user-visible方案 selection before code edits.
- If the change becomes large or risky, pause to state the new scope and choose a more appropriate workflow.
