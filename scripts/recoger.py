#!/usr/bin/env python3
"""Deterministic part of the gw-harvest skill: what changed in projects that use the workflow.

For each project repository it reports, without judging anything:
  * workflow skills whose copy in the project differs from this repo's version (body diff stats);
  * skills born in the project (in .claude/skills/ and not part of the workflow);
  * workflow scripts copied into the project that differ (same file name as in scripts/);
  * retro files and "For Galivelop-workflow" sections added since the last harvest;
  * commits since the last harvested commit;
  * a warning when the clone is behind its remote branch (as of its last fetch: fetch first).

The agent running gw-harvest reads this report, decides what is general and writes the proposals.

Usage:
  python3 scripts/recoger.py PROJECT [PROJECT ...]           # Markdown report
  python3 scripts/recoger.py --json PROJECT ...              # machine-readable
  python3 scripts/recoger.py --diff SKILL PROJECT            # unified diff of one skill
  python3 scripts/recoger.py --update-state PROJECT ...      # record HEAD as harvested
Projects are read-only: this script only runs read-only git commands in them.
"""
import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # this workflow repo
STATE = ROOT / "docs" / "propuestas" / "estado.json"
IDEAS_HEADING = re.compile(r"^#{2,4}\s*(?:For|Para)\s+Galivelop-workflow\b.*$", re.I | re.M)
RETRO_NAME = re.compile(r"(^|/)retro-[^/]*\.md$")


def git(repo, *args):
    """Run a read-only git command; return stdout or None on failure."""
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


def repo_id(repo):
    """Stable key for a project: owner/name from origin, else the folder name."""
    url = git(repo, "remote", "get-url", "origin") or ""
    match = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", url)
    return f"{match.group(1)}/{match.group(2)}".lower() if match else Path(repo).name.lower()


def split_frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (match.group(1), text[match.end():]) if match else ("", text)


def meta_version(frontmatter):
    match = re.search(r'^\s+version:\s*"?([^"\n]+)"?\s*$', frontmatter, re.M)
    return match.group(1).strip() if match else None


def body_diff(ours, theirs):
    """Lines added/removed in the project's copy, comparing bodies only (frontmatter differs by design)."""
    a = split_frontmatter(ours)[1].splitlines()
    b = split_frontmatter(theirs)[1].splitlines()
    added = removed = 0
    for line in difflib.unified_diff(a, b, lineterm="", n=0):
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return added, removed


def skill_files(base):
    return {p.parent.name: p for p in sorted(Path(base).glob("*/SKILL.md"))}


def description(text):
    match = re.search(r"^description:\s*(.+)$", split_frontmatter(text)[0], re.M)
    return match.group(1).strip().strip('"')[:200] if match else ""


def harvest(repo, state):
    repo = Path(repo).resolve()
    head = git(repo, "rev-parse", "HEAD")
    if head is None:
        raise SystemExit(f"{repo}: not a git repository (clone it first)")
    rid = repo_id(repo)
    last = state.get(rid)
    report = {"repo": rid, "path": str(repo), "head": head, "last": last,
              "uses_gw_json": (repo / ".claude" / "gw.json").is_file(),
              "commits": [], "history": "full", "skills_changed": [], "skills_new": [],
              "skills_missing": [], "scripts_changed": [], "retros": [], "ideas": [], "behind": None}

    # A stale clone harvests old work and reports "nothing new": compare HEAD with its remote branch as last fetched.
    upstream = git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}") \
        or git(repo, "rev-parse", "--abbrev-ref", "origin/HEAD")
    if upstream and git(repo, "merge-base", "--is-ancestor", "HEAD", upstream) is not None:
        count = int(git(repo, "rev-list", "--count", f"HEAD..{upstream}") or 0)
        if count:
            report["behind"] = {"ref": upstream, "commits": count}

    changed_files = None
    if last and last != head:
        if git(repo, "cat-file", "-e", f"{last}^{{commit}}") is None:
            report["history"] = (f"commit {last[:12]} not in this clone; run "
                                 f"`git -C {repo} fetch --depth=500 origin` and harvest again (full scan done)")
        else:
            log = git(repo, "log", "--format=%h %s", f"{last}..{head}") or ""
            report["commits"] = log.splitlines()
            names = git(repo, "diff", "--name-only", last, head) or ""
            changed_files = set(names.splitlines())
    elif last == head:
        report["history"] = "nothing new since the last harvest"
        changed_files = set()

    ours, theirs = skill_files(ROOT / "skills"), skill_files(repo / ".claude" / "skills")
    for name, path in theirs.items():
        rel = str(path.relative_to(repo))
        if changed_files is not None and rel not in changed_files:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if name in ours:
            mine = ours[name].read_text(encoding="utf-8")
            added, removed = body_diff(mine, text)
            if added or removed:
                report["skills_changed"].append({"skill": name, "path": rel, "added": added, "removed": removed,
                                                 "their_version": meta_version(split_frontmatter(text)[0])})
        else:
            report["skills_new"].append({"skill": name, "path": rel, "description": description(text)})
    report["skills_missing"] = sorted(set(ours) - set(theirs))

    our_scripts = {p.name: p for p in (ROOT / "scripts").glob("*") if p.is_file()}
    tracked = (git(repo, "ls-files") or "").splitlines()
    for rel in tracked:
        name = Path(rel).name
        if name in our_scripts and name != "recoger.py":
            if changed_files is not None and rel not in changed_files:
                continue
            theirs_text = (repo / rel).read_text(encoding="utf-8", errors="replace")
            if theirs_text != our_scripts[name].read_text(encoding="utf-8"):
                report["scripts_changed"].append({"script": name, "path": rel})
        if RETRO_NAME.search(rel) and (changed_files is None or rel in changed_files):
            report["retros"].append(rel)
            text = (repo / rel).read_text(encoding="utf-8", errors="replace")
            for match in IDEAS_HEADING.finditer(text):
                nxt = re.search(r"^#{1,4}\s", text[match.end():], re.M)
                section = text[match.end(): match.end() + nxt.start()] if nxt else text[match.end():]
                report["ideas"].append({"path": rel, "text": section.strip()[:2000]})
    return report


