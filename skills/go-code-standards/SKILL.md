---
name: go-code-standards
description: Go design, style, readability, and maintainability review Skill. Use to review IDLs, database schemas, core struct fields, package responsibility, function and method shape, comments, naming, and long-term maintainability. Assume code logic is correct; do not use for concurrency issues, suspicious bugs, performance problems, or business logic errors.
---

# Go Style Standards

This Skill handles data-structure design, style, readability, and long-term maintainability. It assumes the code logic is correct and asks whether the IDL, database schema, core structs, and resulting implementation are clear, stable, and appropriate for the business context and Go best practices.

Use `code-risk-review` for risk review.

## Workflow

1. Read business invariants, data access patterns, and local conventions first: IDLs, database schemas, core structs, directory layout, package organization, existing function style, comments, and formatting tools.
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

- Whether data structures are designed before implementation; review IDLs, database schemas, and core struct fields before deciding whether functions are compensating for a weak model.
- Whether IDLs express field semantics, presence, units, enums, and compatibility precisely, and whether database schemas express keys, constraints, nullability, indexes, lifecycle, and access patterns clearly.
- Whether core structs represent stable domain concepts and invariants, with one source of truth, clear ownership and lifecycle, long-term maintainability, and practices appropriate to the current system.
- Directory depth and package responsibility; suggest file or directory splits only, without performing heavy moves before user confirmation.
- Whether structs are necessary and clear, without excessive intermediate types; whether exported structs and their fields have clear comments.
- Whether functions and methods are split reasonably, failure paths return early before a clear sequential main flow, and the code avoids excessive one-off helpers or function-parameter abstractions, meaningless pass-through functions that should be inlined, `var` function aliases, or constant aliases.
- Whether the most important exported functions are first and unexported functions are last.
- Whether function comments describe the actual execution order, selection conditions, and what happens when a condition does not match; whether function names accurately correspond to all behavior they perform, collections use concrete plural element names, and maps use `<key>2<value>` names.
- Whether defaults, internal engineering fallbacks, or deep `normalizeXxx` helpers hide invalid states.
- Whether local variable timing, struct construction, blank lines, and line breaks improve readability.

Read `references/project-rules.md` first, then `references/go-style-rules.md`.
