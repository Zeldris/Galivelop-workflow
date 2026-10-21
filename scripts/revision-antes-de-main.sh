#!/usr/bin/env bash
# galivelop-workflow v0.1.0
# Claude Code PreToolUse hook: no pull request reaches the protected branch without /code-review of the same code,
# and none is merged with CI not green (plan §5.2). Reads the hook JSON (tool_name, tool_input) on stdin.
#   - Create: mcp__github__create_pull_request, mcp__github__update_pull_request that sets `base` to the protected
#     branch, and `gh pr create` typed in Bash (no --base = the default branch, taken as protected). The PR head is
#     the branch on GitHub, read with `git ls-remote origin` (never the local HEAD; nothing written under refs/).
#     Its commit must carry the config's `reviewMark` naming an ancestor with no code after it (es-codigo.sh). A head
#     that brings no code against the protected branch needs no mark.
#   - Merge: mcp__github__merge_pull_request, mcp__github__enable_pr_auto_merge and `gh pr merge` in Bash. Same
#     mark rule on the PR head, plus CI green: every check-run completed with success/neutral/skipped and every
#     commit status success (a commit with no CI reported at all is not green).
#   - Anything else (other tools, update_pull_request_branch, other bases, Bash that only mentions `gh pr`) exits 0
#     silently. pushToProtected does not matter: a PR is another way into the protected branch.
# GitHub API: `gh api` when gh is on PATH and authenticated, else curl with $GITHUB_TOKEN or $GH_TOKEN. No way to
# ask, or any API error: blocked (fail closed), as is any missing commit, config or script.
# Decision: exit 2 with the reason on stderr (Claude Code shows it to the agent); the last line is the command that
# fixes it. Exit 0 lets the call through. Never the JSON permissionDecision, so there is one way to read it.
# Project root: the git top level of this script's folder when it holds .claude/gw.json (the copy in
# .claude/gw/scripts); from the plugin cache, config.py's fallback (it is the only reader of the config).
# Bash 3.2 compatible; the logic is an embedded python3 (3.8+) run isolated (-I) so project files never shadow it.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
prog=""
IFS= read -r -d '' prog <<'PY' || true
import json, os, re, shlex, shutil, subprocess, sys

HERE = sys.argv[1]
NAME = "revision-antes-de-main"
GIT_ENV = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}
GIT_ENV["GIT_TERMINAL_PROMPT"] = "0"
GREEN_RUNS = ("success", "neutral", "skipped")


class Blocked(Exception):
    pass


class ApiError(Exception):
    pass


def block(*lines):
    raise Blocked("\n".join(lines))


def run(cmd, cwd=None, stdin=None):
    try:
        return subprocess.run(cmd, cwd=cwd, env=GIT_ENV, capture_output=True, text=True, input=stdin,
                              stdin=None if stdin is not None else subprocess.DEVNULL)
    except OSError as exc:
        return subprocess.CompletedProcess(cmd, 127, "", str(exc))


# ---- what the tool call does -------------------------------------------------------------------------------------
# Only as a command (start, or after ; & | ( ` or a newline, past VAR=x / env / command prefixes), never inside text
# that names it, e.g. grep "gh pr merge".
GH_PR = re.compile(r"(?:^|[;&|(`\n])\s*(?:\w+=\S*\s+)*(?:(?:env|command|exec|time|sudo)\s+)*gh\s+pr\s+(create|merge)\b"
                   r"([^;&|`)\n]*)")
MERGE_VALUE_FLAGS = {"-R", "--repo", "-b", "--body", "-F", "--body-file", "-t", "--subject", "-A",
                     "--author-email", "--match-head-commit"}


def flag(args, names):
    """Value of the last --name value / --name=value / -X value among args, or None."""
    value = None
    for i, a in enumerate(args):
        for n in names:
            if a == n and i + 1 < len(args):
                value = args[i + 1]
            elif n.startswith("--") and a.startswith(n + "="):
                value = a.split("=", 1)[1]
    return value


def from_bash(command):
    actions = []
    for m in GH_PR.finditer(command):
        try:
            args = shlex.split(m.group(2))
        except ValueError:
            args = m.group(2).split()
        repo = flag(args, ("-R", "--repo"))
        if m.group(1) == "create":
            actions.append({"kind": "create", "base": flag(args, ("-B", "--base")), "head": flag(args, ("-H", "--head")),
                            "repo": repo, "number": None, "how": "gh pr create"})
            continue
        selector, skip = None, False
        for a in args:
            if skip:
                skip = False
            elif a in MERGE_VALUE_FLAGS:
                skip = True
            elif not a.startswith("-") and selector is None:
                selector = a
        number, branch = None, None
        if selector:
            url = re.search(r"github\.com/([^/]+/[^/]+)/pull/(\d+)", selector)
            if url:
                repo, number = repo or url.group(1), url.group(2)
            elif selector.lstrip("#").isdigit():
                number = selector.lstrip("#")
            else:
                branch = selector
        actions.append({"kind": "merge", "base": None, "head": branch, "repo": repo, "number": number,
                        "how": "gh pr merge"})
    return actions


