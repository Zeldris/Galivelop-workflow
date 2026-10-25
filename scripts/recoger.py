#!/usr/bin/env python3
# galivelop-workflow v0.4.0
"""Deterministic part of the gw-harvest skill: what changed in projects that use the workflow.

For each project repository it reports, without judging anything:
  * workflow skills whose copy in the project differs from this repo's version (body diff stats), apart from those
    whose body equals an earlier commit's here (an older copy, listed on its own: not the project's edits);
  * skills born in the project (in .claude/skills/ and not part of the workflow);
  * workflow scripts copied into the project that differ (same file name as in scripts/), older copies apart;
  * retro files, and "For Galivelop-workflow" sections in any tracked .md changed since the last harvest, plus the
    lines there that start with "Propuesta para el flujo" / "Proposal for the workflow" (with their indented
    continuation lines), the way projects note requests in their hand-off log; after an earlier harvest, only the
    ones with a line added or changed since it (never a proposal line twice: inside a section it is part of it);
  * commits since the last harvested commit;
  * a warning when the clone is behind its upstream branch (as of its last fetch: fetch first), or has no upstream
    (then nobody can tell whether it is up to date).

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
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "scripts"))
from aplicar import skill_version_span  # noqa: E402  (the one parser of skill versions)
STATE = ROOT / "docs" / "propuestas" / "estado.json"
IDEAS_HEADING = re.compile(r"^#{2,4}\s*(?:For|Para)\s+Galivelop-workflow\b.*$", re.I | re.M)
IDEAS_LINE = re.compile(r"^([ \t]*)(?:[-*+]\s+|\d+\.\s+)?[*_]{0,2}(?:Propuestas?\s+para\s+el\s+flujo|Proposals?\s+for\s+the\s+workflow)\b",
                        re.I | re.M)
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


def meta_version(text):
    span = skill_version_span(text)
    return text[span[0]:span[1]] or None if span else None


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


def earlier_match(rel, text, body_only=False):
    """The short sha of the latest commit of this repo whose rel (followed through renames) has the same text (only the
    body for a SKILL.md), or None: the project then holds an older copy of the workflow, not edits of its own."""
    log = git(ROOT, "log", "--follow", "--format=%H", "--name-only", "--", rel) or ""
    def comparable(t):
        return (split_frontmatter(t)[1] if body_only else t).strip()
    want, sha = comparable(text), None
    for line in log.splitlines():
        if re.fullmatch(r"[0-9a-f]{40}", line):
            sha = line
        elif line.strip() and sha:
            old = git(ROOT, "show", f"{sha}:{line.strip()}")
            if old is not None and comparable(old + "\n") == want:
                return sha[:7]
    return None


def skill_files(base):
    return {p.parent.name: p for p in sorted(Path(base).glob("*/SKILL.md"))}


def description(text):
    match = re.search(r"^description:\s*(.+)$", split_frontmatter(text)[0], re.M)
    return match.group(1).strip().strip('"')[:200] if match else ""


def added_lines(repo, base, rel):
    """Numbers (1-based) of the lines of rel's working-tree text that were added or changed since commit `base`, or
    None when everything counts: no base (first harvest), the file is new since it, or git could not say."""
    if base is None or git(repo, "cat-file", "-e", f"{base}:{rel}") is None:
        return None
    diff = git(repo, "diff", "-U0", "--no-renames", base, "--", rel)
    if diff is None:
        return None
    lines = set()
    for m in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", diff, re.M):
        start, count = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
        lines.update(range(start, start + count))
    return lines


def ideas_in(text, rel, added):
    """The ideas for this workflow in one Markdown text: "For/Para Galivelop-workflow" sections and "Propuesta para
    el flujo" lines (with their indented continuation lines). With `added` (line numbers changed since the last
    harvest) only the ones that have a line there; a proposal line inside a reported section is not reported twice."""
    lines = text.split("\n")
    def touched(first, last):
        return added is None or any(n in added for n in range(first, last + 1))
    ideas, sections = [], []
    for match in IDEAS_HEADING.finditer(text):
        nxt = re.search(r"^#{1,4}\s", text[match.end():], re.M)
        end = match.end() + nxt.start() if nxt else len(text)
        first = text.count("\n", 0, match.start()) + 1
        last = text.count("\n", 0, end) + (1 if end == len(text) else 0)  # up to the line before the next heading
        sections.append((first, last))
        if touched(first, last):
            ideas.append({"path": rel, "text": text[match.end():end].strip()[:2000]})
    for match in IDEAS_LINE.finditer(text):
        first = text.count("\n", 0, match.start()) + 1
        if any(a <= first <= b for a, b in sections):
            continue  # inside a section: reported with it, or unchanged with it
        indent, kept = len(match.group(1).expandtabs()), [lines[first - 1]]
        for line in lines[first:]:
            if not line.strip() or len(line[:len(line) - len(line.lstrip())].expandtabs()) <= indent:
                break
            kept.append(line)
        if touched(first, first + len(kept) - 1):
            ideas.append({"path": rel, "text": "\n".join(kept).strip()[:2000]})
    return ideas


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
              "skills_missing": [], "skills_older": [], "scripts_changed": [], "scripts_older": [], "retros": [], "ideas": [], "behind": None,
              "upstream": None}

    # A stale clone harvests old work and reports "nothing new": compare HEAD with its own upstream as last fetched
    # (never a guess such as origin/HEAD: that may be another branch). Behind counts even when diverged.
    upstream = git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    report["upstream"] = upstream
    if upstream:
        behind = int(git(repo, "rev-list", "--count", "HEAD..@{upstream}") or 0)
        ahead = int(git(repo, "rev-list", "--count", "@{upstream}..HEAD") or 0)
        if behind:
            report["behind"] = {"ref": upstream, "commits": behind, "diverged": ahead > 0}

    changed_files, base = None, None
    if last and last != head:
        if git(repo, "cat-file", "-e", f"{last}^{{commit}}") is None:
            report["history"] = (f"commit {last[:12]} not in this clone; run "
                                 f"`git -C {repo} fetch --depth=500 origin` and harvest again (full scan done)")
        else:
            log = git(repo, "log", "--format=%h %s", f"{last}..{head}") or ""
            report["commits"] = log.splitlines()
            names = git(repo, "diff", "--name-only", last, head) or ""
            changed_files = set(names.splitlines())
            base = last
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
                older = earlier_match(f"skills/{name}/SKILL.md", text, body_only=True)
                item = {"skill": name, "path": rel, "added": added, "removed": removed,
                        "their_version": meta_version(text)}
                if older:
                    report["skills_older"].append(dict(item, matches=older))
                else:
                    report["skills_changed"].append(item)
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
                older = earlier_match(f"scripts/{name}", theirs_text)
                if older:
                    report["scripts_older"].append({"script": name, "path": rel, "matches": older})
                else:
                    report["scripts_changed"].append({"script": name, "path": rel})
        if rel.endswith(".md") and (changed_files is None or rel in changed_files):
            if RETRO_NAME.search(rel):
                report["retros"].append(rel)
            if not (repo / rel).is_file():
                continue
            text = (repo / rel).read_text(encoding="utf-8", errors="replace")
            report["ideas"] += ideas_in(text, rel, added_lines(repo, base, rel))
    return report


def markdown(report):
    out = [f"## {report['repo']}", "",
           f"- Path: `{report['path']}` · HEAD `{report['head'][:12]}` · last harvest "
           f"`{(report['last'] or 'never')[:12]}` · `.claude/gw.json`: {'yes' if report['uses_gw_json'] else 'no'}",
           f"- History: {report['history']}"]
    fix = (f"update this read-only clone (`git -C {report['path']} fetch && git -C {report['path']} merge --ff-only "
           f"@{{upstream}}`, only if it has no local work) or harvest a fresh clone")
    if report["upstream"] is None:
        out.append(f"- **WARNING:** no upstream: cannot tell whether the clone is up to date; {fix}")
    elif report["behind"]:
        b = report["behind"]
        state = "diverged from" if b["diverged"] else "behind"
        out.append(f"- **WARNING:** the clone has {state} `{b['ref']}`: {b['commits']} commit(s) behind it, which "
                   f"this harvest misses; {fix}, then harvest again")
    if report["commits"]:
        out.append(f"- Commits since last harvest: {len(report['commits'])}")
        out += [f"  - {c}" for c in report["commits"][:30]]
    sections = [
        ("Workflow skills changed in the project", "skills_changed",
         lambda s: f"`{s['skill']}` (`{s['path']}`): +{s['added']} −{s['removed']} lines in the body; "
                   f"their version {s['their_version'] or 'none'}; it matches no earlier workflow copy, so local edits "
                   f"(see them: `python3 scripts/recoger.py --diff {s['skill']} {report['path']}`)"),
        ("Older workflow copies (not project changes)", "skills_older",
         lambda s: f"`{s['skill']}` (`{s['path']}`): body equal to the workflow's at `{s['matches']}`; "
                   f"their version {s['their_version'] or 'none'}"),
        ("Skills born in the project", "skills_new", lambda s: f"`{s['skill']}` (`{s['path']}`): {s['description']}"),
        ("Workflow scripts changed in the project", "scripts_changed", lambda s: f"`{s['script']}` (`{s['path']}`)"),
        ("Older workflow scripts (not project changes)", "scripts_older",
         lambda s: f"`{s['script']}` (`{s['path']}`): equal to the workflow's at `{s['matches']}`"),
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
