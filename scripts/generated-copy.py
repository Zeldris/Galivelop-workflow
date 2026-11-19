#!/usr/bin/env python3
# galivelop-workflow v0.8.1
"""PreToolUse hook on Edit/Write/MultiEdit/NotebookEdit, in the workflow repo only (E56): warn when a session edits a
copy that `apply.py` generates from a source in this repo, and name the source. It never blocks: it adds
`additionalContext` to the call, so the agent edits the source next; with no warning it prints nothing (no opinion).

The copies and their sources (the copy plan of `build` in scripts/apply.py):

  .claude/gw/scripts/<f>                   scripts/<f>
  .claude/gw/schema/<f>                    schema/<f>
  .claude/skills/LICENSE-mattpocock-skills LICENSE-mattpocock-skills
  .claude/skills/<skill>/<f>               skills/<skill>/<f>
  .githooks/<f>                            templates/githooks/<f>
  .claude/agents/<f>                       templates/claude/agents/<f>

The notes in .claude/gw/*.md are not copies (the project owns them once created) and are left alone.

Workflow-only (apply.py `WORKFLOW_ONLY_SCRIPTS`): it is never copied into a project, and only this repo's
.claude/settings.json runs it; taking that entry out turns it off. The root is this script's own repo (its parent
folder), never the current directory. Output format (https://code.claude.com/docs/en/hooks.md, PreToolUse): a JSON
object on stdout, exit 0,

  {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "..."}}

Fails open, because it only advises: stdin it cannot read, another tool, a path outside the repo or outside the copies
print nothing and exit 0; its entry ends in `|| true`, so a missing script (an older checkout) does
not block the edit either. It waits `hookStdinWait` for the event. A relative path is resolved against the event's `cwd`. Python 3.8+ standard library only.
"""
import json
import os
import select
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import config  # noqa: E402

ROOT = os.path.dirname(HERE)
TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
# (copy prefix, source prefix), most specific first: a file maps to the source prefix plus the rest of its path.
COPIES = (
    (".claude/gw/scripts/", "scripts/"),
    (".claude/gw/schema/", "schema/"),
    (".claude/skills/LICENSE-mattpocock-skills", "LICENSE-mattpocock-skills"),
    (".claude/skills/", "skills/"),
    (".githooks/", "templates/githooks/"),
    (".claude/agents/", "templates/claude/agents/"),
)


def read_event():
    if sys.stdin is None or sys.stdin.isatty():
        return None
    try:
        ready, _, _ = select.select([sys.stdin], [], [], config.hook_stdin_wait(ROOT))
        if not ready:
            return None
        data = json.loads(sys.stdin.read())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def copies():
    """COPIES plus the agentsSkillsDir copy of the skills (D7); the schema default when the config cannot be read."""
    try:
        agents = config.agents_skills_dir(config.load(ROOT))
    except Exception:  # advice only: an unreadable config gives the default
        agents = config.agents_skills_dir({})
    agents = agents.strip("/")
    if not agents:
        return COPIES
    return ((f"{agents}/LICENSE-mattpocock-skills", "LICENSE-mattpocock-skills"), (f"{agents}/", "skills/")) + COPIES


def source_of(rel):
    """The source path (repo-relative, '/'-separated) of the copy `rel`, or None when `rel` is not a copy."""
    for copy, source in copies():
        if rel == copy or (copy.endswith("/") and rel.startswith(copy) and len(rel) > len(copy)):
            return source + rel[len(copy):]
    return None


def note(rel, source, exists):
    where = f"Edit {source} instead" if exists else f"Create it as {source} instead"
    return (f"{rel} is a copy that `python3 scripts/apply.py` generates from {source}: an edit here is overwritten "
            f"and `bash tests/check.sh` fails while the two differ. {where}, then run `python3 scripts/apply.py` "
            f"to refresh the copy (docs/agent-map.md says which file is the source).")


def main():
    event = read_event()
    if not event:
        return 0
    key = TOOLS.get(event.get("tool_name"))
    tool_input = event.get("tool_input")
    if key is None or not isinstance(tool_input, dict):
        return 0
    target = tool_input.get(key)
    if not isinstance(target, str) or not target:
        return 0
    cwd = event.get("cwd") if isinstance(event.get("cwd"), str) and event.get("cwd") else os.getcwd()
    path = os.path.realpath(target if os.path.isabs(target) else os.path.join(cwd, target))
    rel = os.path.relpath(path, ROOT)
    if rel == os.pardir or rel.startswith(os.pardir + os.sep) or os.path.isabs(rel):
        return 0
    rel = rel.replace(os.sep, "/")
    source = source_of(rel)
    if source is None:
        return 0
    exists = os.path.exists(os.path.join(ROOT, *source.split("/")))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "additionalContext": note(rel, source, exists)}}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # advice only: never stop an edit
        sys.exit(0)
