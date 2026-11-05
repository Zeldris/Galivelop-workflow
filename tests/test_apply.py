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

    def test_gitignore_gets_the_private_local_file(self):
        p = self.p
        code, out = p.run_apply("--check")
        self.assertEqual(code, 1, out)
        self.assertIn(".gitignore", out)
        self.applied()
        self.assertTrue(p.read(".gitignore").endswith(".claude/gw.local.json\n"))
        self.assertEqual(p.run("git", "check-ignore", "-q", ".claude/gw.local.json")[0], 0)
        p.write(".gitignore", "node_modules/")  # no final newline: the line goes below, not glued to it
        self.applied()
        self.assertEqual(p.read(".gitignore"),
                         "node_modules/\n# galivelop-workflow: private, never committed\n.claude/gw.local.json\n")
        p.write(".gitignore", "/**/gw.local.json\n")  # already listed in another form: left alone
        self.assertNotIn(".gitignore", self.applied())
        self.assertEqual(p.read(".gitignore"), "/**/gw.local.json\n")
        code, out = p.run_apply("--check")
        self.assertEqual(code, 0, out)

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

    def test_agent_signatures_hook_is_applied_once_for_github_text_and_bash(self):
        p = self.p
        out = self.applied()
        self.assertTrue((p.work / ".claude/gw/scripts/agent-signatures.py").is_file(), out)
        s = json.loads(p.read(".claude/settings.json"))
        found = [e for e in s["hooks"]["PreToolUse"]
                 if any("agent-signatures.py" in h["command"] for h in e["hooks"])]
        self.assertEqual(len(found), 1, s["hooks"]["PreToolUse"])
        self.assertIn("add_issue_comment", found[0]["matcher"])
        self.assertTrue(found[0]["matcher"].endswith("|^Bash$"), found[0]["matcher"])
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

    def test_settings_worktree_base_ref_install_update_and_project_value(self):
        p = self.p
        self.applied()  # install
        s = json.loads(p.read(".claude/settings.json"))
        self.assertEqual(s["worktree"], {"baseRef": "head"})
        self.assertIn("nothing to do", self.applied())  # second pass: idempotent
        del s["worktree"]  # update on a project without the key
        p.write(".claude/settings.json", json.dumps(s))
        out = self.applied()
        self.assertIn("merge   .claude/settings.json", out)
        self.assertIn("worktree", out)
        self.assertEqual(json.loads(p.read(".claude/settings.json"))["worktree"], {"baseRef": "head"})
        s["worktree"] = {"baseRef": "fresh", "mine": 1}  # update keeps the project's own value
        p.write(".claude/settings.json", json.dumps(s))
        self.assertIn("nothing to do", self.applied())
        self.assertEqual(json.loads(p.read(".claude/settings.json"))["worktree"], {"baseRef": "fresh", "mine": 1})
        s["worktree"] = {"mine": 1}  # object without baseRef: the missing subkey is added
        p.write(".claude/settings.json", json.dumps(s))
        out = self.applied()
        self.assertIn("worktree.baseRef", out)
        self.assertEqual(json.loads(p.read(".claude/settings.json"))["worktree"], {"mine": 1, "baseRef": "head"})
        self.assertIn("nothing to do", self.applied())

    def test_settings_worktree_not_an_object_is_refused_with_the_fix(self):
        p = self.p
        self.applied()
        s = json.loads(p.read(".claude/settings.json"))
        s["worktree"] = "head"
        p.write(".claude/settings.json", json.dumps(s))
        before = p.read(".claude/settings.json")
        code, out = p.run_apply()
        self.assertEqual(code, 2, out)
        self.assertIn("'worktree' is not an object; fix it and rerun: python3 -m json.tool .claude/settings.json", out)
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

    def test_installed_figures_and_opt_ai_tests_pass_in_the_project(self):
        """gw-media-content's figures tests use .claude/gw (not the repo root) and gw-opt-ai's measure tests ignore the
        project's own .claude/gw/gw-opt-ai.md: same result installed as here (WMF P3)."""
        p = self.p
        self.applied("--with", "gw-opt-ai")
        p.write(".claude/gw/gw-opt-ai.md", "# Local AI\n\n```gw-opt-ai\nlog: no-such-log.jsonl\ncold_ms: 1\n```\n")
        skills = p.work / ".claude" / "skills"
        for skill, test in (("gw-media-content", "test_figures.py"), ("gw-opt-ai", "test_measure.py")):
            code, out = p.run("python3", "-B", "-m", "unittest", "discover", "-s", str(skills / skill / "scripts"),
                              "-p", test)
            self.assertEqual(code, 0, out)
            self.assertNotIn("FileNotFoundError", out)
            self.assertNotIn("skipped", out)  # the config.py test ran, it was not skipped
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

    def test_absolute_hooks_path_is_reported_with_the_fix_like_doctor_does(self):
        p = self.p
        absolute = str(p.work / ".githooks")
        p.run("git", "config", "core.hooksPath", absolute)
        out = self.applied()
        self.assertEqual(p.hooks_path(), absolute)  # not rewritten: it is the user's setting
        self.assertIn(f"core.hooksPath is the absolute path '{absolute}'", out)
        self.assertIn("another branch's hooks", out)
        self.assertIn("git config core.hooksPath .githooks", out)
        self.assertNotIn("another hook manager", out)

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

    def old_script_with_reference(self, hook, line):
        p = self.p
        p.write(".claude/gw/scripts/revisado.sh", "# galivelop-workflow v0.4.3\n")
        p.write(hook, "#!/bin/sh\n" + line + "\n")
        self.commit()
        return self.applied()

    def test_old_script_kept_by_a_reference_with_dot_slash_or_a_variable_prefix(self):
        """D52: the installed path keeps it however it is written."""
        for line in ("bash ./.claude/gw/scripts/revisado.sh", 'bash "$ROOT"/.claude/gw/scripts/revisado.sh'):
            with self.subTest(line=line):
                self.setUp()
                out = self.old_script_with_reference(".githooks/pre-push", line)
                self.assertTrue(self.exists(".claude/gw/scripts/revisado.sh"), out)
                self.assertIn("is still run by .githooks/pre-push", out)

    def test_old_script_kept_by_the_old_hook_variable_forms(self):
        """D52: the real old hooks call `"$scripts/<old>"` or `${scripts}/<old>`; a Windows path counts too."""
        for line in ('python3 "$scripts/bitacora.py"', 'python3 "${scripts}/bitacora.py"',
                     "python3 .claude\\gw\\scripts\\bitacora.py"):
            with self.subTest(line=line):
                self.setUp()
                p = self.p
                p.write(".claude/gw/scripts/bitacora.py", "# galivelop-workflow v0.4.3\n")
                p.write(".githooks/pre-push", "#!/bin/sh\n" + line + "\n")
                self.commit()
                out = self.applied()
                self.assertTrue(self.exists(".claude/gw/scripts/bitacora.py"), out)
                self.assertIn("is still run by .githooks/pre-push", out)

    def test_old_script_not_kept_by_a_same_named_file_elsewhere(self):
        """D52: tools/qa/revisado.sh is another script, not the installed copy."""
        out = self.old_script_with_reference(".githooks/pre-push", "bash tools/qa/revisado.sh")
        self.assertFalse(self.exists(".claude/gw/scripts/revisado.sh"), out)
        self.assertNotIn("is still run by", out)

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

    def test_log_inside_a_moved_folder_is_moved_not_seeded(self):
        """D51: the log arrives at docs/records/traspaso.md through the folder move, so no template is seeded there."""
        p = self.p
        p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, log="docs/registros/traspaso.md"), indent=2) + "\n")
        p.write("docs/registros/traspaso.md", "# my log\n")
        p.write("docs/registros/revisado.txt", "abc\n")
        self.commit()
        code, out = p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertNotRegex(out, r"create\s+docs/records/traspaso\.md")
        self.applied()
        self.assertEqual(p.read("docs/records/traspaso.md"), "# my log\n")
        self.assertFalse(self.exists("docs/registros"))
        self.assertIn("nothing to do", self.applied())

    def test_a_log_missing_from_the_moved_folder_is_still_seeded(self):
        p = self.p
        p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, log="docs/registros/traspaso.md"), indent=2) + "\n")
        p.write("docs/registros/revisado.txt", "abc\n")
        self.commit()
        self.applied()
        self.assertTrue(self.exists("docs/records/traspaso.md"))

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

    def test_the_old_media_folder_moves_to_docs_media_with_git(self):
        p = self.p
        p.write("docs/difusion/proposals/2026-10-25.md", "# P\n")
        p.write("docs/difusion/2026-10-25/01-x/sheet.md", "# S\n")
        self.commit()
        p.write("docs/difusion/untracked.md", "u\n")
        out = self.applied()
        self.assertIn("move    docs/media  (from docs/difusion; gw-media-content: old default folder", out)
        self.assertFalse(self.exists("docs/difusion"))
        self.assertEqual(p.read("docs/media/proposals/2026-10-25.md"), "# P\n")
        self.assertEqual(p.read("docs/media/2026-10-25/01-x/sheet.md"), "# S\n")
        self.assertEqual(p.read("docs/media/untracked.md"), "u\n")
        status = p.run("git", "status", "--short")[1]
        self.assertIn("docs/difusion/proposals/2026-10-25.md -> docs/media/proposals/2026-10-25.md", status)
        self.assertIn("nothing to do", self.applied())  # twice: a no-op

    def test_an_untracked_old_media_folder_moves_too(self):
        self.p.write("docs/difusion/a.md", "a\n")
        self.applied()
        self.assertEqual(self.p.read("docs/media/a.md"), "a\n")
        self.assertFalse(self.exists("docs/difusion"))

    def test_a_folder_the_note_names_is_never_moved(self):
        for folder in ("docs/difusion", "`docs/social`"):
            with self.subTest(folder=folder):
                p = self.p
                p.write(".claude/gw/gw-media-content.md", f"Folder: {folder}\n")
                p.write("docs/difusion/a.md", "a\n")
                self.applied()
                self.assertEqual(p.read("docs/difusion/a.md"), "a\n")
                self.assertFalse(self.exists("docs/media"))

    def test_the_old_media_folder_move_fails_closed_when_docs_media_exists(self):
        p = self.p
        p.write("docs/difusion/a.md", "a\n")
        p.write("docs/media/b.md", "b\n")
        code, out = p.run_apply()
        self.assertEqual(code, 2, out)
        self.assertIn("cannot move docs/difusion to docs/media: docs/media already exists", out)
        self.assertEqual(p.read("docs/difusion/a.md"), "a\n")
        self.assertEqual(p.read("docs/media/b.md"), "b\n")
        self.assertFalse(self.exists(".claude/gw/scripts"))  # nothing else was written

    def test_dry_run_and_check_leave_the_old_media_folder_alone(self):
        p = self.p
        p.write("docs/difusion/a.md", "a\n")
        code, out = p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("move    docs/media  (from docs/difusion", out)
        self.assertEqual(p.run_apply("--check")[0], 1)
        self.assertTrue(self.exists("docs/difusion/a.md"))
        self.assertFalse(self.exists("docs/media"))

    def test_keep_paths_and_keep_legacy_paths_leave_the_old_media_folder_and_say_how_to_silence_doctor(self):
        p = self.p
        p.write("docs/difusion/a.md", "a\n")
        out = self.applied("--keep-paths")
        self.assertTrue(self.exists("docs/difusion/a.md"))
        self.assertFalse(self.exists("docs/media"))
        self.assertIn("docs/difusion is kept (--keep-paths); write `Folder: docs/difusion` in "
                      ".claude/gw/gw-media-content.md so doctor.py stops warning about it", out)
        p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, keepLegacyPaths=True), indent=2) + "\n")
        self.applied()  # set by hand it means the same
        self.assertTrue(self.exists("docs/difusion/a.md"))
        self.assertFalse(self.exists("docs/media"))

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



