# Codex Skills

A multi-Skill repository for Codex workflows.

This repository follows the common public Skill-repo pattern: each Skill is a self-contained directory under `skills/<skill-name>/` with its own `SKILL.md`, optional `agents/`, `references/`, and `scripts/`.

The canonical skill list lives in `skills/manifest.tsv`; both installation and validation read from that manifest.

## Skills

| Skill | Purpose |
| --- | --- |
| `go-code-standards` | English Go code standards and enforcement workflow. |
| `go-code-standards-zh` | Chinese Go code standards. This is the source of truth for project-specific Go rules. |
| `codex-development` | Codex development workflow: explore code, compare 2-3方案, run adversarial subAgent review, then implement. |

## Migration From The Old Single-Skill Layout

Earlier versions exposed the Go standards Skill at the repository root. This repository is now intentionally multi-Skill, so root-level `SKILL.md` is no longer present. Install `go-code-standards` or `go-code-standards-zh` with `scripts/sync_skill.sh` instead of cloning the repository root into a skills directory.

## Install Or Update

Install the default Go standards Skill:

```bash
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash
```

Install a specific Skill:

```bash
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash -s -- --skill codex-development
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
${CODEX_HOME:-$HOME/.codex}/skills/codex-development
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

Strict mode requires recommended external tools such as `gofumpt`, `goimports`, and `golangci-lint`:

```bash
python3 ~/.codex/skills/go-code-standards/scripts/enforce_go_style.py --repo . --strict
```

## Go Rule Priority

The Chinese Go project rules are the source of truth:

1. `skills/go-code-standards-zh/references/project-rules.md`: highest-priority project rules taught by the user. These must be followed completely.
2. `skills/go-code-standards-zh/references/go-style-rules.md`: general Go style rules learned from Google Go Style and the Uber Go Style Guide.
3. Repository-local conventions, only when they do not violate the two rule layers above.

English synchronized files:

- `skills/go-code-standards/references/project-rules.md`
- `skills/go-code-standards/references/go-style-rules.md`

## Codex Development Skill

`codex-development` enforces a deliberate development workflow:

1. Explore the codebase before implementation.
2. Present 2-3方案 with trade-offs and 2-3 hard points.
3. Start a subAgent using `gpt-5.4-mini` with `xhigh` reasoning for adversarial方案 review.
4. Synthesize the review and choose the方案.
5. Execute scoped edits and verification.

## Local Development

Validate the repository:

```bash
scripts/validate_repo.sh
```

Install from a local checkout for testing:

```bash
GO_CODE_STANDARDS_REPO="$(pwd)" scripts/sync_skill.sh --skill codex-development
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
