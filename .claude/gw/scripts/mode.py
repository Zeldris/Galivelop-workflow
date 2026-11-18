#!/usr/bin/env python3
# galivelop-workflow v0.7.1
"""One switch for the workflow's modes: the `modes` section of .claude/gw.json (C6, C7).

  python3 mode.py list                 # each mode with its value and what it does; then the list settings, read-only
  python3 mode.py line                 # one line for SessionStart: "Modes: careful on, questions restrictive"
  python3 mode.py set MODE on|off      # write the mode into .claude/gw.json (also true|false|1|0|yes|no)

The modes it knows are the boolean keys of `modes` (careful, questions); the list keys (carefulExempt,
carefulWorktrees) are shown by `list` and edited by hand. `set` rewrites .claude/gw.json (two-space JSON, key order
kept, a missing `modes` section created) and validates it, putting the old text back if the result is invalid;
config-guard.py treats a gw.json edit by hand the same way. Project root and config: config.find_root and
config.load. Fails closed: no config, an invalid one or an unknown mode -> exit 2 with the command that fixes it.
Python 3.8+ standard library only.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # no __pycache__ in the project's .claude/gw/scripts
sys.path.insert(0, str(HERE))
import config  # noqa: E402

# mode -> (label when true, label when false, meaning)
MODES = {
    "careful": ("on", "off", "careful.py asks before a destructive command (rm -r, git push --force, git reset --hard)"),
    "questions": ("restrictive", "guide", "questions-guard.py (C4, C5): restrictive = the guard blocks, guide = it only advises"),
}
TRUE_WORDS = ("on", "true", "1", "yes")
FALSE_WORDS = ("off", "false", "0", "no")


def label(mode, value):
    """How a mode's value reads: `on`/`off`, or its own words (questions: restrictive/guide)."""
    on, off, _ = MODES.get(mode, ("on", "off", ""))
    return on if value else off


def boolean_modes(conf):
    """The boolean keys of the loaded config's `modes`, in config order, with their values."""
    return {k: v for k, v in config.modes(conf).items() if isinstance(v, bool)}


def write(root, mode, value):
    """Set modes.<mode> to `value` in root/.claude/gw.json and validate it; on an invalid result the old text is put
    back and ConfigError raised."""
    path = Path(root) / config.CONFIG_REL
    old = path.read_text(encoding="utf-8")
    raw = json.loads(old)
    section = raw.get("modes") if isinstance(raw.get("modes"), dict) else {}
    section[mode] = value
    raw["modes"] = section
    path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        config.load(root)
    except config.ConfigError:
        path.write_text(old, encoding="utf-8")
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", help="project path (default: config.find_root)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    sub.add_parser("line")
    setter = sub.add_parser("set")
    setter.add_argument("mode")
    setter.add_argument("value")
    args = parser.parse_args(argv)
    name = Path(__file__).name
    try:
        conf = config.load(args.root)
    except config.ConfigError as exc:
        print(f"gw mode: {exc}; fix .claude/gw.json, then: python3 {name} list", file=sys.stderr)
        return 2
    bools = boolean_modes(conf)
    if args.command == "line":
        print("Modes: " + ", ".join(f"{k} {label(k, v)}" for k, v in bools.items()))
        return 0
    if args.command == "list":
        for k, v in bools.items():
            print(f"{k}: {label(k, v)} ({'true' if v else 'false'}) - {MODES.get(k, ('', '', 'no description'))[2]}")
        for k, v in config.modes(conf).items():
            if isinstance(v, list):
                print(f"{k}: {json.dumps(v)} - list setting, read-only here; edit modes.{k} in .claude/gw.json")
        return 0
    if args.mode not in bools:
        print(f"gw mode: unknown mode `{args.mode}` (known: {', '.join(bools) or 'none'}); run: python3 {name} list",
              file=sys.stderr)
        return 2
    word = args.value.strip().lower()
    if word not in TRUE_WORDS + FALSE_WORDS:
        print(f"gw mode: `{args.value}` is not on or off; run: python3 {name} set {args.mode} on|off", file=sys.stderr)
        return 2
    value = word in TRUE_WORDS
    try:
        write(conf["_root"], args.mode, value)
    except (OSError, ValueError, config.ConfigError) as exc:
        print(f"gw mode: .claude/gw.json was not changed ({exc}); fix it, then: python3 config.py validate",
              file=sys.stderr)
        return 2
    print(f"modes.{args.mode}: {label(args.mode, value)} ({'true' if value else 'false'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
