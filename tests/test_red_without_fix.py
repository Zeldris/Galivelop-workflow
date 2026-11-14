"""red-without-fix.sh: --fix-at (fix already committed) and compile/load red vs assertion red."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from test_hooks import ROOT
from test_utils import DAY, Utils

sys.dont_write_bytecode = True
SCRIPT = "red-without-fix.sh"
WANT = ROOT / "scripts" / SCRIPT


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-rojo-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Utils(self.tmp)
        self.p.write("fix.txt", "bad\n")
        self.p.write("other.txt", "x\n")
        self.p.commit("the bug", env=DAY)
        self.p.write("fix.txt", "good\n")
        self.p.commit("the fix", env=DAY)
        self.fix = self.p.sha()
        self.p.write("later.txt", "later\n")
        self.p.commit("later work", env=DAY)

    def run_script(self, *args):
        return self.p.script(SCRIPT, *args)

    def fix_text(self):
        return (self.p.work / "fix.txt").read_text()


class FixAt(Base):
    def test_committed_fix_passes_and_file_is_restored(self):
        code, out = self.run_script("--fix-at", self.fix, "grep -q good fix.txt", "fix.txt")
        self.assertEqual(code, 0, out)
        self.assertIn("without the fix: exit 1; with the fix: exit 0", out)
        self.assertEqual(self.fix_text(), "good\n")
        self.assertEqual(self.p.git("status", "--porcelain").stdout.strip(), "")

    def test_test_that_passes_without_the_fix_is_refused(self):
        code, out = self.run_script("--fix-at", self.fix, "test -f fix.txt", "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("also passes WITHOUT the fix", out)
        self.assertEqual(self.fix_text(), "good\n")

    def test_symbolic_ref_works(self):
        code, out = self.run_script("--fix-at", "HEAD~1", "grep -q good fix.txt", "fix.txt")
        self.assertEqual(code, 0, out)

    def test_file_created_by_the_fix_is_removed_then_back(self):
        self.p.write("new.txt", "n\n")
        self.p.commit("fix adds new.txt", env=DAY)
        code, out = self.run_script("--fix-at", "HEAD", "test -f new.txt", "new.txt")
        self.assertEqual(code, 0, out)
        self.assertEqual((self.p.work / "new.txt").read_text(), "n\n")

    def test_symlink_in_the_fix_keeps_its_target_untouched(self):
        self.p.git("rm", "-q", "-f", "fix.txt")
        (self.p.work / "t.txt").write_text("target\n")
        (self.p.work / "lnk").symlink_to("t.txt")
        self.p.git("add", "t.txt", "lnk")
        self.p.commit("base link", env=DAY)
        (self.p.work / "lnk").unlink()
        (self.p.work / "lnk").symlink_to("fix2.txt")
        (self.p.work / "fix2.txt").write_text("f2\n")
        self.p.git("add", "lnk", "fix2.txt")
        self.p.commit("fix retargets link", env=DAY)
        code, out = self.run_script("--fix-at", "HEAD", "test \"$(readlink lnk)\" = fix2.txt", "lnk")
        self.assertEqual(code, 0, out)
        self.assertEqual((self.p.work / "t.txt").read_text(), "target\n")
        self.assertEqual((self.p.work / "fix2.txt").read_text(), "f2\n")
        self.assertTrue((self.p.work / "lnk").is_symlink())
        self.assertEqual((self.p.work / "lnk").readlink().as_posix(), "fix2.txt")
        self.assertEqual(self.p.git("status", "--porcelain").stdout.strip(), "")

    def test_mode_only_fix(self):
        self.p.write("run.sh", "echo hi\n")
        self.p.commit("script", env=DAY)
        self.p.git("update-index", "--chmod=+x", "run.sh")
        (self.p.work / "run.sh").chmod(0o755)
        self.p.commit("fix: make executable", env=DAY)
        code, out = self.run_script("--fix-at", "HEAD", "test -x run.sh", "run.sh")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.p.work / "run.sh").stat().st_mode & 0o100)
        self.assertEqual(self.p.git("status", "--porcelain").stdout.strip(), "")

    def test_not_a_commit(self):
        code, out = self.run_script("--fix-at", "nope", "true", "fix.txt")
        self.assertEqual(code, 2, out)
        self.assertIn("--fix-at nope is not a commit", out)

    def test_root_commit_has_no_parent(self):
        root = self.p.git("rev-list", "--max-parents=0", "HEAD").stdout.split()[0]
        code, out = self.run_script("--fix-at", root, "true", "fix.txt")
        self.assertEqual(code, 2, out)
        self.assertIn("no parent commit", out)

    def test_commit_not_an_ancestor(self):
        self.p.git("checkout", "-q", "-b", "side", "HEAD~1")
        self.p.write("s.txt", "s\n")
        self.p.commit("side", env=DAY)
        side = self.p.sha()
        self.p.git("checkout", "-q", "-")
        code, out = self.run_script("--fix-at", side, "true", "s.txt")
        self.assertEqual(code, 2, out)
        self.assertIn("not an ancestor of HEAD", out)

    def test_file_the_commit_did_not_change(self):
        code, out = self.run_script("--fix-at", self.fix, "true", "other.txt")
        self.assertEqual(code, 2, out)
        self.assertIn("does not change other.txt", out)

    def test_uncommitted_changes_in_fix_file_refused(self):
        self.p.write("fix.txt", "dirty\n")
        code, out = self.run_script("--fix-at", self.fix, "true", "fix.txt")
        self.assertEqual(code, 2, out)
        self.assertIn("fix files must be clean", out)
        self.assertEqual(self.fix_text(), "dirty\n")

    def test_test_code_in_the_fix_commit_refused(self):
        self.p.write("m.py", "def helper():\n    return 1\n")
        self.p.commit("m", env=DAY)
        self.p.write("m.py", "def helper():\n    return 2\n\ndef test_it():\n    pass\n")
        self.p.commit("fix with its test", env=DAY)
        code, out = self.run_script("--fix-at", "HEAD", "true", "m.py")
        self.assertEqual(code, 2, out)
        self.assertIn("touch test code", out)

    def test_missing_value(self):
        code, out = self.run_script("--fix-at")
        self.assertEqual(code, 2, out)
        self.assertIn("--fix-at needs a regex or value", out)

    def test_old_invocation_still_works_and_hints_fix_at(self):
        code, out = self.run_script("grep -q good fix.txt", "fix.txt")
        self.assertEqual(code, 2, out)
        self.assertIn("no uncommitted changes", out)
        self.assertIn("--fix-at <commit>", out)
        self.p.write("fix.txt", "better\n")
        code, out = self.run_script("grep -q better fix.txt", "fix.txt")
        self.assertEqual(code, 0, out)


class Uncommitted(Base):
    """The fix is uncommitted: the files are copied aside, never `git stash`ed, and always put back."""

    def setUp(self):
        super().setUp()
        self.p.write("fix.txt", "better\n")

    def stashes(self):
        return self.p.git("stash", "list").stdout.strip()

    def test_restored_after_success_without_a_stash(self):
        code, out = self.run_script("grep -q better fix.txt", "fix.txt")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.fix_text(), "better\n")
        self.assertEqual(self.stashes(), "")
        self.assertEqual(self.p.git("status", "--porcelain").stdout.strip(), "M fix.txt")

    def test_restored_after_the_test_fails_with_the_fix(self):
        code, out = self.run_script("false", "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("does not pass with the fix", out)
        self.assertEqual(self.fix_text(), "better\n")

    def test_restored_when_the_run_without_the_fix_is_killed(self):
        code, out = self.run_script("kill -TERM $PPID; sleep 5", "fix.txt")
        self.assertNotEqual(code, 0, out)
        self.assertEqual(self.fix_text(), "better\n")
        self.assertEqual(self.stashes(), "")

    def test_test_sees_the_head_version_without_the_fix(self):
        code, out = self.run_script("grep -q good fix.txt", "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("without the fix: exit 0; with the fix: exit 1", out)
        self.assertEqual(self.fix_text(), "better\n")

    def test_new_file_is_removed_then_restored(self):
        self.p.write("brand.txt", "n\n")
        code, out = self.run_script("test -f brand.txt", "fix.txt", "brand.txt")
        self.assertEqual(code, 0, out)
        self.assertIn("without the fix: exit 1; with the fix: exit 0", out)
        self.assertEqual((self.p.work / "brand.txt").read_text(), "n\n")
        self.assertEqual(self.stashes(), "")

    def test_staged_new_file_is_restored_and_stays_staged(self):
        self.p.write("brand.txt", "n\n")
        self.p.git("add", "brand.txt")
        code, out = self.run_script("test -f brand.txt", "brand.txt")
        self.assertEqual(code, 0, out)
        self.assertEqual((self.p.work / "brand.txt").read_text(), "n\n")
        self.assertIn("A  brand.txt", self.p.git("status", "--porcelain").stdout)

    def test_file_deleted_by_the_fix_is_back_then_deleted_again(self):
        (self.p.work / "other.txt").unlink()
        code, out = self.run_script("test -f other.txt", "other.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("without the fix: exit 0; with the fix: exit 1", out)
        self.assertFalse((self.p.work / "other.txt").exists())
        code, out = self.run_script("! test -f other.txt", "other.txt")
        self.assertEqual(code, 0, out)
        self.assertFalse((self.p.work / "other.txt").exists())
        self.assertEqual(self.stashes(), "")

    def test_unrelated_changes_and_the_users_stash_are_untouched(self):
        self.p.write("other.txt", "mine\n")
        self.p.git("stash", "push", "--quiet", "--", "other.txt")
        before = self.stashes()
        self.assertNotEqual(before, "")
        self.p.write("later.txt", "unstaged\n")
        self.p.write("untracked.txt", "u\n")
        self.p.git("add", "fix.txt")
        code, out = self.run_script("grep -q better fix.txt", "fix.txt")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.stashes(), before)
        self.assertEqual((self.p.work / "later.txt").read_text(), "unstaged\n")
        self.assertEqual((self.p.work / "untracked.txt").read_text(), "u\n")
        status = self.p.git("status", "--porcelain").stdout
        self.assertIn("M  fix.txt", status)
        self.assertIn(" M later.txt", status)

    def test_executable_mode_is_kept(self):
        import os
        path = self.p.work / "fix.txt"
        os.chmod(path, 0o755)
        code, out = self.run_script("grep -q better fix.txt", "fix.txt")
        self.assertEqual(code, 0, out)
        self.assertTrue(os.access(path, os.X_OK))

    def test_fix_file_in_a_new_directory_is_restored(self):
        self.p.write("newdir/sub/x.txt", "n\n")
        code, out = self.run_script("test -f newdir/sub/x.txt", "newdir/sub/x.txt")
        self.assertEqual(code, 0, out)
        self.assertEqual((self.p.work / "newdir/sub/x.txt").read_text(), "n\n")


    def test_symlink_in_the_fix_is_handled_as_a_link(self):
        import os
        os.symlink("other.txt", self.p.work / "lnk")
        code, out = self.run_script("test -L lnk", "lnk")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.p.work / "lnk").is_symlink())
        self.assertEqual(os.readlink(self.p.work / "lnk"), "other.txt")
        self.assertEqual((self.p.work / "other.txt").read_text(), "x\n")

    def test_dangling_symlink_is_restored(self):
        import os
        os.symlink("nowhere", self.p.work / "lnk")
        code, out = self.run_script("true", "lnk")
        self.assertEqual(os.readlink(self.p.work / "lnk"), "nowhere", out)

    def test_symlink_replacing_a_tracked_file_does_not_corrupt_its_target(self):
        import os
        (self.p.work / "fix.txt").unlink()
        os.symlink("other.txt", self.p.work / "fix.txt")
        code, out = self.run_script("grep -qx x fix.txt", "fix.txt")
        self.assertEqual(code, 0, out)
        self.assertEqual(os.readlink(self.p.work / "fix.txt"), "other.txt")
        self.assertEqual((self.p.work / "other.txt").read_text(), "x\n")

    def test_interrupt_during_the_run_keeps_nothing_in_tmp_and_prints_the_copy_path(self):
        code, out = self.run_script("kill -HUP $PPID; sleep 5", "fix.txt")
        self.assertNotEqual(code, 0, out)
        self.assertIn("gw-red-saved.", out)
        self.assertEqual(self.fix_text(), "better\n")
        self.assertEqual(list((self.p.work / ".git").glob("gw-red-saved.*")), [])

    def test_the_copy_lives_in_the_git_dir_while_the_run_goes(self):
        code, out = self.run_script("ls .git/gw-red-saved.*/1 && grep -q good fix.txt", "fix.txt")
        self.assertEqual(code, 1, out)  # `ls` inside the test command proves the copy exists, grep fails: with = no
        self.assertIn("without the fix: exit 0", out)

    def fake_cp(self, pattern):
        """A `cp` first in PATH that blocks (marker file, then waits) when its arguments match `pattern`."""
        import os
        d = self.tmp / "fakebin"
        d.mkdir()
        marker = self.tmp / "blocked"
        cp = d / "cp"
        cp.write_text('#!/bin/bash\ncase "$*" in *%s*) : > "%s"; sleep 60 & wait ;; esac\nexec /bin/cp "$@"\n'
                      % (pattern.replace(" ", "\\ "), marker))
        os.chmod(cp, 0o755)
        return d, marker

    def run_and_term(self, pattern, files):
        import os, signal, subprocess, time
        d, marker = self.fake_cp(pattern)
        env = dict(os.environ, PATH=str(d) + os.pathsep + os.environ["PATH"])
        proc = subprocess.Popen(["bash", str(self.p.scripts / SCRIPT), "true"] + files, cwd=self.p.work, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
        for _ in range(200):
            if marker.exists():
                break
            time.sleep(0.1)
        self.assertTrue(marker.exists(), "the fake cp was never reached")
        os.killpg(proc.pid, signal.SIGTERM)  # like Ctrl-C/kill of a group: the blocked cp dies too
        out = proc.communicate(timeout=60)[0]
        return proc.returncode, out

    def test_terminate_during_the_copy_leaves_every_file_as_it_was(self):
        self.p.write("other.txt", "mine\n")
        code, out = self.run_and_term("other.txt", ["fix.txt", "other.txt"])
        self.assertEqual(code, 143, out)
        self.assertIn("fix file 1 saved", out)
        self.assertNotIn("fix file 2 saved", out)
        self.assertEqual(self.fix_text(), "better\n")
        self.assertEqual((self.p.work / "other.txt").read_text(), "mine\n")

    def test_terminate_while_restoring_keeps_the_copies(self):
        self.p.write("other.txt", "mine\n")
        code, out = self.run_and_term("-- */gw-red-saved.*/2 ", ["fix.txt", "other.txt"])
        self.assertEqual(code, 143, out)
        self.assertEqual(self.fix_text(), "better\n")
        saved = list((self.p.work / ".git").glob("gw-red-saved.*"))
        self.assertEqual(len(saved), 1, out)
        self.assertEqual((saved[0] / "2").read_text(), "mine\n")

    def test_symlink_to_a_directory_is_not_taken_for_a_directory(self):
        import os
        (self.p.work / "d").mkdir()
        os.symlink("d", self.p.work / "dl")
        code, out = self.run_script("true", "dl")
        self.assertNotIn("is a directory", out)
        self.assertEqual(os.readlink(self.p.work / "dl"), "d")

    def test_restore_refreshes_the_mtime(self):
        import os, time
        path = self.p.work / "fix.txt"
        old = time.time() - 100000
        os.utime(path, (old, old))
        code, out = self.run_script("true", "fix.txt")
        self.assertGreater(path.stat().st_mtime, old + 1000)

    def test_deleted_file_comes_back_with_its_executable_bit(self):
        import os
        self.p.write("run.sh", "#!/bin/sh\n")
        os.chmod(self.p.work / "run.sh", 0o755)
        self.p.git("add", "run.sh")
        self.p.commit("add run.sh", env=DAY)
        (self.p.work / "run.sh").unlink()
        code, out = self.run_script("test -x run.sh", "run.sh")
        self.assertEqual(code, 1, out)
        self.assertIn("without the fix: exit 0; with the fix: exit 1", out)

    def test_directory_argument_is_refused_with_a_clear_reason(self):
        self.p.write("d/x.txt", "n\n")
        code, out = self.run_script("true", "d")
        self.assertEqual(code, 2, out)
        self.assertIn("is a directory", out)

    def test_filters_are_applied_to_the_head_version(self):
        self.p.write(".gitattributes", "*.crlf text eol=crlf\n")
        self.p.git("add", ".gitattributes")
        self.p.commit("attrs", env=DAY)
        self.p.write("a.crlf", "one\n")
        self.p.git("add", "a.crlf")
        self.p.commit("crlf", env=DAY)
        self.p.git("rm", "-q", "--cached", "a.crlf")
        (self.p.work / "a.crlf").write_bytes(b"two\r\n")
        self.p.git("add", "a.crlf")
        self.p.git("reset", "-q", "HEAD", "--", "a.crlf")
        self.p.git("checkout", "-q", "--", ".gitattributes")
        (self.p.work / "a.crlf").write_bytes(b"two\r\n")
        code, out = self.run_script("grep -q 'one.$' a.crlf", "a.crlf")
        self.assertEqual(code, 1, out)
        self.assertIn("without the fix: exit 0", out)


class TextFiles(Base):
    """Prose in a text/data file must not read as test code (`it(` in "improve it (URL)")."""

    def fix_prose(self, name, text="improve it (see URL)\n"):
        self.p.write(name, "old\n")
        self.p.commit("base " + name, env=DAY)
        self.p.write(name, text)

    def test_prose_with_it_paren_in_a_tracked_text_file_is_not_test_code(self):
        self.fix_prose("notes.md")
        code, out = self.run_script("grep -q improve notes.md", "notes.md")
        self.assertEqual(code, 0, out)
        self.assertIn("notes.md is a .md text/data file (nonTestExtensions)", out)

    def test_untracked_text_file_and_upper_case_extension_and_spaces(self):
        self.p.write("my notes.MD", "improve it (see URL)\n")
        code, out = self.run_script("grep -q improve 'my notes.MD'", "my notes.MD")
        self.assertEqual(code, 0, out)
        self.assertIn("my notes.MD is a .md text/data file", out)

    def test_real_test_file_still_refused(self):
        self.fix_prose("m.py", "def test_it():\n    pass\n")
        code, out = self.run_script("true", "m.py")
        self.assertEqual(code, 2, out)
        self.assertIn("touch test code", out)

    def test_file_without_extension_is_still_searched(self):
        self.p.write("Makefile", "improve it (see URL)\n")
        code, out = self.run_script("true", "Makefile")
        self.assertEqual(code, 2, out)
        self.assertIn("touch test code", out)

    def test_list_comes_from_the_config(self):
        path = self.p.work / ".claude" / "gw.json"
        cfg = json.loads(path.read_text())
        cfg["nonTestExtensions"] = []
        path.write_text(json.dumps(cfg))
        self.fix_prose("notes.md")
        code, out = self.run_script("true", "notes.md")
        self.assertEqual(code, 2, out)
        self.assertIn("touch test code", out)


    def test_unreadable_list_blocks_with_exit_2(self):
        path = self.p.work / ".claude" / "gw.json"
        cfg = json.loads(path.read_text())
        cfg["nonTestExtensions"] = ["MD"]
        path.write_text(json.dumps(cfg))
        self.fix_prose("notes.md")
        code, out = self.run_script("true", "notes.md")
        self.assertEqual(code, 2, out)
        self.assertIn("cannot read redWithoutFix.compileRegex", out)  # the first key the script reads: the config is invalid
        self.assertIn("nonTestExtensions", out.split("cannot read")[0])  # config.py names the key and the problem

    def test_extension_with_a_newline_is_never_skipped(self):
        name = "t.md\ndef test_x"
        self.p.write(name, "improve it (see URL)\n")
        code, out = self.run_script("true", name)
        self.assertEqual(code, 2, out)
        self.assertIn("touch test code", out)
        self.assertNotIn("text/data file", out)


class RedKind(Base):
    def cmd(self, message, word="good"):
        return f"if grep -q {word} fix.txt; then exit 0; fi; echo \"{message}\"; exit 1"

    def test_assertion_red_reported(self):
        code, out = self.run_script("--fix-at", self.fix, self.cmd("AssertionError: 'bad' != 'good'"), "fix.txt")
        self.assertEqual(code, 0, out)
        self.assertIn("is an assertion red", out)

    def test_compile_red_reported_by_default_with_matched_line(self):
        for message in ("ModuleNotFoundError: No module named x", "SyntaxError: invalid syntax",
                        "ERROR collecting tests/test_a.py", "error[E0425]: cannot find value", "error TS2304: Cannot find name"):
            code, out = self.run_script("--fix-at", self.fix, self.cmd(message), "fix.txt")
            self.assertEqual(code, 0, (message, out))
            self.assertIn("is a compile/load red", out)
            self.assertIn("matched: " + message, out)
            self.assertEqual(self.fix_text(), "good\n")

    def test_assertion_log_mentioning_import_error_is_reported_not_failed(self):
        code, out = self.run_script("--fix-at", self.fix,
                                    self.cmd("DID NOT RAISE <class 'ImportError'>"), "fix.txt")
        self.assertEqual(code, 0, out)
        self.assertIn("matched: DID NOT RAISE <class 'ImportError'>", out)

    def test_reject_compile_red(self):
        code, out = self.run_script("--reject-compile-red", "--fix-at", self.fix,
                                    self.cmd("SyntaxError: x"), "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("cannot load", out)
        self.assertIn("--fails-with", out)
        self.assertEqual(self.fix_text(), "good\n")

    def test_reject_compile_red_also_for_uncommitted_fix(self):
        self.p.write("fix.txt", "better\n")
        code, out = self.run_script("--reject-compile-red", self.cmd("ImportError: cannot import name", "better"), "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("cannot load", out)
        self.assertEqual(self.p.git("stash", "list").stdout.strip(), "")

    def test_reject_compile_red_passes_an_assertion_red(self):
        code, out = self.run_script("--reject-compile-red", "--fix-at", self.fix,
                                    self.cmd("AssertionError: x"), "fix.txt")
        self.assertEqual(code, 0, out)

    def test_fails_with_decides_over_compile_check(self):
        code, out = self.run_script("--reject-compile-red", "--fails-with", "ImportError", "--fix-at", self.fix,
                                    self.cmd("ImportError: cannot import name"), "fix.txt")
        self.assertEqual(code, 0, out)
        code, out = self.run_script("--fails-with", "other", "--fix-at", self.fix,
                                    self.cmd("ImportError: cannot import name"), "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("but not with /other/", out)

    def test_custom_compile_re(self):
        code, out = self.run_script("--fix-at", self.fix, self.cmd("boom: cannot parse"), "fix.txt")
        self.assertEqual(code, 0, out)
        code, out = self.run_script("--compile-re", "cannot parse", "--fix-at", self.fix,
                                    self.cmd("boom: cannot parse"), "fix.txt")
        self.assertEqual(code, 0, out)
        self.assertIn("compile/load red", out)
        code, out = self.run_script("--reject-compile-red", "--compile-re", "cannot parse", "--fix-at", self.fix,
                                    self.cmd("boom: cannot parse"), "fix.txt")
        self.assertEqual(code, 1, out)
        self.assertIn("cannot load", out)

    def set_keys(self, **keys):
        path = self.p.work / ".claude" / "gw.json"
        cfg = json.loads(path.read_text())
        cfg["redWithoutFix"] = keys
        path.write_text(json.dumps(cfg))

    def test_compile_regex_key_replaces_the_built_in_list_and_the_flag_wins(self):
        self.set_keys(compileRegex="cannot parse")
        code, out = self.run_script("--fix-at", self.fix, self.cmd("boom: cannot parse"), "fix.txt")
        self.assertEqual(code, 0, out)
        self.assertIn("compile/load red", out)
        code, out = self.run_script("--fix-at", self.fix, self.cmd("ImportError: x"), "fix.txt")
        self.assertEqual(code, 0, out)
        self.assertNotIn("compile/load red", out)        # a built-in message is no longer one
        code, out = self.run_script("--compile-re", "ImportError", "--fix-at", self.fix, self.cmd("ImportError: x"),
                                    "fix.txt")
        self.assertIn("compile/load red", out)

    def test_invalid_compile_regex_key_exits_2_naming_it(self):
        self.set_keys(compileRegex="ok[")
        code, out = self.run_script("--fix-at", self.fix, "true", "fix.txt")
        self.assertEqual(code, 2, out)
        self.assertIn("/ok[/ is not a valid extended regex", out)
        self.assertIn("redWithoutFix", out)

    def test_test_regex_key_decides_what_is_test_code_in_a_fix_file(self):
        self.p.write("m.py", "old\n")
        self.p.commit("base m.py", env=DAY)
        self.p.write("m.py", "def check_it():\n    pass\n")
        code, out = self.run_script("true", "m.py")
        self.assertEqual(code, 1, out)                   # not test code by default: it got as far as the run
        self.assertNotIn("touch test code", out)
        self.set_keys(testRegex="def check_")
        code, out = self.run_script("true", "m.py")
        self.assertEqual(code, 2, out)
        self.assertIn("touch test code", out)
        self.p.write("m.py", "def test_it():\n    pass\n")
        code, out = self.run_script("true", "m.py")
        self.assertEqual(code, 1, out)                   # the default no longer applies
        self.assertNotIn("touch test code", out)

    def test_invalid_compile_re(self):
        code, out = self.run_script("--compile-re", "ok[", "--fix-at", self.fix, "true", "fix.txt")
        self.assertEqual(code, 2, out)
        self.assertIn("not a valid extended regex", out)


if __name__ == "__main__":
    unittest.main()
