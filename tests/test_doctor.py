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
        for name in ("revision-antes-de-main.sh", "antes-de-parar.py", "guardia-config.py", "tope-subagentes.py"):
            shutil.copy2(ROOT / "scripts" / name, p.scripts / name)
        shutil.copy2(ROOT / "templates" / "claude" / "settings.json", p.work / ".claude" / "settings.json")
        shutil.copy2(ROOT / "templates" / "githooks" / "commit-msg", p.work / ".githooks" / "commit-msg")
        p.write(".github/workflows/check.yml", "name: check\njobs:\n  c:\n    steps:\n      - run: bash check.sh\n")
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

    def test_older_stop_hook_runs_twice(self):
        s = self.settings()
        s["hooks"]["Stop"].append({"hooks": [{"type": "command", "command": "python3 .claude/hooks/antes-de-parar.py"}]})
        self.save_settings(s)
        (self.p.work / ".claude" / "hooks").mkdir()
        (self.p.work / ".claude" / "hooks" / "antes-de-parar.py").write_text(
            f"#!/usr/bin/env python3\n# galivelop-workflow v{VERSION}\n")
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "settings Stop", "outside .claude/gw/scripts/", "delete that entry")

    def test_older_config_guard_runs_twice(self):
        s = self.settings()
        s["hooks"]["PreToolUse"].append({"matcher": "Edit|Write", "hooks": [
            {"type": "command", "command": "python3 .claude/hooks/guardia-config.py"}]})
        self.save_settings(s)
        (self.p.work / ".claude" / "hooks").mkdir()
        (self.p.work / ".claude" / "hooks" / "guardia-config.py").write_text(
            f"#!/usr/bin/env python3\n# galivelop-workflow v{VERSION}\n")
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "settings PreToolUse", "outside .claude/gw/scripts/", "delete that entry")

    def test_missing_config_guard_script_fails(self):
        (self.p.scripts / "guardia-config.py").unlink()
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "settings PreToolUse", "guardia-config.py", "does not exist")

    def test_older_subagent_cap_runs_twice(self):
        s = self.settings()
        s["hooks"]["PreToolUse"].append({"matcher": "Agent", "hooks": [
            {"type": "command", "command": "python3 .claude/hooks/tope-subagentes.py"}]})
        self.save_settings(s)
        (self.p.work / ".claude" / "hooks").mkdir()
        (self.p.work / ".claude" / "hooks" / "tope-subagentes.py").write_text(
            f"#!/usr/bin/env python3\n# galivelop-workflow v{VERSION}\n")
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "settings PreToolUse", "outside .claude/gw/scripts/", "delete that entry")

    def test_missing_subagent_cap_script_fails(self):
        (self.p.scripts / "tope-subagentes.py").unlink()
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "settings PreToolUse", "tope-subagentes.py", "does not exist")

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

    def test_empty_workflows_folder_warns(self):
        for f in (self.p.work / ".github" / "workflows").iterdir():
            f.unlink()
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "no CI workflow", "comprobar.yml")

    def test_ci_that_already_runs_the_check_is_not_asked_for_comprobar_yml(self):
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        line = self.assertLine(out, "OK", "ci", "check.yml run(s) the check")
        self.assertNotIn("comprobar.yml", line)
        self.assertNotIn("WARN  ci", out)

    def test_ci_that_does_not_run_the_check_proposes_comprobar_yml_or_the_pre_commit_step(self):
        self.p.write(".github/workflows/deploy.yml", "name: deploy\njobs:\n  d:\n    steps:\n      - run: ./deploy.sh\n")
        (self.p.work / ".github" / "workflows" / "check.yml").unlink()
        self.p.commit("only deploy")
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "deploy.yml", "none seems to run", "comprobar.yml", "pre-commit --rango")

    def test_ci_check_command_in_a_comment_or_a_longer_command_does_not_count(self):
        for body in ("name: x\njobs:\n  c:\n    steps:\n      # - run: bash check.sh\n      - run: ./deploy.sh\n",
                     "name: x\njobs:\n  c:\n    steps:\n      - run: bash check.sh-fast\n"):
            with self.subTest(body=body):
                (self.p.work / ".github" / "workflows" / "check.yml").unlink(missing_ok=True)
                self.p.write(".github/workflows/check.yml", body)
                self.p.commit("ci")
                code, out = self.doctor()
                self.assertLine(out, "WARN", "check.yml", "none seems to run")

    def test_ci_check_command_followed_by_a_boundary_counts(self):
        for body in ("      - run: bash check.sh\n", "      - run: bash check.sh && echo ok\n",
                     "      - run: bash check.sh; echo\n", "      - run: |\n          bash check.sh"):
            with self.subTest(body=body):
                self.p.write(".github/workflows/check.yml", "name: x\njobs:\n  c:\n    steps:\n" + body)
                self.p.commit("ci")
                code, out = self.doctor()
                self.assertLine(out, "OK", "ci", "check.yml run(s) the check")

    def test_ci_from_the_workflow_template_counts_as_running_the_check(self):
        (self.p.work / ".github" / "workflows" / "check.yml").unlink()
        self.p.write(".github/workflows/comprobar.yml", (ROOT / "templates" / "github" / "comprobar.yml").read_text())
        code, out = self.doctor()
        self.assertLine(out, "OK", "ci", "comprobar.yml run(s) the check")

    def test_missing_setup_command_warns(self):
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg["setup"] = ["no-such-setup-tool-xyz --build"]
        self.p.write(".claude/gw.json", json.dumps(cfg))
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "setup command", "no-such-setup-tool-xyz")

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

    def test_negated_gitignore_rule_is_not_ignored(self):
        # git check-ignore -v exits 0 on a matching `!` rule too: the file is un-ignored, not ignored
        self.p.write(".gitignore", ".claude/*\n!.claude/settings.json\n")
        self.p.git("rm", "-q", "--cached", ".claude/settings.json")
        code, out = self.doctor()
        self.assertNotIn(".claude/settings.json by", out)

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

    def test_invisible_characters_in_instructions_fail_with_the_fix(self):
        self.p.write("AGENTS.md", "# Rules\n\nDeal work to subagents (skill orchestrate-dealer).\nhid\u200bden\n")
        self.p.write(".claude/skills/selector/SKILL.md",
                     SKILL.format(version=VERSION).replace("Pick", "Pi\u202eck"))
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "invisible", "AGENTS.md", "line 4 col 4 U+200B", "remove them: python3 -c")
        self.assertLine(out, "FAIL", "invisible", ".claude/skills/selector/SKILL.md", "U+202E")
        self.p.write("AGENTS.md", "\ufeff# Rules\n\nDeal work to subagents (skill orchestrate-dealer).\n")
        self.p.write(".claude/skills/selector/SKILL.md", SKILL.format(version=VERSION))
        code, out = self.doctor()  # a BOM as the first character is allowed
        self.assertEqual(code, 0, out)
        self.assertLine(out, "OK", "instructions")

    def test_the_fix_command_for_invisible_characters_works(self):
        self.p.write("AGENTS.md", "# Rules\n\nDeal work (orchestrate-dealer).\nhid\u200bden\u2066\n")
        line = self.assertLine(self.doctor()[1], "FAIL", "invisible", "AGENTS.md")
        command = line.split("remove them: ", 1)[1]
        code, out = self.p.run("bash", "-c", command, cwd=self.p.work)
        self.assertEqual(code, 0, out)
        self.assertEqual((self.p.work / "AGENTS.md").read_text(encoding="utf-8"),
                         "# Rules\n\nDeal work (orchestrate-dealer).\nhidden\n")

    def test_zero_width_joiner_in_an_emoji_passes_and_a_lone_one_fails_with_a_fix_that_keeps_the_emoji(self):
        emoji = "\U0001F469\u200d\U0001F4BB"
        self.p.write("AGENTS.md", f"# Rules {emoji}\n\nDeal work to subagents (skill orchestrate-dealer).\n")
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "OK", "instructions")
        self.p.write("AGENTS.md", f"# Rules {emoji}\n\nDeal work (orchestrate-dealer).\nhid\u200dden {emoji}\u200d\n")
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        line = self.assertLine(out, "FAIL", "invisible", "AGENTS.md", "line 4 col 4 U+200D", "line 4 col 12 U+200D")
        code, out = self.p.run("bash", "-c", line.split("remove them: ", 1)[1], cwd=self.p.work)
        self.assertEqual(code, 0, out)
        self.assertEqual((self.p.work / "AGENTS.md").read_text(encoding="utf-8"),
                         f"# Rules {emoji}\n\nDeal work (orchestrate-dealer).\nhidden {emoji}\n")
        self.assertLine(self.doctor()[1], "OK", "instructions")

    def test_long_instruction_files_warn_then_fail(self):
        base = "# Rules\n\nDeal work to subagents (skill orchestrate-dealer).\n"
        self.p.write("AGENTS.md", base + "line\n" * 148)  # 151 lines
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "size", "AGENTS.md has 151 lines", "warn above 150", "move detail out")
        self.p.write("AGENTS.md", base + "line\n" * 147)  # 150 lines: still fine
        self.assertNotIn("size:", self.doctor()[1])
        self.p.write("CLAUDE.md", base + "line\n" * 248)  # 251 lines
        code, out = self.doctor()
        self.assertEqual(code, 1, out)
        self.assertLine(out, "FAIL", "size", "CLAUDE.md has 251 lines", "fail above 250")

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

    def test_cloud_session_started_in_home_user_is_not_outside(self):
        self.p.transcript(Path("/home/user"), [{"type": "user", "message": {"content": "x"}}])
        code, out = self.doctor_env({"CLAUDE_CODE_REMOTE": "true"})
        self.assertEqual(code, 0, out)
        self.assertLine(out, "OK", "session", "cloud session: it starts in /home/user", "checked under compaction")
        self.assertNotIn("outside the repo", out)

    def test_local_session_in_home_user_still_warns(self):
        self.p.transcript(Path("/home/user"), [{"type": "user", "message": {"content": "x"}}])
        code, out = self.doctor_env({"CLAUDE_CODE_REMOTE": ""})
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "session", "-home-user", "opened outside the repo")

    def test_cloud_session_in_another_folder_still_warns(self):
        self.p.transcript(self.tmp, [{"type": "user", "message": {"content": "x"}}])
        code, out = self.doctor_env({"CLAUDE_CODE_REMOTE": "true"})
        self.assertLine(out, "WARN", "session", "opened outside the repo")

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

    # --- CI access (retro 2026-10-25 P5)

    def ci_env(self, gh=None, token=None):
        """tools() PATH (no real gh) plus a fake `gh` whose `auth status` exits with `gh` (None = no gh), and a token."""
        env = self.tools()
        if gh is not None:
            fake = Path(env["PATH"]) / "gh"
            fake.write_text(f"#!/bin/sh\n[ \"$*\" = \"auth status --hostname github.com\" ] && exit {gh}\nexit 9\n")
            fake.chmod(0o755)
        env.update(GITHUB_TOKEN=token or "", GH_TOKEN="")
        return env

    def ci_lines(self, out):
        return [l for l in out.splitlines() if re.match(r"(OK|WARN|FAIL) +ci access:", l)]

    def github(self, url="https://github.com/galivelop/repo.git"):
        self.p.git("remote", "set-url", "origin", url)

    def test_github_https_remote_without_gh_nor_token_warns_with_the_fix(self):
        self.github()
        code, out = self.doctor_env(self.ci_env())
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "ci access", "neither `gh` is on PATH nor GITHUB_TOKEN/GH_TOKEN is set",
                        "AGENTS.md", "install GitHub CLI and run `gh auth login`, or export GITHUB_TOKEN")

    def test_github_ssh_remotes_warn_too(self):
        for url in ("git@github.com:galivelop/repo.git", "ssh://git@github.com/galivelop/repo.git"):
            self.github(url)
            out = self.doctor_env(self.ci_env())[1]
            self.assertLine(out, "WARN", "ci access", "neither `gh` is on PATH")

    def test_a_token_in_the_environment_is_enough_and_is_never_printed(self):
        self.github()
        value = "not-to-be-printed-1234"
        code, out = self.doctor_env(self.ci_env(token=value))
        self.assertEqual(code, 0, out)
        self.assertLine(out, "OK", "ci access", "GITHUB_TOKEN/GH_TOKEN is set")
        self.assertNotIn(value, out)
        env = self.ci_env()
        env.update(GH_TOKEN="x", GITHUB_TOKEN="")
        self.assertLine(self.doctor_env(env)[1], "OK", "ci access", "GITHUB_TOKEN/GH_TOKEN is set")

    def test_gh_logged_in_passes(self):
        self.github()
        code, out = self.doctor_env(self.ci_env(gh=0))
        self.assertEqual(code, 0, out)
        self.assertLine(out, "OK", "ci access", "`gh` is logged in")
        self.assertNotIn("WARN", "\n".join(self.ci_lines(out)))

    def test_gh_not_logged_in_warns_with_gh_auth_login(self):
        self.github()
        code, out = self.doctor_env(self.ci_env(gh=1))
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "ci access", "`gh auth status` fails", "run `gh auth login`")

    def test_gh_that_cannot_run_warns_instead_of_crashing(self):
        self.github()
        env = self.ci_env(gh=0)
        (Path(env["PATH"]) / "gh").write_text("#!/nonexistent/interpreter\n")  # exec fails with OSError
        code, out = self.doctor_env(env)
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "ci access", "`gh auth status` fails", "run `gh auth login`")

    def test_remote_elsewhere_or_missing_is_not_asked_for_ci_access(self):
        self.assertEqual(self.ci_lines(self.doctor_env(self.ci_env())[1]), [])  # local path
        for url in ("https://gitlab.com/galivelop/repo.git", "https://example.com/github.com/x.git",
                    "git@notgithub.com:x/y.git"):
            self.github(url)
            self.assertEqual(self.ci_lines(self.doctor_env(self.ci_env())[1]), [], url)
        self.p.git("remote", "remove", "origin")
        code, out = self.doctor_env(self.ci_env())
        self.assertEqual(self.ci_lines(out), [], out)

    # --- skill scripts without a test (WMF 2026-10-25 P2)

    def test_skill_script_without_a_test_warns_with_the_file_and_the_fix(self):
        self.p.write(".claude/skills/own/SKILL.md", "---\nname: own\n---\n")
        self.p.write(".claude/skills/own/scripts/tool.py", "print(1)\n")
        self.p.write(".claude/skills/own/scripts/__init__.py", "")
        self.p.write(".claude/skills/own/scripts/test_other.py", "")
        self.p.write(".claude/skills/own/scripts/sub/deep.py", "print(2)\n")
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        line = self.assertLine(out, "WARN", "skill tests", ".claude/skills/own/scripts/tool.py has no test next to it")
        self.assertIn("write .claude/skills/own/scripts/test_tool.py", line)
        self.assertEqual(out.count("WARN skill tests"), 1, out)  # __init__.py, a test_*.py and a subfolder: no warning

    def test_skill_script_with_its_test_passes(self):
        self.p.write(".claude/skills/own/scripts/tool.py", "print(1)\n")
        self.p.write(".claude/skills/own/scripts/test_tool.py", "")
        code, out = self.doctor()
        self.assertEqual(code, 0, out)
        self.assertLine(out, "OK", "skill tests", "every skill script has its test_<name>.py")

    def test_a_test_for_another_script_does_not_cover_it(self):
        self.p.write(".claude/skills/own/scripts/a.py", "")
        self.p.write(".claude/skills/own/scripts/b.py", "")
        self.p.write(".claude/skills/own/scripts/test_a.py", "")
        code, out = self.doctor()
        self.assertLine(out, "WARN", "skill tests", "scripts/b.py has no test", "scripts/test_b.py")
        self.assertNotIn("scripts/a.py has no test", out)

    # --- gw-media-content tools (WMF 2026-10-25 P1)

    def tools(self, node=True, magick=None, convert=None):
        """An env whose PATH holds only python3, git, bash and sh plus fake tools (and no NODE_PATH): magick/convert answer
        `-list format` with the text given (None = absent)."""
        bin_dir = self.tmp / "bin"
        shutil.rmtree(bin_dir, True)
        bin_dir.mkdir()
        for name in ("python3", "git", "bash", "sh"):
            (bin_dir / name).symlink_to(shutil.which(name))
        if node:
            (bin_dir / "node").write_text("#!/bin/sh\n")
        for name, formats in (("magick", magick), ("convert", convert)):
            if formats is not None:
                (bin_dir / name).write_text(f"#!/bin/sh\necho '{formats}'\n")
        for f in bin_dir.iterdir():
            if not f.is_symlink():
                f.chmod(0o755)
        return {"PATH": str(bin_dir), "NODE_PATH": ""}  # a host NODE_PATH may hold a global Playwright

    def media_lines(self, out):
        return [l for l in out.splitlines() if re.match(r"(OK|WARN|FAIL) +media tools:", l)]

    def use_media(self):
        self.p.write(".claude/gw/gw-media-content.md", "Folder: docs/social\n")

    def install_playwright(self, base):
        pw = base / "node_modules" / "playwright"
        pw.mkdir(parents=True)
        (pw / "package.json").write_text("{}")

    def test_project_that_does_not_use_gw_media_content_is_not_asked_for_its_tools(self):
        code, out = self.doctor_env(self.tools(node=False))
        self.assertEqual(code, 0, out)
        self.assertEqual(self.media_lines(out), [], out)

    def test_media_tools_all_present_passes(self):
        self.use_media()
        self.install_playwright(self.tmp)
        code, out = self.doctor_env(self.tools(magick="  WEBP* rw+ WebP"))
        self.assertEqual(code, 0, out)
        self.assertLine(out, "OK", "media tools", "node, Playwright, ImageMagick with WebP (magick) found")

    def test_missing_node_playwright_and_imagemagick_warn_with_their_fixes(self):
        self.use_media()
        code, out = self.doctor_env(self.tools(node=False))
        self.assertEqual(code, 0, out)
        self.assertLine(out, "WARN", "media tools", "node, which is not on PATH", "install Node.js")
        self.assertLine(out, "WARN", "media tools", "Playwright, which is not found", "GW_PLAYWRIGHT_DIR",
                        "npm i -D playwright && npx playwright install chromium")
        self.assertLine(out, "WARN", "media tools", "ImageMagick with WebP support, not found",
                        "apt install imagemagick webp")
        self.assertEqual(len(self.media_lines(out)), 3, out)

    def test_the_media_folder_alone_marks_the_project_as_a_user(self):
        (self.p.work / "docs" / "difusion").mkdir(parents=True)  # the default `Folder`
        code, out = self.doctor_env(self.tools(node=False))
        self.assertLine(out, "WARN", "media tools", "node")

    def test_the_folder_the_note_names_marks_the_project_as_a_user(self):
        self.p.write(".claude/gw/other.md", "x")  # a note of another skill is no signal
        self.assertEqual(self.media_lines(self.doctor_env(self.tools(node=False))[1]), [])
        (self.p.work / "docs" / "social").mkdir(parents=True)
        self.p.write(".claude/gw/gw-media-content.md", "Folder: `docs/social`\n")
        self.assertLine(self.doctor_env(self.tools(node=False))[1], "WARN", "media tools", "node")

    def test_imagemagick_without_webp_warns_and_convert_with_webp_counts(self):
        self.use_media()
        self.install_playwright(self.tmp)
        code, out = self.doctor_env(self.tools(magick="  PNG* rw- PNG", convert="  PNG* rw- PNG"))
        self.assertLine(out, "WARN", "media tools", "ImageMagick with WebP support, not found")
        self.assertEqual(len(self.media_lines(out)), 1, out)
        code, out = self.doctor_env(self.tools(magick="  PNG* rw- PNG", convert="  WEBP* rw+ WebP"))
        self.assertLine(out, "OK", "media tools", "ImageMagick with WebP (convert)")

    def test_playwright_resolved_from_gw_playwright_dir_or_a_parent_of_the_current_folder(self):
        self.use_media()
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        self.install_playwright(elsewhere)
        env = dict(self.tools(magick="WEBP"), GW_PLAYWRIGHT_DIR=str(elsewhere))
        self.assertLine(self.doctor_env(env)[1], "OK", "media tools", "Playwright")
        env = self.tools(magick="WEBP")
        env["NODE_PATH"] = str(elsewhere / "node_modules")
        self.assertLine(self.doctor_env(env)[1], "OK", "media tools", "Playwright")
        self.assertLine(self.doctor_env(self.tools(magick="WEBP"))[1], "WARN", "media tools", "Playwright")
        self.install_playwright(self.tmp)  # doctor runs in self.tmp; a node_modules above also resolves
        self.assertLine(self.doctor_env(self.tools(magick="WEBP"))[1], "OK", "media tools", "Playwright")


class TemplatesAgree(unittest.TestCase):
    def test_plugin_hooks_and_project_template_use_the_same_matchers_and_scripts(self):
        plugin = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]
        project = json.loads((ROOT / "templates" / "claude" / "settings.json").read_text())
        self.assertEqual(project["env"]["CLAUDE_CODE_AUTO_COMPACT_WINDOW"], "200000")
        project = project["hooks"]
        self.assertEqual(sorted(plugin), sorted(project))
        for event in plugin:
            mine = [(e.get("matcher"), [h["command"].rsplit("/", 1)[-1] for h in e["hooks"]]) for e in plugin[event]]
            theirs = [(e.get("matcher"), [h["command"].rsplit("/", 1)[-1] for h in e["hooks"]]) for e in project[event]]
            self.assertEqual(mine, theirs, event)


if __name__ == "__main__":
    unittest.main()
