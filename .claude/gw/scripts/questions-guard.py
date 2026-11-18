#!/usr/bin/env python3
# galivelop-workflow v0.7.1
"""PreToolUse hook on Edit, Write, MultiEdit and NotebookEdit (C4, C5, `modes.questions`): editing code while the current
task has open questions in the questions file (questions.py) is blocked (restrictive mode) or warned about (guide mode).

Which project, task and questions (docs/design/I-lifecycle.md, "Tarea en curso del modo restrictivo"):
  - the project is the git worktree that holds the edited file (`tool_input.file_path`, or `notebook_path`), so an
    edit in a subagent's linked worktree reads that worktree's branch, config, questions file and git dir; a file outside
    this script's repository (another repo, the scratchpad) is not the project's code and is allowed;
  - the current task is task.py current_task(): the id of a branch `agent/<id>-...`, else the mark `gw/current-task` in
    that worktree's git dir (`git rev-parse --git-path`: per worktree, never committed; `task.py new|current <id>`
    write it). No current task: allowed, silently (like a question without Refs, which blocks no task);
  - its questions are questions.open_for_task(): the open ones whose Refs name the task exactly. accepted-risk and
    answered questions, and the questions of other tasks, do not count;
  - the file is code when `bash is-code.sh --list` says so (the `content` regexes of .claude/gw.json at HEAD; the
    workflow's own policy files are always code). Documentation and `content` are always allowed: writing the design is
    not implementing it. A file is code also when is-code.sh cannot classify it or the path cannot be placed (a Windows
    drive path on another system): the safe side.

What it does with open questions and a code file:
  - `modes.questions: true` (restrictive, C4): deny (permissionDecision `deny`), naming each open question (id and one
    line) and the two ways on: `questions.py answer "<n>. <answer>"` or `questions.py accept-risk --refs <id>`;
  - `false` (guide, C5, the default): allow, with `additionalContext` recommending to answer them or to accept the risk,
    once per task and set of open questions (the mark `gw/questions-warned` in the git dir; a new question warns again).

A questions file it cannot read or parse: restrictive mode denies with the reason and the fix (fail closed, as
questions.read_entries asks); guide mode adds a one-line warning. A config it cannot read leaves the defaults (guide
mode, docs/questions.md). An event it cannot read is treated like a code file of the hook's own project. Output:
nothing ("no opinion") or one JSON object on stdout, exit 0 (https://code.claude.com/docs/en/hooks.md, PreToolUse).
Python 3.8+ standard library only.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, HERE)
import config  # noqa: E402
import questions  # noqa: E402
import task  # noqa: E402

TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
WARNED = "gw/questions-warned"
DRIVE = re.compile(r"^[A-Za-z]:[\\/]")


def git(where, *argv):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        r = subprocess.run(["git", "-C", str(where), *argv], capture_output=True, text=True, env=env,
                           stdin=subprocess.DEVNULL, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def read_event():
    if sys.stdin is None or sys.stdin.isatty():
        return None
    try:
        data = json.loads(sys.stdin.read())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def emit(spec):
    print(json.dumps({"hookSpecificOutput": dict({"hookEventName": "PreToolUse"}, **spec)}))


def target_path(event):
    """The edited file as an absolute path (str), or None when the event does not name one."""
    tool_input = event.get("tool_input") if isinstance(event, dict) else None
    if not isinstance(tool_input, dict):
        return None
    raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(raw, str) or not raw.strip():
        return None
    if os.name != "nt":
        if DRIVE.match(raw):
            return None  # a Windows drive path cannot be placed here
        raw = raw.replace("\\", "/")
    if not os.path.isabs(raw):
        cwd = event.get("cwd")
        raw = os.path.join(cwd if isinstance(cwd, str) and os.path.isabs(cwd) else os.getcwd(), raw)
    return os.path.normpath(raw)


def existing_dir(path):
    d = os.path.dirname(path)
    while d and not os.path.isdir(d):
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent
    return d or None


def common_dir(where):
    out = git(where, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return os.path.realpath(out) if out else None


def place(path, home):
    """(worktree root, repo-relative path) of `path`; (None, None) when it is outside the hook's repository `home`."""
    folder = existing_dir(path)
    top = git(folder, "rev-parse", "--show-toplevel") if folder else None
    if not top or common_dir(top) != common_dir(home):
        return None, None
    rel = os.path.relpath(os.path.realpath(path), os.path.realpath(top))  # realpath resolves what exists
    if rel == os.pardir or rel.startswith(os.pardir + os.sep):
        return None, None
    return Path(top), rel.replace(os.sep, "/")


