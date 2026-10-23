"""Git hooks and their scripts, end to end: templates/githooks/pre-push and pre-commit, scripts/es-codigo.sh and
scripts/revisado.sh, in temporary repos (a bare "origin" plus a clone laid out like a project that applied the
workflow), with `git push` / `git commit` going through the real hooks (core.hooksPath).

Git runs isolated from this machine's configuration (GIT_CONFIG_GLOBAL to a temp file, GIT_CONFIG_NOSYSTEM=1), so
the suite behaves the same on a machine that signs commits and on a CI runner without an identity.
"""
import json
import os
import shutil
import subprocess
import tempfile
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

    def __init__(self, tmp, config=None, check="exit 0"):
        self.tmp = tmp
        self.bare = tmp / "origin.git"
        self.work = tmp / "work"
        gitconfig = tmp / "gitconfig"
        gitconfig.write_text("[user]\n\tname = Test\n\temail = test@example.com\n[commit]\n\tgpgsign = false\n"
                             "[tag]\n\tgpgsign = false\n[init]\n\tdefaultBranch = main\n[advice]\n\tdetachedHead = false\n")
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith("GIT_") and k not in ("CLAUDECODE", "CLAUDE_PROJECT_DIR")}
        self.env.update(GIT_CONFIG_GLOBAL=str(gitconfig), GIT_CONFIG_NOSYSTEM="1", TMPDIR=str(tmp))
        self.git("init", "-q", "--bare", str(self.bare), cwd=tmp)
        self.git("init", "-q", str(self.work), cwd=tmp)
        self.git("remote", "add", "origin", str(self.bare))
        gw = self.work / ".claude" / "gw"
        (gw / "scripts").mkdir(parents=True)
        (gw / "schema").mkdir()
        for name in ("config.py", "es-codigo.sh", "revisado.sh"):
            shutil.copy2(ROOT / "scripts" / name, gw / "scripts" / name)
        shutil.copy2(ROOT / "schema" / "gw.schema.json", gw / "schema" / "gw.schema.json")
        (self.work / ".githooks").mkdir()
        for name in ("pre-push", "pre-commit"):
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

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-ganchos-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Project(self.tmp, self.config)


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
        for i in range(3000):
            p.write(f"src/f{i}.py", "x\n")
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


if __name__ == "__main__":
    unittest.main()
