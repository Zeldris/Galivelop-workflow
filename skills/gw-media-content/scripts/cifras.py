#!/usr/bin/env python3
"""gw-media-content: figures about a project, computed from its repo, for the agent to quote (never to invent).

    python3 cifras.py [--desde REF] [--version-file PATH]

Run it from inside the project's git repository; the root is `git rev-parse --show-toplevel`. Prints one JSON object
on stdout: {"raiz", "hoy", "desde", "cifras": {name: {"valor": ..., "fuente": "<command that gives it>"}}}. A figure
that cannot be computed has "valor": null and a "nota" saying why. Every number in a post comes from here or from a
file:line / commit the post's ficha.md cites.

  --desde REF         count from REF (tag, branch or commit; exclusive) up to HEAD. Default: the last tag reachable
                      from HEAD; with no tag, the whole history (the "desde" field says so).
  --version-file P    file (relative to the root) that holds the project's version; default: the first that exists
                      of package.json, .claude-plugin/plugin.json, pyproject.toml, Cargo.toml, VERSION.

Fails closed (exit 2, message on stderr) outside a git repository, with no commits, or with a REF git does not know.
Python 3.8+.
"""
import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

VERSION_FILES = ("package.json", ".claude-plugin/plugin.json", "pyproject.toml", "Cargo.toml", "VERSION")
TEST_NAME = re.compile(r"(?:^|/)(?:test_[^/]+\.(?:py|sh|mjs|js)|[^/]+_test\.(?:py|go|rb)|[^/]+\.(?:test|spec)\.(?:[cm]?[jt]sx?)"
                       r"|[^/]+Test\.java)$")
TEST_NAME_TEXT = "test_*.py|sh|mjs|js, *_test.py|go|rb, *.test|spec.js|ts|mjs|jsx|tsx, *Test.java"
MAX_SUBJECTS = 20


class Fallo(Exception):
    pass


def git(root, *args, check=True):
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise Fallo(f"git {' '.join(args)} failed: {(proc.stderr or proc.stdout).strip()}")
    return proc.stdout.strip() if proc.returncode == 0 else None


def find_root():
    try:
        proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    except OSError as exc:
        raise Fallo(f"cannot run git ({exc}); install git")
    if proc.returncode != 0 or not proc.stdout.strip():
        raise Fallo("not inside a git repository; run it from the project folder: cd <project> && python3 cifras.py")
    return Path(proc.stdout.strip())


def figure(value, source, note=None):
    out = {"valor": value, "fuente": source}
    if note:
        out["nota"] = note
    return out


def project_version(root, explicit):
    """The project's own version, from the first known file (or --version-file)."""
    candidates = (explicit,) if explicit else VERSION_FILES
    for rel in candidates:
        path = root / rel
        if not path.is_file():
            if explicit:
                raise Fallo(f"--version-file {explicit}: no such file in {root}; pass a path relative to the root")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        found = None
        if path.suffix == ".json":
            try:
                data = json.loads(text)
            except ValueError:
                data = None
            found = data.get("version") if isinstance(data, dict) else None
        elif path.suffix == ".toml":
            m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
            found = m.group(1) if m else None
        else:
            found = text.strip().splitlines()[0].strip() if text.strip() else None
        if found:
            return figure(str(found), f"read {rel}")
        if explicit:
            raise Fallo(f"--version-file {explicit}: no version found in it; point to the file that holds it")
    return figure(None, "package.json, .claude-plugin/plugin.json, pyproject.toml, Cargo.toml, VERSION",
                  "no known version file; pass --version-file <path>")


def config_reader(root):
    """The workflow's config reader, if the project has one (installed copy first, then this repo's own)."""
    for rel in (".claude/gw/scripts/config.py", "scripts/config.py"):
        if (root / rel).is_file() and (root / ".claude" / "gw.json").is_file():
            return root / rel
    return None


