#!/usr/bin/env python3
# galivelop-workflow v0.7.1
"""Frozen scope (C13, `scopeGuard`): a change of requirements is another task.

  scope-guard.py                     PreToolUse hook on Edit, Write, MultiEdit and NotebookEdit (event JSON on stdin)
  scope-guard.py --staged [--root P] the pre-commit backup: the staged files (outside Claude Code too)

Which project, file and task: the same as questions-guard.py (it reuses its helpers): the edited file (symlinks
resolved, a relative path against the event's `cwd`, backslashes as `/`) belongs to the project when its worktree shares
the project's git common dir; that worktree gives the config and the current task (task.py current_task(): the branch
`agent/<id>-...`, else the mark `gw/current-task` of that worktree's git dir). A file outside the project, an event
naming no file it can place (a Windows drive path elsewhere), no current task, no record `<taskRecord.path>/<id>.md` or
a record without a `## Files` section: allowed, silently (there is no scope to compare with).

Always allowed: the record, its folder `<id>/` (the decision log), the questions file and the log (`log`). Any other
file must be named in `## Files` (task.py files_of/in_files: exact path, a folder prefix, a simple glob). Outside it, by
`scopeGuard.mode` (config.scope_guard()):
  - `warn` (default): allowed; `additionalContext` once per task and file (mark `gw/scope-warned` in the worktree's git
    dir) saying how to go on, and each time one line in `<git common dir>/gw/deviations.jsonl` (task.py deviations);
  - `block`: denied, with the same two ways on;
  - `auto`: `block` while `modes.questions` is restrictive, else `warn`;
  - `off`: nothing.
The two ways on: add the file to `## Files` and explain it in the record's `## Change log`; or, if it is a new
requirement, open a new task linked from this one: task.py new <newid> --related <id>.

Policy when it cannot tell (unlike questions-guard.py, which denies code with a broken gw.json): this guard's default
job is to warn, so a .claude/gw.json it cannot read gives a one-line warning once and lets the edit through (the
questions guard already blocks code edits then, and commit-msg refuses a commit that is not WIP:); git hanging, or a
crash, denies only when the mode it could read is block. Not covered: files written with Bash. Output: nothing or one
JSON object on stdout, exit 0. With --staged: warnings on stderr, exit 1 only in block mode with staged files outside
Files. Python 3.8+ standard library only.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, HERE)
import config  # noqa: E402
import task  # noqa: E402

_spec = importlib.util.spec_from_file_location("questions_guard", os.path.join(HERE, "questions-guard.py"))
qg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qg)

WARNED = "gw/scope-warned"
NAME = "scope-guard"


def mode_of(cfg):
    """The mode the guard applies (off, warn or block)."""
    return config.scope_guard(cfg)["effective"]


def always_allowed(rel, cfg, record_base, task_id):
    q = config.questions_path(cfg).strip("/")
    log = (cfg.get("log") or config.schema_default("log") or "").strip("/")
    return (rel in (f"{record_base}/{task_id}.md", q, log) or rel.startswith(f"{record_base}/{task_id}/"))


def scope_of(top, cfg, task_id):
    """(record rel path, patterns) of the task, or (rel, None) when there is no record or no Files section."""
    base = config.task_record(cfg)["path"].strip("/")
    rel = f"{base}/{task_id}.md"
    try:
        text = (Path(top) / rel).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return base, rel, None
    return base, rel, task.files_of(text)


def how_on(task_id, record, rel, script_cmd):
    return (f"add `{rel}` to `## Files` of {record} and explain it in its `## Change log`; or, if it is a new requirement, "
            f"open a new task linked from this one: {script_cmd} new <newid> --related {task_id}")


def task_cmd(top):
    own = Path(top) / ".claude" / "gw" / "scripts" / "task.py"
    full = own if own.is_file() else Path(HERE) / "task.py"
    rel = os.path.relpath(str(full), str(top))
    return "python3 " + (str(full) if rel.startswith(os.pardir) else rel)


def warn_once(top, key):
    """True the first time `key` is seen in this worktree's git dir (and records it)."""
    saved, qg.WARNED = qg.WARNED, WARNED
    try:
        return qg.warn_once(top, key)
    finally:
        qg.WARNED = saved


