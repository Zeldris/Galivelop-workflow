"""scripts/doctor.py on temporary projects: a fully set-up one passes; each broken piece gives its FAIL or WARN with
the command that fixes it. HOME points to a temp folder (no real ~/.claude); git runs isolated as in test_ganchos.
"""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from test_ganchos import ROOT, VERSION
from test_sesion import SessionProject

SKILL = """---
name: selector
description: Pick the skill.
metadata:
  version: "{version}"
  source: "Galivelop workshop"
---

# Selector
"""


class Doctor(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-doctor-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        p = self.p = SessionProject(self.tmp)
        shutil.copy2(ROOT / "scripts" / "revision-antes-de-main.sh", p.scripts / "revision-antes-de-main.sh")
        shutil.copy2(ROOT / "templates" / "claude" / "settings.json", p.work / ".claude" / "settings.json")
        p.write(".github/workflows/check.yml", "name: check\n")
        p.write("AGENTS.md", "# Rules\n\nDeal multi-step work to subagents (skill orchestrate-dealer).\n")
        p.write("docs/log.md", "# Log\n\n| Field | Value |\n|---|---|\n| Next step | write tests |\n")
        p.write(".claude/skills/selector/SKILL.md", SKILL.format(version=VERSION))
        p.commit("set up")

    def doctor(self, *args):
        return self.p.run("python3", str(self.p.scripts / "doctor.py"), *args, cwd=self.tmp)

    def settings(self):
        return json.loads((self.p.work / ".claude" / "settings.json").read_text())

    def save_settings(self, data):
        self.p.write(".claude/settings.json", json.dumps(data, indent=2))

    def assertLine(self, out, status, *needles):
        lines = [l for l in out.splitlines() if l.startswith(status)]
        for line in lines:
            if all(n in line for n in needles):
                return line
        self.fail(f"no {status} line with {needles} in:\n{out}")

    def test_fully_set_up_project_passes(self):
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertNotIn("FAIL", out)
        self.assertNotIn("WARN", out)
        code, out = self.doctor("--json")
        items = json.loads(out)
        self.assertTrue(items and all(i["status"] == "OK" for i in items), out)

    def test_missing_session_start_matcher(self):
        s = self.settings()
        del s["hooks"]["SessionStart"][0]["matcher"]
        self.save_settings(s)
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "no matcher", "startup|resume|clear")

    def test_compact_running_something_else(self):
        s = self.settings()
        s["hooks"]["SessionStart"][1]["hooks"].append(
            {"type": "command", "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/gw/scripts/session-start.sh"})
        self.save_settings(s)
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "on compact", "startup|resume|clear")

    def test_hook_command_to_a_missing_file(self):
        (self.p.scripts / "recuperar.py").unlink()
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", ".claude/gw/scripts/recuperar.py", "does not exist", "/gw-update")

    def test_missing_pr_guard(self):
        s = self.settings()
        del s["hooks"]["PreToolUse"]
        self.save_settings(s)
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "PreToolUse", "revision-antes-de-main.sh")

    def test_wrong_hook_version(self):
        hook = self.p.work / ".githooks" / "pre-push"
        hook.write_text(hook.read_text().replace(f"# galivelop-workflow v{VERSION}", "# galivelop-workflow v0.0.1", 1))
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "pre-push", "0.0.1", "/gw-update")

    def test_hook_not_executable(self):
        (self.p.work / ".githooks" / "pre-commit").chmod(0o644)
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "chmod +x .githooks/pre-commit")

    def test_hooks_path_unset_or_foreign(self):
        p = self.p
        p.git("config", "--unset", "core.hooksPath")
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "git config core.hooksPath .githooks")
        p.git("config", "core.hooksPath", ".husky")
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "another hook manager", ".husky/pre-push")

    def test_missing_log_next_step(self):
        self.p.write("docs/log.md", "# Log\n\nnothing here\n")
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "next-step", "Next step")
        self.p.write("docs/log.md", "# Log\n\n**SIGUIENTE PASO:** seguir\n")
        self.assertEqual(self.doctor()[0], 0)

    def test_unknown_check_command(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["check"] = ["no-such-tool-xyz run", "FOO=1 bash check.sh"]
        cfg["install"] = ["./missing-install.sh"]
        p.write(".claude/gw.json", json.dumps(cfg))
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "no-such-tool-xyz", "install no-such-tool-xyz")
        self.assertLine(out, "OK", "FOO=1 bash check.sh")
        self.assertLine(out, "WARN", "./missing-install.sh")

    def test_check_wrapper_must_exist(self):
        p = self.p
        cfg = json.loads((p.work / ".claude" / "gw.json").read_text())
        cfg["checkWrapper"] = "tools/qa/host.sh"
        p.write(".claude/gw.json", json.dumps(cfg))
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "checkWrapper", "'tools/qa/host.sh' is not a command on PATH nor a file in the repo")
        p.write("tools/qa/host.sh", "exec \"$@\"\n")
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "OK", "checkWrapper", "tools/qa/host.sh")

    def test_no_ci(self):
        shutil.rmtree(self.p.work / ".github")
        code, out = self.doctor()
        self.assertLine(out, "WARN", "no CI workflow", "comprobar.yml")

    def test_no_subagent_authorisation(self):
        self.p.write("AGENTS.md", "# Rules\n\nWork alone.\n")
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "orchestrate-dealer", "add to AGENTS.md")

    def test_stale_copied_skill(self):
        self.p.write(".claude/skills/selector/SKILL.md", SKILL.format(version="0.0.5"))
        self.p.write(".claude/skills/local/SKILL.md", "---\nname: local\nmetadata:\n  version: \"9\"\n  source: \"ours\"\n---\n")
        code, out = self.doctor()
        line = self.assertLine(out, "WARN", "selector (0.0.5)", "/gw-update")
        self.assertNotIn("local", line)

    def test_skill_citing_a_missing_license(self):
        self.p.write(".claude/skills/grilling/SKILL.md",
                     SKILL.format(version=VERSION).replace("---\n", "---\nlicense: MIT (see LICENSE-mattpocock-skills)\n", 1))
        code, out = self.doctor()
        self.assertLine(out, "WARN", "grilling cite LICENSE-mattpocock-skills", "/gw-update")
        self.p.write(".claude/skills/LICENSE-mattpocock-skills", "MIT\n")
        code, out = self.doctor()
        self.assertNotIn("cite LICENSE-mattpocock-skills", out)

    def test_git_ignored_workflow_files_fail(self):
        self.p.write(".gitignore", ".claude/*\n")
        self.p.git("rm", "-q", "--cached", ".claude/settings.json")  # as if just installed, before the first commit
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", ".claude/settings.json by .gitignore:1:.claude/*", "!.claude/settings.json")
        self.assertNotIn(".claude/gw.json by", out)  # tracked files are never ignored

    def test_pending_proposals_warn_and_hold_back_skills_ok(self):
        self.p.write(".claude/skills/selector/SKILL.md.gw-nuevo", "new\n")
        code, out = self.doctor()
        self.assertLine(out, "WARN", "1 pending .gw-nuevo proposal(s)",
                        "git diff --no-index .claude/skills/selector/SKILL.md .claude/skills/selector/SKILL.md.gw-nuevo")
        self.assertNotIn("OK   skills", out)

    def test_flow_script_run_from_another_folder_warns(self):
        path = self.p.work / ".claude" / "settings.json"
        settings = json.loads(path.read_text())
        settings["hooks"]["SessionStart"].append(
            {"matcher": "startup", "hooks": [{"type": "command", "command": "bash scripts/session-start.sh"}]})
        path.write_text(json.dumps(settings))
        (self.p.work / "scripts").mkdir()
        (self.p.work / "scripts" / "session-start.sh").write_text(f"#!/usr/bin/env bash\n# galivelop-workflow v{VERSION}\ntrue\n")
        code, out = self.doctor()
        self.assertLine(out, "WARN", "'bash scripts/session-start.sh' runs a workflow script from outside", "delete")

    def test_project_own_script_with_a_flow_name_does_not_warn(self):
        settings = self.settings()
        settings["hooks"]["SessionStart"].append(
            {"matcher": "startup", "hooks": [{"type": "command", "command": "bash scripts/session-start.sh"}]})
        self.save_settings(settings)
        self.p.write("scripts/session-start.sh", "#!/usr/bin/env bash\necho my own setup\n")
        self.p.commit("own hook")
        code, out = self.doctor()
        self.assertNotIn("runs a workflow script from outside", out)
        self.assertNotIn("WARN", out)

    def test_review_mark_ignored_by_git_fails(self):
        mark = json.loads((self.p.work / ".claude" / "gw.json").read_text())["reviewMark"]
        self.p.write(".gitignore", f"{mark}\n")
        self.p.commit("ignore the mark")
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", f"{mark} by .gitignore:1:{mark}", f"!{mark}")

    def test_next_steps_in_the_plural_are_accepted(self):
        self.p.write("docs/log.md", "# Log\n\n## Siguientes pasos\n\n1. write tests\n")
        self.assertLine(self.doctor()[1], "OK", "log", "has a next step")
        self.p.write("docs/log.md", "# Log\n\n## Next steps\n\n1. write tests\n")
        self.assertLine(self.doctor()[1], "OK", "log", "has a next step")

    def test_repeated_glossary_term_warns(self):
        self.p.write("GLOSSARY.md", "# Glossary\n\n- **Mark**: one.\n- **Other**: two.\n- **mark**: again.\n")
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "glossary", "same term twice: mark (line 3)", "merge the entries")
        self.p.write("GLOSSARY.md", "# Glossary\n\n- **Mark**: one.\n- **Other**: two.\n")
        self.assertLine(self.doctor()[1], "OK", "glossary")

    def test_invalid_config_fails_with_validate_command(self):
        (self.p.work / ".claude" / "gw.json").write_text("{}")
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "config", "validate")

    def test_session_opened_outside_the_repo(self):
        p = self.p
        p.transcript(self.tmp, [{"type": "user", "message": {"content": "x"}}])
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "outside the", f"cd {p.work} && claude")

    def test_cloud_session_without_the_compaction_window_warns(self):
        code, out = self.doctor_env({"CLAUDE_CODE_REMOTE": "true"})
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "compaction", "CLAUDE_CODE_AUTO_COMPACT_WINDOW=200000 to the cloud environment")

    def test_cloud_session_with_the_compaction_window_passes(self):
        code, out = self.doctor_env({"CLAUDE_CODE_REMOTE": "true", "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "200000"})
        self.assertEqual(code, 0, out)
        self.assertLine(out, "OK", "compaction", "200000")

    def test_cloud_session_warns_with_the_project_value(self):
        settings = self.settings()
        settings["env"]["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = "150000"
        self.save_settings(settings)
        code, out = self.doctor_env({"CLAUDE_CODE_REMOTE": "true"})
        self.assertLine(out, "WARN", "compaction", "CLAUDE_CODE_AUTO_COMPACT_WINDOW=150000 to the cloud environment")

    def test_project_without_a_compaction_window_says_nothing_about_it(self):
        settings = self.settings()
        del settings["env"]["CLAUDE_CODE_AUTO_COMPACT_WINDOW"]
        self.save_settings(settings)
        code, out = self.doctor_env({"CLAUDE_CODE_REMOTE": "true"})
        self.assertEqual(self.compaction_lines(out), [], out)

    def test_local_session_says_nothing_about_compaction(self):
        code, out = self.doctor()
        self.assertEqual(self.compaction_lines(out), [], out)

    def compaction_lines(self, out):
        return [l for l in out.splitlines() if re.match(r"(OK|WARN|FAIL) +compaction:", l)]

    def doctor_env(self, env):
        return self.p.run("python3", str(self.p.scripts / "doctor.py"), env=env, cwd=self.tmp)


class TemplatesAgree(unittest.TestCase):
    def test_plugin_hooks_and_project_template_use_the_same_matchers_and_scripts(self):
        plugin = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
        project = json.loads((ROOT / "templates" / "claude" / "settings.json").read_text())
        self.assertEqual(project["env"]["CLAUDE_CODE_AUTO_COMPACT_WINDOW"], "200000")
        project = project["hooks"]
        self.assertEqual(sorted(plugin), sorted(project))
        for event in plugin:
            mine = [(e["matcher"], [h["command"].rsplit("/", 1)[-1] for h in e["hooks"]]) for e in plugin[event]]
            theirs = [(e["matcher"], [h["command"].rsplit("/", 1)[-1] for h in e["hooks"]]) for e in project[event]]
            self.assertEqual(mine, theirs, event)


if __name__ == "__main__":
    unittest.main()
