---
name: luna-feature-development
description: Token-efficient feature development workflow. Use when the main agent should scope a code change, delegate the first implementation pass to one gpt-5.6-luna subAgent with minimal context, then review and finish the result.
---

# Luna Feature Development

Use this Skill for small to medium implementation, refactor, or bug-fix work where Luna can handle the first coding pass while the main agent owns scope and final quality.

## Workflow

1. Explore the relevant code, tests, conventions, and boundaries.
2. Summarize only the necessary change points: behavior, likely files, contracts, edge cases, and verification targets.
3. Start exactly one subAgent with model `gpt-5.6-luna` and reasoning `medium`. Do not fork the parent context; provide the repo path, request, constraints, change points, allowed scope, and checks in a compact prompt.
4. Review the subAgent's diff for incomplete behavior, contract violations, unnecessary changes, and missing tests.
5. Make final corrections in the main agent and run appropriate verification.

## Guardrails

- Use Luna for implementation, not product-scope decisions.
- Keep delegated context minimal, but include every constraint needed to avoid rework.
- Do not accept the subAgent result without inspecting the actual diff.
- Do not silently substitute another model. If `gpt-5.6-luna` is unavailable, report it and continue in the main agent only after making the fallback explicit.
