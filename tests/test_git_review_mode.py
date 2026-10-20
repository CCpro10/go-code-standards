"""Exercise review transitions in disposable repos; no production repository or network."""

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/git-review-mode/scripts/git_review.py"


class GitReviewModeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="git review test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "main checkout"
        self.feature = self.root / "feature worktree"
        self.remote = self.root / "remote.git"
        self.repo.mkdir()
        self.env = dict(os.environ, GIT_AUTHOR_NAME="Review Test", GIT_AUTHOR_EMAIL="review@example.com",
                        GIT_COMMITTER_NAME="Review Test", GIT_COMMITTER_EMAIL="review@example.com",
                        GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        self.git(self.repo, "init", "-b", "master")
        self.git(self.root, "init", "--bare", str(self.remote))
        self.git(self.repo, "remote", "add", "origin", str(self.remote))
        self.commit(self.repo, "shared.txt", "original\n")
        self.git(self.repo, "push", "-u", "origin", "master")
        self.git(self.repo, "worktree", "add", "-b", "feature/song", str(self.feature))
        self.commit(self.feature, "song.txt", "feature\n")
        self.git(self.feature, "push", "-u", "origin", "feature/song")
        self.commit(self.repo, "master-only.txt", "master addition\n")
        self.git(self.repo, "push", "origin", "master")

    def git(self, repo, *args, check=True):
        result = subprocess.run(["git", "-C", str(repo), *args], env=self.env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if check and result.returncode:
            self.fail(result.stderr or result.stdout)
        return result

    def commit(self, repo, path, content):
        (repo / path).write_text(content, encoding="utf-8")
        self.git(repo, "add", "--", path)
        self.git(repo, "commit", "-m", f"update {path}")

    def run_review(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.feature), *args],
                                env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def head(self, repo):
        return self.git(repo, "rev-parse", "HEAD").stdout.strip()

    def state(self):
        return json.loads((self.repo / ".git/greview/state.json").read_text())

    def fingerprint(self, repo):
        return (self.head(repo), self.git(repo, "write-tree").stdout,
                self.git(repo, "status", "--porcelain=v1", "-uall").stdout,
                self.git(repo, "diff", "--binary").stdout)

    def test_review_preserves_feature_and_master_only_changes(self):
        (self.feature / "shared.txt").write_text("staged developer edit\n")
        self.git(self.feature, "add", "shared.txt")
        (self.feature / "shared.txt").write_text("uncommitted work\n")
        before = self.fingerprint(self.feature)
        master = self.head(self.repo)
        result = self.run_review("review", "feature/song")
        self.assertIn("未提交修改", result.stderr)
        self.assertEqual(self.fingerprint(self.feature), before)
        self.assertEqual(self.head(self.repo), master)
        self.assertNotEqual(self.git(self.repo, "symbolic-ref", "-q", "HEAD", check=False).returncode, 0)
        self.assertEqual(self.git(self.repo, "diff", "--cached", "--name-only").stdout, "song.txt\n")
        self.assertEqual((self.repo / "master-only.txt").read_text(), "master addition\n")
        self.assertEqual(self.git(self.repo, "diff", "--name-only").stdout, "")
        self.run_review("finish")
        self.assertEqual(self.git(self.repo, "status", "--porcelain").stdout, "")
        self.assertFalse((self.repo / "song.txt").exists())
        self.assertEqual(self.fingerprint(self.feature), before)

    def test_dirty_main_rejected_without_changes(self):
        (self.repo / "shared.txt").write_text("manual main edit\n")
        before = self.fingerprint(self.repo)
        self.run_review("review", "feature/song", ok=False)
        self.assertEqual(self.fingerprint(self.repo), before)

    def test_untracked_main_rejected(self):
        (self.repo / "notes.txt").write_text("do not delete\n")
        self.run_review("review", "feature/song", ok=False)
        self.assertEqual((self.repo / "notes.txt").read_text(), "do not delete\n")

    def test_conflict_does_not_change_main_or_existing_review(self):
        self.run_review("review", "feature/song")
        before = self.fingerprint(self.repo)
        self.commit(self.feature, "shared.txt", "feature version\n")
        upstream = self.root / "upstream"
        self.git(self.root, "clone", str(self.remote), str(upstream))
        self.commit(upstream, "shared.txt", "master version\n")
        self.git(upstream, "push", "origin", "master")
        result = self.run_review("refresh", ok=False)
        self.assertIn("冲突", result.stderr)
        self.assertEqual(self.fingerprint(self.repo), before)
        self.assertEqual(self.state()["phase"], "ready")

    def test_refresh_uses_committed_feature_without_moving_branch(self):
        self.run_review("review", "feature/song")
        self.commit(self.feature, "second.txt", "new feature commit\n")
        before = self.fingerprint(self.feature)
        self.run_review("refresh")
        self.assertEqual(self.fingerprint(self.feature), before)
        self.assertIn("second.txt", self.git(self.repo, "diff", "--cached", "--name-only").stdout)

    def test_fetches_new_master_and_refreshes_base_without_false_deletions(self):
        self.run_review("review", "feature/song")
        original_master_ref = self.git(self.repo, "rev-parse", "master").stdout
        upstream = self.root / "master upstream"
        self.git(self.root, "clone", str(self.remote), str(upstream))
        self.commit(upstream, "new-master.txt", "new master change\n")
        self.git(upstream, "push", "origin", "master")
        self.run_review("refresh")
        self.assertEqual(self.head(self.repo), self.head(upstream))
        self.assertEqual(self.git(self.repo, "rev-parse", "master").stdout, original_master_ref)
        self.assertEqual((self.repo / "new-master.txt").read_text(), "new master change\n")
        self.assertEqual(self.git(self.repo, "diff", "--cached", "--name-only").stdout, "song.txt\n")
        self.run_review("finish")
        self.assertEqual(self.git(self.repo, "status", "--porcelain").stdout, "")

    def test_staged_deletion_and_rename_review_can_finish(self):
        self.git(self.feature, "mv", "shared.txt", "renamed.txt")
        self.git(self.feature, "rm", "song.txt")
        self.git(self.feature, "commit", "-m", "rename and delete")
        self.run_review("review", "feature/song")
        self.assertFalse((self.repo / "shared.txt").exists())
        self.assertTrue((self.repo / "renamed.txt").exists())
        self.run_review("finish")
        self.assertTrue((self.repo / "shared.txt").exists())
        self.assertFalse((self.repo / "renamed.txt").exists())

    def test_upstream_required_for_latest(self):
        self.git(self.feature, "branch", "--unset-upstream")
        result = self.run_review("review", "feature/song", "--latest", ok=False)
        self.assertIn("upstream", result.stderr)

    def test_no_common_history_is_rejected_without_touching_main(self):
        self.git(self.feature, "checkout", "--orphan", "unrelated")
        self.git(self.feature, "commit", "-m", "unrelated history")
        before = self.fingerprint(self.repo)
        self.run_review("review", "unrelated", ok=False)
        self.assertEqual(self.fingerprint(self.repo), before)

    def test_latest_fetches_upstream_without_pulling_feature_worktree(self):
        upstream = self.root / "feature upstream"
        self.git(self.root, "clone", "-b", "feature/song", str(self.remote), str(upstream))
        self.commit(upstream, "remote.txt", "remote feature commit\n")
        self.git(upstream, "push")
        before = self.fingerprint(self.feature)
        self.run_review("review", "feature/song", "--latest")
        self.assertEqual(self.fingerprint(self.feature), before)
        self.assertTrue((self.repo / "remote.txt").exists())
        self.assertNotEqual(self.state()["source_sha"], self.head(self.feature))
        self.run_review("refresh", "--local")
        self.assertFalse((self.repo / "remote.txt").exists())

    def test_latest_rejects_unpushed_or_diverged_commits(self):
        self.commit(self.feature, "local.txt", "local-only commit\n")
        before = self.fingerprint(self.repo)
        result = self.run_review("review", "feature/song", "--latest", ok=False)
        self.assertIn("未包含本地提交", result.stderr)
        self.assertEqual(self.fingerprint(self.repo), before)

    def test_unstaged_and_staged_manual_edits_are_preserved(self):
        for staged in (False, True):
            with self.subTest(staged=staged):
                if not (self.repo / ".git/greview/state.json").exists():
                    self.run_review("review", "feature/song")
                (self.repo / "song.txt").write_text("manual review edit\n")
                if staged:
                    self.git(self.repo, "add", "song.txt")
                before = self.fingerprint(self.repo)
                self.run_review("refresh", ok=False)
                self.run_review("finish", ok=False)
                self.assertEqual(self.fingerprint(self.repo), before)
                # Fixture-only restore to the recorded generated snapshot for the next subtest.
                (self.repo / "song.txt").write_text("feature\n")
                self.git(self.repo, "add", "song.txt")

    def test_new_review_files_block_finish(self):
        self.run_review("review", "feature/song")
        (self.repo / "notes.txt").write_text("review notes\n")
        self.run_review("finish", ok=False)
        self.assertEqual((self.repo / "notes.txt").read_text(), "review notes\n")

    def test_switch_review_keeps_one_main_directory(self):
        self.git(self.feature, "branch", "feature/other", "master")
        self.run_review("review", "feature/song")
        self.run_review("review", "feature/other")
        self.assertEqual(self.state()["branch"], "feature/other")
        self.assertEqual(self.git(self.repo, "status", "--porcelain").stdout, "")
        self.assertEqual(len(self.git(self.repo, "worktree", "list", "--porcelain").stdout.split("worktree ")) - 1, 2)

    def test_ignored_ide_files_stay_but_collisions_are_rejected(self):
        self.commit(self.repo, ".gitignore", ".idea/\n*.local\n")
        self.git(self.repo, "push", "origin", "master")
        (self.repo / ".idea").mkdir()
        (self.repo / ".idea/workspace.xml").write_text("IDE state\n")
        (self.repo / "settings.local").write_text("local state\n")
        self.commit(self.feature, "settings.local", "tracked feature state\n")
        result = self.run_review("review", "feature/song", ok=False)
        self.assertIn("忽略文件", result.stderr)
        self.assertEqual((self.repo / "settings.local").read_text(), "local state\n")
        (self.repo / "settings.local").unlink()
        self.run_review("review", "feature/song")
        self.run_review("finish")
        self.assertEqual((self.repo / ".idea/workspace.xml").read_text(), "IDE state\n")

    def test_status_and_empty_finish(self):
        self.run_review("status")
        self.run_review("finish")
        self.run_review("refresh", ok=False)

    def test_interrupted_apply_can_be_finished(self):
        self.run_review("review", "feature/song")
        state = self.state()
        state.update(phase="applying", allowed_heads=[state["base_sha"]],
                     allowed_trees=[state["tree"]])
        (self.repo / ".git/greview/state.json").write_text(json.dumps(state))
        self.run_review("refresh", ok=False)
        self.run_review("finish")
        self.assertEqual(self.git(self.repo, "status", "--porcelain").stdout, "")

    def test_hidden_index_flags_are_rejected(self):
        self.git(self.repo, "update-index", "--assume-unchanged", "shared.txt")
        (self.repo / "shared.txt").write_text("hidden manual edit\n")
        self.run_review("review", "feature/song", ok=False)
        self.assertEqual((self.repo / "shared.txt").read_text(), "hidden manual edit\n")

    def test_merge_in_progress_is_rejected(self):
        (self.repo / ".git/MERGE_HEAD").write_text(self.head(self.feature) + "\n")
        before = self.fingerprint(self.repo)
        result = self.run_review("review", "feature/song", ok=False)
        self.assertIn("MERGE_HEAD", result.stderr)
        self.assertEqual(self.fingerprint(self.repo), before)

    def add_empty_gitlink(self):
        path = ".idl-ai-coding/idl"
        # The submodule commit is deliberately unavailable; no .gitmodules is present.
        self.git(self.repo, "update-index", "--add", "--cacheinfo", f"160000,{'1' * 40},{path}")
        self.git(self.repo, "commit", "-m", "add residual gitlink")
        self.git(self.repo, "push", "origin", "master")
        self.git(self.feature, "merge", "--no-edit", "master")
        self.git(self.feature, "push", "origin", "feature/song")
        return self.repo / path

    def test_empty_gitlink_without_gitmodules_supports_full_review_cycle(self):
        path = self.add_empty_gitlink()
        path.mkdir(parents=True, exist_ok=True)
        before = self.fingerprint(self.feature)
        self.assertFalse((self.repo / ".gitmodules").exists())
        self.run_review("review", "feature/song")
        self.assertEqual(self.git(self.repo, "ls-files", "-s", "--", ".idl-ai-coding/idl").stdout.split()[0], "160000")
        self.assertEqual(self.git(self.repo, "diff", "--cached", "--name-only").stdout, "song.txt\n")
        self.run_review("refresh", "--latest")
        self.run_review("finish")
        self.assertEqual(self.git(self.repo, "status", "--porcelain").stdout, "")
        self.assertEqual(self.fingerprint(self.feature), before)
        self.assertFalse(any(path.iterdir()))

    def test_absent_gitlink_path_does_not_trigger_recursive_submodule_operations(self):
        path = self.add_empty_gitlink()
        if path.exists():
            path.rmdir()
        self.git(self.repo, "config", "submodule.recurse", "true")
        self.git(self.repo, "config", "fetch.recurseSubmodules", "true")
        self.run_review("review", "feature/song")
        self.run_review("refresh")
        self.run_review("finish")
        self.assertFalse(path.exists() and any(path.iterdir()))

    def test_nonempty_gitlink_is_rejected_without_modifying_files(self):
        path = self.add_empty_gitlink()
        path.mkdir(parents=True, exist_ok=True)
        (path / "keep.txt").write_text("local submodule data\n")
        before = self.fingerprint(self.repo)
        self.run_review("review", "feature/song", ok=False)
        self.assertEqual(self.fingerprint(self.repo), before)
        self.assertEqual((path / "keep.txt").read_text(), "local submodule data\n")

    def test_initialized_gitlink_is_rejected_even_when_clean(self):
        path = self.add_empty_gitlink()
        path.mkdir(parents=True, exist_ok=True)
        self.git(path, "init")
        result = self.run_review("review", "feature/song", ok=False)
        self.assertTrue((path / ".git").is_dir())
        self.assertIn("子模块", result.stderr)

    def test_populated_gitlink_blocks_refresh_and_finish(self):
        path = self.add_empty_gitlink()
        self.run_review("review", "feature/song")
        path.mkdir(parents=True, exist_ok=True)
        (path / "keep.txt").write_text("added during review\n")
        before = self.fingerprint(self.repo)
        self.run_review("refresh", ok=False)
        self.run_review("finish", ok=False)
        self.assertEqual(self.fingerprint(self.repo), before)
        self.assertEqual((path / "keep.txt").read_text(), "added during review\n")

    def test_symlink_gitlink_is_rejected(self):
        path = self.add_empty_gitlink()
        if path.exists():
            path.rmdir()
        outside = self.root / "outside"
        outside.mkdir()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(outside, target_is_directory=True)
        self.run_review("review", "feature/song", ok=False)
        self.assertTrue(path.is_symlink())

    def test_gitlink_pointer_change_is_staged_and_finish_restores_base_pointer(self):
        self.add_empty_gitlink()
        self.git(self.feature, "update-index", "--cacheinfo", f"160000,{'2' * 40},.idl-ai-coding/idl")
        self.git(self.feature, "commit", "-m", "update empty gitlink")
        self.run_review("review", "feature/song")
        self.assertIn("2" * 40, self.git(self.repo, "ls-files", "-s", "--", ".idl-ai-coding/idl").stdout)
        self.run_review("finish")
        self.assertIn("1" * 40, self.git(self.repo, "ls-files", "-s", "--", ".idl-ai-coding/idl").stdout)

    def test_staged_gitlink_edit_is_not_hidden_by_submodule_ignore(self):
        self.add_empty_gitlink()
        self.git(self.repo, "update-index", "--cacheinfo", f"160000,{'2' * 40},.idl-ai-coding/idl")
        index = self.git(self.repo, "write-tree").stdout
        self.run_review("review", "feature/song", ok=False)
        self.assertEqual(self.git(self.repo, "write-tree").stdout, index)

    def test_gitlink_to_regular_files_transition_stops_before_review(self):
        self.add_empty_gitlink()
        path = self.feature / ".idl-ai-coding/idl"
        self.git(self.feature, "rm", "--cached", ".idl-ai-coding/idl")
        path.mkdir(parents=True, exist_ok=True)
        self.commit(self.feature, ".idl-ai-coding/idl/idl.txt", "regular tracked data\n")
        before = self.fingerprint(self.repo)
        result = self.run_review("review", "feature/song", ok=False)
        self.assertIn("类型转换", result.stderr)
        self.assertEqual(self.fingerprint(self.repo), before)


if __name__ == "__main__":
    unittest.main()
