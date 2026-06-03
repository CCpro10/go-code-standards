---
name: go-code-standards-zh
description: Go 风格、可读性和可维护性审查 Skill。用于检查目录层级、package 职责、结构体定义是否必要清晰、函数和方法拆分是否合理、注释命名和局部代码是否易读。默认代码逻辑正确；不用于发现并发问题、可疑 bug、性能问题或业务逻辑错误。
---

# Go 风格规范

本 Skill 只处理风格、可读性和可维护性问题。它假设代码逻辑是正确的，重点判断“这个实现是否写得挫、是否难读、是否难维护”。

风险审查请使用 `code-risk-review`。

## 工作流

1. 先读本地约定：目录结构、package 组织、已有结构体/函数拆分方式、注释风格和格式化工具。
2. 先应用 `references/project-rules.md` 的最高优先级风格规则，再应用 `references/go-style-rules.md` 的通用 Go 风格规则。
3. 如需机械约束，运行 `scripts/enforce_go_style.py`。默认只做风格检查，不跑 `go vet` 和 `go test`。
4. 输出只聚焦风格、可读性和可维护性；不要报告并发、性能、逻辑 bug，除非它直接体现为结构/命名/可维护性问题。

## 机械检查

```bash
python3 /path/to/go-code-standards-zh/scripts/enforce_go_style.py --repo .
```

自动修复格式和导入：

```bash
python3 /path/to/go-code-standards-zh/scripts/enforce_go_style.py --repo . --fix
```

## 审查范围

- 目录层级和 package 职责是否清晰。
- 结构体是否必要、清晰，是否存在大量中间结构。
- 函数和方法拆分是否合理，是否过度抽小函数。
- package 内最重要的可导出函数是否在前，不可导出函数是否在后。
- 注释是否有信息量，命名是否表达真实行为。
- 局部变量声明、结构体构造、空行和换行是否让主流程更易读。

先读 `references/project-rules.md`，再读 `references/go-style-rules.md`。
