---
name: git-review-mode
description: 在主仓库进入、切换、刷新或退出 GoLand Review 模式；功能开发保留在独立 worktree。fetch 最新基准，模拟合并检查冲突，把相对基准的功能变化展示为主仓库暂存区 diff。用于“回到 review 模式”“在 master 看这个分支的改动”“刷新/结束 Review”；保护手动修改和开发分支，不进行真正合并或发布。
---

# 主仓库 Review 模式

主仓库是固定审查目录，功能 worktree 是开发目录。主仓库使用 detached HEAD 指向基准快照，文件和暂存区呈现模拟合并结果。一次只审一个功能分支，审查内容在主动刷新前保持固定。

## 操作

使用本 Skill 的 `scripts/git_review.py`（Python 3.9+，macOS/Linux，Git 2.38+）。从任一 worktree 执行，脚本自动找到主工作区。命令行入口若已安装可使用 `greview`。

```bash
# --repo 必须放在子命令前；省略时使用当前目录所属仓库
python3 /path/to/git-review-mode/scripts/git_review.py --repo /path/to/feature-worktree status
python3 /path/to/git-review-mode/scripts/git_review.py --repo /path/to/feature-worktree review feature/song
python3 /path/to/git-review-mode/scripts/git_review.py --repo /path/to/feature-worktree refresh
python3 /path/to/git-review-mode/scripts/git_review.py --repo /path/to/feature-worktree refresh --latest
python3 /path/to/git-review-mode/scripts/git_review.py --repo /path/to/feature-worktree finish
```

- 先确认用户指定的仓库和功能分支，再用 `status` 查看快照。不要把创建 Skill 时所在仓库误当作目标仓库。
- `review <本地功能分支>`：fetch `origin/master`，用 `merge-tree --write-tree` 检查合并并计算结果，无冲突后在主工作区生成暂存区 diff。可用 `--base main --remote upstream` 指定其他基准。
- 默认包含本地分支已提交代码；功能 worktree 的未提交修改保持原样并明确提示不包含。主仓库原有的未提交修改或未跟踪文件会阻止进入 Review。
- `review <分支> --latest` 或 `refresh --latest`：fetch 功能分支的已配置 upstream，使用远端最新快照；本地未推送或分叉时停止，避免漏掉本地提交。开发分支、工作区和暂存区保持不变。
- `refresh` 保留当前分支和快照来源设置，更新基准与功能提交；`refresh --local` 改回本地已提交快照。`review <另一个分支>` 切换审查对象。
- `finish` 清除脚本生成的差异，保留当前基准 HEAD 的干净内容；主仓库保持 detached HEAD。本地 `master` 分支引用不被推进，实际基准始终以输出的远端提交为准。

## 执行边界

- 有冲突时报告文件和 Git 输出并停止，原 Review 内容保留。不要替用户解决冲突或使用 ours/theirs 绕过。
- 状态记录存放在 Git common dir 的 `greview/state.json`；暂存区树、HEAD 和工作区必须与记录一致。出现手动编辑、重新暂存、提交、切分支或未跟踪文件时停止，先让用户保留或处理修改，不能自动 stash、clean 或强制 reset。
- 支持未初始化的空 gitlink：子模块路径缺失或确实为空目录时可进入、刷新和结束 Review，即使缺少 `.gitmodules` 或本地没有子模块提交对象。保留 `160000` 引用，关闭子模块递归；缺失路径只建立空目录占位，不初始化或下载子模块。
- 子模块路径及其父路径含符号链接、子模块目录非空或已初始化时停止；包括只有忽略文件或 `.git` 的情况。进入、刷新、切换和结束前均检查 HEAD、索引和目标树涉及的路径，子模块与普通文件的类型转换暂不支持。
- 支持保留忽略的 IDE/构建文件，但若它们会被目标 tracked 文件覆盖则停止。sparse checkout 和隐藏索引标记暂不支持，按脚本错误说明处理。
- 若上次操作中断，先 `status` 查看状态；在没有手动修改时使用 `finish` 清理已记录的生成内容，再重新进入。不要删除状态文件强行绕过保护。
- 修复建议回到功能 worktree 修改、提交，再刷新 Review。用户只要求进入 Review 时，完成准备即可；实际代码审查或修复按用户后续要求执行。
- 本流程不创建合并提交，也不 push 目标业务仓库。GoLand 可直接打开主仓库，在 Commit/本地更改中查看 diff；启用 Git staging area 时看 Staged 区域。

## 输出

报告主仓库目录、功能分支和提交、基准远端及提交、快照来源、变更文件概览与下一步刷新/结束命令。实际验证时核对主仓库暂存区树等于模拟合并树、工作区无额外修改、开发 worktree 的分支/HEAD/暂存区/文件均保持原样。
