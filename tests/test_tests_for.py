"""scripts/tests-for.py (E21): the test files a change calls for, from testMap in .claude/gw.json. Every failing case
checks the message, not only the exit code."""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import waits
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
        self.configure(RULES, "python3 -B -m unittest {files}")
        code, out, err = self.run_cli("--run", "tests/test_p.py")
        self.assertEqual(code, 0, out + err)
        self.assertIn("test-run.py: 1 test files, 2 units", out)
        self.assertNotIn("tests-for: PYTHONPATH", out)  # not the serial command
        code, out, err = self.run_cli("--run", "tests/test_p.py", "tests/test_f.py")
        self.assertEqual(code, 1, out + err)
        self.assertIn("boom-marker", out)
        self.assertIn("FAILED (tests/test_f.py::C)", out)

    def configure_timeout(self, seconds, command="python3 -B -m unittest {files}"):
        cfg = json.loads((self.tmp / ".claude" / "gw.json").read_text())
        cfg.update(testUnitTimeout=seconds, testMap={"rules": RULES, "command": command})
        self.write(".claude/gw.json", json.dumps(cfg))

    @staticmethod
    def pid_writer(path):
        """Test-file lines that write `<unit pid> <child pid>` to `path` at once (atomic: never read half-written)."""
        return (f"        open({str(path)!r} + '.tmp', 'w').write(f'{{os.getpid()}} {{p.pid}}')\n"
                f"        os.rename({str(path)!r} + '.tmp', {str(path)!r})\n")

    def test_a_unit_past_its_timeout_is_killed_and_named_with_the_command_to_run_it_alone(self):  # B42
        pids = self.tmp / "pids"
        self.write("tests/test_h.py", "import os, subprocess, time, unittest\n"
                   "class Hang(unittest.TestCase):\n    def test_hang(self):\n"
                   "        p = subprocess.Popen(['sleep', '60'])\n" + self.pid_writer(pids) +
                   "        time.sleep(60)\n"
                   "class Fine(unittest.TestCase):\n    def test_ok(self): pass\n")
        limit = max(5, int(waits.timeout(5)))  # room to start on a loaded runner before it writes the pids
        self.configure_timeout(limit, "PYTHONPATH=tests python3 -B -m unittest {files}")  # review n.º 5: the prefix
        started = time.monotonic()
        code, out, err = self.run_cli("--run", "tests/test_h.py")
        self.assertLess(time.monotonic() - started, limit + waits.timeout(40), out + err)
        self.assertEqual(code, 1, out + err)
        self.assertIn(f"tests-for: tests/test_h.py::Hang did not end within {limit}s (testUnitTimeout in "
                      ".claude/gw.json); run it alone to see which test hangs: PYTHONPATH=tests python3 -B -m "
                      "unittest discover -s tests -p test_h.py -k '*.Hang.*' -v", out)
        self.assertIn("FAILED (tests/test_h.py::Hang timed out)", out)
        self.assertNotIn("Fine", out.split("FAILED")[1])
        self.assertTrue(pids.exists(), f"the unit did not start within {limit}s: {out}")
        alive = [pid for pid in map(int, pids.read_text().split()) if self.alive(pid)]
        self.assertEqual(alive, [], "the unit and its child are killed with their group")

    @staticmethod
    def alive(pid):  # a zombie counts as gone: in a container nobody may reap it
        r = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True)
        return r.returncode == 0 and r.stdout.strip() != "" and not r.stdout.strip().startswith("Z")

    def test_a_process_left_holding_the_output_does_not_keep_the_run_waiting(self):  # B42
        pid = self.tmp / "pid"
        self.write("tests/test_l.py", "import subprocess, unittest\n"
                   "class Leave(unittest.TestCase):\n    def test_leave(self):\n"
                   "        p = subprocess.Popen(['sleep', '60'], start_new_session=True)  # out of the unit's group\n"
                   f"        open({str(pid)!r}, 'w').write(str(p.pid))\n")
        self.configure_timeout(0)
        started = time.monotonic()
        code, out, err = self.run_cli("--run", "tests/test_l.py")
        left = int(pid.read_text())
        self.addCleanup(lambda: subprocess.run(["kill", "-9", str(left)], capture_output=True))
        self.assertEqual(code, 0, out + err)
        self.assertIn("tests-for: OK", out)
        self.assertLess(time.monotonic() - started, waits.timeout(30), "waited for the sleep holding the output")
        self.assertTrue(self.alive(left), "the test's process outlived the unit, as it should for this case")

    def test_what_a_passing_unit_leaves_in_its_group_is_killed_when_it_ends(self):  # review B42 n.º 2
        pids = self.tmp / "pids"
        self.write("tests/test_k.py", "import os, subprocess, unittest\n"
                   "class Keep(unittest.TestCase):\n    def test_keep(self):\n"
                   "        p = subprocess.Popen(['sleep', '60'], stdout=subprocess.DEVNULL)  # in the unit's group\n"
                   + self.pid_writer(pids))
        self.configure_timeout(0)
        code, out, err = self.run_cli("--run", "tests/test_k.py")
        self.assertEqual(code, 0, out + err)
        child = int(pids.read_text().split()[1])
        self.addCleanup(subprocess.run, ["kill", "-9", str(child)], capture_output=True)
        self.assertTrue(waits.wait_for(lambda: not self.alive(child), 10), "the unit's leftover sleep survived it")

    def module(self):
        spec = importlib.util.spec_from_file_location("gw_tests_for", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_no_unit_starts_once_tests_for_is_stopping(self):  # review B42 n.º 1: the stop and a starting unit
        mod = self.module()
        mod.STOPPING.set()
        marker = self.tmp / "ran"
        self.write("tests/test_m.py", f"import unittest\nopen({str(marker)!r}, 'w').write('x')\n"
                   "class M(unittest.TestCase):\n    def test_m(self): pass\n")
        unit, code, _secs, ran, output = mod.run_unit(self.tmp, ("tests", "test_m.py", "M", 1), 0, re.compile("x"))
        self.assertEqual((code, ran, output), (-1, 0, "not started: tests-for was stopped"))
        self.assertFalse(marker.exists(), "the unit ran after the stop")
        self.assertEqual(mod.LIVE, set())

    def test_an_invalid_unit_timeout_fails_closed_in_run_parallel_too(self):  # review B42 n.º 6
        mod = self.module()
        for bad in (-1, "x", True):
            with self.subTest(bad=bad):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    code = mod.run_parallel(self.tmp, {"testUnitTimeout": bad}, ["tests/test_a.py"])
                self.assertEqual(code, 2)
                self.assertIn(f"tests-for: testUnitTimeout must be an integer >= 0 (seconds; 0 = no limit), got {bad!r}; "
                              "fix .claude/gw.json", err.getvalue())

    def test_stopping_tests_for_kills_the_units_it_started(self):  # B42: they run in sessions of their own
        pids = self.tmp / "pids"
        self.write("tests/test_s.py", "import os, subprocess, time, unittest\n"
                   "class Slow(unittest.TestCase):\n    def test_slow(self):\n"
                   "        p = subprocess.Popen(['sleep', '60'])\n" + self.pid_writer(pids) +
                   "        time.sleep(60)\n")
        self.configure_timeout(0)

        def ignore_sigint():  # review n.º 4: launched with `cmd &` by a non-interactive shell, SIGINT comes ignored
            signal.signal(signal.SIGINT, signal.SIG_IGN)
        for sig, preexec in ((signal.SIGTERM, None), (signal.SIGINT, None), (signal.SIGINT, ignore_sigint)):
            with self.subTest(sig=sig.name, inherited_ignore=preexec is not None):
                pids.unlink() if pids.exists() else None
                proc = subprocess.Popen([sys.executable, "-B", str(SCRIPT), "--root", str(self.tmp), "--run",
                                         "tests/test_s.py"], cwd=str(self.tmp), stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL, preexec_fn=preexec)
                self.addCleanup(proc.wait)  # review n.º 9: reaped even if an assertion fails first
                self.addCleanup(proc.kill)
                self.assertTrue(waits.wait_for(pids.exists, 30), "the unit never started")
                started = [int(x) for x in pids.read_text().split()]
                for pid in started:
                    self.addCleanup(subprocess.run, ["kill", "-9", str(pid)], capture_output=True)
                proc.send_signal(sig)
                proc.wait(timeout=waits.timeout(30))
                gone = waits.wait_for(lambda: not any(self.alive(pid) for pid in started), 10)
                self.assertTrue(gone, f"left running after {sig.name}: {[x for x in started if self.alive(x)]}")

    def test_an_invalid_unit_timeout_fails_closed(self):  # B42
        self.write("tests/test_p.py", "import unittest\nclass A(unittest.TestCase):\n    def test_ok(self): pass\n")
        self.configure_timeout(-1)
        code, out, err = self.run_cli("--run", "tests/test_p.py")
        self.assertEqual(code, 2, out + err)
        self.assertIn("$.testUnitTimeout: must be at least 0", err)

    def test_a_file_test_run_cannot_discover_fails_closed(self):  # B33 review: 0 units must not be a green
        self.write("tests/check_x.py", "import unittest\nclass A(unittest.TestCase):\n    def test_bad(self): self.fail('x')\n")
        self.configure([{"paths": "^src/", "tests": ["tests/check_x.py"]}], "python3 -B -m unittest {files}")
        self.write("src/a.py", "x\n")
        code, out, err = self.run_cli("--run", "src/a.py")
        self.assertEqual(code, 2, out + err)
        self.assertIn("tests/check_x.py is not a test_*.py test-run.py can discover", err)
        self.assertNotIn("tests-for: OK", out)

    def test_an_env_prefix_or_other_interpreter_runs_the_command_as_configured(self):  # B33 review
        self.write("tests/test_p.py", "import unittest\nclass A(unittest.TestCase):\n    def test_ok(self): pass\n")
        for command in ("FOO=1 python3 -B -m unittest {files}", ".venv/bin/python -m unittest {files}"):
            self.configure(RULES, command)
            code, out, err = self.run_cli("--run", "tests/test_p.py")
            self.assertNotIn("test-run.py", out, command)
            self.assertIn(f"tests-for: {command.split('{')[0]}", out)

    def test_a_pythonpath_prefix_still_goes_parallel_and_reaches_the_tests(self):  # B33 review
        self.write("lib/mod.py", "VALUE = 7\n")
        self.write("tests/test_m.py", "import unittest\nimport mod\nclass M(unittest.TestCase):\n"
                   "    def test_v(self): self.assertEqual(mod.VALUE, 7)\n")
        self.configure(RULES, "PYTHONPATH=lib python3 -B -m unittest {files}")
        code, out, err = self.run_cli("--run", "tests/test_m.py")
        self.assertEqual(code, 0, out + err)
        self.assertIn("test-run.py: 1 test files, 1 units", out)
        self.configure(RULES, "python3 -B -m unittest {files}")  # without it the import fails: the rest is not hiding it
        code, out, err = self.run_cli("--run", "tests/test_m.py")
        self.assertEqual(code, 1, out + err)
        self.assertIn("No module named 'mod'", out)

    def test_a_test_run_that_does_not_load_is_cannot_run(self):  # B33 review
        scripts = self.tmp / "gw-copy" / "scripts"
        shutil.copytree(ROOT / "scripts", scripts, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "schema", scripts.parent / "schema")
        (scripts / "test-run.py").write_text("raise RuntimeError('broken-marker')\n")
        self.configure(RULES, "python3 -B -m unittest {files}")
        r = subprocess.run([sys.executable, "-B", str(scripts / "tests-for.py"), "--root", str(self.tmp), "--run",
                            "tests/test_a.py"], capture_output=True, text=True, cwd=str(self.tmp))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("cannot load test-run.py (broken-marker); reinstall the workflow: /gw-update", r.stderr)

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


class ShellcheckStep(unittest.TestCase):  # D106
    git, write, configure, run_cli = TestsFor.git, TestsFor.write, TestsFor.configure, TestsFor.run_cli

    def setUp(self):
        TestsFor.setUp(self)
        self.configure(RULES, "true {files}")

    def env_run(self, *args, path=None, **env):
        e = {**os.environ, "CI": "", "CLAUDE_CODE_REMOTE": "", **env}
        if path is not None:
            e["PATH"] = path
        r = subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(self.tmp), *args],
                           capture_output=True, text=True, cwd=str(self.tmp), env=e)
        return r.returncode, r.stdout, r.stderr

    def test_no_sh_changed_no_step(self):
        code, out, _ = self.env_run("--run", "scripts/config-guard.py")
        self.assertNotIn("shellcheck", out)

    @unittest.skipUnless(shutil.which("shellcheck"), "shellcheck not installed")
    def test_warning_fails_with_reason_and_spaces_work(self):
        self.write("scripts/a b.sh", "#!/bin/bash\necho $1\n")
        code, out, _ = self.env_run("--run", "scripts/a b.sh")
        self.assertEqual(code, 1)
        self.assertIn("SC2086", out + _)
        self.assertIn("FAILED (shellcheck", out)

    @unittest.skipUnless(shutil.which("shellcheck"), "shellcheck not installed")
    def test_clean_sh_passes(self):
        self.write("scripts/ok.sh", "#!/bin/bash\necho \"$1\"\n")
        self.assertEqual(self.env_run("--run", "scripts/ok.sh")[0], 0)

    def test_deleted_sh_is_skipped(self):
        code, out, _ = self.env_run("--run", "scripts/gone.sh")
        self.assertEqual(code, 0)
        self.assertNotIn("shellcheck", out)

    def test_missing_shellcheck_warns_locally_and_fails_in_ci(self):
        self.write("scripts/ok.sh", "#!/bin/bash\n")
        nobin = self.tmp / "nobin"  # git and bash, but no shellcheck
        nobin.mkdir()
        for tool in ("git", "bash"):
            (nobin / tool).symlink_to(shutil.which(tool))
        empty = str(nobin)
        code, out, err = self.env_run("--run", "scripts/ok.sh", path=empty)
        self.assertEqual(code, 0, err + out)
        self.assertIn("pip install shellcheck-py", out)
        code, out, err = self.env_run("--run", "scripts/ok.sh", path=empty, CI="true")
        self.assertEqual(code, 1)
        self.assertIn("pip install shellcheck-py", err)

    def ran(self):
        return (self.tmp / "ran.txt").is_file()

    def test_a_shellcheck_failure_stops_before_the_tests(self):  # D116
        self.write("tests/shellcheck.sh", "echo \"SC9999 in $*\"; exit 1\n")
        self.write("scripts/config-guard.sh", "#!/bin/bash\n")
        self.configure(RULES, "touch ran.txt {files}")
        code, out, err = self.env_run("--run", "scripts/config-guard.sh")
        self.assertEqual(code, 1, out + err)
        self.assertIn("SC9999 in scripts/config-guard.sh", out)
        self.assertIn("shellcheck failed, so the tests were not run", out)
        self.assertFalse(self.ran())
        self.assertLess(out.index("tests-for: shellcheck scripts/"), out.index("FAILED (shellcheck"))

    def test_a_clean_shellcheck_runs_first_then_the_tests(self):  # D116
        self.write("tests/shellcheck.sh", "echo checked-marker\n")
        self.write("scripts/config-guard.sh", "#!/bin/bash\n")
        self.configure(RULES, "echo tests-marker; touch ran.txt {files}")
        code, out, err = self.env_run("--run", "scripts/config-guard.sh")
        self.assertEqual(code, 0, out + err)
        self.assertLess(out.index("checked-marker"), out.index("tests-marker"))

    def test_no_sh_or_a_deleted_sh_still_runs_the_tests(self):  # D116
        self.configure(RULES, "touch ran.txt {files}")
        for changed in ("scripts/config-guard.py", "scripts/config-guard.sh"):  # the .sh does not exist
            if self.ran():
                (self.tmp / "ran.txt").unlink()
            code, out, err = self.env_run("--run", changed)
            self.assertEqual(code, 0, out + err)
            self.assertNotIn("shellcheck", out)
            self.assertTrue(self.ran(), changed)

    def test_a_missing_binary_warns_then_runs_the_tests_but_stops_in_ci(self):  # D116
        self.write("scripts/config-guard.sh", "#!/bin/bash\n")
        self.configure(RULES, "touch ran.txt {files}")
        nobin = self.tmp / "nobin"
        nobin.mkdir()
        for tool in ("git", "bash", "touch"):
            (nobin / tool).symlink_to(shutil.which(tool))
        code, out, err = self.env_run("--run", "scripts/config-guard.sh", path=str(nobin))
        self.assertEqual(code, 0, out + err)
        self.assertIn("shellcheck not installed locally", out)
        self.assertTrue(self.ran())
        (self.tmp / "ran.txt").unlink()
        code, out, err = self.env_run("--run", "scripts/config-guard.sh", path=str(nobin), CI="true")
        self.assertEqual(code, 1, out + err)
        self.assertIn("shellcheck is missing and the check needs it", err)
        self.assertIn("shellcheck failed, so the tests were not run", out)
        self.assertFalse(self.ran())

    def test_without_run_lists_the_step(self):
        self.write("scripts/a b.sh", "x\n")
        code, out, err = self.run_cli("scripts/a b.sh")
        self.assertEqual(code, 0)
        self.assertIn("shellcheck: scripts/a b.sh", err)
        # stdout stays test names only: tests/old-python.sh feeds it to unittest (E22)
        self.assertNotIn("shellcheck", out)


