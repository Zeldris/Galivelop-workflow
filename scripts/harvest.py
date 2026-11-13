#!/usr/bin/env python3
# galivelop-workflow v0.5.2
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
  python3 scripts/harvest.py PROJECT [PROJECT ...]           # Markdown report
  python3 scripts/harvest.py --json PROJECT ...              # machine-readable
  python3 scripts/harvest.py --diff SKILL PROJECT            # unified diff of one skill
  python3 scripts/harvest.py --update-state PROJECT ...      # record HEAD as harvested
Projects are read-only: this script only runs read-only git commands in them.

Private projects (E3): with `anonymize` in this repo's .claude/gw.local.json ({"<name>": "private-project-N"}),
everything printed, and the project id recorded in the state file, carries the alias instead of the name (any case,
`-`, `_` and space alike: the matching of private-check.py). A name of privateNames still in a project's report (no
alias for it) -> that project is not printed and the exit code is 1, saying to add the alias. The state is looked up
under the alias and, during 0.x, under the old real id, which --update-state replaces with the alias.
"""
import argparse
import difflib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # this workflow repo
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402  (the only reader of .claude/gw.json)
from apply import OLD_SCRIPTS, OLD_SKILLS, skill_version_span  # noqa: E402  (the one parser of skill versions, and the A8 old names)
IDEAS_HEADING = re.compile(r"^#{2,4}\s*(?:For|Para)\s+Galivelop-workflow\b.*$", re.I | re.M)
IDEAS_LINE = re.compile(r"^([ \t]*)(?:[-*+]\s+|\d+\.\s+)?[*_]{0,2}(?:Propuestas?\s+para\s+el\s+flujo|Proposals?\s+for\s+the\s+workflow)\b",
                        re.I | re.M)


def retro_name(repo):
    """The regex that names a retro file in the harvested project: its `retro.filePattern` (A13), else the default (a
    project with no key, no config or an unreadable one has the built-in pattern)."""
    try:
        pattern = config.retro(config.load(repo))["filePattern"]
        return re.compile(pattern)
    except (config.ConfigError, re.error, OSError):
        return re.compile(config.retro({})["filePattern"])


def load_private_check():
    """scripts/private-check.py as a module (its file name has a dash): its name_regex is the one name matcher."""
    spec = importlib.util.spec_from_file_location("private_check", str(Path(__file__).resolve().parent /
                                                                       "private-check.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Anonymizer:
    """The aliases of the local file: anonymize(obj) puts them in place of the names in every string of obj, and
    leaks(obj) lists the private names still there (they have no alias). Without a local file it changes nothing."""

    def __init__(self, local):
        local = local or {"privateNames": [], "anonymize": {}}
        name_regex = load_private_check().name_regex if local["privateNames"] else None
        # Longest name first: "secret app" is replaced before a shorter "secret".
        self.rules = [(name_regex([name]), alias) for name, alias in
                      sorted(local["anonymize"].items(), key=lambda item: len(item[0]), reverse=True)]
        self.private = name_regex(local["privateNames"]) if name_regex else None

    def __call__(self, obj):
        if isinstance(obj, str):
            for regex, alias in self.rules:
                obj = regex.sub(alias, obj)
            return obj
        if isinstance(obj, list):
            return [self(item) for item in obj]
        if isinstance(obj, dict):
            return {self(k): self(v) for k, v in obj.items()}
        return obj

    def leaks(self, obj):
        if self.private is None:
            return []
        found, todo = set(), [obj]
        while todo:
            item = todo.pop()
            if isinstance(item, str):
                found.update(m.group(0) for m in self.private.finditer(item))
            elif isinstance(item, dict):
                todo += list(item) + list(item.values())
            elif isinstance(item, list):
                todo += item
        return sorted(found)


def refuse(what, leaks):
    """The message for output that still names a private name with no alias (to stderr: it is local)."""
    names = ", ".join(leaks)
    example = json.dumps({"anonymize": {leaks[0]: "private-project-N"}})
    return (f"harvest: {what} mentions private names with no alias ({names}), so it is not printed; add each to "
            f"anonymize in {config.LOCAL_REL.as_posix()} (e.g. {example}) and run it again")


def default_state():
    """<proposalsDir>/state.json of this workflow repo (the config's `proposalsDir`; fails closed without a config)."""
    return ROOT / config.load(ROOT)["proposalsDir"] / "state.json"


def old_state(path):
    """The file the state had before A8 (estado.json next to `path`) when only that one exists, else None."""
    old = path.with_name("estado.json")
    return old if not path.is_file() and old.is_file() else None


def move_old_state(old, new):
    """Rename estado.json to state.json (git mv when tracked) before the new state is written over it."""
    def run(*args):
        return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True).returncode == 0
    if run("ls-files", "--error-unmatch", str(old)) and run("mv", str(old), str(new)):
        return
    old.replace(new)


