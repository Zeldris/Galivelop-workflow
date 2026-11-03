"""scripts/ci-status.py, the GitHub Actions status reader, against a fake `gh` (or fake `curl`) on PATH: no network.
The fake prints the canned JSON in GH_RUNS / GH_STATUS / GH_COMMIT."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
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
  */commits/*/check-runs*) printf '%s' "$GH_RUNS" ;;
  */commits/*/status*) printf '%s' "$GH_STATUS" ;;
  */commits/*) printf '%s' "$GH_COMMIT" ;;
  *) echo "fake gh: unknown path $2" >&2; exit 1 ;;
esac
"""
FAKE_CURL = """#!/bin/sh
cat > "$CURL_LOG"
for a in "$@"; do url="$a"; done
case "$url" in
  *check-runs*) printf '%s' "$GH_RUNS" ;;
  */status*) printf '%s' "$GH_STATUS" ;;
  *) exit 22 ;;
esac
"""


def runs(*items):
    return {"total_count": len(items), "check_runs": [
        {"name": n, "status": "completed" if c else "in_progress", "conclusion": c} for n, c in items]}


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
                    GH_COMMIT=json.dumps({"sha": "b" * 40}), CURL_LOG=str(self.tmp / "curl.log"))
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

    def test_pending_check_run_is_pending_not_red(self):
        self.assertCi(self.ci(run=runs(("build", "success"), ("slow", None))), 1, "pending", "slow: in_progress")

    def test_pending_commit_status(self):
        self.assertCi(self.ci(status=statuses(("deploy", "pending"))), 1, "pending", "deploy: pending")

    def test_failed_status_is_red_even_with_a_pending_run(self):
        self.assertCi(self.ci(run=runs(("slow", None)), status=statuses(("deploy", "failure"))), 1, "red")

    def test_no_ci_reported(self):
        self.assertCi(self.ci(run=runs()), 1, "none", "no CI has reported")

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


if __name__ == "__main__":
    unittest.main()
