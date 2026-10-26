"""Git hooks and their scripts, end to end: templates/githooks/pre-push and pre-commit, scripts/es-codigo.sh and
scripts/revisado.sh, in temporary repos (a bare "origin" plus a clone laid out like a project that applied the
workflow), with `git push` / `git commit` going through the real hooks (core.hooksPath).

Git runs isolated from this machine's configuration (GIT_CONFIG_GLOBAL to a temp file, GIT_CONFIG_NOSYSTEM=1), so
the suite behaves the same on a machine that signs commits and on a CI runner without an identity.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZERO = "0" * 40
VERSION = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]  # one fact, one place
BASE_CONFIG = {"version": VERSION, "language": "en", "log": "docs/log.md", "protectedBranch": "main",
               "pushToProtected": "direct", "check": ["bash check.sh"], "reviewMark": "docs/revisado.txt",
               "content": ["^docs/", "\\.md$"]}
# Built by concatenation so this file itself never looks like a secret or a conflict to the hooks.
FAKE_TOKEN = "gh" + "p_" + "A1b2C3d4" * 5
MARK_OPEN, MARK_CLOSE = "<" * 7 + " HEAD", ">" * 7 + " other"


class Project:
    """A bare origin and a clone (`work`) with .claude/gw.json, the workflow's scripts and the git hooks."""

    def __init__(self, tmp, config=None, check="exit 0", hooks=("pre-push", "pre-commit")):
        self.tmp = tmp
        self.bare = tmp / "origin.git"
        self.work = tmp / "work"
        gitconfig = tmp / "gitconfig"
        gitconfig.write_text("[user]\n\tname = Test\n\temail = test@example.com\n[commit]\n\tgpgsign = false\n"
                             "[tag]\n\tgpgsign = false\n[init]\n\tdefaultBranch = main\n[advice]\n\tdetachedHead = false\n")
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith("GIT_") and k not in ("CLAUDECODE", "CLAUDE_PROJECT_DIR")}
        self.env.update(GIT_CONFIG_GLOBAL=str(gitconfig), GIT_CONFIG_NOSYSTEM="1", TMPDIR=str(tmp),
                        GW_CHECK_CACHE="0")  # the cache is off except in the classes that test it
        self.git("init", "-q", "--bare", str(self.bare), cwd=tmp)
        self.git("init", "-q", str(self.work), cwd=tmp)
        self.git("remote", "add", "origin", str(self.bare))
        gw = self.work / ".claude" / "gw"
        (gw / "scripts").mkdir(parents=True)
        (gw / "schema").mkdir()
        for name in ("config.py", "es-codigo.sh", "revisado.sh", "bitacora.py", "check-verde.sh", "check.sh"):
            shutil.copy2(ROOT / "scripts" / name, gw / "scripts" / name)
        shutil.copy2(ROOT / "schema" / "gw.schema.json", gw / "schema" / "gw.schema.json")
        (self.work / ".githooks").mkdir()
        for name in hooks:  # commit-msg only where a test asks: other suites commit broken configs and old logs
            shutil.copy2(ROOT / "templates" / "githooks" / name, self.work / ".githooks" / name)
        (self.work / ".claude" / "gw.json").write_text(json.dumps(dict(BASE_CONFIG, **(config or {})), indent=2))
        (self.work / "check.sh").write_text(check + "\n")
        (self.work / "docs").mkdir()
        (self.work / "docs" / "notes.md").write_text("notes\n")
        self.git("config", "core.hooksPath", ".githooks")
        self.commit("base")  # goes through pre-commit: the workflow's own files must not look like secrets
        self.git("push", "-q", "--no-verify", "origin", "main")
        self.base = self.sha()

    def git(self, *args, cwd=None, ok=True, env=None, stdin=None):
        r = subprocess.run(["git", *args], cwd=cwd or self.work, env=dict(self.env, **(env or {})),
                           capture_output=True, text=True, input=stdin, stdin=None if stdin else subprocess.DEVNULL)
        if ok and r.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed:\n{r.stdout}{r.stderr}")
        return r

    def write(self, rel, text):
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, message, env=None, ok=True):
        self.git("add", "-A")
        return self.git("commit", "-q", "-m", message, env=env, ok=ok)

    def sha(self, rev="HEAD"):
        return self.git("rev-parse", rev + "^{commit}").stdout.strip()

    def push(self, *args, env=None, cwd=None):
        r = self.git("push", *args, env=env, cwd=cwd, ok=False)
        return r.returncode, r.stdout + r.stderr

    def run(self, *cmd, env=None, cwd=None, stdin=None):
        r = subprocess.run(list(cmd), cwd=cwd or self.work, env=dict(self.env, **(env or {})), capture_output=True,
                           text=True, input=stdin, stdin=None if stdin else subprocess.DEVNULL)
        return r.returncode, r.stdout + r.stderr

    def set_remote_main(self, sha):
        if sha is None:
            self.git("update-ref", "-d", "refs/heads/main", cwd=self.bare)
        else:
            self.git("update-ref", "refs/heads/main", sha, cwd=self.bare)


class Base(unittest.TestCase):
    config = None
    hooks = ("pre-push", "pre-commit")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-ganchos-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Project(self.tmp, self.config, hooks=self.hooks)


