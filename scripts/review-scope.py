#!/usr/bin/env python3
# galivelop-workflow v0.8.0
"""The files the phase 1 `/code-review` reads before the protected branch: the branch's diff without `vendored` files (D82).

  python3 review-scope.py [--base REV] [--workflow DIR] [--all]
  python3 review-scope.py --trivial [--base REV] [--workflow DIR]   # B27: exit 0 if the scoped diff is trivial
                                                                    # (B45: the lines that only change the stamped version
                                                                    # `galivelop-workflow vX.Y.Z`/`version:` are not counted)

Prints, one repo-relative path per line, the files changed between BASE (default `origin/<protectedBranch>`, else the
local protected branch) and HEAD. A file is `vendored` when the project holds it as an unchanged copy of the workflow
(`apply.py --vendored`: `.claude/gw/`, `.claude/skills/gw-*`, `.githooks/`, `.claude/agents/`, the CI file): the workflow
repo reviewed it already, so it stays out. A vendored file the project edited no longer matches the workflow's copy and
stays in; so do the files of `ownedFiles` and anything not copied from the workflow. A renamed
file is listed by its new path (a rename is read as the old path deleted and the new one added). Content is compared on
the working tree: review a clean checkout of the commit. Known limits: the workflow repo is trusted to be at a published version, and the tree must be clean. Deleted files are listed (there is nothing left to compare).

The workflow copy that says what is vendored is `--workflow DIR`, else the env var GW_WORKFLOW, else this script's own
repo when that is the workflow, else the repo under review when it is the workflow, else (a project) the sibling clone
`../Galivelop-workflow` when it is at the `version` of `.claude/gw.json`. Without one it fails closed (D132) with the
command that clones the tagged version; a project's vendored files would otherwise be handed over as its own code.
`--all` prints the whole diff without asking. Fails closed on what it cannot know: an invalid
config, a git error or a `--base` that is not a commit -> exit 2 with what fixes it. Python 3.8+ standard library only.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import stamp  # noqa: E402

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


REPO_URL = "https://github.com/Zeldris/Galivelop-workflow"
SIBLING = "Galivelop-workflow"


def is_workflow(cand):
    return bool(cand) and (Path(cand) / "scripts" / "apply.py").is_file() and (Path(cand) / "skills").is_dir()


def plugin_version(cand):
    try:
        return json.loads((Path(cand) / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")).get("version")
    except (OSError, ValueError, AttributeError):
        return None


def workflow_dir(arg, root, cfg):
    """D132: --workflow, else $GW_WORKFLOW, else this script's own repo. When that is none (the script is the project's
    vendored copy, so its repo is the project) the workflow repo itself is its own copy (root has the workflow layout);
    a project looks for the sibling clone `../Galivelop-workflow` at the version of its `.claude/gw.json`. None found:
    fail closed with the command that clones the tagged version (a whole diff would hand vendored files over as code)."""
    for cand in (arg, os.environ.get("GW_WORKFLOW"), str(HERE.parent), str(root)):
        if is_workflow(cand):
            return Path(cand)
    version = cfg.get("version")
    sibling = Path(root).resolve().parent / SIBLING
    if is_workflow(sibling) and plugin_version(sibling) == version:
        return sibling
    seen = f"; {sibling} is at v{plugin_version(sibling)}, not v{version}" if is_workflow(sibling) else ""
    raise ScopeError(f"no workflow copy at v{version} to tell what is vendored{seen}; clone the tagged version and "
                     f"rerun with --workflow: git clone --branch v{version} --depth 1 {REPO_URL} <DIR> && "
                     f"python3 {Path(__file__).name} --workflow <DIR> (or --all to list the whole diff)")


def vendored(root, workflow, timeout=None):
    try:
        r = subprocess.run([sys.executable, "-B", str(workflow / "scripts" / "apply.py"), "--vendored", str(root)],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ScopeError(f"apply.py --vendored took more than {timeout}s; run it by hand: "
                         f"python3 {workflow / 'scripts' / 'apply.py'} --vendored {root}")
    if r.returncode != 0:
        raise ScopeError(f"apply.py --vendored failed: {r.stderr.strip() or r.stdout.strip()}; run it by hand: "
                         f"python3 {workflow / 'scripts' / 'apply.py'} --vendored {root}")
    return set(r.stdout.split("\n")) - {""}


def trivial(root, cfg, base, kept):
    """B27: exit 0 with the reason when the scoped diff has no code (is-code.sh) or at most reviewTrivialLines changed
    lines; 1 with the figures otherwise."""
    code = []
    if kept:
        merge_base = git(root, "merge-base", base, "HEAD").strip()
        r = subprocess.run(["bash", str(HERE / "is-code.sh"), merge_base, "HEAD"], cwd=str(root),
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise ScopeError(f"is-code.sh failed: {r.stderr.strip()}; run it by hand: bash {HERE / 'is-code.sh'} "
                             f"{merge_base} HEAD")
        code = [p for p in r.stdout.split("\n") if p in set(kept)]
    if not code:
        print(f"{PROG}: trivial: no code in the review scope ({len(kept)} file(s))")
        return 0
    lines = stamped = 0
    skip_stamps = config.scope_guard(cfg)["skipStamps"]
    # B45: the lines that only change the stamped version (stamp.py) are not counted. One diff for every code file,
    # cut at each `diff --git a/X b/X` (no renames: both sides are the same path), the paths taken literally.
    diff = git(root, "--literal-pathspecs", "diff", "-U0", "--no-renames", f"{base}...HEAD", "--", *code)
    for chunk in re.split(r"(?m)^(?=diff --git )", diff):
        if not chunk:
            continue
        rest = chunk.split("\n", 1)[0][len("diff --git "):]
        half = (len(rest) - 3) // 2
        path = rest[2:2 + half] if rest[:2] == "a/" and rest[half + 3:half + 5] == "b/" else None
        n_stamp, n_other = stamp.stamp_diff(chunk, path)
        if not skip_stamps:  # scopeGuard.skipStamps off: every changed line counts
            n_stamp, n_other = 0, n_stamp + n_other
        stamped += n_stamp
        lines += n_other
    note = f" ({stamped} version-stamp line(s) not counted)" if stamped else ""
    limit = config.review_trivial_lines(cfg)
    if limit and lines <= limit:
        print(f"{PROG}: trivial: {lines} changed code line(s){note}, at most reviewTrivialLines={limit}")
        return 0
    print(f"{PROG}: not trivial: {len(code)} code file(s), {lines} changed line(s){note}, reviewTrivialLines={limit}")
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", help="the diff starts at the merge base with this commit (default origin/<protectedBranch>)")
    ap.add_argument("--workflow", help="the workflow repo whose copies are vendored (default $GW_WORKFLOW, else this repo, else ../Galivelop-workflow at the project's version)")
    ap.add_argument("--trivial", action="store_true",
                    help="exit 0 and say why when the scoped diff is trivial (no code, or reviewTrivialLines changed "
                         "lines or fewer), 1 otherwise; prints no paths")
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
            skip = vendored(root, workflow_dir(args.workflow, root, cfg))
        kept = [p for p in paths if p not in skip]
        if args.trivial:
            return trivial(root, cfg, base, kept)
        for p in kept:
            print(p)
        left = sum(1 for p in paths if p in skip)
        if left:
            print(f"{PROG}: {left} vendored file(s) left out of {len(paths)}", file=sys.stderr)
    except (ScopeError, config.ConfigError) as exc:
        print(f"{PROG}: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
