#!/usr/bin/env python3
# galivelop-workflow v0.7.1
"""PreToolUse hook (C8, `modes.careful`): ask the user before Claude runs a destructive Bash command.

It never denies: it returns `ask` (the same JSON as config-guard.py, whose parser it reuses), so the user decides in the
permission prompt; `permissionDecisionReason` names the command and why it is dangerous. No output means "no opinion".
`modes.careful: false` in .claude/gw.json turns it off (it then prints nothing).

What asks, in `tool_input.command` split into simple commands (`;`, `&&`, `||`, `|`, newlines, `bash -c '...'`/`eval`
recursively, wrappers such as `sudo`/`env`/`xargs` looked through):

  rm -r | -R | --recursive (any flag group: `-rf`, `-fr`, `-Rf`)   unless every target is exempt (below)
  git push --force | -f | --force-with-lease | --force-if-includes | a `+ref` refspec       rewrites the remote history
  git push --delete | -d | a `:ref` refspec (`git push origin :old`)                        deletes a remote branch or tag
  git reset --hard                                                                          drops uncommitted work
  git branch -D (or `-d -f`, `--delete --force`)                                            deletes an unmerged branch
  git clean with -f/--force (not with -n/--dry-run)                                         deletes untracked files
  git checkout -- . | git checkout . | git restore . (also `:/`, `*`)                       overwrites the whole tree
      (`git restore --staged .` leaves the files alone and is not asked about)

Not asked about, on purpose (false positives; a hook cannot parse a shell):
  - text that is only data: a quoted commit message or argument (`git commit -m "avoid rm -rf"`), the body of a heredoc
    (`cat <<'EOF' ... EOF`), `echo "git reset --hard"`;
  - `rm -r` whose every target starts with an exempt prefix, `modes.carefulExempt` (default `/tmp/`, `/var/tmp/`,
    `$TMPDIR/`, `${TMPDIR}/`; the scratchpad of a session lives under `/tmp/`). The prefix must be followed by
    something (`/tmp/` itself is not exempt) that has no `..`, `$`, backtick or glob (`/tmp/*`). Only `rm` has
    exemptions: a git command is always asked about.
Not seen: a command built at run time (`$cmd`, `python3 -c "shutil.rmtree(...)"`), `find ... -delete`/`-exec rm -rf`,
`git stash drop`, `git worktree remove --force`.

Fails closed like config-guard.py for an event it cannot read or without a command (-> `ask`), except when the config
turns the mode off. A config it cannot read leaves the mode on with the defaults. Python 3.8+ standard library only.
"""
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, HERE)
import config  # noqa: E402

_spec = importlib.util.spec_from_file_location("config_guard", os.path.join(HERE, "config-guard.py"))
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)  # the parser (tokenize, segments, command_word, ...) lives there: one copy

HEREDOC = re.compile(r"<<-?\s*(?:\\?([A-Za-z_][A-Za-z0-9_]*)|'([^'\n]+)'|\"([^\"\n]+)\")")
RESTORE_ALL = {".", ":/", "*", "./"}
PUSH_VALUE = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
DEFAULT_EXEMPT = ["/tmp/", "/var/tmp/", "$TMPDIR/", "${TMPDIR}/"]


def strip_heredocs(command):
    """`command` without the bodies of its heredocs (the lines after `<<EOF` up to the `EOF` line): they are data."""
    lines, out, end = command.split("\n"), [], []
    for line in lines:
        if end:
            if line.strip() == end[0] or (line.strip("\t") == end[0]):
                end.pop(0)
            continue
        out.append(line)
        end = [m.group(1) or m.group(2) or m.group(3) for m in HEREDOC.finditer(line)]
    return "\n".join(out)


def exempt_target(target, prefixes):
    for p in prefixes:
        if target.startswith(p) and len(target) > len(p):
            return not re.search(r"\.\.|\$|`|[*?\[]", target[len(p):])  # nothing built at run time, no glob, no `..`
    return False


def rm_reason(args, prefixes):
    targets, recursive, dd = [], False, False
    for w in args:
        if dd or not w.startswith("-") or w == "-":
            targets.append(w)
        elif w == "--":
            dd = True
        elif w == "--recursive" or (not w.startswith("--") and re.search(r"[rR]", w)):
            recursive = True
    if not recursive:
        return None
    if targets and all(exempt_target(t, prefixes) for t in targets):
        return None
    return "`rm -r` deletes folders and everything below them, with no way back"


