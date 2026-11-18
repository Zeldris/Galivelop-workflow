#!/usr/bin/env python3
# galivelop-workflow v0.7.1
"""The task record (C11): the contract of a task (`<taskRecord.path>/<id>.md`) and its decision log, one file per
entry in the folder `<taskRecord.path>/<id>/` that nobody edits afterwards.

  python3 task.py [--root PATH] new <id> [--title TEXT]            create the contract from the template
  python3 task.py [--root PATH] log <id> --agent <skill|session>   create a decision log entry (commit marker pending)
  python3 task.py [--root PATH] resolve <id>                       list the entries with the commit that added each
  python3 task.py [--root PATH] current [<id> | --clear]           the current task: with <id> write the mark, with
                                                                   --clear remove it, alone print the current one

The current task (C4, C5; docs/design/I-lifecycle.md) is the id in a branch named `agent/<id>-...` and, if the branch
names none, the per-clone mark `gw/current-task` in the git dir (`git rev-parse --git-path`, so each linked worktree has
its own and it is never committed), which `new <id>` and `current <id>` write. questions-guard.py reads it with
current_task(); `current` prints that same id (nothing when there is none).

The shape the commit-msg hook (commit-message.py, with `taskRecord.enabled`) asks for lives here too: entry_errors and
contract_errors. The commit of an entry is NOT written into the file (that would dirty the tree after the commit, or
need a second commit): the header keeps `taskRecord.pendingMarker` and `resolve` reads the commit with
`git log --diff-filter=A` on that file, which also survives a rebase or a squash. The templates in
templates/<language>/task.md and task-entry.md are the same text this script writes (a test pins it).
Exit 0 ok, 1 refused (each message ends with the command that fixes it). Python 3.8+, stdlib only.
"""
import argparse
import datetime
import os
import posixpath
import re
import secrets
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config as gwconfig  # noqa: E402

SEP = " · "  # the middle dot the entry header uses
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
SLUG = re.compile(r"[a-z0-9][a-z0-9-]*")
OPEN_QUESTIONS = {"es": "Preguntas abiertas: van a {ref}, no aqu\u00ed.",
                  "en": "Open questions: add them to {ref}, not here."}
QUESTIONS_DEFAULT = "docs/questions.md"  # the `questions.path` key of C1, when that key exists in the config
PLACEHOLDER = re.compile(r"(?:\s|\u2014|-|\*|\[[ xX]\])*")  # a body of only dashes and empty checkboxes says nothing
ACCEPTANCE = "Acceptance"  # the section whose empty body is a checkbox; the config may rename it, the template keeps it


class Refused(Exception):
    pass


def questions_ref(config, root, base):
    """How the contract names the questions file: a relative link when the file exists (md-links.py would flag a link to a
    file that does not), plain code otherwise."""
    given = config.get("questions")
    target = given.get("path") if isinstance(given, dict) and isinstance(given.get("path"), str) else QUESTIONS_DEFAULT
    if root is not None and (Path(root) / target).is_file():
        return f"[{target}]({posixpath.relpath(target, base)})"
    return f"`{target}`"


def contract_text(config, task_id, title=None, root=None):
    tr = gwconfig.task_record(config)
    lang = "es" if config.get("language") == "es" else "en"
    head = f"# {task_id}{SEP}{title or ('<título>' if lang == 'es' else '<title>')}"
    parts = [head]
    for name in tr["sections"]:
        parts.append(f"## {name}\n\n" + ("- [ ] —" if name == ACCEPTANCE else "—"))
    parts.append(OPEN_QUESTIONS[lang].format(ref=questions_ref(config, root, tr["path"])))
    return "\n\n".join(parts) + "\n"


def entry_text(config, task_id, agent, date):
    tr = gwconfig.task_record(config)
    parts = [f"# {date}{SEP}{agent}{SEP}{tr['pendingMarker']}{SEP}{task_id}"]
    parts += [f"## {name}\n\n—" for name in tr["logSections"]]
    return "\n\n".join(parts) + "\n"


def sections_of(text):
    """[(heading, body)] of the `## ` sections of a Markdown text, outside code fences."""
    out, fence = [], False
    for line in text.splitlines():
        if line.startswith("```"):
            fence = not fence
        if not fence and line.startswith("## "):
            out.append([line[3:].strip(), []])
        elif out:
            out[-1][1].append(line)
    return [(h, "\n".join(b).strip()) for h, b in out]