def classify(event):
    tool = str(event.get("tool_name") or "")
    data = event.get("tool_input") or {}
    if not isinstance(data, dict):
        data = {}
    if tool == "Bash":
        return from_bash(str(data.get("command") or ""))
    if not tool.startswith("mcp__"):
        return []
    name = tool.rsplit("__", 1)[-1]
    repo = None
    if data.get("owner") and data.get("repo"):
        repo = f"{data['owner']}/{data['repo']}"
    number = str(data["pullNumber"]) if data.get("pullNumber") not in (None, "") else None
    if name == "create_pull_request":
        return [{"kind": "create", "base": data.get("base") or None, "head": data.get("head") or None, "repo": repo,
                 "number": None, "how": "create_pull_request"}]
    if name == "update_pull_request":
        if not data.get("base"):
            return []  # editing title/body/state takes nothing to another branch
        return [{"kind": "retarget", "base": data["base"], "head": None, "repo": repo, "number": number,
                 "how": "update_pull_request"}]
    if name in ("merge_pull_request", "enable_pr_auto_merge"):
        return [{"kind": "merge", "base": None, "head": None, "repo": repo, "number": number, "how": name}]
    return []  # update_pull_request_branch and the rest bring nothing new to the protected branch


# ---- project, git and GitHub -------------------------------------------------------------------------------------
def project():
    sys.dont_write_bytecode = True  # never leave __pycache__ in the project's scripts folder
    sys.path.insert(0, HERE)
    try:
        import config  # the only reader of .claude/gw.json
    except ImportError as exc:
        block(f"cannot load config.py next to {HERE} ({exc}).", "reinstall the workflow: /gw-update")
    try:
        cfg = config.load()
    except config.ConfigError as exc:
        block(f"cannot read the project config: {exc}",
              f"fix it and retry: python3 {os.path.join(HERE, 'config.py')} validate")
    root = str(cfg["_root"])
    own = run(["git", "-C", HERE, "rev-parse", "--show-toplevel"]).stdout.strip()
    candidates = [os.path.join(root, ".claude", "gw", "scripts")]
    if own and os.path.realpath(own) == os.path.realpath(root):
        candidates.append(HERE)
    scripts = next((c for c in candidates if os.path.isfile(os.path.join(c, "es-codigo.sh"))), None)
    if scripts is None:
        block(f"the workflow scripts are missing in {root} (.claude/gw/scripts/es-codigo.sh).",
              "reinstall them: /gw-update")
    return cfg, root, scripts


def git(root, *args):
    return run(["git", "-C", root, *args])


def has_commit(root, sha):
    return git(root, "cat-file", "-e", sha + "^{commit}").returncode == 0


def remote_sha(root, branch):
    r = git(root, "ls-remote", "origin", "refs/heads/" + branch)
    if r.returncode != 0:
        block(f"cannot query origin for {branch}: {(r.stderr or r.stdout).strip()[:300]}",
              f"check the remote and the network, then retry: git -C {root} ls-remote origin refs/heads/{branch}")
    words = r.stdout.split()
    return words[0] if words else None


def ensure(root, sha, refs):
    """Make sha present locally, fetching refs from origin without writing any ref (nor FETCH_HEAD when possible)."""
    if has_commit(root, sha):
        return True
    for ref in refs:
        if not ref:
            continue
        # --refmap= stops git updating refs/remotes/origin/<branch> on its own.
        r = git(root, "fetch", "-q", "--no-write-fetch-head", "--refmap=", "origin", ref)
        if r.returncode != 0 and "no-write-fetch-head" in r.stderr:
            git(root, "fetch", "-q", "--refmap=", "origin", ref)  # git < 2.29: FETCH_HEAD only, still no ref
        if has_commit(root, sha):
            return True
    return False


