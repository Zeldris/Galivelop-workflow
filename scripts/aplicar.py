#!/usr/bin/env python3
# galivelop-workflow v0.1.0
"""Apply or update the workflow in a project: the deterministic core of /gw-init and /gw-update (plan §5.4).

  python3 <workflow>/scripts/aplicar.py [PROJECT] [--update] [--check] [--dry-run] [--with SKILL ...]

Runs FROM the workflow repo (this script's own repo is the source) ONTO a project: PROJECT, else the git top level
of the current directory. The project must have a valid .claude/gw.json (fails closed, exit 2).

What it copies (workflow -> project):
  scripts/*                     -> .claude/gw/scripts/   (not recoger.py nor aplicar.py: workflow-only), exec bits kept
  schema/gw.schema.json         -> .claude/gw/schema/
  skills/<name>/                -> .claude/skills/<name>/ (not the optional opt-ai and scout-updates unless --with
                                   or already installed; not the workflow-only gw-harvest; all of them when PROJECT
                                   is the workflow repo itself)
  templates/githooks/*          -> .githooks/
  templates/claude/settings.json   merged into .claude/settings.json: missing env keys and hook entries are added
                                   (matched by event + matcher + command); nothing is removed or rewritten
and sets core.hooksPath to .githooks when it is unset and no other hook manager owns the hooks.

For each file: identical -> skip; missing -> create; different -> overwritten only when the project's file is
workflow-owned (a `galivelop-workflow vX.Y.Z` header, or metadata.version in the skill's SKILL.md), not newer than
the workflow, and either older or --update is given. Otherwise the new content goes next to it as <file>.gw-nuevo,
a proposal to review by hand. Files the workflow no longer has are reported, never deleted. Never commits.
In the workflow repo itself the copy is generated from scripts/ and skills/, so --update is implied there.

  --check     no writes; exit 1 if the copy differs from the workflow (anything to create, update, merge or chmod,
              a pending .gw-nuevo proposal, or a file the workflow no longer has); core.hooksPath is reported but
              does not fail it (a local git setting: a fresh clone in CI has it unset). The drift test.
  --dry-run   print the plan, no writes, exit 0.
Exit 2 on a missing or invalid config or settings file. Python 3.8+ standard library only.
"""
import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
HERE = Path(__file__).resolve().parent
WORKFLOW = HERE.parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402

WORKFLOW_ONLY_SCRIPTS = {"recoger.py", "aplicar.py"}
WORKFLOW_ONLY_SKILLS = {"gw-harvest"}
OPTIONAL_SKILLS = {"opt-ai", "scout-updates"}
IGNORED = {"__pycache__", ".DS_Store"}
PROPOSAL = ".gw-nuevo"
HEADER = re.compile(r"galivelop-workflow v(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)")
SENSITIVE = (".claude/settings.json", ".claude/hooks/", ".githooks/")


class ApplyError(Exception):
    pass


