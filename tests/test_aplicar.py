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
        self.env.update(GIT_CONFIG_GLOBAL=str(gitconfig), GIT_CONFIG_NOSYSTEM="1", TMPDIR=str(tmp), HOME=str(home))
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
        self.assertEqual(s["hooks"]["Stop"], mine["hooks"]["Stop"])
        self.assertEqual(s["hooks"]["SessionStart"][0], mine["hooks"]["SessionStart"][0])
        commands = [h["command"] for e in s["hooks"]["SessionStart"] + s["hooks"]["PreToolUse"] for h in e["hooks"]]
        for script in ("session-start.sh", "recuperar.py --estado", "revision-antes-de-main.sh"):
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


if __name__ == "__main__":
    unittest.main()
