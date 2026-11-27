#!/usr/bin/env python3
# galivelop-workflow v0.9.1
"""PreToolUse hook (C8, `modes.careful`): ask the user before Claude runs a destructive Bash command.

It never denies: it returns `ask` (the same JSON as config-guard.py, whose parser it reuses), so the user decides in the
permission prompt; `permissionDecisionReason` names the command and why it is dangerous. No output means "no opinion".
`modes.careful: false` in .claude/gw.json turns it off (it then prints nothing).

What asks, in `tool_input.command` split into simple commands (`;`, `&&`, `||`, `|`, newlines, `bash -c '...'`/`eval`
recursively, wrappers such as `sudo`/`env`/`xargs` looked through):

  rm -r | -R | --recursive (any flag group: `-rf`, `-fr`, `-Rf`)   unless every target is exempt (below)
  git push --force | -f | --force-with-lease | --force-if-includes | --mirror | --prune | a `+ref` refspec  rewrites or prunes the remote
  git push --delete | -d | a `:ref` refspec (`git push origin :old`)                        deletes a remote branch or tag
  git reset --hard                                                                          drops uncommitted work
  git branch -D (or `-d -f`, `--delete --force`)                                            deletes an unmerged branch
  git clean with -f/--force (not with -n/--dry-run)                                         deletes untracked files
  git checkout -- . | git checkout . | git restore . (also `:/`, `*`)                       overwrites the whole tree
  git checkout -f | git switch -f | --discard-changes                                       drops local changes
      (`git restore --staged .` leaves the files alone and is not asked about)
  A long option counts by any prefix git would take for it among the subcommand's options (`--forc`, `--delet`,
  `--mirro`, `git reset --ha`; one matching several asks if any is dangerous; `git clean -f --dry` is a dry run), as
  `rm --recur` does for rm; the words after `--` of `git push` are still refspecs (`git push -- origin +main`). A
  command substitution, `$(...)`, backticks or `<(...)`/`>(...)` (not `$((...))`, not inside `'...'` or `$'...'`), is
  read twice: its body as a command of its own, and its output as unknown words; it asks ("cannot read substituted
  commands") when that output is the command word of a line that names `git`, `gh` or `rm`, a word of an `rm`, `eval` or
  `bash -c`, the subcommand or a `-c alias.*` of git, or a word of a git call that careful.py checks (push, reset,
  branch, clean, checkout, switch, restore); not the value of `git -C`. Substitutions nested more than 3 deep ask.

Inside a linked git worktree under a prefix of `modes.carefulWorktrees` (default `.claude/worktrees/`, relative to the main
repository's root; an agent's worktree is disposable and a background subagent has nobody to ask; an empty list = no
exemption) `git reset --hard`, `git clean -f`, `git checkout|restore .`, `git checkout -f` and `git switch -f` are NOT
asked about; `rm -r` outside the exempt prefixes, `git push --force`/`--delete` and `git branch -D` still are, there too.
The exemption is off (it asks) when the command holds a `cd`/`pushd` or sets `GIT_DIR`/`GIT_WORK_TREE`/..., because the
git call may then act on another tree. A git alias it cannot follow (`!...`) asks. `eval` is read as the one command its
words make.

Not asked about, on purpose (false positives; a hook cannot parse a shell):
  - text that is only data: a quoted commit message or argument (`git commit -m "avoid rm -rf"`), the body of a heredoc
    (`cat <<'EOF' ... EOF`), `echo "git reset --hard"`;
  - `rm -r` whose every target starts with an exempt prefix, `modes.carefulExempt` (default `/tmp/`, `/var/tmp/`,
    `$TMPDIR/`, `${TMPDIR}/`, the last two only while TMPDIR is set and not empty in the hook's environment; the scratchpad of a session lives under `/tmp/`). The prefix must be followed by
    something (`/tmp/` itself is not exempt) that has no `..`, `$`, backtick or glob (`/tmp/*`). Only `rm` has
    exemptions: a git command is always asked about.
Not seen: a command built at run time (`$cmd`, `$g push -f`, `python3 -c "shutil.rmtree(...)"`), `find ... -delete`/
`-exec rm -rf`, `git stash drop`, `git worktree remove --force`, `env -S 'git push -f'`, a script fed on stdin
(`bash <<< 'rm -rf x'`, `bash <<EOF ... EOF`), a brace group (`{ git push -f; }`), a substitution in the body of an
unquoted heredoc. It stops model mistakes, not an attacker.

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

DELIMITER = re.compile(r"""-?[ \t]*(?:\\?([A-Za-z_][A-Za-z0-9_]*)|'([^'\n]+)'|"([^"\n]+)")""")
RESTORE_ALL = {".", ":/", "*", "./"}
PUSH_VALUE = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
DEFAULT_EXEMPT = ["/tmp/", "/var/tmp/", "$TMPDIR/", "${TMPDIR}/"]
DEFAULT_WORKTREES = [".claude/worktrees/"]
CD_WORD = re.compile(r"(?:^|[;&|(\s])(?:cd|pushd)(?:\s|$)")
SUBST = "`gw-subst`"  # what a substitution becomes before tokenizing: a backtick, so no rm exemption takes it
NAMES_CMD = re.compile(r"(?<![\w.-])(?:git|gh|rm)(?![\w-])")
GIT_CHECKED = {"push", "reset", "branch", "clean", "checkout", "switch", "restore"}
DANGEROUS_LONGS = {"--force", "--force-with-lease", "--force-if-includes", "--mirror", "--prune", "--delete", "--hard",
                   "--discard-changes"}
