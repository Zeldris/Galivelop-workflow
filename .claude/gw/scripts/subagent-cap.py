#!/usr/bin/env python3
# galivelop-workflow v0.5.1
"""PreToolUse hook: ask the user when a session has launched many subagents, so a loop does not burn tokens unseen,
and deny a subagent that would run on a model in `models.disabled` (B7, below).

It counts every Agent/Task call of a session (the matcher in hooks/hooks.json and in the settings.json template is
`Agent|Task`) and, when the count reaches the cap and every 10 after it (cap, cap+10, cap+20...), returns `ask` so the
user decides in the permission prompt whether the fan-out is on purpose. It never denies, and below the cap it prints
nothing (no opinion: the normal permission flow goes on).

It also warns, without blocking, when the call has no `model` of its own (missing, empty, not a string or `inherit`
in `tool_input`) and its `subagent_type` does not set one (a `model:` other than inherit in the frontmatter of
.claude/agents/<type>.md of the project or ~/.claude/agents/; a type with no definition found is warned). The
warning is `additionalContext`: Claude Code delivers it with the tool result, so it serves the next calls, not the
current one. It is also added to every `ask` this hook gives (cap reached, or cannot count).

Output format (https://code.claude.com/docs/en/hooks.md, PreToolUse "ask" decision): a JSON object on stdout, exit 0,

  {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                          "permissionDecisionReason": "<n> subagents in this session (subagentCap <cap> in
                          .claude/gw.json): check they are not looping (gw-opt-tokens)"}}

The cap is `subagentCap` in .claude/gw.json (integer >= 1, default 30). If the config cannot be read or is invalid, the
default is used and the count goes on.

Symbolic links: the counter is opened with O_NOFOLLOW and must be a regular file owned by the user running the hook, so
a link planted in a shared temp folder is never written through; it is refused with a reason (`ask`, cannot count).
A hard link is refused too (the counter must have a single link). Old counters: when a session's counter is created, the other gw-subagents-* regular files in the folder that nobody
has written for STALE_DAYS (7) days are deleted (never a link, never a file of another user, never the one in use). The delete takes no lock: a session resumed after more than STALE_DAYS days may start from
zero if another session cleans its counter just then (the cap is then late, never skipped silently for other files).

Disabled models (B7): when `models.disabled` in .claude/gw.json is not empty, the hook works out the model the
subagent will run on: the call's own `model`, else the `model:` of its agent definition (as above), else the session's
model, which a subagent inherits (the `model` of the last assistant message in the event's `transcript_path`, read from
its last TRANSCRIPT_TAIL bytes). If an entry blocks it (the rule of models.blocked_by: the id, an id prefix, or the
family alias) the call is denied before it is counted:

  {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                          "permissionDecisionReason": "model <m> is disabled (`<entry>` in models.disabled of
                          .claude/gw.json): ... re-enable: python3 <path>/models.py enable <entry>"}}

If the list is not empty and the model cannot be told (no model anywhere, no readable transcript) or models.py is
missing next to this script, it asks instead, saying why. A config that cannot be read counts as nothing disabled, as
the cap falls back to its default.

The counter is one small file per session in tempfile.gettempdir() (named gw-subagents-<session_id>, with every
character that is not a letter, digit, dot, dash or underscore replaced by `_`). It is updated under an exclusive
lock, so subagents launched in parallel are all counted. A file that is not a non-negative integer is read as 0. The
folder can be changed with the environment variable GW_SUBAGENT_COUNTER_DIR (the tests use it; empty means the default).

Fails closed: stdin it cannot read, an event without a `session_id`, or a counter it cannot write -> `ask`, saying it
cannot count. The project root is found by config.find_root (the script's own repo, never the current directory
first). Python 3.8+ standard library only.
"""
import json
import os
import re
import select
import stat
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, HERE)
import config  # noqa: E402

try:
    import models
except ImportError:  # an install older than B7: a non-empty models.disabled then asks (cannot check)
    models = None

try:
    import fcntl
except ImportError:  # not on POSIX: count without the lock
    fcntl = None

DEFAULT_CAP = 30
STEP = 10
STDIN_WAIT = 3.0
COUNTER_DIR_ENV = "GW_SUBAGENT_COUNTER_DIR"
COUNTER_PREFIX = "gw-subagents-"
STALE_DAYS = 7
TRANSCRIPT_TAIL = 512 * 1024


class CannotCount(Exception):
    pass


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


