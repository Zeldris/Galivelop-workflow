"""scripts/push.sh (D94): retries, failure classification and the success criterion (the remote has the commit).

A local bare repo is `origin`; a fake `git` first on PATH replaces `git push` with a script (one scripted answer per
call, read from a counter file) and runs everything else with the real git.
Edge cases: success first try; transient then success (retried, delays from the config); retries exhausted;
non-transient rejection (no retry, reason and fix shown); non-fast-forward; push OK but remote differs; push fails
but remote matches; ls-remote hangs (limited, reason shown, also when the
push failed too); a hung ls-remote with a child (timeout, Ctrl-C, TERM: no orphan left); timeout 0 (no limit) and a non-numeric one; detached HEAD without argument; explicit branch; unknown branch; no origin; empty delays.
"""
import json
import os
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REAL_GIT = shutil.which("git")
BASE_CONFIG = {"version": "0.1.0", "language": "en", "log": "docs/log.md", "protectedBranch": "main",
               "pushToProtected": "pr", "check": ["true"], "reviewMark": "docs/reviewed.txt", "content": ["^docs/"]}

FAKE_GIT = """#!/usr/bin/env bash
# $FAKE_STEPS: one line per `git push` call: ok | fail:<text> | lie (exit 0 without pushing) | late:<text> (push, then fail)
if [ "$1" = "push" ]; then
  n=$(cat "$FAKE_DIR/count" 2>/dev/null || echo 0); n=$((n + 1)); echo "$n" > "$FAKE_DIR/count"
  step=$(sed -n "${n}p" "$FAKE_DIR/steps"); [ -n "$step" ] || step=ok
  case "$step" in
    ok) exec "$REAL_GIT" "$@" ;;
    lie) exit 0 ;;
    late:*) "$REAL_GIT" "$@" >/dev/null 2>&1; echo "${step#late:}" >&2; exit 1 ;;
    fail:*) echo "${step#fail:}" >&2; exit 1 ;;
  esac
fi
if [ "$1" = "ls-remote" ] && [ -e "$FAKE_DIR/lshang" ]; then exec sleep 30; fi  # a network that never answers
if [ "$1" = "ls-remote" ] && [ -e "$FAKE_DIR/lschild" ]; then  # git hung on its transport (git-remote-https): a child
  sleep 30 & echo "$! $$" > "$FAKE_DIR/lschild.pids"; wait; exit 0
fi
if [ "$1" = "ls-remote" ] && [ -s "$FAKE_DIR/lsslow" ]; then sleep "$(cat "$FAKE_DIR/lsslow")"; fi  # a slow but answering network
if [ "$1" = "ls-remote" ] && [ -s "$FAKE_DIR/lsfail" ]; then  # fail the next N ls-remote calls
  n=$(cat "$FAKE_DIR/lsfail"); if [ "$n" -gt 0 ]; then echo $((n - 1)) > "$FAKE_DIR/lsfail"; echo "fatal: network blip" >&2; exit 128; fi
fi
exec "$REAL_GIT" "$@"
"""