GIT_LONGS = {  # the long options of each checked subcommand (git 2.4x), to expand abbreviations
    "push": {"--all", "--branches", "--prune", "--mirror", "--dry-run", "--porcelain", "--delete", "--tags",
             "--follow-tags", "--signed", "--no-signed", "--atomic", "--no-atomic", "--push-option", "--receive-pack",
             "--exec", "--force-with-lease", "--no-force-with-lease", "--force", "--force-if-includes",
             "--no-force-if-includes", "--repo", "--set-upstream", "--thin", "--no-thin", "--quiet", "--verbose",
             "--progress", "--recurse-submodules", "--no-recurse-submodules", "--verify", "--no-verify", "--ipv4",
             "--ipv6"},
    "reset": {"--mixed", "--soft", "--hard", "--merge", "--keep", "--quiet", "--no-quiet", "--refresh", "--no-refresh",
              "--recurse-submodules", "--no-recurse-submodules", "--pathspec-from-file", "--pathspec-file-nul",
              "--intent-to-add", "--patch", "--unified", "--inter-hunk-context"},
    "branch": {"--delete", "--force", "--move", "--copy", "--list", "--verbose", "--quiet", "--track", "--no-track",
               "--set-upstream-to", "--unset-upstream", "--color", "--no-color", "--remotes", "--all", "--abbrev",
               "--no-abbrev", "--contains", "--no-contains", "--merged", "--no-merged", "--column", "--no-column",
               "--sort", "--points-at", "--format", "--ignore-case", "--omit-empty", "--create-reflog",
               "--edit-description", "--show-current", "--recurse-submodules"},
    "clean": {"--force", "--dry-run", "--quiet", "--interactive", "--exclude"},
    "checkout": {"--quiet", "--progress", "--no-progress", "--force", "--ours", "--theirs", "--track", "--no-track",
                 "--guess", "--no-guess", "--detach", "--orphan", "--ignore-skip-worktree-bits", "--merge", "--conflict",
                 "--patch", "--ignore-other-worktrees", "--overwrite-ignore", "--no-overwrite-ignore",
                 "--recurse-submodules", "--no-recurse-submodules", "--overlay", "--no-overlay", "--pathspec-from-file",
                 "--pathspec-file-nul"},
    "switch": {"--create", "--force-create", "--detach", "--guess", "--no-guess", "--force", "--discard-changes",
               "--merge", "--conflict", "--quiet", "--progress", "--no-progress", "--track", "--no-track", "--orphan",
               "--ignore-other-worktrees", "--recurse-submodules", "--no-recurse-submodules"},
}


