"""PreToolUse hook: scripts/other-repo-read.py (E74), in a temporary project laid out like one that applied the workflow,
run the way Claude Code runs a hook: the event JSON on stdin, the answer on stdout with exit 0. A warning is
`additionalContext` and names the path and the other repository's root; "no opinion" is no output at all.
"""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT, Project

SCRIPT = "other-repo-read.py"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-other-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = Project(self.tmp, hooks=())
        self.scripts = self.p.work / ".claude" / "gw" / "scripts"
        shutil.copy2(ROOT / "scripts" / SCRIPT, self.scripts / SCRIPT)
        self.other = self.tmp / "other"  # another repository: a `.git` folder
        (self.other / ".git").mkdir(parents=True)
        (self.other / "src").mkdir()
        (self.other / "src" / "a.txt").write_text("a\n")
        self.worktree = self.tmp / "wt"  # a linked worktree or submodule: `.git` is a file
        self.worktree.mkdir()
        (self.worktree / ".git").write_text("gitdir: elsewhere\n")
        (self.worktree / "b.txt").write_text("b\n")
        self.loose = self.tmp / "loose"  # inside no repository
        self.loose.mkdir()
        (self.loose / "c.txt").write_text("c\n")

    def event(self, tool, tool_input, cwd=None, **extra):
        return dict({"hook_event_name": "PreToolUse", "cwd": str(cwd or self.p.work), "tool_name": tool,
                     "tool_input": tool_input}, **extra)

    def run_hook(self, event):
        text = event if isinstance(event, str) else json.dumps(event)
        code, out = self.p.run("python3", str(self.scripts / SCRIPT), stdin=text)
        self.assertEqual(code, 0, out)
        return out

    def warns(self, out, path, repo):
        data = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(data["hookEventName"], "PreToolUse")
        self.assertNotIn("permissionDecision", data)
        text = data["additionalContext"]
        self.assertIn(str(path), text)
        self.assertIn(str(repo), text)
        self.assertIn("subagent", text)
        self.assertIn("otherRepoReadWarn", text)
        return text

    def silent(self, out):
        self.assertEqual(out, "")


class Warns(Base):
    def test_read(self):
        path = self.other / "src" / "a.txt"
        self.warns(self.run_hook(self.event("Read", {"file_path": str(path)})), path, self.other)

    def test_read_relative_to_cwd(self):
        out = self.run_hook(self.event("Read", {"file_path": "a.txt"}, cwd=self.other / "src"))
        self.warns(out, self.other / "src" / "a.txt", self.other)

    def test_grep_and_glob(self):
        for tool in ("Grep", "Glob"):
            out = self.run_hook(self.event(tool, {"pattern": "a", "path": str(self.other)}))
            self.warns(out, self.other, self.other)

    def test_bash_word(self):
        path = self.other / "src" / "a.txt"
        self.warns(self.run_hook(self.event("Bash", {"command": f"cat {path} | head"})), path, self.other)

    def test_bash_git_c_and_cd(self):
        self.warns(self.run_hook(self.event("Bash", {"command": f"git -C {self.other} log"})), self.other, self.other)
        self.warns(self.run_hook(self.event("Bash", {"command": f"cd {self.other} && ls"})), self.other, self.other)

    def test_worktree_file_counts_as_a_repo(self):
        path = self.worktree / "b.txt"
        self.warns(self.run_hook(self.event("Read", {"file_path": str(path)})), path, self.worktree)

    def test_one_warning_with_all_paths(self):
        a, b = self.other / "src" / "a.txt", self.worktree / "b.txt"
        out = self.run_hook(self.event("Bash", {"command": f"cat {a} {b}"}))
        text = self.warns(out, a, self.other)
        self.assertIn(str(b), text)
        self.assertIn(str(self.worktree), text)
        self.assertEqual(out.count("additionalContext"), 1)


class Silent(Base):
    def test_inside_the_project(self):
        self.p.write("docs/x.md", "x\n")
        self.silent(self.run_hook(self.event("Read", {"file_path": str(self.p.work / "docs" / "x.md")})))
        self.silent(self.run_hook(self.event("Bash", {"command": "cat docs/x.md; git -C . log"})))

    def test_outside_every_repo(self):
        self.silent(self.run_hook(self.event("Read", {"file_path": str(self.loose / "c.txt")})))
        self.silent(self.run_hook(self.event("Bash", {"command": f"cat {self.loose / 'c.txt'}"})))

    def test_nonexistent_bash_word(self):
        self.silent(self.run_hook(self.event("Bash", {"command": f"echo {self.other}/nope/missing.txt"})))

    def test_from_a_subagent(self):
        out = self.run_hook(self.event("Read", {"file_path": str(self.other / "src" / "a.txt")}, agent_id="abc123"))
        self.silent(out)

    def test_switched_off(self):
        (self.p.work / ".claude" / "gw.json").write_text(json.dumps(dict(BASE_CONFIG, otherRepoReadWarn=False)))
        self.silent(self.run_hook(self.event("Read", {"file_path": str(self.other / "src" / "a.txt")})))

    def test_unreadable_config_still_warns_by_default(self):
        (self.p.work / ".claude" / "gw.json").write_text("{not json")
        out = self.run_hook(self.event("Read", {"file_path": str(self.other / "src" / "a.txt")}))
        self.warns(out, self.other / "src" / "a.txt", self.other)

    def test_broken_input(self):
        for text in (" ", "not json", "[]", json.dumps({"tool_name": "Read"}),
                     json.dumps({"tool_name": "Read", "tool_input": "x"}),
                     json.dumps(self.event("Bash", {"command": "cat 'unclosed " + str(self.other)})),
                     json.dumps(self.event("Edit", {"file_path": str(self.other / "src" / "a.txt")})),
                     json.dumps(self.event("Read", {"file_path": 5}))):
            self.silent(self.run_hook(text))


if __name__ == "__main__":
    unittest.main()
