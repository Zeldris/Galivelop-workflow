"""scripts/review-scope.py (D82) and apply.py --vendored: the phase 1 review leaves out unchanged workflow copies. Every
failing case checks the message, not only the exit code."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from test_apply import Fixture, ROOT

sys.dont_write_bytecode = True
HOOK = ".githooks/pre-push"
SCRIPT = ".claude/gw/scripts/change-size.py"


class ScopeBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-review-scope-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)
        self.assertEqual(self.p.run_apply()[0], 0)
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "base")
        self.p.run("git", "checkout", "-q", "-b", "work")

    def commit(self):
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "work")

    def scope(self, *args):
        return self.p.run("python3", str(self.p.work / ".claude/gw/scripts/review-scope.py"), "--base", "main",
                          "--workflow", str(ROOT), *args)

    def listed(self, *args):
        code, out = self.scope(*args)
        self.assertEqual(code, 0, out)
        return [l for l in out.splitlines() if not l.startswith("review-scope:")]



class ReviewScope(ScopeBase):
    def test_no_vendored_files_lists_the_whole_diff(self):
        self.p.write("src/a.py", "a\n")
        self.p.write("docs/b.md", "b\n")
        self.commit()
        self.assertEqual(self.listed(), ["docs/b.md", "src/a.py"])

    def test_vendored_files_are_left_out(self):
        self.p.write("src/a.py", "a\n")
        self.p.write(HOOK, (self.p.work / HOOK).read_text())  # same bytes: not a change at all
        self.p.write(".claude/gw/scripts/extra.py", "x\n")  # a file the workflow does not ship: the project's own
        self.commit()
        self.assertEqual(self.listed(), [".claude/gw/scripts/extra.py", "src/a.py"])

    def test_all_vendored_prints_nothing_and_says_how_many(self):
        # the whole workflow copy arrives in one branch: the diff is its project's files plus unchanged copies only
        tmp = Path(tempfile.mkdtemp(prefix="gw-review-scope-all-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        q = Fixture(tmp)
        q.run("git", "add", "-A")
        q.run("git", "commit", "-qm", "base")
        q.run("git", "checkout", "-q", "-b", "work")
        self.assertEqual(q.run_apply()[0], 0)
        q.run("git", "add", "-A")
        q.run("git", "commit", "-qm", "work")
        code, out = q.run("python3", str(q.work / ".claude/gw/scripts/review-scope.py"), "--base", "main",
                          "--workflow", str(ROOT))
        self.assertEqual(code, 0, out)
        shown = [l for l in out.splitlines() if not l.startswith("review-scope:")]
        # what stays is the project's to fill in (templates, config): never a script, skill or hook copy
        self.assertFalse([l for l in shown if l.startswith((".claude/gw/scripts/", ".claude/skills/", ".githooks/"))], shown)
        self.assertIn("vendored file(s) left out of", out)

    def test_a_vendored_file_edited_locally_is_still_reviewed(self):
        (self.p.work / SCRIPT).write_text((self.p.work / SCRIPT).read_text() + "# local\n")
        self.p.write(HOOK, (self.p.work / HOOK).read_text())
        self.commit()
        self.assertEqual(self.listed(), [SCRIPT])

    def test_a_renamed_vendored_copy_is_listed_by_its_new_path(self):
        (self.p.work / "tools").mkdir()
        self.p.run("git", "mv", HOOK, "tools/pre-push")
        self.commit()
        self.assertEqual(self.listed(), [HOOK, "tools/pre-push"])

    def test_all_flag_lists_everything(self):
        self.p.write("src/a.py", "a\n")
        (self.p.work / SCRIPT).write_text((self.p.work / SCRIPT).read_text() + "# local\n")
        self.commit()
        self.assertEqual(self.listed("--all"), [SCRIPT, "src/a.py"])

    def test_without_a_workflow_the_whole_diff_is_listed_with_a_note(self):
        self.p.write("src/a.py", "a\n")
        self.commit()
        code, out = self.p.run("python3", str(self.p.work / ".claude/gw/scripts/review-scope.py"), "--base", "main")
        self.assertEqual(code, 0, out)
        self.assertIn("src/a.py", out)
        self.assertIn("no workflow repo to compare with", out)

    def test_a_base_that_is_not_a_commit_fails_with_the_fix(self):
        code, out = self.scope("--base", "nope")
        self.assertEqual(code, 2)
        self.assertIn("is not a commit", out)


class Trivial(ScopeBase):
    """B27: --trivial."""

    def setUp(self):
        super().setUp()
        self.p.write(".claude/gw.json", (self.p.work / ".claude/gw.json").read_text())
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "gw")
        self.p.run("git", "branch", "-f", "main", "HEAD")

    def limit(self, n):
        import json
        cfg = json.loads((self.p.work / ".claude/gw.json").read_text())
        cfg["reviewTrivialLines"] = n
        self.p.write(".claude/gw.json", json.dumps(cfg))
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "limit")
        self.p.run("git", "branch", "-f", "main", "HEAD")

    def code(self, n):
        self.p.write("src/a.py", "".join(f"x{i} = {i}\n" for i in range(n)))
        self.commit()

    def test_no_code_is_trivial_whatever_its_size(self):
        self.limit(0)
        self.p.write("docs/b.md", "".join(f"l{i}\n" for i in range(500)))
        self.commit()
        code, out = self.scope("--trivial")
        self.assertEqual(code, 0, out)
        self.assertIn("no code in the review scope", out)

    def test_small_code_diff_is_trivial(self):
        self.code(5)
        code, out = self.scope("--trivial")
        self.assertEqual(code, 0, out)
        self.assertIn("5 changed code line(s), at most reviewTrivialLines=30", out)

    def test_at_the_threshold_is_trivial_and_one_over_is_not(self):
        self.limit(10)
        self.code(10)
        self.assertEqual(self.scope("--trivial")[0], 0)
        self.code(11)
        code, out = self.scope("--trivial")
        self.assertEqual(code, 1, out)
        self.assertIn("not trivial: 1 code file(s), 11 changed line(s), reviewTrivialLines=10", out)

    def test_zero_turns_the_line_limit_off(self):
        self.limit(0)
        self.code(1)
        code, out = self.scope("--trivial")
        self.assertEqual(code, 1, out)
        self.assertIn("reviewTrivialLines=0", out)

    def test_an_empty_scope_is_trivial(self):
        code, out = self.scope("--trivial")
        self.assertEqual(code, 0, out)


class Vendored(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-vendored-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)
        self.p.run_apply()

    def test_lists_unchanged_copies_and_not_edited_or_template_ones(self):
        (self.p.work / SCRIPT).write_text((self.p.work / SCRIPT).read_text() + "# local\n")
        code, out = self.p.run_apply("--vendored")
        self.assertEqual(code, 0, out)
        lines = out.splitlines()
        self.assertIn(HOOK, lines)
        self.assertNotIn(SCRIPT, lines)
        self.assertNotIn("AGENTS.md", lines)
        self.assertEqual(self.p.read(SCRIPT).splitlines()[-1], "# local", "it writes nothing")

    def test_init_and_vendored_together_write_nothing(self):
        tmp = Path(tempfile.mkdtemp(prefix="gw-vendored-init-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        q = Fixture(tmp)
        (q.work / ".claude/gw.json").unlink()
        code, out = q.run_apply("--init", "--vendored", "--check-command", "true")
        self.assertEqual(code, 2, out)
        self.assertIn("--init writes files", out)
        self.assertFalse((q.work / ".claude/gw.json").exists())

    def test_an_owned_file_is_not_vendored(self):
        self.p.write(".claude/gw.json", (self.p.work / ".claude/gw.json").read_text().replace(
            "{", '{"ownedFiles": [".githooks/pre-push"],', 1))
        code, out = self.p.run_apply("--vendored")
        self.assertEqual(code, 0, out)
        self.assertNotIn(HOOK, out.splitlines())


if __name__ == "__main__":
    unittest.main()
