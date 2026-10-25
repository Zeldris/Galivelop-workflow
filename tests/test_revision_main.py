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
import time
import unittest
from pathlib import Path

from test_ganchos import ROOT, Project

FAKE_GH = """#!/bin/sh
case "$1" in
  auth) echo "fake gh: the hook must check access by reading the repo, not gh auth status" >&2; exit 1 ;;
  api) ;;
  *) echo "fake gh: unsupported $*" >&2; exit 1 ;;
esac
# Like a GitHub App installation token: /user is 403, the repo itself can be read.
[ "$2" != "user" ] || { echo "gh: Resource not accessible by integration (HTTP 403)" >&2; exit 1; }
case "$2" in
  repos/*/*/*) ;;
  repos/*/*)
    [ -z "${GH_UNAUTH:-}" ] || { echo "not logged in" >&2; exit 1; }
    if [ -n "${GH_AUTH_ONCE:-}" ]; then [ ! -e "$GH_AUTH_ONCE" ] || exit 1; : > "$GH_AUTH_ONCE"; fi
    [ -z "${GH_PROBE_LOG:-}" ] || echo "$2" >> "$GH_PROBE_LOG"
    echo '{"full_name":"x"}'; exit 0 ;;
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

    def relax(self, **changes):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg.update(changes)
        p.write(".claude/gw.json", json.dumps(cfg)); p.commit("relax the rule"); self.push()

    def test_pr_cannot_widen_content_to_pass_its_own_code(self):
        self.relax(content=[".*"])
        self.assertBlocked(self.create(), "no review mark", ".claude/gw.json", "src/code.py")

    def test_pr_cannot_unprotect_its_base(self):
        self.relax(protectedBranch="release")
        self.assertBlocked(self.create(), "no review mark")
        self.assertBlocked(self.merge(pr=self.pr()), "no review mark")

    def test_pr_cannot_move_the_mark_to_a_file_it_writes(self):
        p = self.p
        self.relax(reviewMark="src/mark.txt")
        p.write("src/mark.txt", p.sha() + "\n"); p.commit("own mark"); self.push()
        self.assertBlocked(self.create(), "no review mark (docs/revisado.txt)")

    def test_reviewed_config_change_allowed(self):
        self.relax(content=[".*"])
        self.mark(); self.push()
        self.assertAllowed(self.create())

    def test_pr_to_an_open_branch_with_an_invalid_config_allowed(self):
        p = self.p
        p.git("checkout", "-q", "-b", "wip", p.base)
        p.write(".claude/gw.json", "{not json"); p.commit("broken config"); self.push("wip")
        p.git("checkout", "-q", "feature")
        self.assertAllowed(self.create(base="wip"))

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
        self.assertBlocked(self.merge(pr=self.pr(), runs={"total_count": 0, "check_runs": []}), "no CI",
                           "checked only locally", "with their confirmation")

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

    def test_gh_pr_merge_with_global_repo_flag_guarded(self):
        self.assertBlocked(self.bash("gh -R o/r pr merge 7 --squash", pr=self.pr()), "no review mark")
        self.assertBlocked(self.bash("gh --repo o2/r2 pr merge 7", pr=self.pr(), env={"GH_FAIL": "1"}),
                           "PR #7 of o2/r2")
        self.assertBlocked(self.bash("GH_REPO=o3/r3 gh pr merge 7", pr=self.pr(), env={"GH_FAIL": "1"}),
                           "PR #7 of o3/r3")

    def test_gh_pr_merge_inside_a_shell_or_eval_guarded(self):
        for command in ('bash -c "gh pr merge 7 -R o/r"', "sh -c 'gh pr merge 7 -R o/r --squash'",
                        'zsh -lc "cd x && gh -R o/r pr merge 7"', 'eval "gh pr merge 7 -R o/r"', "eval gh pr merge 7 -R o/r"):
            self.assertBlocked(self.bash(command, pr=self.pr()), "no review mark")

    def test_gh_pr_with_tabs_and_escaped_newlines_guarded(self):
        # The pre-filter reads the raw JSON, where a tab is `\t` and a newline `\n` (backslash + letter): those are
        # word separators, and a backslash-newline continuation joins the words of one command.
        for command in ("gh\tpr\tmerge 7 -R o/r", "gh\tpr\tmerge\t7\t-R\to/r", "gh \\\npr merge 7 -R o/r",
                        "gh\\\npr merge 7 -R o/r", "gh pr \\\n  merge 7 -R o/r", "gh pr\\\r\nmerge 7 -R o/r",
                        "gh\tapi\t-X\tPUT\trepos/o/r/pulls/7/merge", "gh api -X PUT repos/o/r/pulls/7/\\\nmerge"):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(command, pr=self.pr()), "no review mark")
        for command in ("gh\tpr\tcreate\t--base\tmain", "gh \\\npr \\\ncreate --fill", "gh\\\npr create --fill"):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(command), "no review mark")
        self.assertAllowed(self.bash("gh\tpr\tcreate\t--base\tdevelop"))
        self.assertAllowed(self.bash("gh\tpr\tview\t7"))

    def test_gh_pr_merge_through_xargs_guarded(self):
        code, out = self.bash("echo 7 | xargs gh pr merge", pr=self.pr())
        self.assertEqual(code, 2, out)
        self.assertBlocked(self.bash("echo 7 | xargs -n 1 gh pr merge 7 -R o/r", pr=self.pr()), "no review mark")

    def test_gh_api_merge_guarded(self):
        for command in ("gh api -X PUT repos/o/r/pulls/7/merge", "gh api --method PUT /repos/o/r/pulls/7/merge",
                        "gh api --method=PUT repos/o/r/pulls/7/merge", "gh api repos/o/r/pulls/7/merge -f merge_method=squash"):
            self.assertBlocked(self.bash(command, pr=self.pr()), "no review mark")
        # {owner}/{repo}: gh fills them from the current repo, here not on github.com, so it cannot be checked
        self.assertBlocked(self.bash("gh api -XPUT 'repos/{owner}/{repo}/pulls/7/merge'", pr=self.pr()), "owner/repo")
        self.assertBlocked(self.bash("gh api -X PUT repos/o4/r4/pulls/7/merge", pr=self.pr(), env={"GH_FAIL": "1"}),
                           "PR #7 of o4/r4")
        self.assertAllowed(self.bash("gh api repos/o/r/pulls/7/merge"))  # GET: is it merged?
        self.assertAllowed(self.bash("gh api repos/o/r/pulls/7"))

    def test_long_unparseable_commands_are_judged_in_under_a_second(self):
        # P4 of docs/propuestas/2026-10-25-repos-x.md: the old SUSPECT regex chained three `[\\s\\S]*` and backtracked
        # for minutes on ~50 KB of `gh pr gh pr ...`. A hook that slow would stall every Bash call of every session.
        cases = {
            "gh pr tokens": ('echo "unterminated ' + "gh pr " * 8000, " merge"),
            "pulls/ words": ('echo "unterminated gh ' + "pulls/x " * 6000, " pulls/merge"),
            "pulls/ in one token": ('echo "unterminated gh ' + "pulls/" * 8000, "merge"),
            "tabs and continuations": ('echo "unterminated gh\t' + "pr\t\\\n" * 10000, " merge"),
        }
        for name, (head, tail) in cases.items():
            with self.subTest(name=name):
                self.assertGreater(len(head), 45000)
                start = time.monotonic()
                allowed = self.bash(head)
                self.assertLess(time.monotonic() - start, 1.0, f"{name}: allowed case took 1 s or more")
                self.assertAllowed(allowed)
                start = time.monotonic()
                blocked = self.bash(head + tail)
                self.assertLess(time.monotonic() - start, 1.0, f"{name}: blocked case took 1 s or more")
                self.assertBlocked(blocked, "cannot parse")

    def test_unparseable_command_that_looks_like_a_merge_blocked(self):
        self.assertBlocked(self.bash('gh pr merge 7 --body "unterminated'), "cannot parse")
        self.assertAllowed(self.bash('echo "unterminated'))

    def test_api_backend_is_decided_once(self):
        self.mark(); self.push()
        env = {"GH_AUTH_ONCE": str(self.tmp / "authed"), "GITHUB_TOKEN": "t0k3n"}  # gw-allow-secret: fake token for the test
        self.assertAllowed(self.merge(pr=self.pr(), env=env))
        self.assertFalse((self.tmp / "curl.log").exists(), "gh and curl mixed in one run")

    def test_text_that_mentions_gh_pr_not_guarded(self):
        self.assertAllowed(self.bash('grep "gh pr merge" docs/notes.md'))
        self.assertAllowed(self.bash("echo 'run gh pr create --base main later'"))
        self.assertAllowed(self.bash('git commit -m "gh pr merge after review"'))

    def test_closed_or_merged_pr_says_so_instead_of_asking_for_a_config(self):
        for state, merged, text in (("closed", False, "is closed"), ("closed", True, "already merged")):
            pr = dict(self.pr(), state=state, merged=merged)
            self.assertBlocked(self.merge(pr=pr), text, "gh pr view 7 -R o/r")
            code, out = self.merge(pr=pr)
            self.assertNotIn("gw.json", out)
        # even when the PR's branch is gone or carries no config
        self.assertBlocked(self.bash("gh pr merge 7 -R o/r", pr=dict(self.pr(), state="closed")), "is closed")
        self.assertBlocked(self.merge(pr=dict(self.pr(), state="closed", merged_at="2026-10-01T00:00:00Z")),
                           "already merged")

    def test_access_is_checked_by_reading_the_repo_not_user(self):
        """A GitHub App installation token gets 403 on /user but can read the repo (the fake gh behaves so)."""
        self.mark(); self.push()
        probes = self.tmp / "probes.log"
        self.assertAllowed(self.merge(pr=self.pr(), env={"GH_PROBE_LOG": str(probes)}))
        self.assertFalse((self.tmp / "curl.log").exists())  # the fake gh refuses `gh auth status`: it would fall to curl
        self.assertEqual(probes.read_text().split(), ["repos/o/r"])

    def test_no_access_to_the_repo_and_no_token_fails_closed(self):
        self.mark(); self.push()
        self.assertBlocked(self.merge(pr=self.pr(), env={"GH_UNAUTH": "1"}),
                           "cannot read repos/o/r", "GITHUB_TOKEN")

    def test_update_that_reopens_a_closed_pr_is_judged_like_an_open_one(self):
        closed = dict(self.pr(), state="closed", merged=False)
        update = {"owner": "o", "repo": "r", "pullNumber": 7, "base": "main"}
        reopen = dict(update, state="open")
        self.assertBlocked(self.hook("mcp__github__update_pull_request", update, pr=closed), "is closed")
        code, out = self.hook("mcp__github__update_pull_request", reopen, pr=closed)
        self.assertEqual(code, 2, out)
        self.assertNotIn("is closed", out)
        self.assertIn("no review mark", out)  # judged on its head like any other retarget
        self.mark(); self.push()
        self.assertAllowed(self.hook("mcp__github__update_pull_request", reopen, pr=dict(closed, head={"sha": self.p.sha(), "ref": "feature"})))
        merged = dict(closed, merged=True)
        self.assertBlocked(self.hook("mcp__github__update_pull_request", reopen, pr=merged), "already merged")

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
    """The matcher includes every Bash call: unrelated commands must pass even without python3, and without starting it."""

    def setUp(self):
        self.tools = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tools, True)
        for name in ("cat", "dirname"):
            (self.tools / name).symlink_to(shutil.which(name))
        self.hook = ROOT / "scripts" / "revision-antes-de-main.sh"

    def run_hook(self, tool, data):
        return subprocess.run([shutil.which("bash"), str(self.hook)], env={"PATH": str(self.tools)},
                              input=json.dumps({"tool_name": tool, "tool_input": data}), capture_output=True, text=True)

    def bash(self, command):
        r = self.run_hook("Bash", {"command": command})
        return r.returncode, r.stderr

    def test_unrelated_bash_passes_without_python(self):
        self.assertEqual(self.bash("ls -la"), (0, ""))

    def test_github_and_projects_are_not_gh_and_pr(self):
        stub = self.tools / "python3"  # records that it started
        stub.write_text(f'#!/bin/sh\n: > "{self.tools}/started"\nexit 5\n')
        stub.chmod(0o755)
        for command in ("grep -rn github projects/", "cat docs/github-projects.md", "git clone https://github.com/o/r",
                        "echo ghost pr", "ls gh-pages/pr"):
            self.assertEqual(self.bash(command), (0, ""), command)
        self.assertFalse((self.tools / "started").exists(), "python3 was started for an unrelated command")
        self.assertEqual(self.run_hook("Write", {"content": "gh pr merge 7"}).returncode, 0)
        self.assertEqual(self.run_hook("mcp__github__pull_request_read", {"pullNumber": 7}).returncode, 0)
        self.assertFalse((self.tools / "started").exists())

    def test_real_pr_commands_do_start_python(self):
        stub = self.tools / "python3"
        stub.write_text(f'#!/bin/sh\n: > "{self.tools}/started"\nexit 2\n')
        stub.chmod(0o755)
        for command in ("gh pr merge 7", "cd x && gh -R o/r pr create --base main", "echo a\ngh pr view 7",
                        "GH_REPO=o/r gh api -X PUT repos/o/r/pulls/7/merge"):
            (self.tools / "started").unlink(missing_ok=True)
            self.assertEqual(self.bash(command)[0], 2, command)
            self.assertTrue((self.tools / "started").exists(), command)

    def test_tabs_and_escaped_newlines_are_separators_in_the_prefilter(self):
        stub = self.tools / "python3"
        stub.write_text(f'#!/bin/sh\n: > "{self.tools}/started"\nexit 2\n')
        stub.chmod(0o755)
        for command in ("gh\tpr\tmerge 7", "gh\tpr\tcreate", "gh \\\npr merge 7", "gh\\\npr merge 7", "gh pr\\\r\nmerge 7",
                        "x\tgh\tapi\t-X\tPUT\trepos/o/r/pulls/7/merge", "a;\tgh\tpr\tmerge"):
            (self.tools / "started").unlink(missing_ok=True)
            self.assertEqual(self.bash(command)[0], 2, repr(command))
            self.assertTrue((self.tools / "started").exists(), repr(command))
        (self.tools / "python3").unlink()  # unrelated or read-only calls must pass without python3
        for command in ("gh\tpr\tview\t7", "echo\tghost\tpr\tmerge", "grep\tgithub\tprojects/"):
            self.assertEqual(self.bash(command), (0, ""), repr(command))
        for command in ("gh\tpr\tmerge 7", "gh \\\npr create"):
            code, err = self.bash(command)
            self.assertEqual(code, 2, repr(command))
            self.assertIn("python3 is missing", err)

    def test_without_python_a_pr_call_fails_closed_and_an_unrelated_gh_call_passes(self):
        for command in ("gh pr merge 7", "gh pr create --fill", "cd r && gh api -X PUT repos/o/r/pulls/7/merge",
                        "true\ngh pr merge 7"):
            code, err = self.bash(command)
            self.assertEqual(code, 2, command)
            self.assertIn("python3 is missing", err)
            self.assertIn("python3 --version", err)
        for command in ("gh pr view 7", "gh pr list --state open", "gh api repos/o/r/pulls/7"):
            self.assertEqual(self.bash(command), (0, ""), command)
        for tool in ("create_pull_request", "update_pull_request", "merge_pull_request", "enable_pr_auto_merge"):
            r = self.run_hook(f"mcp__github__{tool}", {"owner": "o", "repo": "r"})
            self.assertEqual(r.returncode, 2, tool)
            self.assertIn("python3 is missing", r.stderr)
        self.assertEqual(self.run_hook("mcp__github__update_pull_request_branch", {}).returncode, 0)

    def test_empty_and_odd_input_without_python(self):
        for text in ("", "not json", "{}"):
            r = subprocess.run([shutil.which("bash"), str(self.hook)], env={"PATH": str(self.tools)}, input=text,
                               capture_output=True, text=True)
            self.assertEqual((r.returncode, r.stderr), (0, ""), repr(text))