def origin_repo(root):
    url = git(root, "remote", "get-url", "origin").stdout.strip()
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def api(path):
    if shutil.which("gh") and run(["gh", "auth", "status"]).returncode == 0:
        r, how = run(["gh", "api", path]), "gh api " + path
    else:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            raise ApiError("gh is not installed or not authenticated, and neither GITHUB_TOKEN nor GH_TOKEN is set")
        if not shutil.which("curl"):
            raise ApiError("gh is not authenticated and curl is not installed")
        # The token goes on stdin (-H @-), never on the command line where other processes could read it.
        r = run(["curl", "-sS", "-f", "-L", "-H", "Accept: application/vnd.github+json",
                 "-H", "X-GitHub-Api-Version: 2022-11-28", "-H", "@-", "https://api.github.com/" + path],
                stdin=f"Authorization: Bearer {token}\n")
        how = "GET https://api.github.com/" + path
    if r.returncode != 0:
        raise ApiError(f"{how} failed: {(r.stderr or r.stdout).strip()[:300]}")
    try:
        return json.loads(r.stdout)
    except ValueError:
        raise ApiError(f"{how} did not return JSON: {r.stdout.strip()[:200]}")


def pr_info(repo, number):
    try:
        info = api(f"repos/{repo}/pulls/{number}")
        return {"base": info["base"]["ref"], "sha": info["head"]["sha"], "ref": info["head"]["ref"],
                "url": info.get("html_url") or f"https://github.com/{repo}/pull/{number}"}
    except ApiError as exc:
        block(f"cannot read PR #{number} of {repo}: {exc}",
              "authenticate (gh auth login, or export GITHUB_TOKEN) and retry; blocked because it could not be checked")
    except (KeyError, TypeError) as exc:
        block(f"PR #{number} of {repo}: unexpected API answer (missing {exc}).",
              f"check the PR at https://github.com/{repo}/pull/{number} and retry")


def ci_problems(repo, sha):
    runs, page = [], 1
    while True:
        data = api(f"repos/{repo}/commits/{sha}/check-runs?per_page=100&page={page}")
        batch = data["check_runs"]
        runs += batch
        if not batch or len(runs) >= int(data.get("total_count", len(runs))) or page >= 10:
            break
        page += 1
    statuses = api(f"repos/{repo}/commits/{sha}/status?per_page=100")["statuses"]
    if not runs and not statuses:
        return ["no CI has reported on this commit yet"]
    bad = [f"{c.get('name', '?')}: {c.get('conclusion') or c.get('status')}" for c in runs
           if c.get("status") != "completed" or c.get("conclusion") not in GREEN_RUNS]
    bad += [f"{s.get('context', '?')}: {s.get('state')}" for s in statuses if s.get("state") != "success"]
    return bad


# ---- the rules ---------------------------------------------------------------------------------------------------
def es_codigo(root, scripts, a, b):
    r = run(["bash", os.path.join(scripts, "es-codigo.sh"), a, b], cwd=root)
    if r.returncode != 0:
        block(f"cannot tell code from content: {r.stderr.strip()[:400]}",
              f"fix the error above and retry: git -C {root} fetch origin")
    return [line for line in r.stdout.splitlines() if line.strip()]


def check_mark(cfg, root, scripts, head, refs, what):
    protected, mark_file = cfg["protectedBranch"], cfg["reviewMark"]
    fix = (f"run /code-review of the diff against origin/{protected}, push the fixes, then mark and push: "
           f"bash {os.path.join(scripts, 'revisado.sh')} && git push")
    if not ensure(root, head, refs):
        block(f"the PR head {head[:12]} ({what}) is not in this clone and could not be fetched from origin.",
              f"fetch it and retry: git -C {root} fetch origin {refs[0] if refs else ''}".rstrip())
    tip = remote_sha(root, protected)
    base = ""
    if tip:
        if not ensure(root, tip, [protected]):
            block(f"origin/{protected} is at {tip[:12]}, which this clone cannot fetch.",
                  f"fetch it and retry: git -C {root} fetch origin {protected}")
        mb = git(root, "merge-base", tip, head)
        base = mb.stdout.strip() if mb.returncode == 0 else ""
    code = es_codigo(root, scripts, base, head)
    if not code:
        return  # only content against the protected branch: no review needed
    mark = "".join(git(root, "show", f"{head}:{mark_file}").stdout.split())
    if not mark:
        reason = f"the PR head {head[:12]} ({what}) has no review mark ({mark_file})"
    elif not has_commit(root, mark):
        reason = f"the review mark ({mark_file}) names {mark[:12]}, which is not a commit in this clone"
    elif git(root, "merge-base", "--is-ancestor", mark, head).returncode != 0:
        reason = f"the review mark ({mark[:12]}) is not an ancestor of the PR head {head[:12]} ({what})"
    else:
        after = es_codigo(root, scripts, mark, head)
        if not after:
            return
        reason, code = f"code changed after the review mark ({mark[:12]}) on the PR head {head[:12]} ({what})", after
    listed = [f"  {path}" for path in code[:10]] + ([f"  … and {len(code) - 10} more"] if len(code) > 10 else [])
    block(f"Blocked: {reason}; this PR brings unreviewed code to {protected}:", *listed, fix)


