#!/usr/bin/env python3
# galivelop-workflow v0.9.1
"""PreToolUse hook on `Read` and `Bash` (B26, E58, E70): warn when a session reads WHOLE a watched file that is larger
than `wholeReadWarnBytes` in .claude/gw.json. It never blocks: it adds `additionalContext` to the call, so the next
steps read less (it only blocks the files of `wholeReadDenyPaths`, below); with nothing to say it prints nothing.

Watched files: the hand-off log (`log`), its archive (`logArchive`), every file directly or deeper under
`recordsDir`, the files and folders (ending in /) of `wholeReadPaths` and the keys of `readPointers`; never the
extensions of `wholeReadSkipExtensions` (images, PDF, notebooks). A Read is "whole" when `tool_input` has no
`offset`, `limit` or `pages` (a null, 0 or empty value counts as absent). A Bash command is "whole" for each file it
gives to `cat`, `tac`, `nl`, `less`, `more`, `bat` (without a line range) or `sed` (without -n, -i or a `q` script),
also through `<`, unless its output goes to a pipe or a file (`cat F | head`, `cat F > out`; exception, E85: `cat F | head -n N` and
`cat F | sed -n A,Bp` warn with the line count of that second command, as a range read); `cd` in the same command
moves the folder the paths resolve against (inside `( … )` only until it closes), the value of an option that takes
one (`nl -b a F`) is not a file, and the body of a heredoc (also `<<\\EOF`) is not read as commands. `grep`, `tail`, `head` and `sed -n` read a part and are not warned about, with one exception (E85): a range read of
the log or a `roadmapFiles` file over `wholeReadWarnBytes` (`sed -n A,Bp`, `sed -n p`, `head -n N`, `head` without a count
is 10 lines) warns when it covers more than `wholeReadShortLines` lines (default 40; a shorter range is silent), whatever
`wholeReadRepeatOnly` says (a range is not a whole read, so it is not remembered) and with the same output rules as above
(never into a pipe that filters or a file); it is denied only when it reaches the end of a denied file (below). The log is
compared in characters (as `logSize` is), the rest in bytes. A watched file of more than `wholeReadWarnBytes` bytes
(default 20000; 0 turns the hook off) gets a note that names the size and the command that reads less:

  readPointers   its own command ({"<path>": "<command>"}, a folder key ends in /; it wins over the two below)
  hand-off log   python3 .claude/gw/scripts/recover.py --state (the state), or grep -n for a row and Read with
                 offset and limit
  roadmap file   python3 .claude/gw/scripts/roadmap.py show <id> (one row), or grep -n for the row (a `roadmapFiles` path)
  the rest       Read with offset and limit, or grep -n for the heading first

`wholeReadRepeatOnly` (default true) warns only when this session already read the same file whole and it has not
changed since (same size and modification time): the first whole read is often needed, a second one is the content
twice in the context. The reads are kept per session in tempfile.gettempdir()/gw-reads-<session_id>.json (an own
regular file; the other sessions' files not written for `wholeReadStaleDays` days are deleted when one is created).
With no `session_id` in the event a repeat cannot be told, so nothing is warned. false = warn on every whole read.
A lock (gw-reads-<session_id>.lock, fcntl, cleaned like the state) keeps two parallel calls from losing a read, and recover.py --state drops the session's
reads on SessionStart clear|compact (`forget`): the content left the context, so a reread there is not a repeat.

`wholeReadDenyPaths` (E70; {"<path>": "<command>"}, a folder key ends in /) turns the warning into a rejection for
those files: a whole read of one of them (as above, whatever its size, extension, wholeReadWarnBytes or
wholeReadRepeatOnly) is denied with a reason that names its command; a partial read passes. A denial wins over the
warnings of the same call. A bad value denies nothing (the default, {}). For these files it fails closed (D180): a
Read from the top (`offset` absent, 0, 1 or not an integer) with no `limit` or one at or above the file's line count
(a `limit` that is not an integer, or a file it cannot count, too), and a Bash range (`sed -n`, `head`) that runs to
the end or covers the file's line count, are whole reads; `pages` only excuses a PDF. A Bash command it cannot split
is denied when one of its words, or a file its glob matches, is a denied path (against `cwd` or the root).

Output format (https://code.claude.com/docs/en/hooks.md, PreToolUse): a JSON object on stdout, exit 0,

  {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "..."}}
  {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                          "permissionDecisionReason": "..."}}

`screenshotSheet` (E50) advises on loose screenshots: each Read of a file with one of its `extensions` (outside its
`ignorePaths`) adds the image to the session's state (the same gw-reads-<session_id>.json, under "screenshots"; a
reread does not count) and, when the session has read `after` distinct images (default 3; 0 turns it off) or a
multiple of it, the note says to mount the ones still needed in one sheet and Read that: with `command`, the
project's own; without it, a generic example and the key. It works whatever wholeReadWarnBytes says, and `forget`
restarts the count. With no `session_id` nothing is counted.

Fails open, because it only advises (except for the denied paths, above): stdin it cannot read, an event that is not
a Read or a Bash call, a command it cannot split, a path outside the project, a file it cannot stat, a state file it cannot read or write or a config it
cannot read (the defaults apply to the config) print nothing and exit 0. The
project root is config.find_root (the script's own repo, never the current directory first); a relative path is
resolved against the event's `cwd`. Python 3.8+ standard library only.
"""
import contextlib
import glob
import json
import os
import re
import select
import shlex
import stat
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, HERE)
import config  # noqa: E402



