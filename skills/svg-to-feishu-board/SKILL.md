---
name: svg-to-feishu-board
description: 把 SVG 图表、流程图、架构图、UI mockup、海报、平面图、地铁图和插画投放为飞书画板可编辑节点，可嵌入云文档。用于 SVG 转画板、在飞书自由作画，以及需要精细控制布局、分流、循环、边标签与注记的复杂图。简单自动布局图优先使用 Mermaid/DSL。
allowed-tools: Bash, Read, Write
---

# SVG → 飞书画板（可编辑节点）

把 SVG 当作 AI 的**通用矢量画布**，让 Agent 自由表达视觉，再通过 `lark-cli` 投放到飞书画板上，
所有节点（rect / circle / path / text / polygon …）都成为可编辑、可二次创作的真实元素。

## Use When

- 用户希望在飞书里得到**有视觉表现力**的画面：插画、海报、UI mockup、平面图、地铁图、信息图、复杂图表。
- 普通 Mermaid/PlantUML 表现力不足；手写飞书 OpenAPI JSON 又太啰嗦、坐标算到崩溃。
- 用户已经有现成 SVG（设计稿、d3 导出、手画），想直接搬到飞书画板继续编辑。
- 需要**信息密度极高**（如周期表 500+ 节点）或**艺术氛围**（赛博朋克、插画、海报）。
- **需要精细控制布局的流程图**：多道判断分流、失败出口甩到边缘、循环回路、图外注记——
  Mermaid 的自动布局做不出这种"主干竖直 + 分支自由甩出"的效果。见
  [references/flowchart-design.md](references/flowchart-design.md)。

不要用于：

- **结构简单、节点少的**流程图 / 思维导图 / 时序图——直接用 `lark-whiteboard` 的 Mermaid / DSL 路径更省事。
  判据：能被 Mermaid 的自动布局排好、且不需要边标签与注记时，就不必手写 SVG。
- 只是要一张静态 PNG 贴到文档——直接 SVG 转 PNG 即可，无需画板。

## 前置依赖

- `lark-cli`：需自行安装并按所用版本的文档完成用户身份授权，确保具有目标文档和画板的访问权限。不要假设其他环境已经登录。
  - 运行 `lark-cli --version` 确认可用；授权失败时检查 `lark-cli auth --help`，不要读取或输出凭据。
  - 用到的命令：`docs +create` / `whiteboard +update` / `whiteboard +export` / `drive +member-add` /
    `drive permission.members transfer_owner`。
- `@larksuite/whiteboard-cli`（Node ≥ 18）：**仅用于本地渲染预览和静态检查**，投放不再需要它做格式转换。
  本 skill 默认通过 `npx` 使用，无需全局安装。
- `python3`、网络可达 npm（首次拉包）。
- 新建文档的链接优先使用 CLI 返回的 URL；若返回值不含 URL，可配置 `FEISHU_DOC_BASE_URL` 为自己租户的文档前缀（例如 `https://your-tenant.feishu.cn/docx`）。未配置时仍输出文档 token，不猜测租户域名。

> [!IMPORTANT]
> **lark-cli 的文件路径白名单**：`--source @file` 和 `--output` 只接受
> **当前工作目录 / `/tmp` / `~/files`** 下的路径，skill 目录等位置会被拒绝。
> - 读 SVG：用 stdin，即 `--source -` 配合 `< file.svg`，任意路径都可用；
> - 写预览：把 `--output` 指到 `/tmp` 或 cwd 下。
> `scripts/svg_to_board.sh` 已内置这两处处理。

> **关于所有权**：lark-cli 以 `identity: user` 调用，新建文档默认就归**当前用户**所有，
> 可直接编辑，无需转移。需要交付给他人时用 `lark-cli drive` 自行授权——注意
> `permission.members transfer_owner` 是 **high-risk-write**，必须先与用户确认再带 `--yes`，
> 不要在脚本里静默调用。

## 核心工作流（4 步）

```
Step 1  设计：让 AI 自由写 SVG（参考 references/svg-design.md；
        画流程图另读 references/flowchart-design.md）
Step 2  审查：whiteboard-cli 本地渲染 PNG + --check 静态检查
Step 3  投放：lark-cli whiteboard +update --input_format svg  直接把 SVG 投到画板
Step 4  验证：lark-cli whiteboard +export --output-type preview  截图回看，必要时迭代
```

