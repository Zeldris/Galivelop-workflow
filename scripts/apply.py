#!/usr/bin/env python3
# galivelop-workflow v0.4.3
"""Apply or update the workflow in a project: the deterministic core of /gw-init and /gw-update (plan §5.4).

  python3 <workflow>/scripts/apply.py [PROJECT] [--update] [--check] [--dry-run] [--with SKILL ...]
          [--no-personal-notes] [--keep-paths]
  python3 <workflow>/scripts/apply.py [PROJECT] --init --check-command CMD [--language es|en] [--log PATH]
          [--install CMD ...] [--protected-branch B] [--push-to-protected direct|pr] [--content REGEX ...]
          [--review-mark PATH] [--require-retro true|false] [--agent-signatures true|false]
          [--visible-language LANG ...] [--design-reference REF ...]

Runs FROM the workflow repo (this script's own repo is the source) ONTO a project: PROJECT, else the git top level
of the current directory. The project must have a valid .claude/gw.json (fails closed, exit 2), except with --init:
that writes .claude/gw.json from templates/gw.json plus the flags (only when it does not exist yet; --check-command
is required, the log defaults to docs/handoff.md), validates it and then
applies as usual.

What it copies (workflow -> project):
  scripts/*                     -> .claude/gw/scripts/   (not harvest.py, apply.py nor version.py: workflow-only), exec bits kept
  schema/gw.schema.json         -> .claude/gw/schema/
  skills/<name>/                -> .claude/skills/<name>/ (not the optional gw-opt-ai and gw-scout-updates unless --with
                                   or already installed; not the workflow-only gw-harvest; all of them when PROJECT
                                   is the workflow repo itself)
  templates/githooks/*          -> .githooks/
  templates/claude/settings.json   merged into .claude/settings.json: missing env keys and hook entries are added
                                   (matched by event + matcher + command); nothing is removed or rewritten
  templates/<language>/ (`language` of the config), with {{key}} placeholders rendered from the config:
    AGENTS.md, CLAUDE.md        -> the project root; created when missing; an existing one without the
                                   galivelop-workflow marker, or with an older one, gets a .gw-nuevo proposal to merge
                                   by hand (the project fills in its own rules there, so they are never overwritten)
    REVIEW.md, GLOSSARY.md      -> the project root  } created when missing and NEVER written again (the project
    log.md                      -> the config's `log` } fills them in); an older marker is reported as a template
    gw-opt-tokens.md (+ gw-opt-ai.md,  -> .claude/gw/       } update to review with /gw-update
      gw-scout-updates.md when that optional skill is installed)
  templates/github/check.yml -> .github/workflows/check.yml (workflow-owned, like the scripts)
In the workflow repo itself the root templates and the CI file are skipped: it has its own AGENTS.md, log and CI.
  ~/.claude/gw/notas/*          -> .claude/gw/           PERSONAL NOTES of the person running this (folder overridable
                                   with the env var GW_PERSONAL_NOTES; absent folder = nothing happens). Only regular
                                   files directly in it, named [A-Za-z0-9][A-Za-z0-9._-]* (no subfolders, symlinks or
                                   dotfiles). Missing in the project -> created (with --check only reported: it is
                                   not drift); identical -> nothing; different -> NEVER overwritten and no .gw-nuevo
                                   (the project may have adapted it): one line with `diff <source> <target>`, and
                                   --check does not fail for it. A name ending in .gw-nuevo, one a workflow file may
                                   have there, or one whose target is not a regular file is skipped with a WARNING.
                                   Never applied to the workflow repo itself (nothing personal goes in it);
                                   --no-personal-notes skips them for one run.
and sets core.hooksPath to .githooks when it is unset and no other hook manager owns the hooks.

Migration from the names before A8 (0.x), in the same run and without duplicates:
  .github/workflows/comprobar.yml -> .github/workflows/check.yml (git mv when tracked), when it is the workflow's own
                                (a `galivelop-workflow` header); then it is updated like any workflow-owned file, and
                                one with local edits or newer than the workflow keeps them and gets the template as
                                check.yml.gw-nuevo. Without the header it is the project's own CI: left alone, and
                                the template goes next to it as check.yml.gw-nuevo. Both exist: nothing is touched
                                but a warning.
  --sin-notas-personales and GW_NOTAS_PERSONALES (now --no-personal-notes and GW_PERSONAL_NOTES) still work, with a
                                warning on stderr.
  .claude/skills/<old>/         removed when workflow-owned (selector, orchestrate-dealer, opt-tokens, opt-ai,
                                scout-updates): the gw- one replaces it; an installed old optional skill stays
                                installed under its new name; --with <old name> works, with a warning
  .claude/gw/<old>.md           -> .claude/gw/gw-<name>.md (git mv when tracked); both exist: the new one is kept,
                                the old one reported, nothing overwritten
  .claude/gw/scripts/<old>      removed only when git-clean (tracked, no edits, no untracked or ignored files) and no
                                hook, the CI or the config still runs it; otherwise kept with a warning; the
                                old script names in .claude/settings.json hook commands are renamed
  docs/traspaso.md, docs/registros/, docs/propuestas/, docs/registros/revisado.txt (what the config's log,
  recordsDir, proposalsDir and reviewMark hold, or lack, while only the old path exists) -> docs/handoff.md,
  docs/records/, docs/proposals/, docs/records/reviewed.txt, with git mv when tracked; keys that held the old
  path are dropped from .claude/gw.json. Fails closed (exit 2) when a target already exists. --keep-paths moves
  nothing and writes the old paths explicitly into .claude/gw.json with "keepLegacyPaths": true (setting that key
  by hand does the same), so later updates leave them alone.

For each file: identical -> skip; missing -> create; different -> overwritten only when the project's file is
workflow-owned (a `galivelop-workflow vX.Y.Z` header, or metadata.version in the skill's SKILL.md), not newer than
the workflow, and either older or --update is given. Otherwise the new content goes next to it as <file>.gw-nuevo,
a proposal to review by hand. Files the workflow no longer has are reported, never deleted. Never commits.
In the workflow repo itself the copy is generated from scripts/ and skills/, so --update is implied there.

  --check     no writes; exit 1 if the copy differs from the workflow (anything to create, update, merge or chmod,
              a pending .gw-nuevo proposal, or a file the workflow no longer has); core.hooksPath is reported but
              does not fail it (a local git setting: a fresh clone in CI has it unset). The drift test.
  --dry-run   print the plan, no writes, exit 0.
  --keep-paths   keep the old Spanish project paths: write them explicitly in .claude/gw.json instead of moving them.
  --no-personal-notes   do not carry the personal notes (env GW_PERSONAL_NOTES, default ~/.claude/gw/notas/).
Exit 2 on a missing or invalid config or settings file. Python 3.8+ standard library only.
"""
import argparse
import difflib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
HERE = Path(__file__).resolve().parent
WORKFLOW = HERE.parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
from doctor import ignored_paths, stale_flow_hooks  # noqa: E402  (one list each, shared with doctor.py)