def contract_errors(text, config):
    """Why `text` is not a contract of the task record (the `sections`, each heading once and in order); [] if it is."""
    wanted = gwconfig.task_record(config)["sections"]
    found = [h.lower() for h, _ in sections_of(text)]
    missing = [w for w in wanted if w.lower() not in found]
    if missing:
        return [f"no `## {missing[0]}` section (taskRecord.sections: {', '.join(wanted)})"]
    order = [h for h in found if h in [w.lower() for w in wanted]]
    if order != [w.lower() for w in wanted]:
        return [f"the sections are not in the order {', '.join(wanted)}, or one is repeated"]
    bodies = {h.lower(): body for h, body in sections_of(text)}
    for name in (wanted[0], ACCEPTANCE):  # the goal and the acceptance criteria are the contract: they cannot be the template
        if name in wanted and PLACEHOLDER.fullmatch(bodies.get(name.lower(), "")):
            return [f"the `## {name}` section is empty or still the template; write it (the other sections may stay \u2014)"]
    return []


def entry_errors(text, task_id, config):
    """Why `text` is not a decision log entry for `task_id` (form only); [] if it is."""
    tr = gwconfig.task_record(config)
    first = next((l for l in text.splitlines() if l.strip()), "")
    parts = first[2:].split(SEP) if first.startswith("# ") else []
    if len(parts) != 4 or not DATE.fullmatch(parts[0].strip()) or not parts[1].strip():
        return [f"the first line is not `# <date>{SEP}<skill or session>{SEP}<commit>{SEP}<id>`: {first!r}"]
    commit = parts[2].strip()
    if commit != tr["pendingMarker"] and not re.fullmatch(r"[0-9a-f]{7,64}", commit):
        return [f"the commit field is {commit!r}, not `{tr['pendingMarker']}` or a sha"]
    if parts[3].strip() != task_id:
        return [f"the header names the id {parts[3].strip()!r}, not {task_id!r}"]
    found = {h.lower(): body for h, body in sections_of(text)}
    for name in tr["logSections"]:
        if not found.get(name.lower()):
            return [f"no non-empty `## {name}` section (taskRecord.logSections: {', '.join(tr['logSections'])}; "
                    f"write — when there is nothing to say)"]
    first_name = tr["logSections"][0]
    if PLACEHOLDER.fullmatch(found[first_name.lower()]):
        return [f"the `## {first_name}` section is only \u2014 or still the template; say why (the others may stay \u2014)"]
    return []


def _config(root):
    try:
        config = gwconfig.load(root)
    except gwconfig.ConfigError as exc:
        raise Refused(f"cannot read .claude/gw.json ({exc}); fix it: python3 {HERE / 'config.py'} validate")
    return config, Path(config["_root"]), gwconfig.task_record(config)


def check_id(config, task_id):
    import handoff
    pattern = handoff.task_id_pattern(config)
    if not re.fullmatch(pattern, task_id or ""):
        raise Refused(f"{task_id!r} does not have the shape of taskId ({pattern}); use the id of a roadmap row, e.g. C11")


