#!/usr/bin/env bash
set -euo pipefail

repo_url="${GO_CODE_STANDARDS_REPO:-https://github.com/CCpro10/go-code-standards.git}"
lang="${GO_CODE_STANDARDS_LANG:-en}"
target=""

usage() {
  cat <<'USAGE'
Usage: sync_skill.sh [--lang en|zh] [--target /path/to/skill]

Installs or updates go-code-standards into the local Codex skills directory.
Default language is English.

Examples:
  sync_skill.sh
  sync_skill.sh --lang zh
  sync_skill.sh --lang en --target "$HOME/.codex/skills/go-code-standards"

Environment:
  GO_CODE_STANDARDS_REPO    Git repository URL. Defaults to the public GitHub repo.
  GO_CODE_STANDARDS_LANG    en or zh. Defaults to en.
  GO_CODE_STANDARDS_TARGET  Install target. Overrides the default target.
  CODEX_HOME                Codex home. Defaults to "$HOME/.codex".
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --lang)
      lang="${2:-}"
      shift 2
      ;;
    --target)
      target="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "${lang}" in
  en)
    skill_name="go-code-standards"
    ;;
  zh)
    skill_name="go-code-standards-zh"
    ;;
  *)
    echo "--lang must be en or zh" >&2
    exit 2
    ;;
esac

if [[ -z "${target}" ]]; then
  target="${GO_CODE_STANDARDS_TARGET:-${CODEX_HOME:-${HOME}/.codex}/skills/${skill_name}}"
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 2
fi

mkdir -p "$(dirname "${target}")"

if [[ -d "${target}/.git" ]]; then
  git -C "${target}" fetch --prune origin
  git -C "${target}" checkout main
  git -C "${target}" reset --hard origin/main
elif [[ -e "${target}" ]]; then
  echo "target exists but is not a git checkout: ${target}" >&2
  echo "move it aside or set --target / GO_CODE_STANDARDS_TARGET to another path" >&2
  exit 1
else
  git clone "${repo_url}" "${target}"
fi

if [[ "${lang}" == "zh" ]]; then
  cp "${target}/SKILL.zh.md" "${target}/SKILL.md"
  cp "${target}/references/go-style-rules.zh.md" "${target}/references/go-style-rules.md"
  if [[ -f "${target}/agents/openai.zh.yaml" ]]; then
    cp "${target}/agents/openai.zh.yaml" "${target}/agents/openai.yaml"
  fi
fi

echo "installed ${lang} skill at ${target}"
