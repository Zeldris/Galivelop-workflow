"""red-without-fix.sh: --fix-at (fix already committed) and compile/load red vs assertion red."""
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

    def test_invalid_compile_re(self):
        code, out = self.run_script("--compile-re", "ok[", "--fix-at", self.fix, "true", "fix.txt")
        self.assertEqual(code, 2, out)
        self.assertIn("not a valid extended regex", out)


if __name__ == "__main__":
    unittest.main()
