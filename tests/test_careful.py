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

    def hook(self, event=None, stdin=None, cwd=None):
        text = json.dumps({"hook_event_name": "PreToolUse", "cwd": str(cwd or self.work), **(event or {})}) \
            if stdin is None else stdin
        return self.run("python3", str(self.scripts / "careful.py"), stdin=text or None)

    def bash(self, command, cwd=None):
        return self.hook({"tool_name": "Bash", "tool_input": {"command": command}}, cwd=cwd)


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

    def linked(self, name="x", where=".claude/worktrees"):
        wt = self.p.work / where / name
        self.p.git("worktree", "add", "-q", "-b", f"agent/{name}", str(wt))
        return wt

    def set_modes(self, **modes):
        cfg = json.loads((self.p.work / ".claude/gw.json").read_text())
        self.p.write(".claude/gw.json", json.dumps(dict(cfg, modes=modes)))

    def test_linked_worktree_is_disposable_for_reset_clean_restore_only(self):
        wt = self.linked()
        for command in ("git reset --hard abc123", "git clean -fd", "git checkout -- .", "git restore .",
                        "git checkout -f main", "git switch -f main", "git switch --discard-changes main"):
            with self.subTest(command=command, where="linked"):
                self.assertAllowed(self.p.bash(command, cwd=wt))
            with self.subTest(command=command, where="main"):
                self.assertAsks(self.p.bash(command), "destructive command")
        self.assertAllowed(self.p.bash(f"git -C {wt} reset --hard"))  # -C into the linked worktree
        self.assertAsks(self.p.bash(f"git -C {self.p.work} reset --hard", cwd=wt), "uncommitted")
        for command, needle in (("rm -rf build", "rm -r"), ("git push --force", "remote history"),
                                ("git push origin :old", "deletes a remote"), ("git branch -D old", "not merged")):
            with self.subTest(command=command, where="linked still asks"):
                self.assertAsks(self.p.bash(command, cwd=wt), needle)

    # The nine findings of the review of C8, one test each (the scenario first).
    def test_f1_cd_in_the_command_removes_the_worktree_exemption(self):
        wt = self.linked()
        self.assertAllowed(self.p.bash("git reset --hard", cwd=wt))
        for command in (f"cd {self.p.work} && git reset --hard", f"pushd {self.p.work}; git clean -fdx",
                        f"cd {self.p.work}\ngit checkout -- ."):
            with self.subTest(command=command):
                self.assertAsks(self.p.bash(command, cwd=wt), "destructive command")

    def test_f2_here_string_and_quoted_heredoc_marker_do_not_hide_what_follows(self):
        for command in ('grep x <<< "$v"\nrm -rf ~/proj', 'git commit -m "ver <<EOF"\ngit push -f',
                        'grep x <<<foo\nrm -rf ~/proj', "echo '<<EOF'\ngit reset --hard", "cat <<$v\nrm -rf ~/proj"):
            with self.subTest(command=command):
                self.assertAsks(self.p.bash(command), "destructive command")
        self.assertAllowed(self.p.bash("cat <<-'EOF'\n\trm -rf x\n\tEOF"))
        self.assertAllowed(self.p.bash("cat <<A <<B\nrm -rf x\nA\ngit reset --hard\nB"))

    def test_f3_git_alias_it_cannot_follow_asks(self):
        self.p.git("config", "alias.nuke", "!git reset --hard && git clean -fdx")
        self.assertAsks(self.p.bash("git nuke"), "alias it cannot follow", "runs a shell command")

    def test_f4_eval_joins_its_words(self):
        self.assertAsks(self.p.bash("eval rm -rf /home/user/proj"), "rm -r")
        self.assertAsks(self.p.bash("eval git reset --hard"), "uncommitted")
        self.assertAllowed(self.p.bash("eval echo hi"))

    def test_f5_git_env_prefix_removes_the_worktree_exemption(self):
        wt = self.linked()
        for command in (f"GIT_WORK_TREE={self.p.work} GIT_DIR={self.p.work}/.git git reset --hard",
                        f"GIT_DIR={self.p.work}/.git git clean -fd"):
            with self.subTest(command=command):
                self.assertAsks(self.p.bash(command, cwd=wt), "destructive command")

    def test_f6_tmpdir_prefix_needs_tmpdir_set(self):
        import os
        for value, asks in (("", True), ("/", True), ("/var/tmp", False)):
            env_cmd = 'rm -rf "$TMPDIR/home" ${TMPDIR}/x'
            with self.subTest(TMPDIR=value):
                self.p.env["TMPDIR"] = value if value else ""
                res = self.p.bash(env_cmd)
                self.assertAsks(res, "rm -r") if asks else self.assertAllowed(res)
        self.p.env.pop("TMPDIR", None)
        self.assertAsks(self.p.bash("rm -rf $TMPDIR/home"), "rm -r")
        self.assertAllowed(self.p.bash("rm -rf /tmp/x"))  # the literal prefixes do not depend on TMPDIR

    def test_f7_only_worktrees_under_the_configured_prefixes_are_exempt(self):
        other = self.linked("feature", where="../side")
        mine = self.linked("mine")
        self.assertAsks(self.p.bash("git reset --hard", cwd=other), "uncommitted")  # a real worktree, not an agent's
        self.assertAllowed(self.p.bash("git reset --hard", cwd=mine))
        self.set_modes(carefulWorktrees=[])
        self.assertAsks(self.p.bash("git reset --hard", cwd=mine), "uncommitted")  # empty list = no exemption
        self.set_modes(carefulWorktrees=["../side/"])
        self.assertAllowed(self.p.bash("git clean -fd", cwd=other))
        self.assertAsks(self.p.bash("git clean -fd", cwd=mine), "untracked")

    def test_f8_mirror_prune_and_forced_checkout_ask(self):
        for command, needle in (("git push --mirror origin", "remote history"), ("git push --prune origin", "remote history"),
                                ("git checkout -f main", "-f"), ("git checkout --force main", "-f"),
                                ("git switch -f main", "-f"), ("git switch --discard-changes main", "-f")):
            with self.subTest(command=command):
                self.assertAsks(self.p.bash(command), needle)
        self.assertAllowed(self.p.bash("git switch main"))
        self.assertAllowed(self.p.bash("git checkout main"))

    def test_f9_git_rev_parse_runs_only_where_the_exemption_matters(self):
        import subprocess
        trace = self.tmp / "trace.log"
        self.p.env["GIT_TRACE"] = str(trace)
        for command in ("git status", "git log -1", "git diff", "git push origin main", "git branch -a"):
            self.assertAllowed(self.p.bash(command))
        self.assertNotIn("--git-common-dir", trace.read_text() if trace.exists() else "")
        self.assertAsks(self.p.bash("git reset --hard"), "uncommitted")
        self.assertIn("--git-common-dir", trace.read_text())

    def test_wrappers_and_assignments_before_git_are_looked_through(self):
        for command in ("sudo git reset --hard", "FOO=1 git push -f", "env -u X git clean -fd", "nice -n 5 git push --mirror"):
            with self.subTest(command=command):
                self.assertAsks(self.p.bash(command), "destructive command")

    def test_template_and_plugin_register_it(self):
        for rel in ("templates/claude/settings.json", "hooks/hooks.json"):
            data = json.loads((ROOT / rel).read_text())
            found = [g for g in data["hooks"]["PreToolUse"]
                     if any("careful.py" in h["command"] for h in g["hooks"])]
            self.assertEqual([g["matcher"] for g in found], ["Bash"], rel)


if __name__ == "__main__":
    unittest.main()
