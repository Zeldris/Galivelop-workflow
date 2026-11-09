"""Stop hook: scripts/before-stop.py (P1 of docs/proposals/2026-10-25-repos-x.md), in temporary projects (a bare
origin plus a clone laid out like one that applied the workflow), run the way Claude Code runs a hook: the hook JSON
on stdin, the answer on stdout with exit 0.

Every case checks the reason that comes out, not only the exit code.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from test_hooks import ROOT, Project

SCRIPT = "before-stop.py"
LOG = "docs/log.md"


class StopProject(Project):
    def __init__(self, tmp):
        super().__init__(tmp, hooks=())  # no git hooks: the suite pushes to "main" freely
        self.scripts = self.work / ".claude" / "gw" / "scripts"
        shutil.copy2(ROOT / "scripts" / SCRIPT, self.scripts / SCRIPT)
        self.write(LOG, "log\n")
        self.commit("script and log")
        self.git("push", "-q", "-u", "origin", "main")

    def work_branch(self, name="claude/trabajo"):
        """A pushed working branch: the protected branch (main here) is not where the work goes."""
        self.git("checkout", "-q", "-b", name)
        self.git("push", "-q", "-u", "origin", name)

    def stop(self, payload=None, stdin=None, cwd=None, script=None):
        """(exit code, stdout, stderr-and-stdout) of the hook; `payload` is the hook's JSON object."""
        text = json.dumps({"hook_event_name": "Stop", "stop_hook_active": False, **(payload or {})}) \
            if stdin is None else stdin
        code, out = self.run("python3", str(script or self.scripts / SCRIPT), stdin=text or None, cwd=cwd)
        return code, out


def decision(test, out):
    """The hook's stdout parsed as JSON (it must be a single JSON object)."""
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        test.fail(f"stdout is not JSON: {out!r}")
    test.assertIsInstance(data, dict, out)
    return data


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-parar-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = StopProject(self.tmp)

    def assertBlocks(self, out, *needles):
        data = decision(self, out)
        self.assertEqual(data.get("decision"), "block", out)
        for needle in needles:
            self.assertIn(needle, data.get("reason", ""), out)
        return data

    def assertLetsStop(self, code, out):
        self.assertEqual(code, 0, out)
        self.assertNotIn('"block"', out)


class Commits(Base):
    def test_clean_and_pushed_does_not_block(self):
        code, out = self.p.stop()
        self.assertLetsStop(code, out)
        self.assertEqual(out.strip(), "", "nothing to say when there is nothing to fix")

    def test_unpushed_commit_blocks_with_the_push_command(self):
        p = self.p
        p.work_branch()
        p.write("src/a.py", "x = 1\n"); p.commit("local only")
        code, out = p.stop()
        self.assertEqual(code, 0, out)
        data = self.assertBlocks(out, "1 commit", "claude/trabajo", "git push -u origin claude/trabajo")
        self.assertNotIn(LOG, data["reason"], "a clean tree needs no log reminder")

    def test_unpushed_commit_on_the_protected_branch_warns_without_telling_to_push(self):
        p = self.p  # AGENTS.md: a push to the protected branch needs the user's confirmation and the three phases
        p.write("src/a.py", "x = 1\n"); p.commit("local only")
        code, out = p.stop()
        self.assertLetsStop(code, out)
        data = decision(self, out)
        self.assertNotIn("decision", data, out)
        message = data.get("systemMessage", "")
        for needle in ("1 commit", "'main'", "protected branch", "not pushed", "confirmation", "three phases"):
            self.assertIn(needle, message, out)
        self.assertNotIn("git push", message, out)

    def test_protected_branch_unpushed_and_dirty_blocks_only_for_the_log(self):
        p = self.p
        p.write("src/a.py", "x = 1\n"); p.commit("local only")
        p.write("src/b.py", "y = 1\n")
        code, out = p.stop()
        self.assertEqual(code, 0, out)
        data = self.assertBlocks(out, LOG)
        self.assertNotIn("git push", data["reason"])
        self.assertIn("confirmation", data["systemMessage"])

    def test_branch_without_upstream_blocks_with_the_push_command(self):
        p = self.p
        p.git("checkout", "-q", "-b", "claude/tema")
        p.write("src/a.py", "x = 1\n"); p.commit("on a new branch")
        code, out = p.stop()
        self.assertEqual(code, 0, out)
        self.assertBlocks(out, "claude/tema", "git push -u origin claude/tema")

    def test_new_branch_with_nothing_new_does_not_block(self):
        p = self.p
        p.git("checkout", "-q", "-b", "claude/vacia")  # same commit as origin/main: nothing unpushed
        code, out = p.stop()
        self.assertLetsStop(code, out)

    def test_pushed_branch_does_not_block(self):
        p = self.p
        p.git("checkout", "-q", "-b", "claude/subida")
        p.write("src/a.py", "x = 1\n"); p.commit("pushed")
        p.git("push", "-q", "-u", "origin", "claude/subida")
        code, out = p.stop()
        self.assertLetsStop(code, out)

    def test_detached_head_does_not_block(self):
        p = self.p
        p.git("checkout", "-q", "--detach")
        p.write("src/a.py", "x = 1\n"); p.commit("detached")
        code, out = p.stop()
        self.assertLetsStop(code, out)

    def test_stop_hook_active_lets_stop_even_with_unpushed_commits(self):
        p = self.p
        p.write("src/a.py", "x = 1\n"); p.commit("local only")
        p.write("src/b.py", "y = 1\n")  # and a dirty tree too
        code, out = p.stop({"stop_hook_active": True})
        self.assertLetsStop(code, out)
        self.assertEqual(out.strip(), "", "the second attempt is silent")