def git(repo, *args):
    """Run a read-only git command; return stdout or None on failure."""
    # errors="replace": diffs carry the projects' text, which may not be UTF-8.
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, encoding="utf-8", errors="replace")
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
    # Published history only (what a project could have installed, plan section 7): HEAD, main, origin/main and the tags,
    # never other branches (an unpublished branch must not hide a project's real edit as an "older copy").
    log = git(ROOT, "log", "--follow", "--full-history", "--branches=main", "--remotes=origin/main", "--tags", "HEAD",
              "--format=%H", "--name-only", "--", rel) or ""
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


TRUNCATED = "\u2026 (truncated)"


def sizes():
    """The `harvest` key (ideaChars, commitsShown) of the workflow's own config; the defaults when it cannot be read."""
    try:
        return config.harvest(config.load(ROOT))
    except (config.ConfigError, OSError):
        return config.harvest({})


def clip(text):
    """An idea's text cut to `harvest.ideaChars` characters; a cut one ends in TRUNCATED so nobody takes it for the whole."""
    text = text.strip()
    cap = sizes()["ideaChars"]
    return text if len(text) <= cap else text[:cap - len(TRUNCATED) - 1].rstrip() + " " + TRUNCATED


def changed_since(repo, last, head):
    """(new paths changed between two commits, {new path: old path} for the files git sees as renamed with -M)."""
    out = git(repo, "diff", "-M", "--name-status", "-z", last, head) or ""
    parts, files, renames, i = out.split("\0"), set(), {}, 0
    while i < len(parts) and parts[i]:
        if parts[i][0] in "RC":
            files.add(parts[i + 2])
            if parts[i][0] == "R":
                renames[parts[i + 2]] = parts[i + 1]
            i += 3
        else:
            files.add(parts[i + 1])
            i += 2
    return files, renames


def added_lines(repo, base, rel, old=None):
    """Numbers (1-based) of the lines of rel's working-tree text that were added or changed since commit `base`, or
    None when everything counts: no base (first harvest), the file is new since it, or git could not say. `old` is
    the path the file had at `base` when it was moved since: only what changed besides the move counts."""
    if base is None or git(repo, "cat-file", "-e", f"{base}:{old or rel}") is None:
        return None
    if old and old != rel:
        diff = git(repo, "diff", "-U0", "-M", "--no-color", "--no-ext-diff", "--no-textconv", base, "--", old, rel)
        if diff is None or f"rename to {rel}" not in diff.replace('"', ""):
            return None  # git does not see it as a move: count it all
        return {n for m in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", diff, re.M)
                for n in range(int(m.group(1)), int(m.group(1)) + int(m.group(2) if m.group(2) is not None else 1))}
    # Plain diff whatever the person's git config says (color.diff=always, diff.external, textconv).
    diff = git(repo, "diff", "-U0", "--no-renames", "--no-color", "--no-ext-diff", "--no-textconv", base, "--", rel)
    if diff is None or (diff and "\n@@ " not in "\n" + diff):  # e.g. "Binary files differ": count it all
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
            ideas.append({"path": rel, "text": clip(text[match.end():end])})
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
            ideas.append({"path": rel, "text": clip("\n".join(kept))})
    return ideas


def state_key(state, rid, anonymize):
    """The key of this project in the state: its public id (the alias in it), or during 0.x the old real id when only
    that one was recorded."""
    public = anonymize(rid)
    return rid if public not in state and rid in state else public


