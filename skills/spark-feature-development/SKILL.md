---
name: spark-feature-development
description: Spark-assisted feature development workflow. Use for implementation, refactor, or bug-fix work where Codex should explore the codebase, summarize concrete change points, start one 5.3-codex-spark high subAgent to write code, then review and polish the result.
---

# Spark Feature Development

Use this Skill for small to medium code changes where the main agent should keep ownership of planning, review, and final quality while delegating the first implementation pass to Spark.

## Workflow

1. Explore first: read relevant code, tests, conventions, and ownership boundaries. Prefer `rg`, `rg --files`, `git status`, and focused file reads.
2. Summarize concrete change points before delegation: intended behavior, files/modules likely touched, important contracts, edge cases, and verification targets.
3. Start exactly one subAgent with model `5.3-codex-spark` and reasoning `high`. Ask it to implement the summarized change points, stay scoped, follow existing patterns, and report changed files plus checks run.
4. Review the subAgent result yourself: inspect `git diff`, check whether every change point was handled, look for missed edge cases, contract violations, excess refactors, and missing tests.
5. Make final adjustments in the main agent. Run appropriate verification, or clearly report why a check could not run.
6. Close with change points covered, subAgent output reviewed, final files changed, and verification results.

## SubAgent Prompt

```text
Implement the summarized code change. Stay within the listed files/modules unless the codebase requires a small adjacent edit.
Follow existing patterns and keep the diff scoped. Add or update focused tests when the change needs coverage.
Report changed files, key decisions, and verification commands/results. Do not do broad refactors.
```

## Guardrails

- Do not let the subAgent choose the product scope; the main agent owns the change points.
- Do not accept the subAgent diff without review.
- If the requested subAgent model is unavailable, say so and continue only after choosing an explicit fallback.