> [!NOTE]
> lark-cli 原生支持 `--input_format svg`，**不需要**先把 SVG 转成 OpenAPI JSON。
> 旧版本里的「转 JSON + 手工修文字宽度」两步已废弃：文字重排由画板服务端处理，
> 本地只需用 `--check` 提前发现 `text-overflow` / `node-overlap`。

### Step 1：写 SVG

- **配色先看 [`references/svg-design.md`](references/svg-design.md) 的"色彩原则 + 按性格分组的色板"段**——里面给了 OKLCH 亮度对齐过的 6 套色板（pale / muted / vivid / deep / dark / editorial）和 APCA 验证过的文字配对，直接抄不会失衡。
- 给定 viewBox（推荐 `0 0 1600 1000` 或按主题决定的大画布）。
- 优先使用 `<rect>/<circle>/<ellipse>/<line>/<path>/<polygon>/<polyline>/<text>` 这些原子，**少用 `<g transform>`**——画板解析会展开变换，但层级越深越容易丢样式。
- 颜色直接写 `fill="#xxxxxx"` 或 `fill="rgb(…)"`；避免 CSS class、`<style>` 块、`mask`、`filter`、外链字体——这些在画板里通常不可控。
- 文字用独立 `<text>`，写明 `font-size`、`fill`，不要依赖样式表继承。
- 写到本地文件，例如 `/tmp/board.svg`（放 `/tmp` 或 cwd 下可省去路径白名单的麻烦）。

### Step 2：本地渲染 + 静态检查

```bash
WB="@larksuite/whiteboard-cli@^0.2.13"

# 渲染本地预览
npx -y "$WB" -i /tmp/board.svg -o /tmp/board.local.png -f svg

# 静态检查：text-overflow / node-overlap
npx -y "$WB" -i /tmp/board.svg -f svg --check
```

看 `--check` 报告 + 打开 `/tmp/board.local.png` 目测，有问题**改 SVG**（SVG 是单一真源）。

### Step 3：投放到飞书画板

```bash
# A. 已有画板：直接投放
#    注意用 stdin（--source -），可绕开 lark-cli 的 --source 路径白名单
lark-cli whiteboard +update \
  --whiteboard-token "$BOARD_TOKEN" \
  --input_format svg \
  --source - --json < /tmp/board.svg

# B. 新建文档 + 画板
DOC_TOKEN=$(lark-cli docs +create --title "AI 视觉作品" --content '<board/>' --json \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('document_id') or d.get('data',{}).get('document',{}).get('document_id',''))")
# 再从文档正文解析出画板块的 whiteboard token：
lark-cli docs +script --command parse --doc "$DOC_TOKEN" --json
```

> 替换已有画板全部内容时加 `--overwrite`（会**先删除画板现有全部内容**再写入）。
> 对非空画板使用前请先与用户确认。

### Step 4：验证

```bash
lark-cli whiteboard +export \
  --whiteboard-token "$BOARD_TOKEN" \
  --output-type preview \
  --output /tmp/board.preview.png --overwrite
```

打开 `/tmp/board.preview.png` 检查：

- 视觉是否与本地 PNG 一致；
- 是否有节点被裁剪、文字溢出、颜色失真；
- 信息密度是否过高（>500 节点会显著拖慢画板编辑器）。

有问题时改 SVG 重跑 Step 2-4，**SVG 是单一真源**。

## Helper 脚本

`scripts/svg_to_board.sh` 把 Step 2-4 串起来（内部全部走 lark-cli）：

```bash
# A. 投放到已有画板
scripts/svg_to_board.sh /tmp/board.svg --board <WHITEBOARD_TOKEN>

# A2. 覆盖已有画板全部内容（先清空再写入，请先与用户确认）
scripts/svg_to_board.sh /tmp/board.svg --board <WHITEBOARD_TOKEN> --overwrite

# B. 自动新建文档 + 画板（一次 docs +create 完成，SVG 内容随创建落地）
scripts/svg_to_board.sh /tmp/board.svg --new-doc "AI 视觉作品"

# C. 跳过本地渲染与静态检查（赶时间时用，不推荐）
scripts/svg_to_board.sh /tmp/board.svg --board <WHITEBOARD_TOKEN> --skip-check
```

