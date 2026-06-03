---
name: codex-development
description: Codex software development workflow for code changes that require thoughtful design before implementation. Use when Codex is asked to implement, refactor, fix, or extend code and should first explore the codebase, compare 2-3方案 with trade-offs and difficulties, run an adversarial subAgent review with GPT-5.4-mini at xhigh reasoning, then synthesize feedback and execute the selected plan.
---

# Codex Development

Use this Skill for non-trivial coding work where design quality matters before edits begin.

## Mandatory Workflow

Follow this order. Do not skip the adversarial review unless the subagent tool is unavailable; if unavailable, state that clearly and perform a local adversarial review instead.

1. Explore the codebase first.
   - Read the relevant files, tests, local conventions, existing abstractions, and ownership boundaries.
   - Prefer `rg`, `rg --files`, `git status`, and focused file reads.
   - Do not start implementation while the design space is still unclear.

2. Propose 2-3 implementation方案.
   - Each方案 must include concrete scope, likely files touched, benefits, trade-offs, and 2-3 difficult points.
   - Include a clear recommendation, but do not treat it as final before review.
   - Prefer the smallest方案 that satisfies the user request and fits the existing codebase.

3. Start a subAgent for adversarial review.
   - Use the available subagent/multi-agent tool.
   - Set model to `gpt-5.4-mini`.
   - Set reasoning effort to `xhigh`.
   - If the exact model or reasoning effort is unavailable, use the closest available subAgent configuration and report the substitution before continuing.
   - Ask it to review the proposed方案 only, focusing on drawbacks, hidden assumptions, likely failure modes, missing tests, and simpler alternatives.
   - Pass only the necessary code/context and the方案 text. Do not ask it to implement.

4. Wait for the subAgent review when the next step depends on it.
   - Summarize the strongest objections.
   - Discard weak or irrelevant objections.
   - Revise the chosen方案 if the review reveals a better path.

5. Execute the chosen方案.
   - Make scoped edits using repository conventions.
   - Preserve unrelated user changes.
   - Add or update tests proportional to risk.
   - Run focused verification and report anything skipped.

6. Close out.
   - State which方案 was chosen and why.
   - State how the adversarial review changed the plan, if it did.
   - Summarize changed files and verification results.

## SubAgent Prompt Template

Use a prompt like this:

```text
Review these implementation方案 adversarially. Do not implement.

Focus on:
- hidden assumptions
- drawbacks and failure modes
- missing tests or verification
- simpler alternatives
- whether the recommendation is actually the best fit for the existing codebase

Required output:
- strongest objections by方案
- recommended方案 after review
- changes that should be made before implementation
```

## Design Standards

- A方案 is not complete unless it names the hard parts.
- Avoid speculative abstractions.
- Prefer explicit boundaries, clear failure, and direct code.
- If the request is tiny and the correct change is obvious, keep the方案 comparison brief but still identify alternatives and why they are worse.
- If the subAgent review conflicts with repository evidence, trust the codebase evidence and explain why.