class WorkingTree(Base):
    def test_dirty_tree_without_the_log_blocks_naming_the_log(self):
        p = self.p
        p.write("src/a.py", "x = 1\n")  # untracked
        code, out = p.stop()
        self.assertEqual(code, 0, out)
        data = self.assertBlocks(out, LOG, "git add", "git commit")
        self.assertNotIn("git push", data["reason"], "nothing is committed yet, so nothing to push")

    def test_modified_tracked_file_without_the_log_blocks(self):
        p = self.p
        p.write("docs/notes.md", "changed\n")
        code, out = p.stop()
        self.assertEqual(code, 0, out)
        self.assertBlocks(out, LOG)

    def test_dirty_tree_with_the_log_modified_does_not_block(self):
        p = self.p
        p.write("src/a.py", "x = 1\n")
        p.write(LOG, "log\nnext step\n")
        code, out = p.stop()
        self.assertLetsStop(code, out)

    def test_dirty_tree_with_the_log_untracked_does_not_block(self):
        p = self.p
        p.git("rm", "-q", LOG)
        p.git("commit", "-q", "-m", "no log yet")
        p.git("push", "-q")
        p.write("src/a.py", "x = 1\n")
        p.write(LOG, "a new log\n")  # untracked, but it is among the changes
        code, out = p.stop()
        self.assertLetsStop(code, out)

    def test_staged_rename_into_the_log_counts(self):
        p = self.p
        p.git("mv", LOG, "docs/old-log.md")
        p.commit("move the log away")
        p.git("push", "-q")
        p.git("mv", "docs/old-log.md", LOG)  # staged rename: porcelain shows "R  old -> new"
        code, out = p.stop()
        self.assertLetsStop(code, out)

    def test_staged_rename_away_from_the_log_counts(self):
        p = self.p
        p.git("mv", LOG, "docs/log-2026.md")  # porcelain: "R  docs/log.md -> docs/log-2026.md" (origin = the log)
        code, out = p.stop()
        self.assertLetsStop(code, out)

    def test_unpushed_and_dirty_without_log_reports_both(self):
        p = self.p
        p.work_branch()
        p.write("src/a.py", "x = 1\n"); p.commit("local only")
        p.write("src/b.py", "y = 1\n")
        code, out = p.stop()
        self.assertEqual(code, 0, out)
        self.assertBlocks(out, "git push -u origin claude/trabajo", LOG)

    def test_unpushed_with_the_log_modified_still_blocks_on_the_push(self):
        p = self.p
        p.work_branch()
        p.write("src/a.py", "x = 1\n"); p.commit("local only")
        p.write(LOG, "log\nmore\n")
        code, out = p.stop()
        data = self.assertBlocks(out, "git push -u origin claude/trabajo")
        self.assertNotIn("git add", data["reason"])

    def test_gitignored_changes_do_not_count(self):
        p = self.p
        p.write(".gitignore", "build/\n"); p.commit("ignore build"); p.git("push", "-q")
        p.write("build/out.bin", "x\n")
        code, out = p.stop()
        self.assertLetsStop(code, out)

    def test_runs_from_a_subfolder(self):
        p = self.p
        p.write("src/a.py", "x = 1\n")
        code, out = p.stop(cwd=p.work / "src")
        self.assertBlocks(out, LOG)