def strip_heredocs(command):
    """`command` without the bodies of its heredocs (the lines after `<<EOF` up to the `EOF` line): they are data. A `<<`
    counts only outside quotes and not as `<<<` (a here-string); a delimiter it cannot read leaves the text as it is
    (it is then analysed, which can only make it ask more)."""
    out, pending, quote, i, n = [], [], None, 0, len(command)
    while i < n:
        c = command[i]
        if pending and c == "\n":  # the body: skip lines up to each delimiter
            out.append(c)
            i += 1
            while pending and i <= n:
                j = command.find("\n", i)
                j = n if j < 0 else j
                line = command[i:j]
                if line.strip("\t") == pending[0] or line.strip() == pending[0]:
                    pending.pop(0)
                i = j + 1 if j < n else n + 1
                if pending and j < n:
                    continue
                if not pending:
                    out.append("\n" if j < n else "")
            continue
        if quote:
            out.append(c)
            if c == "\\" and quote == '"' and i + 1 < n:
                out.append(command[i + 1])
                i += 1
            elif c == quote:
                quote = None
        elif c == "\\" and i + 1 < n:
            out.append(c + command[i + 1])
            i += 1
        elif c in "'\"":
            quote = c
            out.append(c)
        elif c == "<" and command.startswith("<<", i) and not command.startswith("<<<", i) \
                and not (i and command[i - 1] == "<"):
            m = DELIMITER.match(command, i + 2)
            if m:
                pending.append(m.group(1) or m.group(2) or m.group(3))
                out.append(command[i:m.end()])
                i = m.end()
                continue
            out.append(c)
        else:
            out.append(c)
        i += 1
    return "".join(out)


def closing_paren(command, j):
    r"""(index after the `)` that closes the `(` before `command[j]`, depth left: 0 when it closed). Quotes inside count
    (`"\")"`, `$'\''`), so a `)` in them does not close it."""
    depth, q, n = 1, None, len(command)
    while j < n and depth:
        d = command[j]
        if q == "'":
            q = None if d == "'" else q
        elif q in ("$'", '"'):
            if d == "\\":
                j += 1
            elif d == q[-1]:
                q = None
        elif d == "\\":
            j += 1
        elif d == "$" and command.startswith("$'", j):
            q = "$'"
            j += 1
        elif d in "'\"":
            q = d
        elif d == "(":
            depth += 1
        elif d == ")":
            depth -= 1
        j += 1
    return j, depth


def substitutions(command):
    r"""(`command` with each outermost substitution replaced by SUBST, [their bodies]): `$(...)`, backticks (their body
    without the `\``, `\\`, `\$` escapes) and, outside double quotes, the process substitutions `<(...)` and `>(...)`.
    Single quotes and `$'...'` hide them (they are text there); double quotes do not. `$((` is arithmetic and is left
    alone; an unclosed one takes the rest of the text as its body (it can only make it ask more)."""
    out, bodies, quote, i, n = [], [], None, 0, len(command)
    while i < n:
        c = command[i]
        if quote == "'":
            out.append(c)
            quote = None if c == "'" else quote
        elif quote == "$'":  # ANSI-C quoting: `\'` does not close it
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(command[i + 1])
                i += 1
            elif c == "'":
                quote = None
        elif c == "\\" and i + 1 < n:
            out.append(command[i:i + 2])
            i += 1
        elif quote is None and command.startswith("$'", i):
            quote = "$'"
            out.append("$'")
            i += 1
        elif c == "'" and quote is None:
            quote = "'"
            out.append(c)
        elif c == '"':
            quote = None if quote == '"' else '"'
            out.append(c)
        elif (command.startswith("$(", i) and not command.startswith("$((", i)) \
                or (quote is None and c in "<>" and command.startswith("(", i + 1)):
            j, depth = closing_paren(command, i + 2)
            bodies.append(command[i + 2:j - 1] if not depth else command[i + 2:])
            out.append(SUBST)
            i = j
            continue
        elif c == "`":
            j = i + 1
            while j < n and command[j] != "`":
                j += 2 if command[j] == "\\" else 1
            bodies.append(re.sub(r"\\([`\\$])", r"\1", command[i + 1:j]))
            out.append(SUBST)
            i = j + 1
            continue
        else:
            out.append(c)
        i += 1
    return "".join(out), bodies


def expand_longs(sub, longs):
    """`longs` (the `--x` words of a `git <sub>` call, without `=value`) plus the full names their abbreviations stand
    for: git takes any prefix of a long option of the subcommand (`--forc` is `--force`). A prefix of several options
    adds all of them (git refuses it as ambiguous; asking costs nothing), except the ones that only make it safer
    (`--dry-run`), which count when they are the only match. A word that is no known option of `sub` adds every
    dangerous name it is a prefix of (the lists may miss one: fail closed)."""
    known = GIT_LONGS.get(sub, set())
    out = list(longs)
    for w in longs:
        if w in known or len(w) < 3:
            continue
        cands = [o for o in known if o.startswith(w)]
        if not cands:
            out += [o for o in DANGEROUS_LONGS if o.startswith(w)]
        elif len(cands) == 1:
            out += cands
        else:
            out += [o for o in cands if o in DANGEROUS_LONGS]
    return out


