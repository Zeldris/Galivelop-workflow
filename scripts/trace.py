#!/usr/bin/env python3
# galivelop-workflow v0.7.1
"""Everything about one task id, gathered on the spot from the repo (D14); nothing is stored, so there is no index
to keep in step.

  python3 trace.py ID [--json] [--limit N] [--root PATH]

Sources, in this order (a section with nothing is left out of the text output):
  roadmap   the table rows whose first cell is ID, in each file of `roadmapFiles`, with their `## ` section
  log       the lines of the log (`log`) that name ID
  pending   the lines of the pending file (`pendingFile`) that name ID
  commits   declared: the commits (all local branches and remote-tracking refs) whose `Refs:` trailer lists ID or
            whose subject scope names it (`feat(D14): ...`, `feat(D1, D14): ...`); and the merge commits whose
            message names it (the branch that was merged: the offline stand-in for a PR; nothing is fetched)
  docs      the tracked Markdown files that name ID, other than the roadmap, the log and the pending file (copies
            under `.claude/` are skipped: they are generated)
"Names ID" is a whole-word match: D1 does not match D14 or D1a. --limit N (default 20) caps the entries shown per
source; the text says how many were left out (--json always carries every entry).

ID must match the project's id pattern (config `taskId`, default `[A-Z]{2,5}-\\d+[a-z]?`; the one handoff.py uses).
Exit 0 when something names ID, 1 when ID is well formed but nothing does (the message says where it looked), 2 on a
malformed ID, a bad config or no git repository. --json prints one object: id, found, and a list per source.
Project root: config.find_root (--root PATH, else the script's own repo, never the current directory first).
Python 3.8+ standard library only.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import roadmap  # noqa: E402

SOURCES = ("roadmap", "log", "pending", "commits", "docs")
SNIPPET = 160


class TraceError(Exception):
    pass


def word_re(task):
    """A whole-word match for `task`: not glued to letters, digits, `_` or `-` before, nor to letters, digits or `_` after."""
    return re.compile(r"(?<![\w-])" + re.escape(task) + r"(?!\w)")


def snippet(text):
    text = " ".join(text.split())
    return text if len(text) <= SNIPPET else text[:SNIPPET - 1] + "…"


def read_lines(path):
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None


def roadmap_rows(root, files, task):
    rows, notes = [], []
    for entry in files:
        lines = read_lines(root / entry["path"])
        if lines is None:
            notes.append(f"cannot read {entry['path']}; fix roadmapFiles in .claude/gw.json")
            continue
        heading = ""
        for n, line in enumerate(lines, 1):
            if line.startswith("## "):
                heading = line.strip()
            spans = roadmap.cells(line)
            if spans and line[spans[0][0]:spans[0][1]].strip() == task:
                rows.append({"file": entry["path"], "line": n, "section": heading, "text": snippet(line)})
    return rows, notes


def mentions(root, rel, pattern):
    """([{file, line, text}], note) for the lines of `rel` that match; ([], None) when `rel` is empty."""
    if not rel:
        return [], None
    lines = read_lines(root / rel)
    if lines is None:
        return [], f"cannot read {rel}"
    return [{"file": rel, "line": n, "text": snippet(line)} for n, line in enumerate(lines, 1) if pattern.search(line)], None


def git(root, *args):
    try:
        done = subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
    except OSError as exc:
        raise TraceError(f"cannot run git ({exc.strerror}); install git")
    if done.returncode != 0:
        raise TraceError(f"git {' '.join(args[:2])} failed: {done.stderr.strip() or done.returncode}")
    return done.stdout


def commit_entries(root, task, pattern):
    out = git(root, "log", "--all", "-E", "--grep", re.escape(task), "--format=%x1e%H%x1f%P%x1f%B")
    found = []
    for record in out.split("\x1e"):
        if not record.strip():
            continue
        sha, parents, message = record.split("\x1f", 2)
        lines = message.strip().splitlines()
        subject = lines[0] if lines else ""
        refs = []
        for line in lines[1:]:
            m = re.match(r"Refs:\s*(.*)$", line)
            if m:
                refs += [r.strip() for r in m.group(1).split(",")]
        scope = re.match(r"^(?:WIP:\s*)?[\w-]+\(([^)]*)\)!?:", subject)
        scopes = [s.strip() for s in scope.group(1).split(",")] if scope else []
        if task in refs:
            how = "refs"
        elif task in scopes:
            how = "scope"
        elif len(parents.split()) > 1 and pattern.search(message):
            how = "merge"
        else:
            continue
        found.append({"sha": sha, "short": sha[:7], "how": how, "subject": snippet(subject)})
    return found


def doc_entries(root, task, pattern, skip):
    names = git(root, "ls-files", "-z", "--", "*.md").split("\0")
    found = []
    for rel in sorted(n for n in names if n and n not in skip and not n.startswith(".claude/")):
        lines = read_lines(root / rel)
        for n, line in enumerate(lines or [], 1):
            if pattern.search(line):
                found.append({"file": rel, "line": n, "text": snippet(line)})
    return found


def collect(root, cfg, task):
    pattern = word_re(task)
    notes = []
    rows, more = roadmap_rows(root, config.roadmap_files(cfg), task)
    notes += more
    log_rel = cfg.get("log") or ""
    pend_rel = config.pending_file(cfg)
    log_hits, note = mentions(root, log_rel, pattern)
    notes += [note] if note else []
    pend_hits, note = mentions(root, pend_rel, pattern)
    notes += [note] if note else []
    skip = {e["path"] for e in config.roadmap_files(cfg)} | {log_rel, pend_rel}
    return {"id": task, "roadmap": rows, "log": log_hits, "pending": pend_hits,
            "commits": commit_entries(root, task, pattern), "docs": doc_entries(root, task, pattern, skip),
            "notes": notes}


def render(result, limit):
    lines = [f"trace {result['id']}"]
    for source in SOURCES:
        items = result[source]
        if not items:
            continue
        lines.append(f"\n== {source} ({len(items)})")
        for item in items[:limit]:
            if source == "commits":
                lines.append(f"  {item['short']} [{item['how']}] {item['subject']}")
            elif source == "roadmap":
                lines.append(f"  {item['file']}:{item['line']} {item['section']}\n    {item['text']}")
            else:
                lines.append(f"  {item['file']}:{item['line']}: {item['text']}")
        if len(items) > limit:
            lines.append(f"  … {len(items) - limit} more (--limit N, or --json for all)")
    for note in result["notes"]:
        lines.append(f"\nnote: {note}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Everything about one task id, gathered on the spot.")
    ap.add_argument("id", help="task id, e.g. D14")
    ap.add_argument("--json", action="store_true", help="one JSON object instead of text")
    ap.add_argument("--limit", type=int, default=20, help="entries per source in the text output (default 20)")
    ap.add_argument("--root", help="project root (default: the script's own repo)")
    args = ap.parse_args(argv)
    if args.limit < 1:
        print("trace.py: --limit must be 1 or more; pass e.g. --limit 20", file=sys.stderr)
        return 2
    try:
        root = config.find_root(args.root)
        cfg = config.load(root)
        id_src = cfg.get("taskId") or config.schema_default("taskId")
        try:
            ok = re.fullmatch(id_src, args.id)
        except re.error as exc:
            raise TraceError(f"taskId in .claude/gw.json is not usable ({exc}); fix it: python3 {HERE / 'config.py'} validate")
        if not ok:
            raise TraceError(f"{args.id!r} is not a task id: it must match taskId {id_src!r} (e.g. D14); "
                             "list the ids with: python3 .claude/gw/scripts/roadmap.py list <version>")
        result = collect(root, cfg, args.id)
    except (config.ConfigError, TraceError) as exc:
        print(f"trace.py: {exc}", file=sys.stderr)
        return 2
    result["found"] = any(result[s] for s in SOURCES)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["found"]:
        print(render(result, args.limit))
    else:
        print(f"trace {args.id}: nothing names it (looked in roadmapFiles, the log, pendingFile, the commits' Refs: "
              "and subject scopes, and tracked .md files); check the id, or fetch the branches that carry it: git fetch --all",
              file=sys.stderr)
        for note in result["notes"]:
            print(f"note: {note}", file=sys.stderr)
    return 0 if result["found"] else 1


if __name__ == "__main__":
    sys.exit(main())