def read_event():
    if sys.stdin is None or sys.stdin.isatty():
        return None
    try:
        ready, _, _ = select.select([sys.stdin], [], [], config.hook_stdin_wait())
        if not ready:
            return None
        data = json.loads(sys.stdin.read())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def settings(root):
    """The config as a dict of the hook's keys; the schema defaults when it cannot be read (`log` has none there:
    docs/handoff.md). `skip`: wholeReadSkipExtensions in lower case; `extra`: wholeReadPaths; `pointers`:
    readPointers ({path: command}); `repeat`: wholeReadRepeatOnly; `stale`: wholeReadStaleDays."""
    try:
        cfg = config.load(root)
    except Exception:  # advice only: any problem with the config means the defaults
        cfg = {}
    props = config._schema()["properties"]

    def pick(key, fallback=None):
        value = cfg.get(key)
        if isinstance(value, str) and value:
            return value
        return props[key].get("default", fallback)

    def pick_list(key):
        value = cfg.get(key)
        ok = isinstance(value, list) and all(isinstance(v, str) and v for v in value)
        return list(value) if ok else list(props[key]["default"])

    def pick_map(key):
        value = cfg.get(key)
        ok = isinstance(value, dict) and all(isinstance(k, str) and k and isinstance(v, str) and v
                                             for k, v in value.items())
        return dict(value) if ok else dict(props[key]["default"])

    pointers = pick_map("readPointers")
    repeat = cfg.get("wholeReadRepeatOnly")
    stale = cfg.get("wholeReadStaleDays")
    return {"limit": config.whole_read_warn_bytes(cfg), "log": pick("log", "docs/handoff.md"),
            "archive": pick("logArchive"), "records": pick("recordsDir"), "roadmap": roadmap_paths(cfg),
            "short": short_lines(cfg, props),
            "skip": tuple(e.lower() for e in pick_list("wholeReadSkipExtensions")),
            "extra": pick_list("wholeReadPaths"), "pointers": pointers, "deny": pick_map("wholeReadDenyPaths"),
            "repeat": repeat if isinstance(repeat, bool) else props["wholeReadRepeatOnly"]["default"],
            "stale": (stale if isinstance(stale, int) and not isinstance(stale, bool) and stale >= 1
                      else props["wholeReadStaleDays"]["default"]),
            "shots": shot_settings(cfg.get("screenshotSheet"), props["screenshotSheet"]["properties"])}


def roadmap_paths(cfg):
    """The `path` of each valid entry of `roadmapFiles` (E85); [] when the key is absent or invalid."""
    given = config.roadmap_files(cfg)
    if not isinstance(given, list):
        return []
    return [e["path"] for e in given if isinstance(e, dict) and isinstance(e.get("path"), str) and e["path"]]


def short_lines(cfg, props):
    """`wholeReadShortLines` (E85): the schema default when absent or invalid."""
    return config.whole_read_short_lines(cfg)


def shot_settings(given, props):
    """The `screenshotSheet` keys (E50), each the schema default when absent or invalid: `after`, `ext` (extensions in
    lower case), `command` and `ignore` (ignorePaths)."""
    given = given if isinstance(given, dict) else {}
    after, command = given.get("after"), given.get("command")
    ext, ignore = given.get("extensions"), given.get("ignorePaths")
    ok_list = lambda value: isinstance(value, list) and all(isinstance(v, str) and v for v in value)  # noqa: E731
    return {"after": (after if isinstance(after, int) and not isinstance(after, bool) and after >= 0
                      else props["after"]["default"]),
            "ext": tuple(e.lower() for e in (ext if ok_list(ext) and all(e.startswith(".") for e in ext)
                                             else props["extensions"]["default"])),
            "command": command if isinstance(command, str) else props["command"]["default"],
            "ignore": list(ignore) if ok_list(ignore) else list(props["ignorePaths"]["default"])}