class ClaudeWorktrees(Base):
    """Claude Code keeps isolated worktrees under .claude/worktrees/ inside the repo: untracked there is not work."""

    def test_only_untracked_worktrees_does_not_block(self):
        p = self.p
        p.write(".claude/worktrees/agent-1/src/a.py", "x = 1\n")
        code, out = p.stop()
        self.assertLetsStop(code, out)
        self.assertEqual(out.strip(), "")

    def test_worktrees_plus_a_real_change_blocks_counting_only_the_real_one(self):
        p = self.p
        p.write(".claude/worktrees/agent-1/src/a.py", "x = 1\n")
        p.write(".claude/worktrees/agent-2/b.py", "y = 1\n")
        p.write("src/real.py", "z = 1\n")
        code, out = p.stop()
        data = self.assertBlocks(out, LOG, "1 uncommitted change")
        self.assertNotIn("2 uncommitted", data["reason"])
        self.assertNotIn("3 uncommitted", data["reason"])

    def test_a_similar_prefix_still_counts(self):
        p = self.p
        p.write(".claude/worktrees-old/a.py", "x = 1\n")
        p.write(".claude/worktreesx", "x\n")
        code, out = p.stop()
        self.assertBlocks(out, "2 uncommitted changes")

    def test_a_tracked_file_under_worktrees_still_counts(self):
        p = self.p
        p.write(".claude/worktrees/keep.md", "k\n"); p.commit("track one")
        p.git("push", "-q")
        p.write(".claude/worktrees/keep.md", "changed\n")
        code, out = p.stop()
        self.assertBlocks(out, "1 uncommitted change", LOG)


