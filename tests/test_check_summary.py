"""scripts/check.sh: the summary of the run, the log file and the --quiet mode (trimmed output of what fails).
Each case runs the real script in a temporary git repo with its own `check` list."""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
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

    def configure(self, check, wrapper="", lock_wait=None):
        cfg = {"version": "0.4.3", "schemaVersion": 1, "language": "en", "protectedBranch": "main",
               "pushToProtected": "direct", "content": ["^docs/"], "check": check, "checkWrapper": wrapper}
        if lock_wait is not None:
            cfg["checkLockWait"] = lock_wait
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

    def default_log(self):
        logs = sorted((self.repo / ".git" / "gw").glob("check-*.log"))
        self.assertEqual(len(logs), 1, logs)
        return logs[0]

    def log(self):
        return self.default_log().read_text()

    def quiet_env(self, **extra):
        return dict({"GW_CHECK_QUIET": "1"}, **extra)

    def test_green_run_streams_and_prints_one_ok_line_per_command(self):
        self.configure(["echo first-output", "echo second-output"])
        code, out, err = self.run_check()
        self.assertEqual(code, 0, out + err)
        self.assertIn("first-output", out)
        summary = out.split("check: summary")[1]
        self.assertRegex(summary, r"ok +\d+s +echo first-output\n")
        self.assertRegex(summary, r"ok +\d+s +echo second-output\n")
        self.assertIn("check: all green", out)

    def test_the_default_mode_also_writes_the_log_in_the_common_dir_named_by_the_sha(self):
        self.configure(["echo first-output"])
        self.assertEqual(self.run_check()[0], 0)
        sha = self.git("rev-parse", "--short=12", "HEAD").stdout.strip()
        self.assertIn("first-output", (self.repo / ".git" / "gw" / f"check-{sha}.log").read_text())

    def test_the_default_mode_leaves_stdout_a_pipe_not_a_tee_and_stderr_apart(self):
        self.configure(["echo to-$((1+1)); echo err-$((2+2)) >&2"])
        code, out, err = self.run_check()
        self.assertEqual(code, 0, out + err)
        self.assertIn("\nto-2\n", out)
        self.assertNotIn("err-4", out)
        self.assertIn("err-4", err)

    def test_quiet_log_keeps_a_header_and_the_full_output_of_every_command(self):
        self.configure(["echo first-output", "echo to-stderr >&2"])
        self.assertEqual(self.run_check("-q")[0], 0)
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

    def test_quiet_failure_shows_the_tail_of_that_command_and_the_log_path(self):
        self.configure(["echo earlier-output", "echo only-here; exit 4"])
        code, out, err = self.run_check("--quiet")
        self.assertEqual(code, 1, out + err)
        tail = out.split("of the failed command:")[1]
        self.assertIn("only-here", tail)
        self.assertNotIn("earlier-output", tail)
        self.assertNotIn("== echo", tail)
        self.assertIn("full output: " + str(self.default_log()), out)

    def test_quiet_green_run_prints_no_command_output(self):
        self.configure(["echo noisy-$((6*7))"])
        code, out, err = self.run_check(env=self.quiet_env())
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("noisy-42", out)
        self.assertRegex(out, r"ok +\d+s +echo noisy-")

    def test_a_bad_argument_fails_with_the_usage(self):
        self.configure(["true"])
        code, out, err = self.run_check("--loud")
        self.assertEqual(code, 2, out + err)
        self.assertIn("unexpected argument '--loud'; usage: bash", err)

    def test_an_unwritable_log_fails_before_running_anything(self):
        self.configure(["echo still-runs"])
        code, out, err = self.run_check("-q", env={"GW_CHECK_LOG": str(self.tmp / "no-dir" / "x.log")})
        self.assertEqual(code, 1, out + err)
        self.assertIn("cannot write the log", err)
        self.assertNotIn("still-runs", out)

    def test_a_relative_log_is_resolved_from_the_current_directory(self):
        self.configure(["echo rel-output"])
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        full = dict(os.environ, GW_CHECK_CACHE="0", GW_CHECK_LOG="out/my.log")
        (elsewhere / "out").mkdir()
        r = subprocess.run(["bash", str(self.repo / "scripts" / "check.sh"), "-q"], capture_output=True, text=True,
                           env=full, stdin=subprocess.DEVNULL, cwd=elsewhere)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("rel-output", (elsewhere / "out" / "my.log").read_text())
        self.assertFalse((self.repo / "out").exists())

    def test_a_log_inside_the_work_tree_is_refused_with_its_reason(self):
        self.configure(["echo must-not-run"])
        code, out, err = self.run_check("-q", env={"GW_CHECK_LOG": str(self.repo / "check.log")})
        self.assertEqual(code, 1, out + err)
        self.assertIn("is inside the work tree and would change it; set GW_CHECK_LOG to a path outside", err)
        self.assertNotIn("must-not-run", out)
        self.assertFalse((self.repo / "check.log").exists())

    def test_a_git_ignored_log_inside_the_work_tree_is_accepted(self):
        (self.repo / ".gitignore").write_text("*.log\n")
        self.configure(["echo fine"])
        code, out, err = self.run_check("-q", env={"GW_CHECK_LOG": str(self.repo / "check.log")})
        self.assertEqual(code, 0, out + err)
        self.assertIn("fine", (self.repo / "check.log").read_text())

    def test_quiet_accepts_true_and_yes(self):
        self.configure(["echo hidden-$((6*7))"])
        for value in ("true", "yes"):
            code, out, err = self.run_check(env=self.quiet_env(GW_CHECK_QUIET=value))
            self.assertEqual(code, 0, out + err)
            self.assertNotIn("hidden-42", out)

    def test_an_interrupt_in_quiet_mode_keeps_the_partial_log_and_records_no_green(self):
        self.configure(["echo partial-output; sleep 30"])
        full = dict(os.environ, GW_CHECK_CACHE="", GW_CHECK_QUIET="1")
        p = subprocess.Popen(["bash", str(self.repo / "scripts" / "check.sh")], env=full, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        self.addCleanup(lambda: p.poll() is None and os.killpg(p.pid, signal.SIGKILL))
        deadline = time.time() + 20
        def find():
            return next(iter((self.repo / ".git" / "gw").glob("check-*.log")), self.repo / "none")
        log = find()
        while time.time() < deadline and not (find().exists() and "partial-output" in find().read_text()):
            time.sleep(0.1)
        log = find()
        self.assertIn("partial-output", log.read_text())
        os.killpg(p.pid, signal.SIGINT)
        out, err = p.communicate(timeout=20)
        self.assertNotEqual(p.returncode, 0, out + err)
        self.assertIn("partial-output", log.read_text())
        self.assertNotIn("all green", out)
        self.assertFalse((self.repo / ".git" / "gw-check-green").exists())

    def test_a_green_run_still_records_the_tree_for_the_pre_push(self):
        self.configure(["echo ok"])
        code, out, err = self.run_check(env={"GW_CHECK_CACHE": ""})
        self.assertEqual(code, 0, out + err)
        self.assertIn("the next push of this same tree will skip the check", out)
        self.assertEqual(len((self.repo / ".git" / "gw-check-green").read_text().splitlines()), 1)

    def test_the_quiet_log_inside_the_git_dir_does_not_change_the_recorded_tree(self):
        self.configure(["echo ok"])
        code, out, err = self.run_check("-q", env={"GW_CHECK_CACHE": ""})
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("work tree changed", out + err)
        self.assertIn("will skip the check", out)

    # --- E20: the registry in the common dir, the lock and the closing CHECK line
    def lock_dir(self, repo=None):
        return (repo or self.repo) / ".git" / "gw" / "check.lock"

    def lock_exists(self):
        return os.path.lexists(self.lock_dir())

    def lock_target(self):
        return os.readlink(self.lock_dir())

    @staticmethod
    def start_of(pid):
        r = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True,
                           env=dict(os.environ, LC_ALL="C"))
        return " ".join(r.stdout.split())

    def make_lock(self, pid, start=None):
        self.lock_dir().parent.mkdir(parents=True, exist_ok=True)
        start = self.start_of(pid) if start is None else start
        os.symlink(f"{pid}|{start}|abc123abc123|/some/log", self.lock_dir())

    def start_check(self, *args, env=None):
        full = dict(os.environ, GW_CHECK_CACHE="0", **(env or {}))
        p = subprocess.Popen(["bash", str(self.repo / "scripts" / "check.sh"), *args], env=full, text=True,
                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True)
        self.addCleanup(lambda: p.poll() is None and os.killpg(p.pid, signal.SIGKILL))
        self.addCleanup(lambda: (p.stdout.close(), p.stderr.close()))
        return p

    def wait_for(self, predicate):
        deadline = time.time() + 20
        while time.time() < deadline and not predicate():
            time.sleep(0.1)
        self.assertTrue(predicate(), "timed out waiting")

    def test_the_last_line_is_check_ok_and_a_failure_names_the_failed_section(self):
        self.configure(["echo fine"])
        code, out, err = self.run_check()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out.splitlines()[-1], "CHECK ok: nothing failed")
        self.assertEqual(self.log().splitlines()[-1], "CHECK ok: nothing failed")
        cmd = ("echo '== first'; echo 'FAILED: first-section'; echo '== second'; echo '== third'; "
               "echo 'FAILED: third-section'; echo '== last'; exit 1")
        self.configure(["echo fine", cmd])
        code, out, err = self.run_check()
        self.assertEqual(code, 1, out + err)
        # every section that printed FAILED is named, not just the last `==` seen
        self.assertEqual(out.splitlines()[-1], f"CHECK FAILED: {cmd} (failed: first-section, third-section)")

    def test_a_failure_without_failed_lines_names_no_section(self):
        self.configure(["echo '== looks-like-a-section'; exit 1"])
        code, out, err = self.run_check()
        self.assertEqual(code, 1, out + err)
        self.assertEqual(out.splitlines()[-1], "CHECK FAILED: echo '== looks-like-a-section'; exit 1")

    def test_a_dirty_tree_puts_dirty_in_the_log_name(self):
        self.configure(["echo ok"])
        (self.repo / "untracked.txt").write_text("x")
        self.assertEqual(self.run_check()[0], 0)
        sha = self.git("rev-parse", "--short=12", "HEAD").stdout.strip()
        self.assertTrue((self.repo / ".git" / "gw" / f"check-{sha}-dirty.log").exists())
        self.assertFalse((self.repo / ".git" / "gw" / f"check-{sha}.log").exists())

    def test_a_linked_worktree_writes_the_log_in_the_common_dir(self):
        self.configure(["echo from-worktree"])
        wt = self.tmp / "wt"
        self.git("worktree", "add", "-q", "-b", "other", str(wt))
        r = subprocess.run(["bash", str(wt / "scripts" / "check.sh")], capture_output=True, text=True,
                           env=dict(os.environ, GW_CHECK_CACHE="0"), stdin=subprocess.DEVNULL)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        logs = list((self.repo / ".git" / "gw").glob("check-*.log"))
        self.assertEqual(len(logs), 1, logs)
        self.assertIn("from-worktree", logs[0].read_text())
        self.assertFalse((wt / ".git" / "gw").exists())

    def test_a_green_run_releases_the_lock_and_creates_gw_when_the_git_dir_has_none(self):
        self.configure(["echo ok"])
        shutil.rmtree(self.repo / ".git" / "gw", ignore_errors=True)
        self.assertEqual(self.run_check()[0], 0)
        self.assertTrue((self.repo / ".git" / "gw").is_dir())
        self.assertFalse(self.lock_exists())

    def test_an_orphan_lock_is_discarded(self):
        self.configure(["echo ran-anyway"])
        dead = subprocess.Popen(["true"])
        dead.wait()
        self.make_lock(dead.pid)
        code, out, err = self.run_check()
        self.assertEqual(code, 0, out + err)
        self.assertIn("discarding a stale lock", err)
        self.assertIn(f"pid {dead.pid} is not running", err)
        self.assertIn("ran-anyway", out)
        self.assertFalse(self.lock_exists())

    def test_a_running_check_makes_the_second_exit_naming_its_pid_and_sha(self):
        self.configure(["echo started; sleep 30"])
        first = self.start_check()
        self.wait_for(lambda: self.lock_exists())
        code, out, err = self.run_check()
        self.assertEqual(code, 3, out + err)
        self.assertIn(f"another check is running (pid {first.pid}", err)
        self.assertIn(self.lock_target().split("|")[2], err)
        self.assertIn("checkLockWait", err)
        self.assertNotIn("check: running", out)  # the second one ran nothing
        self.assertTrue(self.lock_exists(), "the first one keeps its lock")

    def test_with_check_lock_wait_the_second_check_waits_for_the_lock(self):
        self.configure(["echo ran-after-wait"], lock_wait=60)
        holder = subprocess.Popen(["sleep", "60"])
        self.addCleanup(holder.kill)
        self.make_lock(holder.pid)
        waiter = self.start_check()
        line = waiter.stderr.readline()  # the signal that it is waiting, not a fixed sleep
        self.assertIn(f"waiting for the check of pid {holder.pid}", line)
        self.assertIsNone(waiter.poll())
        holder.kill()  # the holder dies without cleaning: its lock is now an orphan
        holder.wait()  # reaped, or it would stay a zombie
        out, err = waiter.communicate(timeout=30)
        self.assertEqual(waiter.returncode, 0, out + err)
        self.assertIn("ran-after-wait", out)

    def test_a_reused_pid_is_not_the_holder(self):
        self.configure(["echo ran-anyway"])
        other = subprocess.Popen(["sleep", "60"])  # alive, but not the process that took the lock
        self.addCleanup(other.kill)
        self.make_lock(other.pid, start="Mon Jan  1 00:00:00 2001")
        code, out, err = self.run_check()
        self.assertEqual(code, 0, out + err)
        self.assertIn("discarding a stale lock", err)
        self.assertIn("ran-anyway", out)
        self.assertIsNone(other.poll(), "the unrelated process is left alone")

    def test_a_lock_that_is_no_longer_ours_is_not_removed_on_exit(self):
        other = subprocess.Popen(["sleep", "60"])
        self.addCleanup(other.kill)
        theirs = f"{other.pid}|{self.start_of(other.pid)}|feedfeedfeed|/their/log"
        lock = ".git/gw/check.lock"
        self.configure([f"rm -f {lock}; ln -s '{theirs}' {lock}"])  # someone else holds it by the time we finish
        code, out, err = self.run_check()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.lock_target(), theirs)

    def test_two_checks_started_together_run_one_at_a_time(self):
        marker = self.tmp / "ran.log"
        self.configure([f"echo x >> {marker}; sleep 3"])
        procs = [self.start_check(), self.start_check()]
        results = [(p.communicate(timeout=30), p.returncode) for p in procs]
        codes = sorted(rc for _, rc in results)
        self.assertEqual(codes, [0, 3], results)
        self.assertEqual(marker.read_text(), "x\n", "the command ran once")
        loser = next(res for res, rc in results if rc == 3)
        self.assertIn("another check is running (pid ", loser[1])

    def test_a_background_child_holding_the_output_does_not_hang_the_check(self):
        pidfile = self.tmp / "bg.pid"
        self.configure([f"sleep 60 & echo $! > {pidfile}; echo started"])
        cfg = json.loads((self.repo / ".claude" / "gw.json").read_text())
        cfg["checkOutputGrace"] = 1
        (self.repo / ".claude" / "gw.json").write_text(json.dumps(cfg))
        self.git("commit", "-qam", "grace")
        p = self.start_check()
        out, err = p.communicate(timeout=30)  # without the grace it would wait the 60 s of the child
        self.addCleanup(lambda: os.kill(int(pidfile.read_text()), signal.SIGKILL))
        self.assertEqual(p.returncode, 0, out + err)
        self.assertFalse(self.lock_exists(), "the lock is released")

    def test_no_fifo_is_left_in_tmpdir_after_an_interrupt(self):
        tmpdir = self.tmp / "tmpd"
        tmpdir.mkdir()
        self.configure(["echo partial; sleep 30"])
        p = self.start_check(env={"TMPDIR": str(tmpdir)})
        self.wait_for(lambda: any(tmpdir.glob("gw-check-fifo.*")))
        os.killpg(p.pid, signal.SIGINT)
        p.communicate(timeout=20)
        self.assertEqual(list(tmpdir.glob("gw-check-fifo.*")), [])

    def test_check_lock_wait_gives_up_after_its_seconds(self):
        self.configure(["echo never"], lock_wait=2)
        holder = subprocess.Popen(["sleep", "30"])
        self.addCleanup(holder.kill)
        self.make_lock(holder.pid)
        started = time.time()
        code, out, err = self.run_check()
        self.assertEqual(code, 3, out + err)
        self.assertGreaterEqual(time.time() - started, 2)
        self.assertIn(f"pid {holder.pid}", err)
        self.assertIn("rm ", err)  # the safe remedy, not kill

    def test_ctrl_c_releases_the_lock_and_keeps_the_log(self):
        self.configure(["echo partial; sleep 30"])
        p = self.start_check()
        self.wait_for(lambda: any("partial" in f.read_text() for f in (self.repo / ".git" / "gw").glob("check-*.log")))
        self.assertTrue(self.lock_exists())
        os.killpg(p.pid, signal.SIGINT)
        out, err = p.communicate(timeout=20)
        self.assertEqual(p.returncode, 130, out + err)
        self.assertFalse(self.lock_exists(), "the lock must be released on Ctrl-C")
        self.assertTrue(list((self.repo / ".git" / "gw").glob("check-*.log")))

    def test_a_kill_releases_the_lock(self):
        self.configure(["echo partial; sleep 30"])
        p = self.start_check()
        self.wait_for(lambda: self.lock_exists())
        os.killpg(p.pid, signal.SIGTERM)
        out, err = p.communicate(timeout=20)
        self.assertEqual(p.returncode, 143, out + err)
        self.assertFalse(self.lock_exists())


if __name__ == "__main__":
    unittest.main()