def is_whole(tool_input):
    return not (tool_input.get("offset") or tool_input.get("limit") or tool_input.get("pages"))


def matches(real, root, rel):
    """True when `real` is the repo-relative file `rel`, or lies under it when `rel` is a folder ending in /."""
    target = os.path.realpath(os.path.join(root, rel))
    return real == target or (rel.endswith("/") and real.startswith(target.rstrip(os.sep) + os.sep))


def kind_of(path, root, log, archive, records, extra=(), pointers=None, roadmap=()):
    """('pointer', command) for a key of readPointers, ('log', None) for the hand-off log or its archive,
    ('roadmap', None) for a `roadmapFiles` path (E85), ('record', None) for a file under recordsDir or one of `extra`
    (wholeReadPaths), else (None, None)."""
    real = os.path.realpath(path)
    for rel, command in (pointers or {}).items():
        if matches(real, root, rel):
            return "pointer", command
    for rel in (log, archive):
        if rel and real == os.path.realpath(os.path.join(root, rel)):
            return "log", None
    for rel in roadmap:
        if real == os.path.realpath(os.path.join(root, rel)):
            return "roadmap", None
    if records and matches(real, root, records.rstrip("/") + "/"):
        return "record", None
    for rel in extra:
        if matches(real, root, rel):
            return "record", None
    return None, None


def denied(path, root, deny):
    """The command of the first wholeReadDenyPaths key that `path` is (or lies under), else None."""
    real = os.path.realpath(path)
    for rel, command in deny.items():
        if matches(real, root, rel):
            return command
    return None


def deny_reason(rel, how, command):
    return (f"{rel} may not be read whole (wholeReadDenyPaths in .claude/gw.json): {how} takes it whole. "
            f"Instead: `{command}`, or grep -n for what you need and Read with offset and limit.")


def note(kind, rel, size, limit, how="this Read", command=None, repeat=False, lines=None, short=0):
    taken = "takes it whole"
    if lines is not None:
        taken = ("reads it to the end" if lines >= TO_END else f"reads {lines} lines of it") + \
            f" (wholeReadShortLines {short})"
    head = (f"{rel} is {size} bytes (wholeReadWarnBytes {limit} in .claude/gw.json) and {how} {taken}, "
            f"which costs tokens on every turn it stays in the context. ")
    if repeat:
        head += "This session already read it whole and it has not changed since: its content is in the context. "
    if kind == "pointer":
        return head + f"Instead: `{command}` (readPointers in .claude/gw.json)."
    if kind == "log":
        return head + ("Next time: `python3 .claude/gw/scripts/recover.py --state` for the state, "
                       "or grep -n for the row you need and Read with offset and limit.")
    if kind == "roadmap":
        return head + ("Next time: `python3 .claude/gw/scripts/roadmap.py show <id>` for the row you need, "
                       "or grep -n for it and Read with offset and limit.")
    return head + "Next time: grep -n for the heading you need, then Read with offset and limit."


# --- E50: loose screenshots -----------------------------------------------------------------------------------------

SHOTS = "screenshots"  # the state key of the images read; never a real path (those are absolute)
SHEET_EXAMPLE = "montage <images> -tile 4x -geometry +4+4 sheet.png"


def is_shot(path, shots):
    return shots["after"] > 0 and path.lower().endswith(shots["ext"])


def shot_note(path, root, shots, state):
    """The advice for the Read of the image `path`, or None. Records the image in `state` (a dict) when it counts."""
    if state is None or not os.path.isfile(path):
        return None
    real = os.path.realpath(path)
    if any(matches(real, root, rel) for rel in shots["ignore"]):
        return None
    seen = state.get(SHOTS)
    seen = [s for s in seen if isinstance(s, str)] if isinstance(seen, list) else []
    if real in seen:
        return None
    seen.append(real)
    state[SHOTS] = seen
    if len(seen) % shots["after"]:
        return None
    base = os.path.realpath(root)
    shown = os.path.relpath(real, base) if real.startswith(base.rstrip(os.sep) + os.sep) else real
    head = (f"This session has now read {len(seen)} images one by one (the last: {shown}); each one stays in the "
            "context and costs tokens on every turn. If you still need to look at several, mount them in one sheet "
            "and Read only that: ")
    if shots["command"]:
        return head + f"`{shots['command']}` (screenshotSheet.command in .claude/gw.json)."
    return head + (f"for example `{SHEET_EXAMPLE}` (ImageMagick); set screenshotSheet.command in .claude/gw.json "
                   "to the project's own command.")