def workflow_version():
    return json.loads((WORKFLOW / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]


def version_key(v):
    """'1.2.3-rc1' -> ((1, 2, 3), 0); a pre-release sorts before its release."""
    main, _, pre = v.partition("-")
    nums = tuple(int(x) if x.isdigit() else 0 for x in (main.split(".") + ["0", "0"])[:3])
    return nums, 0 if pre else 1


def header_version(data):
    head = "\n".join(data.decode("utf-8", errors="replace").splitlines()[:5])
    m = HEADER.search(head)
    return m.group(1) if m else None


def skill_version(path):
    """metadata.version from a SKILL.md frontmatter, or None."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    inside = False
    for line in (m.group(1).splitlines() if m else []):
        if re.match(r"^metadata:\s*$", line):
            inside = True
            continue
        if inside:
            sub = re.match(r"^\s+([A-Za-z_-]+):\s*(.*)$", line)
            if not sub:
                break
            if sub.group(1) == "version":
                return sub.group(2).strip().strip("\"'") or None
    return None


def files_under(folder):
    """Regular files under folder (relative paths, sorted), skipping caches and proposals."""
    out = []
    if not folder.is_dir():
        return out
    for dirpath, dirnames, filenames in os.walk(str(folder)):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORED)
        for name in sorted(filenames):
            if name in IGNORED or name.endswith(".pyc") or name.endswith(PROPOSAL):
                continue
            p = Path(dirpath) / name
            if p.is_file() and not p.is_symlink():
                out.append(p.relative_to(folder))
    return out


def is_exec(path):
    return bool(path.stat().st_mode & stat.S_IXUSR)


def git(root, *args):
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


class Plan:
    def __init__(self, root, version, update):
        self.root = root
        self.version = version
        self.update = update
        self.actions = []   # (kind, rel, data, exec, detail); kind: create | update | propose | chmod | merge
        self.notes = []     # reported, never acted on
        self.pending = []   # proposals already written and still current
        self.orphans = []   # files the workflow no longer has
        self.hooks_path = None  # None, or the hint line about core.hooksPath
        self.set_hooks_path = False

    # ------------------------------------------------------------- files

    def file(self, src, rel, owner_version=None, owned=None):
        """Plan one copy. owner_version/owned: for skill files, from the project's SKILL.md (read before writes)."""
        data = src.read_bytes()
        want_exec = is_exec(src)
        dest = self.root / rel
        if not dest.exists():
            self.actions.append(("create", rel, data, want_exec, ""))
            return
        current = dest.read_bytes()
        if current == data:
            if want_exec and not is_exec(dest):
                self.actions.append(("chmod", rel, None, True, "make it executable"))
            return
        if owned is None:
            found = header_version(current)
            owned, owner_version = found is not None, found
        newer = owned and owner_version and version_key(owner_version) > version_key(self.version)
        older = owned and owner_version and version_key(owner_version) < version_key(self.version)
        if owned and owner_version and not newer and (self.update or older):
            why = f"v{owner_version} -> v{self.version}" if older else f"v{owner_version}, local edits replaced (--update)"
            self.actions.append(("update", rel, data, want_exec, why))
            return
        if not owned:
            why = "not workflow-owned (no galivelop-workflow header or skill metadata.version)"
        elif newer:
            why = f"the project's copy is v{owner_version}, newer than the workflow's v{self.version}"
        else:
            why = f"v{owner_version} with local edits (rerun with --update to replace them)"
        proposal = Path(str(rel) + PROPOSAL)
        pdest = self.root / proposal
        if pdest.is_file() and pdest.read_bytes() == data:
            self.pending.append((rel, why))
        else:
            self.actions.append(("propose", proposal, data, want_exec, f"{rel} differs: {why}"))

    def tree(self, src_dir, dest_rel, owner_version=None, owned=None, only=None):
        names = only if only is not None else files_under(src_dir)
        for name in names:
            self.file(src_dir / name, dest_rel / name, owner_version, owned)
        mine = set(names)
        for name in files_under(self.root / dest_rel):
            if name not in mine:
                self.orphans.append(dest_rel / name)

    # ------------------------------------------------------------- settings

    def settings(self, template):
        rel = Path(".claude") / "settings.json"
        path = self.root / rel
        tmpl = json.loads(template.read_text(encoding="utf-8"))
        if path.exists():
            try:
                current = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ApplyError(f"aplicar: {path}: invalid JSON at line {exc.lineno}: {exc.msg}; fix it and rerun: "
                                 f"python3 -m json.tool {path}")
            if not isinstance(current, dict):
                raise ApplyError(f"aplicar: {path} is not a JSON object; fix it and rerun: python3 -m json.tool {path}")
        else:
            current = {}
        merged, added = merge_settings(current, tmpl)
        if not path.exists():
            self.actions.append(("create", rel, dump(merged), False, ""))
        elif added:
            self.actions.append(("merge", rel, dump(merged), False, ", ".join(added)))


def dump(data):
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def merge_settings(current, template):
    """Add the template's missing env keys and hook commands to a copy of current. Returns (merged, [what added])."""
    merged = json.loads(json.dumps(current))
    added = []
    tenv = template.get("env") or {}
    if tenv:
        env = merged.setdefault("env", {})
        if not isinstance(env, dict):
            raise ApplyError("aplicar: .claude/settings.json: 'env' is not an object; fix it and rerun: "
                             "python3 -m json.tool .claude/settings.json")
        for key, value in tenv.items():
            if key not in env:
                env[key] = value
                added.append(f"env {key}")
    thooks = template.get("hooks") or {}
    if thooks:
        hooks = merged.setdefault("hooks", {})
        if not isinstance(hooks, dict):
            raise ApplyError("aplicar: .claude/settings.json: 'hooks' is not an object; fix it and rerun: "
                             "python3 -m json.tool .claude/settings.json")
    for event, entries in thooks.items():
        have = hooks.setdefault(event, [])
        if not isinstance(have, list):
            raise ApplyError(f"aplicar: .claude/settings.json: hooks.{event} is not a list; fix it and rerun: "
                             f"python3 -m json.tool .claude/settings.json")
        for entry in entries:
            matcher = entry.get("matcher")
            same = [e for e in have if isinstance(e, dict) and e.get("matcher") == matcher]
            commands = {h.get("command") for e in same for h in (e.get("hooks") or []) if isinstance(h, dict)}
            missing = [h for h in entry.get("hooks") or [] if h.get("command") not in commands]
            if not missing:
                continue
            if same and isinstance(same[0].get("hooks"), list):
                same[0]["hooks"].extend(missing)
            else:
                new = {k: v for k, v in entry.items() if k != "hooks"}
                new["hooks"] = missing
                have.append(new)
            added.append(f"{event} hook{'s' if len(missing) > 1 else ''} ({matcher or 'no matcher'})")
    return merged, added


# ----------------------------------------------------------------- planning

def chain_hint(hooks_dir):
    return (f"add as the last line of {hooks_dir}/pre-push and {hooks_dir}/pre-commit (with <hook> = the file's "
            f"name): \"$(git rev-parse --show-toplevel)/.githooks/<hook>\" \"$@\" || exit 1")


def plan_hooks_path(plan):
    root = plan.root
    code, current = git(root, "config", "--get", "core.hooksPath")
    if code == 0 and current:
        if current not in (".githooks", str(root / ".githooks")):
            plan.hooks_path = (f"core.hooksPath is '{current}' (another hook manager), left as is; the workflow's "
                               f"hooks run only if chained: {chain_hint(current)}")
        return
    _, hooks_dir = git(root, "rev-parse", "--git-path", "hooks")
    hooks_dir = Path(hooks_dir) if os.path.isabs(hooks_dir) else root / hooks_dir
    foreign = [h for h in ("pre-commit", "pre-push", "commit-msg")
               if (hooks_dir / h).is_file() and os.access(str(hooks_dir / h), os.X_OK)]
    if foreign:
        plan.hooks_path = (f"another hook manager installed {', '.join(foreign)} in {hooks_dir}; core.hooksPath "
                           f"left unset so they keep running; {chain_hint(hooks_dir)}")
        return
    plan.set_hooks_path = True


def build(root, version, update, extra_skills):
    self_apply = root.resolve() == WORKFLOW.resolve()
    plan = Plan(root, version, update or self_apply)
    scripts = [Path(p.name) for p in sorted((WORKFLOW / "scripts").iterdir())
               if p.is_file() and p.name not in WORKFLOW_ONLY_SCRIPTS and p.name not in IGNORED
               and not p.name.endswith(".pyc")]
    plan.tree(WORKFLOW / "scripts", Path(".claude/gw/scripts"), only=scripts)
    plan.tree(WORKFLOW / "schema", Path(".claude/gw/schema"), only=[Path("gw.schema.json")])

    available = sorted(p.name for p in (WORKFLOW / "skills").iterdir() if (p / "SKILL.md").is_file())
    unknown = sorted(set(extra_skills) - set(available))
    if unknown:
        raise ApplyError(f"aplicar: unknown skill(s) for --with: {', '.join(unknown)}; available: "
                         f"{', '.join(available)}")
    installed = root / ".claude" / "skills"
    for name in available:
        wanted = (self_apply or name in extra_skills or (installed / name / "SKILL.md").is_file()
                  or name not in OPTIONAL_SKILLS | WORKFLOW_ONLY_SKILLS)
        if not wanted:
            continue
        dest = Path(".claude/skills") / name
        owner = skill_version(root / dest / "SKILL.md")
        plan.tree(WORKFLOW / "skills" / name, dest, owner_version=owner, owned=owner is not None)

    hooks_src = WORKFLOW / "templates" / "githooks"
    names = files_under(hooks_src)
    for name in names:
        plan.file(hooks_src / name, Path(".githooks") / name)
    for name in files_under(root / ".githooks"):
        if name not in names and header_version((root / ".githooks" / name).read_bytes()):
            plan.orphans.append(Path(".githooks") / name)

    plan.settings(WORKFLOW / "templates" / "claude" / "settings.json")
    plan_hooks_path(plan)
    return plan


# ----------------------------------------------------------------- output

def sensitive(rel):
    s = str(rel).replace(os.sep, "/")
    return any(s == p or s.startswith(p) for p in SENSITIVE)


def describe(plan):
    lines = []
    for kind, rel, _data, _exec, detail in plan.actions:
        lines.append(f"  {kind:<8}{rel}" + (f"  ({detail})" if detail else ""))
    if plan.set_hooks_path:
        lines.append("  git     config core.hooksPath .githooks")
    return lines


def report(plan):
    for rel, why in plan.pending:
        print(f"aplicar: pending proposal {rel}{PROPOSAL} ({rel} differs: {why}); merge it by hand and delete it: "
              f"rm {rel}{PROPOSAL}")
    for rel in plan.orphans:
        print(f"aplicar: {rel} is no longer in the workflow (kept); delete it if nothing uses it: git rm {rel}")
    if plan.hooks_path:
        print(f"aplicar: {plan.hooks_path}")


def apply(plan):
    if any(sensitive(a[1]) for a in plan.actions):
        print("aplicar: note: Claude Code's auto mode may ask for permission to edit .claude/settings.json, "
              ".claude/hooks/ and .githooks/; approve it, or run this script yourself: "
              f"python3 {Path(__file__).resolve()} {plan.root}")
    for kind, rel, data, want_exec, _detail in plan.actions:
        dest = plan.root / rel
        if kind != "chmod":
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        if want_exec:
            dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if plan.set_hooks_path:
        code, _ = git(plan.root, "config", "core.hooksPath", ".githooks")
        if code != 0:
            print("aplicar: could not set core.hooksPath; set it by hand: git config core.hooksPath .githooks")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", nargs="?", help="the project (default: git top level of the current directory)")
    parser.add_argument("--update", action="store_true", help="replace local edits in workflow-owned files")
    parser.add_argument("--check", action="store_true", help="no writes; exit 1 if the copy differs")
    parser.add_argument("--dry-run", action="store_true", help="print the plan, no writes")
    parser.add_argument("--with", dest="extra", action="append", default=[], metavar="SKILL",
                        help="also install an optional skill (repeatable)")
    args = parser.parse_args(argv)

    start = args.project or os.getcwd()
    root = config.git_toplevel(start)
    if root is None:
        print(f"aplicar: {start} is not inside a git repository; create it first: git init {start}", file=sys.stderr)
        return 2
    root = root.resolve()
    if not (root / config.CONFIG_REL).is_file():
        print(f"aplicar: {root / config.CONFIG_REL} not found, so the workflow cannot be applied; create it "
              f"(a template arrives in Phase 4) and validate it: python3 {HERE / 'config.py'} --root {root} validate",
              file=sys.stderr)
        return 2
    try:
        cfg = config.load(str(root))
    except config.ConfigError as exc:
        print(f"aplicar: {exc}\naplicar: fix it and validate: python3 {HERE / 'config.py'} --root {root} validate",
              file=sys.stderr)
        return 2
    version = workflow_version()
    try:
        plan = build(root, version, args.update, args.extra)
    except ApplyError as exc:
        print(exc, file=sys.stderr)
        return 2

    lines = describe(plan)
    if args.check:
        drift = bool(plan.actions or plan.pending or plan.orphans)
        for line in lines:
            if not line.startswith("  git"):
                print(line)
        report(plan)
        if drift:
            print(f"aplicar: the workflow copy in {root} differs from the workflow v{version} (above); bring it up "
                  f"to date: python3 {Path(__file__).resolve()} {root}")
            return 1
        print(f"aplicar: workflow copy in sync with v{version}")
        return 0
    if args.dry_run:
        print(f"aplicar: plan for {root} (workflow v{version}, dry run, nothing written):")
        for line in lines:
            print(line)
        if not lines:
            print("  nothing to do")
        report(plan)
        return 0
    if not lines:
        print(f"aplicar: nothing to do; {root} is at workflow v{version}")
        report(plan)
        return 0
    print(f"aplicar: applying workflow v{version} to {root}:")
    for line in lines:
        print(line)
    apply(plan)
    report(plan)
    if cfg.get("version") != version:
        print(f"aplicar: .claude/gw.json says version {cfg.get('version')}; set it to {version} once the "
              f"proposals are reviewed: edit \"version\" in {root / config.CONFIG_REL}")
    if any(a[0] == "propose" for a in plan.actions):
        print(f"aplicar: review each *{PROPOSAL} (merge by hand, then delete it) before committing")
    if cfg.get("language") == "es":
        title, nxt = f"Flujo Galivelop-workflow v{version}", "Siguiente: <próximo paso concreto>"
    else:
        title, nxt = f"Galivelop-workflow v{version} workflow", "Next: <next concrete step>"
    print("aplicar: nothing was committed; suggested commit (fill in the last line):")
    print(f"  git add -A && git commit -m \"{title}\" -m \"{nxt}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
