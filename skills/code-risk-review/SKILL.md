---
name: code-risk-review
description: "Code risk review workflow for changed files. Use to inspect git diff or staged changes for risk items only: suspicious bugs, logic errors, concurrency problems, performance regressions, resource leaks, API contract issues, and other correctness risks. Splits large reviews across 2-5 subAgents by module, then synthesizes and fixes."
---

# Code Risk Review

Use this Skill for risk review only. Do not comment on style, naming, formatting, or readability unless it creates a concrete risk.

## Workflow

1. Determine scope: prefer staged changes with `git diff --cached --name-only`; otherwise use `git diff --name-only master...HEAD`; if unavailable, use `git diff --name-only`.
2. Read the relevant diff and group changed files by directory/module.
3. If the change is small, roughly 3-5 files or fewer, review locally without subAgents.
4. If larger, split review by module and start 2-5 subAgents. Each subAgent reviews only assigned files for risk items.
5. Main agent synthesizes findings, removes duplicates/weak claims, decides fixes, then edits code if fixes are needed.

## Review Only These Risks

- Concurrency bugs, races, leaks, cancellation or timeout problems.
- Suspicious bugs, nil/empty edge cases, wrong error handling, resource leaks.
- Performance regressions, unnecessary fan-out, repeated heavy work, avoidable allocations.
- Logic errors, state transitions, off-by-one, ordering, idempotency, contract violations.
- API/data compatibility risks and security-sensitive mistakes.

## Output

Lead with concrete findings: severity, file/line, risk, why it matters, and suggested fix. If no risk is found, say so and mention residual test gaps.
