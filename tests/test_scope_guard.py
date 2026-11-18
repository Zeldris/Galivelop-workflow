"""PreToolUse hook scripts/scope-guard.py (C13, `scopeGuard`: frozen scope) and its pre-commit backup
(`scope-guard.py --staged`, from templates/githooks/pre-commit), plus the task.py pieces it reads (files_of, in_files,
the deviations log, `new --related`). A temporary project laid out like one that applied the workflow; "allowed" is no
output. Every case that expects a warning or a deny checks what it says, not only the exit code."""
import json
import sys
import unittest

from test_hooks import BASE_CONFIG, Base, ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import task  # noqa: E402

RECORD = """# C13 · frozen scope

## Goal

Guard the scope.

## Scope

—

## Acceptance

- [ ] works

## Files

- `src/a.py`
- `src/lib/`
- `tests/test_*.py`
- `docs/tasks/C13/…`
- run `python3 x.py` (a command, skipped)

## Change log

—

## Verification

—
"""


class Scope(Base):
    config = {"taskId": "[A-H]\\d+"}
    hooks = ("pre-commit",)

    def build(self):
        super().build()
        p = self.p
        p.write("docs/tasks/C13.md", RECORD)
        p.write("docs/tasks/C14.md", RECORD.replace("## Files\n", "## Other\n").replace("C13", "C14"))
        p.write("src/a.py", "a = 1\n")
        p.write("src/b.py", "b = 1\n")
        p.commit("record")
        p.git("checkout", "-q", "-b", "agent/C13-scope")

    def set_config(self, **extra):
        (self.p.work / ".claude" / "gw.json").write_text(json.dumps(dict(BASE_CONFIG, **self.config, **extra), indent=2))

    def hook(self, path, tool="Edit", cwd=None, work=None):
        work = work or self.p.work
        event = {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": str(cwd or work),
                 "tool_input": {"file_path": path, "old_string": "a", "new_string": "b"}}
        code, out = self.p.run(sys.executable, "-B", str(work / ".claude" / "gw" / "scripts" / "scope-guard.py"),
                               stdin=json.dumps(event), cwd=str(work))
        self.assertEqual(code, 0, out)
        return out

    def spec(self, out):
        data = json.loads(out)
        return data["hookSpecificOutput"]

    def deviations(self):
        f = self.p.work / ".git" / "gw" / "deviations.jsonl"
        return [json.loads(l) for l in f.read_text().splitlines()] if f.exists() else []

    # In scope and always allowed

    def test_in_scope_file_is_allowed(self):
        self.assertEqual(self.hook("src/a.py"), "")
        self.assertEqual(self.deviations(), [])

    def test_folder_prefix_and_glob_match(self):
        self.assertEqual(self.hook("src/lib/deep/x.py"), "")
        self.assertEqual(self.hook("tests/test_new.py"), "")
        self.assertNotEqual(self.hook("src/library.py"), "")  # a prefix is a folder, not a string prefix

    def test_record_its_folder_questions_and_log_always_allowed_even_in_block_mode(self):
        self.set_config(scopeGuard={"mode": "block"})
        for path in ("docs/tasks/C13.md", "docs/tasks/C13/2026-11-18-session-abc.md", "docs/questions.md", "docs/log.md"):
            self.assertEqual(self.hook(path), "", path)

    def test_absolute_path_and_windows_style_relative_path(self):
        self.assertEqual(self.hook(str(self.p.work / "src" / "a.py")), "")
        out = self.spec(self.hook("src\\b.py"))
        self.assertIn("`src/b.py` is outside the scope of task C13", out["additionalContext"])

    def test_windows_drive_path_and_file_outside_the_project_are_allowed(self):
        self.set_config(scopeGuard={"mode": "block"})
        self.assertEqual(self.hook("C:\\work\\src\\b.py"), "")
        self.assertEqual(self.hook(str(self.p.tmp / "elsewhere.py")), "")

    # Out of scope

    def test_out_of_scope_warns_once_then_silent_and_logs_each_time(self):
        out = self.spec(self.hook("src/b.py"))
        self.assertNotIn("permissionDecision", out)
        text = out["additionalContext"]
        self.assertIn("scope-guard: `src/b.py` is outside the scope of task C13 (`## Files` of docs/tasks/C13.md)", text)
        self.assertIn("`## Change log`", text)
        self.assertIn("task.py new <newid> --related C13", text)
        self.assertEqual(self.hook("src/b.py"), "")
        lines = self.deviations()
        self.assertEqual(len(lines), 2)
        self.assertEqual({k: lines[0][k] for k in ("task", "path", "rule", "action")},
                         {"task": "C13", "path": "src/b.py", "rule": "scope", "action": "warn"})
        self.assertRegex(lines[0]["ts"], r"^\d{4}-\d\d-\d\dT")
        code, listed = self.p.run(sys.executable, "-B", str(self.p.work / ".claude/gw/scripts/task.py"), "deviations",
                                  "--task", "C13")
        self.assertEqual(code, 0, listed)
        self.assertEqual(listed.count("C13  scope  warn  src/b.py"), 2, listed)

    def test_block_mode_denies_with_the_reason(self):
        self.set_config(scopeGuard={"mode": "block"})
        out = self.spec(self.hook("src/b.py", tool="Write"))
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("scope-guard (block mode): `src/b.py` is outside the scope of task C13",
                      out["permissionDecisionReason"])
        self.assertIn("--related C13", out["permissionDecisionReason"])
        self.assertEqual(self.deviations(), [])  # a deny lets nothing through

    def test_auto_follows_modes_questions(self):
        self.set_config(scopeGuard={"mode": "auto"}, modes={"questions": True})
        self.assertEqual(self.spec(self.hook("src/b.py"))["permissionDecision"], "deny")
        self.set_config(scopeGuard={"mode": "auto"}, modes={"questions": False})
        self.assertIn("additionalContext", self.spec(self.hook("src/b.py")))

    def test_block_mode_alone_ignores_modes_questions_and_off_does_nothing(self):
        self.set_config(scopeGuard={"mode": "warn"}, modes={"questions": True})
        self.assertNotIn("permissionDecision", self.spec(self.hook("src/b.py")))
        self.set_config(scopeGuard={"mode": "off"})
        self.assertEqual(self.hook("src/c.py"), "")

    def test_bad_mode_is_a_config_error_warned_not_denied(self):
        self.set_config(scopeGuard={"mode": "loud"})
        out = self.spec(self.hook("src/b.py"))
        self.assertNotIn("permissionDecision", out)
        self.assertIn(".claude/gw.json cannot be read", out["additionalContext"])
        self.assertIn("config.py validate", out["additionalContext"])
        self.assertEqual(self.hook("src/c.py"), "")  # once

    def test_other_tools_are_ignored(self):
        self.set_config(scopeGuard={"mode": "block"})
        self.assertEqual(self.hook("src/b.py", tool="Read"), "")

    # No scope to compare with

    def test_no_task_no_record_no_files_section_are_allowed(self):
        self.set_config(scopeGuard={"mode": "block"})
        self.p.git("checkout", "-q", "main")
        self.assertEqual(self.hook("src/b.py"), "")  # no branch task, no mark
        self.p.git("checkout", "-q", "-b", "agent/C99-x")
        self.assertEqual(self.hook("src/b.py"), "")  # no record
        self.p.git("checkout", "-q", "-b", "agent/C14-x")
        self.assertEqual(self.hook("src/b.py"), "")  # a record without `## Files`

    def test_mark_is_per_worktree(self):
        p = self.p
        self.set_config(scopeGuard={"mode": "block"})
        p.git("checkout", "-q", "main")
        p.run(sys.executable, "-B", str(p.work / ".claude/gw/scripts/task.py"), "current", "C13")
        self.assertEqual(self.spec(self.hook("src/b.py"))["permissionDecision"], "deny")  # the main tree's mark
        p.git("add", "-A")
        p.git("commit", "-q", "--no-verify", "-m", "block config")
        wt = p.tmp / "wt"
        p.git("worktree", "add", "-q", "-b", "feature", str(wt))
        self.assertEqual(self.hook(str(wt / "src" / "b.py"), work=wt), "")  # no mark in the linked worktree
        wt2 = p.tmp / "wt2"
        p.git("worktree", "add", "-q", "-b", "agent/C13-other", str(wt2), "main")
        out = self.spec(self.hook(str(wt2 / "src" / "b.py"), work=wt2))
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("task C13", out["permissionDecisionReason"])

    # The pre-commit backup

    def test_pre_commit_warns_about_staged_files_outside_files(self):
        p = self.p
        p.write("src/a.py", "a = 2\n")
        r = p.commit("in scope")
        self.assertNotIn("scope-guard", r.stdout + r.stderr)
        p.write("src/b.py", "b = 2\n")
        r = p.commit("out of scope")
        err = r.stdout + r.stderr
        self.assertIn("scope-guard: WARNING: these staged files are outside the scope of task C13", err)
        self.assertIn("  src/b.py", err)
        self.assertEqual(self.deviations()[-1]["action"], "commit-warn")

    def test_pre_commit_refuses_in_block_mode(self):
        p = self.p
        self.set_config(scopeGuard={"mode": "block"})
        p.git("add", "-A")
        p.git("commit", "-q", "--no-verify", "-m", "block config")
        p.write("src/b.py", "b = 3\n")
        r = p.commit("out of scope", ok=False)
        self.assertNotEqual(r.returncode, 0)
        err = r.stdout + r.stderr
        self.assertIn("scope-guard (block mode): these staged files are outside the scope of task C13", err)
        self.assertIn("git restore --staged -- 'src/b.py'", err)


