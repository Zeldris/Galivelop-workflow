"""scripts/revision-antes-de-main.sh, the PreToolUse hook that keeps unreviewed code and red CI out of the protected
branch through pull requests, against temporary repos: a bare "origin" plus a clone laid out like a project that
applied the workflow (test_ganchos.Project). The PR head is read from origin with `git ls-remote`; GitHub API calls go
to a fake `gh` (or a fake `curl`) on PATH that prints the canned JSON in GH_PR / GH_RUNS / GH_STATUS.

Covers the Installer's P1 list (docs/propuestas/2026-10-21-instalador-wmf-tarkor.md) plus VeriNews's `gh pr` in Bash
and commit statuses, and the portal's mark rule (ancestor with no code after it).
"""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_ganchos import ROOT, Project

FAKE_GH = """#!/bin/sh
case "$1" in
  auth) [ -z "${GH_UNAUTH:-}" ] || { echo "not logged in" >&2; exit 1; }; exit 0 ;;
  api) ;;
  *) echo "fake gh: unsupported $*" >&2; exit 1 ;;
esac
if [ -n "${GH_FAIL:-}" ]; then echo "gh: HTTP 502: Bad Gateway (fake)" >&2; exit 1; fi
case "$2" in
  *check-runs*) printf '%s' "$GH_RUNS" ;;
  */status*) printf '%s' "$GH_STATUS" ;;
  *pulls*) printf '%s' "$GH_PR" ;;
  *) echo "fake gh: unknown path $2" >&2; exit 1 ;;
esac
"""
# Answers like the API and records the header it got on stdin (the token must not be on the command line).
FAKE_CURL = """#!/bin/sh
cat > "$CURL_LOG"
for a in "$@"; do url="$a"; done
echo "$@" >> "$CURL_LOG"
case "$url" in
  *check-runs*) printf '%s' "$GH_RUNS" ;;
  */status*) printf '%s' "$GH_STATUS" ;;
  *pulls*) printf '%s' "$GH_PR" ;;
  *) exit 22 ;;
esac
"""
GREEN_RUNS = {"total_count": 1, "check_runs": [{"name": "comprobar", "status": "completed", "conclusion": "success"}]}
NO_STATUSES = {"state": "pending", "statuses": []}