def ask(reason, event=None):
    out = {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": reason}
    if isinstance(event, dict) and lacks_model(event):
        out["additionalContext"] = NO_MODEL
    print(json.dumps({"hookSpecificOutput": out}))


NO_MODEL = ("this subagent call has no `model` and its subagent type does not set one, so it may run on the "
            "session's model (usually the most expensive one). This reminder arrives with the tool result, so it is "
            "for the next calls: pick the model for the task with the gw-selector skill and pass it as `model` in "
            "the Agent/Task call")
AGENT_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\Z")


def agent_model(name, root):
    """The `model:` in the frontmatter of .claude/agents/<name>.md (None when absent, empty or `inherit`). The project
    file, when it exists, is the definition (the user one is not read then); otherwise the user one."""
    if not isinstance(name, str) or not AGENT_NAME.match(name):
        return None
    folders = [os.path.join(os.path.expanduser("~"), ".claude", "agents")]
    if root is not None:
        folders.insert(0, os.path.join(str(root), ".claude", "agents"))
    for folder in folders:
        try:
            with open(os.path.join(folder, name + ".md"), encoding="utf-8", errors="replace") as fh:
                lines = fh.read(20000).splitlines()
        except OSError:
            continue
        # the first file found is the definition Claude Code uses (project over user): the search stops there
        if not lines or lines[0].strip() != "---":
            return None
        for line in lines[1:]:
            if line.strip() == "---":
                break
            key, _, value = line.partition(":")
            if key.strip() == "model":
                value = value.strip().strip("\"'").strip()
                return value if value and value.lower() != "inherit" else None
        return None
    return None


def agent_sets_model(name, root):
    """True when .claude/agents/<name>.md has a `model:` in its frontmatter other than inherit."""
    return agent_model(name, root) is not None


def own_model(tool_input):
    """The call's own `model`, or None when it is missing, empty, not a string or `inherit`."""
    model = tool_input.get("model")
    if isinstance(model, str) and model.strip() and model.strip().lower() != "inherit":
        return model.strip()
    return None


def project_root():
    try:
        return config.find_root()
    except config.ConfigError:
        return None


def session_model(transcript):
    """The `model` of the last assistant message in the transcript (its last TRANSCRIPT_TAIL bytes), or None."""
    if not isinstance(transcript, str) or not transcript:
        return None
    try:
        with open(transcript, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - TRANSCRIPT_TAIL))
            lines = fh.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        try:
            row = json.loads(line)
        except ValueError:
            continue  # the first line of the tail may be cut
        message = row.get("message") if isinstance(row, dict) and row.get("type") == "assistant" else None
        model = message.get("model") if isinstance(message, dict) else None
        if isinstance(model, str) and model.strip() and not model.startswith("<"):  # `<synthetic>` is no model
            return model.strip()
    return None


def subagent_model(event):
    """(model, where it came from), or (None, None) when it cannot be told."""
    tool_input = event.get("tool_input")
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    model = own_model(tool_input)
    if model:
        return model, "the call's `model`"
    model = agent_model(tool_input.get("subagent_type"), project_root())
    if model:
        return model, f"the definition of the `{tool_input.get('subagent_type')}` agent"
    model = session_model(event.get("transcript_path"))
    if model:
        return model, "the session's model, which the subagent inherits"
    return None, None


def disabled_from_config():
    """The project's models.disabled ([] when the config cannot be read: nothing disabled, the schema default)."""
    try:
        conf = config.load(config.find_root())
    except config.ConfigError:
        return [], None
    entries = config.models(conf)["disabled"]
    return [e for e in entries if isinstance(e, str)] if isinstance(entries, list) else [], conf.get("_root")


def models_command(root):
    """How to run models.py from the project root (this script's own folder, relative when it is inside the root)."""
    path = os.path.join(HERE, "models.py")
    if root is not None:
        rel = os.path.relpath(path, str(root))
        path = path if rel.startswith("..") else rel
    return f"python3 {path}"


def disabled_decision(event):
    """(decision, reason) for a subagent whose model is disabled or cannot be told; (None, None) to go on."""
    entries, root = disabled_from_config()
    if not entries:
        return None, None
    if models is None:
        return "ask", ("models.disabled is set in .claude/gw.json but models.py is missing next to subagent-cap.py, "
                       "so the subagent's model cannot be checked; update the workflow: /gw-update")
    model, source = subagent_model(event)
    if model is None:
        return "ask", (f"models.disabled is set in .claude/gw.json ({', '.join(entries)}) and the model this subagent "
                       f"will run on cannot be told (no `model` in the call or its agent definition, and none in the "
                       f"session transcript); pass an enabled `model` (gw-selector)")
    entry = models.blocked_by(model, entries)
    if entry is None:
        return None, None
    return "deny", (f"model {model} ({source}) is disabled (`{entry}` in models.disabled of .claude/gw.json): launch "
                    f"the subagent with an enabled `model` picked with gw-selector; only if the user wants it back, "
                    f"re-enable: {models_command(root)} enable {entry}")