def unread_substitution(cmd, seg, i, args, line):
    """Why a substitution's output in this simple command can hide a destructive call, or None (`line`: the whole
    command line, substitution bodies included)."""
    if SUBST in seg[i]:
        return "it runs the output of a command substitution as the command" if NAMES_CMD.search(line) else None
    if not any(SUBST in w for w in args):
        return None
    if cmd in guard.SHELLS | {"eval"}:  # `eval "$(...)"`, `bash -c "$(...)"`: the output is run as commands
        return "it runs the output of a command substitution as commands" if NAMES_CMD.search(line) else None
    if cmd == "rm":
        return "an `rm` with a command substitution among its words"
    if cmd == "git":  # not in the value of `-C`/`--git-dir`/... (`git -C "$(git rev-parse ...)" status`)
        k = guard.git_subcommand(args)
        aliases = any(args[m - 1] == "-c" and SUBST in w and (w.startswith(("alias.", SUBST)))
                      for m, w in enumerate(args[:k] if k is not None else args) if m)
        if k is None or aliases or SUBST in args[k] or (args[k] in GIT_CHECKED and any(SUBST in w for w in args[k:])):
            return "a git call with a command substitution among its words"
    return None


def tmpdir_set():
    return os.environ.get("TMPDIR", "") not in ("", "/")


def exempt_target(target, prefixes):
    for p in prefixes:
        if p.startswith(("$TMPDIR", "${TMPDIR}")) and not tmpdir_set():
            continue  # unset, it expands to `/`: `$TMPDIR/home` is `/home`
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
        elif (len(w) > 2 and "--recursive".startswith(w)) or (not w.startswith("--") and re.search(r"[rR]", w)):
            recursive = True
    if not recursive:
        return None
    if targets and all(exempt_target(t, prefixes) for t in targets):
        return None
    return "`rm -r` deletes folders and everything below them, with no way back"


def disposable_worktree(where, worktrees):
    """True when `where` is a linked git worktree (`--git-dir` differs from `--git-common-dir`) whose top folder is under
    one of `worktrees` (relative to the main repository's root). False when git cannot tell: it then asks."""
    if not worktrees:
        return False
    try:
        out = guard.git_run(where, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir",
                            "--show-toplevel").split("\n")
    except Exception:  # noqa: BLE001
        return False
    if len(out) < 3 or not all(out[:3]):
        return False
    gitdir, common, top = (os.path.realpath(x) for x in out[:3])
    if gitdir == common:
        return False
    main = os.path.dirname(common)
    for prefix in worktrees:
        base = os.path.realpath(os.path.join(main, prefix))
        if top.startswith(base.rstrip(os.sep) + os.sep):
            return True
    return False


def git_reason(args, k, base, cfg):
    sub, rest = args[k], args[k + 1:]
    memo = []

    def disposable():  # only the calls it matters for ask git (one run, and not for `git status`)
        if not memo:
            try:
                where = guard.git_cwd(args[:k], base)[0]  # `git -C DIR` runs there
            except guard.Unknown:
                where = None
            memo.append(not cfg["tainted"] and where is not None and disposable_worktree(where, cfg["worktrees"]))
        return memo[0]

    opts = [w for w in rest if w.startswith("-") and w != "--" and w != "-"]
    before_dd = rest[:rest.index("--")] if "--" in rest else rest
    after_dd = rest[rest.index("--") + 1:] if "--" in rest else []
    flags = "".join(w[1:] for w in before_dd if re.fullmatch(r"-[A-Za-z]+", w))
    longs = [w.split("=", 1)[0] for w in before_dd if w.startswith("--")]
    longs = expand_longs(sub, longs)  # git takes any unambiguous prefix: `--forc` is `--force`
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
        pos += after_dd  # `git push -- origin +main`: after `--` every word is a repository or a refspec
        if "--force" in longs or "--force-with-lease" in longs or "--force-if-includes" in longs or "f" in flags \
                or "--mirror" in longs or "--prune" in longs or any(p.startswith("+") for p in pos):
            return "`git push --force` (or --mirror/--prune) rewrites or prunes the remote history and can lose other people's commits"
        if "--delete" in longs or "d" in flags or any(p.startswith(":") and len(p) > 1 for p in pos):
            return "`git push --delete` (or `git push <remote> :<ref>`) deletes a remote branch or tag"
    elif sub == "reset" and "--hard" in longs:
        if not disposable():
            return "`git reset --hard` throws away every uncommitted change"
    elif sub == "branch":
        forced = "--force" in longs or "f" in flags
        if "D" in flags or (("--delete" in longs or "d" in flags) and forced):
            return "`git branch -D` deletes a branch even if it is not merged"
    elif sub == "clean":
        if ("--force" in longs or "f" in flags) and not ("--dry-run" in longs or "n" in flags):
            if not disposable():
                return "`git clean -f` deletes untracked files for good"
    elif sub in ("checkout", "switch", "restore") and guard.git_write_call(args, k):
        paths = rest[rest.index("--") + 1:] if "--" in rest else ([w for w in rest if not w.startswith("-")]
                                                                  if sub == "restore" else rest)
        whole = sub != "switch" and any(p in RESTORE_ALL for p in paths) and not (sub == "checkout" and "-b" in opts)
        forced = sub in ("checkout", "switch") and ("--force" in longs or "--discard-changes" in longs or "f" in flags)
        if (whole or forced) and not disposable():
            if forced and not whole:
                return f"`git {sub} -f` throws away the local changes"
            return f"`git {sub} .` overwrites every modified file of the tree with the committed one"
    return None


