#!/usr/bin/env python3
"""Prepare staged review diffs in the main checkout without moving feature branches."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys


class ReviewError(Exception):
    pass


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-c", "submodule.recurse=false", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="surrogateescape",
    )
    if check and result.returncode:
        raise ReviewError(result.stderr.strip() or result.stdout.strip() or f"git {args[0]} failed")
    return result


def resolve(repo: Path, ref: str) -> str:
    return git(repo, "rev-parse", "--verify", ref).stdout.strip()


def main_checkout(repo: Path) -> tuple[Path, Path]:
    if git(repo, "rev-parse", "--is-bare-repository").stdout.strip() == "true":
        raise ReviewError("需要普通仓库及其主工作区，不支持 bare 仓库。")
    fields = git(repo, "worktree", "list", "--porcelain", "-z").stdout.split("\0")
    if not fields[0].startswith("worktree "):
        raise ReviewError("无法确定主仓库工作目录。")
    main = Path(fields[0][len("worktree "):]).resolve()
    common = Path(git(main, "rev-parse", "--git-common-dir").stdout.strip())
    if not common.is_absolute():
        common = main / common
    return main, common.resolve()


def save_state(path: Path, state: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_state(path: Path, main: Path) -> dict | None:
    if not path.exists():
        return None
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("version") != 1 or state.get("main") != str(main):
        raise ReviewError("Review 状态版本或工作目录不匹配，请检查状态文件。")
    return state


def ensure_supported(main: Path) -> None:
    git_dir = Path(git(main, "rev-parse", "--absolute-git-dir").stdout.strip())
    for marker in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply", "sequencer", "BISECT_START"):
        if (git_dir / marker).exists():
            raise ReviewError(f"主仓库正在执行 Git 操作（{marker}），请先完成或中止。")
    sparse = git(main, "config", "--bool", "core.sparseCheckout", check=False)
    if sparse.returncode not in (0, 1):
        raise ReviewError(sparse.stderr.strip())
    if sparse.stdout.strip() == "true":
        raise ReviewError("主仓库使用 sparse checkout，暂不支持 Review 模式。")
    for entry in git(main, "ls-files", "-v", "-z").stdout.split("\0"):
        if entry and (entry[0].islower() or entry[0] == "S"):
            raise ReviewError("主仓库存在 assume-unchanged/skip-worktree 标记，请先清除再使用。")


def ensure_unedited(main: Path, state: dict | None) -> None:
    ensure_supported(main)
    tree = git(main, "write-tree").stdout.strip()
    ensure_tree_supported(main, "HEAD", tree)
    if state is None:
        if (tree != resolve(main, "HEAD^{tree}")
                or git(main, "status", "--porcelain", "--untracked-files=all", "--ignore-submodules=all").stdout):
            raise ReviewError("主仓库有已有修改或未跟踪文件，请先保存；脚本不会 stash 或覆盖。")
        return

    head = resolve(main, "HEAD")
    allowed_heads = state.get("allowed_heads", [state["base_sha"]])
    allowed_trees = state.get("allowed_trees", [state["tree"]])
    if head not in allowed_heads or tree not in allowed_trees:
        raise ReviewError("HEAD 或暂存区已被手动修改，拒绝覆盖。请先保存修改。")
    branch = git(main, "symbolic-ref", "-q", "HEAD", check=False)
    if branch.returncode not in (0, 1):
        raise ReviewError(branch.stderr.strip())
    if state["phase"] == "ready" and branch.returncode == 0:
        raise ReviewError("主仓库已切换到分支，拒绝覆盖当前状态。")
    diff = git(main, "diff", "--quiet", "--ignore-submodules=all", "--", check=False)
    if diff.returncode:
        raise ReviewError("Review 目录有未暂存修改，拒绝覆盖。请先保存修改。")
    if git(main, "ls-files", "--others", "--exclude-standard", "-z").stdout:
        raise ReviewError("Review 目录有未跟踪文件，拒绝覆盖。请先保存这些文件。")


def ensure_tree_supported(main: Path, tree: str, *other_trees: str) -> None:
    targets = set()
    gitlinks = set()
    regular_paths = set()
    for ref in (tree, *other_trees):
        for entry in filter(None, git(main, "ls-tree", "-r", "-z", ref).stdout.split("\0")):
            metadata, name = entry.split("\t", 1)
            targets.add(name)
            if metadata.startswith("160000 "):
                gitlinks.add(name)
            else:
                regular_paths.add(name)

    for name in sorted(gitlinks):
        if any(path == name or path.startswith(name + "/") or name.startswith(path + "/")
               for path in regular_paths):
            raise ReviewError(f"子模块与普通文件之间的类型转换暂不支持：{name}")
        path = main
        for component in name.split("/"):
            path = path / component
            if path.is_symlink() or (path.exists() and not path.is_dir()):
                raise ReviewError(f"子模块路径必须缺失或为空目录，已停止：{name}")
        # Do not traverse submodules: even ignored files or a .git entry must be preserved.
        if path.exists() and any(path.iterdir()):
            raise ReviewError(f"子模块已初始化或目录非空，已保留内容并停止：{name}")

    # Ignored IDE/build files may stay, but must never be overwritten by tracked content.
    prefixes = set()
    for target in targets:
        parts = target.split("/")
        prefixes.update("/".join(parts[:i]) for i in range(1, len(parts)))
    ignored = git(main, "ls-files", "--others", "--ignored", "--exclude-standard", "-z").stdout
    for name in filter(None, ignored.split("\0")):
        parents = ["/".join(name.split("/")[:i]) for i in range(1, len(name.split("/")) + 1)]
        if name in prefixes or any(parent in targets for parent in parents):
            raise ReviewError(f"忽略文件会与目标内容冲突，已保留文件并停止：{name}")


def fetch_branch(main: Path, remote: str, branch: str) -> str:
    git(main, "check-ref-format", f"refs/heads/{branch}")
    git(main, "remote", "get-url", "--", remote)
    target = f"refs/remotes/{remote}/{branch}"
    git(main, "check-ref-format", target)
    print(f"Fetch {remote}/{branch}", file=sys.stderr)
    git(main, "fetch", "--no-tags", "--recurse-submodules=no", "--", remote, f"+refs/heads/{branch}:{target}")
    return resolve(main, f"{target}^{{commit}}")


def checkout_tree(main: Path, old_tree: str, new_tree: str) -> None:
    git(main, "read-tree", "-m", "-u", old_tree, new_tree)
    # Empty placeholders keep residual gitlinks from appearing as unstaged deletions.
    for entry in filter(None, git(main, "ls-tree", "-r", "-z", new_tree).stdout.split("\0")):
        metadata, name = entry.split("\t", 1)
        if metadata.startswith("160000 "):
            (main / name).mkdir(parents=True, exist_ok=True)


def snapshot(main: Path, branch: str, remote: str, base: str, latest: bool) -> dict:
    git(main, "check-ref-format", f"refs/heads/{branch}")
    if branch == base:
        raise ReviewError("请选择功能分支，不能把基准分支作为 Review 对象。")
    source_ref = f"refs/heads/{branch}"
    source_sha = resolve(main, f"{source_ref}^{{commit}}")
    base_sha = fetch_branch(main, remote, base)
    if latest:
        upstream_remote = git(main, "config", "--get", f"branch.{branch}.remote", check=False).stdout.strip()
        upstream_ref = git(main, "config", "--get", f"branch.{branch}.merge", check=False).stdout.strip()
        if not upstream_remote or upstream_remote == "." or not upstream_ref.startswith("refs/heads/"):
            raise ReviewError("--latest 需要功能分支配置远端 upstream。")
        source_sha = fetch_branch(main, upstream_remote, upstream_ref[len("refs/heads/"):])
        local_sha = resolve(main, f"{source_ref}^{{commit}}")
        ancestor = git(main, "merge-base", "--is-ancestor", local_sha, source_sha, check=False)
        if ancestor.returncode:
            raise ReviewError("远端功能分支未包含本地提交（本地领先或已分叉），拒绝遗漏本地代码；请在开发 worktree 协调后重试。")

    merged = git(main, "merge-tree", "--write-tree", base_sha, source_sha, check=False)
    if merged.returncode == 1:
        raise ReviewError("模拟合并存在冲突，主工作区未改变：\n" + merged.stdout.strip())
    if merged.returncode:
        raise ReviewError(merged.stderr.strip() or "merge-tree 失败；需要 Git 2.38+。")
    tree = merged.stdout.strip().splitlines()[0]
    ensure_tree_supported(main, tree, base_sha)

    worktree = git(main, "for-each-ref", "--format=%(worktreepath)", source_ref).stdout.strip()
    if worktree and git(Path(worktree), "status", "--porcelain").stdout:
        print("注意：功能 worktree 的未提交修改不在本次 Review 快照中。", file=sys.stderr)
    return {"branch": branch, "remote": remote, "base": base, "latest": latest,
            "source_sha": source_sha, "base_sha": base_sha, "tree": tree}


def apply_snapshot(main: Path, state_path: Path, state: dict) -> None:
    old_head = resolve(main, "HEAD")
    old_tree = git(main, "write-tree").stdout.strip()
    ensure_tree_supported(main, state["tree"], state["base_sha"], old_tree, "HEAD")
    state.update(version=1, main=str(main), phase="applying",
                 allowed_heads=[old_head, state["base_sha"]], allowed_trees=[old_tree, state["tree"]])
    # Journal before mutating HEAD/index so an interrupted run can be inspected and finished.
    save_state(state_path, state)
    for name, sha in (("base", state["base_sha"]), ("source", state["source_sha"]), ("tree", state["tree"])):
        git(main, "update-ref", f"refs/greview/{name}", sha)
    git(main, "-c", "core.hooksPath=/dev/null", "checkout", "--detach", "--no-overwrite-ignore", old_head)
    checkout_tree(main, old_tree, state["tree"])
    git(main, "update-ref", "--no-deref", "HEAD", state["base_sha"], old_head)
    state.update(phase="ready")
    state.pop("allowed_heads")
    state.pop("allowed_trees")
    save_state(state_path, state)


def report(main: Path, state: dict | None) -> None:
    print(f"Review 目录：{main}")
    if state is None:
        print("当前没有脚本管理的 Review 快照。")
        return
    print(f"状态：{state['phase']}")
    print(f"功能分支：{state['branch']} @ {state['source_sha'][:12]}")
    print(f"基准：{state['remote']}/{state['base']} @ {state['base_sha'][:12]}")
    print(f"来源：{'远端 upstream 快照' if state['latest'] else '本地已提交快照'}")
    print(git(main, "diff", "--cached", "--stat").stdout, end="")
    print("在 GoLand 打开此目录，在 Commit/本地更改中查看暂存区 diff。")


def finish(main: Path, state_path: Path, state: dict) -> None:
    head_tree = resolve(main, "HEAD^{tree}")
    current_tree = git(main, "write-tree").stdout.strip()
    ensure_tree_supported(main, head_tree, current_tree)
    state.update(phase="finishing", allowed_heads=[resolve(main, "HEAD")],
                 allowed_trees=[current_tree, head_tree])
    save_state(state_path, state)
    checkout_tree(main, current_tree, head_tree)
    for name in ("base", "source", "tree"):
        git(main, "update-ref", "-d", f"refs/greview/{name}")
    state_path.unlink()
    print(f"Review 已结束，主仓库回到当前 HEAD 的干净内容：{main}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="仓库任一 worktree 路径；始终操作主工作区")
    commands = parser.add_subparsers(dest="command", required=True)
    review = commands.add_parser("review", help="生成或切换功能分支 Review")
    review.add_argument("branch", help="本地功能分支名")
    review.add_argument("--remote", default="origin", help="基准远端，默认 origin")
    review.add_argument("--base", default="master", help="基准分支，默认 master")
    review.add_argument("--latest", action="store_true", help="使用 upstream 最新提交，保留开发 worktree 不变")
    refresh = commands.add_parser("refresh", help="刷新现有快照；默认保留此前来源设置")
    refresh.add_argument("--latest", action="store_true", help="改用 upstream 最新提交")
    refresh.add_argument("--local", action="store_true", help="改回本地已提交快照")
    commands.add_parser("finish", help="清除生成的暂存区 diff；手动修改存在时拒绝执行")
    commands.add_parser("status", help="显示当前快照及主工作区状态")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
            if os.environ.get(name):
                raise ReviewError(f"请先移除 {name} 环境覆盖，再使用 Review 脚本。")
        main_dir, common = main_checkout(Path(args.repo).resolve())
        state_dir = common / "greview"
        state_dir.mkdir(exist_ok=True)
        with (state_dir / "lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ReviewError("另一个 greview 操作正在运行，请稍后再试。")
            state_path = state_dir / "state.json"
            state = load_state(state_path, main_dir)
            if args.command == "status":
                report(main_dir, state)
                if state:
                    ensure_unedited(main_dir, state)
                return 0
            ensure_unedited(main_dir, state)
            if args.command == "finish":
                if state:
                    finish(main_dir, state_path, state)
                else:
                    print("当前没有 Review 快照，无需清理。")
                return 0
            if state and state["phase"] != "ready":
                raise ReviewError("上次操作未完成；先运行 status 查看，再运行 finish 清理生成状态。")
            if args.command == "refresh":
                if state is None:
                    raise ReviewError("没有可刷新的 Review，请先运行 review <功能分支>。")
                if args.latest and args.local:
                    raise ReviewError("--latest 与 --local 不能同时使用。")
                latest = args.latest or (state["latest"] and not args.local)
                next_state = snapshot(main_dir, state["branch"], state["remote"], state["base"], latest)
            else:
                next_state = snapshot(main_dir, args.branch, args.remote, args.base, args.latest)
            # Fetch/merge calculation can take time: check again before changing the review directory.
            ensure_unedited(main_dir, state)
            apply_snapshot(main_dir, state_path, next_state)
            report(main_dir, next_state)
        return 0
    except (ReviewError, OSError, ValueError) as error:
        print(f"[greview] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