def config_value(root, reader, key):
    proc = subprocess.run([sys.executable, str(reader), "--root", str(root), "get", key],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None, (proc.stderr.strip().splitlines() or ["the config reader failed"])[0]
    return proc.stdout.strip() or None, None


def changelog_headings(root):
    path = root / "CHANGELOG.md"
    if not path.is_file():
        return figure(None, "CHANGELOG.md", "no CHANGELOG.md at the root")
    section, headings = None, []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^(#{2,6})\s+(.*\S)\s*$", line)
        if not m:
            continue
        if len(m.group(1)) == 2:
            if section is not None:
                break
            section = m.group(2)
        elif section is not None:
            headings.append(m.group(2))
    if section is None:
        return figure(None, "CHANGELOG.md", "CHANGELOG.md has no '## ' section")
    return figure({"seccion": section, "encabezados": headings},
                  "first '## ' section of CHANGELOG.md and its sub-headings")


def compute(root, desde, version_file):
    git(root, "rev-parse", "--verify", "-q", "HEAD^{commit}", check=False) or _no_commits()
    cifras = {}
    cifras["version_proyecto"] = project_version(root, version_file)
    reader = config_reader(root)
    if reader:
        cmd = f"python3 {reader.relative_to(root).as_posix()} get log"
        log, error = config_value(root, reader, "log")
        cifras["bitacora"] = figure(log, cmd, None if log else error or "gw.json has no 'log'")
    tag = git(root, "describe", "--tags", "--abbrev=0", check=False)
    cifras["ultima_etiqueta"] = figure(tag, "git describe --tags --abbrev=0", None if tag else "the repo has no tags")
    if desde:
        if not git(root, "rev-parse", "--verify", "-q", f"{desde}^{{commit}}", check=False):
            raise Fallo(f"--desde {desde}: git does not know that ref; use a tag, branch or commit "
                        f"(git tag --list, git log --oneline)")
        base, base_text = desde, f"--desde {desde}"
    elif tag:
        base, base_text = tag, f"last tag {tag}"
    else:
        base, base_text = None, "first commit (the repo has no tags)"
    rng = f"{base}..HEAD" if base else "HEAD"
    n = int(git(root, "rev-list", "--count", rng))
    cifras["commits_desde"] = figure(n, f"git rev-list --count {rng}")
    plain = int(git(root, "rev-list", "--count", "--no-merges", rng))
    cifras["commits_sin_merges"] = figure(plain, f"git rev-list --count --no-merges {rng}")
    subjects = git(root, "log", "--no-merges", f"--max-count={MAX_SUBJECTS}", "--format=%h %s", rng).splitlines()
    cifras["commits_asuntos"] = figure(subjects, f"git log --no-merges --max-count={MAX_SUBJECTS} --format='%h %s' {rng}",
                                       f"the newest {MAX_SUBJECTS} at most" if plain > MAX_SUBJECTS else None)
    dates = sorted(git(root, "log", "--format=%as", rng).split())
    cifras["rango_fechas"] = figure({"primero": dates[0], "ultimo": dates[-1]} if dates else None,
                                    f"git log --format=%as {rng}", None if dates else "no commits in the range")
    if base:
        names = [x for x in git(root, "diff", "--name-only", base, "HEAD").splitlines() if x]
        add = rem = 0
        for line in git(root, "diff", "--numstat", base, "HEAD").splitlines():
            a, r, _ = (line.split("\t", 2) + ["", ""])[:3]
            add += int(a) if a.isdigit() else 0
            rem += int(r) if r.isdigit() else 0
        cifras["archivos_cambiados"] = figure({"archivos": len(names), "lineas_anadidas": add, "lineas_borradas": rem},
                                              f"git diff --numstat {base} HEAD")
    else:
        files = git(root, "ls-files").splitlines()
        cifras["archivos_cambiados"] = figure({"archivos": len(files)}, "git ls-files | wc -l",
                                              "no base ref: every tracked file counts as new")
    cifras["changelog_ultima_seccion"] = changelog_headings(root)
    tests = [f for f in git(root, "ls-files").splitlines() if TEST_NAME.search(f)]
    cifras["archivos_de_test"] = figure(len(tests), f"git ls-files, names matching {TEST_NAME_TEXT}")
    return base_text, cifras


def _no_commits():
    raise Fallo("the repository has no commits yet; make a commit first")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cifras.py", description="Figures from the repo for gw-media-content posts.")
    ap.add_argument("--desde", metavar="REF", help="count from this tag/branch/commit (default: the last tag)")
    ap.add_argument("--version-file", metavar="PATH", help="file with the project's version, relative to the root")
    args = ap.parse_args(argv)
    try:
        root = find_root()
        base_text, cifras = compute(root, args.desde, args.version_file)
    except Fallo as exc:
        print(f"cifras.py: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"raiz": str(root), "hoy": datetime.date.today().isoformat(), "desde": base_text,
                      "cifras": cifras}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