def command_reason(command, base, cfg, depth=0):
    if depth == 0:  # a `cd`/`pushd` or GIT_DIR=... may point a later git call at another tree: no worktree exemption
        cfg = dict(cfg, tainted=bool(CD_WORD.search(command) or re.search(guard.GIT_ENV, command)))
    text, bodies = substitutions(strip_heredocs(command))
    for body in bodies:  # what a substitution runs is a command of its own
        if depth >= 3:
            return "command substitutions nested too deep for careful.py to read"
        found = command_reason(body, base, cfg, depth + 1)
        if found:
            return found
    for seg in guard.segments(guard.tokenize(text)):
        i, cmd = guard.command_word(seg)
        if cmd is None:
            continue
        sub = guard.git_subcommand(seg[i + 1:]) if cmd == "git" else None
        if cmd == "git" and not (sub is not None and SUBST in seg[i + 1 + sub]):  # a substituted one: asked below
            seg, problem = guard.expand_git_alias(seg, i, base)
            if problem:
                return f"a git alias it cannot follow ({problem}): `{' '.join(seg[i:])[:120]}`"
        args = [seg[j] for j in guard.arg_indexes(seg, i) if j > i]  # not the wrappers and assignments before the command
        if cmd in guard.SHELLS | {"eval"} and depth < 3:
            if cmd == "eval":
                found = command_reason(" ".join(seg[i + 1:]), base, cfg, depth + 1)  # eval joins its words
                if found:
                    return found
            for j, w in enumerate(seg):
                if j > i and cmd != "eval" and (seg[j - 1] == "-c" or re.match(r"-[a-z]*c$", seg[j - 1])):
                    found = command_reason(w, base, cfg, depth + 1)
                    if found:
                        return found
        reason = None
        if cmd == "rm":
            reason = rm_reason(args, cfg["exempt"])
        elif cmd == "git":
            k = guard.git_subcommand(args)
            reason = git_reason(args, k, base, cfg) if k is not None else None
        shown = " ".join(seg[i:]).replace(SUBST, "$(...)")[:120]
        if reason:
            return f"{reason}: `{shown}`"
        reason = unread_substitution(cmd, seg, i, args, command)
        if reason:
            return f"{reason}, and careful.py cannot read substituted commands (confirm what it runs): `{shown}`"
    return None


def settings():
    """The `modes` keys from .claude/gw.json; a config it cannot read leaves the mode on with the defaults."""
    try:
        mode = config.modes(config.load())
        return {"careful": bool(mode["careful"]), "exempt": list(mode["carefulExempt"]),
                "worktrees": list(mode["carefulWorktrees"])}
    except Exception:  # noqa: BLE001 (any config trouble: keep the safe side)
        return {"careful": True, "exempt": DEFAULT_EXEMPT, "worktrees": DEFAULT_WORKTREES}


def main():
    cfg = settings()
    if not cfg["careful"]:
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
    reason = command_reason(command, os.path.realpath(cwd), cfg)
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
