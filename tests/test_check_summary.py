"""scripts/check.sh: the summary of the run, the log file and the --quiet mode (trimmed output of what fails).
Each case runs the real script in a temporary git repo with its own `check` list."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent


class CheckSummary(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-check-summary-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "repo"
        shutil.copytree(ROOT / "scripts", self.repo / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(ROOT / "schema" / "gw.schema.json", self.repo / "scripts" / "gw.schema.json")
        self.git("init", "-q")
        self.git("config", "user.name", "t")
        self.git("config", "user.email", "t@example.com")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, text=True, check=True)

    def configure(self, check, wrapper=""):
        cfg = {"version": "0.4.3", "schemaVersion": 1, "language": "en", "protectedBranch": "main",
               "pushToProtected": "direct", "content": ["^docs/"], "check": check, "checkWrapper": wrapper}
        (self.repo / ".claude").mkdir(exist_ok=True)
        (self.repo / ".claude" / "gw.json").write_text(json.dumps(cfg))
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "x")

    def run_check(self, *args, env=None):
        full = dict(os.environ, GW_CHECK_CACHE="0")
        full.pop("GW_CHECK_QUIET", None)
        full.update(env or {})
        r = subprocess.run(["bash", str(self.repo / "scripts" / "check.sh"), *args], capture_output=True, text=True,
                           env=full, stdin=subprocess.DEVNULL)
        return r.returncode, r.stdout, r.stderr

    def log(self):
        return (self.repo / ".git" / "gw-check.log").read_text()

    def test_green_run_streams_and_prints_one_ok_line_per_command(self):
        self.configure(["echo first-output", "echo second-output"])
        code, out, err = self.run_check()
        self.assertEqual(code, 0, out + err)
        self.assertIn("first-output", out)
        summary = out.split("check: summary")[1]
        self.assertRegex(summary, r"ok +\d+s +echo first-output\n")
        self.assertRegex(summary, r"ok +\d+s +echo second-output\n")
        self.assertIn("check: all green", out)

    def test_the_log_keeps_the_full_output_of_every_command(self):
        self.configure(["echo first-output", "echo to-stderr >&2"])
        self.assertEqual(self.run_check()[0], 0)
        log = self.log()
        self.assertIn("== echo first-output\nfirst-output\n", log)
        self.assertIn("== echo to-stderr >&2\nto-stderr\n", log)

    def test_a_failure_stops_the_run_and_the_summary_names_it_with_its_exit_code(self):
        self.configure(["echo one", "echo boom; exit 3", "echo never-reached"])
        code, out, err = self.run_check()
        self.assertEqual(code, 1, out + err)
        summary = out.split("check: summary")[1]
        self.assertRegex(summary, r"ok +\d+s +echo one\n")
        self.assertRegex(summary, r"FAILED +\d+s +echo boom; exit 3 \(exit 3\)\n")
        self.assertNotIn("never-reached", out + err)
        self.assertIn("failed: 'echo boom; exit 3'", err)
        self.assertIn("full output: " + str(self.repo / ".git" / "gw-check.log"), out)

    def test_quiet_hides_a_passing_command_and_shows_only_the_tail_of_the_failing_one(self):
        self.configure(["echo passing-$((6*7))", "for i in $(seq 1 100); do echo line-$i; done; exit 2"])
        code, out, err = self.run_check("--quiet", env={"GW_CHECK_TAIL": "5"})
        self.assertEqual(code, 1, out + err)
        self.assertNotIn("passing-42", out)
        self.assertIn("last 5 lines of the failed command", out)
        self.assertIn("line-100\n", out)
        self.assertIn("line-96\n", out)
        self.assertNotIn("line-95\n", out)
        self.assertIn("line-1\n", self.log())  # the log is complete
        self.assertIn("passing-42", self.log())
        self.assertIn("failed: ", err)

    def test_quiet_green_run_prints_no_command_output(self):
        self.configure(["echo noisy-$((6*7))"])
        code, out, err = self.run_check(env={"GW_CHECK_QUIET": "1"})
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("noisy-42", out)
        self.assertRegex(out, r"ok +\d+s +echo noisy-")

    def test_a_bad_argument_fails_with_the_usage(self):
        self.configure(["true"])
        code, out, err = self.run_check("--loud")
        self.assertEqual(code, 2, out + err)
        self.assertIn("unexpected argument '--loud'; usage: bash", err)

    def test_an_unwritable_log_warns_and_the_check_still_runs(self):
        self.configure(["echo still-runs"])
        code, out, err = self.run_check(env={"GW_CHECK_LOG": str(self.tmp / "no-dir" / "x.log")})
        self.assertEqual(code, 0, out + err)
        self.assertIn("cannot write the log", err)
        self.assertIn("still-runs", out)

    def test_a_green_run_still_records_the_tree_for_the_pre_push(self):
        self.configure(["echo ok"])
        code, out, err = self.run_check(env={"GW_CHECK_CACHE": ""})
        self.assertEqual(code, 0, out + err)
        self.assertIn("the next push of this same tree will skip the check", out)
        self.assertEqual(len((self.repo / ".git" / "gw-check-green").read_text().splitlines()), 1)

    def test_the_log_inside_the_git_dir_does_not_change_the_recorded_tree(self):
        self.configure(["echo ok"])
        code, out, err = self.run_check(env={"GW_CHECK_CACHE": ""})
        self.assertNotIn("work tree changed", out + err)


if __name__ == "__main__":
    unittest.main()
