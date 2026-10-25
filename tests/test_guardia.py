"""PreToolUse hook: scripts/guardia-config.py (P2 of docs/propuestas/2026-10-25-repos-x.md), in a temporary project laid
out like one that applied the workflow, run the way Claude Code runs a hook: the event JSON on stdin, the answer on
stdout with exit 0. `ask` is the documented PreToolUse JSON; "allowed" is no output at all.

Every case that expects an `ask` checks the reason (the file it names and the workflow rule), not only the exit code.
"""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from test_ganchos import ROOT, Project

SCRIPT = "guardia-config.py"

PROTECTED = [".claude/settings.json", ".claude/gw.json", ".githooks/pre-push", ".githooks/new-hook",
             ".claude/gw/scripts/config.py", ".claude/gw/scripts/sub/new.py"]


class GuardProject(Project):
    def __init__(self, tmp):
        super().__init__(tmp, hooks=())
        self.scripts = self.work / ".claude" / "gw" / "scripts"
        shutil.copy2(ROOT / "scripts" / SCRIPT, self.scripts / SCRIPT)
        self.write(".claude/settings.json", "{}\n")
        (self.work / "src").mkdir()

    def guard(self, event=None, stdin=None, cwd=None):
        """(exit code, output) of the hook; `event` is the hook's JSON object."""
        text = json.dumps({"hook_event_name": "PreToolUse", "cwd": str(self.work), **(event or {})}) \
            if stdin is None else stdin
        return self.run("python3", str(self.scripts / SCRIPT), stdin=text or None, cwd=cwd)

    def tool(self, name, **tool_input):
        return self.guard({"tool_name": name, "tool_input": tool_input})


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-guardia-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = GuardProject(self.tmp)

    def answer(self, out):
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            self.fail(f"stdout is not JSON: {out!r}")
        self.assertEqual(list(data), ["hookSpecificOutput"], out)
        return data["hookSpecificOutput"]

    def assertAsks(self, result, *needles):
        code, out = result
        self.assertEqual(code, 0, out)
        spec = self.answer(out)
        self.assertEqual(spec["hookEventName"], "PreToolUse", out)
        self.assertEqual(spec["permissionDecision"], "ask", out)
        for needle in needles:
            self.assertIn(needle, spec["permissionDecisionReason"], out)
        return spec["permissionDecisionReason"]

    def assertAllowed(self, result):
        code, out = result
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip(), "", "an allowed call gets no output")


class EditTools(Base):
    def test_every_protected_path_asks_naming_the_file_and_the_rule(self):
        for rel in PROTECTED:
            for tool in ("Edit", "Write", "MultiEdit"):
                with self.subTest(tool=tool, path=rel):
                    reason = self.assertAsks(self.p.tool(tool, file_path=str(self.p.work / rel)),
                                             rel, "only with the user's OK", "scripts/aplicar.py")
                    self.assertIn(tool, reason)

    def test_notebook_edit_uses_notebook_path(self):
        self.assertAsks(self.p.tool("NotebookEdit", notebook_path=str(self.p.work / ".githooks" / "x.ipynb")),
                        ".githooks/x.ipynb", "only with the user's OK")

    def test_relative_paths_are_resolved_against_the_event_cwd(self):
        p = self.p
        self.assertAsks(p.tool("Edit", file_path=".claude/settings.json"), ".claude/settings.json")
        self.assertAsks(p.tool("Edit", file_path="./.claude/gw.json"), ".claude/gw.json")
        self.assertAsks(p.tool("Edit", file_path="src/../.githooks/pre-push"), ".githooks/pre-push")
        self.assertAsks(p.tool("Edit", file_path=str(p.work / "src" / ".." / ".claude" / "gw.json")), ".claude/gw.json")
        result = p.guard({"tool_name": "Write", "tool_input": {"file_path": "../.claude/gw.json"},
                          "cwd": str(p.work / "src")})
        self.assertAsks(result, ".claude/gw.json")

    def test_it_works_from_any_process_directory(self):
        self.assertAsks(self.p.guard({"tool_name": "Edit", "tool_input": {"file_path": ".claude/gw.json"}},
                                     cwd=self.tmp), ".claude/gw.json")

    def test_a_symlink_to_a_protected_file_asks(self):
        link = self.p.work / "src" / "link.sh"
        link.symlink_to(self.p.work / ".githooks" / "pre-push")
        self.assertAsks(self.p.tool("Edit", file_path=str(link)), ".githooks/pre-push")

    def test_case_variants_ask(self):
        self.assertAsks(self.p.tool("Edit", file_path=".Claude/Settings.JSON"), "Settings.JSON")

    def test_unrelated_files_are_allowed(self):
        for rel in ("src/a.py", ".claude/settings.local.json", ".claude/skills/x/SKILL.md", "docs/.githooks-notes.md",
                    ".claude/gw/schema/gw.schema.json", ".githooks-old/x", "settings.json", "gw.json",
                    "src/.claude/settings.json"):
            with self.subTest(path=rel):
                self.assertAllowed(self.p.tool("Edit", file_path=str(self.p.work / rel)))

    def test_a_file_outside_the_project_is_allowed(self):
        other = self.tmp / "other" / ".claude"
        other.mkdir(parents=True)
        self.assertAllowed(self.p.tool("Write", file_path=str(other / "settings.json")))

    def test_edit_without_a_target_asks(self):
        for tool_input in ({}, {"file_path": ""}, {"file_path": 3}, {"old_string": "a"}):
            with self.subTest(tool_input=tool_input):
                self.assertAsks(self.p.tool("Edit", **tool_input), "no file_path", "cannot tell which file")