class Why(unittest.TestCase):  # D118
    git, write, configure, run_cli = TestsFor.git, TestsFor.write, TestsFor.configure, TestsFor.run_cli

    def setUp(self):
        TestsFor.setUp(self)

    def test_rule_with_a_named_group(self):
        code, out, err = self.run_cli("--why", "scripts/config-guard.py")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines(), ["tests/test_config_guard.py", "tests/test_hooks.py"])  # stdout unchanged
        self.assertEqual(err.splitlines(), [
            "why: tests/test_config_guard.py <- scripts/config-guard.py (rule 0: ^scripts/(?P<name>[^/]+)\\.(py|sh)$)",
            "why: tests/test_hooks.py <- scripts/config-guard.py (rule 1: ^scripts/)",
        ])

    def test_two_changed_files_bring_the_same_test(self):
        code, out, err = self.run_cli("--why", "scripts/y.py", "scripts/x.py")
        self.assertEqual(code, 0, err)
        self.assertEqual(out.splitlines(), ["tests/test_hooks.py"])
        self.assertEqual(err.splitlines(), ["why: tests/test_hooks.py <- scripts/x.py (rule 1: ^scripts/)",
                                            "why: tests/test_hooks.py <- scripts/y.py (rule 1: ^scripts/)"])

    def test_empty_selection_says_so(self):
        code, out, err = self.run_cli("--why", "README.md")
        self.assertEqual((code, out), (0, ""), err)
        self.assertIn("why: no test file for these changes", err)

    def test_with_run_too(self):
        self.configure(RULES, "true {files}")
        code, out, err = self.run_cli("--why", "--run", "scripts/config-guard.py")
        self.assertEqual(code, 0, out + err)
        self.assertIn("why: tests/test_hooks.py <- scripts/config-guard.py (rule 1: ^scripts/)", err)

    def test_without_why_nothing_is_added(self):
        code, out, err = self.run_cli("scripts/config-guard.py")
        self.assertNotIn("why:", out + err)


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
