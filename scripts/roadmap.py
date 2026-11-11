#!/usr/bin/env python3
# galivelop-workflow v0.5.1
"""See or mark one task row of the roadmap in every language, without reading the roadmap whole (D55).

  python3 roadmap.py show ID              # the row of ID in each file of `roadmapFiles`, with its `## ` section
  python3 roadmap.py done ID [--date D] [--note TEXT ...] [--force]
                                          # mark it done in all of them: the status cell (the last one) becomes
                                          # `<done> (D)` or `<done> (D; TEXT)`

A task row is a Markdown table line whose first cell is exactly ID. `roadmapFiles` in .claude/gw.json lists the
roadmap in each language, the source first: `{"path", "done", "open"}`. `done` is the word written at the start of
the status cell; `open`, the words an open status starts with. `--note` goes once per file, in the order of
`roadmapFiles` (a note in each language), or not at all; `--date` defaults to today (YYYY-MM-DD).

Fails closed, writing nothing, when: `roadmapFiles` is empty, a file is missing, ID has no row or more than one in a
file, the number of notes does not match, or a status does not start with an `open` word (already done, discarded;
`--force` marks it anyway). Every file is checked before any is written. Exit 0 on success, 1 on any of those (with
the command that fixes it), 2 on a bad config. Project root and config: config.find_root and config.load. Python 3.8+
standard library only.
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, str(HERE))
import config  # noqa: E402


class RoadmapError(Exception):
    pass


def cells(line):
    """The cell boundaries of a table line: [(start, end)] of each cell's text, splitting on `|` outside code spans and
    not escaped (`\\|`). None when the line is not a table row."""
    text = line.rstrip("\n")
    stripped = text.rstrip()
    if not text.lstrip().startswith("|") or not stripped.endswith("|"):
        return None
    pipes, tick, i = [], False, 0
    while i < len(stripped):
        ch = stripped[i]
        if ch == "\\" and not tick:
            i += 2
            continue
        if ch == "`":
            tick = not tick
        elif ch == "|" and not tick:
            pipes.append(i)
        i += 1
    if len(pipes) < 2 or pipes[-1] != len(stripped) - 1:
        return None
    return [(a + 1, b) for a, b in zip(pipes, pipes[1:])]


def find_row(lines, task):
    """(index of the row of `task`, the `## ` heading above it or '') in `lines`; RoadmapError if none or several."""
    found, heading = [], ""
    for n, line in enumerate(lines):
        if line.startswith("## "):
            heading = line.strip()
        spans = cells(line)
        if spans and line[spans[0][0]:spans[0][1]].strip() == task:
            found.append((n, heading))
    if not found:
        raise RoadmapError(f"no row for {task}")
    if len(found) > 1:
        raise RoadmapError(f"{len(found)} rows for {task} (lines {', '.join(str(n + 1) for n, _ in found)}); "
                           "keep one and run again")
    return found[0]


def status_of(line):
    a, b = cells(line)[-1]
    return line[a:b].strip()


def with_status(line, status):
    a, b = cells(line)[-1]
    return f"{line[:a]} {status} {line[b:]}"


def load_files(root, files, task):
    """[(entry, path, lines, row index, heading)] for every roadmap file; RoadmapError naming the file on a problem."""
    out = []
    for entry in files:
        path = root / entry["path"]
        try:
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        except OSError as exc:
            raise RoadmapError(f"cannot read {entry['path']} ({exc.strerror}); fix roadmapFiles in .claude/gw.json")
        try:
            n, heading = find_row(lines, task)
        except RoadmapError as exc:
            raise RoadmapError(f"{entry['path']}: {exc}")
        out.append((entry, path, lines, n, heading))
    return out


def cmd_show(loaded):
    for entry, _path, lines, n, heading in loaded:
        where = f" ({heading[3:]})" if heading else ""
        print(f"{entry['path']}:{n + 1}{where}")
        print(lines[n].rstrip("\n"))


def cmd_done(loaded, task, date, notes, force):
    if notes and len(notes) != len(loaded):
        raise RoadmapError(f"{len(notes)} --note for {len(loaded)} roadmap files; give one per file, in the order of "
                           "roadmapFiles, or none")
    changes = []
    for i, (entry, path, lines, n, _heading) in enumerate(loaded):
        status = status_of(lines[n])
        shown = status.lstrip("*_`").lower()  # `**En curso**` and `Pendiente` are open too
        if not force and not any(shown.startswith(word.lower()) for word in entry["open"]):
            raise RoadmapError(f"{entry['path']}:{n + 1}: {task} is not open (status {status!r}); "
                               f"pass --force to mark it {entry['done']!r} anyway")
        inner = date + (f"; {notes[i].replace('|', chr(92) + '|')}" if notes else "")  # `\|`: cells() skips it
        lines = list(lines)
        lines[n] = with_status(lines[n], f"{entry['done']} ({inner})")
        changes.append((path, lines, entry, n))
    for path, lines, entry, n in changes:
        path.write_text("".join(lines), encoding="utf-8")
        print(f"{entry['path']}:{n + 1}: {status_of(lines[n])}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="See or mark one roadmap row in every language (roadmapFiles).")
    parser.add_argument("command", choices=["show", "done"])
    parser.add_argument("task", help="task id, the first cell of its row (D55)")
    parser.add_argument("--date", help="done: date in the status cell (default: today, YYYY-MM-DD)")
    parser.add_argument("--note", action="append", default=[],
                        help="done: text after the date; once per roadmap file, in the order of roadmapFiles")
    parser.add_argument("--force", action="store_true", help="done: mark it even if its status is not open")
    parser.add_argument("--root", help="project root (default: config.find_root)")
    args = parser.parse_args(argv)
    try:
        root = Path(config.find_root(args.root)).resolve()
        files = config.roadmap_files(config.load(root))
    except config.ConfigError as exc:
        print(f"roadmap: {exc}", file=sys.stderr)
        return 2
    if not files:
        print("roadmap: roadmapFiles is empty in .claude/gw.json; list the roadmap in each language "
              "(see docs/en/config.md)", file=sys.stderr)
        return 1
    if args.date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        print(f"roadmap: --date {args.date!r} is not YYYY-MM-DD; pass e.g. --date 2026-11-11", file=sys.stderr)
        return 1
    try:
        loaded = load_files(root, files, args.task)
        if args.command == "show":
            cmd_show(loaded)
        else:
            cmd_done(loaded, args.task, args.date or datetime.date.today().isoformat(), args.note, args.force)
    except RoadmapError as exc:
        print(f"roadmap: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
