# Codex Skills

A multi-Skill repository for Codex workflows.

This repository follows the common public Skill-repo pattern: each Skill is a self-contained directory under `skills/<skill-name>/` with its own `SKILL.md`, optional `agents/`, `references/`, and `scripts/`.

The canonical skill list lives in `skills/manifest.tsv`; both installation and validation read from that manifest.

## Skills

| Skill | Purpose |
| --- | --- |
| `go-code-standards` | English Go style, readability, and maintainability review. |
| `go-code-standards-zh` | Chinese Go style review. This is the source of truth for project-specific style rules. |
| `normal-feature-development` | Normal small feature workflow: explore code, choose a simple approach, implement, and verify without subAgents. |
| `spark-feature-development` | Spark-assisted feature workflow: summarize change points, delegate implementation to Spark, then review and polish. |
| `code-risk-review` | Review changed code for bugs, field/data anomalies, ignored errors, concurrency, performance, logic, and runtime risks. |

## Migration From The Old Single-Skill Layout

Earlier versions exposed the Go standards Skill at the repository root. This repository is now intentionally multi-Skill, so root-level `SKILL.md` is no longer present. Install `go-code-standards` or `go-code-standards-zh` with `scripts/sync_skill.sh` instead of cloning the repository root into a skills directory.

## Install Or Update

Install the default Go standards Skill:

```bash
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash
```

Install a specific Skill:

```bash
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash -s -- --skill normal-feature-development
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash -s -- --skill spark-feature-development
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash -s -- --skill code-risk-review
```

Install the Chinese Go standards Skill:

```bash
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash -s -- --skill go-code-standards-zh
```

Install all Skills:

```bash
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash -s -- --all
```

Backward-compatible language aliases:

```bash
# English Go standards
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash -s -- --lang en

# Chinese Go standards
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash -s -- --lang zh
```

Default install paths:

```text
${CODEX_HOME:-$HOME/.codex}/skills/go-code-standards
${CODEX_HOME:-$HOME/.codex}/skills/go-code-standards-zh
${CODEX_HOME:-$HOME/.codex}/skills/normal-feature-development
${CODEX_HOME:-$HOME/.codex}/skills/spark-feature-development
${CODEX_HOME:-$HOME/.codex}/skills/code-risk-review
```

Re-run the same install command to update. Restart Codex after installing or updating so it can reload skills.

Security note: this repository ships executable scripts. For a new environment, inspect `scripts/sync_skill.sh` before piping it to `bash`.

## Use The Go Checks

Run from a Go repository:

```bash
python3 ~/.codex/skills/go-code-standards/scripts/enforce_go_style.py --repo .
```

Auto-format and clean imports when supported:

```bash
python3 ~/.codex/skills/go-code-standards/scripts/enforce_go_style.py --repo . --fix
```

Strict style mode requires recommended external style tools such as `gofumpt`, `goimports`, and `golangci-lint`:

```bash
python3 ~/.codex/skills/go-code-standards/scripts/enforce_go_style.py --repo . --strict
```

## Go Rule Priority

The Chinese Go style rules are the source of truth:

1. `skills/go-code-standards-zh/references/project-rules.md`: highest-priority style and maintainability rules taught by the user. These must be followed completely.
2. `skills/go-code-standards-zh/references/go-style-rules.md`: general Go style rules learned from Google Go Style and the Uber Go Style Guide.
3. Repository-local conventions, only when they do not violate the two rule layers above.

English synchronized files:

- `skills/go-code-standards/references/project-rules.md`
- `skills/go-code-standards/references/go-style-rules.md`

## Normal Small Feature Development Skill

`normal-feature-development` keeps ordinary implementation work direct:

1. Explore the codebase before implementation.
2. Choose the simplest workable approach; briefly compare options only when the implementation is not obvious.
3. Execute scoped edits that follow existing patterns.
4. Verify with checks appropriate to the touched surface.
5. Report files changed, verification results, and skipped checks.

## Spark Feature Development Skill

`spark-feature-development` delegates the first implementation pass to Spark:

1. Explore the codebase and summarize concrete change points.
2. Start one subAgent with model `5.3-codex-spark` and reasoning `high`.
3. Do not fork full context; pass the required repo path, constraints, change points, scope, and verification target in the subAgent task.
4. Have the subAgent implement the scoped change and report checks.
5. Main agent reviews the diff, adjusts the code, and runs final verification.

## Code Risk Review Skill

`code-risk-review` reviews only concrete risks in the current diff or staged changes:

1. Determine files from staged diff, `master...HEAD`, or current diff.
2. Group changed files by directory/module.
3. For small changes, roughly 3-5 files or fewer, review locally.
4. For larger changes, split work across 2-5 subAgents by module.
5. Main agent synthesizes findings, removes weak claims, and fixes real risks.

## Local Development

Validate the repository:

```bash
scripts/validate_repo.sh
```

Install from a local checkout for testing:

```bash
GO_CODE_STANDARDS_REPO="$(pwd)" scripts/sync_skill.sh --skill normal-feature-development
GO_CODE_STANDARDS_REPO="$(pwd)" scripts/sync_skill.sh --skill spark-feature-development
GO_CODE_STANDARDS_REPO="$(pwd)" scripts/sync_skill.sh --skill code-risk-review
GO_CODE_STANDARDS_REPO="$(pwd)" scripts/sync_skill.sh --all
```

Run script checks directly:

```bash
python3 -m py_compile scripts/validate_skill.py
python3 -m py_compile skills/go-code-standards/scripts/enforce_go_style.py
go run skills/go-code-standards/scripts/check_go_decl_order.go --repo .
bash -n scripts/sync_skill.sh
```

## Notes For Maintainers

- Keep each Skill self-contained under `skills/<skill-name>/`.
- Update Chinese Go project rules first, then synchronize English.
- Keep `SKILL.md` concise; put detailed guidance in `references/`.
- Keep scripts deterministic and low false-positive.
- Do not add pre-commit hook installation; the repository provides scripts only.