OLD_SCHEMA_CONFIG = {k: v for k, v in BASE_CONFIG.items() if k != "schemaVersion"}  # written before 0.5


class SchemaMigration(unittest.TestCase):
    """A9: a gw.json with an older schemaVersion (absent = 0) is written migrated, in one write of the file."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-schema-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)
        self.p.write(".claude/gw.json", json.dumps(OLD_SCHEMA_CONFIG, indent=2) + "\n")

    def config_lines(self, out):
        return [line for line in out.splitlines() if line.lstrip().startswith("merge") and ".claude/gw.json" in line]

    def test_dry_run_and_check_list_the_migration_and_write_nothing(self):
        p = self.p
        before = p.read(".claude/gw.json")
        code, out = p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        lines = self.config_lines(out)
        self.assertEqual(len(lines), 1, out)
        self.assertIn("schemaVersion 0 → 1: schemaVersion written", lines[0])
        code, out = p.run_apply("--check")
        self.assertEqual(code, 1, out)
        self.assertEqual(len(self.config_lines(out)), 1, out)
        self.assertIn("schemaVersion 0 → 1", out)
        self.assertEqual(p.read(".claude/gw.json"), before)

    def test_update_writes_it_after_version_and_keeps_the_rest(self):
        p = self.p
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        cfg = json.loads(p.read(".claude/gw.json"))
        self.assertEqual(cfg["schemaVersion"], 1)
        self.assertEqual(list(cfg)[:2], ["version", "schemaVersion"])
        self.assertEqual({k: v for k, v in cfg.items() if k != "schemaVersion"}, OLD_SCHEMA_CONFIG)
        code, out = p.run_apply("--check")
        self.assertNotIn(".claude/gw.json", "\n".join(self.config_lines(out)), out)
        self.assertEqual(code, 0, out)

    def test_one_write_when_the_old_paths_change_the_config_too(self):
        p = self.p
        old = {k: v for k, v in MIGRATED_CONFIG.items() if k != "schemaVersion"}
        p.write(".claude/gw.json", json.dumps(dict(old, log="docs/traspaso.md",
                                                   reviewMark="docs/registros/revisado.txt"), indent=2) + "\n")
        p.write("docs/traspaso.md", "# Log\n")
        p.write("docs/registros/revisado.txt", "abc\n")
        code, out = p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        lines = self.config_lines(out)
        self.assertEqual(len(lines), 1, out)
        self.assertIn("keys with the old paths dropped", lines[0])
        self.assertIn("schemaVersion 0 → 1", lines[0])
        code, out = p.run_apply()
        self.assertEqual(code, 0, out)
        cfg = json.loads(p.read(".claude/gw.json"))
        self.assertEqual(cfg["schemaVersion"], 1)
        self.assertNotIn("log", cfg)
        self.assertNotIn("reviewMark", cfg)
        self.assertEqual(p.read("docs/handoff.md"), "# Log\n")
        code, out = p.run_apply()
        self.assertIn("nothing to do", out)

    def test_one_write_with_keep_paths_too(self):
        p = self.p
        p.write("docs/traspaso.md", "# Log\n")
        p.write(".claude/gw.json", json.dumps({k: v for k, v in MIGRATED_CONFIG.items() if k != "schemaVersion"},
                                              indent=2) + "\n")
        code, out = p.run_apply("--keep-paths")
        self.assertEqual(code, 0, out)
        lines = self.config_lines(out)
        self.assertEqual(len(lines), 1, out)
        self.assertIn("--keep-paths:", lines[0])
        cfg = json.loads(p.read(".claude/gw.json"))
        self.assertEqual((cfg["schemaVersion"], cfg["log"], cfg["keepLegacyPaths"]), (1, "docs/traspaso.md", True))

    def test_a_newer_schema_version_fails_closed_and_writes_nothing(self):
        p = self.p
        p.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, schemaVersion=99), indent=2) + "\n")
        code, out = p.run_apply()
        self.assertEqual(code, 2, out)
        self.assertIn("schemaVersion 99 is newer than this copy of the workflow knows (1)", out)
        self.assertIn("/gw-update", out)
        self.assertFalse((p.work / ".claude" / "gw" / "scripts").exists())


def load_apply():
    spec = importlib.util.spec_from_file_location("apply_ci", APPLY_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CiSteps(unittest.TestCase):
    """D45: an update never deletes the project's own steps of .github/workflows/check.yml (portal P2, 0.5.0)."""

    CI = ".github/workflows/check.yml"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-ci-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)
        self.p.run_apply()
        self.template = self.p.read(self.CI)
        self.p.write(self.CI, self.template.replace(re.search(r"galivelop-workflow v\S+", self.template).group(0),
                                                    "galivelop-workflow v0.4.0", 1))

    def applied(self, *args):
        code, out = self.p.run_apply(*args)
        self.assertEqual(code, 0, out)
        return out

    def proposal(self):
        return self.p.work / (self.CI + ".gw-new")

    def project_edits(self):
        """The old copy with the project's node 22, a cache and a build step, as in the portal."""
        text = self.p.read(self.CI)
        text = text.replace("node-version: lts/*", "node-version: 22\n          cache: npm")
        text = text.replace("      - name: Check\n", "      - name: Build\n        run: npm run build\n      - name: Check\n")
        self.p.write(self.CI, text)
        return text

    def test_untouched_old_copy_is_updated_without_a_proposal(self):
        out = self.applied()
        self.assertEqual(self.p.read(self.CI), self.template, out)
        self.assertFalse(self.proposal().exists(), out)

    def test_project_added_steps_and_changed_values_are_kept_with_a_proposal(self):
        mine = self.project_edits()
        out = self.applied("--update")
        self.assertEqual(self.p.read(self.CI), mine, out)
        self.assertEqual(self.proposal().read_text(), self.template, out)
        self.assertIn("project's own lines", out)
        self.assertIn(f"diff {self.CI} {self.CI}.gw-new", out)
        self.assertIn("ciKeepSteps", out)
        self.assertIn("DELETE those lines", out)

    def test_template_changed_and_project_changed(self):
        text = self.p.read(self.CI).replace("      - name: Git hooks path\n", "      - name: Mine\n")
        self.p.write(self.CI, text)
        out = self.applied()
        self.assertEqual(self.p.read(self.CI), text, out)
        self.assertTrue(self.proposal().exists(), out)

    def test_old_template_lines_are_not_the_projects_own(self):
        old = self.p.read(self.CI).replace("python-version: ${{ matrix.python }}", "python-version: \"3.x\"")  # an older template's value
        self.p.write(self.CI, old)
        self.applied()
        self.assertFalse(self.proposal().exists())

    def test_missing_file_is_created(self):
        (self.p.work / self.CI).unlink()
        out = self.applied()
        self.assertEqual(self.p.read(self.CI), self.template, out)

    def test_existing_proposal_is_reported_and_not_rewritten(self):
        mine = self.project_edits()
        self.applied()
        mtime = self.proposal().stat().st_mtime_ns
        out = self.applied()
        self.assertEqual(self.proposal().stat().st_mtime_ns, mtime)
        self.assertEqual(self.p.read(self.CI), mine)
        self.assertIn("check.yml.gw-new", out)
        self.assertEqual(self.p.run_apply("--check")[0], 1)

    def test_stale_proposal_is_refreshed(self):
        mine = self.project_edits()
        self.proposal().write_text("old proposal\n")
        self.applied()
        self.assertEqual(self.proposal().read_text(), self.template)
        self.assertEqual(self.p.read(self.CI), mine)

    def test_merged_copy_at_the_current_version_is_up_to_date(self):
        self.project_edits()
        self.applied()
        merged = self.proposal().read_text().replace(
            "      - name: Check\n", "      - name: Build\n        run: npm run build\n      - name: Check\n")
        self.p.write(self.CI, merged)
        self.proposal().unlink()
        out = self.applied()
        self.assertEqual(self.p.read(self.CI), merged, out)
        self.assertFalse(self.proposal().exists(), out)
        code, out = self.p.run_apply("--check")
        self.assertEqual(code, 0, out)

    def test_merged_copy_missing_a_template_line_still_gets_a_proposal(self):
        self.p.write(self.CI, self.template.replace("      - name: Check\n", "      - name: Build\n      - name: Chk\n"))
        out = self.applied()
        self.assertTrue(self.proposal().exists(), out)
        self.assertIn("project's own lines (- name: Build; - name: Chk)", out)

    def test_newer_copy_with_own_lines_keeps_the_newer_message(self):
        text = self.project_edits().replace("galivelop-workflow v0.4.0", "galivelop-workflow v99.0.0", 1)
        self.p.write(self.CI, text)
        out = self.applied("--update")
        self.assertEqual(self.p.read(self.CI), text, out)
        self.assertIn("newer than the workflow's", out)
        self.assertNotIn("project's own lines", out)

    def test_changed_protected_branch_is_not_an_own_line(self):
        text = self.p.read(self.CI)
        self.assertIn("branches-ignore: [main]", text)
        self.p.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, protectedBranch="release"), indent=2) + "\n")
        out = self.applied()
        self.assertFalse(self.proposal().exists(), out)
        self.assertIn("branches-ignore: [release]", self.p.read(self.CI))

    def test_every_released_ci_template_has_no_own_lines(self):
        """The guard of templates/github/check.legacy-lines.txt: an untouched copy of any released version is updated."""
        code, tags = self.p.run("git", "-C", str(ROOT), "tag", "-l", "v*")
        tags = tags.split()
        if code or not tags:
            self.skipTest("no release tags in this clone (git fetch --tags)")
        apply_module = load_apply()
        lines = apply_module.CiLines((ROOT / "templates/github/check.yml").read_text(),
                                     (ROOT / apply_module.CI_LEGACY).read_text())
        cfg = dict(BASE_CONFIG, protectedBranch="trunk")
        for tag in tags:
            names = self.p.run("git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", tag, "--",
                               "templates/github/")[1].split()
            path = next(n for n in names if n.endswith((".yml", ".yaml")))
            raw = self.p.run("git", "-C", str(ROOT), "show", f"{tag}:{path}")[1]
            copy = apply_module.render(raw, cfg, self.p.work, tag[1:], path).encode()
            with self.subTest(tag=tag):
                self.assertEqual(lines.own(copy), [], f"add these lines of {tag} to {apply_module.CI_LEGACY}")

    def test_real_released_copy_is_updated_without_a_proposal(self):
        code, raw = self.p.run("git", "-C", str(ROOT), "show", "v0.4.3:templates/github/comprobar.yml")
        if code:
            self.skipTest("no tag v0.4.3 in this clone (git fetch --tags)")
        self.p.write(self.CI, raw.replace("{{protectedBranch}}", "main"))
        out = self.applied()
        self.assertEqual(self.p.read(self.CI), self.template, out)
        self.assertFalse(self.proposal().exists(), out)

    def test_ci_keep_steps_false_restores_the_replacement(self):
        self.project_edits()
        self.p.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, ciKeepSteps=False), indent=2) + "\n")
        out = self.applied("--update")
        self.assertEqual(self.p.read(self.CI), self.template, out)
        self.assertFalse(self.proposal().exists(), out)


