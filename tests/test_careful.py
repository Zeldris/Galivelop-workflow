"""PreToolUse hook: scripts/careful.py (C8, `modes.careful`), in a temporary project laid out like one that applied the
workflow; the event JSON on stdin, `ask` on stdout with exit 0, "allowed" is no output. Every case that expects an `ask`
checks the reason (what the command does), not only the exit code."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from test_hooks import ROOT, Project

ASKS = [  # (command, text the reason must carry)
    ("rm -rf build", "rm -r"), ("rm -fr build", "rm -r"), ("rm -r build", "rm -r"), ("rm -Rf build", "rm -r"),
    ("rm --recursive --force build", "rm -r"), ("rm -rf -- build", "rm -r"), ("rm -rf /tmp", "rm -r"),
    ("rm -rf /tmp/../etc", "rm -r"), ("rm -rf /tmp/a build", "rm -r"), ("sudo rm -rf build", "rm -r"),
    ("cd x && rm -rf build", "rm -r"), ("ls | xargs rm -rf", "rm -r"), ("bash -c 'rm -rf build'", "rm -r"),
    ("eval \"rm -rf build\"", "rm -r"), ("rm -rf /tmp/$(pwd)", "rm -r"), ("rm -rf /tmp/*", "rm -r"), ("rm -rf /tmpfoo/x", "rm -r"),
    ("git push --force", "remote history"), ("git push -f origin main", "remote history"),
    ("git push --force-with-lease origin x", "remote history"), ("git push origin +main", "remote history"),
    ("git push -fu origin x", "remote history"), ("git -C . push --force", "remote history"),
    ("git push --delete origin old", "deletes a remote"), ("git push -d origin old", "deletes a remote"),
    ("git push origin :old", "deletes a remote"),
    ("git reset --hard", "uncommitted"), ("git reset --hard origin/main", "uncommitted"),
    ("git branch -D old", "not merged"), ("git branch -d -f old", "not merged"), ("git branch --delete --force old", "not merged"),
    ("git clean -fd", "untracked"), ("git clean -f", "untracked"), ("git clean --force -x", "untracked"),
    ("git checkout -- .", "every modified file"), ("git checkout .", "every modified file"),
    ("git restore .", "every modified file"), ("git restore --worktree .", "every modified file"),
    ("git restore --source=HEAD -- .", "every modified file"),
]
ALLOWED = [
    "ls -la", "rm file.txt", "rm -f file.txt", "rm -rf /tmp/scratch/x", "rm -r /var/tmp/a /tmp/b", "rm -rf $TMPDIR/x",
    "rm -rf ${TMPDIR}/x",
    "git commit -m \"avoid rm -rf and git push --force\"", "git commit -m 'git reset --hard'",
    "echo 'git push --force'", "echo \"rm -rf /\"",
    "cat <<'EOF' > notes.md\nrm -rf build\ngit reset --hard\nEOF", "cat <<EOF\ngit push -f\nEOF\nls",
    "git commit -F - <<'EOF'\nfeat: x\n\nrm -rf y\nEOF",
    "git push", "git push origin main", "git push -u origin feature", "git push --dry-run", "git reset --soft HEAD~1",
    "git reset HEAD file", "git branch -d merged", "git branch -a", "git clean -n", "git clean -nd", "git clean --dry-run -f",
    "git checkout main", "git checkout -b new", "git checkout -- file.txt", "git restore file.txt",
    "git restore --staged .", "git status", "git push origin feature:feature", "bash scripts/push.sh branch",
    "grep -r foo .", "python3 -c 'print(1)'", "",
]


class CarefulProject(Project):
    def __init__(self, tmp, config=None):
        super().__init__(tmp, config=config, hooks=())
        self.scripts = self.work / ".claude" / "gw" / "scripts"
        for name in ("careful.py", "config-guard.py"):
            shutil.copy2(ROOT / "scripts" / name, self.scripts / name)

    def hook(self, event=None, stdin=None):
        text = json.dumps({"hook_event_name": "PreToolUse", "cwd": str(self.work), **(event or {})}) \
            if stdin is None else stdin
        return self.run("python3", str(self.scripts / "careful.py"), stdin=text or None)

    def bash(self, command):
        return self.hook({"tool_name": "Bash", "tool_input": {"command": command}})


class CarefulTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-careful-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = CarefulProject(self.tmp)

    def reason(self, result):
        code, out = result
        self.assertEqual(code, 0, out)
        data = json.loads(out)
        self.assertEqual(list(data), ["hookSpecificOutput"], out)
        spec = data["hookSpecificOutput"]
        self.assertEqual((spec["hookEventName"], spec["permissionDecision"]), ("PreToolUse", "ask"), out)
        return spec["permissionDecisionReason"]

    def assertAsks(self, result, *needles):
        text = self.reason(result)
        for n in needles:
            self.assertIn(n, text)

    def assertAllowed(self, result):
        code, out = result
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip(), "", "an allowed call gets no output")

    def test_destructive_commands_ask_with_their_reason(self):
        for command, needle in ASKS:
            with self.subTest(command=command):
                self.assertAsks(self.p.bash(command), "destructive command", needle, "modes.careful")

    def test_reason_names_the_command(self):
        self.assertAsks(self.p.bash("echo hi; git reset --hard HEAD~3"), "git reset --hard HEAD~3")

    def test_false_positives_pass_without_asking(self):
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assertAllowed(self.p.bash(command))

    def test_command_after_a_heredoc_is_still_seen(self):
        self.assertAsks(self.p.bash("cat <<'EOF'\nhello\nEOF\ngit push --force"), "remote history")

    def test_other_tools_are_ignored(self):
        self.assertAllowed(self.p.hook({"tool_name": "Edit", "tool_input": {"file_path": "x", "command": "rm -rf /"}}))

    def test_mode_off_does_nothing(self):
        self.p.write(".claude/gw.json", json.dumps(dict(json.loads((self.p.work / ".claude/gw.json").read_text()),
                                                         modes={"careful": False})))
        self.assertAllowed(self.p.bash("rm -rf build"))
        self.assertAllowed(self.p.hook(stdin="not json"))

    def test_mode_on_explicitly(self):
        self.p.write(".claude/gw.json", json.dumps(dict(json.loads((self.p.work / ".claude/gw.json").read_text()),
                                                         modes={"careful": True})))
        self.assertAsks(self.p.bash("git reset --hard"), "uncommitted")

    def test_exempt_prefixes_are_configurable(self):
        cfg = json.loads((self.p.work / ".claude/gw.json").read_text())
        self.p.write(".claude/gw.json", json.dumps(dict(cfg, modes={"carefulExempt": ["/scratch/", "build/"]})))
        self.assertAllowed(self.p.bash("rm -rf /scratch/x build/out"))
        self.assertAsks(self.p.bash("rm -rf /tmp/x"), "rm -r")  # the list replaces the default one
        self.assertAsks(self.p.bash("git push --force"), "remote history")  # git is never exempt

    def test_broken_config_keeps_the_mode_on(self):
        self.p.write(".claude/gw.json", "{ not json")
        self.assertAsks(self.p.bash("rm -rf build"), "rm -r")
        self.assertAllowed(self.p.bash("ls"))

    def test_unusable_event_asks(self):
        self.assertAsks(self.p.hook(stdin="not json"), "could not use the hook event", "stdin is not valid JSON")
        self.assertAsks(self.p.hook({"tool_name": "Bash", "tool_input": {}}), "no command string")

    def test_git_alias_is_looked_through(self):
        self.p.git("config", "alias.nuke", "reset --hard")
        self.assertAsks(self.p.bash("git nuke"), "uncommitted")

    def test_template_and_plugin_register_it(self):
        for rel in ("templates/claude/settings.json", "hooks/hooks.json"):
            data = json.loads((ROOT / rel).read_text())
            found = [g for g in data["hooks"]["PreToolUse"]
                     if any("careful.py" in h["command"] for h in g["hooks"])]
            self.assertEqual([g["matcher"] for g in found], ["Bash"], rel)


if __name__ == "__main__":
    unittest.main()