def harvest(repo, state, anonymize=lambda text: text):
    """The report of one project, with its real names: the caller anonymizes it."""
    repo = Path(repo).resolve()
    head = git(repo, "rev-parse", "HEAD")
    if head is None:
        raise SystemExit(f"{repo}: not a git repository (clone it first)")
    rid = repo_id(repo)
    last = state.get(state_key(state, rid, anonymize))
    renames = {}
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
            changed_files, renames = changed_since(repo, last, head)
            base = last
    elif last == head:
        report["history"] = "nothing new since the last harvest"
        changed_files = set()

    retro_re = retro_name(repo)
    ours, theirs = skill_files(ROOT / "skills"), skill_files(repo / ".claude" / "skills")
    for name, path in theirs.items():
        rel = str(path.relative_to(repo))
        if changed_files is not None and rel not in changed_files:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        # A project installed before A8 holds the skill under its old name: the same skill, not one born there.
        current = OLD_SKILLS[name] if name not in ours and OLD_SKILLS.get(name) in ours else name
        beside = current != name and current in theirs  # apply.py keeps an old folder beside the new one when it has edits
        if current in ours:
            mine = ours[current].read_text(encoding="utf-8")
            added, removed = body_diff(mine, text)
            if added or removed:
                older = (earlier_match(f"skills/{current}/SKILL.md", text, body_only=True) or
                         (earlier_match(f"skills/{name}/SKILL.md", text, body_only=True) if current != name else None))
                item = {"skill": name, "path": rel, "added": added, "removed": removed,
                        "their_version": meta_version(text)}
                if beside:
                    item["note"] = f"old name kept beside `{current}`"
                if older:
                    report["skills_older"].append(dict(item, matches=older))
                else:
                    report["skills_changed"].append(item)
        else:
            report["skills_new"].append({"skill": name, "path": rel, "description": description(text)})
    report["skills_missing"] = sorted(set(ours) - set(theirs) - {OLD_SKILLS[n] for n in theirs if n in OLD_SKILLS})

    our_scripts = {p.name: p for p in (ROOT / "scripts").glob("*") if p.is_file()}
    tracked = (git(repo, "ls-files") or "").splitlines()
    for rel in tracked:
        name = Path(rel).name
        if rel.startswith(".claude/gw/scripts/"):
            name = OLD_SCRIPTS.get(name, name)  # a pre-A8 install has the Spanish file names (only where the flow puts them)
        if name in our_scripts and name != "harvest.py":
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
            if retro_re.search(rel):
                report["retros"].append(rel)
            if not (repo / rel).is_file():
                continue
            text = (repo / rel).read_text(encoding="utf-8", errors="replace")
            report["ideas"] += ideas_in(text, rel, added_lines(repo, base, rel, renames.get(rel)))
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
        out += [f"  - {c}" for c in report["commits"][:sizes()["commitsShown"]]]
    sections = [
        ("Workflow skills changed in the project", "skills_changed",
         lambda s: f"`{s['skill']}` (`{s['path']}`){' (' + s['note'] + ')' if s.get('note') else ''}: +{s['added']} −{s['removed']} lines in the body; "
                   f"their version {s['their_version'] or 'none'}; it matches no earlier workflow copy, so local edits "
                   f"(see them: `python3 scripts/harvest.py --diff {s['skill']} {report['path']}`)"),
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
                        help="record each project's HEAD as harvested in <proposalsDir>/state.json")
    parser.add_argument("--state", type=Path, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args()

    explicit = args.state is not None
    if args.state is None:
        try:
            args.state = default_state()
        except config.ConfigError as exc:
            print(f"harvest: {exc}", file=sys.stderr)
            return 2
    legacy = None if explicit else old_state(args.state)
    if legacy:
        print(f"harvest: warning: {legacy} is the old name of the state file; reading it, and {args.state.name} is "
              "written (renamed) on --update-state", file=sys.stderr)
    source = legacy or args.state
    state = json.loads(source.read_text(encoding="utf-8")) if source.is_file() else {}
    try:
        anonymize = Anonymizer(config.load_local(ROOT))
    except config.ConfigError as exc:
        print(f"harvest: {exc}", file=sys.stderr)
        return 2

    if not args.diff and git(ROOT, "rev-parse", "--is-shallow-repository") == "true":
        print(f"harvest: {ROOT} is a shallow clone, so an older workflow copy in a project would be reported as the "
              f"project's own edit; run: git -C {ROOT} fetch --unshallow origin", file=sys.stderr)
        return 2

    if args.diff:
        mine = ROOT / "skills" / OLD_SKILLS.get(args.diff, args.diff) / "SKILL.md"  # an old name: its current skill
        for n, project in enumerate(args.projects, 1):
            theirs = Path(project) / ".claude" / "skills" / args.diff / "SKILL.md"
            if not mine.is_file() or not theirs.is_file():
                print(f"{args.diff}: missing in {'this repo' if not mine.is_file() else project}", file=sys.stderr)
                return 1
            diff = anonymize("".join(difflib.unified_diff(
                mine.read_text(encoding="utf-8").splitlines(True), theirs.read_text(encoding="utf-8").splitlines(True),
                fromfile=f"galivelop-workflow/{mine.relative_to(ROOT)}", tofile=str(theirs))))
            leaks = anonymize.leaks(diff)
            if leaks:
                print(refuse(f"the diff of project {n} ({project})", leaks), file=sys.stderr)
                return 1
            sys.stdout.write(diff)
        return 0

    reports, refused = [], False
    for n, project in enumerate(args.projects, 1):
        report = harvest(project, state, anonymize)
        public = anonymize(report)
        # --update-state publishes only the project id (in the state file); a report publishes all of it.
        leaks = anonymize.leaks(public["repo"] if args.update_state else public)
        if leaks:
            print(refuse(f"project {n} ({project})", leaks), file=sys.stderr)
            refused = True
            continue
        reports.append((report["repo"], public))
    if args.update_state:
        if refused:
            print("harvest: state not updated", file=sys.stderr)
            return 1
        for rid, r in reports:
            if rid != r["repo"]:
                state.pop(rid, None)  # 0.x: the old real id becomes the alias
            state[r["repo"]] = r["head"]
        args.state.parent.mkdir(parents=True, exist_ok=True)
        if legacy:
            move_old_state(legacy, args.state)
        args.state.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        try:  # not Path.is_relative_to: that is Python 3.9+
            shown = args.state.relative_to(ROOT)
        except ValueError:
            shown = args.state
        print(f"State updated: {shown}")
        return 0
    public = [r for _, r in reports]
    if args.json:
        print(json.dumps(public, indent=2, ensure_ascii=False))
    else:
        sys.stdout.write("\n".join(markdown(r) for r in public))
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
