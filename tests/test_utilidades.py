"""The workflow's utility scripts, end to end, in temporary projects: bitacora.py, prepush-ramas.sh, fusionar.sh,
rojo-sin-arreglo.sh, tests-relacionados.sh and enlaces-md.py.

Same conventions as test_ganchos.py (it provides the temporary project): git runs isolated from this machine's
configuration and every commit that matters has a fixed date, so the suite does not depend on today's date.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_ganchos import BASE_CONFIG, Project, ROOT, VERSION, ZERO

sys.dont_write_bytecode = True
SCRIPTS = ("bitacora.py", "prepush-ramas.sh", "fusionar.sh", "rojo-sin-arreglo.sh", "tests-relacionados.sh",
           "enlaces-md.py")
DAY = {"GIT_AUTHOR_DATE": "2026-10-21T12:00:00+0000", "GIT_COMMITTER_DATE": "2026-10-21T12:00:00+0000"}
LOG = "docs/log.md"


def log_text(a="doing A", b="doing B", updated="2026-10-21"):
    return f"""# Log

## Current state

| Field | Value |
|---|---|
| **Updated** | {updated} |
| **Tests** | green |
| **Branches** | `feat-a`, `feat-b` |
| **Task in progress · `feat-a`** | {a} |
| **Task in progress · `feat-b`** | {b} |

## Done