def write_new(root, rel, text):
    path = root / rel
    if path.exists():
        raise Refused(f"{rel} exists already; edit it, or for a new decision log entry: python3 {HERE / 'task.py'} log <id> --agent <skill|session>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(rel)


BRANCH_PREFIX = "agent/"
MARK = "gw/current-task"


def _git(root, *argv):
    """stdout of `git -C root ...` without the GIT_* variables a git hook exports, or None when it fails."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        r = subprocess.run(["git", "-C", str(root), *argv], capture_output=True, text=True, env=env,
                           stdin=subprocess.DEVNULL)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def current_mark(root):
    """The file of the current-task mark in the git dir of the worktree at `root`, or None outside git."""
    out = _git(root, "rev-parse", "--git-path", MARK)
    return (Path(root) / out).resolve() if out else None


def branch_task(root, config):
    """The id in a branch named `agent/<id>-<topic>` (or `agent/<id>`), checked against taskId; else None."""
    import handoff
    branch = _git(root, "symbolic-ref", "--short", "-q", "HEAD") or ""
    m = re.match(rf"{re.escape(BRANCH_PREFIX)}({handoff.task_id_pattern(config)})(?=-|$)", branch)
    return m.group(1) if m else None


def mark_task(root, config):
    """The id in the mark, or None when there is no mark or it does not hold a valid id."""
    import handoff
    mark = current_mark(root)
    try:
        text = mark.read_text(encoding="utf-8").strip() if mark else ""
    except (OSError, UnicodeDecodeError):
        return None
    return text if text and re.fullmatch(handoff.task_id_pattern(config), text) else None


def current_task(root, config):
    """(id, source): the current task and where it came from ("branch" or "mark"); (None, None) when there is none.
    The branch beats the mark."""
    found = branch_task(root, config)
    if found:
        return found, "branch"
    found = mark_task(root, config)
    return (found, "mark") if found else (None, None)


def write_mark(root, task_id):
    mark = current_mark(root)
    if mark is None:
        raise Refused(f"{root} is not a git repository, so there is no git dir for the current-task mark; run it inside the "
                      f"project: python3 {HERE / 'task.py'} current {task_id}")
    mark.parent.mkdir(parents=True, exist_ok=True)
    mark.write_text(task_id + "\n", encoding="utf-8")


def resolve(root, rel):
    r = subprocess.run(["git", "-C", str(root), "log", "--diff-filter=A", "--format=%h", "-1", "--", rel],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip() if r.returncode == 0 else ""


def run(args):
    config, root, tr = _config(args.root)
    if args.command == "current":
        return run_current(args, config, root)
    check_id(config, args.id)
    base = tr["path"].strip("/")
    if args.command == "new":
        write_new(root, f"{base}/{args.id}.md", contract_text(config, args.id, args.title, root))
        write_mark(root, args.id)
    elif args.command == "log":
        agent = args.agent.strip().lower()
        if not SLUG.fullmatch(agent) or names_a_model(agent, config):
            raise Refused(f"--agent {args.agent!r} must be a skill name or `session` (letters, digits, hyphens), never a model; "
                          f"e.g.: python3 {HERE / 'task.py'} log {args.id} --agent session")
        date = args.date or datetime.date.today().isoformat()
        if not DATE.fullmatch(date):
            raise Refused(f"--date {date!r} is not YYYY-MM-DD; fix it: python3 {HERE / 'task.py'} log {args.id} --agent {agent}")
        token = secrets.token_hex(4)[:7]
        write_new(root, f"{base}/{args.id}/{date}-{agent}-{token}.md", entry_text(config, args.id, agent, date))
    else:
        folder = root / base / args.id
        for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
            rel = path.relative_to(root).as_posix()
            print(f"{resolve(root, rel) or tr['pendingMarker']}  {rel}")


def run_current(args, config, root):
    if args.clear and args.id:
        raise Refused(f"give an id or --clear, not both: python3 {HERE / 'task.py'} current --clear")
    if args.clear:
        mark = current_mark(root)
        if mark is not None and mark.exists():
            mark.unlink()
        return
    if args.id:
        check_id(config, args.id)
        write_mark(root, args.id)
        branch = branch_task(root, config)
        if branch and branch != args.id:
            print(f"task: the branch names {branch}, which beats the mark; the current task stays {branch}",
                  file=sys.stderr)
        return
    found = current_task(root, config)[0]
    if found:
        print(found)


def names_a_model(agent, config):
    """Whether `agent` names a model or provider, by the rule of the Agent trailer (commit-message.py, with the
    project's agentModelNames and agentModelShapes)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("commit_message", HERE / "commit-message.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.names_a_model(agent, module.model_rules(config))
    except module.Reject as exc:
        raise Refused(str(exc))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", help="project path (default: see config.py)")
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="create the contract <path>/<id>.md")
    new.add_argument("id")
    new.add_argument("--title")
    log = sub.add_parser("log", help="create a decision log entry in <path>/<id>/")
    log.add_argument("id")
    log.add_argument("--agent", required=True, help="the skill that works the task, or `session`")
    log.add_argument("--date", help="YYYY-MM-DD (default: today)")
    res = sub.add_parser("resolve", help="list the entries of <id> with the commit that added each")
    res.add_argument("id")
    cur = sub.add_parser("current", help="print the current task, or set (<id>) or remove (--clear) the mark")
    cur.add_argument("id", nargs="?")
    cur.add_argument("--clear", action="store_true")
    args = parser.parse_args(argv)
    try:
        run(args)
    except Refused as exc:
        print(f"task: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