class ProtectedBranchMark(Base):
    """The portal's eight cases for a push to the protected branch, plus the real revisado.sh flow."""

    def setUp(self):
        super().setUp()
        p = self.p
        p.git("checkout", "-q", "-b", "feature")
        p.write("src/code.py", "x = 1\n"); p.commit("code"); self.code = p.sha()
        p.write("docs/revisado.txt", self.code + "\n"); p.commit("mark")
        p.write("docs/notes.md", "more notes\n"); p.commit("content"); self.marked = p.sha()
        p.write("src/code.py", "x = 2\n"); p.commit("more code"); self.after_mark = p.sha()
        p.git("checkout", "-q", "-b", "other", p.base)
        p.write("docs/notes.md", "only content\n"); p.commit("only content"); self.only_content = p.sha()
        p.write("src/other.py", "y = 1\n"); p.commit("code on other")
        p.write("docs/revisado.txt", self.code + "\n"); p.commit("foreign mark"); self.foreign = p.sha()
        p.write("docs/revisado.txt", "garbage\n"); p.commit("garbage mark"); self.garbage = p.sha()

    def push_main(self, sha, remote_main="base"):
        self.p.set_remote_main(self.p.base if remote_main == "base" else remote_main)
        return self.p.push("-f", "origin", f"{sha}:refs/heads/main")

    def test_code_without_mark_refused(self):
        code, out = self.push_main(self.code)
        self.assertNotEqual(code, 0, out)
        self.assertIn("no review mark", out)
        self.assertIn("revisado.sh", out)

    def test_mark_then_content_accepted(self):
        code, out = self.push_main(self.marked)
        self.assertEqual(code, 0, out)

    def test_dry_run_to_the_protected_branch_runs_the_hook(self):
        # aplicar.md step 6 proves the protection with --dry-run: the hook must refuse it, and nothing moves.
        code, out = self.p.push("--dry-run", "origin", f"{self.code}:refs/heads/main")
        self.assertNotEqual(code, 0, out)
        self.assertIn("no review mark", out)
        self.assertEqual(self.p.git("rev-parse", "main", cwd=self.p.bare).stdout.strip(), self.p.base)

    def test_code_after_mark_refused(self):
        code, out = self.push_main(self.after_mark)
        self.assertNotEqual(code, 0, out)
        self.assertIn("code changed after the review mark", out)

    def test_only_content_accepted(self):
        code, out = self.push_main(self.only_content)
        self.assertEqual(code, 0, out)

    def test_mark_from_another_branch_refused(self):
        code, out = self.push_main(self.foreign)
        self.assertNotEqual(code, 0, out)
        self.assertIn("not an ancestor", out)

    def test_garbage_mark_refused(self):
        code, out = self.push_main(self.garbage)
        self.assertNotEqual(code, 0, out)
        self.assertIn("not a commit", out)

    def test_new_protected_branch_compares_against_empty_tree(self):
        code, out = self.push_main(self.code, remote_main=None)
        self.assertNotEqual(code, 0, out)
        self.assertIn("WARNING: main has no .claude/gw.json on the remote yet", out)
        code, out = self.push_main(self.marked, remote_main=None)
        self.assertEqual(code, 0, out)

    def relax(self, start, **changes):
        """A commit on `start` that adds code and edits its own config to let that code through."""
        p = self.p
        p.git("checkout", "-q", "-B", "relax", start)
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg.update(changes)
        p.write(".claude/gw.json", json.dumps(cfg))
        p.write("src/sneaky.py", "z = 1\n"); p.commit("relax the rule")
        return p.sha()

    def test_a_commit_cannot_widen_content_to_pass_its_own_code(self):
        code, out = self.push_main(self.relax(self.p.base, content=[".*"]))
        self.assertNotEqual(code, 0, out)
        self.assertIn("no review mark", out)
        self.assertIn(".claude/gw.json", out)

    def test_a_commit_cannot_unprotect_the_branch_it_is_pushed_to(self):
        code, out = self.push_main(self.relax(self.p.base, protectedBranch="release"))
        self.assertNotEqual(code, 0, out)
        self.assertIn("no review mark", out)

    def test_a_commit_cannot_move_the_mark_to_a_file_it_writes(self):
        p = self.p
        relaxed = self.relax(p.base, reviewMark="src/mark.txt")
        p.write("src/mark.txt", relaxed + "\n"); p.commit("own mark")
        code, out = self.push_main(p.sha())
        self.assertNotEqual(code, 0, out)
        self.assertIn("no review mark (docs/revisado.txt)", out)

    def test_a_reviewed_config_change_is_accepted(self):
        p = self.p
        relaxed = self.relax(p.base, content=[".*"])
        p.write("docs/revisado.txt", relaxed + "\n"); p.commit("mark")
        code, out = self.push_main(p.sha())
        self.assertEqual(code, 0, out)

    def test_invalid_config_on_the_remote_tip_fails_closed(self):
        p = self.p
        p.git("checkout", "-q", "-b", "broken", p.base)
        p.write(".claude/gw.json", "{not json"); p.git("commit", "-q", "-a", "--no-verify", "-m", "broken config")
        broken = p.sha()
        p.git("push", "-q", "--no-verify", "origin", f"{broken}:refs/heads/broken")
        code, out = self.push_main(self.marked, remote_main=broken)
        self.assertNotEqual(code, 0, out)
        self.assertIn(f"in commit {broken[:7]}", out)

    def test_invalid_config_on_an_open_branch_tip_does_not_block_its_fix(self):
        p = self.p
        p.git("checkout", "-q", "-b", "wip", p.base)
        p.write(".claude/gw.json", "{not json"); p.git("commit", "-q", "-a", "--no-verify", "-m", "WIP: broken config")
        p.git("push", "-q", "--no-verify", "origin", "HEAD:refs/heads/wip")
        p.git("checkout", "-q", p.base, "--", ".claude/gw.json"); p.commit("fix the config")
        code, out = p.push("origin", "HEAD:refs/heads/wip")
        self.assertEqual(code, 0, out)
        self.assertIn("WARNING: the .claude/gw.json of refs/heads/wip's tip", out)

    def test_unknown_remote_protected_sha_fails_closed(self):
        line = f"refs/heads/feature {self.marked} refs/heads/main {'1' * 40}\n"
        code, out = self.p.run(str(self.p.work / ".githooks" / "pre-push"), "origin", str(self.p.bare), stdin=line)
        self.assertNotEqual(code, 0, out)
        self.assertIn("git fetch origin main", out)

    def test_pr_mode_still_requires_the_mark_on_a_direct_push(self):
        p = self.p
        p.git("checkout", "-q", "-b", "pr-mode", self.code)
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["pushToProtected"] = "pr"
        p.write(".claude/gw.json", json.dumps(cfg)); p.commit("pr mode")
        code, out = self.push_main(p.sha())
        self.assertNotEqual(code, 0, out)
        self.assertIn("no review mark", out)

    def test_config_is_read_from_the_pushed_commit_not_the_working_tree(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["content"] = cfg["content"] + ["^src/"]       # uncommitted: would turn the pushed code into content
        cfg["pushToProtected"] = "pr"
        p.write(".claude/gw.json", json.dumps(cfg))
        code, out = self.push_main(self.code)
        self.assertNotEqual(code, 0, out)
        self.assertIn("no review mark", out)

    def test_pushed_commit_without_a_config_refused(self):
        p = self.p
        p.git("checkout", "-q", "-b", "no-config", p.base)
        p.git("rm", "-q", ".claude/gw.json"); p.git("commit", "-q", "--no-verify", "-m", "drop config")
        code, out = p.push("origin", "HEAD:refs/heads/no-config")
        self.assertNotEqual(code, 0, out)
        self.assertIn("from .claude/gw.json in commit", out)

    def test_shallow_clone_fails_closed_with_deepen_command(self):
        p = self.p
        p.set_remote_main(p.base)
        p.git("push", "-q", "--no-verify", "-f", "origin", f"{self.marked}:refs/heads/feature")
        shallow = self.tmp / "shallow"
        p.git("clone", "-q", "--depth", "1", "--branch", "feature", "file://" + str(p.bare), str(shallow), cwd=self.tmp)
        p.git("config", "core.hooksPath", ".githooks", cwd=shallow)
        code, out = p.push("origin", "HEAD:refs/heads/main", cwd=shallow)
        self.assertNotEqual(code, 0, out)
        self.assertIn("git fetch --deepen=200 origin main", out)


class PrePush(Base):
    def setUp(self):
        super().setUp()
        self.p.git("checkout", "-q", "-b", "feature")

    def test_lists_pushed_commits(self):
        p = self.p
        p.write("src/a.py", "a = 1\n"); p.commit("first change")
        p.write("src/a.py", "a = 2\n"); p.commit("second change")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertIn("pushing 2 commit(s) to refs/heads/feature", out)
        self.assertIn("first change", out)
        self.assertIn("all green", out)

    def test_nothing_new_is_said_plainly(self):
        p = self.p  # git skips up-to-date refs, so the hook is fed the line directly
        code, out = p.run("bash", ".githooks/pre-push", "origin", str(p.bare),
                          stdin=f"refs/heads/main {p.base} refs/heads/main {p.base}\n")
        self.assertEqual(code, 0, out)
        self.assertIn("nothing new to push to refs/heads/main", out)
        self.assertIn("did you commit?", out)

    def test_new_ref_on_known_commits_is_a_creation(self):
        code, out = self.p.push("origin", "HEAD:refs/heads/copy")
        self.assertEqual(code, 0, out)
        self.assertIn(f"creating refs/heads/copy at {self.p.base[:7]}: all its commits are already on the remote", out)
        self.assertNotIn("commit(s)", out)
        self.assertNotIn("did you commit?", out)

    def test_rewind_warns_with_the_commits_that_leave(self):
        p = self.p
        p.write("src/a.py", "a = 1\n"); p.commit("one")
        p.write("src/a.py", "a = 2\n"); p.commit("two")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        code, out = p.push("-f", "origin", f"{p.base}:refs/heads/feature")
        self.assertEqual(code, 0, out)
        self.assertIn(f"WARNING: rewinding refs/heads/feature from {p.sha()[:7]} to {p.base[:7]}: "
                      "2 commit(s) leave this branch", out)
        self.assertNotIn("did you commit?", out)

    def test_sideways_force_push_warns_with_the_commits_that_leave(self):
        p = self.p
        p.write("src/a.py", "a = 1\n"); p.commit("one")
        p.write("src/a.py", "a = 2\n"); p.commit("two")
        self.assertEqual(p.push("origin", "feature")[0], 0)
        old = p.sha()
        p.git("checkout", "-q", "-b", "other", p.base)
        p.write("src/b.py", "b = 1\n"); p.commit("elsewhere")
        self.assertEqual(p.push("origin", "other")[0], 0)
        code, out = p.push("-f", "origin", "other:refs/heads/feature")
        self.assertEqual(code, 0, out)
        self.assertIn(f"moving refs/heads/feature to {p.sha()[:7]}: 1 commit(s) it gains", out)
        self.assertIn(f"WARNING: moving refs/heads/feature sideways from {old[:7]} to {p.sha()[:7]}: "
                      "2 commit(s) leave this branch", out)

    def test_fast_forward_to_commits_of_other_branches_counts_what_it_gains(self):
        p = self.p
        p.write("src/a.py", "a = 1\n"); p.commit("one")
        p.write("src/a.py", "a = 2\n"); p.commit("two")
        p.write("src/a.py", "a = 3\n"); p.commit("three")
        self.assertEqual(p.push("origin", "feature")[0], 0)
        self.assertEqual(p.push("origin", f"{p.base}:refs/heads/other")[0], 0)
        code, out = p.push("origin", "feature:refs/heads/other")
        self.assertEqual(code, 0, out)
        self.assertIn(f"moving refs/heads/other to {p.sha()[:7]}: 3 commit(s) it gains, "
                      "already on the remote in other branches", out)

    def marker_check(self, body="exit 0"):
        """A check that copies the push marker (while the hook still runs) to snap.txt, then runs `body`."""
        p = self.p
        self.snap = self.tmp / "snap.txt"
        self.marker = p.work / ".git" / "gw-push-en-curso"
        p.write("check.sh", f'cp "$(git rev-parse --git-common-dir)/gw-push-en-curso" "{self.snap}"; {body}\n')
        p.commit("check records the push marker")

    def test_push_marker_exists_while_checking_and_is_removed_after_success(self):
        p = self.p
        self.marker_check()
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        lines = self.snap.read_text().splitlines()
        self.assertTrue(lines[0].isdigit(), lines)  # the hook's pid
        self.assertEqual(lines[1:], [f"{p.sha()} feature"], "the local sha being pushed, then the branch")
        self.assertFalse(self.marker.exists(), "the marker must go when the push ends")
        self.assertEqual([f.name for f in (p.work / ".git").glob("gw-push-en-curso*")], [])

    def test_push_marker_is_removed_after_a_failing_check(self):
        p = self.p
        self.marker_check("exit 1")
        code, out = p.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn("check failed", out)
        self.assertTrue(self.snap.exists(), "the marker was there while the check ran")
        self.assertFalse(self.marker.exists(), "the marker must go when the push fails")

    def test_push_marker_is_removed_when_the_hook_is_interrupted(self):
        p = self.p
        started = self.tmp / "started"
        marker = p.work / ".git" / "gw-push-en-curso"
        p.write("check.sh", f'touch "{started}"; sleep 30\n'); p.commit("slow check")
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            started.unlink() if started.exists() else None
            proc = subprocess.Popen(["bash", ".githooks/pre-push", "origin", str(p.bare)], cwd=p.work, env=p.env,
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    start_new_session=True)
            proc.stdin.write(f"refs/heads/feature {p.sha()} refs/heads/feature {ZERO}\n"); proc.stdin.close()
            for _ in range(100):
                if started.exists():
                    break
                time.sleep(0.1)
            self.assertTrue(started.exists(), "the check never started")
            self.assertEqual(marker.read_text().splitlines()[0], str(proc.pid), "the marker holds the hook's pid")
            os.killpg(proc.pid, sig)
            proc.communicate(timeout=30)
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse(marker.exists(), f"the marker must go when the hook gets {sig.name}")

    def test_push_marker_lists_the_local_sha_of_each_ref_and_skips_deletions(self):
        p = self.p
        first = p.sha()
        p.write("src/a.py", "a = 1\n"); p.commit("second commit")
        second = p.sha()
        self.marker_check("exit 0")
        third = p.sha()
        self.snap = self.tmp / "snap.txt"
        stdin = (f"refs/heads/feature {third} refs/heads/feature {ZERO}\n"
                 f"refs/heads/old {ZERO} refs/heads/gone {first}\n"
                 f"HEAD~1 {second} refs/heads/other {ZERO}\n")
        code, out = p.run("bash", ".githooks/pre-push", "origin", str(p.bare), stdin=stdin)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.snap.read_text().splitlines()[1:], [f"{third} feature", f"{second} other"])
        self.assertFalse(self.marker.exists())

    def test_push_marker_that_cannot_be_written_does_not_fail_the_push(self):
        p = self.p
        (p.work / ".git" / "gw-push-en-curso").mkdir()  # a directory in the way: mv cannot replace it
        p.write("src/a.py", "a = 1\n"); p.commit("change")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertIn("all green", out)

    def test_push_marker_of_another_push_is_not_removed_by_this_one(self):
        p = self.p
        marker = p.work / ".git" / "gw-push-en-curso"
        self.marker_check("printf '999999\\nother\\n' > \"$(git rev-parse --git-common-dir)/gw-push-en-curso\"")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertEqual(marker.read_text(), "999999\nother\n")

    def test_failing_check_blocks_the_push(self):
        p = self.p
        p.write("check.sh", "echo broken-check-output; exit 1\n"); p.commit("break the check")
        code, out = p.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn("check failed", out)
        self.assertIn("broken-check-output", out)
        self.assertIn("--no-verify", out)

    def test_check_runs_on_the_pushed_commit_not_the_working_tree(self):
        p = self.p
        p.write("check.sh", "test ! -e broken\n"); p.commit("check refuses a broken file")
        p.write("broken", "uncommitted\n")       # dirty working tree that would fail the check in place
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        (p.work / "broken").unlink()
        p.write("broken", "committed\n"); p.commit("commit the broken file")
        (p.work / "broken").unlink()             # clean-looking working tree, broken commit
        code, out = p.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn("check failed", out)
        self.assertEqual(p.git("worktree", "list").stdout.count("\n"), 1, "temporary worktree left behind")

    def test_checks_know_whether_the_push_goes_to_the_protected_branch(self):
        p = self.p
        p.write("check.sh", 'echo "protected=$GW_PUSH_PROTECTED"; [ "$GW_PUSH_PROTECTED" = false ]\n')
        p.commit("check only passes off the protected branch")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        code, out = p.push("origin", "HEAD:refs/heads/feature", "HEAD:refs/heads/main")
        self.assertNotEqual(code, 0, out)
        self.assertIn("check failed", out)
        self.assertIn("protected=true", out)

    def test_checks_run_in_order_and_all_must_pass(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["check"] = ["bash check.sh", "test -e second-ok"]
        p.write(".claude/gw.json", json.dumps(cfg)); p.commit("two checks")
        code, out = p.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn("test -e second-ok", out)

    def test_conflict_markers_refused(self):
        p = self.p
        p.write("src/merged.py", "\n".join([MARK_OPEN, "a = 1", "=======", "a = 2", MARK_CLOSE, ""]))
        p.commit("bad merge")
        code, out = p.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn("conflict markers", out)

    def test_rej_and_orig_files_refused(self):
        p = self.p
        p.write("src/a.py.rej", "leftover\n"); p.commit("leftover")
        code, out = p.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn(".rej", out)

    def test_conflict_markers_already_on_another_branch_refused_on_the_protected_branch(self):
        p = self.p  # a task that publishes alone: git push origin <branch>:main, its commits already on the remote
        p.write("src/merged.py", "\n".join([MARK_OPEN, "a = 1", "=======", "a = 2", MARK_CLOSE, ""]))
        p.commit("bad merge")
        self.assertEqual(p.push("--no-verify", "origin", "feature")[0], 0)
        code, out = p.push("origin", "feature:main")
        self.assertNotEqual(code, 0, out)
        self.assertIn("this push to main has conflict markers", out)
        self.assertIn("src/merged.py", out)

    def test_rej_already_on_another_branch_refused_on_the_protected_branch(self):
        p = self.p
        p.write("src/a.py.orig", "leftover\n"); p.commit("leftover")
        self.assertEqual(p.push("--no-verify", "origin", "feature")[0], 0)
        code, out = p.push("origin", "feature:main")
        self.assertNotEqual(code, 0, out)
        self.assertIn("this push to main adds *.rej / *.orig leftovers", out)

    def test_leftovers_only_on_the_protected_branch_already_are_not_blamed_on_the_push(self):
        p = self.p  # main already carries a marker: a push that does not touch that file is not refused for it
        p.git("checkout", "-q", "main")
        p.write("docs/old.md", "\n".join([MARK_OPEN, "x", MARK_CLOSE, ""])); p.commit("old marker")
        self.assertEqual(p.push("--no-verify", "origin", "main")[0], 0)
        p.write("docs/notes.md", "content only\n"); p.commit("content")
        code, out = p.push("origin", "main")
        self.assertEqual(code, 0, out)

    def test_deleting_a_branch_is_not_checked(self):
        p = self.p
        self.assertEqual(p.push("origin", "feature")[0], 0)
        p.write("check.sh", "exit 1\n"); p.commit("break the check")
        code, out = p.push("origin", ":feature")
        self.assertEqual(code, 0, out)

    def test_optional_scripts_are_called_with_the_ref_lines(self):
        p = self.p
        hook = p.work / ".claude" / "gw" / "scripts" / "tests-relacionados.sh"
        hook.write_text("#!/usr/bin/env bash\nread -r ref _ ; echo \"related saw $ref\"; grep -q check.sh \"$1\" || "
                        "{ echo related-missing-file; exit 1; }\n")
        hook.chmod(0o755)
        p.write("check.sh", "exit 0 # touched\n"); p.commit("touch check")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertIn("related saw refs/heads/feature", out)


    def test_optional_script_without_exec_bit_still_runs(self):
        p = self.p
        hook = p.work / ".claude" / "gw" / "scripts" / "tests-relacionados.sh"
        hook.write_text("#!/usr/bin/env bash\necho related-ran-and-failed; exit 1\n")
        hook.chmod(0o644)  # lost its exec bit: present still means it runs
        p.write("src/a.py", "a = 1\n"); p.commit("code")
        code, out = p.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn("related-ran-and-failed", out)


class PrePushWorktree(Base):
    """The temporary worktree the pre-push runs `check` in (anything but the clean working copy), its linked paths,
    the wrapper and the logs. `dirty` is an untracked file: it makes the working copy not clean."""

    def setUp(self):
        super().setUp()
        self.p.git("checkout", "-q", "-b", "feature")
        self.gwdir = self.gw_folder(self.tmp)

    def gw_folder(self, base, project=None):
        """<base>/gw-pre-push-wt-<uid>-<cksum of the common git dir>: the hook's per-user, per-repo folder."""
        project = project or self.p
        r = subprocess.run(["bash", "-c", 'cd "$(git rev-parse --git-common-dir)" && pwd | tr -d "\\n" | cksum'],
                           cwd=project.work, env=project.env, capture_output=True, text=True, check=True)
        return Path(base) / f"gw-pre-push-wt-{os.getuid()}-{r.stdout.split()[0]}"

    def age(self, path, hours=25):
        old = time.time() - hours * 3600
        os.utime(path, (old, old))

    def configure(self, **keys):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg.update(keys)
        p.write(".claude/gw.json", json.dumps(cfg))

    def leftovers(self):
        return sorted(x.name for x in self.gwdir.glob("wt.*")) if self.gwdir.is_dir() else []

    def assertNoWorktreeLeft(self, repo=None):
        repo = repo or self.p.work
        self.assertEqual(self.p.git("worktree", "list", cwd=repo).stdout.count("\n"),
                         self.worktrees_before, "temporary worktree left in git's list")
        self.assertEqual(self.leftovers(), [], "temporary worktree left on disk")

    worktrees_before = 1

    def where_check_ran(self, pwd_file):
        self.p.write("check.sh", f'pwd -P >> "{pwd_file}"\n')
        self.p.commit("check records where it runs")
        self.p.write("dirty", "untracked\n")

    def test_worktree_lives_in_a_per_repo_tmpdir_folder_never_in_the_git_dir(self):
        pwd_file = self.tmp / "pwd.txt"
        self.where_check_ran(pwd_file)
        code, out = self.p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        ran = Path(pwd_file.read_text().strip())
        self.assertEqual(ran.parent, self.gwdir.resolve())
        self.assertRegex(ran.name, r"^wt\.[A-Za-z0-9]{6}\.d$")
        self.assertNotIn("/.git/", str(ran) + "/", "jest-haste-map and others ignore paths under .git/")
        self.assertFalse((self.p.work / ".git" / "gw-pre-push").exists())
        self.assertNoWorktreeLeft()

    def test_two_repos_get_separate_worktree_folders(self):
        other = Project(Path(tempfile.mkdtemp(prefix="gw-ganchos-b-", dir=self.tmp)).resolve())
        self.assertNotEqual(self.gwdir, self.gw_folder(self.tmp, other))
        other.git("checkout", "-q", "-b", "feature")
        other.write("dirty", "untracked\n")
        self.p.write("dirty", "untracked\n")
        for project in (self.p, other):
            code, out = project.push("origin", "feature")
            self.assertEqual(code, 0, out)
        self.assertNoWorktreeLeft()

    def test_worktree_dir_relative_to_the_repo_root(self):
        p = self.p
        pwd_file = self.tmp / "pwd.txt"
        self.configure(worktreeDir=".cache/wt")
        p.write(".gitignore", ".cache/\ndirty\n")
        self.where_check_ran(pwd_file)
        p.write("dirty2", "untracked\n")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        ran = Path(pwd_file.read_text().strip())
        self.gwdir = self.gw_folder(p.work / ".cache" / "wt")
        self.assertEqual(ran.parent, self.gwdir.resolve())
        self.assertNoWorktreeLeft()

    def test_worktree_dir_absolute(self):
        p = self.p
        pwd_file = self.tmp / "pwd.txt"
        shared = self.tmp / "sandbox visible"
        self.configure(worktreeDir=str(shared) + "/")
        self.where_check_ran(pwd_file)
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.gwdir = self.gw_folder(shared)
        self.assertEqual(Path(pwd_file.read_text().strip()).parent, self.gwdir.resolve())
        self.assertNoWorktreeLeft()

    def test_unwritable_worktree_dir_fails_closed_naming_the_key(self):
        p = self.p
        blocker = self.tmp / "a-file"
        blocker.write_text("not a folder\n")
        self.configure(worktreeDir=str(blocker / "sub"))
        self.where_check_ran(self.tmp / "pwd.txt")
        code, out = p.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn("cannot create", out)
        self.assertIn("worktreeDir", out)

    def test_worktree_folder_is_private_to_the_user(self):
        self.where_check_ran(self.tmp / "pwd.txt")
        code, out = self.p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.gwdir.stat().st_mode & 0o777, 0o700)

    def test_a_symlinked_worktree_folder_is_refused(self):
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        self.gwdir.symlink_to(elsewhere)
        self.where_check_ran(self.tmp / "pwd.txt")
        code, out = self.p.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn("is a symlink", out)
        self.assertEqual(list(elsewhere.iterdir()), [], "nothing may be written through the symlink")

    def test_clean_working_copy_runs_in_place(self):
        pwd_file = self.tmp / "pwd.txt"
        self.p.write("check.sh", f'pwd -P >> "{pwd_file}"\n')
        self.p.commit("check records where it runs")
        code, out = self.p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertEqual(Path(pwd_file.read_text().strip()), self.p.work.resolve())
        self.assertFalse(self.gwdir.exists())

    def test_linked_worktree_uses_the_common_git_dir(self):
        p = self.p
        pwd_file = self.tmp / "pwd.txt"
        self.where_check_ran(pwd_file)
        (p.work / "dirty").unlink()
        linked = self.tmp / "linked"
        p.git("worktree", "add", "-q", "-b", "side", str(linked))
        (linked / "node_modules").mkdir()
        (linked / "node_modules" / "m").write_text("m\n")
        p.write("check.sh", f'pwd -P >> "{pwd_file}"; test -e node_modules/m\n')
        (linked / "check.sh").write_text(f'pwd -P >> "{pwd_file}"; test -e node_modules/m\n')
        p.git("add", "-A", cwd=linked)
        p.git("commit", "-q", "-m", "side change", cwd=linked)
        (linked / "dirty").write_text("untracked\n")
        r = p.git("push", "origin", "side", cwd=linked, ok=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ran = Path(pwd_file.read_text().strip())
        self.assertEqual(ran.parent, self.gwdir.resolve(), "must be the common git dir, not .git/worktrees/<name>")
        self.worktrees_before = 2
        self.assertNoWorktreeLeft(linked)

    def test_default_links_and_listed_paths_incl_spaces_files_and_missing_sources(self):
        p = self.p
        self.configure(worktreeLinks=["my dir/deps", "backend/node_modules", ".env", "absent", "docs/", "trailing/"])
        ran_check = self.tmp / "ran-check"
        p.write("check.sh", 'test -e "my dir/deps/d" && test -e backend/node_modules/b && test -e .env '
                            '&& test ! -e absent && test ! -L docs && test -L .env && test ! -e node_modules '
                            f'&& test -e trailing/t && echo ok >> "{ran_check}"\n')
        p.commit("check sees the links")
        for rel in ("my dir/deps/d", "backend/node_modules/b", "node_modules/default", "trailing/t"):
            p.write(rel, "x\n")
        p.write(".env", "SECRET=1\n")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertNoWorktreeLeft()
        self.assertEqual((p.work / "docs" / "notes.md").read_text(), "notes\n", "a tracked path is never replaced")

    def test_default_worktree_links_are_node_modules_and_venv(self):
        p = self.p
        p.write("check.sh", 'test -e node_modules/m && test -e .venv/v && test ! -e other/o\n')
        p.commit("check sees the default links")
        p.write("node_modules/m", "m\n"); p.write(".venv/v", "v\n"); p.write("other/o", "o\n")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)

    def test_empty_worktree_links_link_nothing(self):
        p = self.p
        self.configure(worktreeLinks=[])
        p.write("check.sh", 'test ! -e node_modules\n')
        p.commit("check sees no link")
        p.write("node_modules/m", "m\n")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)

    def test_worktree_links_outside_the_repo_are_refused_with_the_command(self):
        p = self.p
        self.configure(worktreeLinks=["../outside"])
        p.git("add", "-A"); p.git("commit", "-q", "--no-verify", "-m", "bad link")
        code, out = p.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn("cannot read 'check' from .claude/gw.json", out)
        self.assertIn("config.py", out)
        self.assertIn("validate", out)

    def test_path_with_spaces_everywhere(self):
        shutil.rmtree(self.tmp)
        self.tmp = Path(tempfile.mkdtemp(prefix="gw ganchos ")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = p = Project(self.tmp)
        self.gwdir = self.gw_folder(self.tmp)
        p.git("checkout", "-q", "-b", "feature")
        self.configure(worktreeLinks=["my deps"])
        p.write("check.sh", 'test -e "my deps/d"\n')
        p.commit("check sees the link")
        p.write("my deps/d", "d\n")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertNoWorktreeLeft()

    def test_check_wrapper_prefixes_each_check(self):
        p = self.p
        p.write("wrap.sh", 'echo "wrapped: $*" >> "$WRAP_LOG"; "$@"\n')
        self.configure(checkWrapper="bash wrap.sh", check=["bash check.sh", "test -e check.sh"])
        p.commit("wrapper")
        p.write("dirty", "untracked\n")
        log = self.tmp / "wrap.log"
        code, out = p.push("origin", "feature", env={"WRAP_LOG": str(log)})
        self.assertEqual(code, 0, out)
        self.assertEqual(log.read_text().splitlines(), ["wrapped: bash -c bash check.sh", "wrapped: bash -c test -e check.sh"])
        self.assertIn("check 'bash wrap.sh bash -c 'bash check.sh''", out)

    def test_check_wrapper_wraps_a_compound_check_as_a_whole(self):
        p = self.p
        p.write("wrap.sh", 'echo "args:$#" >> "$WRAP_LOG"; "$@"\n')
        out_file = self.tmp / "both.txt"
        self.configure(checkWrapper="bash wrap.sh", check=[f'echo a >> "{out_file}" && echo b >> "{out_file}"'])
        p.commit("compound check")
        log = self.tmp / "wrap.log"
        code, out = p.push("origin", "feature", env={"WRAP_LOG": str(log)})
        self.assertEqual(code, 0, out)
        self.assertEqual(log.read_text().splitlines(), ["args:3"], "the wrapper gets `bash -c <whole a && b>`")
        self.assertEqual(out_file.read_text(), "a\nb\n")

    def test_worktree_links_through_a_committed_symlink_never_write_outside(self):
        p = self.p
        outside = self.tmp / "outside"
        outside.mkdir()
        self.configure(worktreeLinks=["cache/x"])
        os.symlink(str(outside), p.work / "cache")
        p.commit("evil symlink")
        (p.work / "cache").unlink()  # the working copy has a real folder; the pushed tree has the symlink
        p.write("cache/x", "x\n")
        code, out = p.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn("resolves outside the temporary worktree", out)
        self.assertIn("worktreeLinks", out)
        self.assertEqual(list(outside.iterdir()), [], "nothing may be created outside the worktree")
        self.assertNoWorktreeLeft()

    def test_orphan_cleanup_prunes_nothing_else(self):
        p = self.p
        gone = self.tmp / "gone-worktree"
        p.git("worktree", "add", "-q", "--detach", str(gone), "HEAD")
        shutil.rmtree(gone)  # git still lists it (prunable): not ours to prune
        self.worktrees_before = 2
        self.gwdir.mkdir()
        (self.gwdir / "wt.nogit0.d").mkdir()
        (self.gwdir / "wt.nogit0").write_text("999999999\n")
        self.age(self.gwdir / "wt.nogit0")
        p.write("dirty", "untracked\n")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertIn("gone-worktree", p.git("worktree", "list").stdout)
        self.assertEqual(self.leftovers(), [], "an orphan git does not know is removed with a plain rm")

    def test_a_marker_still_empty_belongs_to_a_push_starting_up(self):
        p = self.p
        self.gwdir.mkdir()
        (self.gwdir / "wt.empty0").write_text("")
        p.write("dirty", "untracked\n")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.leftovers(), ["wt.empty0"])

    def test_a_process_of_another_user_counts_as_alive(self):
        p = self.p
        self.gwdir.mkdir()
        p.git("worktree", "add", "-q", "--detach", str(self.gwdir / "wt.other0.d"), "HEAD")
        (self.gwdir / "wt.other0").write_text("4242\n")
        fake = self.tmp / "fake-kill.sh"
        fake.write_text('kill() { echo "bash: kill: ($2) - Operation not permitted" >&2; return 1; }\n')
        p.write("dirty", "untracked\n")
        code, out = p.push("origin", "feature", env={"BASH_ENV": str(fake)})
        self.assertEqual(code, 0, out)
        self.assertEqual(self.leftovers(), ["wt.other0", "wt.other0.d"])
        self.worktrees_before = 2

    def test_failing_wrapper_blocks_and_names_the_full_command(self):
        p = self.p
        p.write("wrap.sh", 'echo wrapper-refused; exit 3\n')
        self.configure(checkWrapper="bash wrap.sh")
        p.commit("wrapper that refuses")
        code, out = p.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn("check failed", out)
        self.assertIn("'bash wrap.sh bash -c 'bash check.sh''", out)
        self.assertIn("wrapper-refused", out)
        self.assertIn("reproduce with: bash wrap.sh bash -c 'bash check.sh'", out)

    def test_each_failing_check_keeps_its_own_log(self):
        p = self.p
        p.write("check.sh", 'echo "boom-$RANDOM-$$"; exit 1\n')
        p.commit("failing check")
        logs = []
        for _ in range(2):
            code, out = p.push("origin", "feature")
            self.assertNotEqual(code, 0, out)
            found = re.search(r"full log: (\S+)\)", out)
            self.assertIsNotNone(found, out)
            logs.append(Path(found.group(1)))
        self.assertNotEqual(logs[0], logs[1], "a second push must not overwrite the first one's log")
        for log in logs:
            self.assertRegex(log.name, r"^gw-pre-push-check\.[A-Za-z0-9]{6}$")
            self.assertIn("boom-", log.read_text())

    def test_passing_checks_leave_no_log(self):
        code, out = self.p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertEqual(list(self.tmp.glob("gw-pre-push-check.*")), [])

    def test_two_pushes_at_once_do_not_touch_each_others_worktree(self):
        p = self.p
        pwds = self.tmp / "pwds.txt"
        p.write("check.sh", f'pwd -P >> "{pwds}"; sleep 3; test -f check.sh\n')
        p.commit("slow check")
        p.git("branch", "other")
        p.write("more.txt", "more\n"); p.commit("one more")
        p.write("dirty", "untracked\n")

        def start(*args):
            return subprocess.Popen(["git", "push", *args], cwd=p.work, env=p.env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
        first = start("origin", "feature")
        for _ in range(100):
            if pwds.exists():
                break
            time.sleep(0.1)
        second = start("origin", "other:refs/heads/other")
        out1, out2 = first.communicate(timeout=60)[0], second.communicate(timeout=60)[0]
        self.assertEqual((first.returncode, second.returncode), (0, 0), out1 + out2)
        self.assertEqual(len(set(pwds.read_text().split("\n")) - {""}), 2, "each push needs a worktree of its own")
        self.assertNoWorktreeLeft()

    def test_a_worktree_left_by_a_dead_push_is_removed_but_a_live_one_stays(self):
        p = self.p
        self.gwdir.mkdir()
        proc = subprocess.Popen(["true"]); proc.wait(); dead_pid = proc.pid
        live = subprocess.Popen(["sleep", "60"])
        self.addCleanup(live.kill)
        for name, pid in (("wt.dead00", dead_pid), ("wt.live00", live.pid)):
            p.git("worktree", "add", "-q", "--detach", str(self.gwdir / (name + ".d")), "HEAD")
            (self.gwdir / name).write_text(f"{pid}\n")
            self.age(self.gwdir / name)
        p.write("dirty", "untracked\n")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.leftovers(), ["wt.live00", "wt.live00.d"])
        self.assertTrue((self.gwdir / "wt.live00.d").is_dir())
        self.assertFalse((self.gwdir / "wt.dead00.d").exists())
        self.assertNotIn("wt.dead00", p.git("worktree", "list").stdout)

    def test_a_recent_marker_with_an_unknown_pid_stays(self):
        """A push from another pid namespace (container, sandbox) gives "No such process" here: under 24 h it stays."""
        p = self.p
        self.gwdir.mkdir()
        proc = subprocess.Popen(["true"]); proc.wait()
        p.git("worktree", "add", "-q", "--detach", str(self.gwdir / "wt.other1.d"), "HEAD")
        (self.gwdir / "wt.other1").write_text(f"{proc.pid}\n")
        self.age(self.gwdir / "wt.other1", hours=23)
        p.write("dirty", "untracked\n")
        code, out = p.push("origin", "feature")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.leftovers(), ["wt.other1", "wt.other1.d"])
        self.worktrees_before = 2

    def test_interrupting_the_hook_removes_its_worktree(self):
        p = self.p
        started = self.tmp / "started"
        p.write("check.sh", f'touch "{started}"; sleep 30\n')
        p.commit("hanging check")
        p.write("dirty", "untracked\n")
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            started.unlink() if started.exists() else None
            proc = subprocess.Popen(["bash", ".githooks/pre-push", "origin", str(p.bare)], cwd=p.work, env=p.env,
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    start_new_session=True)
            proc.stdin.write(f"refs/heads/feature {p.sha()} refs/heads/feature {ZERO}\n"); proc.stdin.close()
            for _ in range(100):
                if started.exists():
                    break
                time.sleep(0.1)
            self.assertTrue(started.exists(), "the check never started")
            self.assertEqual(len(self.leftovers()), 2, "a worktree and its marker exist while it runs")
            os.killpg(proc.pid, sig)
            proc.communicate(timeout=30)
            self.assertNotEqual(proc.returncode, 0)
            self.assertNoWorktreeLeft()