def is_code(rel, top):
    """True unless is-code.sh lists `rel` as content; a failure counts as code (the safe side)."""
    try:
        r = subprocess.run(["bash", os.path.join(HERE, "is-code.sh"), "--list", rel], cwd=str(top), capture_output=True,
                           text=True, env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
                           stdin=subprocess.DEVNULL, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return True
    if r.returncode != 0:
        return True
    return rel in r.stdout.splitlines()


def load(top):
    """(config, restrictive): the config at `top` with its defaults; a config it cannot read leaves the defaults."""
    try:
        cfg = config.load(top)
    except Exception:  # noqa: BLE001 (missing or broken config: the defaults, guide mode)
        cfg = {"_root": Path(top)}
    try:
        restrictive = bool(config.modes(cfg)["questions"])
    except Exception:  # noqa: BLE001
        restrictive = False
    return cfg, restrictive


def script(top, name):
    """How a message names one of the workflow's scripts: relative to the project when it lives there."""
    full = os.path.join(HERE, name)
    rel = os.path.relpath(full, str(top))
    return "python3 " + (full if rel.startswith(os.pardir) else rel)


def warned_key(task_id, entries):
    return f"{task_id}: " + ",".join(e.id for e in sorted(entries, key=lambda e: e.number))


def warn_once(top, key):
    """True the first time `key` is seen in this worktree (and records it); True also when the mark cannot be kept."""
    out = git(top, "rev-parse", "--git-path", WARNED)
    if not out:
        return True
    mark = (Path(top) / out).resolve()
    try:
        seen = mark.read_text(encoding="utf-8").splitlines() if mark.exists() else []
    except (OSError, UnicodeDecodeError):
        seen = []
    if key in seen:
        return False
    try:
        mark.parent.mkdir(parents=True, exist_ok=True)
        with open(mark, "a", encoding="utf-8") as f:
            f.write(key + "\n")
    except OSError:
        pass  # the worst case is warning once more
    return True


def main():
    event = read_event()
    if event is not None and event.get("tool_name") not in TOOLS:
        return 0
    home = config.git_toplevel(HERE)
    if home is None:
        return 0  # not installed inside a git repository: there is no task to guard
    path = target_path(event) if event is not None else None
    top, rel = (home, None) if path is None else place(path, home)
    if top is None:
        return 0  # outside the project
    cfg, restrictive = load(top)
    task_id, _ = task.current_task(top, cfg)
    if not task_id:
        return 0
    qfile = Path(top) / config.questions_path(cfg)
    try:
        entries = questions.open_for_task(qfile, task_id)
    except (questions.QuestionsError, OSError, UnicodeDecodeError) as exc:
        where = os.path.relpath(qfile, str(top))
        if restrictive:
            emit({"permissionDecision": "deny",
                  "permissionDecisionReason": f"questions-guard (restrictive mode): the questions file {where} cannot be "
                  f"read ({exc}), so it cannot tell whether task {task_id} has open questions; fix the file, then check "
                  f"it: {script(top, 'questions.py')} list"})
        else:
            emit({"additionalContext": f"questions-guard: {where} cannot be read ({exc}); fix it: "
                                       f"{script(top, 'questions.py')} list"})
        return 0
    if not entries:
        return 0
    if rel is not None and not is_code(rel, top):
        return 0
    q = script(top, "questions.py")
    listed = "\n".join(f"  {e.id}: {questions.one_line(e.get('Question'))[:160]}" for e in entries)
    first = entries[0].number
    target = f"`{rel}`" if rel else "this file (the event named none it could read)"
    if restrictive:
        emit({"permissionDecision": "deny",
              "permissionDecisionReason": f"questions-guard (restrictive mode): task {task_id} has {len(entries)} open "
              f"question(s), so code ({target}) cannot be edited yet:\n{listed}\nAsk the user, then record the answer: "
              f"{q} answer \"{first}. <answer>\"; or, if the user decides to go on without one: {q} accept-risk "
              f"--refs {task_id}. Documentation and `content` files can still be edited."})
        return 0
    if warn_once(top, warned_key(task_id, entries)):
        emit({"additionalContext": f"questions-guard (guide mode): task {task_id} has {len(entries)} open question(s) "
              f"before implementing:\n{listed}\nRecommended: ask the user and record the answer: {q} answer "
              f"\"{first}. <answer>\"; to go on anyway: {q} accept-risk --refs {task_id} (this warning is shown once "
              f"per set of open questions)."})
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 (fail closed in restrictive mode; in guide mode say why)
        why = f"questions-guard.py failed ({type(exc).__name__}: {exc}); check it: python3 {os.path.join(HERE, 'questions-guard.py')}"
        try:
            strict = load(config.git_toplevel(HERE))[1]
        except Exception:  # noqa: BLE001
            strict = False
        emit({"permissionDecision": "deny", "permissionDecisionReason": why} if strict else {"additionalContext": why})
        sys.exit(0)
