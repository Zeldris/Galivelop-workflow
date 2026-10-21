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
BASE_CONFIG = {"version": "0.1.0", "language": "en", "log": "docs/log.md", "protectedBranch": "main",
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
        code, out = self.push_main(self.marked, remote_main=None)
        self.assertEqual(code, 0, out)

    def test_unknown_remote_protected_sha_fails_closed(self):
        line = f"refs/heads/feature {self.marked} refs/heads/main {'1' * 40}\n"
        code, out = self.p.run(str(self.p.work / ".githooks" / "pre-push"), "origin", str(self.p.bare), stdin=line)
        self.assertNotEqual(code, 0, out)
        self.assertIn("git fetch origin main", out)

    def test_pr_mode_does_not_require_the_mark(self):
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg["pushToProtected"] = "pr"
        (self.p.work / ".claude" / "gw.json").write_text(json.dumps(cfg))  # read from the working tree
        code, out = self.push_main(self.code)
        self.assertEqual(code, 0, out)

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
        code, out = self.p.push("origin", "HEAD:refs/heads/copy")
        self.assertEqual(code, 0, out)
        self.assertIn("nothing new to push to refs/heads/copy", out)

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


class Revisado(Base):
    def setUp(self):
        super().setUp()
        p = self.p
        p.git("checkout", "-q", "-b", "feature")
        p.write("src/a.py", "a = 1\n"); p.commit("code")
        self.assertEqual(p.push("-u", "origin", "feature")[0], 0)
        self.script = str(p.work / ".claude" / "gw" / "scripts" / "revisado.sh")

    def test_dirty_tree_refused(self):
        self.p.write("stray.txt", "x\n")
        code, out = self.p.run("bash", self.script)
        self.assertNotEqual(code, 0, out)
        self.assertIn("uncommitted or untracked", out)

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

    def test_missing_commit_or_config_exits_2(self):
        p = self.p
        script = str(p.work / ".claude" / "gw" / "scripts" / "es-codigo.sh")
        self.assertEqual(p.run("bash", script, "1" * 40, "HEAD")[0], 2)
        (p.work / ".claude" / "gw.json").unlink()
        self.assertEqual(p.run("bash", script, p.base, "HEAD")[0], 2)


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

    def test_this_test_file_passes_the_scan(self):
        shutil.copy2(Path(__file__), self.p.work / "test_ganchos.py")
        r = self.p.commit("tests", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)

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
