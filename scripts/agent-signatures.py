#!/usr/bin/env python3
# galivelop-workflow v0.4.3
"""PreToolUse hook: with `agentSignatures: false`, block the text an agent publishes on GitHub when it carries a signature (D21).

The commit-msg hook only covers commit messages; this covers the title and body of what goes to GitHub:

  - the GitHub MCP tools that publish text: create_pull_request, update_pull_request, add_issue_comment,
    update_issue_comment, issue_write, add_reply_to_pull_request_comment, add_comment_to_pending_review and
    pull_request_review_write (their `title` and `body`; create_or_update_file and push_files write files, not text,
    and are not touched);
  - Bash commands `gh pr create|edit|comment` and `gh issue create|comment` (also `gh pr review`): the values of
    --title/-t and --body/-b (in `--opt value` and `--opt=value` form, quotes and heredocs included) and the content of
    the file given with --body-file/-F. A command that cannot be split into words is scanned whole.

Signatures (the same set as the commit-msg hook, case-insensitive, plus the footers of a PR): a `Co-Authored-By:` with
noreply@anthropic.com or naming Claude Code/Opus/Sonnet/Haiku/Fable, a `Claude-Session:` line, a line that starts
(after any emoji) with "Generated with/by [Claude Code", and a claude.ai/code/session_ link anywhere.

Without `agentSignatures: false` in .claude/gw.json (absent or true) it does nothing. Output: nothing and exit 0 to
let the tool run; exit 2 with the reason on stderr (in English, ending with the fix) to block it. A tool that is not
one of the above is never blocked, whatever its input. Fails closed where it cannot know: stdin that is not a JSON
object, or an unreadable config or --body-file on an affected call, block with the reason and the fix. The project root
is found by config.find_root (the script's own repo, never the current directory first). Python 3.8+, stdlib only.
"""
import json
import os
import re
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import config  # noqa: E402

GITHUB_TOOLS = frozenset(("create_pull_request", "update_pull_request", "add_issue_comment", "update_issue_comment",
                          "issue_write", "add_reply_to_pull_request_comment", "add_comment_to_pending_review",
                          "pull_request_review_write"))
TEXT_FIELDS = ("title", "body")
GH_COMMAND = re.compile(r"(?:^|[\s;&|(`{])gh\s+(?:pr\s+(?:create|edit|comment|review)|issue\s+(?:create|comment))\b")
TITLE_BODY = {"--title": "text", "-t": "text", "--body": "text", "-b": "text", "--body-file": "file", "-F": "file"}
# Mirrors templates/githooks/commit-msg (grep -iE there, re.I | re.M here); the last two are the footers of a PR.
SIGNATURES = tuple(re.compile(p, re.I | re.M) for p in (
    r"^[ \t]*co-authored-by:.*noreply@anthropic\.com",
    r"^[ \t]*co-authored-by:[ \t]*claude (code|opus|sonnet|haiku|fable)",
    r"^[ \t]*claude-session:",
    r"^[\W_]*generated (with|by) \[?claude code",
    r"^[ \t]*<?https?://claude\.ai/code/session",
    r"claude\.ai/code/session_",
))
STDIN_LIMIT = 8 * 1024 * 1024


class Block(Exception):
    pass


def find_signature(text):
    """The first line of `text` that carries a signature, or None."""
    for pattern in SIGNATURES:
        m = pattern.search(text)
        if m:
            return text[m.start():].strip().split("\n", 1)[0].strip()[:200]
    return None


def github_tool(name):
    """The bare tool name when `name` is one of the GitHub MCP tools that publish text, else None."""
    if not (name.startswith("mcp__") and "github" in name.split("__")[1].lower()):
        return None
    bare = name.rsplit("__", 1)[-1]
    return bare if bare in GITHUB_TOOLS else None


def read_file(path, cwd):
    full = path if os.path.isabs(path) else os.path.join(cwd, path)
    try:
        with open(full, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError as exc:
        raise Block(f"cannot read the file {path} given to gh ({exc.strerror or exc}), so its signatures cannot be checked; "
                    f"write the body to an existing file, or pass it with --body, and run the command again")


def gh_texts(command, cwd):
    """[(where, text)] to scan in a Bash command that publishes with gh; the whole command when it cannot be split."""
    if not GH_COMMAND.search(command):
        return []
    try:
        words = shlex.split(command)
    except ValueError:
        return [("the command", command)]
    texts = []
    for i, word in enumerate(words):
        option, eq, value = word.partition("=")
        if not eq or not option.startswith("--"):
            option, value = word, None
        kind = TITLE_BODY.get(option) if option.startswith("-") else None
        if kind is None:
            continue
        if value is None:
            value = words[i + 1] if i + 1 < len(words) else ""
        texts.append((option, value if kind == "text" else read_file(value, cwd)))
    return texts


def texts_of(event):
    """[(where, text)] of what the tool call would publish; [] for a tool that is not affected."""
    name = event.get("tool_name")
    if not isinstance(name, str):
        return []
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    if name == "Bash":
        command = tool_input.get("command")
        cwd = event.get("cwd") if isinstance(event.get("cwd"), str) else os.getcwd()
        return gh_texts(command, cwd) if isinstance(command, str) else []
    if github_tool(name) is None:
        return []
    return [(field, tool_input[field]) for field in TEXT_FIELDS if isinstance(tool_input.get(field), str)]


def decide(event):
    texts = texts_of(event)
    if not texts:
        return
    try:
        conf = config.load(config.find_root())
    except config.ConfigError as exc:
        raise Block(f"cannot read .claude/gw.json ({exc}), so agentSignatures cannot be checked; fix it: "
                    f"python3 {os.path.join(HERE, 'config.py')} validate")
    if conf.get("agentSignatures", True) is not False:
        return
    for where, text in texts:
        line = find_signature(text)
        if line:
            raise Block(f"the {where} carries an agent signature, which this project forbids "
                        f"(agentSignatures: false in .claude/gw.json): {line}\n"
                        f"Remove that line (the footer or link of the session) from the text and run the call again; "
                        f"if the project does accept signatures: set \"agentSignatures\": true in .claude/gw.json")


def main():
    try:
        raw = sys.stdin.read(STDIN_LIMIT) if sys.stdin is not None and not sys.stdin.isatty() else ""
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise ValueError("not an object")
    except (OSError, ValueError) as exc:
        print(f"agent-signatures: the hook event on stdin cannot be read ({exc}), so the tool call is blocked; "
              f"run the call again, and if it keeps failing check the hook: python3 {os.path.abspath(__file__)} < event.json",
              file=sys.stderr)
        return 2
    try:
        decide(event)
    except Block as exc:
        print(f"agent-signatures: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