def git_reason(args, k, base):
    sub, rest = args[k], args[k + 1:]
    opts = [w for w in rest if w.startswith("-") and w != "--" and w != "-"]
    before_dd = rest[:rest.index("--")] if "--" in rest else rest
    flags = "".join(w[1:] for w in before_dd if re.fullmatch(r"-[A-Za-z]+", w))
    longs = [w.split("=", 1)[0] for w in before_dd if w.startswith("--")]
    pos = []
    n = 0
    while n < len(before_dd):
        w = before_dd[n]
        if w in PUSH_VALUE and sub == "push":
            n += 2
            continue
        if not w.startswith("-"):
            pos.append(w)
        n += 1
    if sub == "push":
        if "--force" in longs or "--force-with-lease" in longs or "--force-if-includes" in longs or "f" in flags \
                or any(p.startswith("+") for p in pos):
            return "`git push --force` rewrites the remote history and can lose other people's commits"
        if "--delete" in longs or "d" in flags or any(p.startswith(":") and len(p) > 1 for p in pos):
            return "`git push --delete` (or `git push <remote> :<ref>`) deletes a remote branch or tag"
    elif sub == "reset" and "--hard" in longs:
        return "`git reset --hard` throws away every uncommitted change"
    elif sub == "branch":
        forced = "--force" in longs or "f" in flags
        if "D" in flags or (("--delete" in longs or "d" in flags) and forced):
            return "`git branch -D` deletes a branch even if it is not merged"
    elif sub == "clean":
        if ("--force" in longs or "f" in flags) and not ("--dry-run" in longs or "n" in flags):
            return "`git clean -f` deletes untracked files for good"
    elif sub in ("checkout", "restore") and guard.git_write_call(args, k):
        paths = rest[rest.index("--") + 1:] if "--" in rest else ([w for w in rest if not w.startswith("-")]
                                                                  if sub == "restore" else rest)
        if any(p in RESTORE_ALL for p in paths) and not (sub == "checkout" and "-b" in opts):
            return f"`git {sub} .` overwrites every modified file of the tree with the committed one"
    return None


def command_reason(command, base, prefixes, depth=0):
    for seg in guard.segments(guard.tokenize(strip_heredocs(command))):
        i, cmd = guard.command_word(seg)
        if cmd is None:
            continue
        if cmd == "git":
            seg, _ = guard.expand_git_alias(seg, i, base)
        args = [seg[j] for j in guard.arg_indexes(seg, i)]
        if cmd in guard.SHELLS | {"eval"} and depth < 3:
            for j, w in enumerate(seg):
                if j > i and (cmd == "eval" or seg[j - 1] == "-c" or re.match(r"-[a-z]*c$", seg[j - 1])):
                    found = command_reason(w, base, prefixes, depth + 1)
                    if found:
                        return found
        reason = None
        if cmd == "rm":
            reason = rm_reason(args, prefixes)
        elif cmd == "git":
            k = guard.git_subcommand(args)
            reason = git_reason(args, k, base) if k is not None else None
        if reason:
            return f"{reason}: `{' '.join(seg[i:])[:120]}`"
    return None


def settings():
    """(careful, exempt) from .claude/gw.json; a config it cannot read leaves the mode on with the defaults."""
    try:
        cfg = config.load()
        mode = config.modes(cfg)
        return bool(mode["careful"]), list(mode["carefulExempt"])
    except Exception:  # noqa: BLE001 (any config trouble: keep the safe side)
        return True, DEFAULT_EXEMPT


def main():
    careful, prefixes = settings()
    if not careful:
        return 0
    event, problem = guard.read_event()
    if event is None:
        guard.ask(f"careful.py could not use the hook event ({problem}), so it cannot tell whether the command is "
                  f"destructive; confirm it is safe (or set modes.careful to false in .claude/gw.json)")
        return 0
    tool_input = event.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if event.get("tool_name") != "Bash":
        return 0
    if not isinstance(command, str):
        guard.ask("the Bash call has no command string, so careful.py cannot tell whether it is destructive; "
                  "confirm it is safe")
        return 0
    cwd = event.get("cwd") if isinstance(event.get("cwd"), str) and os.path.isabs(event.get("cwd", "")) else os.getcwd()
    reason = command_reason(command, os.path.realpath(cwd), prefixes)
    if reason:
        guard.ask(f"destructive command: {reason}. If the user approves, go ahead; to stop asking, set "
                  f"modes.careful to false in .claude/gw.json")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # fail closed
        guard.ask(f"careful.py failed ({type(exc).__name__}: {exc}), so it cannot tell whether the command is "
                  f"destructive; confirm it is safe")
        sys.exit(0)
