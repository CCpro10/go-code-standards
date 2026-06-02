# Go Code Standards Skill

Go code standards for Codex, with executable checks and bilingual Skill files.

中文规则是基准，英文版本保持同步；安装默认使用英文。

## What It Does

This Skill helps Codex write, review, and gate Go code with standards inspired by Google Go Style and the Uber Go Style Guide, plus project-specific rules for clearer business boundaries.

It includes:

- `SKILL.md`: English Skill, installed by default.
- `SKILL.zh.md`: Chinese Skill, canonical source of truth.
- `references/project-rules.md`: English project rules.
- `references/project-rules.zh.md`: Chinese project rules, highest-priority source of truth.
- `references/go-style-rules.md`: English general Go style reference.
- `references/go-style-rules.zh.md`: Chinese general Go style reference.
- `scripts/enforce_go_style.py`: Main enforcement script.
- `scripts/check_go_decl_order.go`: Go AST checker for package declaration ordering.
- `scripts/sync_skill.sh`: Installer/updater for local Codex skills.

## Install or Update

Install or update the default English Skill:

```bash
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash
```

Install or update the Chinese Skill:

```bash
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash -s -- --lang zh
```

Default install paths:

```text
English: ${CODEX_HOME:-$HOME/.codex}/skills/go-code-standards
Chinese: ${CODEX_HOME:-$HOME/.codex}/skills/go-code-standards-zh
```

Re-run the same install command to update. Restart Codex after installing or updating so it can reload skills.

## Use The Checks

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

## Enforced Rules

The script enforces rules that are deterministic enough for automation:

- `gofmt`, and `gofumpt` when available or required.
- `goimports` when available or strict.
- `go mod tidy` verification when `go.mod` exists.
- Package-level exported functions and methods must appear before unexported ones.
- `go vet ./...`.
- `go test ./...`.
- `golangci-lint run ./...` when configured or strict.

Some business-boundary rules are documented as review rules because hard-failing them with scripts would create too many false positives.

## Rule Philosophy

The Chinese rules are the source of truth:

1. `references/project-rules.zh.md`: highest-priority project rules taught by the user. These must be followed completely.
2. `references/go-style-rules.zh.md`: general Go style rules learned from Google Go Style and the Uber Go Style Guide.
3. Repository-local conventions, only when they do not violate the two rule layers above.

Read the full rule set:

- Chinese project rules: `references/project-rules.zh.md`
- Chinese general style rules: `references/go-style-rules.zh.md`
- English project rules: `references/project-rules.md`
- English general style rules: `references/go-style-rules.md`

## Local Development

Validate the Skill:

```bash
uv run --with PyYAML python /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

Validate the Chinese variant:

```bash
tmp="$(mktemp -d)"
cp -R . "$tmp/skill"
cp "$tmp/skill/SKILL.zh.md" "$tmp/skill/SKILL.md"
cp "$tmp/skill/references/project-rules.zh.md" "$tmp/skill/references/project-rules.md"
cp "$tmp/skill/references/go-style-rules.zh.md" "$tmp/skill/references/go-style-rules.md"
cp "$tmp/skill/agents/openai.zh.yaml" "$tmp/skill/agents/openai.yaml"
uv run --with PyYAML python /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$tmp/skill"
rm -rf "$tmp"
```

Run script checks:

```bash
python3 -m py_compile scripts/enforce_go_style.py
go run scripts/check_go_decl_order.go --repo .
bash -n scripts/sync_skill.sh
```

## Notes For Maintainers

- Update Chinese rules first.
- Keep English rules synchronized with Chinese rules.
- Keep `SKILL.md` concise; put detailed guidance in `references/`.
- Keep scripts deterministic and low false-positive.
- Do not add pre-commit hook installation; the repository provides scripts only.
