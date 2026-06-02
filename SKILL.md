---
name: go-code-standards
description: Go code standards and enforcement workflow based on Google Go Style and the Uber Go Style Guide. Use when Codex writes, reviews, refactors, or gates Go code; when a repository needs Go style checks in CI or git hooks; or when enforcing formatting, imports, linting, tests, error handling, naming, interfaces, concurrency, and API hygiene in .go files.
---

# Go Code Standards

## Language Source

This is the default English skill. The Chinese files are the canonical source of truth:

- `SKILL.zh.md`
- `references/go-style-rules.zh.md`

Keep the English version synchronized with the Chinese version when rules change.

## Workflow

Use this skill for Go code changes, Go reviews, and repository-level Go quality gates.

1. Read the local repository conventions first: existing `Makefile`, CI, `.golangci.yml`, `go.mod`, package layout, generated-code policy, and test patterns.
2. Apply the style rules in `references/go-style-rules.md` when writing or reviewing code. Treat existing local conventions as binding unless they conflict with correctness, maintainability, or a stronger project standard.
3. Run `scripts/enforce_go_style.py` from the target repository before finishing.
4. Report any skipped checks and why. Do not claim enforcement passed if required tools were missing or tests were not run.

## Enforcement

Run the style gate from the repository root:

```bash
python3 /path/to/go-code-standards/scripts/enforce_go_style.py --repo .
```

For automatic formatting and import cleanup:

```bash
python3 /path/to/go-code-standards/scripts/enforce_go_style.py --repo . --fix
```

For a stricter CI gate that requires the recommended external tools:

```bash
python3 /path/to/go-code-standards/scripts/enforce_go_style.py --repo . --strict
```

To generate a starter `golangci-lint` config:

```bash
python3 /path/to/go-code-standards/scripts/enforce_go_style.py --repo . --write-golangci-config
```

## Install or Update

Install or update this skill into the local Codex skills directory:

```bash
bash /path/to/go-code-standards/scripts/sync_skill.sh
```

Or bootstrap directly from GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash
```

The script installs English by default to `${CODEX_HOME:-$HOME/.codex}/skills/go-code-standards`. Re-run the same command to update an existing local copy.

Install or update the Chinese version:

```bash
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash -s -- --lang zh
```

The Chinese version installs to `${CODEX_HOME:-$HOME/.codex}/skills/go-code-standards-zh` by default.

## Required Checks

Always run these when the repository has Go files:

- Formatting: `gofmt`; prefer `gofumpt` when available or required by the repo.
- Imports: `goimports` when available or in strict mode.
- Modules: `go mod tidy` verification when `go.mod` exists.
- Package declarations: exported package-level functions and methods must appear before unexported ones in each package; uppercase names are forbidden in the unexported section.
- Local clarity: delay declaring variables until they are needed when earlier failure paths could make them unused; construct large business structs with keyed composite literals instead of declaring an empty value and assigning fields one by one.
- Boundary clarity: do not hide input cleanup, filtering, deduplication, and defaulting behind vague normalization names; validate business inputs at the boundary and fail clearly when required fields are invalid.
- Static checks: `go vet ./...`.
- Tests: `go test ./...`, unless the user explicitly asks to skip tests.
- Linting: `golangci-lint run ./...` when configured or in strict mode.

## Review Priorities

Prioritize issues in this order:

1. Correctness, data races, goroutine leaks, cancellation, timeout propagation, and resource cleanup.
2. Public API clarity: naming, comments for exported symbols, small interfaces, and stable error behavior.
3. Maintainability: simple control flow, small cohesive packages, explicit dependencies, and table-driven tests.
4. Style consistency: formatting, import grouping, receiver names, initialisms, error wrapping, and logging.

Use `references/go-style-rules.md` for the compact style checklist and source links.
