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
import stat
import subprocess
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from test_hooks import BASE_CONFIG as HOOKS_CONFIG, ROOT

# A12: the fixtures are written as schemaVersion 2 has them (`languages` instead of `language`)
BLOCK = {"code": "en", "docs": {"primary": "en", "others": []}, "public": {"primary": "en", "others": []}, "ui": []}
BASE_CONFIG = {**{k: v for k, v in HOOKS_CONFIG.items() if k != "language"}, "schemaVersion": 2, "languages": BLOCK}

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
        self.write(".claude/gw.json", json.dumps({**BASE_CONFIG, "ciYamlCheck": False, **(config or {})}, indent=2) + "\n")  # E54: --update would add the E51 entry
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

    def test_gitattributes_merges_the_ledger_by_union(self):  # B32
        p = self.p
        mark = "# galivelop-workflow: the token ledger only grows, branches merge by keeping both\n"
        code, out = p.run_apply("--dry-run")  # shown in the dry run, nothing written
        self.assertEqual(code, 0, out)
        self.assertIn("create  .gitattributes  (merge the token ledger by keeping both sides: "
                      "docs/metrics/ledger.jsonl merge=union)", out)
        self.assertFalse((p.work / ".gitattributes").exists())
        self.assertIn(".gitattributes", self.applied())  # missing: created
        self.assertEqual(p.read(".gitattributes"), mark + "docs/metrics/ledger.jsonl merge=union\n")
        self.assertIn("merge: union", p.run("git", "check-attr", "merge", "docs/metrics/ledger.jsonl")[1])
        self.assertNotIn(".gitattributes", self.applied())  # already there: never a second line
        self.assertEqual(p.read(".gitattributes").count("merge=union"), 1)
        p.write(".gitattributes", "*.sh text eol=lf")  # the user's lines kept; no final newline: the line goes below
        self.applied()
        self.assertEqual(p.read(".gitattributes"), "*.sh text eol=lf\n" + mark + "docs/metrics/ledger.jsonl merge=union\n")
        p.write(".gitattributes", "/docs/metrics/ledger.jsonl linguist-generated merge=union\n")  # another form: left alone
        self.assertNotIn(".gitattributes", self.applied())
        p.write(".gitattributes", "docs/metrics/ledger.jsonl linguist-generated\n")  # the path without merge=union
        self.applied()
        self.assertTrue(p.read(".gitattributes").endswith(mark + "docs/metrics/ledger.jsonl merge=union\n"))
        self.assertEqual(p.run_apply("--check")[0], 0)

    def test_gitattributes_follows_the_configured_ledger(self):  # B32
        p = self.p
        cfg = json.loads(p.read(".claude/gw.json"))
        cfg["metrics"] = {"ledger": "var/spend log.jsonl"}
        p.write(".claude/gw.json", json.dumps(cfg, indent=2) + "\n")
        self.applied()
        self.assertTrue(p.read(".gitattributes").endswith('"var/spend log.jsonl" merge=union\n'))
        self.assertIn("merge: union", p.run("git", "check-attr", "merge", "var/spend log.jsonl")[1])
        self.assertNotIn("docs/metrics", p.read(".gitattributes"))

    def test_gitattributes_skips_a_ledger_outside_the_project(self):  # B36 review
        p = self.p
        cfg = json.loads(p.read(".claude/gw.json"))
        for ledger in ("../outside/ledger.jsonl", str(p.work / "docs" / "l.jsonl"), "/tmp/elsewhere/l.jsonl"):
            with self.subTest(ledger=ledger):
                cfg["metrics"] = {"ledger": ledger}
                p.write(".claude/gw.json", json.dumps(cfg, indent=2) + "\n")
                code, out = p.run_apply("--dry-run")
                self.assertEqual(code, 0, out)
                self.assertIn("is outside the project, so .gitattributes gets no merge=union line", out)
                self.assertNotIn(".gitattributes  (", out)
                self.applied()
                self.assertFalse((p.work / ".gitattributes").exists())

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

    def test_whole_read_is_applied_once_on_read(self):
        p = self.p
        out = self.applied()
        self.assertTrue((p.work / ".claude/gw/scripts/whole-read.py").is_file(), out)
        s = json.loads(p.read(".claude/settings.json"))
        reads = [e for e in s["hooks"]["PreToolUse"] if any("whole-read.py" in h["command"] for h in e["hooks"])]
        self.assertEqual(len(reads), 1, s["hooks"]["PreToolUse"])
        self.assertEqual(reads[0]["matcher"], "^(Read|Bash)$")
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

    def test_installs_the_gw_worker_agent_and_keeps_a_foreign_one(self):  # B28
        p = self.p
        self.applied()
        src = (ROOT / "templates/claude/agents/gw-worker.md").read_text()
        self.assertEqual(p.read(".claude/agents/gw-worker.md"), src)
        for field in ("name: gw-worker", "tools:", "model:", "effort:"):
            self.assertIn(field, src.split("---")[1])
        mine = "---\nname: gw-worker\n---\nmine\n"
        p.write(".claude/agents/gw-worker.md", mine)
        out = self.applied("--update")
        self.assertIn("propose .claude/agents/gw-worker.md.gw-new", out)
        self.assertIn("not workflow-owned", out)
        self.assertEqual(p.read(".claude/agents/gw-worker.md"), mine)

    def test_installs_the_gw_reviewer_agent(self):  # retro of the 0.7.0, T1
        self.applied()
        src = (ROOT / "templates/claude/agents/gw-reviewer.md").read_text()
        self.assertEqual(self.p.read(".claude/agents/gw-reviewer.md"), src)
        head = src.split("---")[1]
        for field in ("name: gw-reviewer", "model: opus", "effort:"):
            self.assertIn(field, head)
        tools = head.split("tools:")[1].split("\n")[0]
        for tool in ("Skill", "Read", "Bash"):
            self.assertIn(tool, tools)
        self.assertNotIn("mcp__", tools)

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
        p = Fixture(self.tmp / "es", {"languages": dict(BLOCK, docs={"primary": "es", "others": []})})
        code, out = p.run_apply()
        self.assertEqual(code, 0, out)
        self.assertIn(f"Flujo Galivelop-workflow v{VERSION}", out)
        self.assertIn("Siguiente:", out)

    # D128: a matcher the template changed must not leave the project's old entry running the hook twice
    def _whole_read_entries(self):
        s = json.loads(self.p.read(".claude/settings.json"))
        return s, [e for e in s["hooks"]["PreToolUse"] if any("whole-read.py" in h["command"] for h in e["hooks"])]

    def _downgrade_whole_read(self, extra=None):
        """Settings as 0.7.x left them: whole-read.py under the old matcher `Read` (plus optional `extra` hooks there)."""
        s, reads = self._whole_read_entries()
        reads[0]["matcher"] = "Read"
        if extra:
            reads[0]["hooks"].extend(extra)
        self.p.write(".claude/settings.json", json.dumps(s))

    def test_old_matcher_entry_of_a_template_command_is_dropped_on_update(self):
        self.applied()
        s, reads = self._whole_read_entries()
        s["hooks"]["PreToolUse"].append({"matcher": "Read", "hooks": list(reads[0]["hooks"])})  # runs twice
        self.p.write(".claude/settings.json", json.dumps(s))
        out = self.applied("--update")
        self.assertIn("PreToolUse hook removed from matcher (Read)", out)
        _, reads = self._whole_read_entries()
        self.assertEqual([e["matcher"] for e in reads], ["^(Read|Bash)$"])
        before = self.p.read(".claude/settings.json")
        out = self.applied("--update")
        self.assertEqual(self.p.read(".claude/settings.json"), before, "a second run changes nothing")
        self.assertNotIn("removed from matcher", out)

    def test_wider_project_matcher_of_a_template_command_is_kept_with_a_warning(self):  # D128 review
        self.applied()
        s, reads = self._whole_read_entries()
        s["hooks"]["PreToolUse"].append({"matcher": "Read|Bash|mcp__shell__run", "hooks": list(reads[0]["hooks"])})
        self.p.write(".claude/settings.json", json.dumps(s))
        out = self.applied("--update")
        _, reads = self._whole_read_entries()
        self.assertEqual([e["matcher"] for e in reads], ["^(Read|Bash)$", "Read|Bash|mcp__shell__run"])
        self.assertNotIn("removed from matcher", out)
        self.assertIn("PreToolUse registers a workflow command under the matcher 'Read|Bash|mcp__shell__run'", out)
        self.assertIn("kept, as it is wider than the template's", out)
        self.assertIn("delete that command from that entry", out)

    def test_070_settings_end_with_only_the_new_whole_read_matcher(self):
        self.applied()
        self._downgrade_whole_read()
        out = self.applied("--update")
        _, reads = self._whole_read_entries()
        self.assertEqual([e["matcher"] for e in reads], ["^(Read|Bash)$"], out)
        self.assertEqual(sum(h["command"].count("whole-read.py") for e in reads for h in e["hooks"]), 1)

    def test_dry_run_reports_the_removal_without_writing(self):
        self.applied()
        self._downgrade_whole_read()
        before = self.p.read(".claude/settings.json")
        code, out = self.p.run_apply("--update", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("removed from matcher (Read)", out)
        self.assertEqual(self.p.read(".claude/settings.json"), before)

    def test_project_own_hook_shares_the_old_entry_and_keeps_it(self):
        self.applied()
        own = {"type": "command", "command": "bash .claude/hooks/mine.sh"}
        self._downgrade_whole_read([own])  # the old `Read` entry holds whole-read.py and the project's own hook
        self.applied("--update")
        s, reads = self._whole_read_entries()
        self.assertEqual([e["matcher"] for e in reads], ["^(Read|Bash)$"])
        kept = [e for e in s["hooks"]["PreToolUse"] if own in e["hooks"]]
        self.assertEqual(len(kept), 1, s["hooks"]["PreToolUse"])
        self.assertEqual(kept[0]["matcher"], "Read")
        self.assertEqual(kept[0]["hooks"], [own], "only the template's command left that entry")

    def test_own_hook_alone_under_another_matcher_is_not_touched(self):
        self.applied()
        s = json.loads(self.p.read(".claude/settings.json"))
        own = {"matcher": "Read", "hooks": [{"type": "command", "command": "bash .claude/hooks/mine.sh"}]}
        s["hooks"]["PreToolUse"].append(own)
        self.p.write(".claude/settings.json", json.dumps(s))
        self.applied("--update")
        self.assertIn(own, json.loads(self.p.read(".claude/settings.json"))["hooks"]["PreToolUse"])


class AgentsSkills(unittest.TestCase):  # D7: the skills are also plain copies in agentsSkillsDir
    def make(self, config=None):
        tmp = Path(tempfile.mkdtemp(prefix="gw-apply-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        self.p = Fixture(tmp, config)
        return self.p

    def applied(self, *args):
        code, out = self.p.run_apply(*args)
        self.assertEqual(code, 0, out)
        return out

    def test_key_absent_uses_the_default_and_copies_are_identical_plain_files(self):
        p = self.make()
        self.applied()
        mine, theirs = p.work / ".claude" / "skills", p.work / ".agents" / "skills"
        self.assertEqual(p.read(".agents/skills/gw-selector/SKILL.md"), p.read(".claude/skills/gw-selector/SKILL.md"))
        self.assertEqual(p.read(".agents/skills/LICENSE-mattpocock-skills"), p.read(".claude/skills/LICENSE-mattpocock-skills"))
        self.assertEqual(sorted(x.name for x in mine.iterdir()), sorted(x.name for x in theirs.iterdir()))
        self.assertFalse(any(x.is_symlink() for x in theirs.rglob("*")))
        self.assertIn("nothing to do", self.applied())

    # ---- E67: a key absent from gw.json whose default creates files outside .claude/ is a decision

    def test_dry_run_presents_the_absent_key_as_a_decision_with_its_off_switch(self):
        self.make()
        n = len([1 for line in self.applied("--dry-run").splitlines() if line.startswith("  create  .agents/skills/")])
        self.assertGreater(n, 0)
        for args in (("--dry-run",), ("--dry-run", "--summary")):
            out = self.applied(*args)
            self.assertIn(f"  decide  agentsSkillsDir: creates {n} file(s) under .agents/skills/ (the default; the "
                          f"key is not in .claude/gw.json); to turn it off: \"agentsSkillsDir\": \"\"", out)
        self.assertFalse((self.p.work / ".agents").exists())

    def test_no_decision_when_the_key_is_written_or_nothing_is_created(self):
        for config in ({"agentsSkillsDir": ".agents/skills"}, {"agentsSkillsDir": ""}):
            self.make(config)
            self.assertNotIn("decide  ", self.applied("--dry-run", "--summary"))
        self.make()
        self.applied()
        self.assertNotIn("decide  ", self.applied("--update", "--dry-run", "--summary"))

    def test_empty_key_disables_the_second_copy(self):
        p = self.make({"agentsSkillsDir": ""})
        self.applied()
        self.assertTrue((p.work / ".claude" / "skills" / "gw-selector" / "SKILL.md").is_file())
        self.assertFalse((p.work / ".agents").exists())

    def test_custom_dir(self):
        p = self.make({"agentsSkillsDir": "tools/skills"})
        self.applied()
        self.assertTrue((p.work / "tools" / "skills" / "gw-selector" / "SKILL.md").is_file())
        self.assertFalse((p.work / ".agents").exists())

    def test_check_reports_a_missing_and_a_stale_copy(self):
        p = self.make()
        self.applied()
        skill = p.work / ".agents" / "skills" / "gw-selector"
        original = (skill / "SKILL.md").read_text()
        (skill / "SKILL.md").unlink()
        code, out = p.run_apply("--check")
        self.assertEqual(code, 1, out)
        self.assertIn("create  .agents/skills/gw-selector/SKILL.md", out)
        self.applied()
        (skill / "SKILL.md").write_text(original.replace(f'version: "{VERSION}"', 'version: "0.0.1"'))
        code, out = p.run_apply("--check")
        self.assertEqual(code, 1, out)
        self.assertIn("update  .agents/skills/gw-selector/SKILL.md", out)
        self.applied()
        self.assertEqual((skill / "SKILL.md").read_text(), original)

    def test_orphan_file_is_reported_and_kept(self):
        p = self.make()
        self.applied()
        extra = p.work / ".agents" / "skills" / "gw-selector" / "OLD.md"
        extra.write_text("gone upstream\n")
        out = self.applied()
        self.assertIn(".agents/skills/gw-selector/OLD.md is no longer in the workflow", out)
        self.assertTrue(extra.exists())

    def test_users_own_skill_with_a_workflow_name_is_kept_and_a_proposal_made(self):
        p = self.make()
        p.write(".agents/skills/gw-selector/SKILL.md", "---\nname: gw-selector\n---\nmine\n")
        out = self.applied()
        self.assertEqual(p.read(".agents/skills/gw-selector/SKILL.md"), "---\nname: gw-selector\n---\nmine\n")
        self.assertTrue((p.work / ".agents/skills/gw-selector/SKILL.md.gw-new").is_file(), out)

    def test_users_other_skill_is_left_alone(self):
        p = self.make()
        p.write(".agents/skills/my-skill/SKILL.md", "mine\n")
        out = self.applied()
        self.assertEqual(p.read(".agents/skills/my-skill/SKILL.md"), "mine\n")
        self.assertNotIn("my-skill", out)

    def test_unwanted_workflow_skill_copy_is_reported_as_orphan(self):
        p = self.make()
        self.applied("--with", "gw-opt-ai")
        shutil.rmtree(p.work / ".claude" / "skills" / "gw-opt-ai")  # the person uninstalls it
        out = self.applied()
        self.assertIn(".agents/skills/gw-opt-ai/SKILL.md is no longer in the workflow", out)
        self.assertTrue((p.work / ".agents/skills/gw-opt-ai/SKILL.md").exists())

    def test_workflow_copy_is_not_read_as_project_text_by_the_old_names_scan(self):
        p = self.make()
        out = self.applied()
        self.assertNotIn("WARNING: .agents/skills/", out)
        self.assertNotIn("uses the old name", out)

    def test_optional_skills_follow_with_in_both_dirs(self):
        p = self.make()
        self.applied()
        self.assertFalse((p.work / ".agents" / "skills" / "gw-opt-ai").exists())
        out = self.applied("--with", "gw-opt-ai")
        self.assertIn("create  .agents/skills/gw-opt-ai/SKILL.md", out)
        self.assertEqual(p.read(".agents/skills/gw-opt-ai/SKILL.md"), p.read(".claude/skills/gw-opt-ai/SKILL.md"))
        self.assertIn("nothing to do", self.applied())


class OwnedFiles(unittest.TestCase):  # D53
    HOOK = ".githooks/commit-msg"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-owned-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp, {"ownedFiles": [self.HOOK]})
        code, out = self.p.run_apply()
        self.assertEqual(code, 0, out)

    def test_differing_owned_file_is_kept_without_proposal_and_check_passes(self):
        p = self.p
        p.write(self.HOOK, "#!/bin/sh\n# the project's own hook\n")
        for args in ((), ("--update",), ("--check",)):
            code, out = p.run_apply(*args)
            self.assertEqual(code, 0, out)
            self.assertIn(f"owned by the project (ownedFiles): {self.HOOK}", out)
        self.assertEqual(p.read(self.HOOK), "#!/bin/sh\n# the project's own hook\n")
        self.assertFalse((p.work / (self.HOOK + ".gw-new")).exists())
        self.assertNotIn("pending proposal", p.run_apply("--check")[1])

    def test_not_owned_differing_file_still_gets_a_proposal(self):
        p = self.p
        p.write(".githooks/pre-commit", "#!/bin/sh\n# local\n")
        code, out = p.run_apply("--check")
        self.assertEqual(code, 1, out)
        self.assertIn(".githooks/pre-commit.gw-new", out)

    def test_leftover_proposal_is_a_warning_not_drift(self):
        p = self.p
        p.write(self.HOOK, "#!/bin/sh\n# own\n")
        p.write(self.HOOK + ".gw-new", "old proposal\n")
        code, out = p.run_apply("--check")
        self.assertEqual(code, 0, out)
        self.assertIn(f"WARNING: {self.HOOK}.gw-new is a leftover proposal", out)
        self.assertIn(f"rm {self.HOOK}.gw-new", out)
        self.assertNotIn("pending proposal", out)

    def test_missing_owned_file_is_created(self):
        p = self.p
        (p.work / self.HOOK).unlink()
        code, out = p.run_apply("--check")
        self.assertEqual(code, 1, out)
        self.assertIn(f"create  {self.HOOK}", out)
        self.assertEqual(p.run_apply()[0], 0)
        self.assertTrue((p.work / self.HOOK).is_file())

    def test_owned_file_the_workflow_no_longer_has_is_not_an_orphan(self):
        p = self.p
        p.write(".githooks/old-hook", "#!/bin/sh\n# galivelop-workflow v0.0.1\n")
        code, out = p.run_apply("--check")
        self.assertEqual(code, 1, out)
        self.assertIn("is no longer in the workflow", out)
        p.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, ownedFiles=[".githooks/old-*"])) + "\n")
        code, out = p.run_apply("--check")
        self.assertEqual(code, 0, out)
        self.assertIn("owned by the project (ownedFiles): .githooks/old-hook (no longer in the workflow)", out)


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
MIGRATED_CONFIG = {**{k: v for k, v in BASE_CONFIG.items() if k not in ("log", "reviewMark")}, "ciYamlCheck": False}


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

    def test_old_script_kept_by_every_real_way_of_running_it(self):
        """D52: variables, command substitutions, ./ and cd into the folder all keep the script (safe side)."""
        for line in ('python3 "$scripts/bitacora.py"', 'python3 "${scripts}/bitacora.py"',
                     'python3 "$here"/bitacora.py', 'python3 "${here}"/bitacora.py',
                     'python3 $(dirname "$0")/bitacora.py', 'python3 `dirname $0`/bitacora.py',
                     "cd .claude/gw/scripts && ./bitacora.py", "./bitacora.py",
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

    def snapshot(self):
        return sorted((str(f.relative_to(self.p.work)), f.read_bytes()) for f in self.p.work.rglob("*")
                      if f.is_file() and ".git/" not in str(f) + "/" and not str(f).endswith(".git"))

    def test_full_dry_run_shows_moves_once(self):
        self.old_paths()
        before = self.snapshot()
        code, out = self.p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("move    docs/handoff.md  (from docs/traspaso.md", out)
        self.assertNotIn("rename  ", out)  # no duplicates of the move lines
        self.assertEqual(before, self.snapshot())

    def test_summary_counts_and_lists_renames_without_the_per_file_lines(self):
        self.old_paths()
        before = self.snapshot()
        code, out = self.p.run_apply("--dry-run", "--summary")
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"\d+ create")
        self.assertIn("rename  docs/traspaso.md -> docs/handoff.md", out)
        self.assertNotIn("create  .githooks/pre-push", out)
        self.assertIn("summary only", out)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.exists("docs/handoff.md"))

    def test_summary_fresh_install_and_update_and_nothing_to_do(self):
        code, out = self.p.run_apply("--dry-run", "--summary")
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"\d+ create")
        self.assertNotIn("  rename", out)
        self.applied()
        raw = json.loads(self.p.read(".claude/gw.json"))
        self.p.write(".claude/gw.json", json.dumps(dict(raw, pendingFile="docs/records/pending.md")) + "\n")  # D129
        code, out = self.p.run_apply("--update", "--dry-run", "--summary")
        self.assertEqual(code, 0, out)
        self.assertIn("nothing to do", out)
        self.assertNotRegex(out, r"\d+ create")

    # ---- E52: template updates in the dry run

    def marked(self, rel, version, body="# mine\n"):
        self.p.write(rel, f"<!-- galivelop-workflow v{version} -->\n{body}")

    def has_tag(self, tag):
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
                              capture_output=True).returncode == 0

    def test_dry_run_review_diff_is_template_to_template(self):
        if not self.has_tag("v0.5.1"):
            self.skipTest("the workflow clone has no v0.5.1 tag")
        self.marked("REVIEW.md", "0.5.1", "# our own review rules\n")
        before = self.snapshot()
        code, out = self.p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("what the template changed (template v0.5.1 -> v", out)
        self.assertIn("--- REVIEW.md (template v0.5.1)", out)
        self.assertNotIn("our own review rules", out)  # the project's text is not in a template-to-template diff
        self.assertEqual(before, self.snapshot())

    def test_dry_run_review_unchanged_between_versions_says_so(self):
        if not self.has_tag("v0.6.0"):
            self.skipTest("the workflow clone has no v0.6.0 tag")
        self.marked("GLOSSARY.md", "0.6.0")
        code, out = self.p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("the template did not change between those versions; only set the marker line", out)

    def test_dry_run_fails_closed_to_the_old_diff_without_the_installed_tag(self):
        self.marked("REVIEW.md", "0.0.1", "# mine\n")
        code, out = self.p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("cannot read the v0.0.1 template of REVIEW.md (no tag v0.0.1", out)
        self.assertIn("git -C", out)
        self.assertIn("--tags", out)
        self.assertIn("+++ REVIEW.md (template)", out)

    def test_dry_run_without_template_changes_has_no_update_notes(self):
        self.applied()
        code, out = self.p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertNotIn("template update", out)
        self.assertNotIn("cannot read", out)

    def test_dry_run_reports_the_template_update_of_a_log_with_an_old_name(self):
        self.old_paths()
        self.marked("docs/traspaso.md", "0.5.1", "# Log\n")
        before = self.snapshot()
        code, out = self.p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("template update: docs/handoff.md comes from the v0.5.1 template", out)
        self.assertEqual(before, self.snapshot())
        self.assertTrue(self.exists("docs/traspaso.md"))
        code, out = self.p.run_apply("--dry-run", "--summary")
        self.assertIn("template update note(s)", out)

    def settings_with_old_hook(self):
        self.p.write(".claude/settings.json", json.dumps({"hooks": {"Stop": [{"hooks": [
            {"type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/gw/scripts/antes-de-parar.py"}]}]}}))

    def test_summary_lists_hook_renames_but_not_added_hooks(self):
        self.settings_with_old_hook()  # the template's other hooks are ADDED, not renamed
        code, out = self.p.run_apply("--dry-run", "--summary")
        self.assertEqual(code, 0, out)
        self.assertIn("rename  antes-de-parar.py -> before-stop.py", out)
        self.assertEqual(len([l for l in out.splitlines() if l.startswith("  rename")]), 1, out)
        self.assertNotIn("SessionStart hook", "\n".join(l for l in out.splitlines() if l.startswith("  rename")))

    def test_summary_lists_old_script_skill_and_skill_file_renames(self):
        p = self.p
        p.write(".claude/gw/scripts/bitacora.py", "# galivelop-workflow v0.4.3\n")
        p.write(".claude/skills/selector/SKILL.md", SKILL_MD.format(n="selector"))
        self.commit()
        code, out = p.run_apply("--dry-run", "--summary")
        self.assertEqual(code, 0, out)
        self.assertIn("rename  .claude/gw/scripts/bitacora.py -> .claude/gw/scripts/handoff.py", out)
        self.assertIn("rename  .claude/skills/selector -> .claude/skills/gw-selector", out)
        self.assertTrue(self.exists(".claude/gw/scripts/bitacora.py"))

    def test_summary_lists_renamed_skill_files(self):
        p = self.p
        self.applied()
        p.write(".claude/skills/gw-opt-tokens/scripts/medir.py", "x\n")
        self.commit()
        code, out = p.run_apply("--dry-run", "--summary")
        self.assertEqual(code, 0, out)
        self.assertIn("rename  .claude/skills/gw-opt-tokens/scripts/medir.py -> "
                      ".claude/skills/gw-opt-tokens/scripts/measure.py", out)

    def test_summary_shows_pending_orphans_and_hooks_path(self):
        p = self.p
        self.applied()
        p.run("git", "config", "--unset", "core.hooksPath")
        p.write(".claude/gw/scripts/gone.py", "# galivelop-workflow v0.1.0\n")
        code, out = p.run_apply("--dry-run", "--summary")
        self.assertEqual(code, 0, out)
        self.assertIn("core.hooksPath", out)
        self.assertIn("orphan  .claude/gw/scripts/gone.py", out)
        self.assertNotIn("nothing to do", out)

    def test_summary_only_hooks_path_is_not_empty(self):
        p = self.p
        self.applied()
        p.run("git", "config", "--unset", "core.hooksPath")
        code, out = p.run_apply("--dry-run", "--summary")
        self.assertEqual(code, 0, out)
        self.assertIn("core.hooksPath", out)

    def test_summary_without_dry_run_fails_with_the_fix(self):
        for flags in (("--summary",), ("--check", "--summary")):
            code, out = self.p.run_apply(*flags)
            self.assertEqual(code, 2, out)
            self.assertIn("--summary only goes with --dry-run", out)
            self.assertIn("--dry-run --summary", out)
        self.assertFalse(self.exists(".githooks"))

    def test_summary_rename_whose_target_exists_still_fails_closed(self):
        p = self.p
        p.write("docs/traspaso.md", "# Log\n")
        (p.work / "docs" / "handoff.md").mkdir()
        code, out = p.run_apply("--dry-run", "--summary")
        self.assertEqual(code, 2, out)
        self.assertIn("docs/handoff.md already exists", out)

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



