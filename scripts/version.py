#!/usr/bin/env python3
# galivelop-workflow v0.5.2
"""The workflow's version markers: check them or bump them all at once (workflow repo only).

The version lives in .claude-plugin/plugin.json; copies of it mark every workflow-owned file so apply.py and
gw-update can tell versions apart. A marker is only one of these, nothing else (prose and code examples are never
read nor rewritten):
  - a `galivelop-workflow vX.Y.Z` header within the first 5 lines of a file (scripts, templates, the schema's
    "$comment"): the rule of header_version() in apply.py, imported from there;
  - `metadata.version` inside the frontmatter of a SKILL.md: skill_version_span() in apply.py, imported too;
  - the top-level `"version"` of templates/gw.json (and of plugin.json, the source).
Every file under scripts/, every SKILL.md and every file under templates/ and schema/ must carry its marker; the
check flags one that lacks it (exceptions, with the reason, in UNMARKED).
.claude/gw.json is this repo's installed copy: only apply.py writes it.

  python3 scripts/version.py            # list files whose marker differs from plugin.json; exit 1 if any
  python3 scripts/version.py 0.2.0      # set plugin.json and every marker to 0.2.0; add a CHANGELOG entry
  python3 scripts/version.py <current>  # re-sync stale markers to plugin.json's version
  python3 scripts/version.py --suggest  # the bump the commits since the last vX.Y.Z tag ask for (D11); only suggests
                                        # (exit 0); --release prints the same suggestion as a warning
  python3 scripts/version.py --release  # the check, and: copyable files (scripts/, skills/, templates/, schema/,
                                        # LICENSE-mattpocock-skills)
                                        # changed since the last vX.Y.Z tag reachable from HEAD need a
                                        # new version (the pre-push check of a push to main), and a new
                                        # version needs a harvest since that tag: a <proposalsDir>/*.md
                                        # added after it whose first line is "# Harvest …" (skill gw-harvest)
                                        # and a dated, filled-in CHANGELOG entry (## [X.Y.Z] - YYYY-MM-DD)
                                        # whose backticked repo paths all exist in HEAD (placeholders skipped)
Then: python3 scripts/apply.py .  (refresh this repo's copy) and fill in the CHANGELOG entry.
Files are read and written as strict UTF-8 keeping their line endings; a non-UTF-8 file with a marker is reported
and left alone.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402  (the only reader of .claude/gw.json)
from apply import HEADER, SKILL_LICENSE, header_version, skill_version_span  # noqa: E402

PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
TEMPLATE_GW = ROOT / "templates" / "gw.json"
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
TOP_VERSION = re.compile(r'^(  "version"\s*:\s*")([^"]*)(")', re.M)  # a top-level key: two-space indent
SCOPES = ("scripts", "skills", "templates", "schema")
HEAD_LINES = 5  # same as header_version()
UNMARKED = {  # workflow files that carry no header marker, and why
    "templates/gw.json": "JSON; its marker is the top-level \"version\", checked on its own",
    "templates/claude/settings.json": "JSON merged key by key into the project's settings, never owned",
}


class VersionError(Exception):
    """A file the bump needs is not shaped as expected; the message ends with the command that fixes it."""


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


def spans(path, text):
    found = [s for s in (header_span(text),) if s]
    if path.name == "SKILL.md":
        found += [s for s in (skill_version_span(text),) if s]
    return found


def needs_marker(path):
    """True when a workflow-owned file must carry a marker: SKILL.md (metadata.version) or a header elsewhere."""
    rel = path.relative_to(ROOT)
    if rel.as_posix() in UNMARKED:
        return False
    return rel.parts[0] != "skills" or path.name == "SKILL.md"


def own_marker(path, text):
    return skill_version_span(text) if path.name == "SKILL.md" else header_span(text)


def scan(version):
    """Files with a marker other than version [(path, text, stale spans)], the non-UTF-8 ones with a marker, and the
    ones that must carry a marker and lack it."""
    stale, unreadable, missing = [], [], []
    for path in marked_files():
        try:
            text = read(path)
        except UnicodeDecodeError:
            if header_version(path.read_bytes()):
                unreadable.append(path)
            elif needs_marker(path):
                missing.append(path)
            continue
        if needs_marker(path) and own_marker(path, text) is None:
            missing.append(path)
        bad = [s for s in spans(path, text) if text[s[0]:s[1]] != version]
        if bad:
            stale.append((path, text, bad))
    return stale, unreadable, missing


def top_version(path):
    """The top-level "version" of a JSON file, or None when it has none (or is not a JSON object)."""
    data = json.loads(read(path))
    return data.get("version") if isinstance(data, dict) else None


def check(version):
    stale, unreadable, missing = scan(version)
    lines = [f"stale marker: {p.relative_to(ROOT)}: {', '.join(sorted({t[a:b] for a, b in s}))}"
             for p, t, s in stale]
    lines += [f"stale marker: {p.relative_to(ROOT)}: not UTF-8, its marker cannot be checked" for p in unreadable]
    lines += [f"missing marker: {p.relative_to(ROOT)}: add "
              + ("metadata.version to its frontmatter" if p.name == "SKILL.md"
                 else f"a `galivelop-workflow v{version}` comment in its first {HEAD_LINES} lines")
              for p in missing]
    found = top_version(TEMPLATE_GW)  # read once
    if found != version:
        lines.append(f"stale marker: templates/gw.json: version {found if found is not None else 'missing'}")
    return lines


def git(*args):
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def git_raw(*args):
    """Like git() but keeps the output as is (no strip), for file contents."""
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout


def release_check(version):
    """Problems for a push to main: copyable files changed since the last vX.Y.Z tag reachable from HEAD while
    plugin.json still has that tag's version (a project that copied between the two would see "local edits" it never
    made), and a new version without a harvest since that tag (harvest_check) or with an undated or unfinished
    CHANGELOG entry (changelog_check). Run by the pre-push check on a push to the protected branch (GW_PUSH_PROTECTED=true)."""
    code, tag = git("describe", "--tags", "--abbrev=0", "--match", "v[0-9]*", "HEAD")
    if code != 0 or not tag:
        return ["no earlier vX.Y.Z tag in this clone, so the version cannot be compared with the last release; "
                "fetch the tags and retry: git fetch --tags origin && python3 scripts/version.py --release"]
    if tag[1:] != version:
        return changelog_check(version) + harvest_check(version, tag) + release_docs_check(version)
    code, changed = git("diff", "--name-only", tag, "HEAD", "--", *SCOPES, SKILL_LICENSE)
    if code != 0:
        return [f"cannot diff against {tag}; fetch it and retry: git fetch --tags origin && "
                "python3 scripts/version.py --release"]
    if not changed:
        return []
    files = changed.splitlines()
    shown = ", ".join(files[:5]) + (f" and {len(files) - 5} more" if len(files) > 5 else "")
    return [f"unbumped release: {len(files)} copyable file(s) changed since {tag} ({shown}) but the version is still "
            f"{version}; bump it (patch at least) and fill in the CHANGELOG: python3 scripts/version.py X.Y.Z"]


def release_docs_check(version):
    """Problems for releasing `version`: each file of the config's `releaseDocs` (as HEAD has it) must exist in HEAD, the
    tree being released, and name the version as a backticked token (`X.Y.Z`), so a status or what's-new section
    that still shows the previous release is caught before the push."""
    try:
        docs = config.load(ROOT, rev="HEAD")["releaseDocs"]
    except Exception as exc:
        return [f"cannot read releaseDocs: {exc}"]
    problems = []
    for doc in docs:
        code, text = git_raw("show", f"HEAD:{doc}")
        if code != 0:
            problems.append(f"missing release doc: {doc} (releaseDocs) is not in HEAD, the tree being released; "
                            "commit it or remove it from releaseDocs and retry: python3 scripts/version.py --release")
        elif f"`{version}`" not in text:
            problems.append(f"stale release doc: {doc} does not name `{version}`; update its status/what's new "
                            "against the CHANGELOG entry and retry: python3 scripts/version.py --release")
    return problems


def changelog_check(version):
    """Problems for releasing `version`: its CHANGELOG entry, the release notes, must be dated (`## [X.Y.Z] -
    YYYY-MM-DD`, not "Unreleased") and filled in (no "(por completar)" / "(to be filled in)" left by the bump)."""
    code, text = git_raw("show", "HEAD:CHANGELOG.md")
    if code != 0:
        return ["cannot read CHANGELOG.md from HEAD, the tree being released; commit it and retry: "
                "python3 scripts/version.py --release"]
    head = re.search(rf"^## \[{re.escape(version)}\][^\n]*", text, re.M)
    if not head:
        return [f"no CHANGELOG entry for {version}; add it (## [{version}] - YYYY-MM-DD, with ### ES and ### EN) and "
                "retry: python3 scripts/version.py --release"]
    problems = []
    if not re.fullmatch(rf"## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}\s*", head.group(0)):
        problems.append(f"undated release: the CHANGELOG heading of {version} is {head.group(0).strip()!r}; set the "
                        f"release date (## [{version}] - YYYY-MM-DD) and retry: python3 scripts/version.py --release")
    nxt = re.search(r"^## \[", text[head.end():], re.M)
    entry = text[head.end():head.end() + nxt.start()] if nxt else text[head.end():]
    if "(por completar)" in entry or "(to be filled in)" in entry:
        problems.append(f"unfinished CHANGELOG entry for {version}: it still has the bump's placeholder; fill in "
                        "### ES and ### EN and retry: python3 scripts/version.py --release")
    return problems + changelog_paths(version, entry)


REPO_PATH = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*/?$")
PLACEHOLDER = re.compile(r"[<>*{}…]|\bv?X\.Y\.Z\b|\bx\.y\.z\b|\bYYYY\b|\bMM-DD\b|\bNNN\b")
FILE_EXT = re.compile(r"\.(?:md|py|sh|json|ya?ml|toml|txt|cfg|ini)$")
ROOT_DOC = re.compile(r"^[A-Z][A-Za-z0-9_.-]*\.(?:md|txt|json|ya?ml|toml)$")


def looks_like_repo_path(path, tops):
    """True for a quoted token that is meant as a path of this repo: its first segment is a top-level name (of HEAD
    or its history), or it ends in a file extension or a slash (a typo'd directory such as `script/x.py`), or it is a
    root document by name (`CHANGELOG.md`). Prose with a slash (`ES/EN`, `feat/fix`) is not."""
    if not REPO_PATH.match(path):
        return False
    if "/" not in path:
        return path in tops or bool(ROOT_DOC.match(path))
    return path.split("/")[0] in tops or bool(FILE_EXT.search(path)) or path.rstrip("/").count("/") > 0 and path.endswith("/")


def changelog_paths(version, entry):
    """Problems for the repo paths the CHANGELOG entry of `version` quotes in backticks (`docs/...`, `scripts/...`,
    `CHANGELOG.md`): each must exist in HEAD, the tree being released, or have existed in the repo history (an old
    name cited as "antes X"), or be ignored by git (`.claude/gw.local.json`). Paths with a placeholder (`vX.Y.Z`,
    `<...>`, `*`, `YYYY-MM-DD`, `NNN`, `…`) are skipped. Fails closed when the tree cannot be listed."""
    code, out = git("ls-tree", "--name-only", "HEAD")
    if code != 0:
        return [f"cannot list the tree of HEAD to check the paths quoted in the CHANGELOG entry of {version}; commit "
                "first and retry: python3 scripts/version.py --release"]
    history = None  # every path ever in the repo (and its directories), read once and only if a path needs it
    tops = set(out.splitlines())
    problems, seen = [], set()
    for quoted in re.findall(r"`([^`\n]+)`", entry):
        path = quoted.strip()
        if path in seen or PLACEHOLDER.search(path):
            continue
        seen.add(path)
        if history is None:
            history = history_paths()
            tops |= {p.split("/")[0] for p in history}
        if not looks_like_repo_path(path, tops):
            continue
        bare = path.rstrip("/")
        if "/" not in bare and bare not in tops and any(h.rsplit("/", 1)[-1] == bare for h in history):
            continue  # a bare document name (`SKILL.md`) that exists somewhere in the tree or its history
        if git("cat-file", "-e", f"HEAD:{bare}")[0] == 0 or bare in history or \
                git("check-ignore", "--no-index", "-q", "--", path)[0] == 0:
            continue
        problems.append(f"CHANGELOG entry for {version} quotes `{path}`, which does not exist in the tree being "
                        "released, nor ever did, nor is ignored by git; fix the path in CHANGELOG.md (full path from "
                        "the repo root; drop the backticks if it is not a path of this repo) and retry: "
                        "python3 scripts/version.py --release")
    return problems


def history_paths():
    """Every file path that ever existed in any ref, plus all their parent directories (one `git log` pass)."""
    code, out = git("-c", "core.quotepath=off", "log", "--all", "--name-only", "--format=")
    found = set()
    for line in out.splitlines() if code == 0 else []:
        parts = line.split("/")
        for i in range(1, len(parts) + 1):
            found.add("/".join(parts[:i]))
    return found


def proposals_dir():
    """The config's `proposalsDir` as HEAD has it (the commit the diff goes to, not the working tree), where gw-harvest writes its "# Harvest <repo> — <date>" files."""
    return config.load(ROOT, rev="HEAD")["proposalsDir"].rstrip("/")


def harvest_check(version, tag):
    """Problems for releasing `version` after `tag`: every version starts with a harvest of the projects that use the
    workflow (AGENTS.md), so some file added under `proposalsDir` since the tag must be a gw-harvest one."""
    try:
        PROPOSALS = proposals_dir()
    except config.ConfigError as exc:
        return [f"cannot read proposalsDir: {exc}"]
    code, added = git("diff", "--name-only", "--no-renames", "--diff-filter=A", tag, "HEAD", "--", PROPOSALS)
    if code != 0:
        return [f"cannot diff against {tag}; fetch it and retry: git fetch --tags origin && "
                "python3 scripts/version.py --release"]
    for path in added.splitlines():
        if path.endswith(".md"):
            code, text = git("show", f"HEAD:{path}")
            if code == 0 and text.startswith("# Harvest "):
                return []
    return [f"no harvest for {version}: no {PROPOSALS}/*.md starting with '# Harvest' was added since {tag}; run the "
            "gw-harvest skill on the projects that use the workflow, commit its proposals file (one per harvest, also "
            "when nothing is new) and retry: python3 scripts/version.py --release"]


def commit_head(types, wip):
    """The regex of a commit subject `[WIP: ]type(scope)!: text` for the `commitTypes` and `commitWipPrefix` keys."""
    prefix = "(?:" + re.escape(wip) + ")?" if wip else ""
    return re.compile(r"^" + prefix + r"(" + "|".join(re.escape(t) for t in types) + r")(?:\([^()\r\n]*\))?(!)?: \S")


def commit_rules():
    """(the commit_head regex, patch types) from the config of the commit being released (HEAD): `commitTypes`,
    `commitWipPrefix` and `patchCommitTypes`. Raises VersionError when that config cannot be read."""
    try:
        cfg = config.load(ROOT, rev="HEAD")
    except (config.ConfigError, OSError) as exc:
        raise VersionError(f"cannot read commitTypes and patchCommitTypes: {exc}; fix .claude/gw.json and retry: "
                           "python3 scripts/version.py --suggest")
    return (commit_head(config.commit_types(cfg), config.commit_wip_prefix(cfg)),
            tuple(config.patch_commit_types(cfg)))


def numbers(version):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    return tuple(int(n) for n in m.groups()) if m else None


def is_breaking(message, head):
    """True when a commit message has `type!:` in its first line (`head`: commit_head's regex) or a BREAKING CHANGE
    trailer (git's own parse)."""
    first = head.match(message.split("\n", 1)[0])
    if first and first.group(2):
        return True
    r = subprocess.run(["git", "interpret-trailers", "--parse"], input=message, capture_output=True, text=True)
    if r.returncode != 0:
        raise VersionError("git interpret-trailers failed on a commit message; update git and retry: "
                           "python3 scripts/version.py --suggest")
    if any(line.startswith("BREAKING-CHANGE:") for line in r.stdout.splitlines()):
        return True
    # git does not take `BREAKING CHANGE` (with a space, the Conventional Commits spelling) for a trailer token
    paragraphs = [p for p in re.split(r"\n\s*\n", message.strip()) if p.strip()]
    return len(paragraphs) > 1 and any(line.startswith("BREAKING CHANGE:") for line in paragraphs[-1].splitlines())


def suggest(current):
    """Lines (all starting `suggest:` or `warning:`) with the bump the non-merge commits since the last vX.Y.Z tag
    ask for: breaking -> major (minor in 0.x, where a minor may break), feat -> minor, a `patchCommitTypes` type (fix/hotfix/perf) -> patch,
    the rest nothing; commits that do not follow the format are counted. Compares with plugin.json's `current` version."""
    code, tag = git("describe", "--tags", "--abbrev=0", "--match", "v[0-9]*.[0-9]*.[0-9]*", "HEAD")
    base = numbers(tag[1:]) if code == 0 and tag else None
    if base is None:
        return ["suggest: no vX.Y.Z tag reachable from HEAD, so no bump can be suggested; fetch the tags and retry: "
                "git fetch --tags origin && python3 scripts/version.py --suggest"]
    code, out = git("log", "--no-merges", "--format=%x1e%B", f"{tag}..HEAD")
    if code != 0:
        raise VersionError(f"cannot read the commits since {tag}; fetch it and retry: git fetch --tags origin && "
                           "python3 scripts/version.py --suggest")
    messages = [m.strip() for m in out.split("\x1e") if m.strip()]
    head, patch_types = commit_rules()
    counts, loose, breaking = {}, 0, False
    for message in messages:
        m = head.match(message.split("\n", 1)[0])
        if m:
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
        else:
            loose += 1
        breaking = is_breaking(message, head) or breaking
    major, minor, patch = base
    if breaking:
        level = "major" if major >= 1 else "minor"
    elif counts.get("feat"):
        level = "minor"
    elif any(counts.get(t) for t in patch_types):
        level = "patch"
    else:
        level = None
    summary = f"{len(messages)} commit(s) since {tag}"
    if loose:
        summary += f", {loose} not in the type(scope): text format (counted, they suggest nothing)"
    if level is None:
        return [f"suggest: {summary}: no bump suggested (nothing but docs/chore-like commits or none at all)"]
    new = {"major": (major + 1, 0, 0), "minor": (major, minor + 1, 0), "patch": (major, minor, patch + 1)}[level]
    suggested = ".".join(str(n) for n in new)
    lines = [f"suggest: {summary}: {level} bump, {tag[1:]} -> {suggested}"]
    now = numbers(current)
    if now is None:
        lines.append(f"warning: plugin.json version {current!r} is not X.Y.Z, so it cannot be compared with the "
                     f"suggested {suggested}; set it: python3 scripts/version.py {suggested}")
    elif now == new:
        lines.append(f"warning: plugin.json is already at the suggested {suggested}")
    elif now is not None and now > new:
        lines.append(f"warning: plugin.json {current} is ahead of the suggested {suggested}; check that it was intended")
    else:
        lines.append(f"warning: plugin.json {current} is behind the suggested {suggested}; bump it: "
                     f"python3 scripts/version.py {suggested}")
    return lines


def bump_plan(path, new):
    """The new text of a JSON file with only its top-level "version" set to new; None when already there."""
    rel = path.relative_to(ROOT)
    text = read(path)
    data = json.loads(text)
    if not isinstance(data, dict) or "version" not in data:
        raise VersionError(f"{rel} has no top-level \"version\" to bump; add it (\"version\": \"{new}\" as a "
                           f"top-level key) and retry: python3 scripts/version.py {new}")
    if data["version"] == new:
        return None
    out, n = TOP_VERSION.subn(lambda m: m.group(1) + new + m.group(3), text, count=1)
    if n != 1 or json.loads(out) != dict(data, version=new):
        raise VersionError(f"{rel}: its top-level \"version\" is not on its own line indented by two spaces, so it "
                           f"cannot be rewritten safely; reformat it that way and retry: python3 scripts/version.py {new}")
    return out


def changelog_plan(new):
    """The new CHANGELOG text with an entry for new; None when it already has one."""
    log = ROOT / "CHANGELOG.md"
    text = read(log)
    if f"## [{new}]" in text:
        return None
    if not re.search(r"^## \[", text, re.M):
        raise VersionError("CHANGELOG.md has no `## [x.y.z]` heading to put the new entry before; add the first one "
                           f"by hand (## [{new}] - Unreleased, with ### ES and ### EN) and retry: "
                           f"python3 scripts/version.py {new}")
    nl = "\r\n" if "\r\n" in text else "\n"
    entry = nl.join([f"## [{new}] - Unreleased", "", "### ES", "", "- (por completar)", "", "### EN", "",
                     "- (to be filled in)", "", ""])
    return re.sub(r"^## \[", lambda m: entry + "## [", text, count=1, flags=re.M)


def sync(new, with_changelog):
    """One pass: every marker that is not `new` becomes `new`. Everything is planned (and may raise VersionError)
    before anything is written. Returns (changed, skipped non-UTF-8 files)."""
    planned = [(path, bump_plan(path, new)) for path in (TEMPLATE_GW, PLUGIN)]
    if with_changelog:
        planned.append((ROOT / "CHANGELOG.md", changelog_plan(new)))
    stale, unreadable, _ = scan(new)
    for path, text, found in stale:
        for a, b in sorted(found, reverse=True):
            text = text[:a] + new + text[b:]
        planned.append((path, text))
    changed = []
    for path, text in planned:
        if text is not None:
            write(path, text)
            changed.append(path)
    return changed, unreadable


def main(argv):
    current = top_version(PLUGIN)
    if not isinstance(current, str):
        print('version: .claude-plugin/plugin.json has no top-level "version" (the source of every marker); add it '
              '("version": "X.Y.Z") and retry: python3 scripts/version.py', file=sys.stderr)
        return 1
    if argv == ["--suggest"]:
        try:
            for line in suggest(current):
                print(line)
        except VersionError as e:
            print(f"version: {e}", file=sys.stderr)
            return 1
        return 0
    release = argv[:1] == ["--release"]
    if release:
        argv = argv[1:]
    if not argv:
        problems = check(current) + (release_check(current) if release else [])
        for line in problems:
            print(line)
        if release:
            try:
                for line in suggest(current):
                    print(f"warning: {line}" if line.startswith("suggest:") else line)
            except VersionError as e:
                print(f"warning: {e}")
        if any(line.startswith("stale") for line in problems):
            print(f"markers differ from plugin.json ({current}); fix them: python3 scripts/version.py {current}")
        if problems:
            return 1
        print(f"all markers at {current}")
        return 0
    new = argv[0]
    if not SEMVER.match(new):
        print(f"{new!r} is not SemVer (X.Y.Z); retry: python3 scripts/version.py 0.2.0", file=sys.stderr)
        return 2
    try:
        _, skipped = sync(new, new != current)
    except VersionError as e:
        print(f"version: {e}", file=sys.stderr)
        return 1
    for path in skipped:
        print(f"skipped {path.relative_to(ROOT)}: not UTF-8; convert it and retry: python3 scripts/version.py {new}",
              file=sys.stderr)
    print(f"version {current} -> {new}; now: python3 scripts/apply.py . && fill in the CHANGELOG entry")
    return 1 if skipped else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
