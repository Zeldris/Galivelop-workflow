"""PreToolUse hook: scripts/config-guard.py (P2 of docs/proposals/2026-10-25-repos-x.md), in a temporary project laid
out like one that applied the workflow, run the way Claude Code runs a hook: the event JSON on stdin, the answer on
stdout with exit 0. `ask` is the documented PreToolUse JSON; "allowed" is no output at all.

Every case that expects an `ask` checks the reason (the file it names and the workflow rule), not only the exit code.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from test_hooks import ROOT, Project

SCRIPT = "config-guard.py"

PROTECTED = [".claude/settings.json", ".claude/settings.local.json", ".claude/gw.json",
             ".claude/worktrees/agent-x/.claude/settings.json", ".claude/worktrees/agent-x/.githooks/pre-push",
             ".claude/worktrees/agent-x/.claude/gw/scripts/config.py", ".claude/worktrees/agent-x/.claude/gw.json", ".githooks/pre-push", ".githooks/new-hook",
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
                                             rel, "only with the user's OK", "scripts/apply.py")
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
        for rel in ("src/a.py", ".claude/other.json", ".claude/skills/x/SKILL.md", "docs/.githooks-notes.md",
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
        'python3 scripts/apply.py . --check',
        'bash tests/check.sh',
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

    def test_the_value_of_a_copier_option_is_not_the_destination(self):
        self.assertEachAllowed([
            'rsync -a ./ /tmp/x/ --exclude .claude',
            'rsync -a ./ /tmp/x/ --exclude .claude/gw',
            'rsync -a --exclude .claude ./ /tmp/x/',
            'rsync -a --exclude=.claude ./ /tmp/x/',
            'rsync -a --include .claude --exclude "*" ./ /tmp/x/',
            "rsync -a --filter '- .claude' ./ /tmp/x/",
            'rsync -a ./ /tmp/x/ --exclude-from .claude',
            'rsync -a ./ /tmp/x/ --include-from .claude/gw',
            'rsync -ae .claude ./ /tmp/x/',
            'rsync -a -e .claude ./ /tmp/x/',
            'cp -S .claude a src/',
            'cp --suffix .claude a src/',
            'install -m 644 -o root -g root /tmp/x src/a',
            'install -S .claude /tmp/x src/a',
        ])

    def test_a_copier_option_value_does_not_hide_the_real_destination(self):
        self.assertEachAsks(['rsync -a --exclude .git /tmp/x/ .claude/gw/', 'rsync -e ssh /tmp/x/ .claude/gw',
                             'rsync -a /tmp/x/ .claude/gw --exclude .git', 'rsync -ae ssh /tmp/x/ .claude/gw',
                             'install -m 644 -o me /tmp/x .claude/gw', 'cp -S .bak /tmp/x .claude/gw',
                             'cp -at .claude/gw /tmp/x'],
                            named=".claude/gw")

    def test_dd_asks_when_of_names_a_protected_file(self):
        self.assertEachAsks(['dd of=.claude/gw.json', 'dd if=/tmp/x of=.githooks/pre-push',
                             'dd if=/dev/zero of=./.claude/settings.json bs=1 count=1 conv=notrunc',
                             'dd of="$CLAUDE_PROJECT_DIR/.claude/gw.json" if=/tmp/x'])
        self.assertEachAsks(['dd if=/tmp/x of=.githooks/pre-push'], named=".githooks/pre-push")
        self.assertEachAsks(['dd of=.claude/gw.json'], named=".claude/gw.json")

    def test_dd_reading_a_protected_file_or_writing_elsewhere_is_allowed(self):
        self.assertEachAllowed(['dd if=.claude/gw.json of=/tmp/x', 'dd if=.githooks/pre-push', 'dd of=src/a.bin',
                                'dd if=.githooks/pre-push of=src/copy'])

    def test_git_restore_of_the_index_only_is_not_a_write(self):
        self.assertEachAllowed(['git restore --staged .', 'git restore -S .', 'git restore --staged .claude/gw.json',
                                'git restore -S .githooks/pre-push', 'git restore --staged -- .claude',
                                'git restore --source=HEAD --staged .', 'git -C . restore --staged .'])

    def test_git_restore_of_the_worktree_still_asks(self):
        self.assertEachAsks(['git restore --staged --worktree .githooks/pre-push', 'git restore -S -W .githooks/pre-push',
                             'git restore -SW .githooks/pre-push', 'git restore --worktree .githooks/pre-push',
                             'git restore --staged .githooks/pre-push && git restore .githooks/pre-push'],
                            named=".githooks/pre-push")
        self.assertEachAsks(['git restore --staged --worktree .', 'git restore -W .'], named=".")

    def test_git_rm_cached_is_not_a_write(self):
        self.assertEachAllowed(['git rm --cached -r .', 'git rm --cached .claude/gw.json', 'git rm -r --cached .claude',
                                'git rm --cached .githooks/pre-push'])
        self.assertEachAsks(['git rm -r .githooks', 'git rm -f .claude/gw.json'])

    def test_git_clean_dry_run_is_not_a_write(self):
        self.assertEachAllowed(['git clean -n', 'git clean --dry-run .githooks', 'git clean -n -- .claude',
                                'git clean -nd .claude', 'git clean -dn .githooks'])
        self.assertEachAsks(['git clean -f .githooks', 'git clean -fd .claude'])

    def test_reading_or_copying_from_a_protected_path_is_allowed(self):
        self.assertEachAllowed([
            'cp .claude/gw.json /tmp/', 'cp .githooks/pre-push /tmp', 'cp -r .githooks /tmp/backup',
            'cp .claude/settings.json src/a.json', 'install -m 755 .githooks/pre-push /tmp/hook',
            'rsync -a .githooks/ /tmp/x/', 'rsync -a .claude/gw/scripts/ /tmp/x/',
            'ln -s .claude/gw.json /tmp/link', 'ln .githooks/pre-push /tmp/hard', 'cp -t /tmp .claude/gw.json',
            'cp --target-directory=/tmp .githooks/pre-push', 'sudo cp .claude/gw.json /tmp/',
        ])

    def test_a_copier_still_asks_when_the_protected_path_is_the_destination(self):
        self.assertEachAsks(['cp .claude/gw.json .githooks/pre-push', 'install .githooks/pre-push .claude/gw.json',
                             'ln -sf .claude/gw.json .claude/settings.json'])

    def test_rsync_that_removes_its_sources_writes_them(self):
        self.assertEachAsks(['rsync -a --remove-source-files .githooks/ /tmp/x/'], named=".githooks")

    def test_mv_from_a_protected_path_is_a_write_of_it(self):
        self.assertEachAsks(['mv .claude/gw.json /tmp/', 'mv .githooks/pre-push /tmp/hook', 'mv -t /tmp .claude/gw.json'],
                            named=None)
        self.assertEachAsks(['mv .claude/gw.json /tmp/'], named=".claude/gw.json")

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

    def test_settings_local_and_the_same_paths_inside_an_agent_worktree_ask(self):
        self.assertEachAsks([
            'echo x > .claude/settings.local.json',
            'sed -i s/a/b/ .claude/settings.local.json',
            'echo x > .claude/worktrees/agent-x/.claude/settings.json',
            'cp /tmp/x .claude/worktrees/agent-x/.githooks/pre-push',
            'rm .claude/worktrees/agent-x/.claude/gw/scripts/config.py',
            'rm -rf .claude/worktrees/agent-x/.claude',
            'cd .claude/worktrees/agent-x && echo x > .claude/gw.json',
        ])
        self.assertEachAllowed(['echo x > .claude/worktrees/agent-x/src/a.py', 'cat .claude/worktrees/agent-x/.claude/gw.json',
                                'echo x > .claude/worktrees/notes.txt', 'git worktree list'])

    def test_find_exec_of_a_writer_on_a_protected_tree_asks(self):
        self.assertEachAsks(['find .githooks -type f -exec rm {} \\;', 'find .claude/gw/scripts -name "*.py" -exec rm -f {} +',
                             'find .githooks -execdir chmod -x {} \\;', 'find .githooks -exec sed -i s/a/b/ {} +'],
                            named=None)
        self.assertEachAllowed(['find .githooks -type f -exec cat {} \\;', 'find .githooks -exec grep -l x {} +',
                                'find src -exec rm {} \\;', 'find .githooks -name x'])

    def test_tar_and_unzip_extracting_into_a_protected_folder_ask(self):
        self.assertEachAsks(['tar -xf /tmp/a.tar -C .githooks', 'tar xzf /tmp/a.tgz -C .claude/gw/scripts',
                             'tar -C .claude -xf /tmp/a.tar', 'tar --extract --directory=.githooks -f /tmp/a.tar',
                             'tar -xf /tmp/a.tar -C.githooks', 'unzip /tmp/a.zip -d .githooks', 'unzip -o /tmp/a.zip -d .claude',
                             'cd .githooks && tar -xf /tmp/a.tar', 'cd .githooks && unzip /tmp/a.zip'])
        self.assertEachAllowed(['tar -xf /tmp/a.tar -C src', 'tar -cf /tmp/a.tar -C .githooks .', 'tar -tf /tmp/a.tar',
                                'tar -xf /tmp/a.tar', 'tar -czf /tmp/a.tgz .claude', 'unzip /tmp/a.zip -d src',
                                'unzip -l /tmp/a.zip', 'cd .githooks && unzip -l /tmp/a.zip', 'unzip /tmp/a.zip'])

    def test_find_starting_at_a_folder_that_holds_protected_files_asks(self):
        self.assertEachAsks(['find .claude -name gw.json -exec rm {} +', 'find . -name gw.json -delete',
                             'find .claude -delete', 'find . -name settings.local.json -exec rm -f {} \\;',
                             'find .claude/gw -exec rm -rf {} +', 'find .claude -type f -exec rm {} \\;'])
        self.assertEachAllowed(['find .claude -name gw.json', 'find . -name "*.py"', 'find src -delete',
                                'find .claude -exec cat {} +', 'find . -exec grep -l x {} \\;'])

    def test_only_the_project_dir_variable_stands_for_the_root(self):
        self.assertEachAsks(['echo x > $CLAUDE_PROJECT_DIR/.claude/gw.json', 'rm ${CLAUDE_PROJECT_DIR}/.githooks/pre-push'],
                            named=None)
        self.assertEachAsks(['echo x > $CLAUDE_PROJECT_DIR/.claude/gw.json'], named=".claude/gw.json")
        for command in ('echo x > $HOME/.claude/gw.json', 'rm $TMP/.githooks/pre-push', 'rm -rf ${ROOT}/.claude'):
            with self.subTest(command=command):
                reason = self.assertAsks(self.p.tool("Bash", command=command), "a path built from")
                self.assertIn("which may be the project", reason)
        self.assertEachAllowed(['echo x > $HOME/notes.txt', 'rm $TMP/build', 'cat $HOME/.claude/gw.json', 'echo $HOME'])


    def test_a_reference_file_is_read_not_written(self):
        self.assertEachAllowed(['touch -r .claude/gw.json src/a.py', 'touch --reference=.claude/gw.json src/a.py',
                                'touch --reference .githooks/pre-push src/a.py', 'touch -ar .githooks/pre-push src/a.py',
                                'chmod --reference=.githooks/pre-push src/a.sh', 'chmod --reference .githooks/pre-push src/a.sh',
                                'chown --reference=.claude/gw.json src/a.py', 'chown --reference .claude/gw.json src/a.py',
                                'chgrp --reference .claude/gw.json src/a.py'])
        self.assertEachAsks(['touch -r src/a.py .claude/gw.json', 'chmod --reference=src/a.py .githooks/pre-push',
                             'chmod --reference src/a.py .githooks/pre-push', 'touch -r .claude/gw.json .claude/gw.json',
                             'chown --reference=src/a.py .claude/gw.json'], named=None)

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

    def test_grouped_short_options_with_the_value_attached_do_not_swallow_the_command(self):
        # `-uroot` is `-u root` in one word: the next word is the command, not a value
        self.assertEachAsks(['sudo -uroot rm .githooks/pre-push', 'sudo -Euroot rm .githooks/pre-push',
                             'sudo -u root -ggrp rm .githooks/pre-push', 'doas -uroot rm .githooks/pre-push'],
                            named=".githooks/pre-push")
        self.assertEachAsks(['nice -n5 tee .claude/gw.json', 'env -uVAR rm .claude/gw.json',
                             'timeout -sKILL 5 rm .claude/gw.json', 'timeout -k5 -s KILL 9 rm .claude/gw.json',
                             'xargs -I{} rm .claude/gw.json', 'xargs -n1 -P4 rm .claude/gw.json'],
                            named=".claude/gw.json")

    def test_a_group_whose_last_letter_takes_a_value_still_consumes_the_next_word(self):
        self.assertEachAsks(['sudo -Eu root rm .githooks/pre-push', 'sudo -Ei -u root rm .githooks/pre-push'],
                            named=".githooks/pre-push")
        self.assertEachAllowed(['sudo -Eu root cat .githooks/pre-push'])

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
                                         "only with the user's OK", "scripts/apply.py")
                self.assertRegex(reason, r"\.claude|\.githooks")

    def test_the_reason_names_the_file_written(self):
        self.assertAsks(self.p.tool("Bash", command="echo x > .claude/gw.json"), "writes to .claude/gw.json:")
        self.assertAsks(self.p.tool("Bash", command="cp a .githooks/pre-push"), "writes to .githooks/pre-push:")

    def test_reads_are_allowed(self):
        for command in self.READS:
            with self.subTest(command=command):
                self.assertAllowed(self.p.tool("Bash", command=command))

    def test_cp_from_a_protected_file_is_a_read(self):  # only the destination of a copy is written
        self.assertAllowed(self.p.tool("Bash", command="cp .claude/settings.json /tmp/copy.json"))

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


class GitTreeWrites(Base):
    """`git` calls that rewrite the working tree ask only when they would change a protected path."""
    HOOK = ".githooks/pre-push"

    def setUp(self):
        super().setUp()
        p = self.p
        p.commit("guard files")  # the branches below must not carry the untracked guard away
        p.git("push", "-q", "--no-verify", "origin", "main")
        p.git("checkout", "-q", "-b", "hooks")
        p.write(self.HOOK, "#!/bin/sh\n")
        p.commit("hook")
        p.git("checkout", "-q", "main")
        p.git("checkout", "-q", "-b", "docs")
        p.write("docs/notes.md", "changed\n")
        p.commit("notes")
        p.git("checkout", "-q", "main")
        p.git("checkout", "-q", "-b", "wt")
        p.write(".claude/worktrees/agent-x/.claude/gw.json", "{}\n")
        p.commit("worktree copy")
        p.git("checkout", "-q", "main")
        p.git("branch", "-q", "--set-upstream-to=origin/main", "main")

    def asks(self, commands, named):
        for command in commands:
            with self.subTest(command=command):
                reason = self.assertAsks(self.p.tool("Bash", command=command), "this command writes to",
                                         "only with the user's OK")
                self.assertIn(f"writes to {named}:", reason)

    def allowed(self, commands):
        for command in commands:
            with self.subTest(command=command):
                self.assertAllowed(self.p.tool("Bash", command=command))

    def unknown(self, commands, why):
        for command in commands:
            with self.subTest(command=command):
                reason = self.assertAsks(self.p.tool("Bash", command=command), "writes to the working tree",
                                         "cannot tell which files it changes")
                self.assertIn(why, reason)

    def test_each_command_that_would_change_a_protected_file_asks_naming_it(self):
        self.asks(['git merge hooks', 'git merge docs hooks', 'git checkout hooks', 'git checkout -b new hooks',
                   'git switch hooks', 'git switch --detach hooks', 'git reset --hard hooks', 'git reset --keep hooks',
                   'git reset --merge hooks', 'git rebase hooks', 'git rebase --onto hooks main docs',
                   'git rebase main hooks', 'git cherry-pick hooks', 'git cherry-pick main..hooks',
                   'git cherry-pick docs hooks', 'git revert hooks', 'git revert --no-edit hooks',
                   'git -c x=y merge hooks', 'git -C . merge hooks', 'git -c x=y -C . merge hooks',
                   'echo a && git merge hooks', 'cd src && git merge hooks'], self.HOOK)

    def test_a_worktree_copy_of_a_protected_file_counts(self):
        self.asks(['git merge wt', 'git checkout wt', 'git cherry-pick wt'], ".claude/worktrees/agent-x/.claude/gw.json")

    def test_uncommitted_changes_to_a_protected_file_count(self):
        self.p.write(".claude/gw.json", self.p.work.joinpath(".claude/gw.json").read_text() + " ")
        self.asks(['git reset --hard', 'git checkout -f', 'git checkout main', 'git switch main', 'git switch -f main',
                   'git reset --hard HEAD'], ".claude/gw.json")
        self.allowed(['git reset --soft HEAD', 'git checkout -b feature'])

    def test_each_command_that_changes_no_protected_file_is_allowed(self):
        self.allowed(['git merge docs', 'git merge origin/main', 'git pull', 'git checkout docs', 'git checkout main',
                      'git switch docs', 'git switch -c feature', 'git switch main', 'git checkout -b feature docs',
                      'git reset --hard', 'git reset --hard docs', 'git reset --hard HEAD', 'git reset --soft hooks',
                      'git reset --mixed hooks', 'git reset', 'git rebase docs', 'git rebase main docs',
                      'git cherry-pick docs', 'git cherry-pick main..docs', 'git revert docs', 'git revert main..docs',
                      'git -c x=y merge docs', 'git -C . merge origin/main', 'git -C . checkout docs',
                      'git checkout docs -- docs', 'git stash list', 'git stash show', 'git stash',
                      'git merge-base main hooks', 'git fetch origin', 'git log hooks'])

    def stash(self, rel, text):
        self.p.git("checkout", "-q", "docs" if rel.startswith("docs") else "hooks")
        self.p.write(rel, text)
        self.p.git("stash", "-q")
        self.p.git("checkout", "-q", "main")

    def test_stash_pop_and_apply_ask_for_a_stash_that_holds_a_protected_file(self):
        self.stash(self.HOOK, "#!/bin/sh\necho changed\n")
        self.asks(['git stash pop', 'git stash apply', 'git stash apply stash@{0}', 'git stash pop 0',
                   'git stash apply --index'], self.HOOK)

    def test_stash_pop_and_apply_pass_for_a_stash_without_protected_files(self):
        self.stash("docs/notes.md", "stashed\n")
        self.allowed(['git stash pop', 'git stash apply', 'git stash apply stash@{0}', 'git stash apply 0'])
        self.unknown(['git stash pop stash@{7}', 'git stash apply 3'], "failed")

    def test_git_apply_reads_the_patch_for_its_files(self):
        tmp = self.tmp
        (tmp / "hook.patch").write_text(self.p.git("diff", "main", "hooks", "--").stdout)
        (tmp / "docs.patch").write_text(self.p.git("diff", "main", "docs", "--").stdout)
        self.asks([f'git apply {tmp}/hook.patch', f'git apply --index {tmp}/hook.patch',
                   f'git apply --3way {tmp}/hook.patch', f'git apply -p1 {tmp}/hook.patch'], self.HOOK)
        self.allowed([f'git apply {tmp}/docs.patch', f'git apply --check {tmp}/hook.patch',
                      f'git apply --stat {tmp}/hook.patch', f'git apply --cached {tmp}/docs.patch'])
        self.unknown(['git apply', 'git apply -', f'git apply {tmp}/missing.patch'], "git apply")

    def test_git_pull_looks_at_the_upstream(self):
        self.p.git("push", "-q", "origin", "hooks:main")
        self.p.git("fetch", "-q", "origin")
        self.asks(['git pull', 'git pull --rebase', 'git pull origin main', 'git pull --ff-only origin main'], self.HOOK)
        self.p.git("checkout", "-q", "docs")  # no upstream: it cannot tell
        self.unknown(['git pull'], "failed")

    def test_a_reference_that_does_not_exist_asks(self):
        self.unknown(['git merge nosuchref', 'git checkout nosuchref', 'git switch nosuchref',
                      'git reset --hard nosuchref', 'git rebase nosuchref', 'git cherry-pick nosuchref',
                      'git revert nosuchref', 'git cherry-pick main..nosuchref', 'git merge docs nosuchref'], "failed")

    def test_a_call_that_names_nothing_to_compute_from_asks(self):
        self.unknown(['git merge', 'git rebase --continue', 'git rebase --abort',
                      'git cherry-pick --continue', 'git revert --abort'], "names no commit")

    def test_another_repository_or_a_redirected_git_asks(self):
        other = self.tmp / "other"
        self.p.git("init", "-q", str(other), cwd=self.tmp)
        self.unknown([f'git -C {other} merge docs', f'git -C {other} checkout docs'], "another repository")
        self.unknown(['git -C /nonexistent-dir merge docs'], "could not run")
        self.unknown(['git -C "$SOMEWHERE" merge docs'], "path built at run time")
        self.unknown(['git --git-dir=/tmp/x merge docs', 'git --git-dir /tmp/x merge docs',
                      'git --work-tree=/tmp/x checkout docs', 'git --work-tree /tmp/x checkout docs'],
                     "points git somewhere else")
        self.unknown(['git -c core.worktree=/tmp/x merge docs', 'git -c core.worktree=/tmp/x -C . merge docs'],
                     "moves the working tree")
        self.unknown(['GIT_DIR=/tmp/x git merge docs', 'GIT_WORK_TREE=/tmp/x git checkout docs'],
                     "points git somewhere else")

    def test_git_env_set_anywhere_in_the_command_asks_for_a_tree_rewrite(self):
        self.unknown(['export GIT_DIR=/tmp/evil.git GIT_WORK_TREE=.; git checkout -f docs',
                      "sh -c 'export GIT_DIR=/tmp/evil.git; git merge docs'",
                      'GIT_INDEX_FILE=/tmp/i; git reset --hard docs', 'export GIT_CONFIG_COUNT=1; git merge docs',
                      'export GIT_COMMON_DIR=/tmp/c && git rebase docs'], "is set in this command")
        self.allowed(['export GIT_DIR=/tmp/evil.git; git status', 'export FOO=1; git merge docs'])

    def test_global_options_with_a_separate_value_do_not_hide_the_subcommand(self):
        self.asks(['git --namespace x merge hooks', 'git --exec-path=/usr/bin merge hooks',
                   'git --super-prefix x/ merge hooks', 'git -C . -c user.name=x merge hooks',
                   'git -c user.name=x -C . checkout hooks', 'git --no-pager -C . merge hooks'], self.HOOK)
        self.allowed(['git --namespace x merge docs', 'git -C . --no-pager status'])

    def test_an_alias_is_followed_one_level(self):
        self.asks(['git -c alias.m=merge m hooks', 'git -c alias.m="merge --no-ff" m hooks',
                   'git -c alias.co=checkout co hooks'], self.HOOK)
        self.allowed(['git -c alias.m=merge m docs'])
        self.unknown(['git -c alias.x="!rm -rf .claude" x', 'git -c alias.x="!true" x'], "runs a shell command")
        self.unknown(['git -c alias.a=b -c alias.b=merge a hooks', 'git -c alias.a=nosuchthing a hooks'],
                     "expands to another alias")

    def test_an_alias_in_the_git_config_is_followed(self):
        self.p.git("config", "alias.m", "merge")
        self.p.git("config", "alias.sh", "!rm -rf .claude")
        self.asks(['git m hooks'], self.HOOK)
        self.allowed(['git m docs'])
        self.unknown(['git sh'], "runs a shell command")
        self.allowed(['git no-such-external-command'])

    def test_a_builtin_name_is_never_an_alias(self):
        self.p.git("config", "alias.status", "!rm -rf .claude")
        self.allowed(['git status', 'git merge docs'])

    def test_git_apply_never_runs_git_on_the_users_options(self):
        tmp = self.tmp
        (tmp / "docs.patch").write_text(self.p.git("diff", "main", "docs", "--").stdout)
        target = tmp / "fake-ancestor"
        self.p.tool("Bash", command=f'git apply --build-fake-ancestor={target} {tmp}/docs.patch')
        self.assertFalse(target.exists())
        (tmp / "rename.patch").write_text(
            "diff --git a/docs/x.md b/.githooks/pre-push\nsimilarity index 100%\n"
            "rename from docs/x.md\nrename to .githooks/pre-push\n")
        self.asks([f'git apply {tmp}/rename.patch', f'git apply --build-fake-ancestor={target} {tmp}/rename.patch'],
                  self.HOOK)
        self.assertFalse(target.exists())
        (tmp / "new.patch").write_text("--- /dev/null\n+++ b/.githooks/new\n@@ -0,0 +1 @@\n+x\n")
        self.asks([f'git apply {tmp}/new.patch'], ".githooks/new")
        self.allowed([f'git apply --directory=docs {tmp}/docs.patch'])
        (tmp / "quoted.patch").write_text('diff --git "a/a b" "b/a b"\n')
        self.unknown([f'git apply {tmp}/quoted.patch'], "cannot read")

    def test_rebase_compares_the_tree_of_head_with_the_target(self):
        self.p.git("checkout", "-q", "hooks")
        self.asks(['git rebase main', 'git rebase -i main', 'git rebase --onto main hooks~1'], self.HOOK)
        self.allowed(['git rebase hooks'])

    def test_stash_push_and_clean_ask_when_they_would_touch_a_protected_path(self):
        self.allowed(['git stash', 'git stash push', 'git clean -fd', 'git clean -n', 'git clean -nd .githooks'])
        self.p.write(".claude/gw.json", self.p.work.joinpath(".claude/gw.json").read_text() + " ")
        self.asks(['git stash', 'git stash push', 'git stash save x', 'git stash -u'], ".claude/gw.json")
        self.allowed(['git clean -fd'])  # a tracked file is not cleaned
        self.p.write(".githooks/new-hook", "#!/bin/sh\n")
        self.asks(['git clean -fd', 'git clean -f'], ".githooks/new-hook")
        self.allowed(['git stash list'])
        self.allowed(['git clean -n', 'git clean --dry-run -d'])

    def test_merge_abort_looks_at_the_tree_and_continue_and_quit_write_nothing(self):
        self.allowed(['git merge --abort', 'git merge --continue', 'git merge --quit'])
        self.p.write(".claude/gw.json", self.p.work.joinpath(".claude/gw.json").read_text() + " ")
        self.asks(['git merge --abort'], ".claude/gw.json")
        self.allowed(['git merge --quit'])

    def test_the_commands_of_the_workflow_itself_pass(self):
        self.p.git("checkout", "-q", "docs")
        self.p.git("checkout", "-q", "main")
        self.allowed(['git checkout -', 'git checkout -q main', 'git merge --ff-only origin/main',
                      'git merge --no-ff origin/main', 'git fetch origin && git merge origin/main',
                      'git reset --hard origin/main', 'git checkout --track -b feature origin/main',
                      'git checkout main 2>/dev/null', 'git checkout -- docs/notes.md 2>/dev/null'])
        self.p.git("checkout", "-q", "hooks")
        self.p.git("checkout", "-q", "main")
        self.asks(['git checkout -'], self.HOOK)  # `-` is the previous branch

    def test_checkout_of_a_tree_ish_with_paths_looks_only_at_the_paths(self):
        self.allowed(['git checkout hooks -- docs/notes.md', 'git checkout hooks -- src'])
        self.assertAsks(self.p.tool("Bash", command='git checkout hooks -- .githooks/pre-push'), ".githooks/pre-push")

    def test_a_stash_with_an_untracked_protected_file_asks(self):
        self.p.write(".githooks/new-hook", "#!/bin/sh\n")
        self.p.git("stash", "-q", "-u")
        self.asks(['git stash pop', 'git stash apply'], ".githooks/new-hook")

    def test_git_c_reads_its_paths_from_that_folder(self):
        (self.p.work / ".claude" / "worktrees" / "a").mkdir(parents=True)
        self.p.git("worktree", "add", "-q", "-b", "agent", str(self.p.work / ".claude" / "worktrees" / "a"), "main")
        self.assertAsks(self.p.tool("Bash", command='git -C .claude/worktrees/a checkout -- .claude/gw.json'),
                        ".claude/worktrees/a/.claude/gw.json")
        self.assertAsks(self.p.tool("Bash", command='git -C .claude/gw/scripts checkout -- config.py'),
                        ".claude/gw/scripts/config.py")
        self.assertAsks(self.p.tool("Bash", command='git -C .claude -C gw checkout -- scripts/config.py'),
                        ".claude/gw/scripts/config.py")
        self.allowed(['git -C .claude/worktrees/a checkout -- docs/notes.md', 'git -C /tmp checkout -- gw.json',
                      'git -C .claude/gw status', 'git -C .claude/gw/scripts log'])
        self.assertAsks(self.p.tool("Bash", command='git -C .claude/worktrees/a merge hooks'),
                        ".claude/worktrees/a/.githooks/pre-push")

    def test_the_other_repo_check_follows_cd(self):
        other = self.tmp / "other"
        self.p.git("init", "-q", str(other), cwd=self.tmp)
        self.unknown([f'cd {other} && git merge docs'], "another repository")

    def test_a_git_that_fails_or_hangs_asks(self):
        real = shutil.which("git")
        fake = self.tmp / "fakebin"
        fake.mkdir()
        (fake / "git").write_text(f'#!/bin/sh\ncase "$*" in *diff*) echo "fatal: boom" >&2; exit 128;; esac\nexec {real} "$@"\n')
        (fake / "git").chmod(0o755)
        code, out = self.p.run(sys.executable, str(self.p.scripts / SCRIPT),
                               stdin=json.dumps({"tool_name": "Bash", "cwd": str(self.p.work),
                                                 "tool_input": {"command": "git merge docs"}}),
                               env={"PATH": f"{fake}:{os.environ['PATH']}"})
        self.assertAsks((code, out), "cannot tell which files it changes", "boom")


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
