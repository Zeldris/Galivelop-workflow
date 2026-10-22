#!/usr/bin/env python3
# galivelop-workflow v0.1.0
"""The workflow's version markers: check them or bump them all at once (workflow repo only).

The version lives in .claude-plugin/plugin.json; copies of it mark every workflow-owned file so aplicar.py and
gw-update can tell versions apart: `galivelop-workflow vX.Y.Z` headers (scripts, templates, schema) and
`metadata.version` in skills. This keeps them equal.

  python3 scripts/version.py            # list files whose marker differs from plugin.json; exit 1 if any
  python3 scripts/version.py 0.2.0      # bump plugin.json, every marker and templates/gw.json; add a CHANGELOG entry
Then: python3 scripts/aplicar.py .  (refresh this repo's copy) and fill in the CHANGELOG entry.
"""
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
HEADER = re.compile(r"(galivelop-workflow v)(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)")
SKILL = re.compile(r'^(\s+version:\s*")([^"]+)(")', re.M)
SCOPES = ("scripts", "skills", "templates", "schema")


def marked_files():
    for scope in SCOPES:
        for path in sorted((ROOT / scope).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                yield path


def markers(text, is_skill):
    found = [m.group(2) for m in HEADER.finditer(text)]
    if is_skill:
        found += [m.group(2) for m in SKILL.finditer(text)]
    return found


def check(version):
    stale = []
    for path in marked_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        bad = [v for v in markers(text, path.name == "SKILL.md") if v != version]
        if bad:
            stale.append(f"{path.relative_to(ROOT)}: {', '.join(sorted(set(bad)))}")
    gw = json.loads((ROOT / "templates" / "gw.json").read_text(encoding="utf-8"))
    if gw.get("version") != version:
        stale.append(f"templates/gw.json: version {gw.get('version')}")
    return stale


def bump(old, new):
    changed = []
    for path in marked_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        out = HEADER.sub(lambda m: m.group(1) + new if m.group(2) == old else m.group(0), text)
        if path.name == "SKILL.md":
            out = SKILL.sub(lambda m: m.group(1) + new + m.group(3) if m.group(2) == old else m.group(0), out)
        if out != text:
            path.write_text(out, encoding="utf-8")
            changed.append(path)
    for rel in ("templates/gw.json", ".claude/gw.json", ".claude-plugin/plugin.json"):
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        out = re.sub(r'("version":\s*")' + re.escape(old) + '"', r"\g<1>" + new + '"', text, count=1)
        if out != text:
            path.write_text(out, encoding="utf-8")
            changed.append(path)
    log = ROOT / "CHANGELOG.md"
    text = log.read_text(encoding="utf-8")
    if f"## [{new}]" not in text:
        entry = f"## [{new}] - Unreleased\n\n### ES\n\n- (por completar)\n\n### EN\n\n- (to be filled in)\n\n"
        text = re.sub(r"^## \[", entry + "## [", text, count=1, flags=re.M)
        log.write_text(text, encoding="utf-8")
        changed.append(log)
    return changed


def main(argv):
    current = json.loads(PLUGIN.read_text(encoding="utf-8"))["version"]
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
    old = current
    if new == old:  # re-sync stale markers to the current version
        stale_versions = set()
        for path in marked_files():
            stale_versions |= set(markers(path.read_text(encoding="utf-8", errors="replace"), path.name == "SKILL.md"))
        for v in stale_versions - {new}:
            bump(v, new)
    else:
        bump(old, new)
    print(f"version {old} -> {new}; now: python3 scripts/aplicar.py . && fill in the CHANGELOG entry")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