脚本会在投放后做一次**云端回读校验**，统计节点类型并检出被降级为不可编辑图片的大尺寸形状
（最常见原因是用 `<polygon>` 画了菱形等大形状）。输出里的 `cloud_check` 就是这份摘要。

新建的文档归当前 user 身份所有，可直接编辑，**无需转移所有权**；需要分享给他人时用
`lark-cli drive` 相关命令自行授权（`transfer_owner` 属高风险写操作，必须先与用户确认再带 `--yes`）。

执行结束会打印 `board_token / cloud_check / visual / local_png / src_svg / doc_url` 块，方便直接回传给用户。

## 关键约束 / 易踩坑

1. **lark-cli 路径白名单**：`--source @file` 与 `--output` 仅接受 cwd / `/tmp` / `~/files`。读文件用 `--source -` 走 stdin；写文件把 `--output` 指到 `/tmp`。这是最容易踩的一条。
2. **画板不支持的装饰特性**：`<pattern>` / `<clipPath>` / `<mask>` / 非阴影用途的 `<filter>` 会导致渲染问题；`<style>` 块、CSS class 会被丢弃。颜色直接写到元素属性上。阴影只支持 `<feDropShadow>` 或标准 drop/inner primitive 链（drop 至多 1 个、inner 至多 1 个）。
3. **文字用独立 `<text>` 节点**，不要嵌在 `<g>` 内并依赖父级 transform 旋转，画板侧的文字旋转支持有限。画板硬编码 Noto Sans SC，按 CJK ≈ 1em / Latin ≈ 0.6em 预留容器宽度。
4. **节点上限**：经验值单板控制在 **≤ 500 个节点**。更复杂作品拆成多个画板。
5. **viewBox = 画板坐标**：过小会糊，过大会卡。推荐 `1200×800` 起步，或 `0 0 1600 1000`。
6. **变换**：`translate` / `rotate` / `scale` 正常；`skewX` / `skewY` / `matrix(...)` 会降级为不可编辑图片。
7. **渐变边界**：`gradientUnits` 用默认 `objectBoundingBox`，至少 2 个 `<stop>`；`userSpaceOnUse` / `spreadMethod=reflect|repeat` 会变成不可编辑图片。
8. **避免外链资源**：`<image href="https://…">`、外链字体在画板侧通常加载不到，用纯几何 + 系统字体表达。
9. **失败排查**：先跑 `npx -y @larksuite/whiteboard-cli@^0.2.13 -i x.svg -f svg --check`，常见原因是自闭合标签遗漏、`d=""` 路径语法不合法。
10. **文字堆叠**：云端出现本地没有的文字重叠时，改 SVG 放宽 `<text>` 容器宽度并重投，**不要**去手改中间 JSON。
11. **`--overwrite` 会清空画板**：对非空画板使用前必须与用户确认。
12. **可二次编辑**：投放后用户在飞书画板里可以选中、拖动、改色每个元素——这是相比直接贴 PNG 的最大价值。

## Output Shape

完成一次任务时回报：

- SVG 源文件路径（用户可继续迭代）
- 目标画板 whiteboard token + 飞书文档 URL
- 云端预览 PNG 路径（验证用）+ 本地渲染 PNG 路径（对照用）
- 节点规模（提示是否接近 500 上限）

## 参考

- `references/svg-design.md`：SVG 自由设计的几何/配色/排版要点，覆盖 14 类视觉作品的关键技巧。
- `references/flowchart-design.md`：**画流程图必读**。节点形状语义、菱形判断分流、正交连线与边标签、
  「卡片墙」反模式、以及菱形必须用 `<path…Z>` 而非 `<polygon>` 的硬约束。
- `references/sample.svg`：一个最小可工作的 SVG，方便 smoke test。
- `lark-whiteboard` skill（可选）：若已安装，可参考其 SVG 路径与配色文档；未安装时使用 `lark-cli whiteboard --help` 查看当前版本支持的命令。