class Ledger(Base):
    """The token ledger metrics.py rewrites on every stop is not work the log has to mention."""

    def test_only_the_ledger_changed_does_not_block(self):
        p = self.p
        p.write("docs/metrics/ledger.jsonl", "{}\n")
        code, out = p.stop()
        self.assertLetsStop(code, out)
        self.assertEqual(out.strip(), "")

    def test_the_ledger_plus_a_real_change_blocks_counting_only_the_real_one(self):
        p = self.p
        p.write("docs/metrics/ledger.jsonl", "{}\n")
        p.write("src/real.py", "z = 1\n")
        code, out = p.stop()
        data = self.assertBlocks(out, LOG, "1 uncommitted change")
        self.assertNotIn("2 uncommitted", data["reason"])

    def test_a_configured_ledger_path_is_the_one_ignored(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["metrics"] = {"ledger": "data/tokens.jsonl"}
        p.write(".claude/gw.json", json.dumps(cfg))
        p.git("add", "-A"); p.git("commit", "-q", "-m", "config"); p.git("push", "-q")
        p.write("data/tokens.jsonl", "{}\n")
        p.write("docs/metrics/ledger.jsonl", "{}\n")
        code, out = p.stop()
        self.assertBlocks(out, LOG, "1 uncommitted change")


class PushHelpers(Base):
    """P7 helpers shared by the push-marker and check-lock cases: a working branch with one unpushed commit and the
    marker file gw-push-in-progress.<pid> in the worktree's git dir."""

    def setUp(self):
        super().setUp()
        self.p.work_branch()
        self.p.write("src/a.py", "x = 1\n")
        self.p.commit("local only")
        self.marker = self.p.work / ".git" / "gw-push-in-progress.1"  # <pid> only has to be a suffix

    def put(self, text, age=0):
        self.marker.write_text(text)
        if age:
            old = time.time() - age
            os.utime(self.marker, (old, old))

    def mark(self, pid=None, sha=None, branch="claude/trabajo", age=0):
        """A marker as pre-push writes it; the sha defaults to the current HEAD."""
        self.put(f"{os.getpid() if pid is None else pid}\n{sha or self.p.sha()} {branch}\n", age=age)

    def dead_pid(self):
        child = subprocess.Popen([sys.executable, "-c", "pass"])
        child.wait()
        return child.pid

    def assertWarnsWithoutBlocking(self, out, *needles):
        self.assertNotIn('"block"', out)
        data = decision(self, out)
        self.assertNotIn("decision", data, out)
        for needle in ("push of this commit is in progress", "Do not push again", "git status -sb", *needles):
            self.assertIn(needle, data.get("systemMessage", ""), out)

    def assertStillBlocks(self, out):
        self.assertBlocks(out, "1 commit", "claude/trabajo", "git push -u origin claude/trabajo")
        self.assertNotIn("push of this commit is in progress", out)

    def linked_worktree(self):
        """A linked worktree on its own pushed branch with one unpushed commit: (path, hook script, git dir, sha)."""
        p = self.p
        linked = p.tmp / "linked"
        p.git("worktree", "add", "-q", "-b", "claude/otra", str(linked))
        p.git("push", "-q", "-u", "origin", "claude/otra", cwd=linked)
        (linked / "src").mkdir(exist_ok=True)
        (linked / "src" / "b.py").write_text("y = 1\n")
        p.git("add", "-A", cwd=linked)
        p.git("commit", "-q", "-m", "in the linked worktree", cwd=linked)
        script = linked / ".claude" / "gw" / "scripts" / SCRIPT
        gitdir = Path(p.git("rev-parse", "--absolute-git-dir", cwd=linked).stdout.strip())
        return linked, script, gitdir, p.git("rev-parse", "HEAD", cwd=linked).stdout.strip()


class PushInProgress(PushHelpers):
    """P7: while pre-push pushes this very HEAD (markers gw-push-in-progress.<pid> in the worktree's git dir: a pid, then one
    "<local sha> <branch>" line per ref) a second push would race it. A push of another sha does not carry this HEAD."""

    def test_marker_with_the_head_sha_warns_instead_of_blocking(self):
        self.mark()
        code, out = self.p.stop()
        self.assertEqual(code, 0, out)
        self.assertWarnsWithoutBlocking(out, "claude/trabajo", "1 commit")

    def test_marker_among_several_refs_warns_when_one_is_head(self):
        self.put(f"{os.getpid()}\n{'a' * 40} claude/otra\n{self.p.sha()} claude/trabajo\n")
        self.assertWarnsWithoutBlocking(self.p.stop()[1], "claude/trabajo")

    def test_marker_for_another_sha_blocks(self):
        self.mark(sha="a" * 40, branch="claude/otra")  # a subagent pushing another branch
        self.assertStillBlocks(self.p.stop()[1])

    def test_marker_for_another_branch_with_its_own_commit_blocks(self):
        p = self.p
        p.git("checkout", "-q", "-b", "claude/otra", "main")
        p.write("src/o.py", "o = 1\n"); p.commit("other branch")
        other = p.sha()
        p.git("checkout", "-q", "claude/trabajo")
        self.mark(sha=other, branch="claude/otra")
        self.assertStillBlocks(self.p.stop()[1])

    def test_head_advanced_after_the_push_started_blocks(self):
        p = self.p
        self.mark()  # the push started with this commit...
        p.write(LOG, "log\nmore\n"); p.commit("log updated while the push runs")  # ...and the log came after
        self.assertStillBlocks_n(p.stop()[1], "2 commits")

    def assertStillBlocks_n(self, out, count):
        self.assertBlocks(out, count, "git push -u origin claude/trabajo")
        self.assertNotIn("push of this commit is in progress", out)

    def test_marker_without_shas_blocks(self):
        self.put(f"{os.getpid()}\n")
        self.assertStillBlocks(self.p.stop()[1])
        self.put(f"{os.getpid()}\nclaude/trabajo\n")  # an old-format marker: a branch, no sha
        self.assertStillBlocks(self.p.stop()[1])

    def test_pid_of_another_user_counts_as_alive(self):
        self.mark(pid=1)  # init: alive; kill(1, 0) is a PermissionError unless root
        self.assertWarnsWithoutBlocking(self.p.stop()[1])

    def test_dead_pid_blocks(self):
        self.mark(pid=self.dead_pid())
        code, out = self.p.stop()
        self.assertEqual(code, 0, out)
        self.assertStillBlocks(out)

    def test_old_marker_blocks_even_with_a_live_pid(self):
        self.mark(age=3601)
        self.assertStillBlocks(self.p.stop()[1])

    def test_marker_just_under_an_hour_old_still_counts(self):
        self.mark(age=3500)
        self.assertWarnsWithoutBlocking(self.p.stop()[1])

    def test_marker_dated_far_in_the_future_blocks(self):
        self.mark(age=-7200)
        self.assertStillBlocks(self.p.stop()[1])

    def test_garbage_content_blocks(self):
        sha = self.p.sha()
        for text in ("not a pid\nclaude/trabajo\n", "", "\n", f"-5\n{sha} b\n", f"0\n{sha} b\n", f"12abc\n{sha} b\n",
                     "\x00\xff garbage", f"1.5\n{sha} b\n"):
            with self.subTest(text=text):
                self.put(text)
                self.assertStillBlocks(self.p.stop()[1])

    def test_unreadable_marker_blocks(self):
        self.marker.mkdir()  # a directory where the file should be
        self.assertStillBlocks(self.p.stop()[1])

    def test_absent_marker_blocks_as_before(self):
        self.assertFalse(self.marker.exists())
        code, out = self.p.stop()
        self.assertStillBlocks(out)

    def test_marker_is_per_worktree(self):
        p = self.p
        linked, script, gitdir, sha = self.linked_worktree()
        self.assertNotEqual(gitdir, p.work / ".git")
        self.assertBlocks(p.stop(cwd=linked, script=script)[1], "claude/otra", "git push -u origin claude/otra")
        # the marker of the main checkout's push does not silence the linked one, even if it lists its sha...
        self.mark(sha=sha, branch="claude/otra")
        self.assertBlocks(p.stop(cwd=linked, script=script)[1], "claude/otra", "git push -u origin claude/otra")
        # ...one in the linked worktree's own git dir does...
        own = gitdir / f"gw-push-in-progress.{os.getpid()}"
        main_sha = p.sha()
        own.write_text(f"{os.getpid()}\n{sha} claude/otra\n{main_sha} claude/trabajo\n")
        self.assertWarnsWithoutBlocking(p.stop(cwd=linked, script=script)[1], "claude/otra")
        # ...and does not silence the main checkout, even though it lists the main HEAD's sha too
        self.marker.unlink()
        self.assertStillBlocks(p.stop()[1])

    def test_two_markers_in_one_worktree_do_not_hide_each_other(self):
        p = self.p
        first, second = self.p.work / ".git" / "gw-push-in-progress.11", self.p.work / ".git" / "gw-push-in-progress.22"
        self.marker.unlink() if self.marker.exists() else None
        first.write_text(f"{os.getpid()}\n{'a' * 40} claude/otra\n")  # a live push of another sha
        second.write_text(f"{os.getpid()}\n{p.sha()} claude/trabajo\n")  # the push of this HEAD, written later
        self.assertWarnsWithoutBlocking(p.stop()[1], "claude/trabajo")
        first.unlink()
        self.assertWarnsWithoutBlocking(p.stop()[1], "claude/trabajo")
        # a dead and an old marker beside the live one are skipped, not fatal
        first.write_text(f"{self.dead_pid()}\n{p.sha()} claude/x\n")
        self.assertWarnsWithoutBlocking(p.stop()[1], "claude/trabajo")
        old = time.time() - 3601
        os.utime(second, (old, old))
        self.assertStillBlocks(p.stop()[1])

    def test_orphan_or_old_marker_of_a_linked_worktree_blocks(self):
        p = self.p
        linked, script, gitdir, sha = self.linked_worktree()
        marker = gitdir / "gw-push-in-progress.4242"
        marker.write_text(f"{os.getpid()}\n{sha} claude/otra\n")
        self.assertWarnsWithoutBlocking(p.stop(cwd=linked, script=script)[1], "claude/otra")  # it is read at all
        marker.write_text(f"{self.dead_pid()}\n{sha} claude/otra\n")  # the hook died without cleaning up
        self.assertBlocks(p.stop(cwd=linked, script=script)[1], "claude/otra", "git push -u origin claude/otra")
        marker.write_text(f"{os.getpid()}\n{sha} claude/otra\n")
        old = time.time() - 3601
        os.utime(marker, (old, old))
        self.assertBlocks(p.stop(cwd=linked, script=script)[1], "claude/otra", "git push -u origin claude/otra")

    def test_uncommitted_changes_still_block_while_a_push_runs(self):
        self.mark()
        self.p.write("src/b.py", "y = 1\n")
        code, out = self.p.stop()
        data = self.assertBlocks(out, LOG, "1 uncommitted change")
        self.assertNotIn("git push", data["reason"])
        self.assertIn("push of this commit is in progress", data["systemMessage"])

    def test_protected_branch_note_is_unchanged_with_a_marker(self):
        p = self.p
        p.git("checkout", "-q", "main")
        p.write("src/c.py", "z = 1\n"); p.commit("on main")
        self.mark(branch="main")
        code, out = p.stop()
        data = decision(self, out)
        self.assertIn("protected branch", data["systemMessage"])
        self.assertNotIn("push of this commit is in progress", data["systemMessage"])


class CheckInProgress(PushHelpers):
    """D41: while a check of this HEAD holds the E20 lock <git common dir>/gw/check.lock (symlink to
    "pid|start|sha|log") the hook says the check is running instead of telling to push; a dead, reused or malformed
    lock counts as absent, and a check of another commit only adds a note."""

    def lock(self, target, common=None):
        path = (common or self.p.work / ".git") / "gw" / "check.lock"
        path.parent.mkdir(exist_ok=True)
        if path.is_symlink() or path.exists():
            path.unlink()
        os.symlink(target, path)
        return path

    def start(self, pid):
        out = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True,
                             env={**os.environ, "LC_ALL": "C"}).stdout
        return " ".join(out.split())

    def live(self, log="/tmp/gw/check-abc.log", start=None, sha=None, pid=None):
        pid = os.getpid() if pid is None else pid
        sha = self.p.sha()[:12] if sha is None else sha
        return self.lock(f"{pid}|{self.start(pid) if start is None else start}|{sha}|{log}")

    def assertCheckNotice(self, out, log="/tmp/gw/check-abc.log"):
        self.assertNotIn('"block"', out)
        msg = decision(self, out).get("systemMessage", "")
        for needle in ("A check of this commit is running", f"pid {os.getpid()}", log, "wait for CHECK ok"):
            self.assertIn(needle, msg, out)
        self.assertNotIn("push of this commit is in progress", msg)

    def test_live_lock_of_this_head_replaces_the_push_reminder(self):
        self.live()
        self.assertCheckNotice(self.p.stop()[1])

    def test_dirty_run_of_this_head_counts(self):
        self.live(sha=self.p.sha()[:12] + "-dirty")
        self.assertCheckNotice(self.p.stop()[1])

    def test_lock_of_another_sha_blocks_and_notes_it(self):
        self.live(sha="0123456789ab")
        data = self.assertBlocks(self.p.stop()[1], "1 commit", "git push -u origin claude/trabajo")
        for needle in ("check of another commit or worktree is running", f"pid {os.getpid()}", "0123456789ab"):
            self.assertIn(needle, data["systemMessage"])

    def test_dead_pid_is_absent(self):
        self.lock(f"{self.dead_pid()}|Mon Jan  1 00:00:00 2024|abc|/tmp/x.log")
        self.assertStillBlocks(self.p.stop()[1])

    def test_reused_pid_with_another_start_is_absent(self):
        self.live(start="Mon Jan  1 00:00:00 2001")
        self.assertStillBlocks(self.p.stop()[1])

    def test_unknown_start_is_not_proven_live(self):
        # check-green.sh proc_is: "?" only matches when ps itself cannot tell; with a working ps it is another process
        self.live(start="?")
        self.assertStillBlocks(self.p.stop()[1])

    def test_malformed_locks_are_absent(self):
        for bad in ("garbage", "12x|a|b|c", "0|a|b|c", "-5|a|b|c", "|||", f"{os.getpid()}||abc|log"):
            with self.subTest(target=bad):
                self.lock(bad)
                self.assertStillBlocks(self.p.stop()[1])

    def test_regular_file_instead_of_a_symlink_is_absent(self):
        gw = self.p.work / ".git" / "gw"
        gw.mkdir(exist_ok=True)
        (gw / "check.lock").write_text("")
        self.assertStillBlocks(self.p.stop()[1])

    def test_huge_pid_fails_closed_with_the_push_block(self):
        self.live(pid=99999999999999999999)
        code, out = self.p.stop()
        self.assertEqual(code, 0)
        self.assertStillBlocks(out)
        self.assertNotIn("failed (", out)

    def test_unreadable_lock_fails_closed_with_the_push_block(self):
        if os.geteuid() == 0:
            self.skipTest("root reads any folder")
        self.live()
        gw = self.p.work / ".git" / "gw"
        gw.chmod(0o000)
        self.addCleanup(gw.chmod, 0o755)
        code, out = self.p.stop()
        self.assertEqual(code, 0)
        self.assertStillBlocks(out)
        self.assertNotIn("failed (", out)

    def test_no_gw_dir_blocks_as_before(self):
        self.assertFalse((self.p.work / ".git" / "gw").exists())
        self.assertStillBlocks(self.p.stop()[1])

    def test_lock_and_push_marker_together_report_the_push(self):
        self.live()
        self.mark()
        data = decision(self, self.p.stop()[1])
        self.assertNotIn("decision", data)
        self.assertIn("push of this commit is in progress", data["systemMessage"])

    def test_live_lock_does_not_hide_uncommitted_changes(self):
        self.live()
        self.p.write("src/b.py", "y = 1\n")
        data = self.assertBlocks(self.p.stop()[1], LOG, "1 uncommitted change")
        self.assertIn("A check of this commit is running", data["systemMessage"])

    def test_linked_worktree_reads_the_common_dir_and_needs_its_own_sha(self):
        p = self.p
        linked, script, gitdir, sha = self.linked_worktree()
        self.assertNotEqual(gitdir, p.work / ".git")
        self.assertBlocks(p.stop(cwd=linked, script=script)[1], "claude/otra", "git push -u origin claude/otra")
        self.live()  # a check of the main checkout's HEAD, in the .git shared by every worktree
        data = self.assertBlocks(p.stop(cwd=linked, script=script)[1], "claude/otra", "git push -u origin claude/otra")
        self.assertIn("check of another commit or worktree is running", data["systemMessage"])
        self.live(sha=sha[:12])  # a check of the linked worktree's own HEAD
        out = p.stop(cwd=linked, script=script)[1]
        self.assertCheckNotice(out)
        self.assertIn("claude/otra", out)
        self.assertFalse((gitdir / "gw").exists())  # not looked for in the per-worktree git dir


