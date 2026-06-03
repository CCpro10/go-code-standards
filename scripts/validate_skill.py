#!/usr/bin/env python3
"""Validate this repository's Skill files without external Python packages."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^[a-z0-9-]+$")


def fail(message: str) -> None:
    print(f"[fail] {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path}: missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        fail(f"{path}: invalid YAML frontmatter terminator")

    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            fail(f"{path}: invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"')
        if key not in {"name", "description"}:
            fail(f"{path}: unexpected frontmatter key: {key}")
        fields[key] = value
    return fields


def validate_skill(path: Path, expected_name: str) -> None:
    fields = parse_frontmatter(path)
    name = fields.get("name", "")
    description = fields.get("description", "")

    if name != expected_name:
        fail(f"{path}: expected name {expected_name!r}, got {name!r}")
    if not NAME_RE.match(name):
        fail(f"{path}: name must be hyphen-case")
    if len(name) > 64:
        fail(f"{path}: name is longer than 64 characters")
    if not description:
        fail(f"{path}: description is required")
    if len(description) > 1024:
        fail(f"{path}: description is longer than 1024 characters")
    if "<" in description or ">" in description:
        fail(f"{path}: description must not contain angle brackets")


def require_file(relative: str) -> None:
    path = ROOT / relative
    if not path.is_file():
        fail(f"missing required file: {relative}")


def require_executable(relative: str) -> None:
    path = ROOT / relative
    require_file(relative)
    if not path.stat().st_mode & 0o111:
        fail(f"script is not executable: {relative}")


def main() -> int:
    validate_skill(ROOT / "SKILL.md", "go-code-standards")
    validate_skill(ROOT / "SKILL.zh.md", "go-code-standards-zh")

    for relative in (
        "README.md",
        "agents/openai.yaml",
        "agents/openai.zh.yaml",
        "references/project-rules.md",
        "references/project-rules.zh.md",
        "references/go-style-rules.md",
        "references/go-style-rules.zh.md",
    ):
        require_file(relative)

    for relative in (
        "scripts/enforce_go_style.py",
        "scripts/sync_skill.sh",
        "scripts/validate_repo.sh",
        "scripts/validate_skill.py",
    ):
        require_executable(relative)

    print("[ok] skill repository metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
