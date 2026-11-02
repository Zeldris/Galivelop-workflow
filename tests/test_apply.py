"""scripts/apply.py on temporary projects: a fresh apply passes doctor.py, a second run does nothing, owned files
are updated by version, foreign or locally edited ones get a .gw-new proposal, settings.json is merged without
losing anything, optional skills come only with --with, and core.hooksPath is respected. HOME is a temp folder and
git runs isolated as in test_hooks.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT

APPLY_SCRIPT = ROOT / "scripts" / "apply.py"
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
                        GW_PERSONAL_NOTES=str(tmp / "no-personal-notes"))  # never the real ~/.claude/gw/notas
        self.run("git", "init", "-q", str(self.work), cwd=tmp)
        self.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, **(config or {})), indent=2) + "\n")
        self.write("check.sh", "exit 0\n")
        # The project's own log (no marker): apply.py must leave it alone. AGENTS.md and the CI file come from the
        # workflow's templates (tests/test_templates.py).
        self.write("docs/log.md", "# Log\n\n| Field | Value |\n|---|---|\n| Next step | write tests |\n")

    def run(self, *cmd, cwd=None):
        r = subprocess.run(list(cmd), cwd=str(cwd or self.work), env=self.env, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL)
        return r.returncode, r.stdout + r.stderr

    def run_apply(self, *args):
        return self.run("python3", str(APPLY_SCRIPT), str(self.work), *args)

    def write(self, rel, text):
        path = self.work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def read(self, rel):
        return (self.work / rel).read_text()

    def hooks_path(self):
        return self.run("git", "config", "--get", "core.hooksPath")[1].strip()


class Apply(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-apply-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)

    def applied(self, *args):
        code, out = self.p.run_apply(*args)
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
        self.assertFalse((scripts / "apply.py").exists())
        self.assertFalse((scripts / "harvest.py").exists())
        self.assertFalse((scripts / "version.py").exists())  # workflow-only, like harvest.py and apply.py
        self.assertTrue((p.work / ".claude" / "gw" / "schema" / "gw.schema.json").is_file())
        self.assertTrue(os.access(str(p.work / ".githooks" / "pre-push"), os.X_OK))
        self.assertTrue((p.work / ".claude" / "skills" / "gw-selector" / "SKILL.md").is_file())
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
        code, out = p.run_apply("--check")
        self.assertEqual(code, 0, out)
        self.assertIn("in sync", out)

    def test_check_and_dry_run_do_not_write(self):
        p = self.p
        code, out = p.run_apply("--check")
        self.assertEqual(code, 1, out)
        self.assertIn("create  .githooks/pre-push", out)
        code, out = p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("dry run", out)
        self.assertFalse((p.work / ".githooks").exists())
        self.assertFalse((p.work / ".claude" / "settings.json").exists())
        self.assertEqual(p.hooks_path(), "")

    def test_loose_proposal_with_the_old_suffix_is_recognized_with_a_warning(self):
        p = self.p
        self.applied()
        rel = ".claude/gw/scripts/reviewed.sh"
        original = p.read(rel)
        p.write(rel, original + "# local edit\n")
        p.write(rel + ".gw-nuevo", original)  # a proposal left by a run before the rename, still current
        out = self.applied()
        self.assertIn(f"{rel}.gw-nuevo is a proposal with the old suffix", out)
        self.assertIn(f"pending proposal {rel}.gw-nuevo", out)
        self.assertFalse((p.work / (rel + ".gw-new")).exists(), "an identical old proposal is not written twice")
        p.write(rel + ".gw-nuevo", "stale\n")  # an old proposal that is no longer current: the new one is written
        out = self.applied()
        self.assertIn(f"{rel}.gw-nuevo is a proposal with the old suffix", out)
        self.assertEqual(p.read(rel + ".gw-new"), original)
        self.assertEqual(p.read(rel + ".gw-nuevo"), "stale\n", "the person's file is never touched")

    def test_owned_script_older_header_is_updated(self):
        p = self.p
        self.applied()
        rel = ".claude/gw/scripts/reviewed.sh"
        original = p.read(rel)
        p.write(rel, original.replace(f"galivelop-workflow v{VERSION}", "galivelop-workflow v0.0.1") + "# local\n")
        out = self.applied()
        self.assertIn(f"update  {rel}", out)
        self.assertEqual(p.read(rel), original)
        self.assertFalse((p.work / (rel + ".gw-new")).exists())

    def test_same_version_local_edits_give_a_proposal_unless_update(self):
        p = self.p
        self.applied()
        rel = ".claude/gw/scripts/reviewed.sh"
        original = p.read(rel)
        p.write(rel, original + "# local edit\n")
        out = self.applied()
        self.assertIn(f"propose {rel}.gw-new", out)
        self.assertIn("local edits or an older copy of that version", out)
        self.assertIn(f"diff {rel} {rel}.gw-new", out)
        self.assertIn("# local edit", p.read(rel))
        self.assertEqual(p.read(rel + ".gw-new"), original)
        out = self.applied()
        self.assertIn("nothing to do", out)
        self.assertIn("pending proposal", out)
        code, out = p.run_apply("--check")
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
            {"hooks": [{"type": "command", "command": "python3 .claude/hooks/before-stop.py"}]})
        p.write(".claude/settings.json", json.dumps(settings))
        p.write(".claude/hooks/before-stop.py", f"#!/usr/bin/env python3\n# galivelop-workflow v{VERSION}\n")
        out = self.applied()
        self.assertIn("WARNING: .claude/settings.json Stop also runs 'python3 .claude/hooks/before-stop.py'", out)

    def test_config_guard_is_applied_once_with_its_own_matcher(self):
        p = self.p
        out = self.applied()
        self.assertTrue((p.work / ".claude/gw/scripts/config-guard.py").is_file(), out)
        s = json.loads(p.read(".claude/settings.json"))
        guards = [e for e in s["hooks"]["PreToolUse"]
                  if any("config-guard.py" in h["command"] for h in e["hooks"])]
        self.assertEqual(len(guards), 1, s["hooks"]["PreToolUse"])
        self.assertEqual(guards[0]["matcher"], "Edit|Write|MultiEdit|NotebookEdit|Bash")
        before = p.read(".claude/settings.json")
        self.applied()
        self.assertEqual(p.read(".claude/settings.json"), before, "a second run adds nothing")

    def test_subagent_cap_is_applied_once_with_its_own_matcher(self):
        p = self.p
        out = self.applied()
        self.assertTrue((p.work / ".claude/gw/scripts/subagent-cap.py").is_file(), out)
        s = json.loads(p.read(".claude/settings.json"))
        caps = [e for e in s["hooks"]["PreToolUse"]
                if any("subagent-cap.py" in h["command"] for h in e["hooks"])]
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
        rel = ".claude/gw/scripts/reviewed.sh"
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
        self.assertIn("propose .githooks/pre-push.gw-new", out)
        self.assertIn("not workflow-owned", out)
        self.assertEqual(p.read(".githooks/pre-push"), foreign)
        self.assertEqual(p.read(".githooks/pre-push.gw-new"), (ROOT / "templates/githooks/pre-push").read_text())

    def test_foreign_commit_msg_gets_a_proposal_and_the_hook_is_installed(self):
        p = self.p
        foreign = "#!/bin/sh\necho mine\n"
        p.write(".githooks/commit-msg", foreign)
        out = self.applied("--update")
        self.assertIn("propose .githooks/commit-msg.gw-new", out)
        self.assertEqual(p.read(".githooks/commit-msg"), foreign)
        self.assertEqual(p.read(".githooks/commit-msg.gw-new"), (ROOT / "templates/githooks/commit-msg").read_text())

    def test_commit_msg_is_installed_and_named_in_the_chain_hint(self):
        p = self.p
        p.run("git", "config", "core.hooksPath", ".husky")
        out = self.applied()
        self.assertEqual(p.read(".githooks/commit-msg"), (ROOT / "templates/githooks/commit-msg").read_text())
        self.assertIn("/commit-msg", out)

    def test_owned_skill_older_version_is_updated_and_orphans_reported(self):
        p = self.p
        self.applied()
        skill = p.work / ".claude" / "skills" / "gw-selector"
        original = (skill / "SKILL.md").read_text()
        (skill / "SKILL.md").write_text(original.replace(f'version: "{VERSION}"', 'version: "0.0.1"'))
        (skill / "OLD.md").write_text("gone upstream\n")
        out = self.applied()
        self.assertIn("update  .claude/skills/gw-selector/SKILL.md", out)
        self.assertEqual((skill / "SKILL.md").read_text(), original)
        self.assertIn(".claude/skills/gw-selector/OLD.md is no longer in the workflow", out)
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
        for script in ("session-start.sh", "recover.py --state", "review-before-main.sh", "before-stop.py",
                       "config-guard.py", "subagent-cap.py"):
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
        self.assertFalse((skills / "gw-opt-ai").exists())
        self.assertFalse((skills / "gw-scout-updates").exists())
        out = self.applied("--with", "gw-opt-ai")
        self.assertIn("create  .claude/skills/gw-opt-ai/SKILL.md", out)
        self.assertFalse((skills / "gw-scout-updates").exists())
        self.assertIn("nothing to do", self.applied())  # an installed optional skill stays managed
        code, out = p.run_apply("--with", "nope")
        self.assertEqual(code, 2, out)
        self.assertIn("unknown skill", out)

    def test_installed_scout_updates_tests_pass_in_the_project(self):
        """The skill's own tests find config.py in .claude/gw (installed layout), not three folders up (INS P1)."""
        p = self.p
        self.applied("--with", "gw-scout-updates")
        scripts = p.work / ".claude" / "skills" / "gw-scout-updates" / "scripts"
        code, out = p.run("python3", "-B", "-m", "unittest", "discover", "-s", str(scripts), "-p", "test_compare.py")
        self.assertEqual(code, 0, out)
        self.assertNotIn("config.py", out)
        self.assertIn("OK", out)

    def test_no_config_fails_closed(self):
        p = self.p
        (p.work / ".claude" / "gw.json").unlink()
        code, out = p.run_apply()
        self.assertEqual(code, 2, out)
        self.assertIn("gw.json not found", out)
        self.assertIn("config.py", out)
        self.assertFalse((p.work / ".githooks").exists())
        p.write(".claude/gw.json", json.dumps({"version": "0.1.0"}))
        code, out = p.run_apply()
        self.assertEqual(code, 2, out)
        self.assertIn("invalid", out)

    def test_other_hooks_path_is_respected(self):
        p = self.p
        p.run("git", "config", "core.hooksPath", ".husky")
        out = self.applied()
        self.assertEqual(p.hooks_path(), ".husky")
        self.assertIn("another hook manager", out)
        self.assertIn(".husky/pre-push", out)
        code, out = p.run_apply("--check")
        self.assertEqual(code, 0, out)  # a local git setting is not drift of the copy

    def test_spanish_project_commit_message(self):
        (self.tmp / "es").mkdir()
        p = Fixture(self.tmp / "es", {"language": "es"})
        code, out = p.run_apply()
        self.assertEqual(code, 0, out)
        self.assertIn(f"Flujo Galivelop-workflow v{VERSION}", out)
        self.assertIn("Siguiente:", out)


