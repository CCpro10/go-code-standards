#!/usr/bin/env bash
set -euo pipefail

repo_url="${GO_CODE_STANDARDS_REPO:-https://github.com/CCpro10/go-code-standards.git}"
skill="${GO_CODE_STANDARDS_SKILL:-go-code-standards}"
target="${GO_CODE_STANDARDS_TARGET:-}"
target_root="${GO_CODE_STANDARDS_TARGET_ROOT:-}"
agent="${GO_CODE_STANDARDS_AGENT:-codex}"
install_all="false"
skill_set="false"
lang_set="false"

usage() {
  cat <<'USAGE'
Usage: sync_skill.sh [--skill NAME | --all] [--agent codex|codex-standard|claude-code|all] [--target /path/to/skill] [--target-root /path/to/skills] [--lang en|zh]

Installs or updates skills from this repository into a local agent skills directory.
Default skill is go-code-standards.

Agents:
  codex           Install to ${CODEX_HOME:-$HOME/.codex}/skills (legacy/current Codex app path)
  codex-standard  Install to ${AGENTS_HOME:-$HOME/.agents}/skills (OpenAI Agent Skills standard path)
  claude-code     Install to ${CLAUDE_HOME:-$HOME/.claude}/skills
  all             Install to codex, codex-standard, and claude-code

Skills:
  go-code-standards      English Go code standards skill
  go-code-standards-zh   Chinese Go code standards skill
  normal-feature-development
                         Normal small feature development workflow skill
  spark-feature-development
                         Spark-assisted feature development workflow skill
  code-risk-review       Code risk review workflow for changed files

Examples:
  sync_skill.sh
  sync_skill.sh --agent claude-code
  sync_skill.sh --agent codex-standard --all
  sync_skill.sh --skill normal-feature-development
  sync_skill.sh --skill spark-feature-development
  sync_skill.sh --skill go-code-standards-zh
  sync_skill.sh --skill code-risk-review --agent claude-code
  sync_skill.sh --skill go-code-standards --target-root "$PWD/.agents/skills"
  sync_skill.sh --lang zh              # backwards-compatible alias for go-code-standards-zh
  sync_skill.sh --all

Environment:
  GO_CODE_STANDARDS_REPO    Git repository URL. Defaults to the public GitHub repo.
  GO_CODE_STANDARDS_SKILL   Skill name to install.
  GO_CODE_STANDARDS_AGENT   Agent target: codex, codex-standard, claude-code, or all.
  GO_CODE_STANDARDS_TARGET  Install target for a single skill.
  GO_CODE_STANDARDS_TARGET_ROOT
                            Install root containing skill directories.
  CODEX_HOME                Codex home. Defaults to "$HOME/.codex".
  AGENTS_HOME               Agent Skills standard home. Defaults to "$HOME/.agents".
  CLAUDE_HOME               Claude Code home. Defaults to "$HOME/.claude".
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
    --target-root)
      target_root="${2:-}"
      shift 2
      ;;
    --agent)
      agent="${2:-}"
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

case "${agent}" in
  codex|codex-standard|claude-code|all) ;;
  *) echo "--agent must be codex, codex-standard, claude-code, or all" >&2; exit 2 ;;
esac

if [[ "${agent}" == "all" && -n "${target}" ]]; then
  echo "--target cannot be used with --agent all" >&2
  exit 2
fi

if [[ "${agent}" == "all" && -n "${target_root}" ]]; then
  echo "--target-root cannot be used with --agent all" >&2
  exit 2
fi

if [[ -n "${target}" && -n "${target_root}" ]]; then
  echo "--target cannot be combined with --target-root" >&2
  exit 2
fi

if [[ "${install_all}" == "true" && -n "${target}" ]]; then
  echo "--target cannot be used with --all" >&2
  exit 2
fi

if [[ "${skill}" == "codex-development" ]]; then
  skill="normal-feature-development"
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 2
fi

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

skill_root_for_agent() {
  case "$1" in
    codex) echo "${CODEX_HOME:-${HOME}/.codex}/skills" ;;
    codex-standard) echo "${AGENTS_HOME:-${HOME}/.agents}/skills" ;;
    claude-code) echo "${CLAUDE_HOME:-${HOME}/.claude}/skills" ;;
    *) echo "unknown agent: $1" >&2; exit 2 ;;
  esac
}

agent_list() {
  if [[ "${agent}" == "all" ]]; then
    printf '%s\n' codex codex-standard claude-code
  else
    printf '%s\n' "${agent}"
  fi
}

install_skill() {
  local name="$1"
  local root="$2"
  local dest="${3:-${root}/${name}}"
  local source="${tmp}/repo/skills/${name}"

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

while IFS= read -r selected_agent; do
  skills_root="${target_root:-$(skill_root_for_agent "${selected_agent}")}"
  if [[ "${install_all}" == "true" ]]; then
    while IFS=$'\t' read -r skill_name _; do
      [[ -z "${skill_name}" ]] && continue
      install_skill "${skill_name}" "${skills_root}"
    done < "${manifest}"
    continue
  fi

  if [[ -z "${skill}" ]]; then
    echo "--skill requires a value" >&2
    exit 2
  fi
  install_skill "${skill}" "${skills_root}" "${target:-}"
done < <(agent_list)
