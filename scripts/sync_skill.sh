#!/usr/bin/env bash
set -euo pipefail

repo_url="${GO_CODE_STANDARDS_REPO:-https://github.com/CCpro10/go-code-standards.git}"
skill="${GO_CODE_STANDARDS_SKILL:-go-code-standards}"
target=""
install_all="false"
skill_set="false"
lang_set="false"

usage() {
  cat <<'USAGE'
Usage: sync_skill.sh [--skill NAME | --all] [--target /path/to/skill] [--lang en|zh]

Installs or updates skills from this repository into the local Codex skills directory.
Default skill is go-code-standards.

Skills:
  go-code-standards      English Go code standards skill
  go-code-standards-zh   Chinese Go code standards skill
  codex-development      Codex design/review/implementation workflow skill

Examples:
  sync_skill.sh
  sync_skill.sh --skill codex-development
  sync_skill.sh --skill go-code-standards-zh
  sync_skill.sh --lang zh              # backwards-compatible alias for go-code-standards-zh
  sync_skill.sh --all

Environment:
  GO_CODE_STANDARDS_REPO    Git repository URL. Defaults to the public GitHub repo.
  GO_CODE_STANDARDS_SKILL   Skill name to install.
  GO_CODE_STANDARDS_TARGET  Install target for a single skill.
  CODEX_HOME                Codex home. Defaults to "$HOME/.codex".
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)
      skill="${2:-}"
      skill_set="true"
      shift 2
      ;;
    --all)
      install_all="true"
      shift
      ;;
    --target)
      target="${2:-}"
      shift 2
      ;;
    --lang)
      lang_set="true"
      case "${2:-}" in
        en) skill="go-code-standards" ;;
        zh) skill="go-code-standards-zh" ;;
        *) echo "--lang must be en or zh" >&2; exit 2 ;;
      esac
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

if [[ "${install_all}" == "true" && "${skill_set}" == "true" ]]; then
  echo "--all cannot be combined with --skill" >&2
  exit 2
fi

if [[ "${install_all}" == "true" && "${lang_set}" == "true" ]]; then
  echo "--all cannot be combined with --lang" >&2
  exit 2
fi

if [[ "${skill_set}" == "true" && "${lang_set}" == "true" ]]; then
  echo "--lang is a legacy alias for go-code-standards only and cannot be combined with --skill" >&2
  exit 2
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 2
fi

skills_root="${CODEX_HOME:-${HOME}/.codex}/skills"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT

git clone --depth 1 "${repo_url}" "${tmp}/repo" >/dev/null

manifest="${tmp}/repo/skills/manifest.tsv"
if [[ ! -f "${manifest}" ]]; then
  echo "missing skills/manifest.tsv" >&2
  exit 2
fi

skill_exists() {
  local name="$1"
  awk -F '\t' -v name="${name}" '$1 == name { found = 1 } END { exit(found ? 0 : 1) }' "${manifest}"
}

list_skills() {
  cut -f 1 "${manifest}" | sort
}

install_skill() {
  local name="$1"
  local source="${tmp}/repo/skills/${name}"
  local dest="${2:-${skills_root}/${name}}"

  if ! skill_exists "${name}" || [[ ! -f "${source}/SKILL.md" ]]; then
    echo "unknown skill: ${name}" >&2
    echo "available skills:" >&2
    list_skills >&2
    exit 2
  fi

  mkdir -p "$(dirname "${dest}")"
  rm -rf "${dest}.tmp"
  mkdir -p "${dest}.tmp"
  cp -R "${source}/." "${dest}.tmp/"
  rm -rf "${dest}"
  mv "${dest}.tmp" "${dest}"
  echo "installed ${name} at ${dest}"
}

if [[ "${install_all}" == "true" ]]; then
  if [[ -n "${target}" ]]; then
    echo "--target cannot be used with --all" >&2
    exit 2
  fi
  while IFS=$'\t' read -r skill_name _; do
    [[ -z "${skill_name}" ]] && continue
    install_skill "${skill_name}"
  done < "${manifest}"
else
  if [[ -z "${skill}" ]]; then
    echo "--skill requires a value" >&2
    exit 2
  fi
  install_skill "${skill}" "${target:-${skills_root}/${skill}}"
fi
