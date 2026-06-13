---
name: spark-feature-development
description: Spark-assisted feature development workflow. Use for implementation, refactor, or bug-fix work where Codex should explore the codebase, summarize concrete change points, start one 5.3-codex-spark high subAgent to write code, then review and polish the result.
---

# Spark Feature Development

Use this Skill for small to medium code changes where the main agent should keep ownership of planning, review, and final quality while delegating the first implementation pass to Spark.

## Workflow

1. Explore first: read relevant code, tests, conventions, and ownership boundaries. Prefer `rg`, `rg --files`, `git status`, and focused file reads.
2. Summarize concrete change points before delegation: intended behavior, files/modules likely touched, important contracts, edge cases, and verification targets.
3. Start exactly one subAgent with model `5.3-codex-spark` and reasoning `high`. Do not fork the full current context; pass only the necessary repo path, user request, constraints, change points, scope, and verification target in the subAgent task so the model parameters remain controllable.
4. Review the subAgent result yourself: inspect `git diff`, check whether every change point was handled, look for missed edge cases, contract violations, excess refactors, and missing tests.
5. Make final adjustments in the main agent. Run appropriate verification, or clearly report why a check could not run.
6. Close with change points covered, subAgent output reviewed, final files changed, and verification results.

## SubAgent Prompt

```text
Implement the summarized code change. Stay within the listed files/modules unless the codebase requires a small adjacent edit.
Use only the context provided in this task. Do not assume access to the parent agent's full conversation context.
Follow existing patterns and keep the diff scoped. Add or update focused tests when the change needs coverage.
Report changed files, key decisions, and verification commands/results. Do not do broad refactors.
```

## Guardrails

- Do not let the subAgent choose the product scope; the main agent owns the change points.
- Do not accept the subAgent diff without review.
- Do not fork full context when launching the subAgent. If the subAgent tool cannot set `5.3-codex-spark` and `high` while forking context, disable context forking and write the required context into the task.
- If the requested subAgent model is unavailable, say so and continue only after choosing an explicit fallback.
