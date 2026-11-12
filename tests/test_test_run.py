"""scripts/test-run.py (E45): the suites in parallel, one test class per process. Every failing case checks the
message, not only the exit code."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT

sys.dont_write_bytecode = True
SCRIPT = ROOT / "scripts" / "test-run.py"
TWO_CLASSES = (
    "import unittest\n"
    "class Alpha(unittest.TestCase):\n"
    "    def test_one(self): pass\n"
    "    def test_two(self): pass\n"
    "class Beta(Alpha):\n"  # inherits Alpha's tests: its own unit, with its own ids
    "    def test_three(self): pass\n"
)


class TestRun(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-test-run-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        subprocess.run(["git", "-C", str(self.tmp), "init", "-q"], check=True)
        self.configure()
        self.write("tests/test_a.py", TWO_CLASSES)
        self.write("tests/test_b.py", "import unittest\nclass Gamma(unittest.TestCase):\n    def test_x(self): pass\n")

    def write(self, rel, text):
        (self.tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.tmp / rel).write_text(text)

    def configure(self, **extra):
        self.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, **extra), indent=2) + "\n")

    def run_cli(self, *args):
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(self.tmp), *args],
                           capture_output=True, text=True, cwd=str(self.tmp))
        return r.returncode, r.stdout, r.stderr

    def times(self):
        return json.loads((self.tmp / ".git" / "gw" / "test-times.json").read_text())

    def test_every_class_runs_once_and_the_total_matches(self):
        code, out, err = self.run_cli("tests", "--jobs", "2", "--times", "9")
        self.assertEqual(code, 0, out + err)
        # Alpha 2 + Beta 3 (2 inherited) + Gamma 1.
        self.assertIn("test-run: 6 tests in 3 units, 2 jobs", out)
        self.assertTrue(out.rstrip().endswith(": OK"), out)
        for unit in ("tests/test_a.py::Alpha", "tests/test_a.py::Beta", "tests/test_b.py::Gamma"):
            self.assertIn(unit, out)  # --times lists them
        self.assertEqual(set(self.times()), {"tests/test_a.py::Alpha", "tests/test_a.py::Beta",
                                             "tests/test_b.py::Gamma"})

    def test_default_folders_are_tests_and_skill_scripts(self):
        self.write("skills/s/scripts/test_s.py", "import unittest\nclass S(unittest.TestCase):\n    def test_s(self): pass\n")
        subprocess.run(["git", "-C", str(self.tmp), "add", "-A"], check=True)
        code, out, err = self.run_cli("--times", "9")
        self.assertEqual(code, 0, out + err)
        self.assertIn("test-run: 7 tests in 4 units", out)
        self.assertIn("skills/s/scripts/test_s.py::S", out)

    def test_a_failing_test_fails_the_run_and_shows_its_output(self):
        self.write("tests/test_b.py", "import unittest\nclass Gamma(unittest.TestCase):\n"
                                      "    def test_x(self): self.assertEqual(1, 2, 'GAMMA BROKE')\n")
        code, out, err = self.run_cli("tests")
        self.assertEqual(code, 1, out + err)
        self.assertIn("---- tests/test_b.py::Gamma (exit 1)", out)
        self.assertIn("GAMMA BROKE", out)
        self.assertIn("FAILED (tests/test_b.py::Gamma)", out)

    def test_a_file_that_does_not_import_runs_whole_and_fails(self):
        self.write("tests/test_c.py", "import no_such_module_here\n")
        code, out, err = self.run_cli("tests")
        self.assertEqual(code, 1, out + err)
        self.assertIn("---- tests/test_c.py (exit 1)", out)
        self.assertIn("no_such_module_here", out)
        self.assertIn("FAILED (tests/test_c.py)", out)

    def test_a_total_that_does_not_match_fails(self):
        # The class grows a test only in the per-class run (its command line carries -k), so that run counts one more
        # test than discovery did: the totals differ though every unit passed.
        self.write("tests/test_b.py", "import sys, unittest\nclass Gamma(unittest.TestCase):\n    def test_x(self): pass\n"
                                      "if '-k' in sys.argv:\n    Gamma.test_y = lambda self: None\n")
        code, out, err = self.run_cli("tests")
        self.assertEqual(code, 1, out + err)
        self.assertIn("ran 7 tests, discovered 6", out)

    def test_the_slowest_unit_by_the_last_run_goes_first(self):
        (self.tmp / ".git" / "gw").mkdir(parents=True)
        (self.tmp / ".git" / "gw" / "test-times.json").write_text(json.dumps(
            {"tests/test_b.py::Gamma": 99.0, "tests/test_a.py::Alpha": 1.0, "tests/test_a.py::Beta": 2.0}))
        self.write("tests/test_b.py", "import unittest\nclass Gamma(unittest.TestCase):\n"
                                      "    def test_x(self): self.fail('ORDER')\n")
        self.write("tests/test_a.py", TWO_CLASSES.replace("pass", "self.fail('ORDER')"))
        code, out, err = self.run_cli("tests", "--jobs", "1")
        self.assertEqual(code, 1, out + err)
        order = [line for line in out.splitlines() if line.startswith("---- ")]
        self.assertEqual(order, ["---- tests/test_b.py::Gamma (exit 1)", "---- tests/test_a.py::Beta (exit 1)",
                                 "---- tests/test_a.py::Alpha (exit 1)"])

    def test_a_broken_times_cache_only_costs_the_order(self):
        (self.tmp / ".git" / "gw").mkdir(parents=True)
        (self.tmp / ".git" / "gw" / "test-times.json").write_text("not json")
        code, out, err = self.run_cli("tests")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(len(self.times()), 3)

    def test_bad_test_jobs_is_refused(self):
        self.configure(testJobs=-1)
        code, out, err = self.run_cli("tests")
        self.assertEqual(code, 2)
        self.assertIn("$.testJobs: must be at least 0", err)  # the schema refuses it
        self.configure()
        code, out, err = self.run_cli("tests", "--jobs", "-1")
        self.assertEqual(code, 2)
        self.assertIn("testJobs must be an integer >= 0", err)

    def test_a_folder_that_is_not_there_is_refused(self):
        code, out, err = self.run_cli("nowhere")
        self.assertEqual(code, 2)
        self.assertIn("nowhere is not a folder of", err)

    def test_test_jobs_zero_is_one_per_cpu(self):
        code, out, err = self.run_cli("tests")
        self.assertEqual(code, 0, out + err)
        self.assertIn(f"{os.cpu_count()} jobs", out)


if __name__ == "__main__":
    unittest.main()