def hook():
    event = qg.read_event()
    if event is None or event.get("tool_name") not in qg.TOOLS:
        return 0
    home = qg.home_root(event)
    path = qg.target_path(event)
    if home is None or path is None:
        return 0  # not in a repository, or a file it cannot place: no scope to compare with
    top, rel = qg.place(path, home)
    if top is None:
        return 0  # outside the project
    cfg, broken = qg.load(top)
    if broken:
        if rel != ".claude/gw.json" and warn_once(top, "broken-config"):
            qg.emit({"additionalContext": f"{NAME}: .claude/gw.json cannot be read ({broken}), so the task's scope is not "
                                          f"checked; fix it: python3 {os.path.join(HERE, 'config.py')} validate"})
        return 0
    mode = mode_of(cfg)
    if mode == "off":
        return 0
    try:
        task_id, _ = task.current_task(top, cfg)
    except task.GitStuck as exc:
        why = f"{NAME}: git did not answer ({exc}), so it cannot tell the current task; check the repository (git status)"
        if mode == "block":
            qg.emit({"permissionDecision": "deny", "permissionDecisionReason": why})
        elif warn_once(top, "git-stuck"):
            qg.emit({"additionalContext": why})
        return 0
    if not task_id:
        return 0
    base, record, patterns = scope_of(top, cfg, task_id)
    if patterns is None or always_allowed(rel, cfg, base, task_id) or task.in_files(rel, patterns):
        return 0
    way = how_on(task_id, record, rel, task_cmd(top))
    if mode == "block":
        qg.emit({"permissionDecision": "deny", "permissionDecisionReason":
                 f"{NAME} (block mode): `{rel}` is outside the scope of task {task_id} (`## Files` of {record}); {way}."})
        return 0
    task.log_deviation(top, task_id, rel, "warn")
    if warn_once(top, f"{task_id}: {rel}"):
        qg.emit({"additionalContext": f"{NAME}: `{rel}` is outside the scope of task {task_id} (`## Files` of {record}); "
                                      f"{way}. (Shown once per task and file; logged in deviations.jsonl.)"})
    return 0


def staged(root_arg):
    """The pre-commit backup: staged files outside Files. Exit 1 only in block mode."""
    top = Path(root_arg) if root_arg else config.git_toplevel(os.getcwd())
    if top is None:
        print(f"{NAME}: not inside a git work tree; run it in the project: python3 {__file__} --staged", file=sys.stderr)
        return 1
    cfg, broken = qg.load(top)
    if broken:
        print(f"{NAME}: WARNING: .claude/gw.json cannot be read ({broken}), so the task's scope is not checked; fix it: "
              f"python3 {os.path.join(HERE, 'config.py')} --root {top} validate", file=sys.stderr)
        return 0
    mode = mode_of(cfg)
    if mode == "off":
        return 0
    for head in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REBASE_HEAD"):  # the other side's files are not this task's
        out = qg.git(top, "rev-parse", "--git-path", head)
        if out and (Path(top) / out).exists():
            return 0
    task_id, _ = task.current_task(top, cfg)
    if not task_id:
        return 0
    base, record, patterns = scope_of(top, cfg, task_id)
    if patterns is None:
        return 0
    # The hook's own environment (GIT_INDEX_FILE of `git commit -a` or `git commit <paths>`) says what is staged.
    r = subprocess.run(["git", "diff", "--cached", "--name-only", "--no-renames", "-z"], cwd=str(top),
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        print(f"{NAME}: git diff --cached failed ({r.stderr.strip()}); check the repository: git status", file=sys.stderr)
        return 1 if mode == "block" else 0
    outside = [p for p in r.stdout.split("\0") if p and not always_allowed(p, cfg, base, task_id)
               and not task.in_files(p, patterns)]
    if not outside:
        return 0
    way = how_on(task_id, record, outside[0], task_cmd(top))
    listed = "\n".join(f"  {p}" for p in outside)
    if mode == "block":
        print(f"pre-commit: {NAME} (block mode): these staged files are outside the scope of task {task_id} (`## Files` "
              f"of {record}):\n{listed}\npre-commit: {way}; or unstage them: git restore --staged -- '{outside[0]}'",
              file=sys.stderr)
        return 1
    for p in outside:
        task.log_deviation(top, task_id, p, "commit-warn")
    print(f"pre-commit: {NAME}: WARNING: these staged files are outside the scope of task {task_id} (`## Files` of "
          f"{record}):\n{listed}\npre-commit: {way}", file=sys.stderr)
    return 0


def main(argv):
    if argv[:1] == ["--staged"]:
        root = argv[2] if argv[1:2] == ["--root"] and len(argv) > 2 else None
        return staged(root)
    return hook()


if __name__ == "__main__":
    if sys.argv[1:2] == ["--staged"]:
        sys.exit(main(sys.argv[1:]))
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as exc:  # noqa: BLE001 (deny only when the mode it can read is block; else say why)
        why = f"{NAME}.py failed ({type(exc).__name__}: {exc}); check it: python3 {os.path.join(HERE, 'scope-guard.py')}"
        try:
            cfg, broken = qg.load(qg.home_root(None))
            strict = not broken and mode_of(cfg) == "block"
        except Exception:  # noqa: BLE001
            strict = False
        qg.emit({"permissionDecision": "deny", "permissionDecisionReason": why} if strict else {"additionalContext": why})
        sys.exit(0)