class Hook(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-revision-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        p = self.p = Project(self.tmp)
        self.script = p.work / ".claude" / "gw" / "scripts" / "revision-antes-de-main.sh"
        shutil.copy2(ROOT / "scripts" / "revision-antes-de-main.sh", self.script)
        p.commit("add the hook")
        p.git("push", "-q", "--no-verify", "origin", "main")
        p.base = p.sha()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        for name, text in (("gh", FAKE_GH), ("curl", FAKE_CURL)):
            (self.bin / name).write_text(text)
            (self.bin / name).chmod(0o755)
        p.git("checkout", "-q", "-b", "feature")
        p.write("src/code.py", "x = 1\n"); p.commit("code"); self.code = p.sha()
        self.push()

    # helpers ------------------------------------------------------------------------------------------------------
    def push(self, branch="feature"):
        self.p.git("push", "-q", "--no-verify", "-f", "origin", f"HEAD:refs/heads/{branch}")

    def mark(self, sha=None):
        p = self.p
        p.write("docs/revisado.txt", (sha or p.sha()) + "\n"); p.commit("mark")
        return p.sha()

    def hook(self, tool, data, pr=None, runs=GREEN_RUNS, statuses=NO_STATUSES, env=None):
        event = json.dumps({"tool_name": tool, "tool_input": data})
        full = dict(self.p.env, PATH=f"{self.bin}:{self.p.env['PATH']}", GH_PR=json.dumps(pr or {}),
                    GH_RUNS=json.dumps(runs), GH_STATUS=json.dumps(statuses), CURL_LOG=str(self.tmp / "curl.log"))
        for name in ("GITHUB_TOKEN", "GH_TOKEN", "CLAUDE_PROJECT_DIR"):
            full.pop(name, None)
        full.update(env or {})
        # Run from outside the repo: the root must come from the script's path.
        r = subprocess.run(["bash", str(self.script)], input=event, capture_output=True, text=True, env=full,
                           cwd=self.tmp)
        return r.returncode, r.stdout + r.stderr

    def create(self, base="main", head="feature", **kw):
        return self.hook("mcp__github__create_pull_request",
                         {"owner": "o", "repo": "r", "base": base, "head": head, "title": "t"}, **kw)

    def pr(self, sha=None, base="main"):
        return {"base": {"ref": base}, "head": {"sha": sha or self.p.sha(), "ref": "feature"},
                "html_url": "https://github.com/o/r/pull/7"}

    def merge(self, tool="merge_pull_request", **kw):
        return self.hook(f"mcp__github__{tool}", {"owner": "o", "repo": "r", "pullNumber": 7}, **kw)

    def bash(self, command, **kw):
        return self.hook("Bash", {"command": command}, **kw)

    def assertBlocked(self, result, *texts):
        code, out = result
        self.assertEqual(code, 2, out)
        for text in texts:
            self.assertIn(text, out)

    def assertAllowed(self, result):
        code, out = result
        self.assertEqual(code, 0, out)

    # Installer P1 -------------------------------------------------------------------------------------------------
    def test_other_base_allowed(self):
        code, out = self.create(base="develop")
        self.assertEqual((code, out), (0, ""))

    def test_no_mark_blocked_with_the_fix(self):
        self.assertBlocked(self.create(), "no review mark", "src/code.py", "revisado.sh && git push")

    def test_mark_on_the_branch_head_on_github_allowed(self):
        self.mark(); self.push()
        self.assertAllowed(self.create())

    def test_reviewed_but_unpushed_blocked(self):
        self.mark()  # only local: origin/feature still has the unmarked code
        self.assertBlocked(self.create(), "no review mark", self.code[:12])

    def test_head_fetched_without_writing_refs(self):
        other = self.tmp / "other"
        self.p.git("clone", "-q", "--branch", "feature", str(self.p.bare), str(other), cwd=self.tmp)
        (other / "docs" / "revisado.txt").write_text(self.code + "\n")
        self.p.git("add", "-A", cwd=other); self.p.git("commit", "-q", "-m", "mark", cwd=other)
        self.p.git("push", "-q", "--no-verify", "origin", "HEAD:refs/heads/elsewhere", cwd=other)
        refs_before = self.p.git("for-each-ref").stdout
        self.assertAllowed(self.create(head="elsewhere"))
        self.assertEqual(self.p.git("for-each-ref").stdout, refs_before)

    def test_update_without_base_ignored(self):
        self.assertAllowed(self.hook("mcp__github__update_pull_request",
                                     {"owner": "o", "repo": "r", "pullNumber": 7, "title": "x"}))

    def test_update_to_protected_base_guarded_as_create(self):
        data = {"owner": "o", "repo": "r", "pullNumber": 7, "base": "main"}
        self.assertBlocked(self.hook("mcp__github__update_pull_request", data, pr=self.pr(base="develop")),
                           "no review mark")
        self.mark(); self.push()
        self.assertAllowed(self.hook("mcp__github__update_pull_request", data, pr=self.pr(base="develop"),
                                     runs={"total_count": 0, "check_runs": []}))

    def test_auto_merge_guarded_as_merge(self):
        self.mark(); self.push()
        red = {"total_count": 1, "check_runs": [{"name": "comprobar", "status": "in_progress", "conclusion": None}]}
        self.assertBlocked(self.merge("enable_pr_auto_merge", pr=self.pr(), runs=red), "not green",
                           "comprobar: in_progress")
        self.assertAllowed(self.merge("enable_pr_auto_merge", pr=self.pr()))

    def test_update_pull_request_branch_ignored(self):
        self.assertAllowed(self.hook("mcp__github__update_pull_request_branch",
                                     {"owner": "o", "repo": "r", "pullNumber": 7}))

    def test_head_as_owner_colon_branch(self):
        self.assertBlocked(self.create(head="someone:feature"), "no review mark")
        self.mark(); self.push()
        self.assertAllowed(self.create(head="someone:feature"))

    def test_origin_error_visible(self):
        self.p.git("remote", "set-url", "origin", str(self.tmp / "missing.git"))
        self.assertBlocked(self.create(), "cannot query origin", "missing.git", "ls-remote")

    def test_branch_not_on_origin_blocked(self):
        self.assertBlocked(self.create(head="nowhere"), "not on origin", "git push -u origin nowhere")

    # the mark rule (portal) ---------------------------------------------------------------------------------------
    def test_code_after_mark_blocked(self):
        self.mark()
        self.p.write("src/code.py", "x = 2\n"); self.p.commit("more code"); self.push()
        self.assertBlocked(self.create(), "code changed after the review mark")

    def test_only_content_after_mark_allowed(self):
        self.mark()
        self.p.write("docs/notes.md", "after review\n"); self.p.commit("content"); self.push()
        self.assertAllowed(self.create())

    def test_branch_with_only_content_needs_no_mark(self):
        p = self.p
        p.git("checkout", "-q", "-b", "texts", p.base)
        p.write("docs/notes.md", "just text\n"); p.commit("text"); self.push("texts")
        self.assertAllowed(self.create(head="texts"))

    def test_mark_from_another_branch_blocked(self):
        p = self.p
        p.git("checkout", "-q", "-b", "stray", p.base)
        p.write("src/other.py", "y = 1\n"); p.commit("other code")
        self.mark(self.code); self.push("stray")
        self.assertBlocked(self.create(head="stray"), "not an ancestor")

    # merge: CI ----------------------------------------------------------------------------------------------------
    def test_merge_green_and_marked_allowed(self):
        self.mark(); self.push()
        self.assertAllowed(self.merge(pr=self.pr(), statuses={"statuses": [{"context": "vercel", "state": "success"}]}))

    def test_merge_without_mark_blocked_even_with_green_ci(self):
        self.assertBlocked(self.merge(pr=self.pr()), "no review mark")

    def test_merge_red_check_run_blocked(self):
        self.mark(); self.push()
        runs = {"total_count": 2, "check_runs": [GREEN_RUNS["check_runs"][0],
                                                 {"name": "macos", "status": "completed", "conclusion": "failure"}]}
        self.assertBlocked(self.merge(pr=self.pr(), runs=runs), "not green", "macos: failure",
                           "https://github.com/o/r/pull/7")

    def test_merge_failed_commit_status_blocked(self):
        self.mark(); self.push()
        statuses = {"statuses": [{"context": "vercel", "state": "failure"}]}
        self.assertBlocked(self.merge(pr=self.pr(), statuses=statuses), "vercel: failure")

    def test_merge_with_no_ci_reported_blocked(self):
        self.mark(); self.push()
        self.assertBlocked(self.merge(pr=self.pr(), runs={"total_count": 0, "check_runs": []}), "no CI")

    def test_merge_to_other_base_allowed(self):
        self.assertAllowed(self.merge(pr=self.pr(base="develop")))

    def test_api_failure_blocks(self):
        self.mark(); self.push()
        self.assertBlocked(self.merge(pr=self.pr(), env={"GH_FAIL": "1"}), "502", "retry")

    def test_no_gh_auth_and_no_token_blocks(self):
        self.mark(); self.push()
        self.assertBlocked(self.merge(pr=self.pr(), env={"GH_UNAUTH": "1"}), "GITHUB_TOKEN")

    def test_token_fallback_uses_curl_with_token_on_stdin(self):
        self.mark(); self.push()
        token = "t0k3n-for-tests"
        self.assertAllowed(self.merge(pr=self.pr(), env={"GH_UNAUTH": "1", "GITHUB_TOKEN": token}))
        log = (self.tmp / "curl.log").read_text()
        self.assertIn(f"Authorization: Bearer {token}", log.splitlines()[0])
        self.assertNotIn(token, "\n".join(log.splitlines()[1:]))

    # Bash (VeriNews) ----------------------------------------------------------------------------------------------
    def test_gh_pr_create_to_main_guarded(self):
        self.assertBlocked(self.bash('git push && gh pr create --base main --title "x" --body "y"'), "no review mark")
        self.assertBlocked(self.bash("gh pr create --fill"), "no review mark")  # no --base: the default branch

    def test_gh_pr_create_to_other_base_allowed(self):
        self.assertAllowed(self.bash("gh pr create --base develop --fill"))
        self.assertAllowed(self.bash("gh pr create --base=develop --fill"))

    def test_gh_pr_merge_guarded_with_repo_flag(self):
        self.mark(); self.push()
        red = {"total_count": 1, "check_runs": [{"name": "linux", "status": "completed", "conclusion": "failure"}]}
        self.assertBlocked(self.bash("gh pr merge 7 -R o/r --squash", pr=self.pr(), runs=red), "linux: failure")
        self.assertAllowed(self.bash("gh pr merge 7 -R o/r --squash", pr=self.pr()))

    def test_text_that_mentions_gh_pr_not_guarded(self):
        self.assertAllowed(self.bash('grep "gh pr merge" docs/notes.md'))
        self.assertAllowed(self.bash("echo 'run gh pr create --base main later'"))

    def test_unrelated_tool_exits_0_silently(self):
        code, out = self.hook("Read", {"file_path": "/etc/hosts"})
        self.assertEqual((code, out), (0, ""))
        code, out = self.bash("ls -la")
        self.assertEqual((code, out), (0, ""))

    def test_missing_config_fails_closed_for_pr_calls_only(self):
        (self.p.work / ".claude" / "gw.json").unlink()
        self.assertAllowed(self.bash("ls"))
        self.assertBlocked(self.create(), "config")


if __name__ == "__main__":
    unittest.main()


class PreFilter(unittest.TestCase):
    """The matcher includes every Bash call: unrelated commands must pass even without python3."""

    def test_unrelated_bash_passes_without_python(self):
        tools = Path(tempfile.mkdtemp())
        try:
            for name in ("cat", "dirname"):
                (tools / name).symlink_to(shutil.which(name))
            hook = ROOT / "scripts" / "revision-antes-de-main.sh"
            r = subprocess.run([shutil.which("bash"), str(hook)], env={"PATH": str(tools)},
                               input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}),
                               capture_output=True, text=True)
            self.assertEqual((r.returncode, r.stderr), (0, ""))
        finally:
            shutil.rmtree(tools)
