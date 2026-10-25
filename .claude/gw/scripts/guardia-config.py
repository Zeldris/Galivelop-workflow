#!/usr/bin/env python3
# galivelop-workflow v0.4.0
"""PreToolUse hook: ask the user before Claude edits the workflow's own configuration.

The files that wire the workflow (.claude/settings.json, .claude/gw.json, everything under .githooks/ and under
.claude/gw/scripts/) change only with the user's OK; AGENTS.md says so, and this hook makes the rule checkable. It
never denies: it returns `ask`, so the user decides in the permission prompt.

Output format (https://code.claude.com/docs/en/hooks.md, PreToolUse "ask" decision): a JSON object on stdout, exit 0,

  {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                          "permissionDecisionReason": "..."}}

`permissionDecisionReason` is what the user sees in the prompt. No output at all means "no opinion" (the normal
permission flow goes on).

What it looks at, in the event on stdin (`tool_name`, `tool_input`, `cwd`):

  Edit, Write, MultiEdit      tool_input.file_path (NotebookEdit: notebook_path). Absolute or relative (against the
                              event's `cwd`), with `./`, `..` and symlinks resolved; a path outside the project is
                              none of its business.
  Bash                        tool_input.command, split into simple commands (`;`, `&&`, `||`, `|`, `&`, newlines,
                              `bash -c '...'` and `eval` recursively). It asks when a command names a protected path AND
                              writes to it: a redirection (`>`, `>>`, `>|`) to it, `tee`, `sed -i`, `perl -i`, `cp`,
                              `mv`, `rm`, `install`, `ln`, `chmod`, `chown`, `truncate`, `touch`, `dd`, `rsync`,
                              `find -delete`, `git checkout|restore|rm|mv|clean`. A plain read (`cat`, `grep`, `git
                              diff`, `python3 .claude/gw/scripts/x.py`) is allowed. Not seen, on purpose (a hook cannot
                              parse a shell): a path built at run time, and code that opens the file inside
                              `python3 -c`. A `cd` to a literal folder is followed; `rm -r .claude` counts.

Project root: config.find_root (the script's own repo when it holds .claude/gw.json, else the project the hook runs
in); it does not read or validate the config. Fails closed: stdin it cannot read, an event without the tool name or
the target, or a root it cannot find -> `ask`, with that as the reason. Python 3.8+ standard library only.
"""
import json
import os
import re
import select
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, HERE)
import config  # noqa: E402

STDIN_WAIT = 3.0
EDIT_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
TARGET_KEYS = ("file_path", "notebook_path", "path")
EXACT = (".claude/settings.json", ".claude/gw.json")
TREES = (".githooks", ".claude/gw/scripts")
ANCESTORS = (".claude", ".claude/gw")  # removing or moving one takes protected files with it
WRITERS = {"tee", "cp", "mv", "rm", "install", "ln", "chmod", "chown", "chgrp", "truncate", "touch", "dd", "rsync",
           "unlink", "shred", "rmdir", "patch"}
DESTRUCTIVE = {"rm", "mv", "unlink", "shred", "rmdir"}  # these also count when they name an ancestor folder
IN_PLACE = {"sed", "gsed", "perl", "ruby"}
GIT_WRITES = {"checkout", "restore", "rm", "mv", "clean"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
WRAPPERS = {"sudo", "doas", "env", "command", "exec", "time", "nohup", "nice", "xargs", "builtin"}
RULE = ("these files change only with the user's OK (the workflow's rule). If the user approves, go ahead; to "
        "regenerate the applied copy from the workflow, run: python3 scripts/aplicar.py . (in a project, /gw-update)")


def read_event():
    """(event, problem): the hook's JSON object from stdin, or (None, why it cannot be used)."""
    if sys.stdin is None or sys.stdin.isatty():
        return None, "nothing arrived on stdin"
    try:
        ready, _, _ = select.select([sys.stdin], [], [], STDIN_WAIT)
        if not ready:
            return None, "stdin stayed empty"
        text = sys.stdin.read()
    except (OSError, ValueError) as exc:
        return None, f"stdin could not be read ({exc})"
    try:
        data = json.loads(text)
    except ValueError:
        return None, "stdin is not valid JSON"
    if not isinstance(data, dict):
        return None, "stdin is not a JSON object"
    return data, None


def ask(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                             "permissionDecisionReason": reason}}))


def classify(token, base, root):
    """The project-relative, normalised path `token` names and its kind: ('protected' | 'ancestor' | None). `base`
    is the folder relative paths are read from; `root` the real project root."""
    if not token or token.startswith("~"):
        return None, None
    token = re.sub(r"^(\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]*)(?=/|$)", root, token)
    try:
        path = os.path.realpath(token if os.path.isabs(token) else os.path.join(base, token))
        rel = os.path.relpath(path, root)
    except (OSError, ValueError):
        return None, None
    if rel == ".." or rel.startswith("../") or rel.startswith(".." + os.sep):
        return None, None  # outside the project
    rel = rel.replace(os.sep, "/")
    low = rel.lower()  # a case-insensitive disk (macOS, Windows) must not be a way round
    if low in EXACT or any(low == t or low.startswith(t + "/") for t in TREES):
        return rel, "protected"
    if low in ANCESTORS:
        return rel, "ancestor"
    return rel, None


