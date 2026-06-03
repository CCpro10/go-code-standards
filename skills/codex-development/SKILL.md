---
name: codex-development
description: Codex development workflow for non-trivial code changes. Use when Codex should explore the codebase, compare 2-3 implementation方案 with difficulties and trade-offs, run a GPT-5.4-mini xhigh adversarial subAgent review, then synthesize feedback and execute the selected方案.
---

# Codex Development

Use this Skill for implementation, refactor, or bug-fix work that needs design before edits.

## Workflow

1. Explore first: read relevant code, tests, conventions, and ownership boundaries. Prefer `rg`, `rg --files`, `git status`, and focused file reads.
2. Propose 2-3方案: include scope, files likely touched, benefits, trade-offs, and 2-3 hard points for each. Recommend one方案, but keep it provisional.
3. Start an adversarial subAgent: model `gpt-5.4-mini`, reasoning `xhigh`. If unavailable, use the closest available configuration and say so.
4. Ask the subAgent to review only the方案, not implement. It should find drawbacks, hidden assumptions, failure modes, missing tests, and simpler alternatives.
5. Synthesize the review, revise the plan if needed, then implement the chosen方案 with scoped edits and appropriate verification.
6. Close with the chosen方案, how review changed it, files changed, and verification results.

## SubAgent Prompt

```text
Review these implementation方案 adversarially. Do not implement.
Focus on hidden assumptions, drawbacks, failure modes, missing tests, and simpler alternatives.
Return strongest objections, recommended方案, and changes needed before implementation.
```