def head_from_branch(root, branch, how):
    branch = branch.split(":")[-1]  # head may come as owner:branch
    sha = remote_sha(root, branch)
    if not sha:
        block(f"the PR branch {branch} is not on origin ({how}), so its reviewed commit cannot be checked.",
              f"push it and retry: git push -u origin {branch}")
    return sha, branch


def need_repo(action, root):
    repo = action["repo"] or origin_repo(root)
    if not repo:
        block(f"cannot tell the GitHub owner/repo for {action['how']} (no owner/repo in the call, origin is not "
              "a github.com URL).", "pass it explicitly and retry, e.g.: gh pr merge <number> -R <owner>/<repo>")
    return repo


def handle(action, cfg, root, scripts):
    protected = cfg["protectedBranch"]
    if action["kind"] in ("create", "retarget") and action["base"] and action["base"] != protected:
        return
    if action["kind"] == "create":
        branch = action["head"]
        if not branch:
            branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
            if not branch or branch == "HEAD":
                block(f"{action['how']}: no --head given and the checkout is not on a branch.",
                      "switch to the PR branch and retry: git switch <branch>")
        sha, branch = head_from_branch(root, branch, action["how"])
        check_mark(cfg, root, scripts, sha, [branch], f"origin/{branch}")
        return
    repo = need_repo(action, root)
    number = action["number"]
    if number is None and action["kind"] == "merge":
        branch = action["head"] or git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        owner = repo.split("/")[0]
        try:
            found = api(f"repos/{repo}/pulls?head={owner}:{branch}&state=open")
            number = str(found[0]["number"]) if found else None
        except (ApiError, KeyError, TypeError, IndexError) as exc:
            block(f"cannot find the open PR of {branch} in {repo}: {exc}",
                  "pass the PR number and retry: gh pr merge <number>")
        if number is None:
            block(f"no open PR for {branch} in {repo}.", "pass the PR number and retry: gh pr merge <number>")
    if number is None:
        block(f"{action['how']} without a PR number; cannot check it.", "pass pullNumber and retry")
    info = pr_info(repo, number)
    if action["kind"] == "merge" and info["base"] != protected:
        return
    refs = [info["ref"], f"refs/pull/{number}/head"]
    check_mark(cfg, root, scripts, info["sha"], refs, f"PR #{number}")
    if action["kind"] != "merge":
        return
    try:
        bad = ci_problems(repo, info["sha"])
    except (ApiError, KeyError, TypeError, ValueError) as exc:
        block(f"Blocked: could not verify CI of PR #{number} ({info['sha'][:12]}): {exc}",
              f"check CI in the PR ({info['url']}); once it is all green, authenticate (gh auth login, or export "
              "GITHUB_TOKEN) and retry the merge")
    if bad:
        block(f"Blocked: CI of PR #{number} ({info['sha'][:12]}) is not green: {'; '.join(bad)}",
              f"wait until every check passes ({info['url']}), fix what failed if needed, then retry the merge")


def main():
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except ValueError as exc:
        block(f"the hook input is not JSON ({exc}).", "report it: Claude Code sent an unexpected payload")
    actions = classify(event if isinstance(event, dict) else {})
    if not actions:
        return
    cfg, root, scripts = project()
    for action in actions:
        handle(action, cfg, root, scripts)


try:
    main()
except Blocked as exc:
    for line in str(exc).splitlines():
        print(f"{NAME}: {line}", file=sys.stderr)
    sys.exit(2)
except Exception as exc:  # fail closed on anything unexpected
    print(f"{NAME}: unexpected error ({type(exc).__name__}: {exc}); blocked because it could not be checked.",
          file=sys.stderr)
    print(f"{NAME}: fix or report it, then retry: bash {os.path.join(HERE, 'revision-antes-de-main.sh')} < input.json",
          file=sys.stderr)
    sys.exit(2)
PY
input="$(cat)"
# Cheap pre-filter: the matcher includes every Bash call, so anything that cannot be a PR action leaves here without
# needing python3 (a missing python3 must not block unrelated commands). Only PR tools or text with "gh" and "pr" go on.
case "$input" in
  *pull_request*|*auto_merge*|*gh*pr*) ;;
  *) exit 0 ;;
esac
printf '%s' "$input" | python3 -I -c "$prog" "$here"
status=$?
if [ "$status" -ne 0 ] && [ "$status" -ne 2 ]; then  # python3 missing or crashed: still fail closed
  echo "revision-antes-de-main: the check could not run (exit $status); blocked. Install python3 3.8+ and retry: python3 --version" >&2
  exit 2
fi
exit "$status"