WORKFLOW_ONLY_SCRIPTS = {"harvest.py", "apply.py", "version.py"}
WORKFLOW_ONLY_SKILLS = {"gw-harvest"}
OPTIONAL_SKILLS = {"gw-opt-ai", "gw-scout-updates"}
IGNORED = {"__pycache__", ".DS_Store"}
PROPOSAL = ".gw-nuevo"
PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")
TEXT_KEYS = ("log", "protectedBranch", "reviewMark", "language")
LIST_KEYS = ("check", "install")
DIFFED = ("REVIEW.md", "GLOSSARY.md")  # seeded files whose template diff is printed while unmarked or older
DIFF_LINES = 80
ROOT_TEMPLATES = (("AGENTS.md", "merged"), ("CLAUDE.md", "merged"), ("REVIEW.md", "seeded"),
                  ("GLOSSARY.md", "seeded"))
NOTES = (("gw-opt-tokens.md", None), ("gw-opt-ai.md", "gw-opt-ai"), ("gw-scout-updates.md", "gw-scout-updates"))
# A8 (0.x): names the workflow had before the rename; /gw-update migrates an installed project to the new ones.
OLD_SKILLS = {"selector": "gw-selector", "orchestrate-dealer": "gw-orchestrate-dealer", "opt-tokens": "gw-opt-tokens",
              "opt-ai": "gw-opt-ai", "scout-updates": "gw-scout-updates"}
OLD_SCRIPTS = {"antes-de-parar.py": "before-stop.py", "bitacora.py": "handoff.py", "check-verde.sh": "check-green.sh",
               "enlaces-md.py": "md-links.py", "es-codigo.sh": "is-code.sh", "fusionar.sh": "merge-branch.sh",
               "guardia-config.py": "config-guard.py", "mapa-agente.py": "agent-map.py",
               "prepush-ramas.sh": "prepush-branches.sh", "recoger.py": "harvest.py", "recuperar.py": "recover.py",
               "registro_sesion.py": "session_log.py", "revisado.sh": "reviewed.sh",
               "revision-antes-de-main.sh": "review-before-main.sh", "rojo-sin-arreglo.sh": "red-without-fix.sh",
               "tests-relacionados.sh": "related-tests.sh", "tope-subagentes.py": "subagent-cap.py",
               "aplicar.py": "apply.py"}
PATH_DIR_KEYS = ("recordsDir", "proposalsDir")  # moved before the file keys inside them
LOG_BY_LANGUAGE = {"es": "docs/handoff.md", "en": "docs/handoff.md"}  # A8: English paths in every language
NOTES_ENV = "GW_PERSONAL_NOTES"
OLD_NOTES_ENV = "GW_NOTAS_PERSONALES"  # A8 (0.x): read, with a warning, when the new one is unset
OLD_FLAGS = {"--sin-notas-personales": "--no-personal-notes"}
OLD_WORKFLOW = Path(".github/workflows/comprobar.yml")
NEW_WORKFLOW = Path(".github/workflows/check.yml")
# Old option spellings in the hook commands of a project's settings (recover.py's flags), renamed like the scripts
OLD_HOOK_FLAGS = {"--estado": "--state", "--buscar": "--search", "--sesion": "--session", "--ancho": "--width"}
NOTE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
HEADER = re.compile(r"galivelop-workflow v(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)")
SKILL_LICENSE = "LICENSE-mattpocock-skills"  # at the workflow's root; copied next to the skills that cite it
SENSITIVE = (".claude/settings.json", ".claude/gw/scripts/", ".githooks/")


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