# --- Bash: which files a command reads whole -------------------------------------------------------------------------

WHOLE = {"cat", "tac", "nl", "less", "more", "bat", "batcat"}
PREFIXES = {"sudo", "env", "command", "exec", "time", "nohup", "builtin"}
HEREDOC = re.compile(r"(?<!<)<<(?!<)-?\s*\\?(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
# Short options that take the next word as their value, so it is not a file (`nl -b a F`, `less -x 4 F`).
OPTION_ARGS = {"nl": set("bdfhilnsvw"), "less": set("bhjkopxyzDPT"), "more": set("n"), "cat": set(),
               "tac": set("s"), "bat": set("lmHp"), "batcat": set("lmHp")}
SED_QUIT = re.compile(r"(^|[0-9$/;{}\s])[qQ]\s*[0-9]*\s*(;|}|$)")


def command_lines(command):
    """The lines of `command` without heredoc bodies, with backslash-newline continuations joined."""
    lines, ends = [], []
    for line in command.split("\n"):
        if ends:
            if line.strip() == ends[0]:
                ends.pop(0)
            continue
        lines.append(line)
        ends.extend(m.group(2) for m in HEREDOC.finditer(line))
    return "\n".join(lines).replace("\\\n", " ").split("\n")


def simple_commands(line):
    """The simple commands of one shell line, in order, as ("cmd", words, inputs, sent, piped) with `words` without
    redirections, `inputs` the files given with `<`, `sent` True when its standard output goes to a file (so it does
    not reach the context) and `piped` True when it goes to the next command, plus ("(",) and (")",) for the
    subshells. Raises ValueError on a line shlex cannot split (an open quote)."""
    # a lone digit right before < or > is a file descriptor (`2>`), not an operand (`head -n 80 < F`): mark it
    line = re.sub(r"(?:(?<=\s)|^)(\d)(?=[<>])", "\x00\\1", line)
    lex = shlex.shlex(line, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    out, words, inputs, sent, redirect = [], [], [], False, None

    def close(piped=False):
        out.append(("cmd", words, inputs, sent, piped))

    for token in lex:
        if redirect is not None:
            op, fd = redirect
            if op == "<":
                inputs.append(token)
            elif ">" in op and (op.startswith("&") or fd in ("", "1")) and not (op.endswith("&") and token == "2"):
                sent = True  # stdout to a file (`> out`, `&> out`); `>&2` still shows
            redirect = None
        elif token and set(token) <= set("<>&") and ("<" in token or ">" in token):
            fd = words.pop()[1:] if words and words[-1].startswith("\x00") else ""  # `2>` is fd 2, not a file operand
            redirect = (token, fd)
        elif token and set(token) <= set(";&|()"):
            close(token in ("|", "|&"))
            words, inputs, sent = [], [], False
            out.extend((c,) for c in token if c in "()")
        else:
            words.append(token)
    close()
    return out


def sed_files(args):
    """The file operands of a sed call that prints its input whole, or None when it does not: -n/--quiet/--silent,
    -i/--in-place (it edits) or a script that quits early (`q`)."""
    files, scripts, explicit, i = [], [], False, 0
    while i < len(args):
        arg = args[i]
        if arg in ("-l", "--line-length"):
            i += 2
            continue
        if arg in ("-e", "--expression", "-f", "--file"):
            explicit = True
            if arg in ("-e", "--expression") and i + 1 < len(args):
                scripts.append(args[i + 1])
            i += 2
            continue
        if arg.startswith(("--expression=", "--file=")):
            explicit = True
            scripts.append(arg.split("=", 1)[1])
        elif arg in ("--quiet", "--silent") or arg.startswith("--in-place"):
            return None
        elif arg.startswith("-") and not arg.startswith("--") and len(arg) > 1:
            if "n" in arg[1:] or "i" in arg[1:]:
                return None
            if arg.endswith("e") or arg.endswith("f"):
                explicit = True
                if arg.endswith("e") and i + 1 < len(args):
                    scripts.append(args[i + 1])
                i += 2
                continue
        elif not arg.startswith("-"):
            if not explicit and not scripts:
                scripts.append(arg)
            else:
                files.append(arg)
        i += 1
    if any(SED_QUIT.search(s) for s in scripts):
        return None
    return files


TO_END = 10 ** 9  # "lines" of a range that runs to the end of the file
SED_RANGE = re.compile(r"^\s*(?:(\d+)(?:,(\d+|\$))?)?\s*p\s*$")


def sed_range(args):
    """(files, lines) of a `sed -n` that prints one range (`A,Bp`, `A,$p`, `p`; `lines` is TO_END when it runs to the
    end) or None for anything else (-i, several commands, a regex address, a `q`)."""
    quiet, files, scripts, explicit, i = False, [], [], False, 0
    while i < len(args):
        arg = args[i]
        if arg in ("-e", "--expression") and i + 1 < len(args):
            explicit = True
            scripts.append(args[i + 1])
            i += 2
            continue
        if arg in ("-l", "--line-length"):  # its value is no file
            i += 2
            continue
        if arg in ("--quiet", "--silent"):
            quiet = True
        elif arg.startswith("--"):
            if arg.startswith("--in-place") or arg.startswith(("--expression=", "--file=")):
                return None
        elif arg.startswith("-") and len(arg) > 1:
            flags = arg[1:]
            before, has_e, attached = flags.partition("e")  # `-ne 1,80p`, `-e1,80p`, `-n -e 1,80p`
            if "i" in before or "f" in before or (has_e and ("i" in attached or "f" in attached)):
                return None
            quiet = quiet or "n" in before
            if has_e:
                explicit = True
                if attached:
                    scripts.append(attached)
                elif i + 1 < len(args):
                    scripts.append(args[i + 1])
                    i += 1
                else:
                    return None
        elif not explicit and not scripts:
            scripts.append(arg)
        else:
            files.append(arg)
        i += 1
    if not quiet or len(scripts) != 1:
        return None
    match = SED_RANGE.match(scripts[0])
    if not match:
        return None
    first, last = match.group(1), match.group(2)
    if first is None or last == "$":
        return files, TO_END
    if last is None:
        return files, 1
    return files, max(1, int(last) - int(first) + 1)


def head_range(args):
    """(files, lines) of a `head` call (10 lines without a count), or None for a byte count (-c), a count it cannot read
    (`-n -5`, `-n 1k`) or no way to tell."""
    lines, files, i = 10, [], 0
    while i < len(args):
        arg = args[i]
        value = None
        if arg in ("-n", "--lines") and i + 1 < len(args):
            value, i = args[i + 1], i + 1
        elif arg.startswith("--lines="):
            value = arg.split("=", 1)[1]
        elif arg.startswith("-n") and len(arg) > 2:
            value = arg[2:]
        elif re.match(r"^-\d+$", arg):
            value = arg[1:]
        elif arg in ("-c", "--bytes") or arg.startswith(("-c", "--bytes")):
            return None
        elif arg.startswith("-") and len(arg) > 1:
            pass  # -q, -v, -z...
        else:
            files.append(arg)
        if value is not None:
            value = value[1:] if value.startswith("+") else value  # GNU: `-n +200` is 200 lines
            if not value.isdigit():
                return None
            lines = int(value)
        i += 1
    return files, lines


def range_files(name, args):
    """(files, lines) for a Bash call that reads a range of its files (see sed_range and head_range), else None."""
    if name == "sed":
        return sed_range(args)
    if name == "head":
        return head_range(args)
    return None


def whole_files(name, args):
    """The file operands `name args` reads whole (see the module docstring), or None when it reads a part or nothing
    (then its `<` input is not read whole either)."""
    if name == "sed":
        return sed_files(args)
    if name not in WHOLE:
        return None
    if name in ("bat", "batcat") and any(a.startswith(("-r", "--line-range")) for a in args):
        return None
    files, skip = [], False
    for arg in args:
        if skip:
            skip = False
        elif arg.startswith("-") and len(arg) > 1:
            skip = len(arg) == 2 and arg[1] in OPTION_ARGS.get(name, ())
        else:
            files.append(arg)
    return files


def program_words(words):
    """`words` without leading VAR=value assignments and PREFIXES (sudo, env, …)."""
    while words and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]) or words[0] in PREFIXES):
        words = words[1:]
    return words


