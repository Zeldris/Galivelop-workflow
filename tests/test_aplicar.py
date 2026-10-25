"""scripts/aplicar.py on temporary projects: a fresh apply passes doctor.py, a second run does nothing, owned files
are updated by version, foreign or locally edited ones get a .gw-nuevo proposal, settings.json is merged without
losing anything, optional skills come only with --with, and core.hooksPath is respected. HOME is a temp folder and
git runs isolated as in test_ganchos.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_ganchos import BASE_CONFIG, ROOT

APLICAR = ROOT / "scripts" / "aplicar.py"
VERSION = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]


class Fixture:
    """A git repo with a valid .claude/gw.json and what doctor.py needs besides the workflow copy and templates."""

    def __init__(self, tmp, config=None):
        self.work = tmp / "work"
        home = tmp / "home"
        home.mkdir()
        gitconfig = tmp / "gitconfig"
        gitconfig.write_text("[user]\n\tname = Test\n\temail = test@example.com\n[commit]\n\tgpgsign = false\n"
                             "[init]\n\tdefaultBranch = main\n")
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith("GIT_") and k not in ("CLAUDECODE", "CLAUDE_PROJECT_DIR", "CLAUDE_CODE_REMOTE")}
        self.env.update(GIT_CONFIG_GLOBAL=str(gitconfig), GIT_CONFIG_NOSYSTEM="1", TMPDIR=str(tmp), HOME=str(home),
                        GW_NOTAS_PERSONALES=str(tmp / "no-personal-notes"))  # never the real ~/.claude/gw/notas
        self.run("git", "init", "-q", str(self.work), cwd=tmp)
        self.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, **(config or {})), indent=2) + "\n")
        self.write("check.sh", "exit 0\n")
        # The project's own log (no marker): aplicar.py must leave it alone. AGENTS.md and the CI file come from the
        # workflow's templates (tests/test_plantillas.py).
        self.write("docs/log.md", "# Log\n\n| Field | Value |\n|---|---|\n| Next step | write tests |\n")

    def run(self, *cmd, cwd=None):
        r = subprocess.run(list(cmd), cwd=str(cwd or self.work), env=self.env, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL)
        return r.returncode, r.stdout + r.stderr

    def aplicar(self, *args):
        return self.run("python3", str(APLICAR), str(self.work), *args)

    def write(self, rel, text):
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def read(self, rel):
        return (self.work / rel).read_text()

    def hooks_path(self):
        return self.run("git", "config", "--get", "core.hooksPath")[1].strip()


class Aplicar(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-aplicar-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)

    def applied(self, *args):
        code, out = self.p.aplicar(*args)
        self.assertEqual(code, 0, out)
        return out

    def test_fresh_apply_passes_doctor_and_is_idempotent(self):
        p = self.p
        out = self.applied()
        self.assertIn("auto mode may ask for permission", out)
        self.assertIn("git add -A && git commit", out)
        self.assertIn(f"Galivelop-workflow v{VERSION} workflow", out)
        self.assertIn("Next:", out)
        scripts = p.work / ".claude" / "gw" / "scripts"
        self.assertTrue((scripts / "doctor.py").is_file())
        self.assertTrue(os.access(str(scripts / "session-start.sh"), os.X_OK))
        self.assertFalse((scripts / "aplicar.py").exists())
        self.assertFalse((scripts / "recoger.py").exists())
        self.assertFalse((scripts / "version.py").exists())  # workflow-only, like recoger.py and aplicar.py
        self.assertTrue((p.work / ".claude" / "gw" / "schema" / "gw.schema.json").is_file())
        self.assertTrue(os.access(str(p.work / ".githooks" / "pre-push"), os.X_OK))
        self.assertTrue((p.work / ".claude" / "skills" / "selector" / "SKILL.md").is_file())
        self.assertFalse((p.work / ".claude" / "skills" / "gw-harvest").exists())
        self.assertEqual(p.read(".claude/skills/LICENSE-mattpocock-skills"),
                         (ROOT / "LICENSE-mattpocock-skills").read_text())  # the license the adapted skills cite
        self.assertEqual(p.hooks_path(), ".githooks")
        self.assertFalse(list(p.work.rglob("__pycache__")))

        code, out = p.run("python3", str(scripts / "doctor.py"), cwd=p.work)
        self.assertEqual(code, 0, out)
        self.assertNotIn("FAIL", out)

        out = self.applied()
        self.assertIn("nothing to do", out)
        self.assertNotIn("auto mode", out)
        code, out = p.aplicar("--check")
        self.assertEqual(code, 0, out)
        self.assertIn("in sync", out)

    def test_check_and_dry_run_do_not_write(self):
        p = self.p
        code, out = p.aplicar("--check")
        self.assertEqual(code, 1, out)
        self.assertIn("create  .githooks/pre-push", out)
        code, out = p.aplicar("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("dry run", out)
        self.assertFalse((p.work / ".githooks").exists())
        self.assertFalse((p.work / ".claude" / "settings.json").exists())
        self.assertEqual(p.hooks_path(), "")

    def test_owned_script_older_header_is_updated(self):
        p = self.p
        self.applied()
        rel = ".claude/gw/scripts/revisado.sh"
        original = p.read(rel)
        p.write(rel, original.replace(f"galivelop-workflow v{VERSION}", "galivelop-workflow v0.0.1") + "# local\n")
        out = self.applied()
        self.assertIn(f"update  {rel}", out)
        self.assertEqual(p.read(rel), original)
        self.assertFalse((p.work / (rel + ".gw-nuevo")).exists())

    def test_same_version_local_edits_give_a_proposal_unless_update(self):
        p = self.p
        self.applied()
        rel = ".claude/gw/scripts/revisado.sh"
        original = p.read(rel)
        p.write(rel, original + "# local edit\n")
        out = self.applied()
        self.assertIn(f"propose {rel}.gw-nuevo", out)
        self.assertIn("local edits or an older copy of that version", out)
        self.assertIn(f"diff {rel} {rel}.gw-nuevo", out)
        self.assertIn("# local edit", p.read(rel))
        self.assertEqual(p.read(rel + ".gw-nuevo"), original)
        out = self.applied()
        self.assertIn("nothing to do", out)
        self.assertIn("pending proposal", out)
        code, out = p.aplicar("--check")
        self.assertEqual(code, 1, out)
        out = self.applied("--update")
        self.assertIn(f"update  {rel}", out)
        self.assertEqual(p.read(rel), original)

    def test_git_ignored_workflow_files_are_warned_about(self):
        self.p.write(".gitignore", ".githooks/\n")
        out = self.applied()
        self.assertIn("WARNING: git ignores .githooks/pre-push (.gitignore:1:.githooks/)", out)
        self.assertIn("git check-ignore -v .githooks/pre-push", out)

    def test_older_flow_hook_in_settings_is_listed(self):
        p = self.p
        self.applied()
        settings = json.loads(p.read(".claude/settings.json"))
        settings["hooks"]["SessionStart"].append(
            {"matcher": "startup", "hooks": [{"type": "command", "command": "bash .claude/hooks/session-start.sh"}]})
        p.write(".claude/settings.json", json.dumps(settings))
        p.write(".claude/hooks/session-start.sh", f"#!/usr/bin/env bash\n# galivelop-workflow v{VERSION}\ntrue\n")
        out = self.applied()
        self.assertIn("WARNING: .claude/settings.json SessionStart also runs 'bash .claude/hooks/session-start.sh'", out)

    def test_older_stop_hook_in_settings_is_listed(self):
        p = self.p
        self.applied()
        settings = json.loads(p.read(".claude/settings.json"))
        settings["hooks"]["Stop"].append(
            {"hooks": [{"type": "command", "command": "python3 .claude/hooks/antes-de-parar.py"}]})
        p.write(".claude/settings.json", json.dumps(settings))
        p.write(".claude/hooks/antes-de-parar.py", f"#!/usr/bin/env python3\n# galivelop-workflow v{VERSION}\n")
        out = self.applied()
        self.assertIn("WARNING: .claude/settings.json Stop also runs 'python3 .claude/hooks/antes-de-parar.py'", out)

    def test_config_guard_is_applied_once_with_its_own_matcher(self):
        p = self.p
        out = self.applied()
        self.assertTrue((p.work / ".claude/gw/scripts/guardia-config.py").is_file(), out)
        s = json.loads(p.read(".claude/settings.json"))
        guards = [e for e in s["hooks"]["PreToolUse"]
                  if any("guardia-config.py" in h["command"] for h in e["hooks"])]
        self.assertEqual(len(guards), 1, s["hooks"]["PreToolUse"])
        self.assertEqual(guards[0]["matcher"], "Edit|Write|MultiEdit|NotebookEdit|Bash")
        before = p.read(".claude/settings.json")
        self.applied()
        self.assertEqual(p.read(".claude/settings.json"), before, "a second run adds nothing")

    def test_subagent_cap_is_applied_once_with_its_own_matcher(self):
        p = self.p
        out = self.applied()
        self.assertTrue((p.work / ".claude/gw/scripts/tope-subagentes.py").is_file(), out)
        s = json.loads(p.read(".claude/settings.json"))
        caps = [e for e in s["hooks"]["PreToolUse"]
                if any("tope-subagentes.py" in h["command"] for h in e["hooks"])]
        self.assertEqual(len(caps), 1, s["hooks"]["PreToolUse"])
        self.assertEqual(caps[0]["matcher"], "Agent|Task")
        before = p.read(".claude/settings.json")
        self.applied()
        self.assertEqual(p.read(".claude/settings.json"), before, "a second run adds nothing")

    def test_project_own_script_with_a_flow_name_is_not_listed(self):
        p = self.p
        self.applied()
        settings = json.loads(p.read(".claude/settings.json"))
        settings["hooks"]["SessionStart"].append(
            {"matcher": "startup", "hooks": [{"type": "command", "command": "bash .claude/hooks/session-start.sh"}]})
        p.write(".claude/settings.json", json.dumps(settings))
        p.write(".claude/hooks/session-start.sh", "#!/usr/bin/env bash\necho mine\n")
        self.assertNotIn("also runs", self.applied())

    def test_locally_newer_owned_file_is_never_overwritten(self):
        p = self.p
        self.applied()
        rel = ".claude/gw/scripts/revisado.sh"
        newer = p.read(rel).replace(f"galivelop-workflow v{VERSION}", "galivelop-workflow v99.0.0")
        p.write(rel, newer)
        out = self.applied("--update")
        self.assertIn("newer than the workflow", out)
        self.assertEqual(p.read(rel), newer)

    def test_foreign_pre_push_gets_a_proposal(self):
        p = self.p
        foreign = "#!/bin/sh\necho mine\n"
        p.write(".githooks/pre-push", foreign)
        out = self.applied("--update")
        self.assertIn("propose .githooks/pre-push.gw-nuevo", out)
        self.assertIn("not workflow-owned", out)
        self.assertEqual(p.read(".githooks/pre-push"), foreign)
        self.assertEqual(p.read(".githooks/pre-push.gw-nuevo"), (ROOT / "templates/githooks/pre-push").read_text())

    def test_foreign_commit_msg_gets_a_proposal_and_the_hook_is_installed(self):
        p = self.p
        foreign = "#!/bin/sh\necho mine\n"
        p.write(".githooks/commit-msg", foreign)
        out = self.applied("--update")
        self.assertIn("propose .githooks/commit-msg.gw-nuevo", out)
        self.assertEqual(p.read(".githooks/commit-msg"), foreign)
        self.assertEqual(p.read(".githooks/commit-msg.gw-nuevo"), (ROOT / "templates/githooks/commit-msg").read_text())

    def test_commit_msg_is_installed_and_named_in_the_chain_hint(self):
        p = self.p
        p.run("git", "config", "core.hooksPath", ".husky")
        out = self.applied()
        self.assertEqual(p.read(".githooks/commit-msg"), (ROOT / "templates/githooks/commit-msg").read_text())
        self.assertIn("/commit-msg", out)

    def test_owned_skill_older_version_is_updated_and_orphans_reported(self):
        p = self.p
        self.applied()
        skill = p.work / ".claude" / "skills" / "selector"
        original = (skill / "SKILL.md").read_text()
        (skill / "SKILL.md").write_text(original.replace(f'version: "{VERSION}"', 'version: "0.0.1"'))
        (skill / "OLD.md").write_text("gone upstream\n")
        out = self.applied()
        self.assertIn("update  .claude/skills/selector/SKILL.md", out)
        self.assertEqual((skill / "SKILL.md").read_text(), original)
        self.assertIn(".claude/skills/selector/OLD.md is no longer in the workflow", out)
        self.assertTrue((skill / "OLD.md").exists())

    def test_settings_merge_keeps_the_users_and_adds_ours_once(self):
        p = self.p
        mine = {"model": "opus", "env": {"MY_VAR": "1", "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "100000"},
                "hooks": {"SessionStart": [{"matcher": "startup", "hooks": [{"type": "command", "command": "echo hi"}]}],
                          "Stop": [{"hooks": [{"type": "command", "command": "echo bye"}]}]}}
        p.write(".claude/settings.json", json.dumps(mine))
        out = self.applied()
        self.assertIn("merge   .claude/settings.json", out)
        s = json.loads(p.read(".claude/settings.json"))
        self.assertEqual(s["model"], "opus")
        self.assertEqual(s["env"], {"MY_VAR": "1", "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "100000"})
        self.assertEqual(s["hooks"]["Stop"][0]["hooks"][0], mine["hooks"]["Stop"][0]["hooks"][0])  # theirs first
        self.assertEqual(s["hooks"]["SessionStart"][0], mine["hooks"]["SessionStart"][0])
        commands = [h["command"] for e in s["hooks"]["SessionStart"] + s["hooks"]["PreToolUse"] + s["hooks"]["Stop"]
                    for h in e["hooks"]]
        for script in ("session-start.sh", "recuperar.py --estado", "revision-antes-de-main.sh", "antes-de-parar.py",
                       "guardia-config.py", "tope-subagentes.py"):
            self.assertEqual(sum(script in c for c in commands), 1, commands)
        self.assertTrue(p.read(".claude/settings.json").endswith("}\n"))
        before = p.read(".claude/settings.json")
        out = self.applied()
        self.assertIn("nothing to do", out)
        self.assertEqual(p.read(".claude/settings.json"), before)

    def test_optional_skills_only_with_with(self):
        p = self.p
        self.applied()
        skills = p.work / ".claude" / "skills"
        self.assertFalse((skills / "opt-ai").exists())
        self.assertFalse((skills / "scout-updates").exists())
        out = self.applied("--with", "opt-ai")
        self.assertIn("create  .claude/skills/opt-ai/SKILL.md", out)
        self.assertFalse((skills / "scout-updates").exists())
        self.assertIn("nothing to do", self.applied())  # an installed optional skill stays managed
        code, out = p.aplicar("--with", "nope")
        self.assertEqual(code, 2, out)
        self.assertIn("unknown skill", out)

    def test_no_config_fails_closed(self):
        p = self.p
        (p.work / ".claude" / "gw.json").unlink()
        code, out = p.aplicar()
        self.assertEqual(code, 2, out)
        self.assertIn("gw.json not found", out)
        self.assertIn("config.py", out)
        self.assertFalse((p.work / ".githooks").exists())
        p.write(".claude/gw.json", json.dumps({"version": "0.1.0"}))
        code, out = p.aplicar()
        self.assertEqual(code, 2, out)
        self.assertIn("invalid", out)

    def test_other_hooks_path_is_respected(self):
        p = self.p
        p.run("git", "config", "core.hooksPath", ".husky")
        out = self.applied()
        self.assertEqual(p.hooks_path(), ".husky")
        self.assertIn("another hook manager", out)
        self.assertIn(".husky/pre-push", out)
        code, out = p.aplicar("--check")
        self.assertEqual(code, 0, out)  # a local git setting is not drift of the copy

    def test_spanish_project_commit_message(self):
        (self.tmp / "es").mkdir()
        p = Fixture(self.tmp / "es", {"language": "es"})
        code, out = p.aplicar()
        self.assertEqual(code, 0, out)
        self.assertIn(f"Flujo Galivelop-workflow v{VERSION}", out)
        self.assertIn("Siguiente:", out)


class NotasPersonales(unittest.TestCase):
    """Personal notes: regular files of GW_NOTAS_PERSONALES (default ~/.claude/gw/notas) copied to
    <project>/.claude/gw/ when missing; a differing one is reported and never touched."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-notas-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)
        self.notas = self.tmp / "notas"
        self.p.env["GW_NOTAS_PERSONALES"] = str(self.notas)

    def note(self, name, text="my note\n"):
        self.notas.mkdir(exist_ok=True)
        (self.notas / name).write_text(text)
        return self.notas / name

    def target(self, name):
        return self.p.work / ".claude" / "gw" / name

    def applied(self, *args):
        code, out = self.p.aplicar(*args)
        self.assertEqual(code, 0, out)
        return out

    def test_absent_folder_does_nothing_and_says_nothing(self):
        self.assertNotIn("personal", self.applied())
        self.assertEqual(self.p.aplicar("--check")[0], 0)

    def test_folder_pointing_to_a_missing_path_does_nothing(self):
        self.p.env["GW_NOTAS_PERSONALES"] = str(self.tmp / "nope" / "missing")
        self.assertNotIn("personal", self.applied())
        self.assertFalse((self.tmp / "nope").exists())

    def test_empty_folder_does_nothing(self):
        self.notas.mkdir()
        self.assertNotIn("personal", self.applied())

    def test_default_folder_is_under_the_home_dir(self):
        folder = Path(self.p.env["HOME"]) / ".claude" / "gw" / "notas"  # the fixture's HOME, never the real one
        folder.mkdir(parents=True)
        (folder / "from-home.md").write_text("home note\n")
        del self.p.env["GW_NOTAS_PERSONALES"]
        out = self.applied()
        self.assertIn("personal note", out)
        self.assertEqual(self.target("from-home.md").read_text(), "home note\n")

    def test_missing_note_is_created_and_reported(self):
        self.note("style.md", "I like short answers\n")
        out = self.applied()
        self.assertEqual(self.target("style.md").read_text(), "I like short answers\n")
        self.assertIn("personal note", out)
        self.assertIn("style.md", out)
        self.assertFalse((self.p.work / ".claude" / "gw" / "style.md.gw-nuevo").exists())
        self.assertNotIn("personal", self.applied())  # second run: identical, silent

    def test_identical_note_is_silent_and_check_passes(self):
        self.note("style.md")
        self.applied()
        code, out = self.p.aplicar("--check")
        self.assertEqual(code, 0, out)
        self.assertNotIn("personal", out)

    def test_different_note_is_reported_untouched_and_check_still_passes(self):
        src = self.note("style.md", "mine\n")
        self.applied()
        self.target("style.md").write_text("adapted for this project\n")
        want = f"diff {src} {self.target('style.md')}"
        out = self.applied()
        self.assertEqual(self.target("style.md").read_text(), "adapted for this project\n")
        self.assertFalse((self.p.work / ".claude" / "gw" / "style.md.gw-nuevo").exists())
        self.assertIn("personal note", out)
        self.assertIn(want, out)
        code, out = self.p.aplicar("--check")
        self.assertEqual(code, 0, out)
        self.assertIn(want, out)

    def test_dry_run_and_check_write_nothing(self):
        self.note("style.md")
        out = self.applied("--dry-run")
        self.assertIn("style.md", out)
        self.assertIn("personal note", out)
        self.assertFalse(self.target("style.md").exists())
        code, out = self.p.aplicar("--check")
        self.assertEqual(code, 1, out)  # a missing note is something to create
        self.assertIn("style.md", out)
        self.assertFalse(self.target("style.md").exists())

    def test_symlink_dotfile_subfolder_and_bad_names_are_skipped(self):
        real = self.note("real.md")
        (self.notas / "link.md").symlink_to(real)
        for bad in (".hidden.md", "-dash.md", "bad name.md", "a$b.md", "é.md"):
            self.note(bad)
        (self.notas / "sub").mkdir()
        (self.notas / "sub" / "inner.md").write_text("x\n")
        (self.notas / "dir.md").mkdir()
        self.note("1.v2-x.txt")
        self.note("a_b.md")
        self.applied()
        created = sorted(p.name for p in (self.p.work / ".claude" / "gw").iterdir()
                         if p.name in {"real.md", "link.md", ".hidden.md", "-dash.md", "bad name.md", "a$b.md",
                                       "é.md", "sub", "inner.md", "dir.md", "1.v2-x.txt", "a_b.md"})
        self.assertEqual(created, ["1.v2-x.txt", "a_b.md", "real.md"])

    def test_workflow_repo_itself_never_gets_personal_notes(self):
        self.note("style.md")
        code, out = self.p.run("python3", str(APLICAR), str(ROOT), "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertNotIn("style.md", out)
        self.assertNotIn("personal", out)

    def test_a_project_with_this_workflows_plugin_json_is_skipped(self):
        self.note("style.md")
        self.p.write(".claude-plugin/plugin.json", json.dumps({"name": "galivelop-workflow", "version": VERSION}))
        self.assertNotIn("personal", self.applied())
        self.assertFalse(self.target("style.md").exists())

    def test_a_project_with_another_plugin_json_gets_the_notes(self):
        self.note("style.md")
        self.p.write(".claude-plugin/plugin.json", json.dumps({"name": "something-else", "version": "1.0.0"}))
        self.applied()
        self.assertTrue(self.target("style.md").is_file())

    def test_opt_out_flag(self):
        self.note("style.md")
        self.assertNotIn("personal", self.applied("--sin-notas-personales"))
        self.assertFalse(self.target("style.md").exists())
        self.assertEqual(self.p.aplicar("--check", "--sin-notas-personales")[0], 0)

    def test_target_that_is_not_a_regular_file_is_reported_not_replaced(self):
        self.note("style.md")
        self.target("style.md").mkdir(parents=True)
        out = self.applied()
        self.assertTrue(self.target("style.md").is_dir())
        self.assertIn("personal note", out)
        self.assertIn("not a regular file", out)

    def test_help_mentions_the_notes_and_the_flag(self):
        code, out = self.p.run("python3", str(APLICAR), "--help")
        self.assertEqual(code, 0, out)
        self.assertIn("GW_NOTAS_PERSONALES", out)
        self.assertIn("--sin-notas-personales", out)


if __name__ == "__main__":
    unittest.main()