class PortableShell(unittest.TestCase):
    """macOS ships bash 3.2 and a BSD mktemp: no mapfile / associative arrays, and mktemp templates end in XXXXXX."""

    FILES = ("templates/githooks/pre-push", "templates/githooks/pre-commit", "scripts/tests-relacionados.sh",
             "scripts/fusionar.sh")

    def test_no_bash_4_features_and_bsd_safe_mktemp_templates(self):
        for rel in self.FILES:
            for n, line in enumerate((ROOT / rel).read_text().splitlines(), 1):
                code = line.split("#", 1)[0] if not line.lstrip().startswith("#") else ""
                self.assertNotRegex(code, r"\bmapfile\b|\breadarray\b|declare -A|typeset -A|\$\{[A-Za-z_]+,,\}|\$\{[A-Za-z_]+\^\^\}",
                                    f"{rel}:{n} uses a bash 4 feature")
                for template in re.findall(r'mktemp\b[^\n]*?"([^"]*X[^"]*)"', code):
                    self.assertRegex(template, r"XXXXXX$", f"{rel}:{n}: BSD mktemp needs the template to end in XXXXXX")


class CheckCache(Base):
    """The pre-push skips a `check` that already passed on the same tree with the same commands (check-verde.sh)."""
    SKIP = "check already green on this tree"
    ON = {"GW_CHECK_CACHE": ""}  # anything but 0 turns the cache on

    def setUp(self):
        super().setUp()
        p = self.p
        self.runs = self.tmp / "runs.txt"      # outside the work tree: the check counts its own runs here
        self.flag = self.tmp / "fail-flag"     # while it exists the check fails
        self.script(f'echo run >> "{self.runs}"; [ ! -e "{self.flag}" ]')
        p.commit("check counts its runs")
        p.git("push", "-q", "--no-verify", "origin", "main")
        p.base = p.sha()
        p.git("checkout", "-q", "-b", "feature")
        self.cache = p.work / ".git" / "gw-check-verde"

    def script(self, body):
        self.p.write("check.sh", body + "\n")

    def count(self):
        return len(self.runs.read_text().split()) if self.runs.exists() else 0

    def lines(self):
        return self.cache.read_text().splitlines() if self.cache.is_file() else []

    def push(self, *args, env=None):
        return self.p.push(*args, env=dict(self.ON, **(env or {})))

    def doc_change(self, text="x\n"):
        self.p.write("docs/notes.md", text)
        self.p.commit("doc " + text.strip())

    def test_green_push_is_recorded_and_the_same_tree_to_another_branch_skips_the_check(self):
        self.doc_change()
        code, out = self.push("origin", "feature")
        self.assertEqual((code, self.count(), len(self.lines())), (0, 1, 1), out)
        self.assertNotIn(self.SKIP, out)
        code, out = self.push("origin", "HEAD:refs/heads/other")
        self.assertEqual((code, self.count()), (0, 1), out)
        tree = self.p.git("rev-parse", "HEAD^{tree}").stdout.strip()
        self.assertRegex(out, re.escape(f"pre-push: {self.SKIP} ({tree[:7]}) with the same commands ") + r"\d+ min ago; "
                         r"skipping it \(to run it anyway: GW_CHECK_CACHE=0 git push\)")
        self.assertIn("all green", out)
        self.assertNotIn("check 'bash check.sh'", out)

    def test_a_different_tree_runs_the_check(self):
        self.doc_change("one\n")
        self.assertEqual(self.push("origin", "feature")[0], 0)
        self.doc_change("two\n")
        code, out = self.push("origin", "feature")
        self.assertEqual((code, self.count(), len(self.lines())), (0, 2, 2), out)
        self.assertNotIn(self.SKIP, out)
        self.assertIn("check 'bash check.sh'", out)

    def test_different_check_commands_run_the_check(self):
        self.doc_change()
        self.assertEqual(self.push("origin", "feature")[0], 0)
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg["check"] = ["bash check.sh", "true"]
        self.p.write(".claude/gw.json", json.dumps(cfg)); self.p.commit("one more command")
        code, out = self.push("origin", "feature")
        self.assertEqual((code, self.count()), (0, 2), out)
        self.assertNotIn(self.SKIP, out)
        self.assertIn("check 'true'", out)

    def test_a_cached_key_of_other_commands_is_not_a_hit_for_the_same_tree(self):
        # The config is part of the tree, so the key's own sensitivity to the commands is tested on its own here.
        self.doc_change()
        tree = self.p.git("rev-parse", "HEAD^{tree}").stdout.strip()
        helper = ".claude/gw/scripts/check-verde.sh"
        other = self.p.run("bash", helper, "key", tree, "", stdin="bash check.sh\ntrue\n")[1].strip()
        self.assertRegex(other, r"^[0-9a-f]{40}$")
        self.cache.write_text(f"{int(time.time())} {other}\n")
        code, out = self.push("origin", "feature")
        self.assertEqual((code, self.count()), (0, 1), out)
        self.assertNotIn(self.SKIP, out)

    def test_a_failing_check_is_not_recorded_and_the_next_push_runs_it(self):
        self.doc_change()
        self.flag.write_text("")
        code, out = self.push("origin", "feature")
        self.assertNotEqual(code, 0, out)
        self.assertIn("check failed", out)
        self.assertEqual((self.count(), self.lines()), (1, []), out)
        self.flag.unlink()
        code, out = self.push("origin", "feature")
        self.assertEqual((code, self.count(), len(self.lines())), (0, 2, 1), out)
        self.assertNotIn(self.SKIP, out)

    def test_a_push_to_the_protected_branch_neither_reads_nor_records_the_cache(self):
        self.doc_change()
        self.assertEqual(self.push("origin", "feature")[0], 0)
        before = self.lines()
        self.assertEqual(len(before), 1)
        code, out = self.push("origin", "HEAD:refs/heads/main")  # content only: no review mark needed
        self.assertEqual((code, self.count()), (0, 2), out)
        self.assertNotIn(self.SKIP, out)
        self.assertIn("check 'bash check.sh'", out)
        self.assertEqual(self.lines(), before)

    def test_a_protected_push_that_runs_green_does_not_record_either(self):
        self.doc_change()
        code, out = self.push("origin", "HEAD:refs/heads/main")
        self.assertEqual((code, self.count(), self.lines()), (0, 1, []), out)

    def test_gw_check_cache_0_runs_the_check_even_with_a_cached_key(self):
        self.doc_change()
        self.assertEqual(self.push("origin", "feature")[0], 0)
        code, out = self.push("origin", "HEAD:refs/heads/other", env={"GW_CHECK_CACHE": "0"})
        self.assertEqual((code, self.count()), (0, 2), out)
        self.assertNotIn(self.SKIP, out)
        code, out = self.push("origin", "HEAD:refs/heads/third")
        self.assertEqual((code, self.count()), (0, 2), out)
        self.assertIn(self.SKIP, out)

    def test_an_entry_older_than_24_hours_runs_the_check(self):
        self.doc_change()
        self.assertEqual(self.push("origin", "feature")[0], 0)
        key = self.lines()[0].split()[1]
        self.cache.write_text(f"{int(time.time()) - 24 * 3600 - 60} {key}\n")
        code, out = self.push("origin", "HEAD:refs/heads/other")
        self.assertEqual((code, self.count()), (0, 2), out)
        self.assertNotIn(self.SKIP, out)
        self.cache.write_text(f"{int(time.time()) - 24 * 3600 + 600} {key}\n")  # 10 minutes inside the window
        code, out = self.push("origin", "HEAD:refs/heads/third")
        self.assertEqual((code, self.count()), (0, 2), out)
        self.assertRegex(out, r"the same commands 14(3[0-9]|40) min ago")

    def test_a_missing_helper_runs_the_check_as_before(self):
        self.doc_change()
        (self.p.work / ".claude" / "gw" / "scripts" / "check-verde.sh").unlink()
        for ref in ("feature", "HEAD:refs/heads/other"):
            code, out = self.push("origin", ref)
            self.assertEqual(code, 0, out)
            self.assertNotIn(self.SKIP, out)
            self.assertIn("check 'bash check.sh'", out)
        self.assertEqual((self.count(), self.lines()), (2, []))

    def test_a_cache_path_that_is_a_directory_never_blocks_the_push(self):
        self.doc_change()
        self.cache.mkdir()
        for ref in ("feature", "HEAD:refs/heads/other"):
            code, out = self.push("origin", ref)
            self.assertEqual(code, 0, out)
            self.assertNotIn(self.SKIP, out)
        self.assertEqual(self.count(), 2)
        self.assertIn("is a directory, check not recorded", out)

    def test_the_hook_still_sets_up_the_worktree_for_the_related_tests_when_it_skips(self):
        # tests-relacionados.sh gets the folder the pushed commit is checked out in, also when the check is skipped.
        p = self.p
        where = self.tmp / "related-pwd.txt"
        shutil.copy2(ROOT / "scripts" / "tests-relacionados.sh", p.work / ".claude" / "gw" / "scripts" / "tests-relacionados.sh")
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["relatedTests"] = {"fast": [f'pwd > "{where}"'], "slow": []}
        p.write(".claude/gw.json", json.dumps(cfg))
        p.commit("related tests runner that says where it runs")
        self.assertEqual(self.push("origin", "feature")[0], 0)
        self.assertEqual(where.read_text().strip(), str(p.work))  # clean HEAD: the project itself
        where.unlink()
        p.write("dirty.txt", "makes the work tree dirty: the hook uses a temporary worktree\n")
        code, out = self.push("origin", "HEAD:refs/heads/other")
        self.assertEqual(code, 0, out)
        self.assertIn(self.SKIP, out)
        self.assertIn("related tests (fast)", out)
        ran_in = where.read_text().strip()
        self.assertRegex(ran_in, re.escape(str(self.tmp)) + r"/gw-pre-push-wt-\d+-\d+/wt\.\w+\.d$")

    def test_a_check_that_dirties_the_project_it_runs_in_is_not_recorded(self):
        # With HEAD clean the check runs in the project itself; a file it writes there is not in the pushed tree.
        p = self.p
        self.script(f'echo run >> "{self.runs}"; echo report > report.txt')
        p.commit("check leaves a report behind")
        code, out = self.push("origin", "feature")
        self.assertEqual((code, self.count(), self.lines()), (0, 1, []), out)
        self.assertIn("pre-push: the check left changes in the work tree, so it is not recorded and the next push "
                      "runs it again; see them with: git status", out)
        (p.work / "report.txt").unlink()
        code, out = self.push("origin", "HEAD:refs/heads/other")
        self.assertEqual((code, self.count()), (0, 2), out)
        self.assertNotIn(self.SKIP, out)

    def test_a_push_protected_only_by_the_remote_tips_config_does_not_read_the_cache(self):
        p = self.p
        self.doc_change()
        pushed = p.sha()
        self.assertEqual(self.push("origin", "feature")[0], 0)
        before = self.lines()
        self.assertEqual(len(before), 1)
        # The remote's release branch says it is the protected one; the pushed commit and the work tree say main.
        p.git("checkout", "-q", "-b", "release", p.base)
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["protectedBranch"] = "release"
        p.write(".claude/gw.json", json.dumps(cfg)); p.commit("release protects itself")
        p.git("push", "-q", "--no-verify", "origin", "release")
        p.git("checkout", "-q", "feature")
        code, out = self.push("-f", "origin", f"{pushed}:refs/heads/release")
        self.assertEqual(self.count(), 2, out)
        self.assertNotIn(self.SKIP, out)
        self.assertIn("check 'bash check.sh'", out)
        self.assertIn("no review mark", out)  # judged as the protected branch
        self.assertEqual(self.lines(), before)

    def test_a_push_protected_only_by_the_work_trees_config_does_not_read_the_cache(self):
        p = self.p
        self.doc_change()
        self.assertEqual(self.push("origin", "feature")[0], 0)
        before = self.lines()
        self.assertEqual(len(before), 1)
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["protectedBranch"] = "release"
        p.write(".claude/gw.json", json.dumps(cfg))  # not committed: only the work tree says it
        code, out = self.push("origin", "HEAD:refs/heads/release")
        self.assertEqual(self.count(), 2, out)
        self.assertNotIn(self.SKIP, out)
        self.assertIn("check 'bash check.sh'", out)
        self.assertIn("no review mark", out)  # judged as the protected branch
        self.assertEqual(self.lines(), before)