def passes_through(rest):
    """True when the command a pipe feeds (the first of `rest`) shows its input whole (`| less`, `| cat -n`), so what
    went into the pipe still reaches the context; False for a filter (`| head`, `| grep x`) or a file sink."""
    for item in rest:
        if item[0] != "cmd":
            continue
        _, words, inputs, sent, piped = item
        words = program_words(words)
        if not words or sent or inputs:
            return False
        operands = whole_files(os.path.basename(words[0]), words[1:])
        return operands == [] and (not piped or passes_through(rest[rest.index(item) + 1:]))
    return False


def piped_range(rest):
    """(name, lines) when the command a pipe feeds is a `head` or `sed -n A,Bp` with no file of its own (an operand `-`
    is the standard input) whose output reaches the context (E85: `cat F | head -n 200` reads 200 lines of F). Stages
    that only pass their input on (`| cat |`) are skipped before it, and stages that pass its output on (`| cat -n`)
    may follow it; anything else gives None."""
    for index, item in enumerate(rest):
        if item[0] != "cmd":
            continue
        _, words, inputs, sent, piped = item
        words = program_words(words)
        if not words or sent or inputs:
            return None
        name = os.path.basename(words[0])
        found = range_files(name, words[1:])
        if found is None:
            if piped and whole_files(name, words[1:]) == []:
                continue  # a stage that passes its input on: the range command may come after it
            return None
        if [f for f in found[0] if f != "-"]:
            return None
        if piped and not passes_through(rest[index + 1:]):
            return None
        return " ".join([name] + words[1:]), found[1]
    return None


