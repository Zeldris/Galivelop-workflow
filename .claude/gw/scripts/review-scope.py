#!/usr/bin/env python3
# galivelop-workflow v0.5.1
"""The files the phase 1 `/code-review` reads before the protected branch: the branch's diff without `vendored` files (D82).

  python3 review-scope.py [--base REV] [--workflow DIR] [--all]

Prints, one repo-relative path per line, the files changed between BASE (default `origin/<protectedBranch>`, else the
local protected branch) and HEAD. A file is `vendored` when the project holds it as an unchanged copy of the workflow
(`apply.py --vendored`: `.claude/gw/`, `.claude/skills/gw-*`, `.githooks/`, `.claude/agents/`, the CI file): the workflow
repo reviewed it already, so it stays out. A vendored file the project edited no longer matches the workflow's copy and
stays in; so does a file the project made its own (`ownedFiles`) and anything not copied from the workflow. A renamed
file is listed by its new path (a rename is read as the old path deleted and the new one added). Content is compared on
the working tree: review a clean checkout of the commit. Deleted files are listed (there is nothing left to compare).

The workflow copy that says what is vendored is `--workflow DIR`, else the env var GW_WORKFLOW, else this script's own
repo when that is the workflow. Without one the whole diff is printed, with a note on stderr saying so (reviewing too
much is the safe side). `--all` prints the whole diff without asking. Fails closed on what it cannot know: an invalid
config, a git error or a `--base` that is not a commit -> exit 2 with what fixes it. Python 3.8+ standard library only.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, str(HERE))
import config  # noqa: E402

PROG = "review-scope"


class ScopeError(Exception):
    pass


def git(root, *args):
    r = subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=false", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise ScopeError(f"git {' '.join(args)} failed: {r.stderr.strip() or r.returncode}; check the repository: "
                         "git status")
    return r.stdout


def has_ref(root, ref):
    return subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "-q", ref + "^{commit}"],
                          capture_output=True).returncode == 0


def default_base(root, cfg):
    branch = cfg.get("protectedBranch") or "main"
    for ref in (f"refs/remotes/origin/{branch}", f"refs/heads/{branch}"):
        if has_ref(root, ref):
            return ref
    raise ScopeError(f"no origin/{branch} nor {branch} to diff against; give the base: "
                     f"python3 {Path(__file__).name} --base <commit>")


def changed(root, base):
    """Paths changed since the merge base of BASE and HEAD (no rename detection: old and new path both appear)."""
    out = git(root, "diff", "--name-only", "-z", "--no-renames", f"{base}...HEAD")
    return [p for p in out.split("\0") if p]


def workflow_dir(arg):
    for cand in (arg, os.environ.get("GW_WORKFLOW"), str(HERE.parent)):
        if cand and (Path(cand) / "scripts" / "apply.py").is_file() and (Path(cand) / "skills").is_dir():
            return Path(cand)
    return None


def vendored(root, workflow):
    r = subprocess.run([sys.executable, "-B", str(workflow / "scripts" / "apply.py"), "--vendored", str(root)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise ScopeError(f"apply.py --vendored failed: {r.stderr.strip() or r.stdout.strip()}; run it by hand: "
                         f"python3 {workflow / 'scripts' / 'apply.py'} --vendored {root}")
    return set(r.stdout.split("\n")) - {""}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", help="the diff starts at the merge base with this commit (default origin/<protectedBranch>)")
    ap.add_argument("--workflow", help="the workflow repo whose copies are vendored (default $GW_WORKFLOW, else this repo)")
    ap.add_argument("--all", action="store_true", help="the whole diff, nothing left out")
    args = ap.parse_args(argv)
    try:
        root = config.find_root()
        cfg = config.load(str(root))
        base = args.base or default_base(root, cfg)
        if not has_ref(root, base):
            raise ScopeError(f"--base {base} is not a commit; give one that is: git log --oneline")
        paths = changed(root, base)
        skip = set()
        if not args.all:
            workflow = workflow_dir(args.workflow)
            if workflow is None:
                print(f"{PROG}: no workflow repo to compare with, so the whole diff is listed; give it: "
                      f"python3 {Path(__file__).name} --workflow <workflow repo>", file=sys.stderr)
            else:
                skip = vendored(root, workflow)
        for p in paths:
            if p not in skip:
                print(p)
        if skip:
            left = sum(1 for p in paths if p in skip)
            print(f"{PROG}: {left} vendored file(s) left out of {len(paths)}", file=sys.stderr)
    except (ScopeError, config.ConfigError) as exc:
        print(f"{PROG}: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
