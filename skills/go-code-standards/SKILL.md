---
name: go-code-standards
description: Go style, readability, and maintainability review Skill. Use to review directory depth, package responsibility, struct necessity, function and method shape, comments, naming, formatting, and local readability. Assume code logic is correct; do not use for concurrency issues, suspicious bugs, performance problems, or business logic errors.
---

# Go Style Standards

This Skill only handles style, readability, and maintainability. It assumes the code logic is correct and asks whether the implementation is awkward, hard to read, or hard to maintain.

Use `code-risk-review` for risk review.

## Workflow

1. Read local conventions first: directory layout, package organization, existing struct/function style, comments, and formatting tools.
2. Apply `references/project-rules.md` first, then `references/go-style-rules.md`.
3. For mechanical constraints, run `scripts/enforce_go_style.py`. By default it only runs style checks, not `go vet` or `go test`.
4. Report only style, readability, and maintainability issues. Do not report concurrency, performance, or logic bugs unless they directly show up as structure, naming, or maintainability problems.

## Mechanical Checks

```bash
python3 /path/to/go-code-standards/scripts/enforce_go_style.py --repo .
```

Auto-fix formatting and imports:

```bash
python3 /path/to/go-code-standards/scripts/enforce_go_style.py --repo . --fix
```

## Review Scope

- Directory depth and package responsibility; suggest file or directory splits only, without performing heavy moves before user confirmation.
- Whether structs are necessary and clear, without excessive intermediate types; whether exported structs and their fields have clear comments.
- Whether functions and methods are split reasonably, without too many one-off helpers, meaningless wrapper functions, or function aliases.
- Whether the most important exported functions are first and unexported functions are last.
- Whether comments add information and names reveal real behavior.
- Whether defaults, internal engineering fallbacks, or deep `normalizeXxx` helpers hide invalid states.
- Whether local variable timing, struct construction, blank lines, and line breaks improve readability.

Read `references/project-rules.md` first, then `references/go-style-rules.md`.
