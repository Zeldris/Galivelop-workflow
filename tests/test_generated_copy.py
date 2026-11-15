"""PreToolUse hook: scripts/generated-copy.py (E56), run the way Claude Code runs a hook: the event JSON on stdin, the
answer on stdout with exit 0. A warning is `additionalContext` naming the source; "no opinion" is no output at all.
The hook's root is its own repo, so the events point at paths of this repo (nothing is written).
"""
import json
import subprocess
import sys
import unittest

from test_hooks import ROOT
from waits import timeout

SCRIPT = ROOT / "scripts" / "generated-copy.py"


def run(event, cwd=ROOT):
    data = event if isinstance(event, str) else json.dumps(event)
    return subprocess.run([sys.executable, str(SCRIPT)], input=data, cwd=str(cwd), capture_output=True, text=True,
                          timeout=timeout(30))


def edit(path, tool="Edit", key="file_path", cwd=ROOT):
    return run({"hook_event_name": "PreToolUse", "cwd": str(cwd), "tool_name": tool, "tool_input": {key: str(path)}})


class Warns(unittest.TestCase):
    def note(self, r):
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertNotIn("permissionDecision", out)  # advice, never a block
        return out["additionalContext"]

    def test_each_copy_names_its_source(self):
        cases = {
            ".claude/gw/scripts/config.py": "scripts/config.py",
            ".claude/gw/schema/gw.schema.json": "schema/gw.schema.json",
            ".claude/skills/gw-update/SKILL.md": "skills/gw-update/SKILL.md",
            ".claude/skills/LICENSE-mattpocock-skills": "LICENSE-mattpocock-skills",
            ".githooks/pre-push": "templates/githooks/pre-push",
            ".claude/agents/gw-worker.md": "templates/claude/agents/gw-worker.md",
            ".claude/agents/gw-reviewer.md": "templates/claude/agents/gw-reviewer.md",
        }
        for copy, source in cases.items():
            with self.subTest(copy=copy):
                text = self.note(edit(copy))
                self.assertIn(f"{copy} is a copy", text)
                self.assertIn(f"Edit {source} instead", text)
                self.assertIn("python3 scripts/apply.py", text)

    def test_absolute_path_and_every_edit_tool(self):
        for tool, key in (("Write", "file_path"), ("MultiEdit", "file_path"), ("NotebookEdit", "notebook_path")):
            with self.subTest(tool=tool):
                text = self.note(edit(ROOT / ".claude/gw/scripts/doctor.py", tool=tool, key=key))
                self.assertIn("Edit scripts/doctor.py instead", text)

    def test_relative_path_against_the_event_cwd(self):
        text = self.note(edit("../gw/scripts/config.py", cwd=ROOT / ".claude" / "skills"))
        self.assertIn(".claude/gw/scripts/config.py is a copy", text)

    def test_new_file_in_a_copy_folder_names_where_to_create_it(self):
        text = self.note(edit(".claude/gw/scripts/brand-new.py", tool="Write"))
        self.assertIn("Create it as scripts/brand-new.py instead", text)


class Silent(unittest.TestCase):
    def quiet(self, r):
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_sources_and_owned_files(self):
        for path in ("scripts/config.py", "skills/gw-update/SKILL.md", "templates/githooks/pre-push",
                     ".claude/gw/gw-opt-tokens.md", ".claude/gw.json", ".claude/settings.json", "README.md",
                     ".claude/skills", ".claude/gw/scripts-old/x.py"):
            with self.subTest(path=path):
                self.quiet(edit(path))

    def test_outside_the_repo(self):
        self.quiet(edit(ROOT.parent / "elsewhere" / ".claude" / "gw" / "scripts" / "config.py"))

    def test_other_tools_and_bad_events(self):
        self.quiet(edit(".claude/gw/scripts/config.py", tool="Read"))
        self.quiet(edit(".claude/gw/scripts/config.py", tool="Bash", key="command"))
        for raw in ("", "not json", "[1]", json.dumps({"tool_name": "Edit", "tool_input": "x"}),
                    json.dumps({"tool_name": "Edit", "tool_input": {"file_path": 3}})):
            with self.subTest(raw=raw):
                self.quiet(run(raw))


class Wiring(unittest.TestCase):
    def test_workflow_only_and_registered_only_here(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import importlib
        apply = importlib.import_module("apply")
        self.assertIn("generated-copy.py", apply.WORKFLOW_ONLY_SCRIPTS)
        self.assertFalse((ROOT / ".claude/gw/scripts/generated-copy.py").exists())
        here = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
        commands = [h["command"] for e in here["hooks"]["PreToolUse"] for h in e["hooks"]]
        # `|| true`: a checkout without the script (an older commit) must not block every edit (exit 2)
        self.assertIn('python3 "$CLAUDE_PROJECT_DIR"/scripts/generated-copy.py || true', commands)
        template = (ROOT / "templates/claude/settings.json").read_text(encoding="utf-8")
        self.assertNotIn("generated-copy.py", template)


if __name__ == "__main__":
    unittest.main()