class BashWrites(Base):
    WRITES = [
        'echo x > .claude/settings.json',
        'echo x >> .claude/settings.json',
        'echo x >.claude/gw.json',
        'echo x >| .githooks/pre-push',
        'cat <<EOF > .githooks/pre-push\nhi\nEOF',
        'echo x 2> .claude/gw.json',
        'echo x &> .claude/gw.json',
        'echo x | tee .claude/gw/scripts/config.py',
        'echo x | tee -a "$CLAUDE_PROJECT_DIR"/.claude/settings.json',
        'sed -i s/a/b/ .claude/settings.json',
        "sed -i'' -e s/a/b/ .githooks/pre-push",
        "sed -ni 's/a/b/p' .claude/gw.json",
        'sed --in-place s/a/b/ .claude/gw.json',
        'perl -pi -e s/a/b/ .claude/gw/scripts/config.py',
        'cp /tmp/x .claude/settings.json',
        'cp /tmp/x ./.githooks/pre-push',
        'mv /tmp/x .claude/gw/scripts/config.py',
        'rm .githooks/pre-push',
        'rm -rf .githooks',
        'rm -rf .claude',
        'install -m 755 /tmp/x .githooks/pre-push',
        'ln -sf /tmp/x .githooks/pre-push',
        'chmod +x .githooks/pre-push',
        'truncate -s 0 .claude/gw.json',
        'touch .githooks/new',
        'git checkout -- .claude/settings.json',
        'git checkout main -- .githooks',
        'git restore .claude/gw.json',
        'git -C . restore --staged --worktree .githooks/pre-push',
        'git rm .githooks/pre-push',
        'find .githooks -type f -delete',
        'echo ok && cp /tmp/x .claude/settings.json',
        'cd src; echo x > ../.claude/settings.json',
        'sudo cp /tmp/x .githooks/pre-push',
        'FOO=1 cp /tmp/x .githooks/pre-push',
        'bash -c "echo x > .claude/gw.json"',
        "sh -c 'cp /tmp/x .githooks/pre-push'",
        'eval "rm .githooks/pre-push"',
        'echo x > "$CLAUDE_PROJECT_DIR/.claude/settings.json"',
        'echo x > ${CLAUDE_PROJECT_DIR}/.claude/settings.json',
        'cp /tmp/x .claude/gw/scripts/../../settings.json',
        'cd .claude && echo x > settings.json',
        'cd .githooks; rm pre-push',
        'cp /tmp/x .githooks/*',
    ]
    READS = [
        'cat .claude/settings.json',
        'grep -n hooks .claude/settings.json .githooks/pre-push',
        'python3 .claude/gw/scripts/config.py validate',
        'python3 .claude/gw/scripts/doctor.py > /tmp/out.txt',
        'bash .githooks/pre-push',
        'cat .claude/settings.json > /tmp/copy.json',
        'ls -la .githooks .claude/gw/scripts',
        'git diff -- .claude/settings.json',
        'git log --oneline -- .githooks',
        'git show HEAD:.claude/gw.json',
        'git add .githooks/pre-push',
        'diff .githooks/pre-push /tmp/x',
        'sed -n 1,5p .githooks/pre-push',
        'sed -n s/i/j/p .claude/gw.json',
        'head -3 .claude/gw/scripts/config.py | grep import',
        'python3 scripts/aplicar.py . --check',
        'bash tests/comprobar.sh',
        'echo hi > src/out.txt',
        'rm -rf src/build',
        'cp /tmp/x src/a.py',
        'echo ".claude/settings.json is protected" > src/notes.txt',
        'echo "rm .githooks/pre-push"',
        'cat .claude/settings.local.json',
        'echo x > /tmp/other/.claude/settings.json',
        'ls',
    ]

    def assertEachAsks(self, commands, named=None):
        for command in commands:
            with self.subTest(command=command):
                reason = self.assertAsks(self.p.tool("Bash", command=command), "this command writes to",
                                         "only with the user's OK")
                if named:
                    self.assertIn(f"writes to {named}:", reason)

    def assertEachAllowed(self, commands):
        for command in commands:
            with self.subTest(command=command):
                self.assertAllowed(self.p.tool("Bash", command=command))

    def test_a_writer_whose_destination_is_an_ancestor_folder_asks(self):
        self.assertEachAsks([
            'cp templates/claude/settings.json .claude/',
            'cp -r templates/claude/. .claude',
            'cp -r /tmp/x ./.claude/gw/',
            'install -m 644 /tmp/x .claude/',
            'rsync -a /tmp/x/ .claude/gw',
            'ln -sf /tmp/x .claude/',
            'cp -t .claude /tmp/x',
            'cp --target-directory=.claude /tmp/x',
            'cp /tmp/x "$CLAUDE_PROJECT_DIR/.claude"',
            'sudo cp /tmp/x .claude/',
            'cd src; cp /tmp/x ../.claude/',
            'cd .claude && cp /tmp/x .',
        ])

    def test_an_ancestor_folder_as_the_source_of_a_copy_is_allowed(self):
        self.assertEachAllowed([
            'cp -r .claude /tmp/backup',
            'cp -r .claude/ /tmp/backup/',
            'rsync -a .claude/gw /tmp/backup',
            'cp /tmp/a.txt .',
            'cp -r /tmp/x/. src',
            'cp -r .claude .claude-backup',
        ])

    def test_a_whole_tree_git_restore_asks(self):
        self.assertEachAsks([
            'git checkout -- .',
            'git checkout .',
            'git restore .',
            'git restore --source=HEAD~1 --worktree .',
            'git checkout main -- .',
            'git checkout -- .claude',
            'git restore .claude/',
            'git -C . checkout -- .',
            'cd .claude && git checkout -- .',
        ])

    def test_git_commands_that_do_not_cover_a_protected_file_are_allowed(self):
        self.assertEachAllowed([
            'git checkout main',
            'git checkout -b feature',
            'git switch feature',
            'git restore src/a.py',
            'git checkout -- src',
            'git -C . restore src/a.py',
            'git -C . status',
            'cd src && git checkout -- .',
            'git status',
            'git add .',
            'git diff .',
            'git log -- .',
        ])

    def test_option_values_of_wrappers_are_skipped(self):
        self.assertEachAsks([
            'sudo -u me rm .claude/gw.json',
            'sudo -Eu me rm .githooks/pre-push',
            'sudo --user me rm .githooks/pre-push',
            'sudo -u me nice -n 5 rm .claude/gw.json',
            'env -u VAR rm .claude/gw.json',
            'env -i FOO=1 rm .githooks/pre-push',
            'nice -n 5 tee .claude/gw.json',
            'nice -5 tee .claude/gw.json',
            'time -p rm .githooks/pre-push',
            'timeout 5 rm .githooks/pre-push',
            'timeout -s KILL 5 rm .githooks/pre-push',
            'stdbuf -o0 tee .claude/gw.json',
            'doas -u me rm .githooks/pre-push',
            'xargs -I{} cp {} .githooks/pre-push',
            'xargs -I {} cp {} .githooks/pre-push',
            'xargs -n 1 -P 4 cp /tmp/x .githooks/pre-push',
            'echo x | xargs -0 rm .githooks/pre-push',
            'sudo -u me bash -c "rm .githooks/pre-push"',
        ])

    def test_reads_behind_wrappers_with_option_values_are_allowed(self):
        self.assertEachAllowed([
            'sudo -u me cat .claude/gw.json',
            'env -u VAR cat .claude/settings.json',
            'nice -n 5 grep x .githooks/pre-push',
            'timeout 5 cat .claude/gw.json',
            'xargs -I{} echo {} .githooks/pre-push',
            'sudo -u me cp /tmp/x src/a.py',
        ])

    def test_a_redirection_before_the_command_asks(self):
        self.assertEachAsks(['> .claude/gw.json echo x', '>> .githooks/pre-push echo x', '2>/dev/null > .claude/gw.json'])

    def test_a_redirection_to_another_file_before_the_command_is_allowed(self):
        self.assertEachAllowed(['> /tmp/out cat .claude/gw.json', '2>&1 cat .claude/gw.json'])

    def test_writes_ask_naming_the_file(self):
        for command in self.WRITES:
            with self.subTest(command=command):
                reason = self.assertAsks(self.p.tool("Bash", command=command), "this command writes to",
                                         "only with the user's OK", "scripts/aplicar.py")
                self.assertRegex(reason, r"\.claude|\.githooks")

    def test_the_reason_names_the_file_written(self):
        self.assertAsks(self.p.tool("Bash", command="echo x > .claude/gw.json"), "writes to .claude/gw.json:")
        self.assertAsks(self.p.tool("Bash", command="cp a .githooks/pre-push"), "writes to .githooks/pre-push:")

    def test_reads_are_allowed(self):
        for command in self.READS:
            with self.subTest(command=command):
                self.assertAllowed(self.p.tool("Bash", command=command))

    def test_cp_from_a_protected_file_asks_too(self):  # cp counts as a write whenever it names a protected path
        self.assertAsks(self.p.tool("Bash", command="cp .claude/settings.json /tmp/copy.json"),
                        ".claude/settings.json")

    def test_relative_paths_use_the_event_cwd(self):
        p = self.p
        result = p.guard({"tool_name": "Bash", "tool_input": {"command": "echo x > ../.githooks/pre-push"},
                          "cwd": str(p.work / "src")})
        self.assertAsks(result, ".githooks/pre-push")
        result = p.guard({"tool_name": "Bash", "tool_input": {"command": "echo x > .githooks/pre-push"},
                          "cwd": str(p.work / "src")})
        self.assertAllowed(result)  # src/.githooks/pre-push is not the project's

    def test_an_unclosed_quote_is_still_looked_at(self):
        self.assertAsks(self.p.tool("Bash", command="echo 'x > .claude/gw.json"), ".claude/gw.json")