class ReminderNotGate(Base):
    """Without what it needs, the hook warns (systemMessage) and lets Claude stop."""

    def assertWarns(self, code, out, *needles):
        self.assertEqual(code, 0, out)
        data = decision(self, out)
        self.assertNotIn("decision", data, out)
        message = data.get("systemMessage", "")
        self.assertIn("doctor.py", message, out)
        self.assertIn(str(self.p.scripts / "doctor.py"), message, out)
        for needle in needles:
            self.assertIn(needle, message, out)

    def test_not_a_git_repo(self):
        scripts = self.tmp / "loose" / "scripts"
        scripts.mkdir(parents=True)
        for name in (SCRIPT, "config.py"):
            shutil.copy2(ROOT / "scripts" / name, scripts / name)
        elsewhere = self.tmp / "nogit"
        elsewhere.mkdir()
        code, out = self.p.stop(cwd=elsewhere, script=scripts / SCRIPT)
        self.assertEqual(code, 0, out)
        data = decision(self, out)
        self.assertNotIn("decision", data, out)
        self.assertIn("not inside a git repository", data["systemMessage"])
        self.assertIn(str(scripts / "doctor.py"), data["systemMessage"])

    def test_no_config(self):
        p = self.p
        (p.work / ".claude" / "gw.json").unlink()
        p.write("src/a.py", "x = 1\n")  # would block with a config
        code, out = p.stop()
        self.assertWarns(code, out, "gw.json")

    def test_invalid_config(self):
        p = self.p
        (p.work / ".claude" / "gw.json").write_text("{ nope")
        p.write("src/a.py", "x = 1\n")
        code, out = p.stop()
        self.assertWarns(code, out, "invalid JSON")

    def test_git_error(self):
        p = self.p
        p.write("src/a.py", "x = 1\n")
        (p.work / ".git" / "index").write_text("garbage, not an index")  # `git status` fails
        code, out = p.stop()
        self.assertWarns(code, out, "git status")

    def test_unreadable_stdin(self):
        p = self.p
        p.write("src/a.py", "x = 1\n")
        for stdin in ("this is not json", "[1, 2]", ""):
            with self.subTest(stdin=stdin):
                code, out = p.stop(stdin=stdin)
                self.assertWarns(code, out, "stdin")

    def test_no_remote_warns_instead_of_blocking(self):
        p = self.p
        p.git("remote", "remove", "origin")
        p.write("src/a.py", "x = 1\n"); p.commit("nowhere to push")
        code, out = p.stop()
        self.assertWarns(code, out, "remote")


