"""scripts/tests-for.py (E21): the test files a change calls for, from testMap in .claude/gw.json. Every failing case
checks the message, not only the exit code."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT

sys.dont_write_bytecode = True
SCRIPT = ROOT / "scripts" / "tests-for.py"
RULES = [
    {"paths": "^scripts/(?P<name>[^/]+)\\.(py|sh)$", "tests": ["tests/test_{name:id}.py"]},
    {"paths": "^scripts/", "tests": ["tests/test_hooks.py", "tests/test_missing.py"]},
    {"paths": "^tests/test_[^/]+\\.py$", "tests": ["{path}"]},
    {"paths": "^tests/", "contains": "[a-z]+@[a-z]+\\.[a-z]+", "tests": ["tests/test_private.py"]},
]


class TestsFor(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-tests-for-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.git("init", "-q")
        self.git("config", "user.name", "Test"); self.git("config", "user.email", "t@example.com")
        self.git("config", "commit.gpgsign", "false")
        for test in ("test_config_guard.py", "test_hooks.py", "test_private.py", "test_a.py", "test_b c.py"):
            self.write("tests/" + test, "import unittest\n")
        self.write("scripts/config-guard.py", "x\n")
        self.configure(RULES, "")
        self.git("add", "-A"); self.git("commit", "-qm", "base")

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.tmp), *args], check=True, capture_output=True)

    def write(self, rel, text):
        (self.tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.tmp / rel).write_text(text)

    def configure(self, rules, command):
        cfg = dict(BASE_CONFIG, testMap={"rules": rules, "command": command})
        self.write(".claude/gw.json", json.dumps(cfg, indent=2) + "\n")

    def run_cli(self, *args, cwd=None):
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(self.tmp), *args],
                           capture_output=True, text=True, cwd=str(cwd or self.tmp))
        return r.returncode, r.stdout, r.stderr

    def test_rules_give_existing_tests_sorted_once(self):
        code, out, err = self.run_cli("scripts/config-guard.py", "scripts/related-tests.sh", "scripts/config-guard.py")
        self.assertEqual(code, 0, err)
        # {name:id} turns '-' into '_'; test_related_tests.py and test_missing.py do not exist, so they are left out.
        self.assertEqual(out.splitlines(), ["tests/test_config_guard.py", "tests/test_hooks.py"])

    def test_a_path_through_a_symlink_to_the_root_counts_as_inside(self):
        link = Path(tempfile.mkdtemp(prefix="gw-tests-for-link-")) / "repo"
        self.addCleanup(shutil.rmtree, link.parent, True)
        link.symlink_to(self.tmp, target_is_directory=True)
        code, out, err = self.run_cli(str(link / "scripts" / "config-guard.py"))
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines(), ["tests/test_config_guard.py", "tests/test_hooks.py"])
        code, out, err = self.run_cli(str(link.parent / "elsewhere.py"))
        self.assertEqual(code, 2)
        self.assertIn("is outside the project", err)

    def test_path_placeholder_and_contains(self):
        self.write("tests/test_a.py", "MAIL = 'someone@example.org'\n")
        code, out, err = self.run_cli("tests/test_a.py", "tests/test_b c.py")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines(), ["tests/test_a.py", "tests/test_b c.py", "tests/test_private.py"])

    def test_contains_never_matches_a_deleted_file(self):
        code, out, err = self.run_cli("tests/gone.py")
        self.assertEqual((code, out), (0, ""), err)

    def test_absolute_and_relative_to_the_current_directory(self):
        code, out, _ = self.run_cli(str(self.tmp / "scripts" / "config-guard.py"))
        self.assertIn("tests/test_config_guard.py", out.splitlines())
        code, out, _ = self.run_cli("config-guard.py", cwd=self.tmp / "scripts")
        self.assertIn("tests/test_config_guard.py", out.splitlines())

    def test_file_outside_the_project_is_an_error(self):
        code, out, err = self.run_cli("/etc/hosts")
        self.assertEqual(code, 2)
        self.assertIn("/etc/hosts is outside the project", err)

    def test_unknown_placeholder_is_an_error(self):
        self.configure([{"paths": "^scripts/", "tests": ["tests/test_{nope}.py"]}], "")
        code, out, err = self.run_cli("scripts/config-guard.py")
        self.assertEqual(code, 2)
        self.assertIn("{nope} in 'tests/test_{nope}.py' names no group", err)

    def test_diff_adds_changed_and_untracked_files(self):
        self.write("scripts/config-guard.py", "y\n")
        self.write("tests/test_a.py", "z\n")  # tracked and changed
        self.git("add", "tests/test_a.py"); self.git("commit", "-qm", "change")
        code, out, err = self.run_cli("--diff", "HEAD~1")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines(), ["tests/test_a.py", "tests/test_config_guard.py", "tests/test_hooks.py"])
        self.write("tests/test_new.py", "x\n")  # untracked
        code, out, _ = self.run_cli("--diff", "HEAD")
        self.assertIn("tests/test_new.py", out.splitlines())

    def test_diff_against_an_unknown_ref(self):
        code, out, err = self.run_cli("--diff", "nope")
        self.assertEqual(code, 2)
        self.assertIn("cannot diff against 'nope'", err)

    def test_run_without_command_fails_closed(self):
        code, out, err = self.run_cli("--run", "scripts/config-guard.py")
        self.assertEqual(code, 2)
        self.assertIn("testMap.command is empty", err)

    def test_run_quotes_the_files_and_returns_their_exit_code(self):
        self.configure(RULES, "printf '<%s>' {files} > ran.txt; exit 3")
        code, out, err = self.run_cli("--run", "tests/test_b c.py", "tests/test_a.py")
        self.assertEqual(code, 3, err)
        self.assertEqual((self.tmp / "ran.txt").read_text(), "<tests/test_a.py><tests/test_b c.py>")

    def test_plain_unittest_command_goes_through_test_run_in_parallel(self):  # B33
        self.write("tests/test_p.py", "import unittest\nclass A(unittest.TestCase):\n    def test_ok(self): pass\n"
                   "class B(unittest.TestCase):\n    def test_ok(self): pass\n")
        self.write("tests/test_f.py", "import unittest\nclass C(unittest.TestCase):\n    def test_bad(self): self.fail('boom-marker')\n")
        self.configure(RULES, "PYTHONPATH=tests python3 -B -m unittest {files}")
        code, out, err = self.run_cli("--run", "tests/test_p.py")
        self.assertEqual(code, 0, out + err)
        self.assertIn("test-run.py: 1 test files, 2 units", out)
        self.assertNotIn("tests-for: PYTHONPATH", out)  # not the serial command
        code, out, err = self.run_cli("--run", "tests/test_p.py", "tests/test_f.py")
        self.assertEqual(code, 1, out + err)
        self.assertIn("boom-marker", out)
        self.assertIn("FAILED (tests/test_f.py::C)", out)

    def test_another_command_is_still_run_as_configured(self):  # B33
        self.configure(RULES, "printf serial > ran.txt")
        code, out, err = self.run_cli("--run", "tests/test_a.py")
        self.assertEqual((code, (self.tmp / "ran.txt").read_text()), (0, "serial"), err)
        self.assertNotIn("test-run.py", out)

    def test_run_with_nothing_to_run(self):
        self.configure(RULES, "exit 9")
        code, out, err = self.run_cli("--run", "README.md")
        self.assertEqual(code, 0, err)
        self.assertIn("nothing to run", out)

    def test_no_rules_says_so(self):
        self.configure([], "")
        code, out, err = self.run_cli("scripts/config-guard.py")
        self.assertEqual((code, out), (0, ""))
        self.assertIn("testMap.rules is empty", err)

    def test_invalid_regex_fails_closed(self):
        self.configure([{"paths": "^scripts/", "contains": "(", "tests": ["x"]}], "")
        code, out, err = self.run_cli("scripts/config-guard.py")
        self.assertEqual(code, 2)
        self.assertIn("$.testMap.rules[0].contains: '(' is not a valid regex", err)


class ThisRepo(unittest.TestCase):
    """The map of the workflow's own repo (retro 0.5.0 R2)."""

    def test_a_script_calls_for_its_test_and_the_copies_and_hooks(self):
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(ROOT), "scripts/config-guard.py"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.splitlines(),
                         ["tests/test_config_guard.py", "tests/test_hooks.py", "tests/test_reviewed.py"])


if __name__ == "__main__":
    unittest.main()
