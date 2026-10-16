#!/usr/bin/env bash
# svg_to_board.sh — 把 SVG 投放到飞书画板（一键脚本）
#
# 用法：
#   svg_to_board.sh <svg_path> --board <whiteboard_token> [--overwrite]
#   svg_to_board.sh <svg_path> --new-doc <title>
#
# 依赖：lark-cli, python3；node>=18 + npx（仅本地渲染/静态检查用，可 --skip-check 跳过）
#
# 行为：
#   1) 可选：whiteboard-cli 本地渲染 PNG + 静态检查（text-overflow / node-overlap）
#   2) 投放：
#        --board   → whiteboard +update --input_format svg
#        --new-doc → docs +create 直接内联 <whiteboard type="svg">，一次调用建文档+画板+内容，
#                    并从返回的 new_blocks[].block_token 拿到画板 token
#   3) 云端回读校验：export --output-type raw，统计节点类型，检出被降级的大尺寸形状
#   4) 云端预览：优先 preview；失败则回退 svg 导出 + 本地渲染
#
# 鉴权：运行前需完成 lark-cli 用户身份授权。
# 文档链接：优先使用 CLI 返回的 URL；否则可设置 FEISHU_DOC_BASE_URL 为租户文档前缀。
#
# 已知问题：
#   1) --output-type preview 目前服务端可能返回 text/plain 而非图片
#      （报 "expected image/png ... got Content-Type: text/plain"）。脚本会自动回退到
#      svg 导出再本地渲染，产物内容一致。
#   2) 对同一画板短时间内反复 --overwrite 可能触发服务端 timeout
#      （"API call failed: server time out error"）。这不是脚本问题，稍等再试即可。
#   3) 刚写入后立刻回读可能为空，Step 3 已内置重试。

set -eo pipefail

err()  { printf '[svg_to_board] ERROR: %s\n' "$*" >&2; exit 1; }
info() { printf '[svg_to_board] %s\n' "$*" >&2; }
usage() {
  cat <<USAGE >&2
用法:
  $0 <svg_path> --board <whiteboard_token> [--overwrite]
  $0 <svg_path> --new-doc <title>

--board      投放到已有画板；加 --overwrite 会先清空画板全部内容再写入
--new-doc    新建文档 + 画板（一次 docs +create 完成，SVG 内容随创建落地）
--skip-check 跳过 whiteboard-cli 本地渲染与静态检查

注：新建的文档归当前 user 身份所有，可直接编辑，无需转移所有权。
    如需分享给他人，用 lark-cli drive 相关命令自行授权。
USAGE
  exit 2
}

[[ $# -ge 1 ]] || usage
SVG_PATH="$1"; shift
[[ -f "$SVG_PATH" ]] || err "SVG 文件不存在: $SVG_PATH"

MODE=""; BOARD_TOKEN=""; TITLE=""; OVERWRITE=0; SKIP_CHECK=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --board)
      [[ -n "${2:-}" ]] || err "--board 需要参数 <whiteboard_token>"
      MODE="board"; BOARD_TOKEN="$2"; shift 2 ;;
    --new-doc)
      [[ -n "${2:-}" ]] || err "--new-doc 需要参数 <title>"
      MODE="new-doc"; TITLE="$2"; shift 2 ;;
    --overwrite)  OVERWRITE=1;  shift ;;
    --skip-check) SKIP_CHECK=1; shift ;;
    -h|--help) usage ;;
    *) err "未知参数: $1" ;;
  esac
done

[[ -n "$MODE" ]] || usage
command -v lark-cli >/dev/null || err "未找到 lark-cli"
command -v python3  >/dev/null || err "未找到 python3"

export LARKSUITE_CLI_NO_UPDATE_NOTIFIER=1
export LARKSUITE_CLI_NO_SKILLS_NOTIFIER=1

WB_CLI="@larksuite/whiteboard-cli@latest"
LOCAL_PNG="${SVG_PATH%.svg}.local.png"