def tokenize(command):
    """Shell words of `command`; operators (`;`, `&&`, `>>`, ...) come out as words of their own."""
    text = command.replace("\\\n", " ").replace("\n", " ; ")
    lex = shlex.shlex(text, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    try:
        return list(lex)
    except ValueError:  # an unclosed quote: still look at the words, cut crudely
        return [w.strip("'\"") for w in re.split(r"\s+|(?<=[;&|<>])|(?=[;&|<>])", text) if w and w.strip("'\"")]


def is_redirect(word):
    return "<" in word or ">" in word


def is_separator(word):
    return bool(word) and all(c in "();|&" for c in word)


def segments(words):
    out, cur = [], []
    for w in words:
        if is_separator(w):
            if cur:
                out.append(cur)
            cur = []
        else:
            cur.append(w)
    if cur:
        out.append(cur)
    return out


def command_word(words):
    """(index, word) of the command a simple command runs: after variable assignments, wrappers (`sudo`, `env`, ...)
    and the options that follow them."""
    skipping = False
    for i, w in enumerate(words):
        if is_redirect(w):
            continue
        if re.match(r"[A-Za-z_][A-Za-z0-9_]*=", w):
            continue
        if skipping and w.startswith("-"):
            continue
        name = os.path.basename(w)
        if name in WRAPPERS:
            skipping = True
            continue
        return i, name
    return None, None


def in_place_flag(words):
    return any(w == "--in-place" or w.startswith("--in-place=") or re.match(r"-[A-Za-z]*i", w) and not w.startswith("--")
               for w in words)


def bash_hits(command, base, root, depth=0):
    """[rel, ...]: the protected paths `command` writes to."""
    hits = []
    for seg in segments(tokenize(command)):
        i, cmd = command_word(seg)
        args = [w for j, w in enumerate(seg) if j != i and not is_redirect(w)]
        if cmd in ("cd", "pushd"):  # later commands read their relative paths from there
            target = next((w for w in args if not w.startswith("-")), None)
            if target and not re.search(r"[$~`*?\[]", target):
                base = os.path.realpath(target if os.path.isabs(target) else os.path.join(base, target))
            continue
        if cmd in SHELLS | {"eval"} and depth < 3:
            for j, w in enumerate(seg):
                if j > (i or 0) and (cmd == "eval" or seg[j - 1] == "-c" or re.match(r"-[a-z]*c$", seg[j - 1])):
                    hits += bash_hits(w, base, root, depth + 1)
        writes = False
        if cmd in WRITERS:
            writes = True
        elif cmd in IN_PLACE and in_place_flag(args):
            writes = True
        elif cmd == "git":
            sub = next((w for k, w in enumerate(args) if not w.startswith("-") and (k == 0 or args[k - 1] not in ("-C", "-c"))), "")
            writes = sub in GIT_WRITES
        elif cmd == "find":
            writes = "-delete" in args
        for j, w in enumerate(seg):
            if is_redirect(w) or j == i:
                continue
            rel, kind = classify(w, base, root)
            if kind is None:
                continue
            redirected = j > 0 and ">" in seg[j - 1]  # `>`, `>>`, `>|`, `&>`: the word after it is written
            if kind == "protected" and (redirected or writes):
                hits.append(rel)
            elif kind == "ancestor" and (redirected or cmd in DESTRUCTIVE):
                hits.append(rel)
    return hits


def decide(event, root):
    """The reason to ask, or None to say nothing."""
    tool = event.get("tool_name")
    tool_input = event.get("tool_input")
    if not isinstance(tool, str) or not tool:
        return "the hook event has no tool_name, so guardia-config.py cannot tell what is about to run"
    if not isinstance(tool_input, dict):
        return f"the {tool} call has no tool_input, so guardia-config.py cannot tell what it touches"
    cwd = event.get("cwd") if isinstance(event.get("cwd"), str) and os.path.isabs(event.get("cwd", "")) else root
    base = os.path.realpath(cwd)
    if tool == "Bash":
        command = tool_input.get("command")
        if not isinstance(command, str):
            return "the Bash call has no command string, so guardia-config.py cannot tell what it writes"
        hits = bash_hits(command, base, root)
        if hits:
            return f"this command writes to {hits[0]}: {RULE}"
        return None
    if tool in EDIT_TOOLS:
        target = next((tool_input[k] for k in TARGET_KEYS if isinstance(tool_input.get(k), str) and tool_input[k]), None)
        if target is None:
            return f"the {tool} call names no file_path, so guardia-config.py cannot tell which file it edits"
        rel, kind = classify(target, base, root)
        if kind == "protected":
            return f"{tool} would change {rel}: {RULE}"
    return None


def main():
    event, problem = read_event()
    if event is None:
        ask(f"guardia-config.py could not use the hook event ({problem}), so it cannot tell whether the workflow's "
            f"configuration is being edited; confirm the call is safe")
        return 0
    try:
        root = os.path.realpath(str(config.find_root()))
    except config.ConfigError as exc:
        ask(f"guardia-config.py cannot find the project root ({str(exc).strip()}), so it cannot tell whether the "
            f"workflow's configuration is being edited; confirm the call is safe")
        return 0
    reason = decide(event, root)
    if reason:
        ask(reason)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail closed: a guard that crashed must not look like a green light
        ask(f"guardia-config.py failed ({type(exc).__name__}: {exc}), so it cannot tell whether the workflow's "
            f"configuration is being edited; confirm the call is safe")
        sys.exit(0)
