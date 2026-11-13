---
name: go-code-standards-zh
description: Go 局部表达与代码规范 Review：命名、注释、导出范围、声明顺序、排版、变量声明与结构体构造。默认只审查；数据模型、行为抽象、主流程、契约和故障交给其他专项。
---

# Go 表达规范 Review

读取 references/project-rules.md 的最高优先级规则，再读取 references/go-style-rules.md。中文规则为准。

按用户指定范围审查，必要时追踪调用点确认命名和导出语义。输出位置、违反的规则、具体影响和改进建议；没有问题直接说明。默认只 Review，明确要求修复后才改代码。

机械检查可运行下列命令。默认检查不运行 go vet/test；--fix 会修改文件，仅在用户要求修复时使用。脚本只能验证格式或部分声明形状，不能证明业务语义正确。

```bash
python3 /path/to/go-code-standards-zh/scripts/enforce_go_style.py --repo .
```

不将函数类型、单实现接口、薄包装归为局部风格问题：这些由 abstraction-review 负责。ID​​L/DB 和状态生命周期归 data-model-review；整体流程归 main-flow-review；校验/默认值归 contract-boundary-review；具体故障归 code-risk-review。
