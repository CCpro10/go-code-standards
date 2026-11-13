---
name: code-review
description: 多专项代码 Review 的兼容入口。转到 review-coordinator，先确认范围、专项、子 Agent 模型与思考等级，再分别审查并汇总。
---

# 兼容入口

读取同级 `../review-coordinator/SKILL.md` 并执行其流程。此入口没有独立审查规则，不再使用旧的自动重构 smell baseline。

若未安装 review-coordinator，先说明缺少该 Skill，使用仓库安装脚本安装后继续。用户已给出的范围与模型直接沿用；其余选项先询问。默认只 Review。