# lark-cli 的路径参数有白名单（仅 cwd / /tmp / ~/files）。
# 落在白名单外时，云端产物改写到 /tmp，避免投放成功却在最后一步失败。
SVG_DIR="$(cd "$(dirname "$SVG_PATH")" && pwd)"
CWD="$(pwd)"
BASE="$(basename "${SVG_PATH%.svg}")"
case "$SVG_DIR" in
  "$CWD"|"$CWD"/*|/tmp|/tmp/*|"$HOME"/files|"$HOME"/files/*)
    OUT_PREFIX="${SVG_PATH%.svg}" ;;
  *)
    OUT_PREFIX="/tmp/$BASE"
    info "NOTE: SVG 目录不在 lark-cli 输出白名单内，云端产物将保存到 /tmp/" ;;
esac
PREVIEW_PNG="${OUT_PREFIX}.preview.png"
CLOUD_SVG="${OUT_PREFIX}.cloud.svg"

# ---- Step 1: 本地渲染 + 静态检查 ----
if [[ "$SKIP_CHECK" -eq 0 ]] && command -v npx >/dev/null; then
  info "Step 1/4  本地渲染 -> $LOCAL_PNG"
  npx -y -p "$WB_CLI" whiteboard-cli -i "$SVG_PATH" -o "$LOCAL_PNG" -f svg >/dev/null 2>&1 \
    || info "WARN: 本地渲染失败（不阻塞投放）"
  info "Step 1/4  静态检查（text-overflow / node-overlap）"
  # --check 的报告写 stdout，这里只保留 issues 摘要，避免整份 JSON 污染脚本输出
  CHECK_OUT=$(npx -y -p "$WB_CLI" whiteboard-cli -i "$SVG_PATH" -f svg --check 2>/dev/null) || true
  if [[ -n "$CHECK_OUT" ]]; then
    printf '%s' "$CHECK_OUT" | python3 -c "
import sys, json, re
raw = sys.stdin.read(); i = raw.find('{')
if i < 0:
    sys.exit()
try:
    d = json.loads(raw[i:raw.rfind('}') + 1])
except Exception:
    sys.exit()
def walk(o):
    if isinstance(o, dict):
        if 'issues' in o and isinstance(o['issues'], list):
            return o['issues']
        for v in o.values():
            r = walk(v)
            if r is not None:
                return r
    return None
issues = walk(d)
if issues:
    print('  ⚠ 静态检查发现 %d 个问题:' % len(issues), file=sys.stderr)
    for it in issues[:5]:
        print('    - %s' % str(it)[:150], file=sys.stderr)
else:
    print('  ✓ 静态检查通过（无文字溢出 / 节点重叠）', file=sys.stderr)
" || true
  fi
else
  info "Step 1/4  跳过本地渲染与检查"
fi

# ---- Step 2: 投放 ----
DOC_URL=""
if [[ "$MODE" == "new-doc" ]]; then
  # docs +create 支持内联 <whiteboard type="svg">，一次调用完成
  # 建文档 + 建画板 + 写入 SVG，并在 new_blocks 里直接返回画板 token。
  # path="@file" 只接受 cwd 下相对路径，所以先 cd 到 SVG 所在目录。
  info "Step 2/4  新建文档 + 画板 (标题: $TITLE)"
  SVG_BASE="$(basename "$SVG_PATH")"
  CREATE_JSON=$(cd "$SVG_DIR" && lark-cli docs +create \
    --title "$TITLE" \
    --content "<whiteboard type=\"svg\" path=\"@${SVG_BASE}\"></whiteboard>" \
    --json) || err "新建文档失败"

  read -r DOC_TOKEN BOARD_TOKEN DOC_URL <<<"$(printf '%s' "$CREATE_JSON" | python3 -c "
import sys, json
raw = sys.stdin.read(); i = raw.find('{')
d = json.loads(raw[i:raw.rfind('}') + 1])
if not d.get('ok'):
    sys.exit('create 返回 ok=false: ' + json.dumps(d.get('error', {}), ensure_ascii=False)[:300])
doc = d.get('data', {}).get('document', {})
tok = doc.get('document_id') or ''
board = ''
for b in doc.get('new_blocks') or []:
    if b.get('block_type') == 'whiteboard' and b.get('block_token'):
        board = b['block_token']; break
if not tok or not board:
    sys.exit('未能解析 document_id / 画板 token: ' + json.dumps(doc, ensure_ascii=False)[:300])
url = doc.get('url') or doc.get('document_url') or '-'
print(tok, board, url)
")" || err "解析创建结果失败"

  if [[ "$DOC_URL" == "-" ]]; then
    DOC_URL=""
    if [[ -n "${FEISHU_DOC_BASE_URL:-}" ]]; then
      DOC_URL="${FEISHU_DOC_BASE_URL%/}/$DOC_TOKEN"
    fi
  fi
  info "        画板内容已随创建写入，跳过二次 update"
else
  info "Step 2/4  投放 SVG 到已有画板: $BOARD_TOKEN"
  # --source @file 同样受路径白名单限制，统一用 stdin + `--source -` 绕开。
  UPDATE_ARGS=(whiteboard +update
    --whiteboard-token "$BOARD_TOKEN"
    --input_format svg
    --source -
    --json)
  [[ "$OVERWRITE" -eq 1 ]] && {
    info "        --overwrite 已启用：将先清空画板原有内容"
    UPDATE_ARGS+=(--overwrite)
  }
  lark-cli "${UPDATE_ARGS[@]}" < "$SVG_PATH" >/dev/null || err "投放失败"
fi

# ---- Step 3: 云端回读校验 ----
# 本地 PNG 正常不代表云端正常：<polygon> 等元素会被降级为不可编辑图片。
# 判据：所有 image 节点尺寸都应 ≤40px（只该是箭头三角）。
# 注：刚写入后立刻回读可能拿不到内容（服务端有短暂延迟，--overwrite 后尤其明显），
#     这里做有上限的重试，避免把"写入成功但读得太早"误报成校验失败。
info "Step 3/4  云端回读校验（检出被降级的形状）"
RAW_JSON=""
for attempt in 1 2 3 4; do
  RAW_JSON=$(lark-cli whiteboard +export \
    --whiteboard-token "$BOARD_TOKEN" \
    --output-type raw --format json 2>/dev/null) || RAW_JSON=""
  [[ -n "$RAW_JSON" ]] && break
  [[ "$attempt" -lt 4 ]] && { info "        回读为空，${attempt}s 后重试 ($attempt/3)"; sleep "$attempt"; }
done
[[ -z "$RAW_JSON" ]] && info "WARN: 回读失败，跳过校验（投放本身已成功）"

NODE_SUMMARY="(回读失败)"
if [[ -n "$RAW_JSON" ]]; then
  NODE_SUMMARY=$(printf '%s' "$RAW_JSON" | python3 -c "
import sys, json
from collections import Counter
raw = sys.stdin.read(); i = raw.find('{')
try:
    d = json.loads(raw[i:raw.rfind('}') + 1])
    nodes = d.get('data', {}).get('nodes') or []
except Exception:
    print('(解析失败)'); sys.exit()
c = Counter(n.get('type') for n in nodes)
imgs = [n for n in nodes if n.get('type') == 'image']
big = [(round(n.get('width', 0)), round(n.get('height', 0)))
       for n in imgs if n.get('width', 0) > 40 or n.get('height', 0) > 40]
parts = ['%d nodes' % len(nodes)]
parts += ['%s=%d' % (k, v) for k, v in sorted(c.items())]
print(' | '.join(parts))
if big:
    print('  ⚠ 检出 %d 个大尺寸降级图片 %s' % (len(big), big[:5]), file=sys.stderr)
    print('    形状被降级为不可编辑图片。常见原因：用了 <polygon> 画大形状，', file=sys.stderr)
    print('    改用 <path d=\"M…Z\"> 重画。详见 references/flowchart-design.md', file=sys.stderr)
else:
    print('  ✓ 无大尺寸降级（image 节点仅为箭头三角）', file=sys.stderr)
")
fi

# ---- Step 4: 云端预览 ----
info "Step 4/4  拉取云端预览"
if lark-cli whiteboard +export \
     --whiteboard-token "$BOARD_TOKEN" \
     --output-type preview \
     --output "$PREVIEW_PNG" \
     --overwrite >/dev/null 2>&1; then
  VISUAL="$PREVIEW_PNG"
else
  info "        preview 导出失败（已知服务端问题），回退 svg 导出 + 本地渲染"
  VISUAL=""
  if lark-cli whiteboard +export \
       --whiteboard-token "$BOARD_TOKEN" \
       --output-type svg \
       --output "$CLOUD_SVG" \
       --overwrite >/dev/null 2>&1; then
    if command -v npx >/dev/null; then
      npx -y -p "$WB_CLI" whiteboard-cli -i "$CLOUD_SVG" -o "$PREVIEW_PNG" -f svg >/dev/null 2>&1 \
        && VISUAL="$PREVIEW_PNG (由云端 SVG 本地渲染)" \
        || VISUAL="$CLOUD_SVG (渲染失败，请直接看 SVG)"
    else
      VISUAL="$CLOUD_SVG (无 npx，未渲染)"
    fi
  else
    info "WARN: 云端产物均拉取失败（不影响投放结果）"
  fi
fi

# 注：统一用 printf 输出。另注意——变量后紧跟全角括号（如 "$VAR）"）会导致
# bash 把多字节字符当作变量名的一部分解析，输出乱码；涉及变量的括号一律用半角。
printf -- '---- DONE ----\n'
printf 'board_token : %s\n' "$BOARD_TOKEN"
printf 'cloud_check : %s\n' "$NODE_SUMMARY"
printf 'visual      : %s\n' "${VISUAL:-(未获取)}"
printf 'local_png   : %s\n' "$LOCAL_PNG"
printf 'src_svg     : %s\n' "$SVG_PATH"
[[ -n "$DOC_URL" ]] && printf 'doc_url     : %s\n' "$DOC_URL"
[[ -n "${DOC_TOKEN:-}" ]] && printf 'doc_token   : %s\n' "$DOC_TOKEN"
exit 0
