---
name: go-code-standards
description: Review local Go expression: naming, comments, exports, declaration order, formatting, variable placement and struct literals. Review-only by default; data design, behavior abstraction, orchestration, contracts and failures belong to other specialties.
---

# Go Expression Review

Read references/project-rules.md, then references/go-style-rules.md. For Chinese reviews, read the corresponding .zh.md pair instead. Chinese rules prevail if translations differ.

Use the user-selected scope; otherwise review staged changes, or unstaged changes and relevant untracked files if the index is clean. For branch comparisons use the actual base's merge-base. Trace callers when needed to establish naming and export semantics. Report location, rule, impact and recommendation; say so when no findings exist. Edit only when fixes are requested.

Use the command below for mechanical checks. It does not run go vet/test by default. --fix modifies files and requires a request to fix. Checks establish formatting or partial declaration shapes, not semantic correctness.

```bash
python3 /path/to/go-code-standards/scripts/enforce_go_style.py --repo .
```

Function types, single-implementation interfaces and thin wrappers belong to abstraction-review. IDL/DB and state lifecycle belong to data-model-review; orchestration to main-flow-review; validation/defaulting to contract-boundary-review; concrete failures to code-risk-review.