class CheckRunner(Base):
    """scripts/check.sh: the whole check through the same cache the pre-push reads."""
    ON = CheckCache.ON

    def setUp(self):
        super().setUp()
        p = self.p
        self.runs = self.tmp / "runs.txt"
        p.write("check.sh", f'echo run >> "{self.runs}"; echo checking-output; [ ! -e "{self.tmp / "fail-flag"}" ]\n')
        p.commit("check counts its runs")
        p.git("push", "-q", "--no-verify", "origin", "main")
        p.git("checkout", "-q", "-b", "feature")
        self.cache = p.work / ".git" / "gw-check-verde"
        self.runner = ".claude/gw/scripts/check.sh"

    def count(self):
        return len(self.runs.read_text().split()) if self.runs.exists() else 0

    def run_check(self, env=None):
        return self.p.run("bash", self.runner, env=dict(CheckCache.ON, **(env or {})))

    def test_a_dirty_work_tree_records_the_tree_it_would_commit_and_the_push_of_that_commit_skips(self):
        p = self.p
        p.write("docs/notes.md", "edited\n")
        p.write("src/new.py", "untracked = 1\n")
        index_before = (p.work / ".git" / "index").read_bytes()
        code, out = self.run_check()
        self.assertEqual((code, self.count()), (0, 1), out)
        self.assertIn("checking-output", out)  # streamed
        self.assertIn("the next push of this same tree will skip the check", out)
        self.assertEqual((p.work / ".git" / "index").read_bytes(), index_before)
        self.assertEqual(len(self.cache.read_text().splitlines()), 1)
        p.commit("exactly those changes")
        tree = p.git("rev-parse", "HEAD^{tree}").stdout.strip()
        code, out = p.push("origin", "feature", env=CheckCache.ON)
        self.assertEqual((code, self.count()), (0, 1), out)
        self.assertIn(f"check already green on this tree ({tree[:7]})", out)

    def test_a_different_change_than_the_one_checked_runs_the_check_on_push(self):
        p = self.p
        p.write("docs/notes.md", "edited\n")
        self.assertEqual(self.run_check()[0], 0)
        p.write("docs/notes.md", "edited differently\n")
        p.commit("another change")
        code, out = p.push("origin", "feature", env=CheckCache.ON)
        self.assertEqual((code, self.count()), (0, 2), out)
        self.assertNotIn("check already green", out)

    def test_a_check_that_modifies_a_tracked_file_is_not_recorded(self):
        p = self.p
        p.write("check.sh", f'echo run >> "{self.runs}"; echo more >> docs/notes.md\n')
        p.commit("check rewrites a tracked file")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)
        self.assertIn("the work tree changed during the run", out)
        self.assertIn("not recorded", out)
        self.assertNotIn("will skip the check", out)
        self.assertFalse(self.cache.exists())

    def test_a_check_that_creates_an_untracked_file_is_not_recorded(self):
        p = self.p
        p.write("check.sh", f'echo run >> "{self.runs}"; echo out > report.txt\n')
        p.commit("check leaves a report behind")
        code, out = self.run_check()
        self.assertEqual((code, self.count()), (0, 1), out)
        self.assertIn("the work tree changed during the run", out)
        self.assertNotIn("will skip the check", out)
        self.assertFalse(self.cache.exists())

    def test_assume_unchanged_or_skip_worktree_entries_run_the_check_but_record_nothing(self):
        p = self.p
        for n, flag in enumerate(("--assume-unchanged", "--skip-worktree"), 1):
            p.git("update-index", flag, "docs/notes.md")
            p.write("docs/notes.md", f"edit {n} git add -A would not see\n")
            code, out = self.run_check()
            self.assertEqual((code, self.count()), (0, n), out)
            self.assertIn("'docs/notes.md' is assume-unchanged or skip-worktree", out)
            self.assertIn("git update-index --no-assume-unchanged --no-skip-worktree -- 'docs/notes.md'", out)
            self.assertIn("not recorded for the pre-push: the cache is unavailable", out)
            self.assertFalse(self.cache.exists())
            p.git("update-index", "--no-" + flag[2:], "docs/notes.md")
            p.git("checkout", "--", "docs/notes.md")

    def test_a_failing_check_stops_at_the_failure_names_it_and_records_nothing(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["check"] = ["bash check.sh", "echo second-command; exit 3", "echo never-reached"]
        p.write(".claude/gw.json", json.dumps(cfg)); p.commit("three commands")
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("failed: 'echo second-command; exit 3'", out)
        self.assertIn("second-command", out)
        self.assertNotIn("never-reached", out)
        self.assertFalse(self.cache.exists())

    def test_the_check_wrapper_and_the_protected_flag_are_applied_like_the_pre_push_does(self):
        p = self.p
        out_file = self.tmp / "wrapped.txt"
        (p.work / "wrap.sh").write_text('"$@"\n')
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["checkWrapper"] = "bash wrap.sh"
        cfg["check"] = ["echo \"it's $GW_PUSH_PROTECTED\" >> \"%s\"" % out_file]
        p.write(".claude/gw.json", json.dumps(cfg)); p.commit("wrapped check")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)
        self.assertIn("running 'bash wrap.sh bash -c", out)
        self.assertEqual(out_file.read_text(), "it's false\n")

    def test_it_runs_from_the_repo_root_whatever_the_current_directory(self):
        p = self.p
        (p.work / "sub").mkdir()
        code, out = p.run("bash", str(p.work / self.runner), cwd=p.work / "sub", env=CheckCache.ON)
        self.assertEqual((code, self.count()), (0, 1), out)

    def test_with_the_cache_off_it_runs_and_leaves_the_cache_alone(self):
        code, out = self.run_check(env={"GW_CHECK_CACHE": "0"})
        self.assertEqual((code, self.count()), (0, 1), out)
        self.assertIn("not recorded", out)
        self.assertFalse(self.cache.exists())


