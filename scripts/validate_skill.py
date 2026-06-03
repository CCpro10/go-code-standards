#!/usr/bin/env python3
"""Validate this multi-skill repository without external Python packages."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
MANIFEST = SKILLS_DIR / "manifest.tsv"
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


def validate_skill(skill_dir: Path) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        fail(f"{skill_dir}: missing SKILL.md")

    fields = parse_frontmatter(skill_md)
    name = fields.get("name", "")
    description = fields.get("description", "")

    if name != skill_dir.name:
        fail(f"{skill_md}: expected name {skill_dir.name!r}, got {name!r}")
    if not NAME_RE.match(name):
        fail(f"{skill_md}: name must be hyphen-case")
    if len(name) > 64:
        fail(f"{skill_md}: name is longer than 64 characters")
    if not description:
        fail(f"{skill_md}: description is required")
    if len(description) > 1024:
        fail(f"{skill_md}: description is longer than 1024 characters")
    if "<" in description or ">" in description:
        fail(f"{skill_md}: description must not contain angle brackets")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if not openai_yaml.is_file():
        fail(f"{skill_dir}: missing agents/openai.yaml")


def require_file(relative: str) -> None:
    path = ROOT / relative
    if not path.is_file():
        fail(f"missing required file: {relative}")


def require_executable(relative: str) -> None:
    path = ROOT / relative
    require_file(relative)
    if not path.stat().st_mode & 0o111:
        fail(f"script is not executable: {relative}")


def read_manifest() -> dict[str, str]:
    if not MANIFEST.is_file():
        fail("missing skills/manifest.tsv")

    skills: dict[str, str] = {}
    for lineno, line in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            fail(f"skills/manifest.tsv:{lineno}: expected two tab-separated columns")
        name, description = parts
        if not NAME_RE.match(name):
            fail(f"skills/manifest.tsv:{lineno}: invalid skill name: {name}")
        if not description.strip():
            fail(f"skills/manifest.tsv:{lineno}: description is required")
        if name in skills:
            fail(f"skills/manifest.tsv:{lineno}: duplicate skill name: {name}")
        skills[name] = description
    if not skills:
        fail("skills/manifest.tsv: no skills listed")
    return skills


def main() -> int:
    if not SKILLS_DIR.is_dir():
        fail("missing skills/ directory")

    manifest = read_manifest()
    found = {path.name for path in SKILLS_DIR.iterdir() if path.is_dir()}
    expected = set(manifest)
    missing = expected - found
    if missing:
        fail("missing expected skills: " + ", ".join(sorted(missing)))
    extra = found - expected
    if extra:
        fail("skill directories missing from manifest: " + ", ".join(sorted(extra)))

    for skill_dir in sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir()):
        validate_skill(skill_dir)

    require_file("README.md")
    require_file(".github/workflows/validate.yml")

    for relative in (
        "scripts/sync_skill.sh",
        "scripts/validate_repo.sh",
        "scripts/validate_skill.py",
    ):
        require_executable(relative)

    print("[ok] multi-skill repository metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
