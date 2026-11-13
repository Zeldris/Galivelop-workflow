"""scripts/ci-status.py, the GitHub Actions status reader, against a fake `gh` (or fake `curl`) on PATH: no network.
The fake prints the canned JSON in GH_RUNS / GH_STATUS / GH_COMMIT."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "ci-status.py"

FAKE_GH = """#!/bin/sh
[ "$1" = api ] || { echo "fake gh: unsupported $*" >&2; exit 1; }
case "$2" in
  repos/*/*/*) ;;
  repos/*/*) [ -z "${GH_UNAUTH:-}" ] || { echo "not logged in" >&2; exit 1; }; echo '{"full_name":"x"}'; exit 0 ;;
esac
if [ -n "${GH_FAIL:-}" ]; then echo "gh: HTTP 502: Bad Gateway (fake)" >&2; exit 1; fi
case "$2" in
  */annotations) printf '%s' "${GH_NOTES:-[]}" ;;
  */actions/jobs/*/logs) [ -z "${GH_NO_JOB:-}" ] || { echo "gh: HTTP 404: Not Found (fake)" >&2; exit 1; }
    printf '%s' "$GH_LOG" ;;
  */actions/jobs/*) [ -z "${GH_NO_JOB:-}" ] || { echo "gh: HTTP 404: Not Found (fake)" >&2; exit 1; }
    printf '%s' "$GH_JOB" ;;
  */commits/*/check-runs*) [ -z "${GH_SLOW:-}" ] || sleep "$GH_SLOW"; printf '%s' "$GH_RUNS" ;;
  */commits/*/status*) printf '%s' "$GH_STATUS" ;;
  */commits/*) [ -z "${GH_NO_COMMIT:-}" ] || { echo "gh: HTTP 422: No commit found for SHA (fake)" >&2; exit 1; }
    printf '%s' "$GH_COMMIT" ;;
  *) echo "fake gh: unknown path $2" >&2; exit 1 ;;
esac
"""
FAKE_CURL = """#!/bin/sh
cat > "$CURL_LOG"
for a in "$@"; do url="$a"; done
case "$url" in
  *check-runs*) printf '%s' "$GH_RUNS" ;;
  */status*) printf '%s' "$GH_STATUS" ;;
  */commits/*) printf '%s' "$GH_COMMIT" ;;
  *) exit 22 ;;
esac
"""


def runs(*items):
    return {"total_count": len(items), "check_runs": [
        {"id": 100 + i, "name": n, "status": "completed" if c else "in_progress", "conclusion": c,
         "html_url": f"https://github.com/o/r/runs/{100 + i}"} for i, (n, c) in enumerate(items)]}


STAMP = "2026-11-10T12:00:00.1234567Z "
JOB = {"html_url": "https://github.com/o/r/actions/runs/7/job/100", "steps": [
    {"name": "Set up job", "conclusion": "success"}, {"name": "Check", "conclusion": "failure"},
    {"name": "Post", "conclusion": "skipped"}]}
LOG = "\n".join(STAMP + line for line in [
    "\ufeffSetting up", "##[group]Run actions/checkout@v4", "with: x", "##[endgroup]", "checked out",
    "##[group]Run bash tests/check.sh", "bash tests/check.sh", "shell: /usr/bin/bash -e {0}", "##[endgroup]",
    "== unit", "ok 1", "ok 2", "FAIL: test_thing (test_x.Thing)", "AssertionError: 1 != 2",
    "##[error]Process completed with exit code 1.", "##[group]Run actions/cache/save", "cache", "##[endgroup]"])


def statuses(*items):
    return {"statuses": [{"context": c, "state": s} for c, s in items]}


class CiStatus(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-ci-status-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.work = self.tmp / "work"
        (self.work / ".claude").mkdir(parents=True)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        for name in ("GITHUB_TOKEN", "GH_TOKEN", "CLAUDE_PROJECT_DIR"):
            self.env.pop(name, None)
        subprocess.run(["git", "init", "-q", str(self.work)], check=True, env=self.env)
        subprocess.run(["git", "-C", str(self.work), "remote", "add", "origin", "https://github.com/o/r.git"],
                       check=True, env=self.env)
        subprocess.run(["git", "-C", str(self.work), "-c", "user.name=T", "-c", "user.email=t@e.x", "commit", "-q",
                        "--allow-empty", "-m", "base"], check=True, env=self.env)
        self.sha = subprocess.run(["git", "-C", str(self.work), "rev-parse", "HEAD"], capture_output=True, text=True,
                                  env=self.env).stdout.strip()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        for name, text in (("gh", FAKE_GH), ("curl", FAKE_CURL)):
            (self.bin / name).write_text(text)
            (self.bin / name).chmod(0o755)
        self.config({})

    def config(self, extra):
        base = {"version": "0.1.0", "language": "en", "log": "docs/log.md", "protectedBranch": "main",
                "pushToProtected": "pr", "check": ["exit 0"], "reviewMark": "docs/reviewed.txt", "content": ["^docs/"]}
        (self.work / ".claude" / "gw.json").write_text(json.dumps(dict(base, **extra)))

    def ci(self, *args, run=None, status=None, env=None, path=None):
        full = dict(self.env, PATH=path or f"{self.bin}:{self.env['PATH']}",
                    GH_RUNS=json.dumps(run if run is not None else runs(("build", "success"))),
                    GH_STATUS=json.dumps(status if status is not None else statuses()),
                    GH_COMMIT=json.dumps({"sha": "b" * 40}), CURL_LOG=str(self.tmp / "curl.log"),
                    GH_JOB=json.dumps(JOB), GH_LOG=LOG)
        full.update(env or {})
        r = subprocess.run([sys.executable, "-I", str(SCRIPT), "--root", str(self.work), *args], capture_output=True,
                           text=True, env=full, cwd=self.tmp)
        return r.returncode, r.stdout + r.stderr

    def assertCi(self, result, code, *texts):
        got, out = result
        self.assertEqual(got, code, out)
        for text in texts:
            self.assertIn(text, out)

    def test_green(self):
        self.assertCi(self.ci(), 0, "green", self.sha[:12])

    def test_red_check_run_names_it(self):
        self.assertCi(self.ci(run=runs(("build", "success"), ("macos", "failure"))), 1, "red", "macos: failure")

    def test_green_conclusions_default_to_success_neutral_skipped(self):
        self.assertCi(self.ci(run=runs(("a", "success"), ("b", "neutral"), ("c", "skipped"))), 0, "green")
        self.assertCi(self.ci(run=runs(("a", "success"), ("d", "cancelled"))), 1, "red", "d: cancelled")

    def test_green_conclusions_key_changes_what_counts_as_green(self):
        self.config({"ciGreenConclusions": ["success"]})
        self.assertCi(self.ci(run=runs(("a", "success"), ("b", "neutral"))), 1, "red", "b: neutral")
        self.config({"ciGreenConclusions": ["success", "cancelled"]})
        self.assertCi(self.ci(run=runs(("a", "success"), ("d", "cancelled"))), 0, "green")

    def test_green_conclusions_key_validates_in_the_config(self):
        for bad in ([], "success", ["Success"], [1]):
            with self.subTest(bad=bad):
                self.config({"ciGreenConclusions": bad})
                code, out = self.ci()
                self.assertEqual(code, 2, out)
                self.assertIn("ciGreenConclusions", out)

    def test_status_timeout_defaults_to_no_limit_and_a_set_one_fails_closed_with_its_reason(self):
        self.assertCi(self.ci(env={"GH_SLOW": "2"}), 0, "green")  # no limit: the slow call is waited for
        self.config({"ciStatusTimeout": 1})
        started = time.time()
        code, out = self.ci(env={"GH_SLOW": "20"})
        self.assertEqual(code, 2, out)
        self.assertIn("timed out after 1 s (ciStatusTimeout", out)
        self.assertLess(time.time() - started, 15, out)

    def test_pending_check_run_is_pending_not_red(self):
        self.assertCi(self.ci(run=runs(("build", "success"), ("slow", None))), 1, "pending", "slow: in_progress")

    def test_pending_commit_status(self):
        self.assertCi(self.ci(status=statuses(("deploy", "pending"))), 1, "pending", "deploy: pending")

    def test_failed_status_is_red_even_with_a_pending_run(self):
        self.assertCi(self.ci(run=runs(("slow", None)), status=statuses(("deploy", "failure"))), 1, "red")

    def test_no_ci_reported(self):
        self.assertCi(self.ci(run=runs()), 1, "none", "no CI has reported")

    def test_no_ci_with_ci_on_push_off_says_check_yml_runs_only_on_pull_requests(self):
        self.config({"ciOnPush": False})
        code, out = self.ci(run=runs())
        self.assertCi((code, out), 1, "none", "ciOnPush is false", "ci-local.py --record")
        self.assertNotIn("ciOnPush", self.ci(run=runs(("build", "failure")))[1])  # only when nothing reported

    def test_no_ci_with_ci_on_push_on_has_no_pull_request_hint(self):
        self.assertNotIn("ciOnPush", self.ci(run=runs())[1])

    def test_json_output(self):
        code, out = self.ci("--json", run=runs(("build", "failure")))
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual((data["state"], data["problems"], data["repo"], data["sha"]),
                         ("red", ["build: failure"], "o/r", self.sha))

    def test_branch_resolves_through_the_api(self):
        self.assertCi(self.ci("--branch", "feature"), 0, "b" * 12)

    def test_sha_and_repo_flags(self):
        self.assertCi(self.ci("--sha", "c" * 40, "--repo", "x/y"), 0, "x/y", "c" * 12)

    def test_head_not_pushed_says_push_first_not_authenticate(self):
        code, out = self.ci(env={"GH_NO_COMMIT": "1"})
        self.assertEqual(code, 2, out)
        self.assertIn("is not on GitHub", out)
        self.assertIn("git push", out)
        self.assertNotIn("authenticate", out)

    def test_git_dir_from_a_hook_does_not_redirect_the_root(self):
        self.assertCi(self.ci(env={"GIT_DIR": str(self.tmp / "nowhere")}), 0, "green", self.sha[:12])

    # fail closed ---------------------------------------------------------------------------------------------------
    def test_no_gh_and_no_token_fails_closed_with_the_fix(self):
        (self.bin / "gh").unlink()
        sysbin = self.tmp / "sysbin"
        sysbin.mkdir()
        for tool in ("git", "python3"):
            os.symlink(shutil.which(tool), sysbin / tool)
        self.assertCi(self.ci(path=f"{sysbin}:{self.bin}"), 2, "neither GITHUB_TOKEN nor GH_TOKEN", "gh auth login")

    def test_gh_unauthenticated_and_no_token_fails_closed(self):
        self.assertCi(self.ci(env={"GH_UNAUTH": "1"}), 2, "neither GITHUB_TOKEN nor GH_TOKEN", "gh auth login")

    def test_token_fallback_uses_curl_with_the_token_on_stdin(self):
        code, out = self.ci(env={"GH_UNAUTH": "1", "GITHUB_TOKEN": "sekret"})  # gw-allow-secret
        self.assertEqual(code, 0, out)
        log = (self.tmp / "curl.log").read_text()
        self.assertIn("Authorization: Bearer sekret", log)
        self.assertNotIn("sekret", " ".join(log.splitlines()[1:]))  # never in the arguments

    def test_api_error_fails_closed(self):
        self.assertCi(self.ci(env={"GH_FAIL": "1"}), 2, "could not read the CI status", "502")

    def test_422_in_the_request_path_is_not_a_missing_commit(self):
        # A 502 on a path holding "422" (a sha or, here, the repo name) is an API error, not "HEAD is not on GitHub".
        subprocess.run(["git", "-C", str(self.work), "remote", "set-url", "origin", "https://github.com/o/r422.git"],
                       check=True, env=self.env)
        code, out = self.ci(env={"GH_FAIL": "1"})
        self.assertCi((code, out), 2, "could not read the CI status", "502")
        self.assertNotIn("is not on GitHub", out)

    def test_unexpected_answer_fails_closed(self):
        self.assertCi(self.ci(run={"oops": 1}), 2, "could not read the CI status")

    def test_json_on_error_has_state_error(self):
        code, out = self.ci("--json", env={"GH_FAIL": "1"})
        data = json.loads(out)
        self.assertEqual((code, data["state"]), (2, "error"))
        self.assertIn("502", data["error"])

    def test_invalid_config_fails_closed(self):
        (self.work / ".claude" / "gw.json").write_text("{not json")
        self.assertCi(self.ci(), 2, "config.py")

    # D20: ciIgnore -------------------------------------------------------------------------------------------------
    def test_ignored_red_foreign_status_does_not_block(self):
        self.config({"ciIgnore": ["Vercel"]})
        self.assertCi(self.ci(status=statuses(("Vercel", "failure"))), 0, "green", "ignored: Vercel")

    def test_ignored_pending_foreign_run_does_not_block(self):
        self.config({"ciIgnore": ["deploy-*"]})
        self.assertCi(self.ci(run=runs(("build", "success"), ("deploy-prod", None))), 0, "ignored: deploy-prod")

    def test_mixed_ignored_and_own_red_stays_red(self):
        self.config({"ciIgnore": ["Vercel"]})
        code, out = self.ci(run=runs(("build", "failure")), status=statuses(("Vercel", "failure")))
        self.assertEqual(code, 1, out)
        self.assertIn("build: failure", out)
        self.assertNotIn("Vercel: failure", out)

    def test_ignore_is_exact_and_case_sensitive(self):
        self.config({"ciIgnore": ["vercel"]})
        self.assertCi(self.ci(status=statuses(("Vercel", "failure"))), 1, "Vercel: failure")
        self.assertCi(self.ci(status=statuses(("vercel-preview", "failure"))), 1, "vercel-preview: failure")

    def test_star_matches_any_text_and_nothing_else_is_special(self):
        self.config({"ciIgnore": ["a.c", "x*z"]})
        self.assertCi(self.ci(status=statuses(("abc", "failure"))), 1, "abc: failure")  # `.` is not a regex
        self.assertCi(self.ci(status=statuses(("xyyz", "failure"))), 0, "green")

    def test_only_ignored_checks_reported_counts_as_no_ci(self):
        self.config({"ciIgnore": ["Vercel"]})
        self.assertCi(self.ci(run=runs(), status=statuses(("Vercel", "success"))), 1, "none", "no CI has reported")

    def test_ignore_flag_adds_to_the_config(self):
        self.config({"ciIgnore": ["Vercel"]})
        self.assertCi(self.ci("--ignore", "Netlify", status=statuses(("Vercel", "failure"), ("Netlify", "pending"))),
                      0, "green")

    def test_ciignore_validates_in_the_config(self):
        self.config({"ciIgnore": [""]})
        self.assertCi(self.ci(), 2, "ciIgnore")

    # D56: --failed ------------------------------------------------------------------------------------------------
    def test_failed_prints_the_step_its_error_lines_and_the_log_url(self):
        code, out = self.ci("--failed", run=runs(("build", "success"), ("macos", "failure")))
        self.assertCi((code, out), 1, "red", "macos: step 'Check' failed", JOB["html_url"], "Run bash tests/check.sh",
                      "FAIL: test_thing", "AssertionError: 1 != 2", "error: Process completed with exit code 1.")
        for gone in ("2026-11-10T", "shell: /usr/bin/bash", "checked out", "actions/cache/save", "Setting up"):
            self.assertNotIn(gone, out)  # timestamps, the folded command echo and the other steps

    def test_failed_caps_the_lines_from_the_config_and_the_flag(self):
        self.config({"ciFailedLines": 3})
        code, out = self.ci("--failed", run=runs(("build", "failure")))
        self.assertCi((code, out), 1, "Run bash tests/check.sh", "AssertionError", "exit code 1",
                      "4 earlier line(s) of the step left out", "--lines N")
        self.assertNotIn("FAIL: test_thing", out)  # the cut keeps the end, where the error is
        code, out = self.ci("--failed", "--lines", "20", run=runs(("build", "failure")))
        self.assertCi((code, out), 1, "== unit", "FAIL: test_thing")
        self.assertNotIn("left out", out)

    def test_failed_lines_must_be_positive(self):
        code, out = self.ci("--failed", "--lines", "0", run=runs(("build", "failure")))
        self.assertEqual(code, 2, out)
        self.assertIn("--lines must be 1 or more", out)

    def test_failed_lines_validates_in_the_config(self):
        self.config({"ciFailedLines": 0})
        self.assertCi(self.ci(), 2, "ciFailedLines")

    def test_failed_without_a_readable_job_gives_only_the_url(self):
        code, out = self.ci("--failed", run=runs(("lint-app", "failure")), env={"GH_NO_JOB": "1"})
        self.assertCi((code, out), 1, "lint-app; whole log: https://github.com/o/r/runs/100", "(no log:", "404")
        self.assertNotIn("Process completed", out)

    def test_failed_commit_status_gives_its_url(self):
        st = {"statuses": [{"context": "deploy", "state": "failure", "target_url": "https://ci.example/9"}]}
        self.assertCi(self.ci("--failed", status=st), 1, "deploy; whole log: https://ci.example/9")

    def test_failed_json_lists_each_job(self):
        code, out = self.ci("--failed", "--json", run=runs(("build", "failure")))
        self.assertEqual(code, 1, out)
        item, = json.loads(out)["failed"]
        self.assertEqual((item["name"], item["step"], item["url"], item["cut"]), ("build", "Check", JOB["html_url"], 0))
        self.assertEqual(item["lines"][0], "Run bash tests/check.sh")
        self.assertEqual(item["lines"][-1], "error: Process completed with exit code 1.")

    def test_failed_on_green_or_pending_reads_no_log(self):
        code, out = self.ci("--failed", env={"GH_LOG": "SHOULD NOT SHOW"})
        self.assertCi((code, out), 0, "green")
        self.assertNotIn("whole log", out)
        self.assertCi(self.ci("--failed", run=runs(("slow", None))), 1, "pending", "nothing has failed yet")

    def test_failed_on_jobs_github_never_started_says_so(self):
        data = runs(("build", "failure"))
        data["check_runs"][0]["output"] = {"title": "The job was not started because your account is locked due "
                                                    "to a billing issue", "summary": "spending limit needs to be "
                                                                                     "increased"}
        code, out = self.ci("--failed", run=data)
        self.assertCi((code, out), 1, "GitHub never started these jobs")
        self.assertNotIn("whole log", out)


class LogExcerpt(unittest.TestCase):
    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("ci_status", SCRIPT)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def test_a_log_without_error_lines_gives_its_tail(self):
        log = "\n".join(f"{STAMP}line {i}" for i in range(10))
        self.assertEqual(self.mod.log_excerpt(log, 3), (["line 7", "line 8", "line 9"], 7))

    def test_errors_without_a_step_header_start_at_the_top(self):
        self.assertEqual(self.mod.log_excerpt("a\n##[error]boom\nlater", 5), (["a", "error: boom"], 0))

    def test_the_last_error_picks_the_step_not_the_first(self):
        log = "\n".join(["##[group]Run flaky", "cmd", "##[endgroup]", "##[error]ignored (continue-on-error)",
                         "##[group]Run tests", "echo", "##[endgroup]", "FAILED test_x", "##[error]Process exited 1"])
        self.assertEqual(self.mod.log_excerpt(log, 10), (["Run tests", "FAILED test_x", "error: Process exited 1"], 0))

    def test_the_header_is_the_nearest_run_group_and_nested_groups_do_not_hide_errors(self):
        log = "\n".join(["##[group]Run tests", "echo", "##[endgroup]", "##[group]Nested", "inner", "##[error]inside",
                         "##[endgroup]", "##[error]end"])
        self.assertEqual(self.mod.log_excerpt(log, 10), (
            ["Run tests", "##[group]Nested", "inner", "error: inside", "##[endgroup]", "error: end"], 0))

    def test_without_a_run_group_the_nearest_group_is_the_header(self):
        log = "\n".join(["##[group]Set up job", "x", "##[endgroup]", "##[group]Post step", "y", "##[error]boom"])
        self.assertEqual(self.mod.log_excerpt(log, 10), (["Post step", "error: boom"], 0))

    def test_an_excerpt_never_exceeds_the_cap(self):
        log = "\n".join(["##[group]Run t", "e", "##[endgroup]", "l1", "l2", "l3", "##[error]boom"])
        self.assertEqual(self.mod.log_excerpt(log, 3), (["Run t", "l3", "error: boom"], 2))
        self.assertEqual(self.mod.log_excerpt(log, 1), (["error: boom"], 3))
        for cap in (1, 2, 3, 4, 5):
            lines, cut = self.mod.log_excerpt(log, cap)
            self.assertLessEqual(len(lines), cap)


if __name__ == "__main__":
    unittest.main()