def lacks_model(event):
    """True when the call names no model of its own (`inherit` is not one) and its agent definition sets none."""
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    if own_model(tool_input):
        return False
    return not agent_sets_model(tool_input.get("subagent_type"), project_root())


def cap_from_config():
    """The project's subagentCap, or the default when the config cannot be read or has no valid one."""
    try:
        cap = config.load(config.find_root()).get("subagentCap", DEFAULT_CAP)
    except config.ConfigError:
        return DEFAULT_CAP
    return cap if isinstance(cap, int) and not isinstance(cap, bool) and cap >= 1 else DEFAULT_CAP


def counter_path(session_id):
    folder = os.environ.get(COUNTER_DIR_ENV) or tempfile.gettempdir()
    return os.path.join(folder, COUNTER_PREFIX + re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)[:120])


def clean_old(keep):
    """Delete the stale counters next to `keep`: own regular files named gw-subagents-* not written for STALE_DAYS."""
    folder = os.path.dirname(keep)
    limit = time.time() - STALE_DAYS * 86400
    try:
        names = os.listdir(folder)
    except OSError:
        return
    uid = os.geteuid() if hasattr(os, "geteuid") else None
    for name in names:
        path = os.path.join(folder, name)
        if not name.startswith(COUNTER_PREFIX) or path == keep:
            continue
        try:
            info = os.lstat(path)  # lstat: a link is never followed, and never deleted here
            if stat.S_ISREG(info.st_mode) and info.st_mtime < limit and (uid is None or info.st_uid == uid):
                os.unlink(path)
        except OSError:
            pass  # cleaning is best effort: it must never stop the count


def bump(path):
    """Add one to the session's counter under an exclusive lock and return the new count."""
    if not os.path.lexists(path):
        clean_old(path)
    try:
        fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    except OSError as exc:
        if os.path.islink(path):
            raise CannotCount(f"the subagent counter {path} is a symbolic link, which is not followed "
                              f"(delete it: rm {path})")
        raise CannotCount(f"the subagent counter {path} cannot be opened ({exc.strerror or exc})")
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or (hasattr(os, "geteuid") and info.st_uid != os.geteuid()) \
                or info.st_nlink != 1:
            raise CannotCount(f"the subagent counter {path} is not a regular file of this user with a single link "
                              f"(delete it: rm {path})")
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_EX)
        raw = os.read(fd, 64)
        try:
            count = int(raw.decode("ascii").strip())
        except (UnicodeDecodeError, ValueError):
            count = 0
        if count < 0:
            count = 0
        count += 1
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, str(count).encode("ascii"))
        return count
    except OSError as exc:
        raise CannotCount(f"the subagent counter {path} cannot be updated ({exc.strerror or exc})")
    finally:
        os.close(fd)  # closing releases the lock


def main():
    event, problem = read_event()
    if event is None:
        ask(f"subagent-cap.py could not use the hook event ({problem}), so it cannot count the subagents of this "
            f"session; check they are not looping (gw-opt-tokens)")
        return 0
    decision, reason = disabled_decision(event)
    if decision is not None:
        out = {"hookEventName": "PreToolUse", "permissionDecision": decision, "permissionDecisionReason": reason}
        if lacks_model(event):
            out["additionalContext"] = NO_MODEL
        print(json.dumps({"hookSpecificOutput": out}))
        return 0  # not counted: a denied call launches nothing (an approved ask goes uncounted, so the cap may come late)
    session_id = event.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        ask("subagent-cap.py got an event with no session_id, so it cannot count the subagents of this session; "
            "check they are not looping (gw-opt-tokens)", event)
        return 0
    cap = cap_from_config()
    try:
        count = bump(counter_path(session_id))
    except CannotCount as exc:
        ask(f"subagent-cap.py cannot count the subagents of this session: {exc}; check they are not looping "
            f"(gw-opt-tokens)", event)
        return 0
    out = {"hookEventName": "PreToolUse"}
    if count >= cap and (count - cap) % STEP == 0:
        out["permissionDecision"] = "ask"
        out["permissionDecisionReason"] = (f"{count} subagents in this session (subagentCap {cap} in "
                                           f".claude/gw.json): check they are not looping (gw-opt-tokens)")
    if lacks_model(event):
        out["additionalContext"] = NO_MODEL
    if len(out) > 1:
        print(json.dumps({"hookSpecificOutput": out}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail closed: a counter that crashed must not look like a green light
        ask(f"subagent-cap.py failed ({type(exc).__name__}: {exc}), so it cannot count the subagents of this "
            f"session; check they are not looping (gw-opt-tokens)")
        sys.exit(0)
