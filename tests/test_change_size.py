"""scripts/change-size.py (D43): commit and review-block size in changed lines, with warnings above changeSize, and its
call from the commit-msg hook. Every failing case checks the message, not only the exit code."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT, Base

sys.dont_write_bytecode = True
SCRIPT = ROOT / "scripts" / "change-size.py"


def lines(n, tag="x"):
    return "".join(f"{tag}{i}\n" for i in range(n))


class ChangeSize(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-change-size-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test"); self.git("config", "user.email", "t@example.com")
        self.git("config", "commit.gpgsign", "false")
        self.configure({"commit": 10, "block": 30})
        self.write("a.txt", "a\n")
        self.commit("base")
        self.git("checkout", "-q", "-b", "work")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.tmp), *args], check=True, capture_output=True, text=True).stdout

    def write(self, rel, text):
        (self.tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.tmp / rel).write_text(text)

    def commit(self, message):
        self.git("add", "-A"); self.git("commit", "-qm", message)

    def configure(self, size):
        cfg = dict(BASE_CONFIG, changeSize=size)
        self.write(".claude/gw.json", json.dumps(cfg, indent=2) + "\n")

    def run_cli(self, *args):
        self.git("add", "-A")
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(self.tmp), *args],
                           capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr

    def test_commit_over_the_limit_warns_and_under_it_is_silent(self):
        self.write("b.txt", lines(10))
        code, out, err = self.run_cli()
        self.assertEqual((code, out, err), (0, "", ""))
        self.write("b.txt", lines(11))
        code, out, err = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("WARNING: this commit changes 11 lines (more than 10, changeSize.commit", err)

    def test_deleted_lines_count_and_zero_turns_the_warning_off(self):
        self.write("b.txt", lines(8)); self.commit("b")
        self.write("b.txt", lines(8, "y"))  # 8 deleted + 8 added
        self.assertIn("changes 16 lines", self.run_cli()[2])
        self.configure({"commit": 0, "block": 0})
        code, out, err = self.run_cli("--show")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("(limit off)", out)

    def test_excluded_generated_and_binary_files_do_not_count(self):
        self.write(".claude/gw/scripts/x.py", lines(50))
        self.write("package-lock.json", lines(50))
        self.write(".gitattributes", "gen/** linguist-generated\n")  # 1 line
        self.write("gen/out.html", lines(50))
        (self.tmp / "img.bin").write_bytes(bytes(range(256)) * 10)
        self.write("b.txt", lines(3))
        code, out, err = self.run_cli("--show")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("the staged change: 4 lines", out)

    def test_a_pair_counts_its_larger_side_and_a_lone_side_counts_whole(self):
        self.write("docs/es/g.md", lines(6)); self.write("docs/en/g.md", lines(7))
        self.write("README.md", lines(2)); self.write("README.es.md", lines(2))
        self.write("docs/plan.en.md", lines(1))  # its pair docs/plan.md does not change: counts
        code, out, _ = self.run_cli("--show")
        self.assertIn("the staged change: 10 lines", out)

    def test_block_starts_after_the_last_review_trailer_and_skips_main_and_merges(self):
        self.write("b.txt", lines(20)); self.commit("before the review")
        self.write("c.txt", lines(5)); self.git("add", "-A")
        self.git("commit", "-qm", "fix: review\n\nFindings: 0")
        self.write("d.txt", lines(9)); self.commit("after")
        self.git("checkout", "-q", "main"); self.write("m.txt", lines(40)); self.commit("on main")
        self.git("checkout", "-q", "work"); self.git("merge", "-q", "--no-edit", "main")
        self.write("e.txt", lines(4))
        code, out, err = self.run_cli("--show")
        self.assertEqual(err, "")
        self.assertRegex(out, r"the block after [0-9a-f]{12} \(last commit with a Findings: trailer\): 13 lines with "
                              r"the staged change, 1 commit\(s\)")
        self.write("e.txt", lines(10))  # 9 + 10 = 19: still under 30
        self.write("f.txt", lines(10))  # 29 ... and the commit itself warns (20 > 10)
        self.write("g.txt", lines(2))   # 31 > 30
        err = self.run_cli()[2]
        self.assertIn("WARNING: the block after", err)
        self.assertIn("changes 31 lines with this commit (1 commit(s) before it; more than 30, changeSize.block", err)
        self.assertIn("`Findings: <n>`", err)

    def test_without_a_review_the_block_is_the_whole_branch_and_base_overrides_it(self):
        self.write("b.txt", lines(20)); self.commit("one")
        self.write("c.txt", lines(15)); self.commit("two")
        err = self.run_cli()[2]
        self.assertIn("the block since the branch left main changes 35 lines", err)
        out = self.run_cli("--base", "HEAD~1", "--show")[1]
        self.assertIn("the block after HEAD~1: 15 lines", out)

    def test_no_block_on_the_protected_branch(self):
        self.git("checkout", "-q", "main")
        self.write("b.txt", lines(5))
        out = self.run_cli("--show")[1]
        self.assertNotIn("block", out)

    def test_no_protected_branch_gives_a_note(self):
        self.git("branch", "-m", "main", "old")
        code, out, err = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("no origin/main nor main, so the block size is not checked", err)
        self.assertIn("--base <commit>", err)

    def test_bad_base_fails_closed(self):
        code, out, err = self.run_cli("--base", "nope")
        self.assertEqual(code, 2)
        self.assertIn("--base nope is not a commit", err)

    def test_invalid_regexes_are_config_errors(self):
        self.configure({"exclude": ["("], "pairs": {"^a(b)$": "\\2"}})
        code, out, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("$.changeSize.exclude[0]: '(' is not a valid regex", err)
        self.assertIn("$.changeSize.pairs['^a(b)$']: replacement '\\\\2' does not fit its regex", err)


class CommitMsgSize(Base):
    """templates/githooks/commit-msg calls change-size.py: it warns and the commit goes on."""
    config = {"changeSize": {"commit": 3, "block": 0}}
    hooks = ("pre-push", "pre-commit", "commit-msg")

    def test_a_big_commit_is_warned_not_stopped(self):
        self.p.write("docs/notes.md", lines(5))
        r = self.p.commit("notes", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("change-size: WARNING: this commit changes 6 lines", r.stderr)

    def test_a_failing_size_check_does_not_stop_the_commit(self):
        script = self.p.work / ".claude" / "gw" / "scripts" / "change-size.py"
        script.write_text("import sys\nprint('change-size: broken', file=sys.stderr)\nsys.exit(2)\n")
        self.p.write("docs/notes.md", lines(5))
        r = self.p.commit("notes", ok=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("change-size: broken", r.stderr)
        self.assertIn("WARNING: the size check failed (above); the commit goes on", r.stderr)

    def test_missing_script_fails_closed(self):
        (self.p.work / ".claude" / "gw" / "scripts" / "change-size.py").unlink()
        self.p.write("docs/notes.md", "x\n")
        r = self.p.commit("notes", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("change-size.py is missing; reinstall the workflow scripts", r.stderr)


if __name__ == "__main__":
    unittest.main()
