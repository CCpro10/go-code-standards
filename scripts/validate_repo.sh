#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 scripts/validate_skill.py
python3 -m py_compile scripts/enforce_go_style.py scripts/validate_skill.py
bash -n scripts/sync_skill.sh scripts/validate_repo.sh
go run scripts/check_go_decl_order.go --repo .

echo "[ok] repository validation passed"
