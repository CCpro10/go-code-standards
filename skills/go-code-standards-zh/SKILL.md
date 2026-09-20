---
name: go-code-standards-zh
description: Go 设计、风格、可读性和可维护性审查 Skill。用于检查 IDL、DB schema、核心结构体字段设计，目录与 package 职责，函数和方法形状、注释命名及局部代码是否长期易维护。默认代码逻辑正确；不用于发现并发问题、可疑 bug、性能问题或业务逻辑错误。
---

# Go 风格规范

本 Skill 处理数据结构设计、风格、可读性和长期可维护性问题。它假设代码逻辑是正确的，重点判断 IDL、DB schema、核心结构体及其上的实现是否清晰、稳定且符合 Go 和当前业务的最佳实践。

风险审查请使用 `code-risk-review`。

## 工作流

1. 先读业务不变量、数据访问方式和本地约定：IDL、DB schema、核心结构体、目录结构、package 组织、已有函数拆分方式、注释风格和格式化工具。
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

- 数据结构是否先于实现被正确设计；先审 IDL、DB schema 和核心结构体字段，再判断函数实现是否被迫承担数据模型缺陷。
- IDL 是否准确表达接口契约、字段语义、必填性、单位、枚举和兼容演进；DB 是否清晰表达主键、约束、空值、索引、生命周期和访问方式。
- 核心结构体是否表达稳定领域概念和不变量，字段是否有唯一事实来源、明确所有权与生命周期，是否能长期维护并符合当前场景的最佳实践。
- 目录层级和 package 职责是否清晰；只提出拆文件/迁移目录建议，不主动执行这类重操作。
- 结构体是否必要、清晰，是否存在大量中间结构；可导出结构体及其字段是否有清晰注释。
- 函数和方法拆分是否合理，异常路径是否先快速返回，正常逻辑是否保持顺序清晰；是否过度抽小函数或传递函数制造抽象，是否存在必须内联的无意义纯转发函数、`var` 函数别名或常量别名。
- package 内最重要的可导出函数是否在前，不可导出函数是否在后。
- 函数注释是否说明实际执行顺序、选择条件和未命中后的下一步，函数名是否清晰且与实际完成的全部功能准确对应；集合是否按具体元素复数命名，map 是否使用 `<key>2<value>` 命名。
- 是否存在隐藏默认值、内部工程参数兜底、深层 `normalizeXxx` 掩盖非法状态。
- 局部变量声明、结构体构造、空行和换行是否让主流程更易读。

先读 `references/project-rules.md`，再读 `references/go-style-rules.md`。