class PushSh(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-test-push."))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.origin, self.work, self.fake = self.tmp / "origin.git", self.tmp / "work", self.tmp / "fake"
        self.fake.mkdir()
        (self.fake / "git").write_text(FAKE_GIT)
        (self.fake / "git").chmod(0o755)
        self.env = dict(os.environ, PATH=f"{self.fake}:{os.environ['PATH']}", FAKE_DIR=str(self.fake),
                        REAL_GIT=REAL_GIT, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            self.env.pop(key, None)
        self.git(self.tmp, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.git(self.tmp, "init", "-q", "-b", "main", str(self.work))
        for k, v in (("user.name", "t"), ("user.email", "t@example.com")):
            self.git(self.work, "config", k, v)
        self.git(self.work, "remote", "add", "origin", str(self.origin))
        (self.work / "scripts").mkdir()
        (self.work / "schema").mkdir()
        for name in ("push.sh", "config.py"):
            shutil.copy(ROOT / "scripts" / name, self.work / "scripts" / name)
        shutil.copy(ROOT / "schema" / "gw.schema.json", self.work / "schema" / "gw.schema.json")
        self.set_delays([0, 0, 0])
        self.commit("one")

    def git(self, cwd, *args):
        return subprocess.run([REAL_GIT, *args], cwd=cwd, env=self.env, capture_output=True, text=True, check=True)

    def commit(self, text):
        (self.work / "f.txt").write_text(text)
        self.git(self.work, "add", "-A")
        self.git(self.work, "commit", "-q", "-m", text)

    def set_delays(self, delays, **extra):
        (self.work / ".claude").mkdir(exist_ok=True)
        (self.work / ".claude" / "gw.json").write_text(json.dumps(dict(BASE_CONFIG, pushRetryDelays=delays, **extra)))

    def steps(self, *lines):
        (self.fake / "steps").write_text("\n".join(lines) + "\n")

    def pushes(self):
        path = self.fake / "count"
        return int(path.read_text()) if path.exists() else 0

    def run_push(self, *args, cwd=None):
        return subprocess.run(["bash", str(self.work / "scripts" / "push.sh"), *args], cwd=cwd or self.work,
                              env=self.env, capture_output=True, text=True)

    def remote(self, branch="main"):
        out = self.git(self.origin, "rev-parse", "--verify", "-q", f"refs/heads/{branch}").stdout.strip()
        return out

    def head(self):
        return self.git(self.work, "rev-parse", "HEAD").stdout.strip()

    def test_success_first_try(self):
        r = self.run_push()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("push: ok: origin/main is at " + self.head(), r.stdout)
        self.assertEqual((self.remote(), self.pushes()), (self.head(), 1))

    def test_transient_failure_then_success(self):
        self.steps("fail:fatal: unable to access 'x': Could not resolve host: example.com", "ok")
        r = self.run_push()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.pushes(), 2)
        self.assertIn("transient failure (attempt 1); retrying in 0s", r.stderr)
        self.assertEqual(self.remote(), self.head())

    def test_every_transient_text_is_retried(self):
        for text in ("Connection reset by peer", "Connection refused", "Connection timed out", "Operation timed out",
                     "error: RPC failed; curl 56", "fatal: early EOF", "fatal: the remote end hung up unexpectedly",
                     "error: unexpected disconnect while reading", "The requested URL returned error: 502",
                     "HTTP 503 Service Unavailable", "returned error: 500", "HTTP/1.1 504 Gateway Timeout",
                     "ssh: connect to host github.com port 22: Network is unreachable",
                     "Failed to connect to github.com port 443 after 21000 ms: Couldn't connect to server",
                     "OpenSSL SSL_read: Connection was reset, errno 104", "OpenSSL SSL_read: SSL_ERROR_SYSCALL",
                     "gnutls_handshake() failed: The TLS connection was non-properly terminated",
                     "unable to access 'x': The requested URL returned error: 408",
                     "remote: Internal Server Error", "Bad Gateway", "Service Unavailable",
                     "Connection closed by remote host", "kex_exchange_identification: read: Connection reset"):
            with self.subTest(text=text):
                (self.fake / "count").unlink(missing_ok=True)
                subprocess.run([REAL_GIT, "branch", "-q", "-D", "main"], cwd=self.origin, env=self.env, capture_output=True)
                self.steps("fail:fatal: " + text, "ok")
                r = self.run_push()
                self.assertEqual((r.returncode, self.pushes()), (0, 2), r.stderr)

    def test_retries_exhausted(self):
        self.set_delays([0, 0])
        self.steps(*["fail:fatal: Could not resolve host: example.com"] * 5)
        r = self.run_push()
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.pushes(), 3)  # the first try + one per delay
        self.assertIn("transient failure and the 3 attempt(s) are used up (pushRetryDelays)", r.stderr)
        self.assertIn("bash " + str(self.work / "scripts" / "push.sh") + " main", r.stderr)
        self.assertEqual(self.git(self.origin, "branch", "--list").stdout.strip(), "")

    def test_empty_delays_means_no_retry(self):
        self.set_delays([])
        self.steps("fail:Connection reset by peer", "ok")
        r = self.run_push()
        self.assertEqual((r.returncode, self.pushes()), (1, 1))
        self.assertIn("used up", r.stderr)

    def test_hook_rejection_is_not_retried(self):
        self.steps("fail:pre-push: the check is not green\nerror: failed to push some refs to 'x'", "ok")
        r = self.run_push()
        self.assertEqual((r.returncode, self.pushes()), (1, 1))
        self.assertIn("not a transient network one", r.stderr)
        self.assertIn("a hook or the remote rejected it; read its output above", r.stderr)
        self.assertIn("pre-push: the check is not green", r.stdout + r.stderr)

    def test_hook_text_that_looks_transient_is_still_not_retried(self):
        self.steps("fail:pre-push: Connection timed out in a test\nerror: failed to push some refs", "ok")
        r = self.run_push()
        self.assertEqual((r.returncode, self.pushes()), (1, 1))

    def test_output_of_a_passing_pre_push_hook_does_not_decide(self):
        # A real pre-push hook that passes but prints text that looks like a rejection; then the network fails.
        hook = self.work / ".git" / "hooks" / "pre-push"
        hook.write_text("#!/bin/sh\necho 'pre-push: all green.'\necho 'error: 403 Permission denied in a test'\n"
                        "echo 'pre-push: hook declined nothing' >&2\nexit 0\n")
        hook.chmod(0o755)
        self.steps("fail:error: RPC failed; HTTP 502 curl 22\nfatal: the remote end hung up unexpectedly", "ok")
        r = self.run_push()
        self.assertEqual((r.returncode, self.pushes()), (0, 2), r.stderr)
        self.assertIn("transient failure (attempt 1)", r.stderr)
        self.assertEqual(self.remote(), self.head())

    def test_real_hook_output_with_a_real_push_passes(self):
        hook = self.work / ".git" / "hooks" / "pre-push"
        hook.write_text("#!/bin/sh\necho 'pre-push: all green.'\nexit 0\n")
        hook.chmod(0o755)
        r = self.run_push()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("pre-push: all green.", r.stdout)

    def test_request_timeout_408_is_transient(self):
        self.steps("fail:fatal: unable to access 'x': The requested URL returned error: 408", "ok")
        r = self.run_push()
        self.assertEqual((r.returncode, self.pushes()), (0, 2), r.stderr)

    def test_push_ok_but_ls_remote_blips_rechecks_without_pushing_again(self):
        # push OK, then the first ls-remote after it fails: only the check is retried.
        self.git(self.work, "push", "-q", "-u", "origin", "main")
        (self.fake / "lsfail").write_text("1")
        r = self.run_push()
        self.assertEqual((r.returncode, self.pushes()), (0, 1), r.stderr)

    def test_push_ok_and_ls_remote_always_fails_reports_it(self):
        (self.fake / "lsfail").write_text("99")
        r = self.run_push()
        self.assertEqual(r.returncode, 1)
        self.assertIn("origin cannot be read to confirm it", r.stderr)
        self.assertEqual(self.pushes(), 1)

    def test_late_failure_with_remote_matching_sets_upstream_and_tracking_ref(self):
        self.steps("late:fatal: the remote end hung up unexpectedly")
        r = self.run_push()
        self.assertEqual(r.returncode, 0, r.stderr)
        up = self.git(self.work, "rev-parse", "--abbrev-ref", "main@{upstream}").stdout.strip()
        self.assertEqual(up, "origin/main")
        self.assertEqual(self.git(self.work, "rev-parse", "refs/remotes/origin/main").stdout.strip(), self.head())

    def test_forbidden_is_not_retried(self):
        self.steps("fail:fatal: unable to access 'x': The requested URL returned error: 403", "ok")
        r = self.run_push()
        self.assertEqual((r.returncode, self.pushes()), (1, 1))
        self.assertIn("access was refused; check the credentials or permissions for origin", r.stderr)

    def test_non_fast_forward_says_how_to_fix_it(self):
        self.steps("fail: ! [rejected]        main -> main (fetch first)\nerror: failed to push some refs", "ok")
        r = self.run_push()
        self.assertEqual((r.returncode, self.pushes()), (1, 1))
        self.assertIn("git fetch origin main && git merge --no-edit origin/main && bash", r.stderr)

    def test_real_non_fast_forward(self):
        other = self.tmp / "other"
        self.git(self.tmp, "clone", "-q", str(self.origin), str(other))  # empty origin: clone then push a divergent main
        self.git(other, "config", "user.name", "o")
        self.git(other, "config", "user.email", "o@example.com")
        (other / "g.txt").write_text("x")
        self.git(other, "add", "-A")
        self.git(other, "commit", "-q", "-m", "other")
        self.git(other, "push", "-q", "origin", "HEAD:main")
        r = self.run_push()
        self.assertEqual(r.returncode, 1)
        self.assertIn("git fetch origin main && git merge --no-edit origin/main", r.stderr)

    def test_push_ok_but_remote_differs_fails(self):
        self.steps("lie")
        r = self.run_push()
        self.assertEqual(r.returncode, 1)
        self.assertIn("git push said OK but origin/main is not at " + self.head(), r.stderr)

    def test_push_fails_but_remote_matches_succeeds(self):
        self.steps("late:error: output lost\nfatal: the remote end hung up unexpectedly")
        r = self.run_push()
        self.assertEqual((r.returncode, self.pushes()), (0, 1), r.stderr)
        self.assertIn("push: ok: origin/main is at " + self.head(), r.stdout)

    def test_detached_head_without_argument_fails_closed(self):
        self.git(self.work, "checkout", "-q", "--detach")
        r = self.run_push()
        self.assertEqual((r.returncode, self.pushes()), (2, 0))
        self.assertIn("detached HEAD and no branch given", r.stderr)

    def test_explicit_branch_from_a_detached_head(self):
        self.git(self.work, "checkout", "-q", "-b", "feature")
        self.commit("two")
        feature = self.head()
        self.git(self.work, "checkout", "-q", "--detach", "main")
        r = self.run_push("feature")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.remote("feature"), self.pushes()), (feature, 1))

    def test_unknown_branch_fails_closed(self):
        r = self.run_push("nope")
        self.assertEqual((r.returncode, self.pushes()), (2, 0))
        self.assertIn("there is no local branch 'nope'", r.stderr)

    def test_no_origin_fails_closed(self):
        self.git(self.work, "remote", "remove", "origin")
        r = self.run_push()
        self.assertEqual((r.returncode, self.pushes()), (2, 0))
        self.assertIn("has no remote 'origin'; add it: git remote add origin <url>", r.stderr)

    def test_root_comes_from_the_script_not_the_current_directory(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        r = self.run_push(cwd=outside)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.remote(), self.head())

    def test_ls_remote_that_hangs_is_stopped_and_the_reason_shown(self):
        # D94 n.5: a network that never answers must not block push.sh for ever (the fake would sleep 30 s)
        self.set_delays([0, 0], pushLsRemoteTimeout=1)
        (self.fake / "lshang").write_text("1")
        start = time.monotonic()
        r = self.run_push()
        self.assertLess(time.monotonic() - start, 15)
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("git ls-remote origin took over 1s and was stopped (pushLsRemoteTimeout", r.stderr)
        self.assertIn("origin cannot be read to confirm it", r.stderr)
        self.assertEqual(self.remote(), self.head())  # the push itself did happen, only the confirmation failed

    def test_ls_remote_slower_than_zero_limit_is_waited_for_and_over_a_real_limit_is_not(self):
        (self.fake / "lsslow").write_text("2")
        self.set_delays([0], pushLsRemoteTimeout=0)  # 0 = no limit
        r = self.run_push()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("push: ok", r.stdout)
        self.commit("two")
        self.set_delays([0], pushLsRemoteTimeout=1)  # the same 2 s answer is now too slow
        r = self.run_push()
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("took over 1s", r.stderr)

    def test_ls_remote_timeout_default_is_30_and_a_bad_value_fails_closed(self):
        self.assertEqual(json.loads((ROOT / "schema" / "gw.schema.json").read_text())["properties"]
                         ["pushLsRemoteTimeout"]["default"], 30)
        self.assertEqual(self.run_push().returncode, 0)  # absent in the config: the default applies
        for bad in ("abc", -1, 1.5, True):
            self.commit(f"bad {bad}")
            before = self.pushes()
            self.set_delays([0], pushLsRemoteTimeout=bad)
            r = self.run_push()
            self.assertEqual((r.returncode, self.pushes()), (2, before), bad)
            self.assertIn("push: invalid config (.claude/gw.json); see what is wrong and fix it: python3 ", r.stderr)
            self.assertIn(" validate", r.stderr)
            self.assertNotIn("pushRetryDelays", r.stderr)  # it does not blame a key the user may not have touched

    def child_pids(self):
        """The (transport child, fake git) pids the hung ls-remote wrote, once it wrote them."""
        path = self.fake / "lschild.pids"
        deadline = time.monotonic() + 10
        while not (path.exists() and path.read_text().strip()) and time.monotonic() < deadline:
            time.sleep(0.05)
        return [int(x) for x in path.read_text().split()]

    def assertGone(self, pids):
        """Each pid has exited (a zombie waiting for its reaper counts as gone): no orphan of push.sh is left."""
        deadline = time.monotonic() + 5
        alive = pids
        while alive and time.monotonic() < deadline:
            alive = [pid for pid in pids if subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True,
                                                            text=True).stdout.strip()[:1] not in ("", "Z")]
            time.sleep(0.05)
        for pid in alive:
            os.kill(pid, 9)
        self.assertEqual(alive, [], "processes of the hung ls-remote outlived push.sh")

    def test_ls_remote_timeout_kills_git_and_its_transport_child(self):
        # D94: killing only `git` would leave the hung git-remote-https behind, one more per retry
        self.set_delays([0], pushLsRemoteTimeout=1)
        (self.fake / "lschild").write_text("1")
        r = self.run_push()
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("took over 1s and was stopped", r.stderr)
        self.assertGone(self.child_pids())

    def test_interrupt_or_term_kills_the_hung_ls_remote_and_its_child(self):
        # D94: the background job ignores the terminal's Ctrl-C, so push.sh's own trap must stop it
        for sig, code in ((signal.SIGINT, 130), (signal.SIGTERM, 143)):
            with self.subTest(sig=sig):
                self.commit(f"for {sig.name}")
                (self.fake / "lschild.pids").unlink(missing_ok=True)
                self.set_delays([0], pushLsRemoteTimeout=0)  # no limit: only the signal ends it
                (self.fake / "lschild").write_text("1")
                proc = subprocess.Popen(["bash", str(self.work / "scripts" / "push.sh")], cwd=self.work, env=self.env,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                pids = self.child_pids()
                proc.send_signal(sig)
                proc.communicate(timeout=20)
                self.assertEqual(proc.returncode, code)
                self.assertGone(pids)

    def test_push_failed_and_ls_remote_timed_out_says_why(self):
        # D94: the pushLsRemoteTimeout note also on the failure path, not only after a push that said OK
        self.set_delays([0], pushLsRemoteTimeout=1)
        self.steps(*["fail:fatal: Could not resolve host: example.com"] * 3)
        (self.fake / "lshang").write_text("1")
        r = self.run_push()
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("used up (pushRetryDelays)", r.stderr)
        self.assertIn("took over 1s and was stopped (pushLsRemoteTimeout", r.stderr)

    def test_suggested_commands_quote_a_root_with_spaces(self):
        spaced = self.tmp / "my work"
        self.set_delays([])
        shutil.copytree(self.work, spaced, symlinks=True)
        self.steps("fail:fatal: Could not resolve host: example.com")
        r = subprocess.run(["bash", str(spaced / "scripts" / "push.sh")], cwd=spaced, env=self.env,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stderr)
        line = next(x for x in r.stderr.splitlines() if "used up" in x)
        self.assertEqual(shlex.split(line.split("run again: ", 1)[1]), ["bash", str(spaced / "scripts" / "push.sh"), "main"])

    def test_too_many_arguments(self):
        r = self.run_push("a", "b")
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage: bash", r.stderr)


if __name__ == "__main__":
    unittest.main()