1. nothing yet
"""


class Utilidades(Project):
    """The base project plus the utility scripts (committed and pushed) and a log with two branch rows."""

    def __init__(self, tmp, config=None, check="exit 0"):
        super().__init__(tmp, dict({"logRows": True}, **(config or {})), check)
        scripts = self.work / ".claude" / "gw" / "scripts"
        for name in SCRIPTS:
            shutil.copy2(ROOT / "scripts" / name, scripts / name)
        self.write(LOG, log_text())
        self.commit("scripts and log", env=DAY)
        self.git("push", "-q", "--no-verify", "origin", "main")
        self.base = self.sha()
        self.scripts = scripts

    def script(self, name, *args, **kw):
        interpreter = ["python3"] if name.endswith(".py") else ["bash"]
        return self.run(*interpreter, str(self.scripts / name), *args, **kw)

    def branch(self, name, start=None):
        self.git("checkout", "-q", "-b", name, start or self.base)


class Base(unittest.TestCase):
    config = None

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-utilidades-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Utilidades(self.tmp, self.config)


class BitacoraRows(Base):
    def test_check_accepts_a_well_formed_log(self):
        code, out = self.p.script("bitacora.py", "check")
        self.assertEqual(code, 0, out)

    def test_row_over_600_characters_refused(self):
        self.p.write(LOG, log_text(a="x" * 601))
        code, out = self.p.script("bitacora.py", "check")
        self.assertEqual(code, 1, out)
        self.assertIn("601 characters (limit 600)", out)
        self.p.write(LOG, log_text(a="x" * 600))
        self.assertEqual(self.p.script("bitacora.py", "check")[0], 0)

    def test_two_rows_for_one_branch_refused(self):
        self.p.write(LOG, log_text() + "\n| **Task in progress · `feat-a`** | again |\n")
        code, out = self.p.script("bitacora.py", "check")
        self.assertEqual(code, 1, out)
        self.assertIn("two rows for feat-a", out)

    def test_updated_older_than_the_commit_day_refused(self):
        self.p.write(LOG, log_text(updated="2026-10-01"))
        code, out = self.p.script("bitacora.py", "check", "--date", "2026-10-21")
        self.assertEqual(code, 1, out)
        self.assertIn("2026-10-01", out)
        self.assertEqual(self.p.script("bitacora.py", "check", "--date", "2026-10-01")[0], 0)

    def test_off_without_logrows(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        p = Utilidades(self.tmp, {"logRows": False})
        p.write(LOG, log_text(a="x" * 900))
        self.assertEqual(p.script("bitacora.py", "check")[0], 0)
        self.assertEqual(p.script("bitacora.py", "close-row", "feat-a")[0], 0)
        self.assertNotIn("Merged", (p.work / LOG).read_text())


class BitacoraOwnRow(Base):
    def commit_log(self, **kw):
        self.p.write(LOG, log_text(**kw))
        self.p.commit("edit the log", env=DAY)
        return self.p.sha()

    def test_own_row_and_free_rows_accepted(self):
        self.p.branch("feat-a")
        sha = self.commit_log(a="A moved on", updated="2026-10-22")
        self.assertEqual(self.p.script("bitacora.py", "own-row", sha, "feat-a")[0], 0)

    def test_other_branch_row_refused(self):
        self.p.branch("feat-a")
        sha = self.commit_log(b="A rewrote B")
        code, out = self.p.script("bitacora.py", "own-row", sha, "feat-a")
        self.assertEqual(code, 1, out)
        self.assertIn("Task in progress · feat-b", out)
        self.assertIn("BITACORA_COMPARTIDA=1 git push", out)

    def test_shared_row_refused_and_allowed_with_env_or_flag(self):
        self.p.branch("feat-a")
        self.p.write(LOG, log_text().replace("`feat-a`, `feat-b`", "`feat-a`, `feat-b`, `feat-c`"))
        self.p.commit("edit a shared row", env=DAY)
        sha = self.p.sha()
        code, out = self.p.script("bitacora.py", "own-row", sha, "feat-a")
        self.assertEqual(code, 1, out)
        self.assertIn("Branches", out)
        for env in ({"BITACORA_COMPARTIDA": "1"}, {"GW_SHARED_LOG": "1"}):
            self.assertEqual(self.p.script("bitacora.py", "own-row", sha, "feat-a", env=env)[0], 0, env)
        self.assertEqual(self.p.script("bitacora.py", "own-row", sha, "feat-a", "--shared")[0], 0)


class BitacoraTasks(Base):
    PLAN = "docs/plan.md"

    def plan(self, text, message="plan"):
        self.p.write(self.PLAN, text)
        self.p.commit(message, env=DAY)
        return self.p.sha()

    def test_in_progress_task_whose_entry_did_not_change_warns_but_passes(self):
        self.p.branch("feat-a")
        base = self.plan("- [ ] **INS-7** 🚧 half done, missing the form\n- [ ] **INS-8** later\n")
        self.p.write("src/x.py", "x = 1\n")
        self.p.commit("Work on INS-7 and INS-8", env=DAY)
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "in-progress", base, self.p.sha())
        self.assertEqual(code, 0, out)
        self.assertIn("warning", out)
        self.assertIn("INS-7", out)
        self.assertNotIn("INS-8", out)  # not marked 🚧
        self.plan("- [ ] **INS-7** 🚧 half done, the form is missing now\n- [ ] **INS-8** later\n", "update INS-7")
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "in-progress", base, self.p.sha())
        self.assertEqual(code, 0, out)
        self.assertNotIn("warning", out)

    def test_closed_task_must_be_in_done(self):
        self.p.branch("feat-a")
        base = self.plan("- [ ] **INS-3** the thing\n- [ ] **TASK-1** other\n")
        self.plan("- [x] **INS-3** the thing\n- [ ] **TASK-1** other\n", "close INS-3")
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, self.p.sha())
        self.assertEqual(code, 1, out)
        self.assertIn("INS-3", out)
        self.p.write(LOG, log_text().replace("1. nothing yet", "1. ~~INS-3~~ done"))
        self.p.commit("log", env=DAY)
        self.assertEqual(self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, self.p.sha())[0], 0)

    def test_closed_on_the_configured_protected_branch_needs_no_done_entry(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"protectedBranch": "trunk"})
        self.p.branch("feat-a")
        base = self.plan("- [ ] **INS-3** the thing\n")
        sha = self.plan("- [x] **INS-3** the thing\n", "close INS-3 (from trunk)")
        self.p.git("push", "-q", "--no-verify", "origin", "HEAD:trunk")
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, sha)
        self.assertEqual(code, 0, out)

    def test_struck_multiline_task_and_custom_id_regex(self):
        self.p.branch("feat-a")
        base = self.plan("- TASK-1 one\n- TASK-2 two\n")
        self.plan("- ~~TASK-1 one\n  continued~~\n- TASK-2 two\n", "close TASK-1")
        args = ("--plan", self.PLAN, "--id-regex", r"TASK-\d+", "closed", base, self.p.sha())
        code, out = self.p.script("bitacora.py", *args)
        self.assertEqual(code, 1, out)
        self.assertIn("TASK-1", out)
        self.assertNotIn("TASK-2", out)

    def test_task_id_with_capturing_groups_does_not_crash_closed_and_still_checks(self):
        self.p.branch("feat-a")
        base = self.plan("- INS-1 one\n- FLU-2 two\n- INS-3 three\n- INS-1 to INS-3 range\n")
        self.plan("- ~~INS-1 to INS-3 range~~\n- INS-1 one\n- FLU-2 two\n", "close")
        args = ("--plan", self.PLAN, "--id-regex", r"(INS|FLU)-\d+", "closed", base, self.p.sha())
        code, out = self.p.script("bitacora.py", *args)
        self.assertEqual(code, 1, out)
        self.assertNotIn("Traceback", out)
        self.assertIn("INS-1 is closed in the plan", out)
        self.assertIn("INS-3 is closed in the plan", out)
        self.assertNotIn("FLU-2", out)
        self.p.write(LOG, log_text().replace("1. nothing yet", "1. ~~INS-1 to INS-3~~ done"))
        self.p.commit("log", env=DAY)
        args = args[:-1] + (self.p.sha(),)
        self.assertEqual(self.p.script("bitacora.py", *args)[0], 0)

    def test_task_id_from_the_config_with_groups(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"taskId": r"(INS|FLU)-\d+"})
        self.p.branch("feat-a")
        base = self.plan("- FLU-9 nine\n")
        self.plan("- ~~FLU-9 nine~~\n", "close FLU-9")
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, self.p.sha())
        self.assertEqual(code, 1, out)
        self.assertIn("FLU-9 is closed in the plan", out)

    def test_backreference_in_the_id_regex_is_a_usage_error(self):
        code, out = self.p.script("bitacora.py", "--id-regex", r"(a)\1", "closed", "HEAD", "HEAD")
        self.assertEqual(code, 2, out)
        self.assertIn("back-reference", out)

    def test_only_struck_or_dated_lines_in_done_record_a_task(self):
        self.p.branch("feat-a")
        base = self.plan("- [ ] **INS-3** the thing\n")
        self.plan("- [x] **INS-3** the thing\n", "close INS-3")
        for text in ("1. INS-3 done, not struck", "- [x] **INS-3** ticked", "1. mentioned later: INS-3 pending"):
            self.p.write(LOG, log_text().replace("1. nothing yet", text))
            self.p.commit("log", env=DAY)
            code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, self.p.sha())
            self.assertEqual(code, 1, f"{text}: {out}")
            self.assertIn("INS-3 is closed in the plan", out)
        self.p.write(LOG, log_text().replace("1. nothing yet", "1. 2026-10-21 — closed INS-3 with the fix"))
        self.p.commit("log", env=DAY)
        code, out = self.p.script("bitacora.py", "--plan", self.PLAN, "closed", base, self.p.sha())
        self.assertEqual(code, 0, out)

    def test_check_fails_on_a_task_row_without_a_branch_even_with_good_rows(self):
        self.p.write(LOG, log_text().replace("| **Branches**", "| **Tarea en curso** | no branch here |\n| **Branches**"))
        code, out = self.p.script("bitacora.py", "check")
        self.assertEqual(code, 1, out)
        self.assertIn("task row without a branch", out)
        self.assertIn("Tarea en curso", out)
        self.p.write(LOG, log_text())
        self.assertEqual(self.p.script("bitacora.py", "check")[0], 0)


class BitacoraCloseRow(Base):
    def test_close_row_writes_merged_text_only_in_that_row(self):
        code, out = self.p.script("bitacora.py", "close-row", "feat-a")
        self.assertEqual(code, 0, out)
        text = (self.p.work / LOG).read_text()
        self.assertIn("| **Task in progress · `feat-a`** | Merged, branch finished: nothing is pending on it. |", text)
        self.assertIn("| **Task in progress · `feat-b`** | doing B |", text)
        self.assertEqual(self.p.script("bitacora.py", "check")[0], 0)

    def test_close_row_with_text_and_unknown_branch(self):
        self.assertEqual(self.p.script("bitacora.py", "close-row", "feat-b", "--text", "done, merged")[0], 0)
        self.assertIn("| **Task in progress · `feat-b`** | done, merged |", (self.p.work / LOG).read_text())
        code, out = self.p.script("bitacora.py", "close-row", "nope")
        self.assertEqual(code, 1, out)
        self.assertIn("found 0 rows for nope", out)


class PrepushRamas(Base):
    def run_hook(self, sha, remote_sha=ZERO, ref="feat-a", env=None):
        stdin = f"refs/heads/{ref} {sha} refs/heads/{ref} {remote_sha}\n"
        changed, pushed = self.tmp / "changed", self.tmp / "pushed"
        changed.write_text("")
        pushed.write_text("")
        code, out = self.p.script("prepush-ramas.sh", str(changed), str(pushed), stdin=stdin, env=env)
        return code, out, changed.read_text().split(), pushed.read_text().split()

    def edit(self, **kw):
        self.p.write(LOG, log_text(**kw))
        self.p.commit("edit the log", env=DAY)
        return self.p.sha()

    def test_own_row_passes_and_lists_files_and_commits(self):
        self.p.branch("feat-a")
        sha = self.edit(a="A moved on")
        code, out, changed, pushed = self.run_hook(sha)
        self.assertEqual(code, 0, out)
        self.assertEqual(changed, [LOG])
        self.assertEqual(pushed, [sha])

    def test_other_row_refused_unless_shared(self):
        self.p.branch("feat-a")
        sha = self.edit(b="A rewrote B")
        code, out, _, _ = self.run_hook(sha)
        self.assertEqual(code, 1, out)
        self.assertIn("Task in progress · feat-b", out)
        for var in ("BITACORA_COMPARTIDA", "GW_SHARED_LOG"):
            self.assertEqual(self.run_hook(sha, env={var: "1"})[0], 0, var)

    def test_row_over_the_limit_refused(self):
        self.p.branch("feat-a")
        sha = self.edit(a="x" * 700)
        code, out, _, _ = self.run_hook(sha)
        self.assertEqual(code, 1, out)
        self.assertIn("700 characters", out)

    def test_commit_from_another_local_branch_may_use_its_row(self):
        self.p.branch("feat-b")
        self.edit(b="B moved on")
        self.p.branch("feat-a", "main")
        self.p.git("merge", "-q", "--ff-only", "feat-b")
        sha = self.p.sha()
        self.assertEqual(self.run_hook(sha)[0], 0)

    def test_noop_without_logrows(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"logRows": False})
        self.p.branch("feat-a")
        sha = self.edit(b="A rewrote B", a="x" * 900)
        code, out, changed, pushed = self.run_hook(sha)
        self.assertEqual((code, out, changed, pushed), (0, "", [], []))

    def test_single_branch_clone_falls_back_to_unpushed_commits(self):
        p = self.p
        p.git("push", "-q", "--no-verify", "origin", "main:other")
        p.git("update-ref", "-d", "refs/remotes/origin/main")  # a single-branch clone has no origin/main
        p.branch("feat-a")
        p.write("src/x.txt", "x\n")
        p.commit("add x", env=DAY)
        sha = p.sha()
        code, out, changed, _ = self.run_hook(sha)
        self.assertEqual(code, 0, out)
        self.assertEqual(changed, ["src/x.txt"])
        sha = self.edit(b="A rewrote B")
        code, out, _, _ = self.run_hook(sha)
        self.assertEqual(code, 1, out)

    def test_forks_from_the_configured_protected_branch(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        p = self.p = Utilidades(self.tmp, {"protectedBranch": "trunk"})
        p.git("push", "-q", "--no-verify", "origin", "main:trunk")
        p.git("update-ref", "-d", "refs/remotes/origin/main")  # only trunk is the protected branch here
        p.branch("feat-a")
        p.write("src/x1.txt", "1\n"); p.commit("x1", env=DAY)
        p.git("push", "-q", "--no-verify", "origin", "HEAD:refs/heads/feat-a-old")  # already on a remote ref
        p.write("src/x2.txt", "2\n"); p.commit("x2", env=DAY)
        code, out, changed, _ = self.run_hook(p.sha())
        self.assertEqual(code, 0, out)
        self.assertEqual(changed, ["src/x1.txt", "src/x2.txt"])

    def test_protected_branch_row_is_never_borrowed(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"protectedBranch": "feat-b"})
        self.p.branch("feat-b")
        self.edit(b="B moved on")
        self.p.branch("feat-a", "main")
        self.p.git("merge", "-q", "--ff-only", "feat-b")
        code, out, _, _ = self.run_hook(self.p.sha())
        self.assertEqual(code, 1, out)

    def test_pre_push_calls_it(self):
        self.p.branch("feat-a")
        self.edit(b="A rewrote B")
        code, out = self.p.push("origin", "feat-a")
        self.assertNotEqual(code, 0, out)
        self.assertIn("Task in progress · feat-b", out)
        self.assertIn("prepush-ramas.sh refused the push", out)
        code, out = self.p.push("origin", "feat-a", env={"BITACORA_COMPARTIDA": "1"})
        self.assertEqual(code, 0, out)


class Fusionar(Base):
    def agent(self, name="worktree-agent-1", path="a.txt", text="from the agent\n"):
        """A subagent's branch with its worktree (under .claude/worktrees/) and one commit."""
        wt = self.p.work / ".claude" / "worktrees" / name
        self.p.git("worktree", "add", "-q", "-b", name, str(wt))
        (wt / path).write_text(text)
        self.p.git("add", "-A", cwd=wt)
        self.p.git("commit", "-q", "-m", "agent work", cwd=wt, env=DAY)
        return wt

    def branches(self):
        return self.p.git("branch", "--format=%(refname:short)").stdout.split()

    def test_merges_runs_check_and_removes_worktree_and_branch(self):
        self.p.write("check.sh", "echo ran >> check.log\n")
        self.p.commit("check writes a log", env=DAY)
        wt = self.agent()
        code, out = self.p.script("fusionar.sh", "worktree-agent-1", "Merge agent 1", "--reviewed")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.p.work / "a.txt").is_file())
        self.assertEqual((self.p.work / "check.log").read_text(), "ran\n")
        self.assertEqual(self.p.git("log", "-1", "--format=%s").stdout.strip(), "Merge agent 1")
        self.assertEqual(len(self.p.git("log", "-1", "--format=%P").stdout.split()), 2, "merge, not rebase")
        self.assertFalse(wt.exists(), out)
        self.assertNotIn("worktree-agent-1", self.branches())
        self.assertNotIn("--reviewed", out.replace("no --reviewed", ""))

    def test_reminds_about_review_without_the_flag(self):
        self.agent()
        code, out = self.p.script("fusionar.sh", "worktree-agent-1", "Merge agent 1")
        self.assertEqual(code, 0, out)
        self.assertIn("no --reviewed", out)

    def test_conflict_stops_and_keeps_everything(self):
        wt = self.agent(path="docs/notes.md", text="agent notes\n")
        self.p.write("docs/notes.md", "main notes\n")
        self.p.commit("main edits the same file", env=DAY)
        code, out = self.p.script("fusionar.sh", "worktree-agent-1", "Merge agent 1")
        self.assertEqual(code, 1, out)
        self.assertIn("CONFLICT", out)
        self.assertIn("docs/notes.md", out)
        self.assertIn("git merge --abort", out)
        self.assertTrue((self.p.work / ".git" / "MERGE_HEAD").is_file())
        self.assertTrue(wt.exists())
        self.assertIn("worktree-agent-1", self.branches())

    def test_failing_check_says_how_to_undo_and_keeps_the_branch(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, check="exit 1")
        wt = self.agent()
        code, out = self.p.script("fusionar.sh", "worktree-agent-1", "Merge agent 1")
        self.assertEqual(code, 1, out)
        self.assertIn("CHECK FAILED", out)
        self.assertIn("git reset --hard HEAD^1", out)
        self.assertTrue(wt.exists())
        self.assertIn("worktree-agent-1", self.branches())

    def test_session_branches_are_merged_but_not_deleted(self):
        self.p.git("checkout", "-q", "-b", "claude/topic")
        self.p.write("t.txt", "t\n")
        self.p.commit("topic", env=DAY)
        self.p.git("checkout", "-q", "main")
        code, out = self.p.script("fusionar.sh", "claude/topic", "Merge topic")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.p.work / "t.txt").is_file())
        self.assertIn("claude/topic", self.branches())

    def test_unknown_branch_and_already_merged(self):
        self.assertEqual(self.p.script("fusionar.sh", "nope", "m")[0], 2)
        code, out = self.p.script("fusionar.sh", "main", "m")
        self.assertEqual(code, 0, out)
        self.assertIn("nothing to merge", out)