class FailClosed(Base):
    def test_unusable_stdin_asks_with_that_reason(self):
        cases = {"": "nothing arrived on stdin", "not json": "not valid JSON", "[1, 2]": "not a JSON object",
                 '"text"': "not a JSON object"}
        for text, why in cases.items():
            with self.subTest(stdin=text):
                code, out = self.p.run("python3", str(self.p.scripts / SCRIPT), stdin=text or None)
                self.assertAsks((code, out), "could not use the hook event", "cannot tell whether")
                if text:
                    self.assertIn(why, out)

    def test_an_event_without_the_tool_asks(self):
        self.assertAsks(self.p.guard({"tool_input": {"command": "ls"}}), "no tool_name")

    def test_an_event_without_tool_input_asks(self):
        self.assertAsks(self.p.guard({"tool_name": "Edit"}), "no tool_input", "cannot tell what it touches")
        self.assertAsks(self.p.guard({"tool_name": "Bash", "tool_input": "ls"}), "no tool_input")

    def test_bash_without_a_command_string_asks(self):
        for tool_input in ({}, {"command": None}, {"command": ["ls"]}):
            with self.subTest(tool_input=tool_input):
                self.assertAsks(self.p.tool("Bash", **tool_input), "no command string")

    def test_no_project_root_asks(self):
        lone = self.tmp / "lone"
        lone.mkdir()
        shutil.copy2(ROOT / "scripts" / SCRIPT, lone / SCRIPT)
        shutil.copy2(ROOT / "scripts" / "config.py", lone / "config.py")
        code, out = self.p.run("python3", str(lone / SCRIPT), cwd=lone,
                               stdin=json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}),
                               env={"GIT_CEILING_DIRECTORIES": str(self.tmp), "CLAUDE_PROJECT_DIR": ""})
        self.assertAsks((code, out), "cannot find the project root", "cannot tell whether")

    def test_other_tools_are_not_its_business(self):
        self.assertAllowed(self.p.tool("Read", file_path=str(self.p.work / ".claude" / "settings.json")))


if __name__ == "__main__":
    unittest.main()