class PersonalNotes(unittest.TestCase):
    """Personal notes: regular files of GW_PERSONAL_NOTES (default ~/.claude/gw/notas) copied to
    <project>/.claude/gw/ when missing; a differing one is reported and never touched."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-notas-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)
        self.notes_dir = self.tmp / "notas"
        self.p.env["GW_PERSONAL_NOTES"] = str(self.notes_dir)

    def note(self, name, text="my note\n"):
        self.notes_dir.mkdir(exist_ok=True)
        (self.notes_dir / name).write_text(text)
        return self.notes_dir / name

    def target(self, name):
        return self.p.work / ".claude" / "gw" / name

    def applied(self, *args):
        code, out = self.p.run_apply(*args)
        self.assertEqual(code, 0, out)
        return out

    def test_absent_folder_does_nothing_and_says_nothing(self):
        self.assertNotIn("personal", self.applied())
        self.assertEqual(self.p.run_apply("--check")[0], 0)

    def test_folder_pointing_to_a_missing_path_does_nothing(self):
        self.p.env["GW_PERSONAL_NOTES"] = str(self.tmp / "nope" / "missing")
        self.assertNotIn("personal", self.applied())
        self.assertFalse((self.tmp / "nope").exists())

    def test_empty_folder_does_nothing(self):
        self.notes_dir.mkdir()
        self.assertNotIn("personal", self.applied())

    def test_default_folder_is_under_the_home_dir(self):
        folder = Path(self.p.env["HOME"]) / ".claude" / "gw" / "notas"  # the fixture's HOME, never the real one
        folder.mkdir(parents=True)
        (folder / "from-home.md").write_text("home note\n")
        del self.p.env["GW_PERSONAL_NOTES"]
        out = self.applied()
        self.assertIn("personal note", out)
        self.assertEqual(self.target("from-home.md").read_text(), "home note\n")

    def test_missing_note_is_created_and_reported(self):
        self.note("style.md", "I like short answers\n")
        out = self.applied()
        self.assertEqual(self.target("style.md").read_text(), "I like short answers\n")
        self.assertIn("personal note", out)
        self.assertIn("style.md", out)
        self.assertFalse((self.p.work / ".claude" / "gw" / "style.md.gw-new").exists())
        self.assertNotIn("personal", self.applied())  # second run: identical, silent

    def test_identical_note_is_silent_and_check_passes(self):
        self.note("style.md")
        self.applied()
        code, out = self.p.run_apply("--check")
        self.assertEqual(code, 0, out)
        self.assertNotIn("personal", out)

    def test_different_note_is_reported_untouched_and_check_still_passes(self):
        src = self.note("style.md", "mine\n")
        self.applied()
        self.target("style.md").write_text("adapted for this project\n")
        want = f"diff {src} {self.target('style.md')}"
        out = self.applied()
        self.assertEqual(self.target("style.md").read_text(), "adapted for this project\n")
        self.assertFalse((self.p.work / ".claude" / "gw" / "style.md.gw-new").exists())
        self.assertIn("personal note", out)
        self.assertIn(want, out)
        code, out = self.p.run_apply("--check")
        self.assertEqual(code, 0, out)
        self.assertIn(want, out)

    def test_dry_run_writes_nothing(self):
        self.note("style.md")
        out = self.applied("--dry-run")
        self.assertIn("style.md", out)
        self.assertIn("personal note", out)
        self.assertFalse(self.target("style.md").exists())

    def test_check_does_not_fail_for_a_missing_note_and_says_what_a_normal_run_does(self):
        self.applied("--no-personal-notes")  # the workflow copy itself is up to date
        self.note("style.md")
        code, out = self.p.run_apply("--check")
        self.assertEqual(code, 0, out)  # the note is not drift of the workflow copy
        self.assertIn("would create personal note style.md", out)
        self.assertIn("without --check", out)
        self.assertNotIn("differs from the workflow", out)
        self.assertFalse(self.target("style.md").exists())
        self.applied()  # a normal run still creates it
        self.assertTrue(self.target("style.md").is_file())

    def test_check_still_fails_for_real_drift_when_a_note_is_missing(self):
        self.applied()
        (self.p.work / ".claude" / "gw" / "scripts" / "config.py").write_text("# local edit\n")
        self.note("other.md")
        code, out = self.p.run_apply("--check")
        self.assertEqual(code, 1, out)
        self.assertIn("would create personal note other.md", out)

    def test_name_ending_in_gw_new_is_rejected_with_a_warning(self):
        self.note("style.md.gw-new")
        self.note("Other.GW-NEW")
        out = self.applied()
        self.assertIn("WARNING", out)
        self.assertIn("style.md.gw-new", out)
        self.assertIn(".gw-new", out)
        self.assertIn("pending proposal", out)
        self.assertIn("rename", out)
        self.assertFalse(self.target("style.md.gw-new").exists())
        self.assertFalse(self.target("Other.GW-NEW").exists())

    def test_name_ending_in_the_previous_proposal_suffix_is_still_rejected_with_a_warning(self):
        self.note("style.md.gw-nuevo")
        self.note("Other.GW-NUEVO")
        out = self.applied()
        self.assertIn("WARNING: personal note style.md.gw-nuevo ends in .gw-new (or the old .gw-nuevo)", out)
        self.assertIn("rename", out)
        self.assertFalse(self.target("style.md.gw-nuevo").exists())
        self.assertFalse(self.target("Other.GW-NUEVO").exists())

    def test_names_of_workflow_files_are_rejected_even_when_not_installed_and_ignoring_case(self):
        names = ("GW-OPT-TOKENS.md", "gw-opt-ai.md", "GW-Scout-Updates.md", "scripts", "SCHEMA", "gw.json",
                 "gw-opt-tokens.md.gw-new")
        for name in names:
            self.note(name)
        (self.p.work / ".claude" / "skills").mkdir(parents=True, exist_ok=True)
        out = self.applied()
        for name in ("GW-OPT-TOKENS.md", "gw-opt-ai.md", "GW-Scout-Updates.md", "scripts", "SCHEMA", "gw.json"):
            self.assertRegex(out, rf"WARNING: personal note {re.escape(name)} has the name of a workflow file")
        self.assertIn("rename", out)
        for name in ("GW-OPT-TOKENS.md", "gw-opt-ai.md", "GW-Scout-Updates.md", "SCHEMA", "gw.json"):
            # by exact name: on a case-insensitive disk (macOS) GW-OPT-TOKENS.md "exists" as the workflow's gw-opt-tokens.md
            parent = self.target(name).parent
            self.assertNotIn(name, os.listdir(parent) if parent.is_dir() else [], name)
        self.assertFalse(self.target("scripts").is_file())
        self.assertFalse((self.p.work / ".claude" / "gw" / "gw-opt-ai.md").exists())

    def test_unreadable_source_note_is_a_clean_line_not_a_traceback(self):
        src = self.note("style.md")
        os.chmod(src, 0)
        self.addCleanup(os.chmod, src, 0o644)
        if os.access(src, os.R_OK):
            self.skipTest("running as a user that ignores file permissions")
        out = self.applied()
        self.assertNotIn("Traceback", out)
        self.assertIn(f"personal note {src} cannot be read", out)
        self.assertIn("fix its permissions", out)
        self.assertFalse(self.target("style.md").exists())

    def test_unreadable_destination_note_is_a_clean_line_not_a_traceback(self):
        self.note("style.md")
        self.applied()
        dest = self.target("style.md")
        os.chmod(dest, 0)
        self.addCleanup(os.chmod, dest, 0o644)
        if os.access(dest, os.R_OK):
            self.skipTest("running as a user that ignores file permissions")
        out = self.applied()
        self.assertNotIn("Traceback", out)
        self.assertIn(f"personal note style.md: {dest} cannot be read", out)
        self.assertIn("fix its permissions", out)

    def test_notes_folder_that_is_a_file_or_unreadable_warns_but_absent_is_silent(self):
        self.notes_dir.write_text("not a folder\n")
        out = self.applied()
        self.assertIn(f"WARNING: personal notes path {self.notes_dir} is not a folder", out)
        self.assertIn("GW_PERSONAL_NOTES", out)
        self.notes_dir.unlink()
        self.notes_dir.mkdir()
        os.chmod(self.notes_dir, 0)
        self.addCleanup(os.chmod, self.notes_dir, 0o755)
        if os.access(self.notes_dir, os.R_OK):
            self.skipTest("running as a user that ignores directory permissions")
        out = self.applied()
        self.assertNotIn("Traceback", out)
        self.assertIn(f"WARNING: personal notes folder {self.notes_dir} cannot be read", out)
        self.assertIn("chmod", out)

    def test_relative_env_folder_is_resolved_to_an_absolute_path(self):
        src = self.note("style.md", "mine\n")
        self.applied()
        self.target("style.md").write_text("adapted\n")
        self.p.env["GW_PERSONAL_NOTES"] = "../notas"  # relative to the project, where the script runs
        out = self.applied()
        self.assertIn(f"diff {src} {self.target('style.md')}", out)

    def test_is_workflow_repo_fails_closed_when_its_own_plugin_json_is_unreadable(self):
        spec = importlib.util.spec_from_file_location("apply_closed", APPLY_SCRIPT)
        apply_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(apply_module)
        apply_module.WORKFLOW = self.tmp / "no-such-workflow"
        self.assertTrue(apply_module.is_workflow_repo(self.p.work))
        broken = self.tmp / "broken"
        (broken / ".claude-plugin").mkdir(parents=True)
        (broken / ".claude-plugin" / "plugin.json").write_text("{not json")
        apply_module.WORKFLOW = broken
        self.assertTrue(apply_module.is_workflow_repo(self.p.work))

    def test_symlink_dotfile_subfolder_and_bad_names_are_skipped(self):
        real = self.note("real.md")
        (self.notes_dir / "link.md").symlink_to(real)
        for bad in (".hidden.md", "-dash.md", "bad name.md", "a$b.md", "é.md"):
            self.note(bad)
        (self.notes_dir / "sub").mkdir()
        (self.notes_dir / "sub" / "inner.md").write_text("x\n")
        (self.notes_dir / "dir.md").mkdir()
        self.note("1.v2-x.txt")
        self.note("a_b.md")
        self.applied()
        created = sorted(p.name for p in (self.p.work / ".claude" / "gw").iterdir()
                         if p.name in {"real.md", "link.md", ".hidden.md", "-dash.md", "bad name.md", "a$b.md",
                                       "é.md", "sub", "inner.md", "dir.md", "1.v2-x.txt", "a_b.md"})
        self.assertEqual(created, ["1.v2-x.txt", "a_b.md", "real.md"])

    def test_workflow_repo_itself_never_gets_personal_notes(self):
        self.note("style.md")
        code, out = self.p.run("python3", str(APPLY_SCRIPT), str(ROOT), "--dry-run")
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
        self.assertNotIn("personal", self.applied("--no-personal-notes"))
        self.assertFalse(self.target("style.md").exists())
        self.assertEqual(self.p.run_apply("--check", "--no-personal-notes")[0], 0)

    def test_target_that_is_not_a_regular_file_is_reported_not_replaced(self):
        self.note("style.md")
        self.target("style.md").mkdir(parents=True)
        out = self.applied()
        self.assertTrue(self.target("style.md").is_dir())
        self.assertIn("personal note", out)
        self.assertIn("not a regular file", out)

    def test_help_mentions_the_notes_and_the_flag(self):
        code, out = self.p.run("python3", str(APPLY_SCRIPT), "--help")
        self.assertEqual(code, 0, out)
        self.assertIn("GW_PERSONAL_NOTES", out)
        self.assertIn("--no-personal-notes", out)


SKILL_MD = "---\nname: {n}\ndescription: old copy\nmetadata:\n  version: \"0.4.3\"\n---\n# {n}\n"
MIGRATED_CONFIG = {k: v for k, v in BASE_CONFIG.items() if k not in ("log", "reviewMark")}


class Migrate(unittest.TestCase):
    """A8 chunk 4: apply.py moves a project installed with the old names to the new ones, with no duplicates."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-migrar-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)
        self.p.write(".claude/gw.json", json.dumps(MIGRATED_CONFIG, indent=2) + "\n")  # no `log`, no `reviewMark`

    def applied(self, *args):
        code, out = self.p.run_apply(*args)
        self.assertEqual(code, 0, out)
        return out

    def commit(self):
        self.p.run("git", "add", "-A")
        self.assertEqual(self.p.run("git", "commit", "-qm", "x")[0], 0)

    def exists(self, rel):
        return (self.p.work / rel).exists()

    def old_paths(self):
        p = self.p
        p.write("docs/traspaso.md", "# Log\n")
        p.write("docs/registros/revisado.txt", "abc\n")
        p.write("docs/registros/release-v0.1.0.md", "r\n")
        p.write("docs/propuestas/uno.md", "# Harvest\n")

    # ---- skills

    def test_old_skill_folders_are_replaced_not_duplicated(self):
        p = self.p
        for old in ("selector", "opt-tokens", "opt-ai"):
            p.write(f".claude/skills/{old}/SKILL.md", SKILL_MD.format(n=old))
            p.write(f".claude/skills/{old}/extra.md", "x\n")
        self.commit()
        out = self.applied()
        for old in ("selector", "opt-tokens", "opt-ai"):
            self.assertFalse(self.exists(f".claude/skills/{old}"), out)
        self.assertIn("remove  .claude/skills/selector", out)
        self.assertTrue(self.exists(".claude/skills/gw-selector/SKILL.md"))
        self.assertTrue(self.exists(".claude/skills/gw-opt-ai/SKILL.md"))  # the old optional skill was installed: kept
        self.assertFalse(self.exists(".claude/skills/gw-scout-updates"))
        self.assertIn("nothing to do", self.applied())  # rerun: no-op

    def test_old_optional_skill_not_installed_stays_out(self):
        self.applied()
        self.assertFalse(self.exists(".claude/skills/gw-opt-ai"))
        self.assertFalse(self.exists(".claude/skills/gw-scout-updates"))

    def test_with_old_name_warns_and_installs_the_new_one(self):
        out = self.applied("--with", "opt-ai")
        self.assertIn("--with opt-ai is the old name; use --with gw-opt-ai", out)
        self.assertTrue(self.exists(".claude/skills/gw-opt-ai/SKILL.md"))
        self.assertTrue(self.exists(".claude/gw/gw-opt-ai.md"))
        self.assertFalse(self.exists(".claude/skills/opt-ai"))

    def test_foreign_skill_with_an_old_name_is_kept_with_a_warning(self):
        self.p.write(".claude/skills/selector/SKILL.md", "---\nname: selector\ndescription: mine\n---\n")
        out = self.applied()
        self.assertTrue(self.exists(".claude/skills/selector/SKILL.md"))
        self.assertIn("is not a workflow skill", out)
        self.assertIn("git rm -r .claude/skills/selector", out)

    # ---- notes

    def test_tracked_note_is_git_moved_and_history_kept(self):
        p = self.p
        p.write(".claude/gw/opt-tokens.md", "# my notes\n")
        p.write(".claude/gw/orchestrate-dealer.md", "# dealer\n")
        self.commit()
        self.applied()
        self.assertEqual(p.read(".claude/gw/gw-opt-tokens.md"), "# my notes\n")  # not the template
        self.assertFalse(self.exists(".claude/gw/opt-tokens.md"))
        self.assertEqual(p.read(".claude/gw/gw-orchestrate-dealer.md"), "# dealer\n")
        status = p.run("git", "status", "--short")[1]
        self.assertRegex(status, r"R  \.claude/gw/opt-tokens\.md -> \.claude/gw/gw-opt-tokens\.md")

    def test_untracked_note_is_renamed(self):
        self.p.write(".claude/gw/selector.md", "# sel\n")
        self.applied()
        self.assertEqual(self.p.read(".claude/gw/gw-selector.md"), "# sel\n")
        self.assertFalse(self.exists(".claude/gw/selector.md"))

    def test_both_notes_exist_keeps_the_new_one_and_warns(self):
        p = self.p
        p.write(".claude/gw/opt-tokens.md", "# old\n")
        p.write(".claude/gw/gw-opt-tokens.md", "# new\n")
        out = self.applied()
        self.assertEqual(p.read(".claude/gw/gw-opt-tokens.md"), "# new\n")
        self.assertEqual(p.read(".claude/gw/opt-tokens.md"), "# old\n")
        self.assertIn(".claude/gw/opt-tokens.md and .claude/gw/gw-opt-tokens.md both exist", out)
        self.assertIn("git rm .claude/gw/opt-tokens.md", out)

    # ---- scripts

    def test_old_script_copies_are_removed_and_hook_commands_renamed(self):
        p = self.p
        p.write(".claude/gw/scripts/bitacora.py", "# galivelop-workflow v0.4.3\n")
        p.write(".claude/gw/scripts/mine.py", "print(1)\n")
        p.write(".claude/gw/scripts/revisado.sh", "# my own script, no header\n")
        p.write(".claude/settings.json", json.dumps({"hooks": {"Stop": [{"hooks": [
            {"type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/gw/scripts/antes-de-parar.py"}]}]}}))
        p.write(".claude/gw/scripts/antes-de-parar.py", "# galivelop-workflow v0.4.3\n")
        self.commit()
        out = self.applied()
        self.assertFalse(self.exists(".claude/gw/scripts/bitacora.py"), out)
        self.assertFalse(self.exists(".claude/gw/scripts/antes-de-parar.py"), out)
        self.assertTrue(self.exists(".claude/gw/scripts/handoff.py"))
        self.assertTrue(self.exists(".claude/gw/scripts/mine.py"))
        self.assertTrue(self.exists(".claude/gw/scripts/revisado.sh"))  # not generated by the workflow: kept
        commands = [h["command"] for e in json.loads(p.read(".claude/settings.json"))["hooks"]["Stop"]
                    for h in e["hooks"]]
        self.assertEqual(sum("before-stop.py" in c for c in commands), 1, commands)  # renamed, not duplicated
        self.assertFalse(any("antes-de-parar" in c for c in commands), commands)
        self.assertIn("nothing to do", self.applied())

    def test_old_script_kept_while_a_git_hook_still_runs_it(self):
        p = self.p
        p.write(".claude/gw/scripts/revisado.sh", "# galivelop-workflow v0.4.3\n")
        p.write(".githooks/pre-push", "#!/bin/sh\nbash .claude/gw/scripts/revisado.sh\n")  # not workflow-owned
        self.commit()
        out = self.applied()
        self.assertTrue(self.exists(".claude/gw/scripts/revisado.sh"), out)
        self.assertNotIn("no longer in the workflow (kept); delete it if nothing uses it: git rm "
                         ".claude/gw/scripts/revisado.sh", out)  # reported once, as in use
        self.assertIn("is the old name of reviewed.sh and is still run by .githooks/pre-push", out)

    # ---- project paths

    def test_old_paths_move_with_git_and_nothing_is_written_in_the_config(self):
        p = self.p
        self.old_paths()
        self.commit()
        p.write("docs/registros/revisado.txt", "abc edited\n")  # a dirty tree does not matter
        p.write("docs/registros/untracked.md", "u\n")
        before = p.read(".claude/gw.json")
        out = self.applied()
        self.assertFalse(self.exists("docs/traspaso.md"), out)
        self.assertFalse(self.exists("docs/registros"))
        self.assertFalse(self.exists("docs/propuestas"))
        self.assertEqual(p.read("docs/handoff.md"), "# Log\n")  # the project's log, not the template
        self.assertEqual(p.read("docs/records/reviewed.txt"), "abc edited\n")
        self.assertTrue(self.exists("docs/records/release-v0.1.0.md"))
        self.assertTrue(self.exists("docs/records/untracked.md"))
        self.assertTrue(self.exists("docs/proposals/uno.md"))
        self.assertEqual(p.read(".claude/gw.json"), before)
        status = p.run("git", "status", "--short")[1]
        self.assertIn("docs/traspaso.md -> docs/handoff.md", status)
        code, cfg = p.run("python3", str(ROOT / "scripts" / "config.py"), "--root", str(p.work), "get", "log")
        self.assertEqual(cfg.strip(), "docs/handoff.md", cfg)
        out = self.applied()  # twice: a no-op
        self.assertIn("nothing to do", out)
        self.assertEqual(p.read("docs/handoff.md"), "# Log\n")

    def test_untracked_old_paths_are_renamed_too(self):
        self.old_paths()
        self.applied()
        self.assertEqual(self.p.read("docs/records/reviewed.txt"), "abc\n")
        self.assertFalse(self.exists("docs/registros"))

    def test_explicit_old_paths_in_the_config_move_and_the_keys_are_dropped(self):
        p = self.p
        p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, log="docs/traspaso.md",
                                                   reviewMark="docs/registros/revisado.txt"), indent=2) + "\n")
        self.old_paths()
        self.applied()
        cfg = json.loads(p.read(".claude/gw.json"))
        self.assertNotIn("log", cfg)
        self.assertNotIn("reviewMark", cfg)
        self.assertEqual(p.read("docs/handoff.md"), "# Log\n")
        self.assertEqual(p.read("docs/records/reviewed.txt"), "abc\n")
        self.assertIn("nothing to do", self.applied())

    def test_a_custom_log_path_is_never_touched(self):
        p = self.p
        p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, log="notes/log.md"), indent=2) + "\n")
        p.write("notes/log.md", "# mine\n")
        p.write("docs/traspaso.md", "# unrelated old file\n")  # the key is explicit and is not the old path
        self.applied()
        self.assertEqual(p.read("notes/log.md"), "# mine\n")
        self.assertEqual(p.read("docs/traspaso.md"), "# unrelated old file\n")

    def test_move_fails_closed_when_the_target_exists(self):
        p = self.p
        p.write("docs/traspaso.md", "# Log\n")
        (p.work / "docs" / "handoff.md").mkdir()  # an empty folder: the old path still counts as the log
        code, out = p.run_apply()
        self.assertEqual(code, 2, out)
        self.assertIn("cannot move docs/traspaso.md to docs/handoff.md: docs/handoff.md already exists", out)
        self.assertIn("--keep-paths", out)
        self.assertEqual(p.read("docs/traspaso.md"), "# Log\n")
        self.assertFalse(self.exists(".claude/gw/scripts"))  # nothing else was written

    def test_dry_run_and_check_move_nothing(self):
        p = self.p
        self.old_paths()
        code, out = p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("move    docs/handoff.md  (from docs/traspaso.md", out)
        self.assertTrue(self.exists("docs/traspaso.md"))
        self.assertFalse(self.exists("docs/handoff.md"))
        code, out = p.run_apply("--check")
        self.assertEqual(code, 1, out)
        self.assertIn("move    docs/records/reviewed.txt", out)
        self.assertTrue(self.exists("docs/registros/revisado.txt"))

    def test_keep_paths_writes_the_old_paths_explicitly_and_moves_nothing(self):
        p = self.p
        self.old_paths()
        out = self.applied("--keep-paths")
        self.assertIn("--keep-paths:", out)
        cfg = json.loads(p.read(".claude/gw.json"))
        self.assertEqual(cfg["log"], "docs/traspaso.md")
        self.assertEqual(cfg["reviewMark"], "docs/registros/revisado.txt")
        self.assertEqual(cfg["recordsDir"], "docs/registros")
        self.assertEqual(cfg["proposalsDir"], "docs/propuestas")
        self.assertTrue(self.exists("docs/traspaso.md"))
        self.assertFalse(self.exists("docs/handoff.md"))
        again = self.applied("--keep-paths")  # keys already explicit: a no-op
        self.assertIn("nothing to do", again)
        self.assertEqual(json.loads(p.read(".claude/gw.json")), cfg)
        self.assertTrue(cfg["keepLegacyPaths"])
        code, out = self.p.run_apply("--check")  # a later plain run or --check respects the choice
        self.assertNotIn("move ", out)
        self.assertTrue(self.exists("docs/traspaso.md"))

    def test_keep_paths_with_nothing_old_changes_nothing(self):
        before = self.p.read(".claude/gw.json")
        self.applied("--keep-paths")
        self.assertEqual(self.p.read(".claude/gw.json"), before)

    # ---- review of the first version

    def test_keep_paths_also_writes_keys_inside_a_kept_folder(self):
        self.old_paths()
        self.applied("--keep-paths")
        cfg = json.loads(self.p.read(".claude/gw.json"))
        self.assertEqual(cfg["ciLocalLog"], "docs/registros/ci-local.md")  # no ci-local.md yet, still inside it

    def test_keep_paths_plan_line_mentions_the_reformat(self):
        self.old_paths()
        self.assertIn("gw.json is rewritten with 2-space indent", self.p.run_apply("--keep-paths", "--dry-run")[1])

    def test_a_rerun_repairs_an_explicit_key_after_a_manual_move(self):
        p = self.p
        p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, log="docs/traspaso.md"), indent=2) + "\n")
        p.write("docs/handoff.md", "# Log moved by hand\n")  # the old file is gone, the key still names it
        self.applied()
        self.assertNotIn("log", json.loads(p.read(".claude/gw.json")))
        self.assertEqual(p.read("docs/handoff.md"), "# Log moved by hand\n")

    def test_old_skill_with_local_changes_is_kept_with_the_reason(self):
        p = self.p
        p.write(".claude/skills/selector/SKILL.md", SKILL_MD.format(n="selector"))
        self.commit()
        p.write(".claude/skills/selector/mine.md", "my file\n")  # untracked
        out = self.applied()
        self.assertTrue(self.exists(".claude/skills/selector/mine.md"), out)
        self.assertIn("not in git or has uncommitted changes or untracked or ignored files, so it is kept", out)
        self.assertIn("git rm -r .claude/skills/selector", out)  # tracked: git rm

    def old_media_skill(self):
        p = self.p
        p.write(".claude/skills/gw-media-content/SKILL.md", SKILL_MD.format(n="gw-media-content"))
        for rel in ("catalogo.md", "nota.md", "reglas.json", "plantilla/ficha.md", "plantilla/medios/fuente/tarjeta.html",
                    "scripts/cifras.py", "scripts/comprobar.py", "scripts/test_cifras.py", "scripts/test_comprobar.py"):
            p.write(f".claude/skills/gw-media-content/{rel}", "old\n")

    def test_old_named_files_of_an_installed_skill_are_removed_and_the_new_ones_installed(self):
        self.old_media_skill()
        self.commit()
        out = self.applied()
        base = ".claude/skills/gw-media-content/"
        for old in ("catalogo.md", "nota.md", "reglas.json", "plantilla", "scripts/cifras.py", "scripts/comprobar.py",
                    "scripts/test_cifras.py", "scripts/test_comprobar.py"):
            self.assertFalse(self.exists(base + old), old)
        for new in ("catalog.md", "note.md", "rules.json", "template/sheet.md", "template/media/source/card.html",
                    "scripts/figures.py", "scripts/check.py", "scripts/render.mjs"):
            self.assertTrue(self.exists(base + new), new)
        self.assertIn("remove  .claude/skills/gw-media-content/plantilla", out)
        self.assertNotIn("is no longer in the workflow", out)
        self.assertIn("nothing to do", self.applied())  # rerun: no-op

    def test_old_spanish_script_of_an_installed_skill_is_replaced_by_the_english_one(self):
        p = self.p
        p.write(".claude/skills/gw-opt-tokens/SKILL.md", SKILL_MD.format(n="gw-opt-tokens"))
        for rel in ("scripts/medir.py", "scripts/test_medir.py"):
            p.write(f".claude/skills/gw-opt-tokens/{rel}", "old\n")
        self.commit()
        self.applied()
        base = ".claude/skills/gw-opt-tokens/scripts/"
        self.assertFalse(self.exists(base + "medir.py"))
        self.assertFalse(self.exists(base + "test_medir.py"))
        self.assertTrue(self.exists(base + "measure.py"))

    def test_old_named_file_of_a_skill_with_local_edits_is_kept_with_the_reason(self):
        self.old_media_skill()
        self.commit()
        self.p.write(".claude/skills/gw-media-content/catalogo.md", "my edit\n")
        out = self.applied()
        self.assertTrue(self.exists(".claude/skills/gw-media-content/catalogo.md"), out)
        self.assertFalse(self.exists(".claude/skills/gw-media-content/nota.md"), out)
        self.assertIn(".claude/skills/gw-media-content/catalogo.md is the old name of a workflow copy, but it is not in "
                      "git or has uncommitted changes", out)
        self.assertIn("git rm -r .claude/skills/gw-media-content/catalogo.md", out)

    def test_old_named_files_of_a_foreign_skill_folder_are_left_alone(self):
        self.p.write(".claude/skills/gw-media-content/SKILL.md", "---\nname: gw-media-content\ndescription: mine\n---\n")
        self.p.write(".claude/skills/gw-media-content/catalogo.md", "mine\n")
        self.commit()
        self.applied()
        self.assertTrue(self.exists(".claude/skills/gw-media-content/catalogo.md"))

    def test_old_skill_not_in_git_is_kept(self):
        self.p.write(".claude/skills/selector/SKILL.md", SKILL_MD.format(n="selector"))
        out = self.applied()
        self.assertTrue(self.exists(".claude/skills/selector/SKILL.md"), out)
        self.assertIn("delete it yourself: rm -r .claude/skills/selector", out)  # untracked: plain rm
        self.assertNotIn("git rm -r", out)

    def test_old_script_with_uncommitted_edits_is_kept(self):
        p = self.p
        p.write(".claude/gw/scripts/bitacora.py", "# galivelop-workflow v0.4.3\n")
        self.commit()
        p.write(".claude/gw/scripts/bitacora.py", "# galivelop-workflow v0.4.3\nedited\n")
        out = self.applied()
        self.assertTrue(self.exists(".claude/gw/scripts/bitacora.py"), out)
        self.assertIn("has uncommitted changes or untracked or ignored files, so it is kept", out)

    def test_hand_set_keep_legacy_paths_also_writes_the_implicit_keys(self):
        p = self.p
        self.old_paths()
        p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, keepLegacyPaths=True), indent=2) + "\n")
        self.applied()
        cfg = json.loads(p.read(".claude/gw.json"))
        self.assertEqual(cfg["log"], "docs/traspaso.md")
        self.assertEqual(cfg["reviewMark"], "docs/registros/revisado.txt")
        self.assertTrue(self.exists("docs/traspaso.md"))
        self.assertFalse(self.exists("docs/handoff.md"))
        self.assertIn("nothing to do", self.applied())

    def test_explicit_key_inside_a_folder_moved_by_hand_follows_the_file(self):
        p = self.p
        p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, reviewMark="docs/registros/revisado.txt",
                                                   staleRefs={"patterns": ["x"], "skip": ["docs/registros/old"]}),
                                              indent=2) + "\n")
        p.write("docs/records/revisado.txt", "abc\n")  # the folder was moved by hand, the file kept its name
        self.applied()
        cfg = json.loads(p.read(".claude/gw.json"))
        self.assertNotIn("reviewMark", cfg)
        self.assertEqual(cfg["staleRefs"]["skip"], ["docs/records/old"])
        self.assertEqual(p.read("docs/records/reviewed.txt"), "abc\n")
        self.assertFalse(self.exists("docs/records/revisado.txt"))
        self.assertIn("in sync", self.p.run_apply("--check")[1])

    def test_old_script_kept_because_not_clean_is_not_reported_as_an_orphan(self):
        p = self.p
        p.write(".claude/gw/scripts/bitacora.py", "# galivelop-workflow v0.4.3\n")
        self.commit()
        p.write(".claude/gw/scripts/bitacora.py", "# galivelop-workflow v0.4.3\nedited\n")
        out = self.applied()
        self.assertIn("so it is kept", out)
        self.assertNotIn("bitacora.py is no longer in the workflow", out)  # reported once, not also as an orphan

    def test_ignored_files_make_an_old_skill_not_clean(self):
        p = self.p
        p.write(".gitignore", "*.cache\n")
        p.write(".claude/skills/selector/SKILL.md", SKILL_MD.format(n="selector"))
        self.commit()
        p.write(".claude/skills/selector/x.cache", "ignored\n")
        out = self.applied()
        self.assertTrue(self.exists(".claude/skills/selector/x.cache"), out)
        self.assertIn("untracked or ignored files, so it is kept", out)

    def test_values_pointing_inside_a_moved_folder_follow_it(self):
        p = self.p
        p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, ciLocalLog="docs/registros/mi-ci.md",
                                                   staleRefs={"patterns": ["x"], "skip": ["docs/registros/old"]}),
                                              indent=2) + "\n")
        self.old_paths()
        p.write("docs/registros/mi-ci.md", "ci\n")
        self.applied()
        cfg = json.loads(p.read(".claude/gw.json"))
        self.assertEqual(cfg["ciLocalLog"], "docs/records/mi-ci.md")
        self.assertEqual(cfg["staleRefs"]["skip"], ["docs/records/old"])
        self.assertTrue(self.exists("docs/records/mi-ci.md"))

    def test_settings_local_hooks_are_renamed_and_protect_the_old_script(self):
        p = self.p
        p.write(".claude/gw/scripts/bitacora.py", "# galivelop-workflow v0.4.3\n")
        p.write(".claude/settings.local.json", json.dumps({"hooks": {"Stop": [{"hooks": [
            {"type": "command", "command": "python3 .claude/gw/scripts/bitacora.py check"}]}]}}))
        self.commit()
        self.applied()
        text = p.read(".claude/settings.local.json")
        self.assertIn("handoff.py check", text)
        self.assertNotIn("bitacora", text)
        self.assertFalse(self.exists(".claude/gw/scripts/bitacora.py"))

    # ---- CI file and option names (A8 chunk 6a)

    def tracked_workflow(self, text):
        self.p.write(".github/workflows/comprobar.yml", text)
        self.commit()

    def test_own_old_workflow_file_is_moved_to_check_yml_and_updated(self):
        p = self.p
        self.tracked_workflow("# galivelop-workflow v0.4.0\nname: Comprobar\n")
        out = self.applied()
        self.assertFalse(self.exists(".github/workflows/comprobar.yml"), out)
        self.assertIn("name: Check", p.read(".github/workflows/check.yml"))
        self.assertFalse(self.exists(".github/workflows/check.yml.gw-new"), out)
        self.assertIn("nothing to do", self.applied())

    def test_old_workflow_file_with_a_version_not_older_keeps_its_content_and_gets_a_proposal(self):
        p = self.p
        self.tracked_workflow("# galivelop-workflow v99.0.0\nname: Mine\n")
        out = self.applied()
        self.assertFalse(self.exists(".github/workflows/comprobar.yml"), out)
        self.assertIn("name: Mine", p.read(".github/workflows/check.yml"))
        self.assertTrue(self.exists(".github/workflows/check.yml.gw-new"), out)

    def test_old_workflow_file_without_header_is_the_projects_own_and_stays(self):
        p = self.p
        self.tracked_workflow("name: CI of mine\n")
        out = self.applied()
        self.assertEqual(p.read(".github/workflows/comprobar.yml"), "name: CI of mine\n")
        self.assertFalse(self.exists(".github/workflows/check.yml"), out)
        self.assertTrue(self.exists(".github/workflows/check.yml.gw-new"), out)
        self.assertIn("looks like the project's own CI", out)

    def test_old_workflow_file_next_to_check_yml_is_only_warned(self):
        p = self.p
        self.tracked_workflow("# galivelop-workflow v0.4.3\nname: Comprobar\n")
        self.applied()
        p.write(".github/workflows/comprobar.yml", "# galivelop-workflow v0.4.3\nname: Comprobar\n")
        out = self.applied()
        self.assertTrue(self.exists(".github/workflows/comprobar.yml"), out)
        self.assertIn("both exist", out)

    def test_recover_hook_flags_are_renamed_without_a_duplicate_hook(self):
        p = self.p
        p.write(".claude/settings.json", json.dumps({"hooks": {"SessionStart": [{"matcher": "clear|compact", "hooks": [
            {"type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/gw/scripts/recover.py --estado"}]}]}}))
        self.commit()
        self.applied()
        commands = [h["command"] for e in json.loads(p.read(".claude/settings.json"))["hooks"]["SessionStart"]
                    for h in e["hooks"] if "recover.py" in h["command"]]
        self.assertEqual(len(commands), 1, commands)
        self.assertTrue(commands[0].endswith("recover.py --state"), commands)
        self.assertNotIn("--estado", commands[0])
        self.assertIn("nothing to do", self.applied())

    def test_old_option_and_env_names_warn_with_the_new_name(self):
        p = self.p
        code, out = p.run_apply("--sin-notas-personales")
        self.assertEqual(code, 0, out)
        self.assertIn("--sin-notas-personales", out)
        self.assertIn("--no-personal-notes", out)
        notes = self.tmp / "notes-old"
        notes.mkdir()
        (notes / "x.md").write_text("n\n")
        del p.env["GW_PERSONAL_NOTES"]
        p.env["GW_NOTAS_PERSONALES"] = str(notes)
        code, out = p.run_apply()
        self.assertEqual(code, 0, out)
        self.assertIn("GW_NOTAS_PERSONALES", out)
        self.assertIn("GW_PERSONAL_NOTES", out)
        self.assertIn("x.md", out)


    def test_help_mentions_keep_paths(self):
        code, out = self.p.run("python3", str(APPLY_SCRIPT), "--help")
        self.assertIn("--keep-paths", out)


if __name__ == "__main__":
    unittest.main()