class Parsing(unittest.TestCase):
    def test_files_of(self):
        self.assertEqual(task.files_of(RECORD), ["src/a.py", "src/lib/", "tests/test_*.py", "docs/tasks/C13/"])
        self.assertIsNone(task.files_of("# X\n\n## Goal\n\nx\n"))
        self.assertEqual(task.files_of("## Files\n\n`./a\\b.py`, `/abs`, `../up`, `C:/x`\n"), ["a/b.py"])

    def test_in_files(self):
        self.assertTrue(task.in_files("src/lib", ["src/lib/"]))
        self.assertTrue(task.in_files("a/b/c.py", ["a/*.py"]))  # fnmatch: * crosses folders
        self.assertFalse(task.in_files("src/libx.py", ["src/lib"]))

    def test_related_of(self):
        self.assertEqual(task.related_of("# X\n\nRelated: C14, C15\n"), ["C14", "C15"])


class NewRelated(Base):
    config = {"taskId": "[A-H]\\d+"}
    hooks = ()

    def test_new_related_links_both_records(self):
        p = self.p
        script = str(p.work / ".claude/gw/scripts/task.py")
        code, out = p.run(sys.executable, "-B", script, "new", "C20", "--related", "C13")
        self.assertEqual(code, 1)
        self.assertIn("docs/tasks/C13.md does not exist", out)
        self.assertEqual(p.run(sys.executable, "-B", script, "new", "C13")[0], 0)
        code, out = p.run(sys.executable, "-B", script, "new", "C20", "--related", "C13")
        self.assertEqual(code, 0, out)
        self.assertIn("Related: C13", (p.work / "docs/tasks/C20.md").read_text())
        old = (p.work / "docs/tasks/C13.md").read_text()
        self.assertIn("Related: C20", old)
        self.assertEqual(task.related_of(old), ["C20"])


if __name__ == "__main__":
    unittest.main()