def markdown(report):
    out = [f"## {report['repo']}", "",
           f"- Path: `{report['path']}` · HEAD `{report['head'][:12]}` · last harvest "
           f"`{(report['last'] or 'never')[:12]}` · `.claude/gw.json`: {'yes' if report['uses_gw_json'] else 'no'}",
           f"- History: {report['history']}"]
    if report["behind"]:
        b = report["behind"]
        out.append(f"- **WARNING:** the clone is {b['commits']} commit(s) behind `{b['ref']}`; this harvest misses them. "
                   f"Update it and harvest again: `git -C {report['path']} merge --ff-only {b['ref']}`")
    if report["commits"]:
        out.append(f"- Commits since last harvest: {len(report['commits'])}")
        out += [f"  - {c}" for c in report["commits"][:30]]
    sections = [
        ("Workflow skills changed in the project", "skills_changed",
         lambda s: f"`{s['skill']}` (`{s['path']}`): +{s['added']} −{s['removed']} lines in the body; "
                   f"their version {s['their_version'] or 'none'}"),
        ("Skills born in the project", "skills_new", lambda s: f"`{s['skill']}` (`{s['path']}`): {s['description']}"),
        ("Workflow scripts changed in the project", "scripts_changed", lambda s: f"`{s['script']}` (`{s['path']}`)"),
        ("Retro files", "retros", lambda r: f"`{r}`"),
        ("Ideas for Galivelop-workflow", "ideas", lambda i: f"`{i['path']}`:\n\n{i['text']}\n"),
    ]
    for title, key, fmt in sections:
        out += ["", f"### {title}", ""]
        out += [f"- {fmt(item)}" for item in report[key]] or ["- none"]
    if report["skills_missing"]:
        out += ["", f"Workflow skills not present in the project: {', '.join(report['skills_missing'])}"]
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("projects", nargs="+", help="paths to project clones")
    parser.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    parser.add_argument("--diff", metavar="SKILL", help="print the unified diff of one skill (ours → theirs)")
    parser.add_argument("--update-state", action="store_true",
                        help=f"record each project's HEAD as harvested in {STATE.relative_to(ROOT)}")
    parser.add_argument("--state", type=Path, default=STATE, help=argparse.SUPPRESS)
    args = parser.parse_args()

    state = json.loads(args.state.read_text(encoding="utf-8")) if args.state.is_file() else {}

    if args.diff:
        mine = ROOT / "skills" / args.diff / "SKILL.md"
        for project in args.projects:
            theirs = Path(project) / ".claude" / "skills" / args.diff / "SKILL.md"
            if not mine.is_file() or not theirs.is_file():
                print(f"{args.diff}: missing in {'this repo' if not mine.is_file() else project}", file=sys.stderr)
                return 1
            sys.stdout.writelines(difflib.unified_diff(
                mine.read_text(encoding="utf-8").splitlines(True), theirs.read_text(encoding="utf-8").splitlines(True),
                fromfile=f"galivelop-workflow/skills/{args.diff}/SKILL.md", tofile=str(theirs)))
        return 0

    reports = [harvest(p, state) for p in args.projects]
    if args.update_state:
        for r in reports:
            state[r["repo"]] = r["head"]
        args.state.parent.mkdir(parents=True, exist_ok=True)
        args.state.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"State updated: {args.state.relative_to(ROOT) if args.state.is_relative_to(ROOT) else args.state}")
        return 0
    if args.json:
        print(json.dumps(reports, indent=2, ensure_ascii=False))
    else:
        sys.stdout.write("\n".join(markdown(r) for r in reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