def bash_reads(command, cwd):
    """[(path, program, lines)] for each file the Bash `command` reads into the context (not into a pipe or a file):
    whole (`lines` None) or, for `sed -n A,Bp` and `head`, a range of `lines` (E85),
    resolved against `cwd` and the `cd`s before it (a `cd` inside `( … )` ends with it); globs are expanded. Raises
    ValueError when a line cannot be split."""
    found, stack = [], []
    for line in command_lines(command):
        items = simple_commands(line)
        for index, item in enumerate(items):
            if item[0] == "(":
                stack.append(cwd)
                continue
            if item[0] == ")":
                cwd = stack.pop() if stack else cwd
                continue
            _, words, inputs, sent, piped = item
            words = program_words(words)
            if not words:
                continue
            name = os.path.basename(words[0])
            if name == "cd":
                if len(words) > 1 and words[1] != "-":
                    cwd = os.path.join(cwd, os.path.expanduser(words[1]))
                continue
            operands, lines = whole_files(name, words[1:]), None
            label = " ".join([name] + words[1:] + [f"< {i}" for i in inputs])
            if operands is None:
                operands, lines = range_files(name, words[1:]) or (None, None)
                name = f"{name} " + " ".join(words[1:]) if lines is not None else name
            # the range of a later `head`/`sed -n` (also after a range or a pass-through stage) is what reaches the
            # context, but only when one file feeds it: with several, the count is not any one file's
            if operands is not None and piped and not sent and len(operands + inputs) == 1:
                tail = piped_range(items[index + 1:])
                if tail:
                    name, lines = f"{label} | {tail[0]}", tail[1] if lines is None else min(lines, tail[1])
                    piped = False
            if operands is None or sent or (piped and not passes_through(items[index + 1:])):
                continue
            for operand in operands + inputs:
                path = os.path.join(cwd, os.path.expanduser(operand))
                hits = sorted(glob.glob(path)) if any(c in operand for c in "*?[") else [path]
                found.extend((hit, name, lines) for hit in hits)
    return found


# --- per-session memory of whole reads ------------------------------------------------------------------------------

SESSION = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def state_path(session_id):
    if not isinstance(session_id, str) or not SESSION.match(session_id):
        return None
    return os.path.join(tempfile.gettempdir(), f"gw-reads-{session_id}.json")


def own_regular(path):
    info = os.lstat(path)
    return stat.S_ISREG(info.st_mode) and (not hasattr(os, "getuid") or info.st_uid == os.getuid())


def load_state(path):
    """{realpath: [size, mtime_ns]} of the session's earlier whole reads ({} when there are none)."""
    try:
        if not own_regular(path):
            return {}
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def clean_old(keep, days):
    """Delete other sessions' gw-reads-*.json and their .lock (own regular files) not written for `days` days."""
    folder, cutoff = os.path.dirname(keep), time.time() - days * 86400
    for path in glob.glob(os.path.join(folder, "gw-reads-*.json")) + \
            glob.glob(os.path.join(folder, "gw-reads-*.lock")):
        try:
            if path != keep and own_regular(path) and os.lstat(path).st_mtime < cutoff:
                os.unlink(path)
        except OSError:
            pass