class Plugin(Base):
    def test_runs_from_the_plugin_folder_on_the_projects_repo(self):
        plugin = self.tmp / "plugin"
        (plugin / "scripts").mkdir(parents=True)
        (plugin / "schema").mkdir()
        for name in (SCRIPT, "config.py"):
            shutil.copy2(ROOT / "scripts" / name, plugin / "scripts" / name)
        shutil.copy2(ROOT / "schema" / "gw.schema.json", plugin / "schema" / "gw.schema.json")
        p = self.p
        p.write("src/a.py", "x = 1\n")
        code, out = p.stop(cwd=p.work, script=plugin / "scripts" / SCRIPT)
        self.assertBlocks(out, LOG)


class Wiring(unittest.TestCase):
    """The hook is registered where the other workflow hooks are."""

    def commands(self, path):
        data = json.loads((ROOT / path).read_text())
        return [h["command"] for e in data["hooks"].get("Stop", []) for h in e["hooks"]
                if "before-stop.py" in h["command"]]

    def test_plugin_hooks(self):
        cmds = self.commands("hooks/hooks.json")
        self.assertEqual(len(cmds), 1, cmds)
        self.assertIn('"${CLAUDE_PLUGIN_ROOT}"/scripts/before-stop.py', cmds[0])
        self.assertTrue(cmds[0].startswith("python3 "), cmds[0])

    def test_metrics_is_a_second_stop_hook(self):
        for path, base in (("hooks/hooks.json", '"${CLAUDE_PLUGIN_ROOT}"/scripts'),
                           ("templates/claude/settings.json", '"$CLAUDE_PROJECT_DIR"/.claude/gw/scripts')):
            data = json.loads((ROOT / path).read_text())
            cmds = [h["command"] for e in data["hooks"]["Stop"] for h in e["hooks"]]
            self.assertEqual(cmds[-1], f"python3 {base}/metrics.py record", cmds)

    def test_settings_template(self):
        cmds = self.commands("templates/claude/settings.json")
        self.assertEqual(len(cmds), 1, cmds)
        self.assertIn('"$CLAUDE_PROJECT_DIR"/.claude/gw/scripts/before-stop.py', cmds[0])
        self.assertTrue(cmds[0].startswith("python3 "), cmds[0])


if __name__ == "__main__":
    unittest.main()