class RojoSinArreglo(Base):
    def setUp(self):
        super().setUp()
        self.p.write("fix.txt", "bad\n")
        self.p.commit("the bug", env=DAY)
        self.p.write("fix.txt", "good\n")  # the fix, uncommitted

    def stashes(self):
        return self.p.git("stash", "list").stdout.strip()

    def test_test_that_fails_without_the_fix_passes_the_check_and_restores_it(self):
        code, out = self.p.script("rojo-sin-arreglo.sh", "grep -q good fix.txt", "fix.txt")
        self.assertEqual(code, 0, out)
        self.assertIn("OK", out)
        self.assertEqual((self.p.work / "fix.txt").read_text(), "good\n")
        self.assertEqual(self.stashes(), "")

    def test_test_that_passes_without_the_fix_is_detected(self):
        code, out = self.p.script("rojo-sin-arreglo.sh", "test -f fix.txt", "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("also passes WITHOUT the fix", out)
        self.assertEqual((self.p.work / "fix.txt").read_text(), "good\n")
        self.assertEqual(self.stashes(), "")

    def test_test_that_fails_with_the_fix_too(self):
        code, out = self.p.script("rojo-sin-arreglo.sh", "grep -q never fix.txt", "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("does not pass with the fix", out)
        self.assertEqual((self.p.work / "fix.txt").read_text(), "good\n")

    def test_fix_file_without_changes_refused(self):
        code, out = self.p.script("rojo-sin-arreglo.sh", "true", "docs/notes.md")
        self.assertEqual(code, 2, out)
        self.assertIn("no uncommitted changes", out)

    def test_untracked_new_fix_file(self):
        self.p.write("new.txt", "x\n")
        code, out = self.p.script("rojo-sin-arreglo.sh", "test -f new.txt", "new.txt")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.p.work / "new.txt").is_file())
        self.assertEqual(self.stashes(), "")

    def test_fails_with_checks_the_reason(self):
        cmd = "echo boom; grep -q good fix.txt"
        self.assertEqual(self.p.script("rojo-sin-arreglo.sh", "--fails-with", "boom", cmd, "fix.txt")[0], 0)
        code, out = self.p.script("rojo-sin-arreglo.sh", "--fails-with", "other reason", cmd, "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("another reason", out)
        self.assertEqual((self.p.work / "fix.txt").read_text(), "good\n")

    def test_ran_one_requires_exactly_one_matching_line(self):
        one = "echo 'ok 1 - a'; grep -q good fix.txt"
        self.assertEqual(self.p.script("rojo-sin-arreglo.sh", "--ran-one", "^ok ", one, "fix.txt")[0], 0)
        two = "echo 'ok 1 - a'; echo 'ok 2 - b'; grep -q good fix.txt"
        code, out = self.p.script("rojo-sin-arreglo.sh", "--ran-one", "^ok ", two, "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("2 lines match /^ok /", out)
        code, out = self.p.script("rojo-sin-arreglo.sh", "--ran-one", "^ok ", "grep -q good fix.txt", "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("0 lines match /^ok /", out)
        self.assertEqual((self.p.work / "fix.txt").read_text(), "good\n")
        self.assertEqual(self.stashes(), "")

    def test_options_combine_and_need_a_value(self):
        cmd = "echo boom; echo 'ok 1'; grep -q good fix.txt"
        code, out = self.p.script("rojo-sin-arreglo.sh", "--fails-with", "boom", "--ran-one", "^ok ", cmd, "fix.txt")
        self.assertEqual(code, 0, out)
        code, out = self.p.script("rojo-sin-arreglo.sh", "--ran-one")
        self.assertEqual(code, 2, out)
        self.assertIn("--ran-one needs a regex", out)


class TestsRelacionados(Base):
    def run_with(self, related, changed=("src/a.py",)):
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        if related is not None:
            cfg["relatedTests"] = related
        (self.p.work / ".claude" / "gw.json").write_text(json.dumps(cfg))
        for f in ("src/a.py", "name with space.txt"):
            self.p.write(f, "x\n")
        listing = self.tmp / "changed"
        listing.write_text("".join(f + "\n" for f in changed))
        (self.p.work / "out.log").write_text("")
        self.p.git("add", "-A"); self.p.git("commit", "-q", "--no-verify", "-m", "related setup")
        code, out = self.p.script("tests-relacionados.sh", str(listing), stdin="refs/heads/x 1 refs/heads/x 2\n")
        return code, out, (self.p.work / "out.log").read_text().splitlines()

    def test_fast_then_slow_with_quoted_existing_files(self):
        fast = "for f in {files}; do echo \"fast:$f\" >> out.log; done"
        slow = "for f in {files}; do echo \"slow:$f\" >> out.log; done"
        code, out, lines = self.run_with({"fast": [fast], "slow": [slow]},
                                         ("src/a.py", "gone.py", "name with space.txt"))
        self.assertEqual(code, 0, out)
        self.assertEqual(lines, ["fast:src/a.py", "fast:name with space.txt", "slow:src/a.py", "slow:name with space.txt"])

    def test_no_changed_files_runs_only_fast_commands_without_files(self):
        related = {"fast": ["echo always >> out.log", "echo withfiles {files} >> out.log"],
                   "slow": ["echo slow >> out.log"]}
        code, out, lines = self.run_with(related, ())
        self.assertEqual(code, 0, out)
        self.assertEqual(lines, ["always"])

    def test_failure_stops_and_names_the_command(self):
        code, out, lines = self.run_with({"fast": ["exit 3"], "slow": ["echo slow >> out.log"]})
        self.assertEqual(code, 1, out)
        self.assertIn("failed (fast): exit 3", out)
        self.assertEqual(lines, [])

    def test_slow_failure(self):
        code, out, _ = self.run_with({"slow": ["false {files}"]})
        self.assertEqual(code, 1, out)
        self.assertIn("(slow)", out)

    def test_noop_when_absent_or_empty(self):
        for related in (None, {}, {"fast": [], "slow": []}):
            code, out, lines = self.run_with(related)
            self.assertEqual((code, out, lines), (0, "", []), related)

    def test_invalid_config_fails_closed(self):
        code, out, _ = self.run_with({"fast": "not a list"})
        self.assertEqual(code, 1, out)
        self.assertIn("config is invalid", out)

    def test_pre_push_runs_it_on_the_changed_files(self):
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg["relatedTests"] = {"fast": ["echo {files} > related.log"]}
        self.p.write(".claude/gw.json", json.dumps(cfg))
        self.p.branch("feat-a")
        self.p.write("src/b.py", "b\n")
        self.p.commit("add b", env=DAY)
        code, out = self.p.push("origin", "feat-a")
        self.assertEqual(code, 0, out)
        self.assertIn("src/b.py", (self.p.work / "related.log").read_text())

    def test_pre_push_runs_them_on_the_pushed_commit(self):
        p = self.p
        out_log = self.tmp / "related.log"
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["relatedTests"] = {"fast": [f"echo {{files}} > {out_log}; cat src/b.py >> {out_log}"]}
        p.write(".claude/gw.json", json.dumps(cfg))
        p.branch("feat-a")
        p.write("src/b.py", "committed-b\n"); p.write("src/gone.py", "g\n")
        p.commit("add b", env=DAY)
        p.git("rm", "-q", "src/gone.py"); p.git("commit", "-q", "--no-verify", "-m", "drop gone")
        (p.work / "src" / "b.py").unlink()            # dirty working tree: the file is only in the commit
        p.write("src/gone.py", "untracked again\n")   # and this one only on disk
        code, out = p.push("origin", "feat-a")
        self.assertEqual(code, 0, out)
        text = out_log.read_text()
        self.assertIn("src/b.py", text)
        self.assertNotIn("src/gone.py", text)
        self.assertIn("committed-b", text)


class EnlacesMd(Base):
    config = {"staleRefs": ["fase 3\\.5", "INS-\\d{2}"]}

    def run_it(self, *args):
        self.p.git("add", "-A")
        return self.p.script("enlaces-md.py", *args)

    def test_clean_docs_pass(self):
        self.p.write("README.md", "[notes](docs/notes.md) [web](https://example.com/x) [mail](mailto:a@b.c)\n")
        code, out = self.run_it()
        self.assertEqual(code, 0, out)

    def test_broken_link_and_anchor_listed_with_line(self):
        self.p.write("docs/a.md", "# Title\n\n[gone](missing.md)\n[ok](#title) [bad](#nope) [other](notes.md#x)\n")
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("docs/a.md:3: no such file missing.md", out)
        self.assertIn("docs/a.md:4: (this file) has no heading with the anchor #nope", out)
        self.assertIn("docs/a.md:4: notes.md has no heading with the anchor #x", out)
        self.assertNotIn("#title", out)
        self.assertIn("rerun: python3", out)
        code, out = self.run_it("--files-only")
        self.assertIn("no such file missing.md", out)
        self.assertNotIn("anchor", out)

    def test_links_in_code_are_ignored(self):
        self.p.write("docs/a.md", "```\n[x](nope.md)\n```\nand `[y](nope2.md)`\n")
        self.assertEqual(self.run_it()[0], 0)

    def test_stale_reference_hit_case_insensitive(self):
        self.p.write("docs/a.md", "ok\nSee FASE 3.5 and INS-12 here\n")
        code, out = self.run_it()
        self.assertEqual(code, 1, out)
        self.assertIn("docs/a.md:2: stale reference /fase 3\\.5/ matches 'FASE 3.5'", out)
        self.assertIn("INS-12", out)
        self.p.write("README.es.md", "fase 3.5\n")
        self.assertIn("README.es.md:1", self.run_it()[1])

    def test_log_claude_and_other_folders_are_skipped(self):
        for rel in (LOG, ".claude/notes.md", "notes/other.md", "src/readme.txt"):
            self.p.write(rel, "fase 3.5 and INS-12\n")
        code, out = self.run_it()
        self.assertEqual(code, 0, out)

    def test_invalid_regex_fails_closed(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.p = Utilidades(self.tmp, {"staleRefs": ["("]})
        code, out = self.run_it()
        self.assertEqual(code, 2, out)
        self.assertIn("not a valid regex", out)


class RepoItself(unittest.TestCase):
    def test_scripts_are_executable_and_versioned(self):
        for name in SCRIPTS:
            path = ROOT / "scripts" / name
            with self.subTest(script=name):
                self.assertTrue(path.stat().st_mode & 0o111, f"{name} must be executable: chmod +x scripts/{name}")
                head = path.read_text(encoding="utf-8").splitlines()[:3]
                self.assertIn(f"# galivelop-workflow v{VERSION}", head)
                self.assertTrue(head[0].startswith("#!"))

    def test_python_scripts_do_not_write_bytecode(self):
        for name in (n for n in SCRIPTS if n.endswith(".py")):
            self.assertIn("sys.dont_write_bytecode = True", (ROOT / "scripts" / name).read_text(encoding="utf-8"))

    def test_gw_json_of_this_repo_is_valid(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "config.py"), "validate"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads((ROOT / ".claude" / "gw.json").read_text())["version"], VERSION)


if __name__ == "__main__":
    unittest.main()