OLD_SCHEMA_CONFIG = {**{k: v for k, v in HOOKS_CONFIG.items() if k != "schemaVersion"}, "ciYamlCheck": False}  # written before 0.5: has `language`


class ConfigVersion(unittest.TestCase):
    """B34: apply.py sets the project's gw.json "version" to the workflow's and keeps every other key."""

    def test_stale_version_is_set_and_the_other_keys_kept(self):
        tmp = Path(tempfile.mkdtemp(prefix="gw-ver-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        p = Fixture(tmp, {"version": "0.0.1", "commitTypes": ["feat", "fix"]})
        before = json.loads(p.read(".claude/gw.json"))
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertIn(f"version 0.0.1 -> {VERSION}", out)  # the detail names the version it came from
        after = json.loads(p.read(".claude/gw.json"))
        self.assertEqual(after["version"], VERSION)
        self.assertEqual({k: v for k, v in after.items() if k != "version"},
                         {k: v for k, v in before.items() if k != "version"})
        self.assertTrue(p.read(".claude/gw.json").endswith("}\n"))
        code, out = p.run_apply("--check")
        self.assertNotIn(".claude/gw.json", out)

    def test_a_project_newer_than_the_workflow_is_not_lowered(self):
        tmp = Path(tempfile.mkdtemp(prefix="gw-ver-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        p = Fixture(tmp, {"version": "9.9.9"})
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertNotIn("version 9.9.9", out)
        self.assertEqual(json.loads(p.read(".claude/gw.json"))["version"], "9.9.9")


class LanguagesInit(unittest.TestCase):
    """A12: --init writes the `languages` block; --update writes schemaVersion 2 from a config with the old keys."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-lang-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)

    def init(self, *args):
        (self.p.work / ".claude/gw.json").unlink(missing_ok=True)
        code, out = self.p.run_apply("--init", "--check-command", "true", *args)
        return code, out, (json.loads(self.p.read(".claude/gw.json")) if code == 0 else None)

    def test_default_block(self):
        code, out, cfg = self.init()
        self.assertEqual(code, 0, out)
        self.assertEqual((cfg["schemaVersion"], cfg["languages"]), (2, BLOCK))
        self.assertNotIn("language", cfg)
        self.assertNotIn("visibleLanguages", cfg)

    def test_language_fills_both_primaries_and_visible_language_fills_ui(self):
        code, out, cfg = self.init("--language", "es", "--visible-language", "es", "--visible-language", "gl")
        self.assertEqual(code, 0, out)
        self.assertEqual(cfg["languages"], {"code": "en", "docs": {"primary": "es", "others": []},
                                            "public": {"primary": "es", "others": []}, "ui": ["es", "gl"]})
        self.assertEqual(cfg["log"], "docs/handoff.md")

    def test_the_new_flags_are_repeatable_and_the_first_is_the_primary(self):
        code, out, cfg = self.init("--language", "en", "--code-language", "es", "--docs-language", "es",
                                   "--docs-language", "en", "--public-language", "en", "--public-language", "es")
        self.assertEqual(code, 0, out)
        self.assertEqual(cfg["languages"], {"code": "es", "docs": {"primary": "es", "others": ["en"]},
                                            "public": {"primary": "en", "others": ["es"]}, "ui": []})

    def test_an_invalid_code_fails_with_its_reason_and_writes_nothing(self):
        code, out, cfg = self.init("--docs-language", "Spanish")
        self.assertNotEqual(code, 0, out)
        self.assertIn("$.languages.docs.primary: 'Spanish' does not match", out)
        self.assertFalse((self.p.work / ".claude/gw.json").exists())

    def test_a_primary_repeated_in_others_is_refused_before_writing(self):
        code, out, cfg = self.init("--docs-language", "es", "--docs-language", "es")
        self.assertNotEqual(code, 0, out)
        self.assertIn("is already languages.docs.primary", out)
        self.assertFalse((self.p.work / ".claude/gw.json").exists())

    def test_code_language_takes_one_value(self):
        code, out, cfg = self.init("--code-language", "es", "--code-language", "en")
        self.assertEqual(code, 2, out)
        self.assertIn("--code-language takes one value", out)
        self.assertFalse((self.p.work / ".claude/gw.json").exists())

    def test_a_docs_language_without_templates_uses_the_english_ones(self):
        code, out, cfg = self.init("--docs-language", "gl")
        self.assertEqual(code, 0, out)
        self.assertNotIn("Traceback", out)
        self.assertEqual(cfg["languages"]["docs"]["primary"], "gl")
        self.assertTrue((self.p.work / "AGENTS.md").is_file())
        self.assertEqual(out.count("has no templates/gl/ folder, so the English templates (en) are used"), 1, out)
        self.assertIn("languages.docs.primary is 'gl'", out)

    def test_the_new_flags_need_init(self):
        code, out = self.p.run_apply("--docs-language", "es")
        self.assertEqual(code, 2, out)
        self.assertIn("--docs-language only go with --init", out)

    def test_update_writes_schema_2_from_the_old_keys(self):
        old = {k: v for k, v in HOOKS_CONFIG.items() if k != "language"}
        self.p.write(".claude/gw.json", json.dumps(dict(old, schemaVersion=1, language="es",
                                                        visibleLanguages=["es", "en"], ciYamlCheck=False),
                                                   indent=2) + "\n")
        code, out = self.p.run_apply("--update")
        self.assertEqual(code, 0, out)
        cfg = json.loads(self.p.read(".claude/gw.json"))
        self.assertEqual(cfg["schemaVersion"], 2)
        self.assertEqual(cfg["languages"], {"code": "en", "docs": {"primary": "es", "others": []},
                                            "public": {"primary": "es", "others": []}, "ui": ["es", "en"]})
        self.assertNotIn("language", cfg)
        self.assertNotIn("visibleLanguages", cfg)
        self.assertNotIn(".claude/gw.json", "\n".join(l for l in self.p.run_apply("--check")[1].splitlines()
                                                      if l.lstrip().startswith("merge")))


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
        self.assertIn("schemaVersion 0 → 2: schemaVersion written", lines[0])
        code, out = p.run_apply("--check")
        self.assertEqual(code, 1, out)
        self.assertEqual(len(self.config_lines(out)), 1, out)
        self.assertIn("schemaVersion 0 → 2", out)
        self.assertEqual(p.read(".claude/gw.json"), before)

    def test_update_writes_it_after_version_and_keeps_the_rest(self):
        p = self.p
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        cfg = json.loads(p.read(".claude/gw.json"))
        self.assertEqual(cfg["schemaVersion"], 2)
        self.assertEqual(list(cfg)[:2], ["version", "schemaVersion"])
        expected = {k: v for k, v in OLD_SCHEMA_CONFIG.items() if k != "language"}
        expected["languages"] = BLOCK  # A12: `language` "en" became the block
        self.assertEqual({k: v for k, v in cfg.items() if k not in ("schemaVersion", "languages")},
                         {k: v for k, v in expected.items() if k != "languages"})
        self.assertEqual(cfg["languages"], BLOCK)
        self.assertNotIn("language", cfg)
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
        self.assertIn("schemaVersion 0 → 2", lines[0])
        code, out = p.run_apply()
        self.assertEqual(code, 0, out)
        cfg = json.loads(p.read(".claude/gw.json"))
        self.assertEqual(cfg["schemaVersion"], 2)
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
        self.assertEqual((cfg["schemaVersion"], cfg["log"], cfg["keepLegacyPaths"]), (2, "docs/traspaso.md", True))

    def test_a_newer_schema_version_fails_closed_and_writes_nothing(self):
        p = self.p
        p.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, schemaVersion=99), indent=2) + "\n")
        code, out = p.run_apply()
        self.assertEqual(code, 2, out)
        self.assertIn("schemaVersion 99 is newer than this copy of the workflow knows (2)", out)
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

    def test_update_adds_workflow_call_to_a_copy_without_own_steps(self):
        """D63: an old copy of the workflow (no `workflow_call:`) is updated, not proposed, and gains it."""
        old = self.p.read(self.CI).replace("  workflow_call:\n", "", 1)
        self.assertNotIn("\n  workflow_call:\n", old)
        self.p.write(self.CI, old)
        out = self.applied("--update")
        self.assertIn("\n  workflow_call:\n", self.p.read(self.CI), out)
        self.assertFalse(self.proposal().exists(), out)

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

    def test_push_that_only_changes_the_metrics_ledger_does_not_run_ci(self):
        """D162: check.yml carries `paths-ignore` of `metrics.ledger` (the configured path) on push only."""
        text = self.p.read(self.CI)
        self.assertIn('    paths-ignore: ["docs/metrics/ledger.jsonl"]\n  pull_request:\n', text)
        cfg = dict(BASE_CONFIG, metrics={"ledger": "tele/l.jsonl"})
        self.p.write(".claude/gw.json", json.dumps(cfg, indent=2) + "\n")
        out = self.applied("--update")
        self.assertIn('paths-ignore: ["tele/l.jsonl"]', self.p.read(self.CI), out)

    def test_ci_ledger_path_is_normalized_and_a_glob_fails_closed(self):
        """D162: `./x` and `a//x` still match in paths-ignore once normalized; a glob fails with the fixing step."""
        for given, want in (("./tele/l.jsonl", "tele/l.jsonl"), ("tele//sub/./l.jsonl", "tele/sub/l.jsonl")):
            with self.subTest(ledger=given):
                self.p.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, metrics={"ledger": given}), indent=2) + "\n")
                out = self.applied("--update")
                self.assertIn(f'paths-ignore: ["{want}"]', self.p.read(self.CI), out)
        for glob in ("tele/*.jsonl", "tele/l?.jsonl", "tele/[ab].jsonl", "docs/c++/l.jsonl", "!tele/l.jsonl",
                     "tele\\l.jsonl"):
            with self.subTest(ledger=glob):
                self.p.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, metrics={"ledger": glob}), indent=2) + "\n")
                code, out = self.p.run_apply("--update")
                self.assertNotEqual(code, 0, out)
                self.assertIn("has a glob character", out)
                self.assertIn("edit metrics.ledger in", out)

    def test_ci_on_push_false_runs_check_yml_only_on_pull_requests_and_back(self):
        """D54: `ciOnPush: false` renders the push filter as every branch; the copy stays the workflow's."""
        self.p.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, ciOnPush=False), indent=2) + "\n")
        out = self.applied()
        text = self.p.read(self.CI)
        self.assertIn("    branches-ignore: ['**']\n", text, out)
        self.assertNotIn("branches-ignore: [main]", text)
        self.assertFalse(self.proposal().exists(), out)
        self.p.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, ciOnPush=True), indent=2) + "\n")
        out = self.applied("--update")  # same version: changing the key needs --update, as the docs say
        self.assertIn("branches-ignore: [main]", self.p.read(self.CI), out)
        self.assertFalse(self.proposal().exists(), out)

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

    def test_a_personal_note_created_in_the_same_run_is_a_new_name_that_exists(self):
        notes = self.tmp / "notes"
        notes.mkdir()
        (notes / "gw-selector.md").write_text("my selector notes\n")
        self.p.env["GW_PERSONAL_NOTES"] = str(notes)
        self.p.write("docs/notes.md", "see .claude/gw/selector.md\n")
        out = self.applied()
        self.assertTrue((self.p.work / ".claude/gw/gw-selector.md").is_file(), out)
        self.assertIn("docs/notes.md:1 uses the old name .claude/gw/selector.md; replace it with "
                      ".claude/gw/gw-selector.md", out)

    def test_check_mode_warns_and_dry_run_too_without_failing(self):
        self.p.write("README.md", "see .claude/skills/selector/SKILL.md\n")
        self.applied("--dry-run")
        out = self.p.run_apply("--check")[1]
        self.assertIn("README.md:1 uses the old name .claude/skills/selector; replace it with "
                      ".claude/skills/gw-selector", out)

    def test_a_dotted_agents_skills_dir_is_normalized_before_the_prefix_comparison(self):
        self.p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, agentsSkillsDir="./.agents/skills"), indent=2) + "\n")
        self.applied()
        skill = self.p.work / ".agents" / "skills" / "gw-selector" / "SKILL.md"
        self.assertTrue(skill.is_file())
        skill.write_text(skill.read_text() + "\nrun scripts/check-verde.sh\n")  # a workflow copy: not the project's text
        out = self.p.run_apply("--check")[1]
        self.assertNotIn(".agents/skills/gw-selector/SKILL.md:", "\n".join(self.warnings(out)))

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

    def test_dry_run_summary_gives_one_count_per_old_name(self):
        """D161: the summary prints one line per old name, not one per use."""
        self.p.write("docs/notes.md", "docs/traspaso.md\ndocs/traspaso.md\ndocs/traspaso.md\n")
        code, out = self.p.run_apply("--dry-run", "--summary")
        self.assertEqual(code, 0, out)
        lines = [l for l in out.splitlines() if "old name" in l or "old names" in l]
        self.assertEqual(len(lines), 1, out)
        self.assertIn("3 use(s) of the old name docs/traspaso.md", lines[0])
        self.assertIn("git grep -n -F 'docs/traspaso.md'", lines[0])
        self.assertNotIn("docs/notes.md:", out)
        self.assertIn("files in legacyNamesSkip not counted", lines[0])
        self.assertIn("its output may be longer", lines[0])

    def test_old_name_warning_says_git_grep_also_lists_the_skipped_files(self):
        """D161: the per-use line warns that the suggested git grep includes legacyNamesSkip files."""
        self.p.write("docs/notes.md", "docs/traspaso.md\n")
        out = self.applied()
        self.assertIn("files in legacyNamesSkip included, so the number may be higher", out)

    def test_summary_help_names_the_old_name_count(self):
        code, out = self.p.run_apply("--help")
        self.assertIn("count of uses per old name", " ".join(out.split()))

    def test_old_name_warning_suggests_legacy_names_skip_for_quotes_of_other_repos(self):
        """D165: the warning names the key that silences a file quoting another repo."""
        self.p.write("docs/notes.md", "docs/traspaso.md\n")
        out = self.applied()
        self.assertIn("docs/notes.md:1 uses the old name docs/traspaso.md", out)
        self.assertIn("if it quotes another repo's text, add the file to legacyNamesSkip", out)

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
        self.p.write("docs/media/b.md", "exists\n")
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

    # ---- D100: roadmapFiles are history; a new name the project lacks is not proposed

    def roadmap_cfg(self, files):
        cfg = dict(MIGRATED_CONFIG)
        if files is not None:
            cfg["roadmapFiles"] = files
        self.p.write(".claude/gw.json", json.dumps(cfg, indent=2) + "\n")

    def test_roadmap_files_are_skipped_other_files_are_not(self):
        self.roadmap_cfg([{"path": "docs/roadmap-front.md", "done": "x", "open": ["y"]}])
        self.p.write("docs/roadmap-front.md", "closed: run check-verde.sh\n")
        self.p.write("docs/notes.md", "run check-verde.sh\n")
        found = self.warnings(self.applied())
        self.assertEqual(len(found), 1, found)
        self.assertIn("docs/notes.md:1 uses the old name check-verde.sh", found[0])

    def test_roadmap_files_absent_or_empty_skip_nothing(self):
        self.p.write("docs/roadmap-front.md", "run check-verde.sh\n")
        for files in (None, []):
            self.roadmap_cfg(files)
            found = self.warnings(self.applied())
            self.assertEqual(len(found), 1, found)
            self.assertIn("docs/roadmap-front.md:1 uses the old name", found[0])

    def test_new_name_missing_in_project_is_not_proposed(self):
        # silent: a warning without a replacement would still send the reader to rename a text that is history
        self.p.write("docs/notes.md", "run docs/difusion/x.md\n")
        self.assertEqual(self.warnings(self.applied()), [])

    def test_roadmap_path_is_normalized(self):
        self.roadmap_cfg([{"path": ".\\docs\\roadmap-front.md", "done": "x", "open": ["y"]}])
        self.p.write("docs/roadmap-front.md", "run check-verde.sh\n")
        self.assertEqual(self.warnings(self.applied()), [])

    def test_ls_files_failure_warns_as_before(self):
        spec = importlib.util.spec_from_file_location("apply_lsf", APPLY_SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        plan = mod.Plan(self.p.work, VERSION, False)
        failed = subprocess.CompletedProcess([], 128, b"", b"fatal")
        with unittest.mock.patch.object(mod.subprocess, "run", return_value=failed):
            paths = mod.project_paths(plan)
        self.assertIsNone(paths)
        self.assertTrue(mod.name_exists(paths, "merge-branch.sh"))

    def test_name_on_disk_counts_even_if_ignored(self):
        self.p.write(".gitignore", ".claude/gw/\n")
        self.p.write(".claude/gw/scripts/merge-x.sh", "x\n")
        self.p.write("docs/notes.md", "docs/difusion/x.md\n")
        spec = importlib.util.spec_from_file_location("apply_disk", APPLY_SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertFalse(mod.name_exists(set(), "merge-x.sh"))
        self.assertTrue(mod.name_exists(set(), ".claude/gw/scripts/merge-x.sh", self.p.work))

    def test_name_exists_helper(self):
        spec = importlib.util.spec_from_file_location("apply_names", APPLY_SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        paths = {"/docs/media/a.md", "/.claude/gw/scripts/check-green.sh"}  # as project_paths gives them
        self.assertTrue(mod.name_exists(paths, "docs/media"))
        self.assertTrue(mod.name_exists(paths, "check-green.sh"))
        self.assertFalse(mod.name_exists(paths, "merge-branch.sh"))
        self.assertFalse(mod.name_exists(paths, "docs/medi"))

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


class ConditionalBlocks(unittest.TestCase):
    """D58: `<!-- if key -->` ... `<!-- /if -->` in a template, resolved by apply.py from a boolean config key."""

    NOTE = "Con logRows cada rama escribe en su fila."
    TEXT = "before\n<!-- if logRows -->\n" + NOTE + "\n<!-- /if -->\nafter\n"

    def setUp(self):
        spec = importlib.util.spec_from_file_location("apply_blocks", APPLY_SCRIPT)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)

    def blocks(self, text, cfg):
        return self.mod.conditional_blocks(text, cfg, "x.md")

    def test_true_key_drops_only_the_marker_lines(self):
        self.assertEqual(self.blocks(self.TEXT, {"logRows": True}), "before\n" + self.NOTE + "\nafter\n")

    def test_false_and_absent_keys_drop_the_whole_block(self):
        for cfg in ({"logRows": False}, {}):
            self.assertEqual(self.blocks(self.TEXT, cfg), "before\nafter\n", cfg)

    def test_a_removed_block_leaves_no_repeated_blank_line(self):
        text = "a\n\n<!-- if logRows -->\nx\n<!-- /if -->\n\nb\n\n\nc\n"
        self.assertEqual(self.blocks(text, {"logRows": False}), "a\n\nb\n\n\nc\n")  # existing doubles stay
        self.assertEqual(self.blocks(text, {"logRows": True}), "a\n\nx\n\nb\n\n\nc\n")

    def test_negated_key_keeps_the_block_only_when_explicitly_false(self):
        text = "a\n<!-- if !agentSignatures -->\nx\n<!-- /if -->\nb\n"
        self.assertEqual(self.blocks(text, {"agentSignatures": False}), "a\nx\nb\n")
        for cfg in ({"agentSignatures": True}, {}):  # absent is the default, true
            self.assertEqual(self.blocks(text, cfg), "a\nb\n", cfg)

    def test_any_boolean_key_and_odd_spacing(self):
        text = "a\n  <!--   if   otherKey-->  \nb\n<!--/if-->\nc\n"
        self.assertEqual(self.blocks(text, {"otherKey": True}), "a\nb\nc\n")
        self.assertEqual(self.blocks(text, {"otherKey": False}), "a\nc\n")

    def test_text_without_blocks_is_unchanged(self):
        self.assertEqual(self.blocks("a\n\nb", {}), "a\n\nb")

    def expect_error(self, text, *fragments):
        with self.assertRaises(self.mod.ApplyError) as cm:
            self.blocks(text, {"logRows": True})
        for fragment in fragments:
            self.assertIn(fragment, str(cm.exception))
        self.assertIn("fix the template in", str(cm.exception))

    def test_unclosed_block_is_an_error(self):
        self.expect_error("a\n<!-- if logRows -->\nb\n", "never closed", "logRows")

    def test_nested_block_is_an_error(self):
        self.expect_error("<!-- if logRows -->\n<!-- if other -->\nx\n<!-- /if -->\n<!-- /if -->\n", "do not nest")

    def test_close_without_open_and_open_without_key_are_errors(self):
        self.expect_error("a\n<!-- /if -->\n", "without an open")
        self.expect_error("<!-- if -->\nx\n<!-- /if -->\n", "needs a config key")

    def test_marker_inside_a_line_is_plain_text(self):
        text = "see <!-- if logRows --> here\n"
        self.assertEqual(self.blocks(text, {}), text)

    def apply_log(self, log_rows, update=False):
        tmp = Path(tempfile.mkdtemp(prefix="gw-apply-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        p = Fixture(tmp, {"log": "notes/log.md", "languages": dict(BLOCK, docs={"primary": "es", "others": []}), "logRows": log_rows})
        code, out = p.run_apply()
        self.assertEqual(code, 0, out)
        return p, p.read("notes/log.md")

    def test_the_seeded_log_explains_logrows_only_when_it_is_on(self):
        for log_rows, shown in ((True, True), (False, False)):
            _, log = self.apply_log(log_rows)
            self.assertEqual("Con `logRows` en" in log, shown, log_rows)
            self.assertNotIn("\n\n\n", log)
            self.assertNotIn("<!-- if", log)
            self.assertNotIn("<!-- /if", log)

    def test_update_of_an_installed_project_keeps_the_log(self):
        p, log = self.apply_log(False)
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.read("notes/log.md"), log)
        self.assertFalse((p.work / "notes" / "log.md.gw-new").exists())


class CiValidateMigration(unittest.TestCase):
    """E54: --update adds `ci-local.py --validate` (E51) to the `check` list of an installed project."""

    CMD = "python3 .claude/gw/scripts/ci-local.py --validate"

    def project(self, **config):
        tmp = Path(tempfile.mkdtemp(prefix="gw-civ-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        return Fixture(tmp, dict({"ciYamlCheck": True}, **config, version=VERSION))

    def check_list(self, p):
        return json.loads(p.read(".claude/gw.json"))["check"]

    def merge_lines(self, out):
        return [l for l in out.splitlines() if l.lstrip().startswith("merge") and ".claude/gw.json" in l]

    def test_missing_entry_is_added_before_tests_after_main_and_the_rest_keeps_its_order(self):
        old = ["make check", "python3 x.py", "python3 .claude/gw/scripts/tests-after-main.py"]
        p = self.project(check=old)
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.check_list(p), old[:2] + [self.CMD] + old[2:])
        p.run_apply("--update")  # not twice
        self.assertEqual(self.check_list(p).count(self.CMD), 1)

    def test_without_tests_after_main_it_goes_last(self):
        p = self.project(check=["make check"])
        p.run_apply("--update")
        self.assertEqual(self.check_list(p), ["make check", self.CMD])

    def test_present_in_any_form_is_left_alone(self):
        for entry in (self.CMD, "bash -c 'python3 scripts/ci-local.py --validate && true'"):
            p = self.project(check=["make check", entry])
            before = p.read(".claude/gw.json")
            code, out = p.run_apply("--update")
            self.assertEqual(code, 0, out)
            self.assertEqual(p.read(".claude/gw.json"), before, entry)

    def test_ci_yaml_check_off_is_respected(self):
        p = self.project(check=["make check"], ciYamlCheck=False)
        code, out = p.run_apply("--update")
        self.assertEqual(self.check_list(p), ["make check"], out)

    def test_not_added_without_update(self):
        p = self.project(check=["make check"])
        p.run_apply()
        self.assertEqual(self.check_list(p), ["make check"])

    def test_check_reports_the_difference_and_writes_nothing(self):
        p = self.project(check=["make check"])
        before = p.read(".claude/gw.json")
        code, out = p.run_apply("--update", "--check")
        self.assertEqual(code, 1, out)
        self.assertEqual(len(self.merge_lines(out)), 1, out)
        self.assertIn("ci-local.py --validate", out)
        self.assertEqual(p.read(".claude/gw.json"), before)

    def test_dry_run_summary_warns_counts_and_writes_nothing(self):
        p = self.project(check=["make check"])
        before = p.read(".claude/gw.json")
        code, out = p.run_apply("--update", "--dry-run", "--summary")
        self.assertEqual(code, 0, out)
        lines = self.merge_lines(out)
        self.assertEqual(len(lines), 1, out)
        self.assertIn("check lacks `ci-local.py --validate`", lines[0])
        self.assertRegex(out, r"\d+ merge")
        self.assertEqual(p.read(".claude/gw.json"), before)

    def test_joins_the_other_gw_json_changes_in_one_write(self):
        p = self.project(check=["make check"])
        p.write(".claude/gw.json", json.dumps(dict(BASE_CONFIG, check=["make check"], version="0.0.1"), indent=2) + "\n")
        code, out = p.run_apply("--update", "--dry-run")
        lines = self.merge_lines(out)
        self.assertEqual(len(lines), 1, out)
        self.assertIn("version 0.0.1", lines[0])
        self.assertIn("ci-local.py --validate", lines[0])

    def test_odd_shapes_fail_closed_and_are_never_rewritten(self):
        # `check` is a required array of non-empty strings: config.py rejects the odd shapes (exit 2) before the guard
        # runs, so nothing is written. A gw.json without `check` is the same case (no default is invented here).
        for odd in ({"check": "make check"}, {"check": [1, None]}, {"check": []}, {"check": None}):
            p = self.project(**odd)
            before = p.read(".claude/gw.json")
            code, out = p.run_apply("--update")
            self.assertEqual(code, 2, (odd, out))
            self.assertEqual(p.read(".claude/gw.json"), before, odd)
        p = self.project()
        raw = json.loads(p.read(".claude/gw.json"))
        del raw["check"]
        p.write(".claude/gw.json", json.dumps(raw) + "\n")
        before = p.read(".claude/gw.json")
        code, out = p.run_apply("--update")
        self.assertEqual(code, 2, out)
        self.assertEqual(p.read(".claude/gw.json"), before)


class PendingFileMigration(unittest.TestCase):
    """D129: --update writes `pendingFile` when the log points to the pending file; D130: the AGENTS.md proposal is
    rendered with the already migrated gw.json."""

    POINTER = "\nPending items live in the `pendingFile` file (`.claude/gw.json`).\n"
    DEFAULT = "docs/records/pending.md"

    def project(self, pointer=True, **config):
        tmp = Path(tempfile.mkdtemp(prefix="gw-pf-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        p = Fixture(tmp, dict(config, version=VERSION))
        if pointer:
            p.write("docs/log.md", p.read("docs/log.md") + self.POINTER)
        return p

    def test_no_pointer_in_the_log_needs_no_migration(self):
        p = self.project(pointer=False)
        before = p.read(".claude/gw.json")
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertEqual(p.read(".claude/gw.json"), before)
        self.assertNotIn("pendingFile", out)

    def test_without_update_nothing_is_written(self):
        p = self.project()
        before = p.read(".claude/gw.json")
        p.run_apply()
        self.assertEqual(p.read(".claude/gw.json"), before)

    def test_key_already_set_is_never_overwritten(self):
        for value in ("notes/todo.md", ""):
            p = self.project(pendingFile=value)
            code, out = p.run_apply("--update")
            self.assertEqual(code, 0, out)
            self.assertEqual(json.loads(p.read(".claude/gw.json"))["pendingFile"], value)
            self.assertNotIn("pendingFile set to", out)

    def test_unwritable_gw_json_warns_with_the_key_and_the_command(self):
        p = self.project()
        before = p.read(".claude/gw.json")
        with unittest.mock.patch.object(os, "access", return_value=False):
            module = load_apply()
            plan = module.Plan(p.work, VERSION, True)
            plan.cfg = {"log": "docs/log.md"}
            module.plan_pending_file(plan)
        self.assertEqual(plan.actions, [])
        self.assertEqual(len(plan.warnings), 1)
        self.assertIn('"pendingFile": "docs/records/pending.md"', plan.warnings[0])
        self.assertIn("cannot be read or written", plan.warnings[0])
        self.assertIn("handoff.py", plan.warnings[0])
        self.assertEqual(p.read(".claude/gw.json"), before)

    def test_unreadable_gw_json_warns_instead_of_writing(self):
        p = self.project()
        p.write(".claude/gw.json", "{not json")
        module = load_apply()
        plan = module.Plan(p.work, VERSION, True)
        plan.cfg = {"log": "docs/log.md"}
        module.plan_pending_file(plan)
        self.assertEqual(plan.actions, [])
        self.assertIn("pendingFile", plan.warnings[0])
        self.assertEqual(p.read(".claude/gw.json"), "{not json")

    def test_key_is_written_with_the_templates_value_and_once(self):
        p = self.project()
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertEqual(json.loads(p.read(".claude/gw.json"))["pendingFile"], self.DEFAULT)
        self.assertIn("pendingFile set to", out)
        code, out = p.run_apply("--update")
        self.assertNotIn("pendingFile set to", out)

    def test_it_shares_the_single_gw_json_write_with_the_schema_migration(self):
        p = self.project()
        raw = json.loads(p.read(".claude/gw.json"))
        del raw["schemaVersion"]
        p.write(".claude/gw.json", json.dumps(raw) + "\n")
        code, out = p.run_apply("--update", "--dry-run")
        lines = [l for l in out.splitlines() if l.lstrip().startswith("merge") and ".claude/gw.json" in l]
        self.assertEqual(len(lines), 1, out)
        self.assertIn("schemaVersion 0", lines[0])
        self.assertIn("pendingFile set to", lines[0])

    def test_agents_proposal_lists_the_migrated_check(self):  # D130
        cmd = "python3 .claude/gw/scripts/ci-local.py --validate"
        p = self.project(pointer=False, ciYamlCheck=True, check=["make old-check"])
        p.write("AGENTS.md", "# Project rules, no marker\n")
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        proposal = p.read("AGENTS.md.gw-new")
        self.assertIn(cmd, proposal)
        self.assertIn("make old-check", proposal)
        self.assertIn(cmd, p.read(".claude/gw.json"))

    def test_agents_proposal_keeps_the_current_check_without_a_migration(self):  # D130
        p = self.project(pointer=False, check=["make old-check"])  # ciYamlCheck false: no merge of the check list
        p.write("AGENTS.md", "# Project rules, no marker\n")
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        proposal = p.read("AGENTS.md.gw-new")
        self.assertIn("make old-check", proposal)
        self.assertNotIn("ci-local.py --validate", proposal)

    def test_a_mention_of_pendingfile_in_the_log_is_not_the_pointer(self):  # review: only the pointer line counts
        p = self.project(pointer=False)
        p.write("docs/log.md", p.read("docs/log.md") + "\n- Done: talked about `pendingFile` here\n")
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertNotIn("pendingFile", json.loads(p.read(".claude/gw.json")))
        self.assertNotIn("pendingFile set to", out)

    def test_old_log_path_still_to_move_is_read_where_it_is(self):  # review: plan_paths moves the log in the same run
        p = self.project(pointer=False, log="docs/traspaso.md")
        p.write("docs/traspaso.md", "# Log\n" + self.POINTER)
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertIn("from docs/traspaso.md", out)
        self.assertEqual(json.loads(p.read(".claude/gw.json"))["pendingFile"], self.DEFAULT)


class StaleRefsMigration(unittest.TestCase):
    """D83: --update adds the names the migration renames to the project's `staleRefs` (both forms, no duplicates)."""

    def project(self, **config):
        tmp = Path(tempfile.mkdtemp(prefix="gw-stale-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        p = Fixture(tmp)
        p.write(".claude/gw.json", json.dumps(dict(MIGRATED_CONFIG, **config), indent=2) + "\n")  # no `log`
        p.write("docs/traspaso.md", "# Log\n")
        return p

    def refs(self, p):
        return json.loads(p.read(".claude/gw.json")).get("staleRefs")

    def test_list_form_keeps_user_entries_and_gets_the_old_names_once(self):
        p = self.project(staleRefs=["phase 9"])
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        refs = self.refs(p)["patterns"]  # the form becomes {patterns, skip} (history skipped, see below)
        self.assertEqual(refs[0], "phase 9")
        self.assertIn(r"(?<![\w.-])docs/traspaso\.md(?![\w-])", refs)
        self.assertIn("staleRefs gets the renamed names", out)
        self.assertEqual(len(refs), len(set(refs)))
        n = len(refs)
        p.run_apply("--update")  # the paths moved: nothing renamed any more, nothing added
        self.assertEqual(len(self.refs(p)["patterns"]), n)

    def test_object_form_keeps_skip_and_is_not_duplicated(self):
        entry = r"(?<![\w.-])docs/traspaso\.md(?![\w-])"
        p = self.project(staleRefs={"patterns": ["x", entry], "skip": ["docs/old/"]})
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        refs = self.refs(p)
        self.assertEqual(refs["skip"], ["docs/old/"])
        self.assertEqual(refs["patterns"].count(entry), 1)
        self.assertEqual(refs["patterns"][:2], ["x", entry])

    def test_history_folders_go_to_skip_so_old_records_stay_green(self):
        p = self.project(staleRefs=["phase 9"])
        p.write("docs/registros/old.md", "see docs/traspaso.md\n")
        p.write("docs/notes.md", "fine\n")
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        refs = self.refs(p)
        self.assertIsInstance(refs, dict)
        self.assertEqual(refs["patterns"][0], "phase 9")
        self.assertIn("docs/records/", refs["skip"])
        self.assertIn("docs/proposals/", refs["skip"])
        self.assertIn("CHANGELOG*", refs["skip"])
        p.run("git", "add", "-A")
        code, out = p.run("python3", str(p.work / ".claude/gw/scripts/md-links.py"))
        self.assertEqual(code, 0, out)  # the moved record quotes the old path: skipped, not red
        p.write("docs/notes.md", "see docs/traspaso.md\n")
        p.run("git", "add", "-A")
        code, out = p.run("python3", str(p.work / ".claude/gw/scripts/md-links.py"))
        self.assertNotEqual(code, 0, out)
        self.assertIn("stale reference", out)

    def test_absent_key_becomes_a_list_and_without_update_nothing_is_added(self):
        p = self.project()
        code, out = p.run_apply("--dry-run")
        self.assertEqual(code, 0, out)
        self.assertNotIn("staleRefs gets", out)
        code, out = p.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertIn(r"(?<![\w.-])docs/traspaso\.md(?![\w-])", self.refs(p)["patterns"])


class GitignoreBlock(unittest.TestCase):
    """D127: --init writes a marked per-stack block in .gitignore without touching the rest; a rerun replaces it."""

    PREFIX = "# galivelop-workflow:gitignore begin"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-gi-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Fixture(self.tmp)

    def init(self, *args):
        """--init as a new project does it: gw.json absent (an existing one makes --init a no-op)."""
        (self.p.work / ".claude/gw.json").unlink(missing_ok=True)
        return self.p.run_apply("--init", "--check-command", "true", *args)

    def block(self, text):
        lines = text.splitlines()
        a = next(i for i, l in enumerate(lines) if l.startswith(self.PREFIX))
        return lines, a, lines.index("# galivelop-workflow:gitignore end")

    def test_block_is_appended_for_the_detected_stacks_and_the_rest_is_kept(self):
        p = self.p
        p.write("package.json", "{}\n")
        p.write("setup.cfg", "\n")
        p.write(".gitignore", "mine/\n")
        code, out = self.init()
        self.assertEqual(code, 0, out)
        lines, a, b = self.block(p.read(".gitignore"))
        self.assertEqual(lines[0], "mine/")
        self.assertIn("node_modules/", lines[a:b])
        self.assertIn("__pycache__/", lines[a:b])
        self.assertIn("/dist/", lines[a:b])
        self.assertNotIn("vendor/", lines)
        self.assertNotIn("target/", lines)
        self.assertIn(".claude/gw.local.json", lines[b:])
        # each fragment's own version marker (version.py) stays in the template, not in the user's file
        self.assertFalse([x for x in lines if x.startswith("# galivelop-workflow v")], lines)

    def test_rerun_replaces_only_the_block_even_if_its_begin_text_changed(self):
        p = self.p
        p.write("Cargo.toml", "\n")
        self.assertEqual(self.init()[0], 0)
        _, a, b = self.block(p.read(".gitignore"))
        lines = p.read(".gitignore").splitlines()
        lines[a:b] = [self.PREFIX + " (older wording)", "stale"]
        p.write(".gitignore", "\n".join(["top/"] + lines + ["bottom/"]) + "\n")
        code, out = self.init()
        self.assertEqual(code, 0, out)
        again = p.read(".gitignore").splitlines()
        self.assertEqual((again[0], again[-1]), ("top/", "bottom/"))
        self.assertNotIn("stale", again)
        self.assertIn("target/", again)
        self.assertEqual(len([l for l in again if l.startswith(self.PREFIX)]), 1)
        before = p.read(".gitignore")
        self.assertEqual(self.init()[0], 0)
        self.assertEqual(p.read(".gitignore"), before)

    def test_existing_gw_json_makes_init_ignore_the_gitignore_too(self):
        p = self.p
        p.write("package.json", "{}\n")
        code, out = p.run_apply("--init")
        self.assertEqual(code, 0, out)
        self.assertIn("flags are ignored", out)
        self.assertNotIn("gitignore begin", p.read(".gitignore"))

    def test_init_writes_the_project_skill_prefix_and_rejects_the_workflow_one(self):
        # E73: --project-skill-prefix goes to projectSkillPrefix; gw- is the workflow's and fails the schema
        code, out = self.init("--project-skill-prefix", "gvg-")
        self.assertEqual(code, 0, out)
        self.assertEqual(json.loads(self.p.read(".claude/gw.json"))["projectSkillPrefix"], "gvg-")
        code, out = self.init("--project-skill-prefix", "gw-")
        self.assertNotEqual(code, 0, out)
        self.assertIn("projectSkillPrefix", out)

    def test_without_init_or_stack_there_is_no_block(self):
        p = self.p
        p.write("package.json", "{}\n")
        p.run_apply()
        self.assertNotIn("gitignore begin", p.read(".gitignore"))

    def test_init_without_stack_writes_only_the_common_block(self):
        # E28 (C4): secrets are ignored whatever the stack; with none detected the block holds only the common fragment
        p = self.p
        self.assertEqual(self.init()[0], 0)
        lines, a, b = self.block(p.read(".gitignore"))
        self.assertEqual(lines[a + 1:b], ["# common", ".env", ".env.*", "!.env.example", "!.env.sample",
                                          "!.env.template", ".claude/settings.local.json", "*.gw-tmp"])

    def test_gitignore_common_is_a_boolean_key_true_by_default(self):
        # E28 (C4): configurable, like every behaviour; a non-boolean fails closed with the fix
        p = self.p
        new = json.loads((ROOT / "templates" / "gw.json").read_text())
        self.assertIs(new["gitignoreCommon"], True)
        code, out = p.run("python3", "-c", "import sys; sys.path.insert(0, sys.argv[1]); import config; "
                          "print(config.gitignore_common({}), config.gitignore_common({'gitignoreCommon': False}))",
                          str(ROOT / "scripts"))
        self.assertEqual(out.strip(), "True False", out)
        code, out = p.run("python3", "-c", "import sys; sys.path.insert(0, sys.argv[1]); import config; "
                          "config.gitignore_common({'gitignoreCommon': 'no'})", str(ROOT / "scripts"))
        self.assertNotEqual(code, 0)
        self.assertIn("gitignoreCommon must be true or false", out)
        import types
        mod = load_apply()
        p.write("go.mod", "module x\n")
        for on, expected in ((True, True), (False, False)):
            plan = types.SimpleNamespace(root=p.work, cfg={"gitignoreCommon": on}, actions=[])
            mod.plan_gitignore(plan, init=True)
            text = plan.actions[0][2].decode()
            self.assertEqual("\n.env\n" in text, expected, text)
            self.assertIn("# go", text)
    def test_init_refused_by_a_link_leaves_no_gw_json_so_the_rerun_inits(self):
        # E28: gw.json is removed again when the run fails, so --init (and the common block) runs on the rerun
        p = self.p
        outside = self.tmp / "outside"
        outside.mkdir()
        (p.work / ".githooks").symlink_to(outside, target_is_directory=True)
        code, out = self.init()
        self.assertEqual(code, 2, out)
        self.assertIn(".githooks is a symbolic link", out)
        self.assertIn("--init --check-command true", out)  # the fix repeats the original arguments
        self.assertFalse((p.work / ".claude/gw.json").exists(), out)
        self.assertEqual(list(outside.iterdir()), [])
        (p.work / ".githooks").unlink()
        code, out = p.run_apply("--init", "--check-command", "true")
        self.assertEqual(code, 0, out)
        self.assertNotIn("already exists", out)
        self.assertIn("\n.env\n", p.read(".gitignore"))

    def test_common_block_ignores_secrets_and_keeps_the_samples_for_every_stack(self):
        # E28 (C4): .env, .env.* and .claude/settings.local.json ignored; .env.example-style samples still committed
        p = self.p
        p.write("go.mod", "module x\n")
        code, out = self.init()
        self.assertEqual(code, 0, out)
        lines, a, b = self.block(p.read(".gitignore"))
        self.assertEqual(lines[a + 1], "# common")
        self.assertLess(lines.index("# common"), lines.index("# go"))
        for rel in (".env", ".env.local", ".env.production", ".claude/settings.local.json", "sub/.env"):
            self.assertEqual(p.run("git", "check-ignore", "-q", rel)[0], 0, rel)
        for rel in (".env.example", ".env.sample", ".env.template", ".claude/settings.json"):
            self.assertEqual(p.run("git", "check-ignore", "-q", rel)[0], 1, rel)

    def test_the_workflow_repo_ignores_secrets_and_local_settings(self):
        # E28 (C4): this repo's own .gitignore
        def ignored(rel):
            return subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", "--no-index", rel]).returncode == 0
        for rel in (".env", ".env.local", ".claude/settings.local.json"):
            self.assertTrue(ignored(rel), rel)
        self.assertFalse(ignored(".env.example"))

    def test_stack_flag_overrides_detection(self):
        p = self.p
        p.write("package.json", "{}\n")
        code, out = self.init("--stack", "go")
        self.assertEqual(code, 0, out)
        self.assertIn("*.test", p.read(".gitignore"))
        self.assertNotIn("node_modules/", p.read(".gitignore"))
        self.assertEqual(json.loads(p.read(".claude/gw.json"))["gitignoreStacks"], ["go"])

    def test_unterminated_block_and_non_utf8_fail_closed_with_the_reason(self):
        p = self.p
        p.write("package.json", "{}\n")
        p.write(".gitignore", self.PREFIX + "\nx\n")
        code, out = self.init()
        self.assertEqual(code, 2, out)
        self.assertIn("but not its end line", out)
        self.assertEqual(p.read(".gitignore"), self.PREFIX + "\nx\n")
        raw = "A\xf1o/\n".encode("latin-1")
        (p.work / ".gitignore").write_bytes(raw)
        code, out = self.init()
        self.assertEqual(code, 2, out)
        self.assertIn("is not UTF-8", out)
        self.assertEqual((p.work / ".gitignore").read_bytes(), raw)

    def test_bad_gitignore_stacks_values_are_refused_with_the_fix(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import config as gwconfig
        self.assertEqual(gwconfig.gitignore_stacks({}), [])
        self.assertEqual(gwconfig.gitignore_stacks({"gitignoreStacks": ["go", "node"]}), ["go", "node"])
        for bad in ("python", ["python", "python"], ["cobol"], [1]):
            with self.assertRaises(gwconfig.ConfigError) as cm:
                gwconfig.gitignore_stacks({"gitignoreStacks": bad})
            self.assertIn("gitignoreStacks must be a list of different stacks", str(cm.exception))
            self.assertIn("validate", str(cm.exception))


class SymlinkTargets(unittest.TestCase):
    """B1 (E28): apply.py never writes, chmods or deletes through a symbolic link a cloned repo tracks."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-link-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self.outside = self.tmp / "home"
        self.outside.mkdir()
        self.apply = load_apply()

    def plan(self, *actions):
        import types
        return types.SimpleNamespace(root=self.root, actions=list(actions), set_hooks_path=False)

    def refused(self, plan, link):
        with self.assertRaises(self.apply.ApplyError) as cm:
            self.apply.apply(plan)
        msg = str(cm.exception)
        self.assertIn(f"{link} is a symbolic link", msg)
        self.assertIn(f"rm {link}", msg)

    def test_a_symlinked_file_is_refused_and_its_target_untouched(self):
        bashrc = self.outside / ".bashrc"
        bashrc.write_text("mine\n")
        os.chmod(bashrc, 0o644)
        (self.root / ".githooks").mkdir()
        link = self.root / ".githooks" / "pre-commit"
        link.symlink_to(bashrc)
        self.refused(self.plan(("update", Path(".githooks/pre-commit"), b"evil\n", True, "")), link)
        self.assertEqual(bashrc.read_text(), "mine\n")
        self.assertEqual(stat.S_IMODE(bashrc.stat().st_mode), 0o644)  # nor made executable
        self.assertTrue(link.is_symlink())
        new = self.root / ".githooks" / "pre-commit.gw-new"
        new.symlink_to(bashrc)
        self.refused(self.plan(("propose", Path(".githooks/pre-commit.gw-new"), b"x\n", False, "")), new)
        self.refused(self.plan(("chmod", Path(".githooks/pre-commit"), None, True, "")), link)
        self.assertEqual(bashrc.read_text(), "mine\n")
        self.assertEqual(stat.S_IMODE(bashrc.stat().st_mode), 0o644)

    def test_a_symlinked_parent_folder_is_refused_and_nothing_is_written(self):
        (self.root / ".claude").mkdir()
        link = self.root / ".claude" / "gw"
        link.symlink_to(self.outside, target_is_directory=True)
        plan = self.plan(("create", Path("AGENTS.md"), b"a\n", False, ""),
                         ("create", Path(".claude/gw/scripts/x.py"), b"evil\n", False, ""))
        self.refused(plan, link)
        self.assertEqual(list(self.outside.iterdir()), [])
        self.assertFalse((self.root / "AGENTS.md").exists())  # one link refuses the whole plan, before any write

    def test_a_legacy_removal_through_a_symlink_is_refused_and_the_target_kept(self):
        (self.outside / "scripts").mkdir()
        old = self.outside / "scripts" / "bitacora.py"
        old.write_text("keep\n")
        (self.root / ".claude").mkdir()
        link = self.root / ".claude" / "gw"
        link.symlink_to(self.outside, target_is_directory=True)
        self.refused(self.plan(("remove", Path(".claude/gw/scripts/bitacora.py"), None, False, "")), link)
        self.assertEqual(old.read_text(), "keep\n")
        (self.root / ".claude" / "skills").mkdir()
        skill = self.root / ".claude" / "skills" / "gw-viejo"
        skill.symlink_to(self.outside, target_is_directory=True)
        self.refused(self.plan(("remove", Path(".claude/skills/gw-viejo"), None, False, "")), skill)
        self.assertEqual(old.read_text(), "keep\n")

    def test_a_folder_whose_real_path_is_outside_the_root_is_refused(self):
        self.apply_root = self.tmp / "repo-link"
        self.apply_root.symlink_to(self.root, target_is_directory=True)  # the root itself may be a link (macOS /tmp)
        plan = self.plan(("create", Path("docs/a.md"), b"a\n", False, ""))
        plan.root = self.apply_root
        self.apply.apply(plan)
        self.assertEqual((self.root / "docs/a.md").read_bytes(), b"a\n")
        with self.assertRaises(self.apply.ApplyError) as cm:
            self.apply.safe_target(self.root, Path("../home/x"))
        self.assertIn("is not a path inside", str(cm.exception))

    def test_a_write_replaces_the_file_keeps_its_mode_and_leaves_no_temporary(self):
        dest = self.root / "x.sh"
        dest.write_text("old\n")
        os.chmod(dest, 0o750)
        self.apply.apply(self.plan(("update", Path("x.sh"), b"new\n", False, "")))
        self.assertEqual(dest.read_bytes(), b"new\n")
        self.assertEqual(stat.S_IMODE(dest.stat().st_mode), 0o750)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["x.sh"])

    def test_a_failed_write_leaves_no_temporary(self):
        with unittest.mock.patch.object(self.apply.os, "replace", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.apply.write_file(self.root, Path("x.sh"), b"new\n")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_a_symlink_is_never_moved_and_nothing_is_written(self):
        (self.root / ".github").mkdir()
        target = self.outside / "ci.yml"
        target.write_text("theirs\n")
        old = self.root / ".github" / "comprobar.yml"
        old.symlink_to(target)
        plan = self.plan(("move", Path(".github/check.yml"), Path(".github/comprobar.yml"), False, ""),
                         ("update", Path(".github/check.yml"), b"ci\n", False, ""))
        self.refused(plan, old)
        self.assertTrue(old.is_symlink())
        self.assertFalse(os.path.lexists(self.root / ".github" / "check.yml"))
        self.assertEqual(target.read_text(), "theirs\n")

    def test_a_link_inside_a_moved_folder_refuses_the_plan_before_the_move(self):
        (self.root / "old" / "sub").mkdir(parents=True)
        link = self.root / "old" / "sub" / "x"
        link.symlink_to(self.outside / "x")
        plan = self.plan(("move", Path("new"), Path("old"), False, ""),
                         ("create", Path("new/sub/x"), b"evil\n", False, ""))
        self.refused(plan, link)
        self.assertTrue((self.root / "old").is_dir())
        self.assertFalse(os.path.lexists(self.root / "new"))
        self.assertEqual(list(self.outside.iterdir()), [])

    def test_a_parent_whose_real_path_leaves_the_root_is_refused_even_if_the_link_check_misses_it(self):
        # the per-part check can miss a link that appears after it (a race): the real-path check still refuses
        (self.root / "docs").symlink_to(self.outside, target_is_directory=True)
        with unittest.mock.patch.object(self.apply.Path, "is_symlink", return_value=False):
            with self.assertRaises(self.apply.ApplyError) as cm:
                self.apply.safe_target(self.root, Path("docs/a.md"))
        msg = str(cm.exception)
        self.assertIn(f"is really {self.outside}, outside {self.root}", msg)
        self.assertIn("make it a plain folder of the project", msg)
        self.assertEqual(list(self.outside.iterdir()), [])

    def test_update_of_a_cloned_repo_with_a_symlinked_hook_fails_closed(self):
        (self.tmp / "fx").mkdir()
        fx = Fixture(self.tmp / "fx")
        code, out = fx.run_apply()
        self.assertEqual(code, 0, out)
        hooks = fx.work / ".githooks"
        shutil.rmtree(hooks)
        hooks.symlink_to(self.outside, target_is_directory=True)  # e.g. ~/bin, ~/.ssh
        code, out = fx.run_apply("--dry-run")  # the dry run refuses what the real run refuses
        self.assertEqual(code, 2, out)
        self.assertIn(f"{hooks} is a symbolic link", out)
        code, out = fx.run_apply("--update")
        self.assertEqual(code, 2, out)
        self.assertIn(f"{hooks} is a symbolic link", out)
        self.assertIn(f"{fx.work} --update", out)  # the fix repeats the original arguments
        self.assertEqual(list(self.outside.iterdir()), [])

    def test_a_linked_old_script_is_not_planned_for_removal(self):
        (self.tmp / "fx").mkdir()
        fx = Fixture(self.tmp / "fx")
        code, out = fx.run_apply()
        self.assertEqual(code, 0, out)
        old = self.outside / "bitacora.py"
        old.write_text("# galivelop-workflow v0.1.0\n")
        link = fx.work / ".claude/gw/scripts/bitacora.py"
        link.symlink_to(old)
        fx.run("git", "add", "-A")
        self.assertEqual(fx.run("git", "commit", "-qm", "cloned")[0], 0)  # tracked and clean: removable if a file
        code, out = fx.run_apply("--update")
        self.assertEqual(code, 0, out)
        self.assertTrue(link.is_symlink())
        self.assertEqual(old.read_text(), "# galivelop-workflow v0.1.0\n")


class TemplateAtFallback(unittest.TestCase):
    """A12 (Q-15): template_at falls back to templates/en only for a language with no folder in the tag."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.flow = self.tmp / "flow"
        for rel, text in (("templates/es/a.md", "es a\n"), ("templates/en/a.md", "en a\n"),
                          ("templates/en/b.md", "en b\n")):
            path = self.flow / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@e", GIT_COMMITTER_NAME="t",
                   GIT_COMMITTER_EMAIL="t@e")
        for args in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "x"], ["tag", "v0.1.0"]):
            subprocess.run(["git", "-C", str(self.flow), *args], check=True, env=env, capture_output=True)
        self.apply = load_apply()
        self.apply.WORKFLOW = self.flow

    def plan(self, primary):
        plan = self.apply.Plan(self.tmp / "proj", "0.2.0", True)
        plan.cfg = {"languages": {"docs": {"primary": primary}}}
        return plan

    def test_a_language_with_a_folder_never_takes_an_english_file(self):
        self.assertEqual(self.plan("es").template_at("a.md", "0.1.0"), b"es a")
        self.assertIsNone(self.plan("es").template_at("b.md", "0.1.0"))  # templates/es existed: no per-file fallback

    def test_a_language_without_a_folder_uses_the_english_one(self):
        self.assertEqual(self.plan("gl").template_at("b.md", "0.1.0"), b"en b")

    def test_the_english_fallback_warns_once_per_run_and_names_the_language(self):
        plan = self.plan("gl")
        plan.template_at("a.md", "0.1.0")
        plan.template_at("b.md", "0.1.0")
        self.assertEqual(plan.warnings, ["languages.docs.primary is 'gl' but the workflow has no templates/gl/ folder, "
                                         "so the English templates (en) are used"])
        self.plan("es").template_at("a.md", "0.1.0")  # a language with a folder says nothing


if __name__ == "__main__":
    unittest.main()
