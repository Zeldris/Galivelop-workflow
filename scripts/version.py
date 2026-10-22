#!/usr/bin/env python3
# galivelop-workflow v0.1.0
"""The workflow's version markers: check them or bump them all at once (workflow repo only).

The version lives in .claude-plugin/plugin.json; copies of it mark every workflow-owned file so aplicar.py and
gw-update can tell versions apart. A marker is only one of these, nothing else (prose and code examples are never
read nor rewritten):
  - a `galivelop-workflow vX.Y.Z` header within the first 5 lines of a file (scripts, templates, the schema's
    "$comment"): the rule of header_version() in aplicar.py, imported from there;
  - `metadata.version` inside the frontmatter of a SKILL.md;
  - `"version"` in templates/gw.json.
.claude/gw.json is this repo's installed copy: only aplicar.py writes it.

  python3 scripts/version.py            # list files whose marker differs from plugin.json; exit 1 if any
  python3 scripts/version.py 0.2.0      # set plugin.json and every marker to 0.2.0; add a CHANGELOG entry
  python3 scripts/version.py <current>  # re-sync stale markers to plugin.json's version
Then: python3 scripts/aplicar.py .  (refresh this repo's copy) and fill in the CHANGELOG entry.
Files are read and written as strict UTF-8 keeping their line endings; a non-UTF-8 file with a marker is reported
and left alone.
"""
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from aplicar import HEADER, header_version  # noqa: E402

PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
TEMPLATE_GW = ROOT / "templates" / "gw.json"
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
JSON_VERSION = re.compile(r'("version"\s*:\s*")([^"]*)(")')
SCOPES = ("scripts", "skills", "templates", "schema")
HEAD_LINES = 5  # same as header_version()


def marked_files():
    for scope in SCOPES:
        for path in sorted((ROOT / scope).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path != TEMPLATE_GW:
                yield path


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def header_span(text):
    """(start, end) of the header version in the first lines, or None (same match as header_version())."""
    head = "".join(text.splitlines(keepends=True)[:HEAD_LINES])
    m = HEADER.search(head)
    return m.span(1) if m else None


def skill_span(text):
    """(start, end) of metadata.version's value inside a SKILL.md frontmatter, or None."""
    fm = re.match(r"---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not fm:
        return None
    pos, inside = fm.start(1), False
    for line in fm.group(1).splitlines(keepends=True):
        bare = line.rstrip("\r\n")
        if re.match(r"metadata:\s*$", bare):
            inside = True
        elif inside:
            sub = re.match(r"(\s+)([A-Za-z_-]+):\s*([\"']?)([^\"'\s]*)", bare)
            if not sub:
                break
            if sub.group(2) == "version":
                return pos + sub.start(4), pos + sub.end(4)
        pos += len(line)
    return None


def spans(path, text):
    found = [s for s in (header_span(text),) if s]
    if path.name == "SKILL.md":
        found += [s for s in (skill_span(text),) if s]
    return found


def scan(version):
    """[(path, text, stale spans)] for files with a marker other than version, and the non-UTF-8 ones with a marker."""
    stale, unreadable = [], []
    for path in marked_files():
        try:
            text = read(path)
        except UnicodeDecodeError:
            if header_version(path.read_bytes()):
                unreadable.append(path)
            continue
        bad = [s for s in spans(path, text) if text[s[0]:s[1]] != version]
        if bad:
            stale.append((path, text, bad))
    return stale, unreadable


def json_version(path):
    m = JSON_VERSION.search(read(path))
    return m.group(2) if m else None


def check(version):
    stale, unreadable = scan(version)
    lines = [f"{p.relative_to(ROOT)}: {', '.join(sorted({t[a:b] for a, b in s}))}" for p, t, s in stale]
    lines += [f"{p.relative_to(ROOT)}: not UTF-8, its marker cannot be checked" for p in unreadable]
    if json_version(TEMPLATE_GW) != version:
        lines.append(f"templates/gw.json: version {json_version(TEMPLATE_GW)}")
    return lines


def set_json_version(path, new):
    text = read(path)
    out = JSON_VERSION.sub(lambda m: m.group(1) + new + m.group(3), text, count=1)
    if out != text:
        write(path, out)
        return True
    return False


def sync(new):
    """One pass: every marker that is not `new` becomes `new`. Returns (changed, skipped non-UTF-8 files)."""
    stale, unreadable = scan(new)
    changed = []
    for path, text, found in stale:
        for a, b in sorted(found, reverse=True):
            text = text[:a] + new + text[b:]
        write(path, text)
        changed.append(path)
    for path in (TEMPLATE_GW, PLUGIN):
        if set_json_version(path, new):
            changed.append(path)
    return changed, unreadable


def add_changelog_entry(new):
    log = ROOT / "CHANGELOG.md"
    text = read(log)
    if f"## [{new}]" in text:
        return
    nl = "\r\n" if "\r\n" in text else "\n"
    entry = nl.join([f"## [{new}] - Unreleased", "", "### ES", "", "- (por completar)", "", "### EN", "",
                     "- (to be filled in)", "", ""])
    write(log, re.sub(r"^## \[", lambda m: entry + "## [", text, count=1, flags=re.M))


def main(argv):
    current = json.loads(read(PLUGIN))["version"]
    if not argv:
        stale = check(current)
        for line in stale:
            print(f"stale marker: {line}")
        if stale:
            print(f"markers differ from plugin.json ({current}); fix them: python3 scripts/version.py {current}")
            return 1
        print(f"all markers at {current}")
        return 0
    new = argv[0]
    if not SEMVER.match(new):
        print(f"{new!r} is not SemVer (X.Y.Z); retry: python3 scripts/version.py 0.2.0", file=sys.stderr)
        return 2
    _, skipped = sync(new)
    if new != current:
        add_changelog_entry(new)
    for path in skipped:
        print(f"skipped {path.relative_to(ROOT)}: not UTF-8; convert it and retry: python3 scripts/version.py {new}",
              file=sys.stderr)
    print(f"version {current} -> {new}; now: python3 scripts/aplicar.py . && fill in the CHANGELOG entry")
    return 1 if skipped else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
