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

    # E35: the flaky registry. A class that fails only while its marker file is missing, then creates it.
    def flaky_test(self, fails=1):
        marker = self.tmp / "marker"
        self.write("tests/test_b.py", "import unittest\nfrom pathlib import Path\nclass Gamma(unittest.TestCase):\n"
                   "    def test_x(self):\n"
                   f"        m = Path({str(marker)!r}); n = int(m.read_text()) if m.exists() else 0\n"
                   "        m.write_text(str(n + 1))\n"
                   f"        self.assertGreaterEqual(n, {fails}, 'FLAKY FIRST')\n")
        return marker

    def registry(self):
        path = self.tmp / ".git" / "gw" / "flaky.jsonl"
        return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []

    def test_a_unit_that_passes_on_retry_is_recorded_and_reported(self):
        self.flaky_test()
        code, out, err = self.run_cli("tests")
        self.assertEqual(code, 0, out + err)
        self.assertIn("test-run: flaky: tests/test_b.py::Gamma (passed on retry; 1 times recorded)", out)
        self.assertNotIn("fix it", out)
        self.assertTrue(out.rstrip().endswith(": OK"), out)
        (rec,) = self.registry()
        self.assertEqual(rec["unit"], "tests/test_b.py::Gamma")
        self.assertIn("FLAKY FIRST", rec["output"])
        self.assertRegex(rec["date"], r"^\d{4}-\d\d-\d\dT")
        self.assertRegex(rec["commit"], r"^$|^[0-9a-f]{7,}$")  # an empty repo has no HEAD yet

    def test_a_unit_that_fails_twice_is_a_normal_failure_with_both_outputs(self):
        self.flaky_test(fails=5)
        code, out, err = self.run_cli("tests")
        self.assertEqual(code, 1, out + err)
        self.assertIn("FAILED (tests/test_b.py::Gamma)", out)
        self.assertIn("--- run 1 of 2", out)
        self.assertIn("--- run 2 of 2", out)
        self.assertNotIn("flaky:", out)
        self.assertEqual(self.registry(), [])

    def test_retries_zero_neither_retries_nor_records(self):
        marker = self.flaky_test()
        self.configure(flaky={"retries": 0})
        code, out, err = self.run_cli("tests")
        self.assertEqual(code, 1, out + err)
        self.assertEqual(marker.read_text(), "1")  # run once
        self.assertEqual(self.registry(), [])

    def test_the_proposal_appears_at_propose_after(self):
        self.configure(flaky={"proposeAfter": 2})
        for n in (1, 2):
            if (self.tmp / "marker").exists():
                (self.tmp / "marker").unlink()
            self.flaky_test()
            code, out, err = self.run_cli("tests")
            self.assertEqual(code, 0, out + err)
            self.assertIn(f"passed on retry; {n} times recorded)", out)
            self.assertEqual("fix it" in out, n == 2, out)
        self.assertIn("unittest discover -s tests -p test_b.py -k '*.Gamma.*' -v", out)

    def test_a_bad_flaky_config_is_refused_with_its_reason(self):
        for bad, reason in (({"retries": -1}, "$.flaky.retries: must be at least 0"),
                            ({"proposeAfter": 0}, "$.flaky.proposeAfter: must be at least 1"),
                            ({"retries": "1"}, "$.flaky.retries"), ({"other": 1}, "$.flaky")):
            self.configure(flaky=bad)
            code, out, err = self.run_cli("tests")
            self.assertEqual(code, 2, out + err)
            self.assertIn(reason, err)

    def test_without_a_git_common_dir_the_flaky_unit_still_passes(self):
        import contextlib
        import importlib.util
        import io
        spec = importlib.util.spec_from_file_location("test_run_under_test", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.times_path = lambda root: None  # what `git rev-parse --git-common-dir` failing gives
        self.flaky_test()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = mod.main(["tests", "--root", str(self.tmp)])
        self.assertEqual(code, 0, out.getvalue())
        self.assertIn("passed on retry; 0 times recorded)", out.getvalue())
        self.assertEqual(self.registry(), [])


if __name__ == "__main__":
    unittest.main()
