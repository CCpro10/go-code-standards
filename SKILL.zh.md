---
name: go-code-standards-zh
description: Go 代码规范与强制检查工作流，参考 Google Go Style 和 Uber Go Style Guide。用于 Codex 编写、审查、重构或门禁 Go 代码；用于仓库配置 Go 风格检查；用于约束 .go 文件中的格式化、导入、lint、测试、错误处理、命名、接口、并发、边界校验和 API 清晰度。
---

# Go 代码规范

## 语言源

中文版本是本 Skill 的规则基准。英文版本必须与中文版本保持同步；当规则发生冲突时，以中文版本为准。

## 工作流

在 Go 代码修改、Go 代码审查和仓库级 Go 质量门禁中使用本 Skill。

1. 先阅读本地仓库约定：已有 `Makefile`、CI、`.golangci.yml`、`go.mod`、包结构、生成代码策略和测试模式。
2. 编写或审查代码时，先应用 `references/project-rules.md` 中的最高优先级项目规则，再应用 `references/go-style-rules.md` 中的通用 Go 风格规则。
3. 结束前在目标仓库运行 `scripts/enforce_go_style.py`。
4. 说明所有被跳过的检查及原因。缺少必需工具或未运行测试时，不要声称约束已通过。

## 强制检查

在仓库根目录运行：

```bash
python3 /path/to/go-code-standards-zh/scripts/enforce_go_style.py --repo .
```

自动修复格式和导入：

```bash
python3 /path/to/go-code-standards-zh/scripts/enforce_go_style.py --repo . --fix
```

严格 CI 门禁，要求推荐外部工具存在：

```bash
python3 /path/to/go-code-standards-zh/scripts/enforce_go_style.py --repo . --strict
```

生成初始 `golangci-lint` 配置：

```bash
python3 /path/to/go-code-standards-zh/scripts/enforce_go_style.py --repo . --write-golangci-config
```

## 安装或更新

默认安装英文版本：

```bash
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash
```

安装或更新中文版本：

```bash
curl -fsSL https://raw.githubusercontent.com/CCpro10/go-code-standards/main/scripts/sync_skill.sh | bash -s -- --lang zh
```

中文版本默认同步到 `${CODEX_HOME:-$HOME/.codex}/skills/go-code-standards-zh`。重复运行同一命令即可更新。

## 必跑检查

当仓库中存在 Go 文件时，始终运行：

- 格式化：`gofmt`；如果仓库采用或要求 `gofumpt`，优先使用 `gofumpt`。
- 导入：可用或 strict 模式下使用 `goimports`。
- 模块：存在 `go.mod` 时验证 `go mod tidy`。
- 包级声明顺序：每个 package 中，最重要的可导出 package-level 函数和方法必须位于最前面，其他可导出函数随后，不可导出函数和方法在最后；private section 后禁止出现大写开头的函数或方法。
- 局部清晰度：如果变量可能因为后续失败路径而没有机会使用，应延后声明；大业务结构体优先使用 keyed composite literal 一次性构造，不要先声明空值再逐字段赋值。
- 注释和结构体：函数代码必须包含有信息量的注释；复杂函数必须有详细注释。结构体必须必要且清晰，禁止大量无必要中间结构体。
- 边界清晰度：不要用含糊的 normalization 名称隐藏输入清洗、过滤、去重和默认值补齐；业务输入应在边界校验，非法时清晰失败。
- 静态检查：`go vet ./...`。
- 测试：`go test ./...`，除非用户明确要求跳过。
- Lint：存在配置或 strict 模式下运行 `golangci-lint run ./...`。

## 审查优先级

按以下顺序优先处理问题：

1. 正确性、数据竞争、goroutine 泄漏、取消传播、超时传播和资源清理。
2. 公共 API 清晰度：命名、导出符号注释、小接口和稳定错误行为。
3. 可维护性：简单控制流、小而内聚的 package、显式依赖和表驱动测试。
4. 风格一致性：格式、导入分组、receiver 命名、initialism、错误包装和日志。

先使用 `references/project-rules.md` 查看最高优先级项目规则，再使用 `references/go-style-rules.md` 查看通用 Go 风格规则和来源链接。