def save_state(path, data, stale):
    if not os.path.lexists(path):
        clean_old(path, stale)
    elif not own_regular(path):
        return
    fd, tmp = tempfile.mkstemp(prefix="gw-reads-tmp-", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        os.replace(tmp, path)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def forget(session_id):
    """Drop the session's whole reads: after a compaction or /clear their content is no longer in the context, so a
    reread is not a repeat (recover.py --state calls it on SessionStart clear|compact)."""
    path = state_path(session_id)
    try:
        if path and os.path.lexists(path) and own_regular(path):
            os.unlink(path)
    except OSError:
        pass


@contextlib.contextmanager
def locked(path):
    """An exclusive lock on `path` with .lock for .json while the state is read and written, so two Reads in parallel do not lose one
    of them (the last os.replace would win). No lock where fcntl is missing (Windows) or the file cannot be opened.
    The .lock is opened without following a link (O_NOFOLLOW) and only used when it is a regular file of this user,
    like the .json: a link planted in the shared temp folder is never written through (B4, E28)."""
    try:
        import fcntl
        flags = (os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
                 | getattr(os, "O_CLOEXEC", 0))  # O_NONBLOCK: a FIFO with no reader fails at once (ENXIO), no hang
        fd = os.open(path[:-len(".json")] + ".lock", flags, 0o600)
    except (ImportError, OSError):
        yield
        return
    handle = None
    try:
        info = os.fstat(fd)
        if stat.S_ISREG(info.st_mode) and (not hasattr(os, "getuid") or info.st_uid == os.getuid()):
            handle = os.fdopen(fd, "a")
    except OSError:
        pass
    if handle is None:
        os.close(fd)
        yield
        return
    try:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield
    finally:
        handle.close()


def check(path, root, conf, state, how, lines=None):
    """The note for one whole read of `path`, or None. Records the read in `state` (a dict) when it is watched. A range
    of `lines` (E85) only counts on the log and the `roadmapFiles`, over `wholeReadShortLines`, and is never recorded."""
    try:
        info = os.stat(path)
    except OSError:
        return None
    if not stat.S_ISREG(info.st_mode):
        return None
    size, limit = info.st_size, conf["limit"]
    if limit <= 0 or size <= limit or path.lower().endswith(conf["skip"]):
        return None
    kind, command = kind_of(path, root, conf["log"], conf["archive"], conf["records"], conf["extra"],
                            conf["pointers"], conf["roadmap"])
    if kind is None or (lines is not None and (kind not in ("log", "roadmap") or lines <= conf["short"])):
        return None
    real = os.path.realpath(path)
    if conf["log"] and real == os.path.realpath(os.path.join(root, conf["log"])):
        # logSize counts characters: a log of accents that passes logSize must not warn here
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                if len(handle.read()) <= limit:
                    return None
        except OSError:
            return None
    repeat = False
    if conf["repeat"] and lines is None:
        if state is None:
            return None
        now = [size, info.st_mtime_ns]
        repeat = state.get(real) == now
        state[real] = now
        if not repeat:
            return None
    rel = os.path.relpath(real, os.path.realpath(root))
    return note(kind, rel, size, limit, how, command, repeat, lines, conf["short"])


def deny_out(reasons):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": "\n".join(reasons)}}))
    return 0


def line_count(path):
    """The lines of `path` as Read counts them (a last line without a newline counts), or None when it cannot be read."""
    try:
        with open(path, "rb") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return None


def reaches_the_end(tool_input, path):
    """How a partial-looking Read takes the denied `path` whole (D180), or None: it starts at the top (`offset` absent,
    0, 1 or not an integer) and has no `limit` (`offset` 1 alone reads like no offset) or one at or above the file's
    line count. Fails closed: a `limit` that is not an integer, or a file it cannot count, counts as whole; `pages`
    only excuses a PDF (Read ignores it on any other file)."""
    offset, limit = tool_input.get("offset"), tool_input.get("limit")
    if tool_input.get("pages") and path.lower().endswith(".pdf"):
        return None
    if is_number(offset) and offset > 1:
        return None
    if not limit:
        return f"this Read (offset {offset!r} and no limit: it starts at the top)"
    reach = covers(limit if is_number(limit) else TO_END, path)
    return f"this Read (limit {limit!r}; {reach})" if reach else None


def is_number(value):
    return isinstance(value, int) and not isinstance(value, bool)


def covers(lines, path):
    """Why a read of the first `lines` lines of the denied `path` takes it whole (D180), or None: `lines` is TO_END
    (or not known) or at or above the file's line count; a file it cannot count counts as whole."""
    if lines >= TO_END:
        return "it runs to the end"
    count = line_count(path)
    if count is None:
        return "the file's lines cannot be counted"
    return f"the file has {count} lines" if lines >= count else None


NAME = re.compile(r"[^\s;&|()<>'\"`=]+")


def named_denied(command, cwd, root, deny):
    """[(rel, command)] of the wholeReadDenyPaths files that a Bash `command` bash_reads cannot split names (D180):
    each word, resolved against `cwd` and against the root (a `cd` before it is not followed), with its glob expanded."""
    found = []
    for word in NAME.findall(command):
        word = os.path.expanduser(word)
        for base in (cwd, root):
            path = os.path.join(base, word)
            hits = [path] + (sorted(glob.glob(path)) if any(c in word for c in "*?[") else [])
            for hit in hits:
                alternative = denied(hit, root, deny)
                if not alternative:
                    continue
                rel = os.path.relpath(os.path.realpath(hit), os.path.realpath(root))
                if (rel, alternative) not in found:
                    found.append((rel, alternative))
    return found


def unparsed_reason(rel, command):
    return (f"{rel} may not be read whole (wholeReadDenyPaths in .claude/gw.json) and this command cannot be split "
            f"(an open quote?), so it is denied because it names it. Fix the quoting, or instead: `{command}`, or "
            f"grep -n for what you need and Read with offset and limit.")


def main():
    event = read_event()
    if not event or event.get("tool_name") not in ("Read", "Bash"):
        return 0
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    cwd = event.get("cwd") if isinstance(event.get("cwd"), str) and event.get("cwd") else os.getcwd()
    partial = unparsed = None  # D180: what only a wholeReadDenyPaths entry can deny
    if event["tool_name"] == "Read":
        target = tool_input.get("file_path")
        if not isinstance(target, str) or not target:
            return 0
        target = target if os.path.isabs(target) else os.path.join(cwd, target)
        reads = [(target, "this Read", None)] if is_whole(tool_input) else []
        partial = None if reads else target
    else:
        command = tool_input.get("command")
        if not isinstance(command, str) or not command:
            return 0
        try:
            reads = [(path, f"this `{name}`", lines) for path, name, lines in bash_reads(command, cwd)]
        except Exception:  # a command it cannot split: only a denied path it names stops it
            reads, unparsed = [], command
    if not reads and partial is None and unparsed is None:
        return 0
    try:
        root = str(config.find_root())
    except Exception:
        return 0
    conf = settings(root)
    if partial is not None:
        alternative = denied(partial, root, conf["deny"])
        how = reaches_the_end(tool_input, partial) if alternative else None
        if how:
            rel = os.path.relpath(os.path.realpath(partial), os.path.realpath(root))
            return deny_out([deny_reason(rel, how, alternative)])
        return 0
    if unparsed is not None:
        reasons = [unparsed_reason(rel, alternative)
                   for rel, alternative in named_denied(unparsed, cwd, root, conf["deny"])]
        return deny_out(reasons) if reasons else 0
    reasons = []
    for path, how, lines in reads:
        command = denied(path, root, conf["deny"])
        reach = covers(lines, path) if command and lines is not None else None
        if command and (lines is None or reach):  # D180: a range that reaches the end is a whole read
            rel = os.path.relpath(os.path.realpath(path), os.path.realpath(root))
            text = deny_reason(rel, how if lines is None else f"{how} ({reach})", command)
            if text not in reasons:
                reasons.append(text)
    if reasons:  # a denial wins over any warning of the same call
        return deny_out(reasons)
    shots = conf["shots"]
    shot_reads = [path for path, how, _ in reads if how == "this Read" and is_shot(path, shots)]
    if conf["limit"] <= 0 and not shot_reads:
        return 0
    need_state = (conf["repeat"] and conf["limit"] > 0) or shot_reads
    spath = state_path(event.get("session_id")) if need_state else None
    notes = []
    with locked(spath) if spath else contextlib.nullcontext():
        state = load_state(spath) if spath else None
        before = json.dumps(state, sort_keys=True) if state is not None else None
        for path, how, lines in reads if conf["limit"] > 0 else ():
            text = check(path, root, conf, state if conf["repeat"] else None, how, lines)
            if text and text not in notes:
                notes.append(text)
        for path in shot_reads:
            text = shot_note(path, root, shots, state)
            if text:
                notes.append(text)
        if spath and json.dumps(state, sort_keys=True) != before:
            save_state(spath, state, conf["stale"])
    if notes:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "additionalContext": "\n".join(notes)}}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # advice only: never stop a Read
        sys.exit(0)