class LegacyNames(unittest.TestCase):
    """D46: uses of the pre-A8 names in the project's own files are listed as warnings (file:line), never failing."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-legacy-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)
        self.p.write(".claude/gw.json", json.dumps(MIGRATED_CONFIG, indent=2) + "\n")

    def applied(self, *args):
        code, out = self.p.run_apply(*args)
        self.assertEqual(code, 0, out)
        return out

    def warnings(self, out):
        return [l for l in out.splitlines() if "uses the old name" in l]

    def test_silent_without_old_names(self):
        self.p.write("docs/notes.md", "run scripts/check-green.sh and see docs/handoff.md\n")
        self.assertEqual(self.warnings(self.applied()), [])

    def test_text_file_lists_line_and_new_name(self):
        self.p.write("docs/notes.md", "ok\nrun scripts/check-verde.sh and read docs/traspaso.md\n")
        out = self.applied()
        found = self.warnings(out)
        self.assertEqual(len(found), 2, out)
        self.assertIn("docs/notes.md:2 uses the old name check-verde.sh; replace it with check-green.sh", found[0])
        self.assertIn("docs/notes.md:2 uses the old name docs/traspaso.md; replace it with docs/handoff.md", found[1])
        self.assertIn("git grep -n -F", found[0])

    def test_check_mode_warns_and_dry_run_too_without_failing(self):
        self.p.write("README.md", "see .claude/skills/selector/SKILL.md\n")
        self.applied("--dry-run")
        out = self.p.run_apply("--check")[1]
        self.assertIn("README.md:1 uses the old name .claude/skills/selector; replace it with "
                      ".claude/skills/gw-selector", out)

    def test_binary_file_is_skipped(self):
        path = self.p.work / "data.bin"
        path.write_bytes(b"\x00\x01check-verde.sh\n")
        self.assertEqual(self.warnings(self.applied()), [])

    def test_files_the_workflow_installs_are_skipped(self):
        self.applied()  # installs the scripts, skills and hooks
        self.p.write(".claude/gw/scripts/mine.py", "# old: check-verde.sh\n")
        self.p.write(".claude/skills/gw-selector/extra.md", "docs/traspaso.md\n")
        self.p.write("docs/owned.md", "<!-- galivelop-workflow v0.1.0 -->\ndocs/traspaso.md\n")
        self.p.write(".claude/settings.json", json.dumps({"x": "check-verde.sh"}))
        self.assertEqual(self.warnings(self.applied("--update")), [])

    def test_ignored_files_and_dirs_are_skipped(self):
        self.p.write(".gitignore", "node_modules/\nsecret.md\n")
        self.p.write("node_modules/pkg/readme.md", "docs/traspaso.md\n")
        self.p.write("secret.md", "docs/traspaso.md\n")
        self.assertEqual(self.warnings(self.applied()), [])

    def test_name_inside_a_longer_name_is_not_a_use(self):
        self.p.write("docs/notes.md", "docs/registros-extra.md mydocs/traspaso.md "
                                      "scripts/xcheck-verde.sh .claude/skills/selector-x docs/traspaso.mdx\n")
        self.assertEqual(self.warnings(self.applied()), [])

    def test_switch_off_and_cap(self):
        self.p.write("docs/notes.md", "docs/traspaso.md\ndocs/traspaso.md\ndocs/traspaso.md\n")
        self.p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, legacyNamesMax=1), indent=2) + "\n")
        out = self.applied()
        self.assertEqual(len(self.warnings(out)), 1, out)
        self.assertIn("2 more use(s) of old names not listed; raise legacyNamesMax", out)
        self.p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, legacyNames=False), indent=2) + "\n")
        self.assertEqual(self.warnings(self.applied()), [])

    def test_keep_legacy_paths_does_not_warn_about_docs_paths(self):
        self.p.write("docs/notes.md", "docs/traspaso.md and check-verde.sh\n")
        self.p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, keepLegacyPaths=True,
                                                         log="docs/traspaso.md"), indent=2) + "\n")
        self.p.write("docs/traspaso.md", "# Log\n")
        found = self.warnings(self.applied())
        self.assertEqual(len(found), 1, found)
        self.assertIn("check-verde.sh", found[0])

    # ---- review fixes

    def test_plan_is_applied_to_the_scan(self):
        p = self.p
        p.write("docs/traspaso.md", "# Log\nrun check-verde.sh\n")
        p.write("docs/registros/release-v0.1.0.md", "check-verde.sh\n")
        p.write(".claude/gw/selector.md", "check-verde.sh\n")
        p.write(".claude/skills/selector/SKILL.md", SKILL_MD.format(n="selector"))
        p.write(".claude/skills/selector/extra.md", "check-verde.sh\n")
        p.write("docs/difusion/post.md", "check-verde.sh\n")
        self.p.run("git", "add", "-A")
        self.p.run("git", "commit", "-qm", "x")
        out = self.applied("--update")
        found = self.warnings(out)
        self.assertEqual(len(found), 2, out)  # the moved note and the media post, at their destinations
        self.assertIn(".claude/gw/selector.md:1 (moved to .claude/gw/gw-selector.md) uses the old name", found[0])
        self.assertIn("docs/difusion/post.md:1 (moved to docs/media/post.md) uses the old name check-verde.sh",
                      found[1])
        self.assertNotIn("docs/traspaso.md:", out.replace("old name docs/traspaso.md", ""))
        self.assertNotIn("extra.md:1", out)  # under a removed folder
        self.assertNotIn("release-v0.1.0.md:1", out)  # recordsDir: history

    def test_merged_agents_and_claude_are_scanned(self):
        self.applied()
        for name in ("AGENTS.md", "CLAUDE.md"):
            with (self.p.work / name).open("a") as f:
                f.write("\nRun scripts/check-verde.sh\n")
        found = self.warnings(self.applied())
        self.assertEqual(sorted(l.split(" uses")[0].split("apply: WARNING: ")[1].split(":")[0] for l in found),
                         ["AGENTS.md", "CLAUDE.md"], found)

    def test_bare_old_ci_file_and_media_folder_are_names(self):
        self.p.write("README.md", "![ci](https://x/actions/workflows/comprobar.yml/badge.svg) docs/difusion/a.md\n")
        found = self.warnings(self.applied())
        self.assertEqual(len(found), 2, found)
        self.assertIn("old name comprobar.yml; replace it with check.yml", found[0])
        self.assertIn("old name docs/difusion; replace it with docs/media", found[1])

    def test_project_notes_are_scanned(self):
        self.p.write(".claude/gw/gw-opt-tokens.md", "mine: run check-verde.sh\n")
        found = self.warnings(self.applied())
        self.assertEqual(len(found), 1, found)
        self.assertIn(".claude/gw/gw-opt-tokens.md:1", found[0])

    def test_history_is_skipped_and_the_skip_is_configurable(self):
        p = self.p
        p.write("CHANGELOG.md", "check-verde.sh\n")
        p.write("docs/handoff.md", "check-verde.sh\n" * 5)
        p.write("docs/proposals/a.md", "check-verde.sh\n")
        p.write("docs/old/a.md", "check-verde.sh\n")
        self.assertEqual(len(self.warnings(self.applied())), 1)  # only docs/old/a.md
        p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, legacyNamesSkip=["docs/old/*"]), indent=2) + "\n")
        out = self.applied()
        self.assertEqual([l.split(" uses")[0].split(": ")[-1] for l in self.warnings(out)], ["CHANGELOG.md:1"], out)

    def test_keep_paths_flag_of_this_run_is_respected(self):
        self.p.write("docs/traspaso.md", "# Log\n")
        self.p.write("docs/notes.md", "see docs/traspaso.md\n")
        self.assertEqual(self.warnings(self.applied("--keep-paths", "--dry-run")), [])

    def test_user_git_config_does_not_hide_the_warnings(self):
        self.p.write("docs/n.md", "run check-verde.sh\n")
        for key, value in (("color.ui", "always"), ("color.grep", "always"), ("grep.column", "true"),
                           ("grep.lineNumber", "false"), ("grep.fullName", "true")):
            self.p.run("git", "config", key, value)
        found = self.warnings(self.applied())
        self.assertEqual(len(found), 1, found)
        self.assertIn("docs/n.md:1 uses the old name check-verde.sh", found[0])

    def test_git_grep_failure_is_a_warning_not_a_failure(self):
        from unittest import mock
        spec = importlib.util.spec_from_file_location("apply_grep", APPLY_SCRIPT)
        apply_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(apply_module)
        plan = apply_module.Plan(self.p.work, VERSION, False)
        failed = subprocess.CompletedProcess([], 128, b"", b"fatal")
        with mock.patch.object(apply_module.subprocess, "run", return_value=failed):
            apply_module.plan_legacy_names(plan, dict(MIGRATED_CONFIG), set(), False)
        self.assertEqual(len(plan.warnings), 1)
        self.assertIn("could not run (git grep exit 128); check it by hand: git -C", plan.warnings[0])

    def test_not_a_git_repo_is_refused_as_before(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        code, out = self.p.run("python3", str(APPLY_SCRIPT), str(plain))
        self.assertEqual(code, 2, out)
        self.assertIn("is not inside a git repository", out)


if __name__ == "__main__":
    unittest.main()