def skill_version_span(text):
    """(start, end) of metadata.version's value inside a SKILL.md frontmatter, or None. LF or CRLF; the value runs up
    to whitespace, a quote or `#` (its quotes and a trailing comment are not part of it). The one parser of skill
    versions: version.py imports it."""
    fm = re.match(r"---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not fm:
        return None
    pos, inside = fm.start(1), False
    for line in fm.group(1).splitlines(keepends=True):
        bare = line.rstrip("\r\n")
        if re.match(r"metadata:\s*(?:#.*)?$", bare):
            inside = True
        elif inside:
            sub = re.match(r"(\s+)([A-Za-z_-]+):\s*([\"']?)([^\"'\s#]*)", bare)
            if not sub:
                break
            if sub.group(2) == "version":
                return pos + sub.start(4), pos + sub.end(4)
        pos += len(line)
    return None


def skill_version(path):
    """metadata.version from a SKILL.md frontmatter, or None."""
    try:
        with open(path, encoding="utf-8", errors="replace", newline="") as f:
            text = f.read()
    except OSError:
        return None
    span = skill_version_span(text)
    return text[span[0]:span[1]] or None if span else None


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
        self.warnings = []  # the same, about the project's own files
        self.diffs = []     # (rel, project's bytes, template bytes): printed, never written
        self.personal = []  # info lines about personal notes the project has differently: never drift
        self.pending = []   # proposals already written and still current
        self.orphans = []   # files the workflow no longer has
        self.moved_to = set()   # repo-relative targets of the planned moves: nothing is seeded there
        self.hooks_path = None  # None, or the hint line about core.hooksPath
        self.set_hooks_path = False

    # ------------------------------------------------------------- files

    def file(self, src, rel, owner_version=None, owned=None, data=None, existing=None):
        """Plan one copy. owner_version/owned: for skill files, from the project's SKILL.md (read before writes).
        data: rendered content instead of src's bytes (a template; never executable). existing: the repo-relative
        file whose content stands for the one at `rel` (it is being moved there in the same run)."""
        want_exec = is_exec(src) if data is None else False
        data = src.read_bytes() if data is None else data
        dest = self.root / rel
        here = self.root / existing if existing else dest
        if not here.exists():
            self.actions.append(("create", rel, data, want_exec, ""))
            return
        current = here.read_bytes()
        if current == data:
            if want_exec and not is_exec(here):
                self.actions.append(("chmod", rel, None, True, "make it executable"))
            return
        if owned is None:
            found = header_version(current)
            owned, owner_version = found is not None, found
        newer = owned and owner_version and version_key(owner_version) > version_key(self.version)
        older = owned and owner_version and version_key(owner_version) < version_key(self.version)
        if owned and owner_version and not newer and (self.update or older):
            why = (f"v{owner_version} -> v{self.version}" if older
                   else f"v{owner_version}, local edits or an older copy of that version replaced (--update)")
            self.actions.append(("update", rel, data, want_exec, why))
            return
        if not owned:
            why = "not workflow-owned (no galivelop-workflow header or skill metadata.version)"
        elif newer:
            why = f"the project's copy is v{owner_version}, newer than the workflow's v{self.version}"
        else:
            why = (f"differs from the workflow's v{owner_version}: local edits or an older copy of that version; see it: "
                   f"diff {rel} {rel}{PROPOSAL} (rerun with --update to replace it)")
        self.propose(rel, data, want_exec, why)

    def propose(self, rel, data, want_exec, why):
        proposal = Path(str(rel) + PROPOSAL)
        pdest = self.root / proposal
        if pdest.is_file() and pdest.read_bytes() == data:
            self.pending.append((rel, why))
        else:
            self.actions.append(("propose", proposal, data, want_exec, f"{rel} differs: {why}"))

    def template(self, rel, data, kind):
        """Plan one rendered template. kind: owned (like a script), merged (AGENTS.md/CLAUDE.md: the project adds its
        rules, so never overwritten; a proposal when unmarked or older) or seeded (created once, never written
        again; an older marker is only reported)."""
        if kind == "owned":
            self.file(None, rel, data=data)
            return
        if str(rel) in self.moved_to:
            return  # the project's own file is about to be moved there
        dest = self.root / rel
        if not dest.exists():
            self.actions.append(("create", rel, data, False, ""))
            return
        current = dest.read_bytes()
        if current == data:
            return
        found = header_version(current)
        older = found is not None and version_key(found) < version_key(self.version)
        if kind == "seeded":
            if str(rel) in DIFFED and (found is None or older):
                self.diffs.append((rel, current, data))
            if older:
                self.notes.append(f"{rel} comes from the v{found} template and the template is now v{self.version}; "
                                  f"the project's file is never overwritten: review the template change with "
                                  f"/gw-update, then set its marker line to v{self.version}")
            return
        if found is not None and not older:
            return  # the project's own edits at this version (or a newer copy)
        why = (f"v{found}, the template is now v{self.version}" if found is not None
               else "not workflow-owned (no galivelop-workflow marker)")
        self.propose(rel, data, False, why + "; merge this block by hand or with the agent, keeping the marker line "
                     "at the top")

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
                raise ApplyError(f"apply: {path}: invalid JSON at line {exc.lineno}: {exc.msg}; fix it and rerun: "
                                 f"python3 -m json.tool {path}")
            if not isinstance(current, dict):
                raise ApplyError(f"apply: {path} is not a JSON object; fix it and rerun: python3 -m json.tool {path}")
        else:
            current = {}
        renamed = rename_hook_scripts(current)
        merged, added = merge_settings(current, tmpl)
        if renamed:
            added.insert(0, f"hook commands renamed: {', '.join(sorted(renamed))}")
        hooks = merged.get("hooks") if isinstance(merged.get("hooks"), dict) else {}
        for event, command in stale_flow_hooks(hooks, self.root):
            self.warnings.append(f".claude/settings.json {event} also runs '{command}', a workflow script from "
                                 f"outside .claude/gw/scripts/ (an older copy?); delete that entry if so, or it runs twice")
        if not path.exists():
            self.actions.append(("create", rel, dump(merged), False, ""))
        elif added:
            self.actions.append(("merge", rel, dump(merged), False, ", ".join(added)))
        local = Path(".claude") / "settings.local.json"  # the person's own hooks: only the old script names change
        try:
            mine = json.loads((self.root / local).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            mine = None
        if isinstance(mine, dict):
            renamed = rename_hook_scripts(mine)
            if renamed:
                self.actions.append(("merge", local, dump(mine), False,
                                     f"hook commands renamed: {', '.join(sorted(renamed))}"))


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
            raise ApplyError("apply: .claude/settings.json: 'env' is not an object; fix it and rerun: "
                             "python3 -m json.tool .claude/settings.json")
        for key, value in tenv.items():
            if key not in env:
                env[key] = value
                added.append(f"env {key}")
    thooks = template.get("hooks") or {}
    if thooks:
        hooks = merged.setdefault("hooks", {})
        if not isinstance(hooks, dict):
            raise ApplyError("apply: .claude/settings.json: 'hooks' is not an object; fix it and rerun: "
                             "python3 -m json.tool .claude/settings.json")
    for event, entries in thooks.items():
        have = hooks.setdefault(event, [])
        if not isinstance(have, list):
            raise ApplyError(f"apply: .claude/settings.json: hooks.{event} is not a list; fix it and rerun: "
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


def rename_hook_scripts(settings):
    """Rewrite, in place, the old script names (and recover.py's old option names) in the commands of settings['hooks'] that run a copy under
    .claude/gw/scripts/. Returns the set of 'old -> new' renamed."""
    done = set()
    hooks = settings.get("hooks")
    for entries in (hooks.values() if isinstance(hooks, dict) else []):
        for entry in entries if isinstance(entries, list) else []:
            for h in (entry.get("hooks") or []) if isinstance(entry, dict) and isinstance(entry.get("hooks"), list) else []:
                command = h.get("command") if isinstance(h, dict) else None
                if not isinstance(command, str) or ".claude/gw/scripts/" not in command:
                    continue
                for old, new in OLD_SCRIPTS.items():
                    fixed = re.sub(rf"(?<![\w.-]){re.escape(old)}(?![\w-])", new, command)
                    if fixed != command:
                        done.add(f"{old} -> {new}")
                        command = fixed
                if re.search(r"recover\.py", command):
                    for old, new in OLD_HOOK_FLAGS.items():
                        fixed = re.sub(rf"(?<![\w-]){re.escape(old)}(?![\w-])", new, command)
                        if fixed != command:
                            done.add(f"recover.py {old} -> {new}")
                            command = fixed
                h["command"] = command
    return done


# ----------------------------------------------------------------- planning

def chain_hint(hooks_dir):
    return (f"add as the last line of {hooks_dir}/pre-push, {hooks_dir}/pre-commit and {hooks_dir}/commit-msg (with <hook> = the file's "
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


def inline_list(items):
    return ", ".join(f"`{i}`" for i in items) if items else "—"


def render(text, cfg, root, version, name):
    """Replace {{key}}: config keys (lists as an inline code list), {{version}} (the workflow's), {{project}}."""
    def value(m):
        key = m.group(1)
        if key in TEXT_KEYS:
            return str(cfg[key])
        if key in LIST_KEYS:
            return inline_list(cfg.get(key) or [])
        if key == "version":
            return version
        if key == "project":
            return root.name
        raise ApplyError(f"apply: template {name} has an unknown placeholder {{{{{key}}}}}; fix the template in "
                         f"{WORKFLOW / 'templates'}")
    return PLACEHOLDER.sub(value, text)


def plan_templates(plan, cfg, self_apply, wanted_skills):
    lang_dir = WORKFLOW / "templates" / cfg["language"]

    def rendered(src):
        return render(src.read_text(encoding="utf-8"), cfg, plan.root, plan.version,
                      str(src.relative_to(WORKFLOW))).encode("utf-8")

    if not self_apply:
        for name, kind in ROOT_TEMPLATES:
            plan.template(Path(name), rendered(lang_dir / name), kind)
        plan.template(Path(cfg["log"]), rendered(lang_dir / "log.md"), "seeded")
        plan_workflow(plan, rendered(WORKFLOW / "templates" / "github" / "check.yml"))
    for name, skill in NOTES:
        if skill is None or skill in wanted_skills:
            plan.template(Path(".claude/gw") / name, rendered(lang_dir / name), "seeded")


def plan_workflow(plan, data):
    """The CI file: .github/workflows/check.yml, migrating the workflow's own comprobar.yml (A8) to it."""
    old = plan.root / OLD_WORKFLOW
    if not old.is_file() and not old.is_symlink():
        plan.template(NEW_WORKFLOW, data, "owned")
        return
    if os.path.lexists(plan.root / NEW_WORKFLOW):
        plan.template(NEW_WORKFLOW, data, "owned")
        plan.warnings.append(f"{OLD_WORKFLOW} and {NEW_WORKFLOW} both exist; nothing is moved or deleted: keep the "
                             f"one you want and remove the other ({NEW_WORKFLOW} is the workflow's CI), or two CI "
                             f"runs start on every push")
        return
    if old.is_symlink() or header_version(old.read_bytes()) is None:
        plan.propose(NEW_WORKFLOW, data, False,
                     f"{OLD_WORKFLOW} is not workflow-owned (no galivelop-workflow header), so it is left as it is")
        plan.warnings.append(f"{OLD_WORKFLOW} looks like the project's own CI and stays; the workflow's CI is "
                             f"proposed as {NEW_WORKFLOW}{PROPOSAL}: merge it by hand, or if {OLD_WORKFLOW} is an "
                             f"old copy of the workflow's, delete it and copy the proposal over {NEW_WORKFLOW}")
        return
    plan_move(plan, OLD_WORKFLOW, NEW_WORKFLOW, "the workflow's CI file has an English name")
    plan.file(None, NEW_WORKFLOW, data=data, existing=OLD_WORKFLOW)


def personal_notes_dir():
    """The folder of the person's own notes: env GW_PERSONAL_NOTES (made absolute), else ~/.claude/gw/notas."""
    custom = config.legacy_env(NOTES_ENV, OLD_NOTES_ENV, "apply")
    if custom:
        return Path(os.path.abspath(os.path.expanduser(custom)))
    return Path(os.path.expanduser("~")) / ".claude" / "gw" / "notas"


def is_workflow_repo(root):
    """True when root is this workflow's repo (same folder as this script's repo, or a plugin.json with its name).
    Fails closed: when the workflow's own plugin.json cannot be read it cannot be told apart, so it counts as the
    workflow repo (nothing personal goes in)."""
    if root.resolve() == WORKFLOW.resolve():
        return True
    try:
        mine = json.loads((WORKFLOW / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["name"]
    except (OSError, ValueError, KeyError, TypeError):
        return True
    try:
        theirs = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")).get("name")
    except (OSError, ValueError, AttributeError):
        return False
    return theirs == mine


def workflow_gw_names(plan):
    """Lower-cased names the workflow may write directly in .claude/gw/, installed now or not: every note (optional
    ones too), its proposal, the config files, the folders, and whatever the plan already writes there."""
    names = {name for name, _skill in NOTES} | {"scripts", "schema", "gw.json", "gw.schema.json"}
    names |= {name + PROPOSAL for name in names}
    for action in plan.actions:
        parts = Path(action[1]).parts
        if parts[:2] == (".claude", "gw") and len(parts) > 2:
            names.add(parts[2])
    return {name.lower() for name in names}


def plan_personal_notes(plan, check=False):
    """Carry the person's own notes into the project's .claude/gw/: create the missing ones (with check: only say
    so, it is not drift), report (never touch) the ones that differ. Nothing happens when the folder is absent."""
    folder = personal_notes_dir()
    try:
        sources = sorted(p for p in folder.iterdir()
                         if not p.is_symlink() and p.is_file() and NOTE_NAME.fullmatch(p.name))
    except FileNotFoundError:
        return  # absent folder: nothing to carry, nothing to say
    except NotADirectoryError:
        plan.warnings.append(f"personal notes path {folder} is not a folder; point {NOTES_ENV} to a folder or remove "
                             f"the file")
        return
    except OSError as exc:
        plan.warnings.append(f"personal notes folder {folder} cannot be read ({exc.strerror}); fix its permissions "
                             f"and rerun: chmod u+rx {folder}")
        return
    reserved = workflow_gw_names(plan)
    for src in sources:
        rel = Path(".claude/gw") / src.name
        dest = plan.root / rel
        if src.name.lower().endswith(PROPOSAL):
            plan.warnings.append(f"personal note {src.name} ends in {PROPOSAL}, which doctor.py treats as a pending "
                                 f"proposal; rename it in {folder} to carry it")
            continue
        if src.name.lower() in reserved:
            plan.warnings.append(f"personal note {src.name} has the name of a workflow file ({rel}); rename it in "
                                 f"{folder} to carry it")
            continue
        try:
            data = src.read_bytes()
        except OSError as exc:
            plan.warnings.append(f"personal note {src} cannot be read ({exc.strerror}); fix its permissions and "
                                 f"rerun: chmod u+r {src}")
            continue
        try:
            if dest.is_symlink() or (dest.exists() and not dest.is_file()):
                plan.warnings.append(f"personal note {src.name}: {rel} is not a regular file; left as is")
            elif not dest.exists():
                if check:
                    plan.personal.append(f"would create personal note {src.name} as {rel}; run python3 "
                                         f"{Path(__file__).resolve()} {plan.root} without --check to create it")
                else:
                    plan.actions.append(("create", rel, data, False, "personal note"))
            elif dest.read_bytes() != data:
                plan.personal.append(f"personal note {src.name} differs from the project's {rel}, which is kept (it "
                                     f"may be adapted on purpose); see it: diff {src} {dest}")
        except OSError as exc:
            plan.warnings.append(f"personal note {src.name}: {dest} cannot be read ({exc.strerror}); fix its "
                                 f"permissions and rerun: chmod u+r {dest}")


def is_tracked(root, rel):
    code, out = git(root, "ls-files", "--", str(rel))
    return code == 0 and bool(out)


def plan_move(plan, old, new, why):
    """Plan moving old -> new (repo-relative; git mv when tracked). Fails closed when new exists."""
    old, new = Path(old), Path(new)
    if os.path.lexists(plan.root / new) or str(new) in plan.moved_to:
        raise ApplyError(f"apply: cannot move {old} to {new}: {new} already exists; merge them by hand and remove "
                         f"the old one (git mv/git rm), or keep the old paths: python3 {Path(__file__).resolve()} "
                         f"{plan.root} --keep-paths")
    plan.actions.append(("move", new, old, False, f"from {old}; {why}"))
    plan.moved_to.add(str(new))


def rewrite_under(value, old, new):
    """`value` (JSON) with every string equal to `old` or under `old/` moved under `new`. Returns (value, changed)."""
    if isinstance(value, str):
        if value == old or value.startswith(old + "/"):
            return new + value[len(old):], True
        return value, False
    changed = False
    if isinstance(value, list):
        out = []
        for item in value:
            item, c = rewrite_under(item, old, new)
            out.append(item)
            changed = changed or c
        return out, changed
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            item, c = rewrite_under(item, old, new)
            out[key] = item
            changed = changed or c
        return out, changed
    return value, False


def plan_paths(plan, cfg, keep):
    """The project paths still at their old Spanish names (a key absent and filled from the old path by config.py,
    or written explicitly as the old path) move to the English ones; with keep, the old paths are written
    explicitly instead, plus `keepLegacyPaths: true`, which later runs respect. Either way the config stops relying
    on the silent fallback. Changes cfg to match."""
    cfg_path = plan.root / config.CONFIG_REL
    try:
        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    keep = keep or raw.get("keepLegacyPaths") is True  # set by hand it means the same as --keep-paths
    schema = json.loads((WORKFLOW / "schema" / "gw.schema.json").read_text(encoding="utf-8"))
    exists = config.path_exists_fn(plan.root)
    note = "gw.json is rewritten with 2-space indent"
    found = {}  # key -> (old, new, explicit)
    repaired = []  # explicit old paths whose folder or file was already moved (by hand, or by an interrupted run)
    manual_dirs = []  # (old, new) folders already moved by hand or by an interrupted run
    for dkey in PATH_DIR_KEYS:
        dold, dnew = config.LEGACY_PATHS[dkey], schema["properties"][dkey]["default"]
        if not keep and not exists(dold) and exists(dnew):
            manual_dirs.append((dold, dnew))
    manual_files = []  # (key, where the file is now, new path): its folder moved, the file kept its old name
    for key, old in config.LEGACY_PATHS.items():
        new = schema["properties"][key]["default"]
        if key not in raw:
            if (cfg.get("_legacy") or {}).get(key) == old:
                found[key] = (old, new, False)
        elif raw[key] == old:
            now = old
            for dold, dnew in manual_dirs:
                if old.startswith(dold + "/"):
                    now = dnew + old[len(dold):]
            if not exists(new) and exists(old):
                found[key] = (old, new, True)
            elif exists(new) and not exists(old):
                repaired.append(key)
            elif now != old and now != new and exists(now) and not exists(new):
                manual_files.append((key, now, new))
    if keep:
        if not found:
            return
        written = {key: old for key, (old, _new, explicit) in found.items() if not explicit}
        for key, old in config.LEGACY_PATHS.items():  # keys that live inside a kept folder
            if key not in raw and key not in written and any(
                    old.startswith(d[0] + "/") for k, d in found.items() if k in PATH_DIR_KEYS):
                written[key] = old
        if not written and raw.get("keepLegacyPaths") is True:
            return  # nothing implicit left to write
        raw.update(written)
        raw["keepLegacyPaths"] = True
        plan.actions.append(("merge", config.CONFIG_REL, dump(raw), False,
                             f"--keep-paths: {', '.join(f'{k}={v}' for k, v in written.items())} and "
                             f"keepLegacyPaths written, so the old paths stop depending on the fallback; {note}"))
        return
    changed = bool(repaired or manual_files)
    for key in repaired:
        raw.pop(key)
        cfg[key] = schema["properties"][key]["default"]
    for key, now, new in manual_files:
        plan_move(plan, now, new, f"{key}: its folder was already moved; the file gets the English name")
        raw.pop(key)
        cfg[key] = new
    moved_dirs = list(manual_dirs)
    for key in sorted(found, key=lambda k: (k not in PATH_DIR_KEYS, k)):
        old, new, explicit = found[key]
        source = old
        for dold, dnew in moved_dirs:
            if old.startswith(dold + "/"):
                source = dnew + old[len(dold):]
        if source != new:
            plan_move(plan, source, new, f"{key}: old name, moved to the English one")
        if key in PATH_DIR_KEYS:
            moved_dirs.append((old, new))
        cfg[key] = new
        if explicit:
            raw.pop(key)  # the default is the new path
            changed = True
    for dold, dnew in moved_dirs:  # other values that point inside a moved folder follow it
        raw, moved = rewrite_under(raw, dold, dnew)
        if moved:
            changed = True
            for key in list(cfg):
                if key != "_root" and key in raw:
                    cfg[key] = raw[key]
    cfg.pop("_legacy", None)
    if changed:
        plan.actions.append(("merge", config.CONFIG_REL, dump(raw), False,
                             f"keys with the old paths dropped (the defaults are the new paths) or moved with their "
                             f"folder; {note}"))


def plan_notes(plan):
    """.claude/gw/<old skill>.md -> .claude/gw/gw-<name>.md; when both exist the new one is kept and the old reported."""
    gw = Path(".claude/gw")
    for old, new in OLD_SKILLS.items():
        src, dest = gw / f"{old}.md", gw / f"{new}.md"
        if not (plan.root / src).is_file() or (plan.root / src).is_symlink():
            continue
        if os.path.lexists(plan.root / dest):
            plan.warnings.append(f"{src} and {dest} both exist; {dest} is kept untouched and nothing is overwritten: "
                                 f"bring what you need from the old note by hand, then remove it: "
                                 f"git rm {src} (or rm {src} when untracked)")
        else:
            plan_move(plan, src, dest, "skill note renamed with the gw- prefix")


def clean_in_git(root, rel):
    """True when git tracks something under rel and nothing there is modified or untracked."""
    if not is_tracked(root, rel):
        return False
    code, out = git(root, "status", "--porcelain", "--untracked-files=all", "--ignored", "--", str(rel))
    return code == 0 and not out


def keep_message(root, rel):
    remove = f"git rm -r {rel}" if is_tracked(root, rel) else f"rm -r {rel}"
    return (f"{rel} is the old name of a workflow copy, but it is not in git or has uncommitted changes or untracked "
            f"or ignored files, so it is kept; commit or discard them and rerun, or delete it yourself: {remove}")


def plan_old_skills(plan, wanted_skills):
    """Remove the old skill folders (generated copies) of the skills that now have their gw- name."""
    for old, new in OLD_SKILLS.items():
        folder = plan.root / ".claude" / "skills" / old
        if new not in wanted_skills or not folder.is_dir() or folder.is_symlink():
            continue
        rel = Path(".claude/skills") / old
        if skill_version(folder / "SKILL.md") is None:
            plan.warnings.append(f"{rel} is not a workflow skill (no metadata.version in its SKILL.md), so it is kept "
                                 f"beside {new}; remove it if it is an old copy: git rm -r {rel}")
            continue
        if not clean_in_git(plan.root, rel):
            plan.warnings.append(keep_message(plan.root, rel))
            continue
        plan.actions.append(("remove", rel, None, False, f"replaced by .claude/skills/{new}"))


def plan_old_scripts(plan):
    """Remove the Spanish-named script copies once nothing in the project runs them (hooks, CI, config)."""
    folder = plan.root / ".claude" / "gw" / "scripts"
    old_copies = [(old, folder / old) for old in OLD_SCRIPTS if (folder / old).is_file()]
    if not old_copies:
        return
    planned = {str(a[1]): a[2] for a in plan.actions if a[2] is not None and isinstance(a[2], bytes)}
    texts = []
    for sub in (".githooks", ".github/workflows", ".claude/settings.json", ".claude/settings.local.json",
                ".claude/gw.json"):
        base = plan.root / sub
        for path in ([base] if base.is_file() else [p for p in sorted(base.rglob("*")) if p.is_file()]
                     if base.is_dir() else []):
            rel = str(path.relative_to(plan.root))
            texts.append((rel, planned[rel] if rel in planned else path.read_bytes()))
    for rel in planned:  # created files the project did not have
        if rel not in {t[0] for t in texts} and rel.startswith((".githooks/", ".github/workflows/")):
            texts.append((rel, planned[rel]))
    for old, path in old_copies:
        rel = path.relative_to(plan.root)
        if header_version(path.read_bytes()) is None:
            continue  # not generated by the workflow: left to the orphan report
        pattern = re.compile(rf"(?<![\w.-]){re.escape(old)}(?![\w-])".encode())
        users = [name for name, data in texts if pattern.search(data)]
        if users:
            plan.orphans = [o for o in plan.orphans if o != rel]  # reported below, not as deletable
            plan.warnings.append(f"{rel} is the old name of {OLD_SCRIPTS[old]} and is still run by "
                                 f"{', '.join(users)}, so it is kept; update those files (rerun with --update, or merge "
                                 f"their .gw-nuevo) and rerun apply.py to remove it")
        elif not clean_in_git(plan.root, rel):
            plan.orphans = [o for o in plan.orphans if o != rel]  # reported below, not as deletable
            plan.warnings.append(keep_message(plan.root, rel))
        else:
            plan.orphans = [o for o in plan.orphans if o != rel]
            plan.actions.append(("remove", rel, None, False, f"old name of {OLD_SCRIPTS[old]}"))


def build(root, version, update, extra_skills, cfg, personal=True, check=False, keep_paths=False):
    self_apply = root.resolve() == WORKFLOW.resolve()
    plan = Plan(root, version, update or self_apply)
    if not self_apply:  # this repo renames its own files in a later chunk of A8
        plan_paths(plan, cfg, keep_paths)
        plan_notes(plan)
    renamed = [e for e in extra_skills if e in OLD_SKILLS]
    for old in renamed:
        plan.warnings.append(f"--with {old} is the old name; use --with {OLD_SKILLS[old]}")
    extra_skills = [OLD_SKILLS.get(e, e) for e in extra_skills]
    scripts = [Path(p.name) for p in sorted((WORKFLOW / "scripts").iterdir())
               if p.is_file() and p.name not in WORKFLOW_ONLY_SCRIPTS and p.name not in IGNORED
               and not p.name.endswith(".pyc")]
    plan.tree(WORKFLOW / "scripts", Path(".claude/gw/scripts"), only=scripts)
    plan.tree(WORKFLOW / "schema", Path(".claude/gw/schema"), only=[Path("gw.schema.json")])

    available = sorted(p.name for p in (WORKFLOW / "skills").iterdir() if (p / "SKILL.md").is_file())
    unknown = sorted(set(extra_skills) - set(available))
    if unknown:
        raise ApplyError(f"apply: unknown skill(s) for --with: {', '.join(unknown)}; available: "
                         f"{', '.join(available)}")
    installed = root / ".claude" / "skills"
    old_name = {new: old for old, new in OLD_SKILLS.items()}
    wanted_skills = set()
    for name in available:
        was = old_name.get(name)  # installed under the name it had before the rename (workflow-owned copy)
        wanted = (self_apply or name in extra_skills or (installed / name / "SKILL.md").is_file()
                  or (was is not None and skill_version(installed / was / "SKILL.md") is not None)
                  or name not in OPTIONAL_SKILLS | WORKFLOW_ONLY_SKILLS)
        if not wanted:
            continue
        wanted_skills.add(name)
        dest = Path(".claude/skills") / name
        owner = skill_version(root / dest / "SKILL.md")
        plan.tree(WORKFLOW / "skills" / name, dest, owner_version=owner, owned=owner is not None)
    # Skills adapted from Matt Pocock's say "license: MIT (see LICENSE-mattpocock-skills)": the file goes with them.
    if not self_apply:
        plan_old_skills(plan, wanted_skills)
    if any(SKILL_LICENSE in (WORKFLOW / "skills" / n / "SKILL.md").read_text(encoding="utf-8") for n in wanted_skills):
        plan.file(WORKFLOW / SKILL_LICENSE, Path(".claude/skills") / SKILL_LICENSE)

    hooks_src = WORKFLOW / "templates" / "githooks"
    names = files_under(hooks_src)
    for name in names:
        plan.file(hooks_src / name, Path(".githooks") / name)
    for name in files_under(root / ".githooks"):
        if name not in names and header_version((root / ".githooks" / name).read_bytes()):
            plan.orphans.append(Path(".githooks") / name)

    plan.settings(WORKFLOW / "templates" / "claude" / "settings.json")
    plan_templates(plan, cfg, self_apply, wanted_skills)
    if not self_apply:
        plan_old_scripts(plan)
    if personal and not is_workflow_repo(root):
        plan_personal_notes(plan, check)
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
        print(f"apply: pending proposal {rel}{PROPOSAL} ({rel} differs: {why}); merge it by hand and delete it: "
              f"rm {rel}{PROPOSAL}")
    for rel in plan.orphans:
        print(f"apply: {rel} is no longer in the workflow (kept); delete it if nothing uses it: git rm {rel}")
    for note in plan.notes:
        print(f"apply: template update: {note}")
    for rel, current, data in plan.diffs:
        print(f"apply: {rel} exists and is never written; what differs from the v{plan.version} template (bring the "
              f"missing rules by hand, then set its first line to <!-- galivelop-workflow v{plan.version} -->):")
        diff = list(difflib.unified_diff(current.decode("utf-8", "replace").splitlines(),
                                         data.decode("utf-8", "replace").splitlines(),
                                         f"{rel} (project)", f"{rel} (template)", lineterm=""))
        for line in diff[:DIFF_LINES]:
            print(f"  {line}")
        if len(diff) > DIFF_LINES:
            print(f"  … {len(diff) - DIFF_LINES} more line(s)")
    for line in plan.personal:
        print(f"apply: {line}")
    for warning in plan.warnings:
        print(f"apply: WARNING: {warning}")
    if plan.hooks_path:
        print(f"apply: {plan.hooks_path}")


def move(root, old, new):
    """old -> new under root: git mv when git tracks something there (a folder moves whole, tracked or not)."""
    (root / new).parent.mkdir(parents=True, exist_ok=True)
    if is_tracked(root, old):
        code, out = git(root, "mv", str(old), str(new))
        if code != 0:
            raise ApplyError(f"apply: git mv {old} {new} failed ({out}); do it by hand and rerun: "
                             f"git mv {old} {new}")
    else:
        os.rename(root / old, root / new)


def apply(plan):
    if any(sensitive(a[1]) for a in plan.actions):
        print("apply: note: Claude Code's auto mode may ask for permission to edit .claude/settings.json, "
              ".claude/gw/scripts/ and .githooks/; approve it, or run this script yourself: "
              f"python3 {Path(__file__).resolve()} {plan.root}")
    for kind, rel, old, _exec, _detail in plan.actions:
        if kind == "move":
            move(plan.root, old, rel)
    for kind, rel, data, want_exec, _detail in plan.actions:
        dest = plan.root / rel
        if kind == "move":
            continue
        if kind == "remove":
            if dest.is_dir() and not dest.is_symlink():
                shutil.rmtree(dest)
            else:
                dest.unlink()
            continue
        if kind != "chmod":
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        if want_exec:
            dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if plan.set_hooks_path:
        code, _ = git(plan.root, "config", "core.hooksPath", ".githooks")
        if code != 0:
            print("apply: could not set core.hooksPath; set it by hand: git config core.hooksPath .githooks")


def init_config(args, version):
    """The new .claude/gw.json: templates/gw.json with the flags on top. Raises ApplyError when invalid."""
    if not args.check_commands:
        raise ApplyError("apply: --init needs the project's check, at least one --check-command \"<command>\" "
                         "(e.g. --check-command \"npm test\"); rerun with it")
    new = json.loads((WORKFLOW / "templates" / "gw.json").read_text(encoding="utf-8"))
    new["version"] = version
    if args.language:
        new["language"] = args.language
    new["log"] = args.log or LOG_BY_LANGUAGE.get(new["language"], new["log"])
    new["check"] = args.check_commands
    new["install"] = args.install
    for key, flag in (("protectedBranch", args.protected_branch), ("pushToProtected", args.push_to_protected),
                      ("reviewMark", args.review_mark), ("content", args.content or None),
                      ("visibleLanguages", args.visible_languages or None),
                      ("designReferences", args.design_references or None)):
        if flag:
            new[key] = flag
    if args.require_retro is not None:
        new["requireRetro"] = args.require_retro == "true"
    if args.agent_signatures is not None:
        new["agentSignatures"] = args.agent_signatures == "true"
    schema = json.loads((WORKFLOW / "schema" / "gw.schema.json").read_text(encoding="utf-8"))
    errors = config.validate(new, schema)
    if errors:
        raise ApplyError("apply: the config --init would write is invalid:\n  " + "\n  ".join(errors)
                         + "\napply: fix the flags and rerun")
    return new, schema


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", nargs="?", help="the project (default: git top level of the current directory)")
    parser.add_argument("--update", action="store_true", help="replace local edits in workflow-owned files")
    parser.add_argument("--check", action="store_true", help="no writes; exit 1 if the copy differs")
    parser.add_argument("--dry-run", action="store_true", help="print the plan, no writes")
    parser.add_argument("--no-personal-notes", dest="no_personal", action="store_true",
                        help=f"do not carry the personal notes (env {NOTES_ENV}, default ~/.claude/gw/notas/)")
    parser.add_argument("--with", dest="extra", action="append", default=[], metavar="SKILL",
                        help="also install an optional skill (repeatable)")
    parser.add_argument("--keep-paths", action="store_true",
                        help="a project still on the old Spanish paths (docs/traspaso.md, docs/registros/...) keeps "
                             "them: they are written explicitly in .claude/gw.json instead of being moved")
    init = parser.add_argument_group("--init (write .claude/gw.json first, only when it does not exist)")
    init.add_argument("--init", action="store_true", help="write .claude/gw.json from templates/gw.json + flags")
    init.add_argument("--language", choices=["es", "en"])
    init.add_argument("--log", metavar="PATH")
    init.add_argument("--check-command", dest="check_commands", action="append", default=[], metavar="CMD",
                      help="a `check` command (repeatable; at least one)")
    init.add_argument("--install", action="append", default=[], metavar="CMD", help="an `install` command (repeatable)")
    init.add_argument("--protected-branch", metavar="BRANCH")
    init.add_argument("--push-to-protected", choices=["direct", "pr"])
    init.add_argument("--require-retro", choices=["true", "false"],
                      help="reviewed.sh requires a decided retro on the branch (default: false)")
    init.add_argument("--agent-signatures", choices=["true", "false"],
                      help="false: the commit-msg hook rejects agent signatures in commit messages (default: true)")
    init.add_argument("--visible-language", dest="visible_languages", action="append", default=[], metavar="LANG",
                      help="a language every user-visible text must exist in (repeatable)")
    init.add_argument("--design-reference", dest="design_references", action="append", default=[], metavar="REF",
                      help="a product or standard design proposals are contrasted with (repeatable)")
    init.add_argument("--content", action="append", default=[], metavar="REGEX", help="a `content` regex (repeatable)")
    init.add_argument("--review-mark", metavar="PATH")
    args = parser.parse_args(config.legacy_flags(sys.argv[1:] if argv is None else argv, OLD_FLAGS, "apply"))
    init_flags = [f for f, v in (("--language", args.language), ("--log", args.log),
                                 ("--check-command", args.check_commands), ("--install", args.install),
                                 ("--protected-branch", args.protected_branch),
                                 ("--push-to-protected", args.push_to_protected), ("--content", args.content),
                                 ("--review-mark", args.review_mark), ("--require-retro", args.require_retro),
                                 ("--agent-signatures", args.agent_signatures),
                                 ("--visible-language", args.visible_languages),
                                 ("--design-reference", args.design_references)) if v]
    if init_flags and not args.init:
        parser.error(f"{', '.join(init_flags)} only go with --init")
    if args.init and args.check:
        parser.error("--init writes files; run --check after it")

    start = args.project or os.getcwd()
    root = config.git_toplevel(start)
    if root is None:
        print(f"apply: {start} is not inside a git repository; create it first: git init {start}", file=sys.stderr)
        return 2
    root = root.resolve()
    version = workflow_version()
    cfg = None
    if args.init:
        if (root / config.CONFIG_REL).is_file():
            print(f"apply: {root / config.CONFIG_REL} already exists; left as is (the --init flags are ignored)")
        else:
            try:
                new, schema = init_config(args, version)
            except ApplyError as exc:
                print(exc, file=sys.stderr)
                return 2
            text = json.dumps(new, indent=2, ensure_ascii=False) + "\n"
            if args.dry_run:
                print(f"apply: --init would write {root / config.CONFIG_REL}:\n{text}", end="")
                cfg = config.with_defaults(new, schema)
                cfg["_root"] = root
            else:
                (root / ".claude").mkdir(parents=True, exist_ok=True)
                (root / config.CONFIG_REL).write_text(text, encoding="utf-8")
                print(f"apply: wrote {root / config.CONFIG_REL}")
    if cfg is None and not (root / config.CONFIG_REL).is_file():
        print(f"apply: {root / config.CONFIG_REL} not found, so the workflow cannot be applied; create it "
              f"with --init, or by hand from {WORKFLOW / 'templates' / 'gw.json'}: python3 {Path(__file__).resolve()} "
              f"{root} --init --check-command \"<the project's check>\" (by hand, validate it: python3 "
              f"{HERE / 'config.py'} --root {root} validate)", file=sys.stderr)
        return 2
    if cfg is None:
        try:
            cfg = config.load(str(root))
        except config.ConfigError as exc:
            print(f"apply: {exc}\napply: fix it and validate: python3 {HERE / 'config.py'} --root {root} validate",
                  file=sys.stderr)
            return 2
    try:
        plan = build(root, version, args.update, args.extra, cfg, not args.no_personal, args.check, args.keep_paths)
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
            print(f"apply: the workflow copy in {root} differs from the workflow v{version} (above); bring it up "
                  f"to date: python3 {Path(__file__).resolve()} {root}")
            return 1
        print(f"apply: workflow copy in sync with v{version}")
        return 0
    if args.dry_run:
        print(f"apply: plan for {root} (workflow v{version}, dry run, nothing written):")
        for line in lines:
            print(line)
        if not lines:
            print("  nothing to do")
        report(plan)
        return 0
    if not lines:
        print(f"apply: nothing to do; {root} is at workflow v{version}")
        report(plan)
        return 0
    print(f"apply: applying workflow v{version} to {root}:")
    for line in lines:
        print(line)
    try:
        apply(plan)
    except ApplyError as exc:
        print(exc, file=sys.stderr)
        return 2
    report(plan)
    for rel, rule in ignored_paths(root):
        print(f"apply: WARNING: git ignores {rel} ({rule}), so the commit would leave it out; add !{rel} to "
              f".gitignore and check: git check-ignore -v {rel}")
    if cfg.get("version") != version:
        print(f"apply: .claude/gw.json says version {cfg.get('version')}; set it to {version} once the "
              f"proposals are reviewed: edit \"version\" in {root / config.CONFIG_REL}")
    if any(a[0] == "propose" for a in plan.actions):
        print(f"apply: review each *{PROPOSAL} (merge by hand, then delete it) before committing")
    if cfg.get("language") == "es":
        title, nxt = f"Flujo Galivelop-workflow v{version}", "Siguiente: <próximo paso concreto>"
    else:
        title, nxt = f"Galivelop-workflow v{version} workflow", "Next: <next concrete step>"
    print("apply: nothing was committed; suggested commit (fill in the last line):")
    print(f"  git add -A && git commit -m \"{title}\" -m \"{nxt}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
