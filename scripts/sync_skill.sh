#!/usr/bin/env bash
set -euo pipefail

repo_url="${GO_CODE_STANDARDS_REPO:-https://github.com/CCpro10/go-code-standards.git}"
skill_name="go-code-standards"
skills_root="${CODEX_HOME:-${HOME}/.codex}/skills"
target="${GO_CODE_STANDARDS_TARGET:-${skills_root}/${skill_name}}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 2
fi

mkdir -p "$(dirname "${target}")"

if [[ -d "${target}/.git" ]]; then
  git -C "${target}" fetch --prune origin
  git -C "${target}" checkout main
  git -C "${target}" pull --ff-only origin main
  echo "updated ${target}"
  exit 0
fi

if [[ -e "${target}" ]]; then
  echo "target exists but is not a git checkout: ${target}" >&2
  echo "move it aside or set GO_CODE_STANDARDS_TARGET to another path" >&2
  exit 1
fi

git clone "${repo_url}" "${target}"
echo "installed ${target}"
