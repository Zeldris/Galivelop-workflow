#!/usr/bin/env python3
# galivelop-workflow v0.6.0
"""The test files a change calls for, from `testMap` in .claude/gw.json (E21).

  python3 tests-for.py FILE [...]          # the test files, one per line (repo-relative, sorted, no repeats)
  python3 tests-for.py --diff REV [FILE...] # also every file that differs from REV (commits and working tree)
  python3 tests-for.py --run ...           # run them with testMap.command ({files} -> the test files, shell-quoted)

Every rule of `testMap.rules` whose `paths` regex is found in a changed path (repo-relative, `/`) and, when it has
`contains`, whose regex is found in that file's text on disk, adds its `tests`: `{name}` is the rule's named group as
matched, `{name:id}` the same with every character that is not a letter, digit or `_` turned into `_`
(`scripts/config-guard.py` -> `tests/test_config_guard.py`), `{path}` the changed path. A test file that does not
exist is left out, so a broad rule costs nothing. A changed file may be absolute or relative to the current directory;
one outside the project is an error. Nothing matched: no output, exit 0 (with --run, a note and exit 0).

Who uses it: the brief of gw-orchestrate-dealer (a subagent runs the tests of what it touches instead of a list
written by hand) and anyone before a commit. It is not a hook: the push runs `check` and `relatedTests`. Project root
and config: config.find_root and config.load. Fails closed: no config, an invalid one, a placeholder the rule has no
group for, or --run with an empty `testMap.command` -> exit 2 with what fixes it. With --run the exit code is the
command's. Python 3.8+ standard library only.
"""
import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, str(HERE))
import config  # noqa: E402

PLACEHOLDER = re.compile(r"\{(\w+)(?::(id))?\}")


class MapError(Exception):
    pass


def expand(template, match, path):
    """`template` with its placeholders filled from `match` (named groups) and `path`; MapError on an unknown one."""
    groups = match.groupdict()

    def fill(m):
        name, ident = m.group(1), m.group(2)
        if name == "path":
            value = path
        elif name in groups:
            value = groups[name] or ""
        else:
            raise MapError(f"{{{name}}} in {template!r} names no group of its rule's `paths`; add (?P<{name}>...) to "
                           "it or fix the placeholder in testMap of .claude/gw.json")
        return re.sub(r"[^A-Za-z0-9_]", "_", value) if ident else value

    return PLACEHOLDER.sub(fill, template)


def text_of(root, rel):
    try:
        return (root / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def tests_for(root, rules, files):
    """The existing test files (repo-relative, sorted) the rules give for `files` (repo-relative paths)."""
    found = set()
    for rule in rules:
        paths = re.compile(rule["paths"])
        contains = re.compile(rule["contains"]) if rule.get("contains") else None
        for rel in files:
            match = paths.search(rel)
            if not match:
                continue
            if contains is not None:
                text = text_of(root, rel)
                if text is None or not contains.search(text):
                    continue
            for template in rule["tests"]:
                test = expand(template, match, rel)
                if (root / test).is_file():
                    found.add(test)
    return sorted(found)


def relative(root, name):
    """`name` (absolute or relative to the current directory) as a repo-relative path with `/`."""
    full = Path(os.path.abspath(name))
    for candidate in (full, Path(os.path.realpath(full.parent)) / full.name):  # a symlinked path to the root
        try:
            return candidate.relative_to(root).as_posix()
        except ValueError:
            pass
    raise MapError(f"{name} is outside the project {root}; pass files of this project")


def diff_files(root, rev):
    r = subprocess.run(["git", "-C", str(root), "diff", "--name-only", "--no-renames", rev, "--"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise MapError(f"cannot diff against {rev!r} ({r.stderr.strip()}); fetch it first: git fetch origin")
    untracked = subprocess.run(["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"],
                               capture_output=True, text=True)
    return [f for f in (r.stdout + untracked.stdout).splitlines() if f]


def main(argv=None):
    parser = argparse.ArgumentParser(description="The test files a change calls for (testMap in .claude/gw.json).")
    parser.add_argument("files", nargs="*", help="changed files (absolute or relative to the current directory)")
    parser.add_argument("--diff", metavar="REV", help="add every file that differs from REV, plus untracked ones")
    parser.add_argument("--run", action="store_true", help="run the test files with testMap.command")
    parser.add_argument("--root", help="project root (default: config.find_root)")
    args = parser.parse_args(argv)
    try:
        root = Path(config.find_root(args.root)).resolve()
        cfg = config.load(root)
    except config.ConfigError as exc:
        print(f"tests-for: {exc}", file=sys.stderr)
        return 2
    mapping = config.test_map(cfg)
    try:
        files = [relative(root, f) for f in args.files]
        if args.diff:
            files += diff_files(root, args.diff)
        tests = tests_for(root, mapping["rules"], sorted(set(files)))
    except MapError as exc:
        print(f"tests-for: {exc}", file=sys.stderr)
        return 2
    if not mapping["rules"]:
        print("tests-for: testMap.rules is empty, so no change calls for a test; add rules to .claude/gw.json "
              "(see docs/en/config.md)", file=sys.stderr)
    if not args.run:
        for test in tests:
            print(test)
        return 0
    if not mapping["command"]:
        print("tests-for: testMap.command is empty; set it in .claude/gw.json "
              "(e.g. \"PYTHONPATH=tests python3 -B -m unittest {files}\")", file=sys.stderr)
        return 2
    if not tests:
        print("tests-for: no test file for these changes; nothing to run")
        return 0
    command = mapping["command"].replace("{files}", " ".join(shlex.quote(t) for t in tests))
    print(f"tests-for: {command}", flush=True)
    return subprocess.run(["bash", "-c", command], cwd=str(root)).returncode


if __name__ == "__main__":
    sys.exit(main())
