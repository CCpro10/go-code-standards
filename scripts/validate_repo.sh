#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 scripts/validate_skill.py
python3 -m py_compile scripts/validate_skill.py
python3 -m py_compile skills/go-code-standards/scripts/enforce_go_style.py
python3 -m py_compile skills/go-code-standards-zh/scripts/enforce_go_style.py
bash -n scripts/sync_skill.sh scripts/validate_repo.sh
bash -n skills/svg-to-feishu-board/scripts/svg_to_board.sh
python3 -m unittest discover -s tests -p 'test_git_review_mode.py'
go run skills/go-code-standards/scripts/check_go_decl_order.go --repo .
go run skills/go-code-standards-zh/scripts/check_go_decl_order.go --repo .

echo "[ok] repository validation passed"