class CheckVerde(Base):
    """scripts/check-verde.sh on its own: key, worktree-tree, has and add, with their edge cases."""
    HELPER = ".claude/gw/scripts/check-verde.sh"
    TREE = "a" * 40

    def setUp(self):
        super().setUp()
        self.cache = self.p.work / ".git" / "gw-check-verde"

    def helper(self, *args, stdin=None, env=None, cwd=None, helper=None):
        return self.p.run("bash", helper or self.HELPER, *args, stdin=stdin, env=dict(CheckCache.ON, **(env or {})), cwd=cwd)

    def key(self, tree=None, wrapper="", commands="bash check.sh\n"):
        code, out = self.helper("key", tree or self.TREE, wrapper, stdin=commands)
        self.assertEqual(code, 0, out)
        return out.strip()

    def test_the_key_changes_with_the_tree_the_wrapper_and_each_command(self):
        base = self.key()
        self.assertRegex(base, r"^[0-9a-f]{40}$")
        self.assertEqual(self.key(), base)
        self.assertEqual(self.key(commands="bash check.sh"), base)  # a trailing newline is not a command
        keys = {self.key(tree="b" * 40), self.key(wrapper="flatpak run x"), self.key(commands="bash check.sh\ntrue\n"),
                self.key(commands="bash  check.sh\n"), self.key(commands="\n")}
        self.assertEqual(len(keys), 5)
        self.assertNotIn(base, keys)

    def test_the_key_is_the_hash_of_the_documented_text(self):
        text = f"gw-check-cache 1\ntree {self.TREE}\nwrapper w\ncommands\nc1\nc2\n"
        expected = self.p.git("hash-object", "--stdin", stdin=text).stdout.strip()
        self.assertEqual(self.key(wrapper="w", commands="c1\nc2\n"), expected)

    def test_worktree_tree_is_the_tree_of_a_commit_with_everything_added_and_leaves_the_index_alone(self):
        p = self.p
        p.write("docs/notes.md", "edited\n")
        p.write("src/new file.py", "untracked = 1\n")
        (p.work / "docs" / "notes.md").chmod(0o644)
        index_before = (p.work / ".git" / "index").read_bytes()
        status_before = p.git("status", "--porcelain").stdout
        code, out = self.helper("worktree-tree")
        self.assertEqual(code, 0, out)
        self.assertEqual((p.work / ".git" / "index").read_bytes(), index_before)
        self.assertEqual(p.git("status", "--porcelain").stdout, status_before)
        self.assertEqual([e for e in os.listdir(self.tmp) if e.startswith("gw-check")], [], "temp left behind")
        p.commit("exactly those changes")
        self.assertEqual(out.strip(), p.git("rev-parse", "HEAD^{tree}").stdout.strip())

    def test_worktree_tree_of_a_clean_tree_is_the_head_tree(self):
        code, out = self.helper("worktree-tree")
        self.assertEqual((code, out.strip()), (0, self.p.git("rev-parse", "HEAD^{tree}").stdout.strip()), out)

    def test_worktree_tree_with_no_index_yet_in_a_folder_with_spaces(self):
        solo = self.tmp / "solo repo"
        (solo / "scripts").mkdir(parents=True)
        shutil.copy2(ROOT / "scripts" / "check-verde.sh", solo / "scripts" / "check-verde.sh")
        self.p.git("init", "-q", cwd=solo)
        (solo / "a b.txt").write_text("hello\n")
        self.assertFalse((solo / ".git" / "index").exists())
        code, out = self.helper("worktree-tree", cwd=solo, helper=str(solo / "scripts" / "check-verde.sh"))
        self.assertEqual(code, 0, out)
        self.assertFalse((solo / ".git" / "index").exists(), "the real index must stay absent")
        self.p.git("add", "-A", cwd=solo)
        self.assertEqual(out.strip(), self.p.git("write-tree", cwd=solo).stdout.strip())

    def test_worktree_tree_sees_a_file_edited_in_the_same_second_it_was_staged(self):
        # Racy git: an entry as new as the index is re-read from disk. A copy of the index with a newer mtime would
        # trust the entry's size and mtime and stage the old content. checkStat=minimal leaves only size and mtime,
        # as when the edit happens in the same second (same ctime) on a real machine.
        p = self.p
        p.git("config", "core.checkStat", "minimal")
        f = p.work / "docs" / "racy.md"
        f.write_text("bbbb\n")
        p.git("add", "docs/racy.md")
        st = f.stat()
        f.write_text("cccc\n")  # same size
        os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns))
        index = p.work / ".git" / "index"
        os.utime(index, ns=(st.st_atime_ns, st.st_mtime_ns))  # the index written in that same instant
        time.sleep(1.1)  # the temp copy, if it got a new mtime, would be clearly newer than the entry
        code, out = self.helper("worktree-tree")
        self.assertEqual(code, 0, out)
        blob = p.git("rev-parse", f"{out.strip()}:docs/racy.md").stdout.strip()
        self.assertEqual(p.git("cat-file", "-p", blob).stdout, "cccc\n")

    def test_worktree_tree_refuses_entries_git_does_not_compare_with_the_disk(self):
        p = self.p
        for flag, unflag in (("--assume-unchanged", "--no-assume-unchanged"), ("--skip-worktree", "--no-skip-worktree")):
            p.git("update-index", flag, "docs/notes.md")
            p.write("docs/notes.md", "edited but hidden from git add\n")
            code, out = self.helper("worktree-tree")
            self.assertEqual(code, 1, out)
            self.assertIn("'docs/notes.md' is assume-unchanged or skip-worktree", out)
            self.assertTrue(out.rstrip().endswith("git update-index --no-assume-unchanged --no-skip-worktree -- 'docs/notes.md'"), out)
            self.assertNotRegex(out, r"(?m)^[0-9a-f]{40}$")
            p.git("update-index", unflag, "docs/notes.md")
            p.git("checkout", "--", "docs/notes.md")
        self.assertEqual(self.helper("worktree-tree")[0], 0)

    def test_worktree_tree_refuses_a_submodule_with_changes_inside(self):
        p = self.p
        sub = p.work / "lib"
        p.git("init", "-q", str(sub))
        (sub / "a.txt").write_text("one\n")
        p.git("add", "a.txt", cwd=sub); p.git("commit", "-q", "-m", "sub", cwd=sub)
        p.git("add", "lib"); p.git("commit", "-q", "--no-verify", "-m", "gitlink")
        self.assertEqual(self.helper("worktree-tree")[0], 0)
        (sub / "a.txt").write_text("two\n")
        code, out = self.helper("worktree-tree")
        self.assertEqual(code, 1, out)
        self.assertIn("submodule 'lib' has new commits or changes inside", out)
        self.assertTrue(out.rstrip().endswith("git -C 'lib' status"), out)

    def test_worktree_tree_failure_names_the_command_that_reproduces_it(self):
        self.p.git("config", "core.hooksPath", ".githooks")
        broken = self.tmp / "broken"
        (broken / "scripts").mkdir(parents=True)
        shutil.copy2(ROOT / "scripts" / "check-verde.sh", broken / "scripts" / "check-verde.sh")
        self.p.git("init", "-q", cwd=broken)
        (broken / ".git" / "index").write_bytes(b"not an index")
        code, out = self.helper("worktree-tree", cwd=broken, helper=str(broken / "scripts" / "check-verde.sh"))
        self.assertNotEqual(code, 0, out)
        self.assertIn("git add -A --dry-run", out)

    def test_has_misses_without_a_cache_file_and_with_garbage(self):
        k = self.key()
        self.assertEqual(self.helper("has", k)[0], 1)
        self.cache.write_bytes(b"\xff\xfe garbage\n\n1 2 3\nabc " + k.encode() + b"\n-5 " + k.encode() + b"\n")
        code, out = self.helper("has", k)
        self.assertEqual((code, out), (1, ""))

    def test_has_misses_for_a_cache_path_that_is_a_directory_or_a_bad_key(self):
        k = self.key()
        self.cache.mkdir()
        self.assertEqual(self.helper("has", k), (1, ""))
        self.cache.rmdir()
        self.cache.write_text(f"{int(time.time())} {k}\n")
        self.assertEqual(self.helper("has", "short")[0], 1)
        self.assertEqual(self.helper("has", k.upper())[0], 1)

    def test_has_prints_the_age_in_minutes_and_the_newest_line_wins(self):
        k = self.key()
        now = int(time.time())
        self.cache.write_text(f"{now - 7200} {k}\n{now - 600 - 5} {k}\n{now - 60} {self.key(wrapper='x')}\n")
        code, out = self.helper("has", k)
        self.assertEqual((code, out.strip()), (0, "10"))

    def test_has_misses_for_an_entry_from_the_future_and_with_the_cache_off(self):
        k = self.key()
        self.cache.write_text(f"{int(time.time()) + 3600} {k}\n")
        self.assertEqual(self.helper("has", k)[0], 1)
        self.cache.write_text(f"{int(time.time())} {k}\n")
        self.assertEqual(self.helper("has", k)[0], 0)
        self.assertEqual(self.helper("has", k, env={"GW_CHECK_CACHE": "0"})[0], 1)

    def test_add_records_the_epoch_and_the_key_and_keeps_the_last_50_lines(self):
        keys = [self.key(tree=f"{i:040x}") for i in range(55)]
        for k in keys:
            self.assertEqual(self.helper("add", k)[0], 0)
        lines = self.cache.read_text().splitlines()
        self.assertEqual([ln.split()[1] for ln in lines], keys[-50:])
        self.assertRegex(lines[-1], r"^\d{10,} [0-9a-f]{40}$")
        self.assertEqual([e for e in os.listdir(self.cache.parent) if e.startswith("gw-check-verde.")], [], "temp left behind")

    def test_add_again_replaces_the_older_line_of_the_same_key(self):
        k = self.key()
        self.cache.write_text(f"1000000000 {k}\n")
        self.assertEqual(self.helper("add", k)[0], 0)
        self.assertEqual(len(self.cache.read_text().splitlines()), 1)
        self.assertEqual(self.helper("has", k)[0], 0)

    def test_add_never_fails_when_it_cannot_write_it_warns(self):
        k = self.key()
        self.cache.mkdir()
        code, out = self.helper("add", k)
        self.assertEqual(code, 0, out)
        self.assertIn("is a directory, check not recorded", out)
        self.assertIn("rm -r", out)

    def test_add_interrupted_leaves_no_temp_file(self):
        k = self.key()
        self.cache.write_text(f"{int(time.time())} {self.key(wrapper='old')}\n")
        bin_dir = self.tmp / "slow-bin"
        bin_dir.mkdir()
        started = self.tmp / "awk-started"
        real_awk = shutil.which("awk")
        (bin_dir / "awk").write_text(f'#!/bin/sh\ntouch "{started}"\nsleep 2\nexec "{real_awk}" "$@"\n')
        (bin_dir / "awk").chmod(0o755)
        env = dict(self.p.env, GW_CHECK_CACHE="", PATH=f"{bin_dir}:{os.environ['PATH']}")
        proc = subprocess.Popen(["bash", self.HELPER, "add", k], cwd=self.p.work, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for _ in range(100):
            if started.exists():
                break
            time.sleep(0.05)
        self.assertTrue(started.exists(), "add never reached awk")
        self.assertEqual(len([e for e in os.listdir(self.cache.parent) if e.startswith("gw-check-verde.")]), 1,
                         "the temp file exists while add runs")
        proc.send_signal(signal.SIGTERM)
        proc.communicate(timeout=30)
        self.assertEqual(proc.returncode, 143)
        self.assertEqual([e for e in os.listdir(self.cache.parent) if e.startswith("gw-check-verde.")], [], "temp left behind")

    def test_every_warning_of_add_ends_with_the_command_that_fixes_it(self):
        text = (ROOT / "scripts" / "check-verde.sh").read_text()
        warnings = re.findall(r'echo "(check-verde: warning: [^"]*)"', text)
        self.assertGreaterEqual(len(warnings), 5)
        for w in warnings:
            self.assertRegex(w, r"; [^;]*: \S.*$", w)

    def test_add_with_a_bad_key_and_unknown_subcommands_say_how_to_call_it(self):
        code, out = self.helper("add", "nope")
        self.assertEqual(code, 2, out)
        self.assertIn("'nope' is not a git object name", out)
        self.assertIn("usage: bash", out)
        code, out = self.helper("frobnicate")
        self.assertEqual(code, 2, out)
        self.assertIn("unknown subcommand 'frobnicate'", out)

    def test_a_linked_worktree_shares_the_cache(self):
        p = self.p
        k = self.key()
        self.assertEqual(self.helper("add", k)[0], 0)
        linked = self.tmp / "linked tree"
        p.git("worktree", "add", "-q", "--detach", str(linked))
        code, out = self.helper("has", k, cwd=linked, helper=str(linked / self.HELPER))
        self.assertEqual((code, out.strip()), (0, "0"), out)
        self.assertEqual(self.helper("add", self.key(wrapper="y"), cwd=linked, helper=str(linked / self.HELPER))[0], 0)
        self.assertEqual(len(self.cache.read_text().splitlines()), 2)

    def test_the_root_comes_from_the_script_path_not_the_current_directory_nor_git_dir(self):
        k = self.key()
        self.assertEqual(self.helper("add", k, cwd=self.tmp, helper=str(self.p.work / self.HELPER),
                                     env={"GIT_DIR": str(self.tmp / "nowhere")})[0], 0)
        self.assertEqual(len(self.cache.read_text().splitlines()), 1)


class Revisado(Base):
    def setUp(self):
        super().setUp()
        p = self.p
        p.git("checkout", "-q", "-b", "feature")
        p.write("src/a.py", "a = 1\n"); p.commit("code")
        self.assertEqual(p.push("-u", "origin", "feature")[0], 0)
        self.script = str(p.work / ".claude" / "gw" / "scripts" / "revisado.sh")

    def test_tracked_edit_refused_untracked_draft_ignored(self):
        p = self.p
        p.write("src/a.py", "a = 2\n")  # an edit to a tracked file
        code, out = p.run("bash", self.script)
        self.assertNotEqual(code, 0, out)
        self.assertIn("uncommitted changes to tracked files", out)
        self.assertIn("git add -u && git commit && git push", out)
        p.git("checkout", "--", "src/a.py")
        p.write("draft.txt", "not mine to commit\n")  # a draft that git does not track
        code, out = p.run("bash", self.script)
        self.assertEqual(code, 0, out)
        self.assertEqual(p.git("status", "--porcelain").stdout.strip(), "?? draft.txt")  # left where it was

    def test_footer_becomes_the_last_line_of_the_mark_commit(self):
        p = self.p
        code, out = p.run("bash", self.script, "--footer", "Siguiente: push and open the PR")
        self.assertEqual(code, 0, out)
        body = p.git("log", "-1", "--format=%B").stdout.rstrip("\n").splitlines()
        self.assertEqual((body[0], body[-1]), (f"Reviewed: {p.git('rev-parse', 'HEAD~1').stdout.strip()}", "Siguiente: push and open the PR"))

    def test_bad_arguments_refused_with_the_usage(self):
        for args, text in ((["--footer"], "--footer needs a line"), ([ "--footer", ""], "--footer needs a line"),
                           (["--nope"], "unknown argument '--nope'")):
            code, out = self.p.run("bash", self.script, *args)
            self.assertEqual(code, 1, out)
            self.assertIn(text, out)

    def test_not_pushed_refused(self):
        p = self.p
        p.write("src/a.py", "a = 2\n"); p.commit("unpushed")
        code, out = p.run("bash", self.script)
        self.assertNotEqual(code, 0, out)
        self.assertIn("git push -u origin feature", out)

    def test_writes_and_commits_the_mark_then_main_accepts_it(self):
        p = self.p
        head = p.sha()
        code, out = p.run("bash", self.script, cwd=self.tmp)  # not from the repo: the root comes from its path
        self.assertEqual(code, 0, out)
        self.assertEqual((p.work / "docs" / "revisado.txt").read_text().strip(), head)
        self.assertEqual(p.git("log", "-1", "--format=%s").stdout.strip(), f"Reviewed: {head}")
        p.write("docs/notes.md", "after review\n"); p.commit("content after review")
        code, out = p.push("origin", "HEAD:refs/heads/main")
        self.assertEqual(code, 0, out)


class RevisadoSpanishWithRetro(Base):
    config = {"language": "es", "requireRetro": True}

    def setUp(self):
        super().setUp()
        self.p.git("checkout", "-q", "-b", "feature")
        self.script = str(self.p.work / ".claude" / "gw" / "scripts" / "revisado.sh")

    def retro(self, status):
        p = self.p
        p.write("docs/registros/retro-2026-10-21.md", f"# Retro\n\n**Estado:** {status}\n")
        p.commit(f"retro {status}")
        self.assertEqual(p.push("-u", "origin", "feature")[0], 0)
        return p.run("bash", self.script)

    def test_pending_retro_refused(self):
        code, out = self.retro("pendiente")
        self.assertNotEqual(code, 0, out)
        self.assertIn("retro", out)

    def test_done_alone_refused(self):
        code, out = self.retro("hecha")
        self.assertNotEqual(code, 0, out)

    def test_undecided_refused(self):
        code, out = self.retro("undecided")
        self.assertNotEqual(code, 0, out)

    def test_pending_with_a_decision_word_refused(self):
        code, out = self.retro("pendiente; la propuesta 2 aún no aplicada")
        self.assertNotEqual(code, 0, out)

    def test_english_decisions_accepted(self):
        code, out = self.retro("Rejected: x; applied: y")
        self.assertEqual(code, 0, out)

    def test_approved_accepted_in_both_languages(self):
        for status in ("aprobada (P1, P2)", "Aprobadas todas", "approved with changes"):
            code, out = self.retro(status)
            self.assertEqual(code, 0, f"{status}: {out}")
            self.p.git("reset", "-q", "--hard", "HEAD~1")  # undo the mark commit, keep the retro pushed

    def test_whole_status_paragraph_is_read_not_only_its_first_line(self):
        p = self.p
        p.write("docs/registros/retro-2026-10-22.md",
                "# Retro\n\n**Estado:** revisada con la persona el 2026-10-22;\nla propuesta 1 aprobada y la 2 rechazada.\n\nOtro texto pendiente.\n")
        p.commit("multi-line status")
        self.assertEqual(p.push("-u", "origin", "feature")[0], 0)
        code, out = p.run("bash", self.script)
        self.assertEqual(code, 0, out)

    def test_pending_on_a_later_line_of_the_paragraph_refused(self):
        p = self.p
        p.write("docs/registros/retro-2026-10-22.md", "# Retro\n\n**Estado:** aprobada la 1;\nla 2 pendiente de la persona.\n")
        p.commit("pending on line 2")
        self.assertEqual(p.push("-u", "origin", "feature")[0], 0)
        code, out = p.run("bash", self.script)
        self.assertNotEqual(code, 0, out)

    def test_pending_words_veto_only_as_whole_words(self):
        for status in ("aprobada; spending cut by 20 %", "aplicada, dependiente de la CI", "approved; unpending"):
            code, out = self.retro(status)
            self.assertEqual(code, 0, f"{status}: {out}")
            self.p.git("reset", "-q", "--hard", "HEAD~1")  # undo the mark commit, keep the retro pushed
        for status in ("aprobada, pending P2", "aprobada; quedan 2 pendientes", "approved (Pending: P3)",
                       "aplicada la 1, la 2 aún no", "approved, not yet P2"):
            code, out = self.retro(status)
            self.assertNotEqual(code, 0, f"{status}: {out}")
            self.assertIn("paragraph records", out)
            self.assertIn("as whole words", out)

    def test_refusal_lists_the_valid_words(self):
        code, out = self.retro("hecha")
        self.assertNotEqual(code, 0, out)
        for word in ("aplicad*", "rechazad*", "aplazad*", "decidid*", "aprobad*", "pendiente/pending"):
            self.assertIn(word, out)
        self.assertIn("bash ", out)

    def test_no_estado_line_at_all_refused(self):
        p = self.p
        p.write("docs/registros/retro-2026-10-22.md", "# Retro\n\nSin línea de estado, aplicada.\n")
        p.commit("no status line")
        self.assertEqual(p.push("-u", "origin", "feature")[0], 0)
        code, out = p.run("bash", self.script)
        self.assertNotEqual(code, 0, out)
        self.assertIn("**Estado:**/**Status:** paragraph", out)

    def test_applied_retro_accepted_and_spanish_subject(self):
        code, out = self.retro("aplicada (propuestas 1 y 2), la 3 rechazada")
        self.assertEqual(code, 0, out)
        self.assertTrue(self.p.git("log", "-1", "--format=%s").stdout.startswith("Revisado: "))


class EsCodigo(Base):
    def test_lists_only_code_and_never_the_mark(self):
        p = self.p
        p.write("src/a.py", "a\n"); p.write("docs/x.md", "x\n"); p.write("README.md", "r\n")
        p.write("docs/revisado.txt", "abc\n"); p.commit("mixed")
        script = str(p.work / ".claude" / "gw" / "scripts" / "es-codigo.sh")
        code, out = p.run("bash", script, p.base, "HEAD", cwd=self.tmp)
        self.assertEqual((code, out.split()), (0, ["src/a.py"]))
        code, out = p.run("bash", script, "", "HEAD")
        self.assertIn("check.sh", out.split())

    def test_explicar_says_code_or_content_and_why(self):
        p = self.p
        script = str(p.work / ".claude" / "gw" / "scripts" / "es-codigo.sh")
        code, out = p.run("bash", script, "--explicar", "src/a.py", "docs/x.md", ".githooks/pre-push",
                          "docs/revisado.txt")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines(), [
            "src/a.py: code (matches no content regex)",
            'docs/x.md: content (matches content regex "^docs/")',
            ".githooks/pre-push: code (the workflow policy and guards are always code)",
            "docs/revisado.txt: content (it is the review mark file, reviewMark)"])
        code, out = p.run("bash", script, "--explicar")
        self.assertEqual(code, 2, out)
        self.assertIn("usage", out)

    def test_invalid_content_regex_is_named_and_other_failures_are_not_blamed_on_it(self):
        p = self.p
        script = str(p.work / ".claude" / "gw" / "scripts" / "es-codigo.sh")
        p.write("src/a.py", "a\n"); p.commit("code")
        good = (p.work / ".claude" / "gw.json").read_text()
        cfg = json.loads(good)
        cfg["content"] = ["^docs/", "(unclosed"]
        p.write(".claude/gw.json", json.dumps(cfg)); p.git("commit", "-q", "-am", "bad regex", "--no-verify")
        for args in ((p.base, "HEAD"), ("--explicar", "src/a.py")):
            code, out = p.run("bash", script, *args)
            self.assertEqual(code, 2, out)
            self.assertIn('content regex "(unclosed" is invalid', out)
            self.assertIn("fix the regex in .claude/gw.json", out)
        # The same classifier failing for another reason (no python3 to run it) is not called a bad regex.
        p.write(".claude/gw.json", good); p.git("commit", "-q", "-am", "good again", "--no-verify")
        tools = self.tmp / "tools"
        tools.mkdir()
        real = shutil.which("python3")
        (tools / "python3").write_text(
            f'#!/bin/sh\ncase "$*" in *config.py*) exec {real} "$@" ;; *) echo "boom" >&2; exit 1 ;; esac\n')
        (tools / "python3").chmod(0o755)
        code, out = p.run("bash", script, p.base, "HEAD", env={"PATH": f"{tools}:{p.env['PATH']}"})
        self.assertEqual(code, 2, out)
        self.assertIn("classification failed (exit 1), not because of a content regex", out)
        self.assertNotIn("invalid", out)

    def test_reader_closing_the_pipe_early_is_not_an_error(self):
        p = self.p
        script = str(p.work / ".claude" / "gw" / "scripts" / "es-codigo.sh")
        for i in range(3000):  # ~300 KB of paths: more than a pipe buffer, so the writer is still writing
            p.write(f"src/{'d' * 90}/f{i}.py", "x\n")
        p.commit("many files")
        code, out = p.run("bash", "-c", f'bash "{script}" {p.base} HEAD | head -1; exit "${{PIPESTATUS[0]}}"')
        self.assertEqual(code, 0, out)
        self.assertEqual(len(out.splitlines()), 1, out)
        self.assertNotIn("invalid", out)
        self.assertNotIn("Traceback", out)

    def test_workflow_guards_are_code_whatever_content_says(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["content"] = [".*"]
        p.write(".claude/gw.json", json.dumps(cfg))
        p.write(".githooks/pre-push", "exit 0\n"); p.write(".claude/settings.json", "{}\n")
        p.write(".claude/gw/scripts/extra.sh", "true\n"); p.write("src/a.py", "a\n")
        p.commit("guards", env=None)
        script = str(p.work / ".claude" / "gw" / "scripts" / "es-codigo.sh")
        code, out = p.run("bash", script, p.base, "HEAD")
        self.assertEqual((code, sorted(out.split())), (0, [".claude/gw.json", ".claude/gw/scripts/extra.sh",
                                                          ".claude/settings.json", ".githooks/pre-push"]))

    def test_missing_commit_or_config_exits_2(self):
        p = self.p
        script = str(p.work / ".claude" / "gw" / "scripts" / "es-codigo.sh")
        self.assertEqual(p.run("bash", script, "1" * 40, "HEAD")[0], 2)
        p.git("rm", "-q", ".claude/gw.json"); p.git("commit", "-q", "--no-verify", "-m", "drop config")
        code, out = p.run("bash", script, p.base, "HEAD")
        self.assertEqual(code, 2, out)
        self.assertEqual(p.run("bash", script, "--rev", p.base, p.base, "HEAD")[0], 0)

    def test_config_comes_from_the_commit_not_the_working_tree(self):
        p = self.p
        p.write("src/a.py", "a\n"); p.commit("code")
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["content"] = cfg["content"] + ["^src/"]
        p.write(".claude/gw.json", json.dumps(cfg))  # uncommitted
        script = str(p.work / ".claude" / "gw" / "scripts" / "es-codigo.sh")
        code, out = p.run("bash", script, p.base, "HEAD")
        self.assertEqual((code, out.split()), (0, ["src/a.py"]))


class PreCommit(Base):
    config = {"protectedPaths": ["drafts/"]}

    def test_secret_in_staged_file_refused(self):
        self.p.write("src/settings.py", f'GITHUB = "{FAKE_TOKEN}"\n')
        r = self.p.commit("leak", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("shaped like a key", r.stderr)

    def test_word_ending_in_key_prefix_passes(self):
        p = self.p
        p.write("docs/fuentes.md", "- https://ppc.land/x-drops-link-penalty-musk-tells-zuckerberg-on-platform/\n")
        p.commit("url")
        p.write("src/llm.py", "KEY=" + "sk-" + "ant-" + "A1b2C3d4" * 3 + "\n")
        r = p.commit("leak", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("shaped like a key", r.stderr)
        self.assertIn("  sk-ant-A", r.stderr)

    def test_literal_assignment_refused_env_reference_allowed(self):
        p = self.p
        p.write("src/db.py", "db_pass" + 'word = "hunter2-real"\n')
        r = p.commit("literal", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("literal secret", r.stderr)
        p.write("src/db.py", "db_" + 'password = os.environ["DB_PASSWORD"]\n')
        p.write("config/app.yml", "api_" + "key: ${API_KEY}\n")
        self.assertEqual(p.commit("from env", ok=False).returncode, 0)

    def test_env_file_refused_example_allowed(self):
        p = self.p
        p.write(".env.example", "API_" + "KEY=your-key-here\n")
        self.assertEqual(p.commit("example", ok=False).returncode, 0)
        p.write(".env", "API_" + "KEY=" + "x" * 20 + "\n")
        r = p.commit("real env", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(".env", r.stderr)

    def test_protected_paths_only_under_claude_code(self):
        p = self.p
        p.write("drafts/idea.md", "draft\n")
        r = p.commit("agent commit", env={"CLAUDECODE": "1"}, ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("git restore --staged", r.stderr)
        self.assertEqual(p.commit("person commit", ok=False).returncode, 0)

    def test_actions_permissions_and_short_values_are_not_secrets(self):
        p = self.p
        p.write(".github/workflows/ci.yml", "permissions:\n  id-token: write\n  contents: read\n"
                "jobs:\n  x:\n    with:\n      token: false\n      github-token: none\n      api_key: abc123\n")
        r = p.commit("workflow", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        p.write("config/app.yml", "api_" + "key: abcdefgh12345\n")
        r = p.commit("real", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("literal secret", r.stderr)

    def test_this_test_file_passes_the_scan(self):
        shutil.copy2(Path(__file__), self.p.work / "test_ganchos.py")
        r = self.p.commit("tests", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_commit_inside_a_linked_worktree_finds_its_root(self):
        """Git exports GIT_DIR (and GIT_INDEX_FILE) to the hook there: the root must still come from the hook's path,
        or the CLAUDECODE=1 check cannot find .claude/gw/scripts and every commit fails."""
        p = self.p
        linked = self.tmp / "linked"
        p.git("worktree", "add", "-q", "-b", "side", str(linked))
        env = {"CLAUDECODE": "1"}
        (linked / "src").mkdir()
        (linked / "src" / "side.py").write_text("s = 1\n")
        p.git("add", "-A", cwd=linked)
        r = p.git("commit", "-q", "-m", "on side", cwd=linked, env=env, ok=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("cannot read protectedPaths", r.stdout + r.stderr)
        # The checks still run against the linked worktree's own index.
        (linked / "drafts").mkdir()
        (linked / "drafts" / "wip.md").write_text("wip\n")
        (linked / "src" / "leak.py").write_text(f'GITHUB = "{FAKE_TOKEN}"\n')
        p.git("add", "-A", cwd=linked)
        r = p.git("commit", "-q", "-m", "leak", cwd=linked, env=env, ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("shaped like a key", r.stderr)
        p.git("reset", "-q", "src/leak.py", cwd=linked)
        r = p.git("commit", "-q", "-m", "draft", cwd=linked, env=env, ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("under protectedPaths", r.stderr)

    def test_range_mode_for_ci(self):
        p = self.p
        hook = str(p.work / ".githooks" / "pre-commit")
        p.write("src/ok.py", "ok = 1\n"); p.commit("clean")
        self.assertEqual(p.run("bash", hook, "--rango", f"{p.base}..HEAD")[0], 0)
        p.write("src/leak.py", f'T = "{FAKE_TOKEN}"\n')
        p.git("add", "-A"); p.git("commit", "-q", "--no-verify", "-m", "leak")
        code, out = p.run("bash", hook, "--rango", f"{p.base}..HEAD")
        self.assertNotEqual(code, 0, out)
        self.assertIn("rotate the credential", out)


class CommitMsg(Base):
    """templates/githooks/commit-msg: bitacora.py check on the staged log, at commit time."""
    config = {"logRows": True}
    hooks = ("pre-push", "pre-commit", "commit-msg")

    def log_text(self, updated=None):
        today = updated or time.strftime("%Y-%m-%d")
        return (f"# Log\n\n## Current state\n\n| **Updated** | {today} |\n| **Phase · `main`** | working |\n")

    def test_passes_when_the_log_is_not_staged(self):
        self.p.write("docs/notes.md", "other\n")
        self.assertEqual(self.p.commit("notes", ok=False).returncode, 0)

    def test_stale_updated_date_refused_naming_the_fix(self):
        self.p.write("docs/log.md", self.log_text("2000-01-01"))
        r = self.p.commit("log", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Updated", r.stderr)
        self.assertIn("commit-msg:", r.stderr)
        self.assertIn("git add docs/log.md", r.stderr)

    def test_size_and_done_warnings_are_shown_but_do_not_stop_the_commit(self):
        text = self.log_text().replace("| **Updated**", "| **Notes** | " + "n" * 801 + " |\n| **Updated**")
        text += "\n## Done (last 5)\n\n" + "".join(f"{i}. 2026-10-2{i} — x\n" for i in range(1, 7))
        self.p.write("docs/log.md", text)
        r = self.p.commit("log", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("WARNING: bitacora: a cell of the state table (\"Notes\") has 801 characters (limit 800)", r.stderr)
        self.assertIn("WARNING: bitacora: the Done section has 6 items (limit 5)", r.stderr)

    def test_valid_log_passes(self):
        self.p.write("docs/log.md", self.log_text())
        self.assertEqual(self.p.commit("log", ok=False).returncode, 0)

    def test_a_log_configured_with_a_dot_slash_prefix_is_still_checked(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["log"] = "./docs/log.md"
        p.write(".claude/gw.json", json.dumps(cfg))
        p.git("add", ".claude/gw.json")
        p.write("docs/log.md", self.log_text("2000-01-01"))
        r = p.commit("log", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Updated", r.stderr)
        self.assertIn("git add docs/log.md", r.stderr)

    def test_a_log_configured_with_a_double_slash_is_still_checked(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["log"] = "docs//log.md"
        p.write(".claude/gw.json", json.dumps(cfg))
        p.git("add", ".claude/gw.json")
        p.write("docs/log.md", self.log_text("2000-01-01"))
        r = p.commit("log", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Updated", r.stderr)

    def set_log(self, rel):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["log"] = rel
        p.write(".claude/gw.json", json.dumps(cfg))
        p.git("add", ".claude/gw.json")

    def test_a_log_with_non_ascii_characters_in_its_path_is_still_checked(self):
        # git quotes such paths in `diff --name-only` ("docs/bit\303\241cora.md") unless core.quotepath is off
        p = self.p
        self.set_log("docs/bitácora.md")
        p.write("docs/bitácora.md", self.log_text("2000-01-01"))
        r = p.commit("log", ok=False)
        self.assertNotEqual(r.returncode, 0, "the hook skipped a log whose path has an accent")
        self.assertIn("Updated", r.stderr)
        self.assertIn("git add docs/bitácora.md", r.stderr)

    def test_a_valid_log_with_non_ascii_characters_in_its_path_passes(self):
        p = self.p
        self.set_log("docs/bitácora.md")
        p.write("docs/bitácora.md", self.log_text())
        self.assertEqual(p.commit("log", ok=False).returncode, 0)

    def test_a_python_that_cannot_normalise_names_the_log_path_in_the_message(self):
        p = self.p
        self.set_log("./docs/log.md")
        fake = self.tmp / "fakebin"
        fake.mkdir()
        (fake / "python3").write_text(f'#!/bin/sh\ncase "$*" in *posixpath*) exit 1;; esac\nexec {sys.executable} "$@"\n')
        os.chmod(fake / "python3", 0o755)
        p.write("docs/log.md", self.log_text())
        r = p.commit("log", env={"PATH": f"{fake}{os.pathsep}{os.environ['PATH']}"}, ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("cannot normalise the log path './docs/log.md'", r.stderr)
        self.assertIn("python3 --version", r.stderr)

    def test_checks_the_staged_version_not_the_working_tree(self):
        p = self.p
        p.write("docs/log.md", self.log_text("2000-01-01"))
        p.git("add", "docs/log.md")
        p.write("docs/log.md", self.log_text())  # fixed in the working tree only
        r = p.git("commit", "-q", "-m", "log", ok=False)
        self.assertNotEqual(r.returncode, 0)

    def test_deleting_the_log_is_not_checked(self):
        p = self.p
        p.write("docs/log.md", self.log_text())
        p.commit("log")
        os.remove(p.work / "docs" / "log.md")
        self.assertEqual(p.commit("drop", ok=False).returncode, 0)

    def test_skipped_while_finishing_a_merge(self):
        p = self.p
        (p.work / ".git" / "MERGE_HEAD").write_text(p.sha() + "\n")
        p.write("docs/log.md", self.log_text("2000-01-01"))
        self.assertEqual(p.commit("merge", ok=False).returncode, 0)

    def test_skipped_during_a_rebase(self):
        p = self.p
        (p.work / ".git" / "rebase-merge").mkdir()
        p.write("docs/log.md", self.log_text("2000-01-01"))
        self.assertEqual(p.commit("pick", ok=False).returncode, 0)

    def test_config_without_a_log_key_is_invalid_and_fails_closed(self):  # `log` is required by the schema
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        del cfg["log"]
        p.write(".claude/gw.json", json.dumps(cfg))
        p.write("docs/log.md", self.log_text("2000-01-01"))
        r = p.commit("no log key", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("gw.json", r.stderr)

    def test_fails_closed_without_config_py(self):
        p = self.p
        os.remove(p.work / ".claude" / "gw" / "scripts" / "config.py")
        p.write("docs/notes.md", "x\n")
        r = p.commit("no config.py", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("/gw-update", r.stderr)

    def test_fails_closed_without_bitacora_py_when_the_log_is_staged(self):
        p = self.p
        os.remove(p.work / ".claude" / "gw" / "scripts" / "bitacora.py")
        p.write("docs/log.md", self.log_text())
        r = p.commit("no bitacora", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("/gw-update", r.stderr)


class CommitMsgSignatures(Base):
    """templates/githooks/commit-msg with agentSignatures: false rejects an agent's signature in the message."""
    config = {"agentSignatures": False}
    hooks = ("pre-push", "pre-commit", "commit-msg")
    CLAUDE_TRAILER = "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"

    def set_signatures(self, value):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        if value is None:
            cfg.pop("agentSignatures", None)
        else:
            cfg["agentSignatures"] = value
        p.write(".claude/gw.json", json.dumps(cfg))
        p.git("add", ".claude/gw.json")
        p.commit("config")

    def refused(self, message, culprit):
        p = self.p
        before = p.sha()
        p.write("docs/notes.md", f"{message}\n")
        r = p.commit(message, ok=False)
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("commit-msg:", r.stderr)
        self.assertIn("agent signature", r.stderr)
        self.assertIn(culprit, r.stderr)
        self.assertIn("agentSignatures: false", r.stderr)
        self.assertEqual(p.sha(), before, "the refused commit was created")

    def editor(self, text):
        """An editor that puts `text` above whatever git prepared (so -v keeps its diff below the scissors)."""
        script = self.tmp / "editor.sh"
        script.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$GW_TEST_MESSAGE\" | cat - \"$1\" > \"$1.new\" && mv \"$1.new\" \"$1\"\n")
        os.chmod(script, 0o755)
        return {"GIT_EDITOR": str(script), "GW_TEST_MESSAGE": text}

    def test_a_claude_signature_passes_when_the_key_is_absent(self):
        p = self.p
        self.set_signatures(None)
        p.write("docs/notes.md", "n1\n")
        r = p.commit(f"work\n\n{self.CLAUDE_TRAILER}", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_claude_signature_passes_when_the_key_is_true(self):
        p = self.p
        self.set_signatures(True)
        p.write("docs/notes.md", "n2\n")
        r = p.commit(f"work\n\n{self.CLAUDE_TRAILER}", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_claude_co_author_is_refused(self):
        self.refused(f"work\n\n{self.CLAUDE_TRAILER}", self.CLAUDE_TRAILER)

    def test_an_anthropic_co_author_is_refused_whatever_the_case(self):
        self.refused("work\n\nco-authored-by: Bot <bot@ANTHROPIC.com>", "co-authored-by: Bot <bot@ANTHROPIC.com>")

    def test_a_claude_session_trailer_is_refused(self):
        self.refused("work\n\nClaude-Session: abc123", "Claude-Session: abc123")

    def test_a_generated_with_line_is_refused(self):
        line = "\U0001f916 Generated with [Claude Code](https://claude.com/claude-code)"
        self.refused(f"work\n\n{line}", "Generated with [Claude Code]")

    def test_a_session_link_is_refused(self):
        self.refused("work\n\nhttps://claude.ai/code/session_01ABC", "https://claude.ai/code/session_01ABC")

    def test_a_human_co_author_passes(self):
        p = self.p
        p.write("docs/notes.md", "human\n")
        r = p.commit("work\n\nCo-Authored-By: Ana Perez <ana@example.com>", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_a_comment_line_with_a_signature_passes_with_the_default_cleanup(self):
        p = self.p
        p.write("docs/notes.md", "comment\n")
        p.git("add", "-A")
        r = p.git("commit", "-q", "-e", ok=False,
                  env=self.editor("work\n\n# Generated with Claude Code\n# Co-Authored-By: Claude <noreply@anthropic.com>"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("Claude", p.git("log", "-1", "--format=%B").stdout)

    def test_a_signature_above_the_comment_lines_is_still_refused(self):
        p = self.p
        before = p.sha()
        p.write("docs/notes.md", "mixed\n")
        p.git("add", "-A")
        r = p.git("commit", "-q", "-e", ok=False, env=self.editor("work\n\nClaude-Session: x\n# a comment"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("agent signature", r.stderr)
        self.assertEqual(p.sha(), before)

    def test_a_verbose_diff_below_the_scissors_is_not_scanned(self):
        p = self.p
        p.write("docs/notes.md", "verbose\n")
        p.write("docs/session.md", "see https://claude.ai/code/session_01ABC and Claude-Session: x\n")
        p.git("add", "-A")
        r = p.git("commit", "-q", "-v", ok=False, env=self.editor("document the session"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(p.git("log", "-1", "--format=%s").stdout.strip(), "document the session")

    def test_a_merge_message_with_a_signature_is_refused(self):
        p = self.p
        p.git("checkout", "-q", "-b", "side")
        p.write("docs/side.md", "side\n"); p.commit("side")
        p.git("checkout", "-q", "main")
        p.write("docs/main.md", "main\n"); p.commit("main")
        before = p.sha()
        r = p.git("merge", "--no-ff", "-m", f"Merge side\n\n{self.CLAUDE_TRAILER}", "side", ok=False)
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("agent signature", r.stderr)
        self.assertIn(self.CLAUDE_TRAILER, r.stderr)
        self.assertEqual(p.sha(), before)

    def test_a_clean_merge_message_passes(self):
        p = self.p
        p.git("checkout", "-q", "-b", "side")
        p.write("docs/side.md", "side\n"); p.commit("side")
        p.git("checkout", "-q", "main")
        p.write("docs/main.md", "main\n"); p.commit("main")
        r = p.git("merge", "--no-ff", "-m", "Merge side", "side", ok=False)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_skipped_during_a_rebase(self):
        p = self.p
        (p.work / ".git" / "rebase-merge").mkdir()
        p.write("docs/notes.md", "pick\n")
        r = p.commit(f"pick\n\n{self.CLAUDE_TRAILER}", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
