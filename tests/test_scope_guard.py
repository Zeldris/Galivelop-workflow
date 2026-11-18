"""PreToolUse hook scripts/scope-guard.py (C13, `scopeGuard`: frozen scope) and its pre-commit backup
(`scope-guard.py --staged`, from templates/githooks/pre-commit), plus the task.py pieces it reads (files_of, in_files,
the deviations log, `new --related`). A temporary project laid out like one that applied the workflow; "allowed" is no
output. Every case that expects a warning or a deny checks what it says, not only the exit code."""
import json
import shutil
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


class ScopeBase(Base):
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

    def load_guard(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("scope_guard", self.p.work / ".claude/gw/scripts/scope-guard.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def spec(self, out):
        data = json.loads(out)
        return data["hookSpecificOutput"]

    def deviations(self):
        f = self.p.work / ".git" / "gw" / "deviations.jsonl"
        return [json.loads(l) for l in f.read_text().splitlines()] if f.exists() else []



class Scope(ScopeBase):
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


class ReviewFixes(ScopeBase):
    """The /code-review findings 1-6 and 10 (C13)."""

    def staged(self, env=None):
        return self.p.run(sys.executable, "-B", str(self.p.work / ".claude/gw/scripts/scope-guard.py"), "--staged",
                          env=env)

    def block(self):
        self.set_config(scopeGuard={"mode": "block"})
        self.p.git("add", "-A")
        self.p.git("commit", "-q", "--no-verify", "-m", "block config")

    def test_1_workflow_files_from_the_config_are_always_allowed(self):
        self.block()
        sys.path.insert(0, str(ROOT / "scripts"))
        import config as gwconfig
        cfg = gwconfig.load(self.p.work)
        for rel in (gwconfig.metrics(cfg)["ledger"], cfg["reviewMark"], cfg["ciLocalLog"]):
            self.assertEqual(self.hook(rel), "", rel)
        self.p.write(gwconfig.metrics(cfg)["ledger"], "{}\n")
        self.p.write(cfg["reviewMark"], "abc\n")
        r = self.p.commit("ledger and mark")
        self.assertNotIn("scope-guard", r.stdout + r.stderr)

    def test_2_a_related_record_is_the_guards_own_way_on(self):
        self.block()
        code, out = self.p.run(sys.executable, "-B", str(self.p.work / ".claude/gw/scripts/task.py"), "new", "C20",
                               "--related", "C13")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.hook("docs/tasks/C20.md"), "")
        self.assertEqual(self.hook("docs/tasks/C20/2026-11-18-session-abc.md"), "")
        r = self.p.commit("new requirement")
        self.assertNotIn("scope-guard", r.stdout + r.stderr)
        self.assertNotEqual(self.hook("docs/tasks/C21.md"), "")  # an unrelated record is not

    def test_3_git_stuck_warns_in_warn_mode_and_refuses_in_block(self):
        import contextlib
        import io
        mod = self.load_guard()

        def stuck(*_):
            raise mod.task.GitStuck("`git rev-parse` took more than 10s")
        mod.task.current_task = stuck
        for mode, code in (("warn", 0), ("block", 1)):
            self.set_config(scopeGuard={"mode": mode})
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(mod.staged(str(self.p.work)), code)
            self.assertIn("git did not answer (`git rev-parse` took more than 10s)", err.getvalue())
            self.assertIn("index.lock", err.getvalue())
            self.assertIn("(block mode)" if mode == "block" else "WARNING", err.getvalue())

    def test_3_own_failure_names_the_fix(self):
        fake = self.p.tmp / "fakebin"
        fake.mkdir()
        (fake / "git").write_text('#!/bin/sh\ncase "$*" in *"--name-only --no-renames -z"*) echo boom >&2; exit 2;; '
                                  'esac\nexec ' + shutil.which("git") + ' "$@"\n')
        (fake / "git").chmod(0o755)
        self.p.write("src/b.py", "b = 9\n")
        self.p.git("add", "-A")
        env = {"PATH": f"{fake}:{self.p.env['PATH']}"}
        code, out = self.staged(env)
        self.assertEqual(code, 0, out)
        self.assertIn("WARNING: it failed (RuntimeError: git diff --cached failed: boom)", out)
        self.assertIn("scope-guard.py --staged", out)

    def test_4_revert_squash_and_rebase_in_progress_are_skipped(self):
        self.block()
        self.p.write("src/b.py", "b = 4\n")
        self.p.git("add", "-A")
        code, out = self.staged()
        self.assertEqual(code, 1, out)
        for name in ("REVERT_HEAD", "SQUASH_MSG", "rebase-merge"):
            path = self.p.work / ".git" / name
            path.mkdir() if name == "rebase-merge" else path.write_text("x\n")
            code, out = self.staged()
            self.assertEqual((code, out), (0, ""), name)
            shutil.rmtree(path) if name == "rebase-merge" else path.unlink()

    def test_5_growing_files_needs_a_change_log_line(self):
        self.block()
        rec = self.p.work / "docs/tasks/C13.md"
        rec.write_text(rec.read_text().replace("- `src/a.py`\n", "- `src/a.py`\n- `src/c.py`\n"))
        self.p.write("src/c.py", "c = 1\n")
        r = self.p.commit("grow", ok=False)
        self.assertNotEqual(r.returncode, 0)
        err = r.stdout + r.stderr
        self.assertIn("docs/tasks/C13.md adds to `## Files` without naming them in its `## Change log`", err)
        self.assertIn("  src/c.py", err)
        rec.write_text(rec.read_text().replace("## Change log\n\n—", "## Change log\n\n- `src/c.py`: the parser lives there"))
        r = self.p.commit("grow, explained")
        self.assertNotIn("scope-guard", r.stdout + r.stderr)

    def test_5_warn_mode_logs_the_unexplained_growth(self):
        rec = self.p.work / "docs/tasks/C13.md"
        rec.write_text(rec.read_text().replace("- `src/a.py`\n", "- `src/a.py`\n- `src/d.py`\n"))
        r = self.p.commit("grow")
        self.assertIn("WARNING: docs/tasks/C13.md adds to `## Files`", r.stdout + r.stderr)
        self.assertEqual(self.deviations()[-1]["action"], "files-unlogged")

    def test_6_pre_commit_names_each_missing_script(self):
        for name in ("task.py", "questions-guard.py", "questions.py"):
            path = self.p.work / ".claude/gw/scripts" / name
            saved = path.read_bytes()
            path.unlink()
            r = self.p.commit(f"no {name}", ok=False)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn(f".claude/gw/scripts/{name} is missing; reinstall the workflow scripts: /gw-update",
                          r.stdout + r.stderr)
            path.write_bytes(saved)

    def test_10_crash_reads_the_mode_of_the_edited_worktree(self):
        import contextlib
        import io
        wt = self.p.tmp / "wt"
        self.p.git("worktree", "add", "-q", "-b", "agent/C13-wt", str(wt))
        (wt / ".claude" / "gw.json").write_text(json.dumps(dict(BASE_CONFIG, **self.config, scopeGuard={"mode": "block"})))
        mod = self.load_guard()
        mod.STATE["top"] = wt
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            mod.crash(RuntimeError("boom"))
        spec = json.loads(out.getvalue())["hookSpecificOutput"]
        self.assertEqual(spec["permissionDecision"], "deny")
        self.assertIn("scope-guard.py failed (RuntimeError: boom)", spec["permissionDecisionReason"])
        mod.STATE.clear()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            mod.crash(RuntimeError("boom"))
        self.assertNotIn("permissionDecision", json.loads(out.getvalue())["hookSpecificOutput"])  # the session: warn


class VersionStamp(ScopeBase):
    """B44: a copy of the workflow and a version stamp are not deviations; a real change still is."""

    def stamped(self, version="0.8.0", body="x = 1\n"):
        self.p.write("src/s.py", f"# galivelop-workflow v{version}\n{body}")

    def setUp(self):
        super().setUp()
        self.stamped()
        self.p.commit("a stamped file, outside the scope")  # warn mode: the commit goes through

    def staged_err(self, vendored=None):
        """(exit code, stderr+stdout) of `scope-guard.py --staged`; VENDORED patches what apply.py --vendored says."""
        code = ("import importlib.util, sys; from pathlib import Path\n"
                "spec = importlib.util.spec_from_file_location('sg', '.claude/gw/scripts/scope-guard.py')\n"
                "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
                f"v = {vendored!r}\n"
                "if v is not None:\n"
                "    m.rs.workflow_dir = lambda arg: Path('.')\n"
                "    m.rs.vendored = lambda root, workflow, timeout=None: v\n"
                "sys.exit(m.staged(None))\n")
        return self.p.run(sys.executable, "-B", "-c", code, cwd=str(self.p.work))

    def test_stamp_only_change_is_not_a_deviation(self):
        self.stamped("0.8.1")
        self.p.git("add", "-A")
        code, err = self.staged_err()
        self.assertEqual((code, err), (0, ""))

    def test_a_stamp_commit_in_block_mode_needs_nothing_else(self):
        self.stamped("0.8.1")
        self.p.git("add", "-A")
        self.set_config(scopeGuard={"mode": "block"})
        code, err = self.staged_err()
        self.assertEqual((code, err), (0, ""))

    def test_stamp_plus_real_change_still_counts(self):
        self.stamped("0.8.1", body="x = 2\n")
        self.p.git("add", "-A")
        code, err = self.staged_err()
        self.assertEqual(code, 0)
        self.assertIn("these staged files are outside the scope of task C13", err)
        self.assertIn("  src/s.py", err)

    def test_a_vendored_copy_is_not_a_deviation_and_an_edited_one_is(self):
        self.p.write("src/b.py", "b = 5\n")
        self.p.git("add", "-A")
        self.assertEqual(self.staged_err({"src/b.py"}), (0, ""))
        code, err = self.staged_err(set())  # the project edited it: no longer an unchanged copy
        self.assertEqual(code, 0)
        self.assertIn("  src/b.py", err)

    def test_hook_skips_a_stamp_only_edit_but_not_a_real_one(self):
        def edit(old, new):
            event = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "cwd": str(self.p.work),
                     "tool_input": {"file_path": "src/s.py", "old_string": old, "new_string": new}}
            code, out = self.p.run(sys.executable, "-B", str(self.p.work / ".claude/gw/scripts/scope-guard.py"),
                                   stdin=json.dumps(event), cwd=str(self.p.work))
            self.assertEqual(code, 0, out)
            return out
        before = len(self.deviations())
        self.assertEqual(edit("# galivelop-workflow v0.8.0", "# galivelop-workflow v0.8.1"), "")
        self.assertEqual(len(self.deviations()), before)
        out = self.spec(edit("x = 1", "x = 2"))
        self.assertIn("`src/s.py` is outside the scope of task C13", out["additionalContext"])

    def hook_with_vendored(self, rel, vendored, old="a", new="b"):
        """Output of the PreToolUse hook for an edit of REL while apply.py --vendored says VENDORED (patched in)."""
        event = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "cwd": str(self.p.work),
                 "tool_input": {"file_path": rel, "old_string": old, "new_string": new}}
        code = ("import importlib.util, sys; from pathlib import Path\n"
                "spec = importlib.util.spec_from_file_location('sg', '.claude/gw/scripts/scope-guard.py')\n"
                "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
                "m.rs.workflow_dir = lambda arg: Path('.')\n"
                f"m.rs.vendored = lambda root, workflow, timeout=None: {vendored!r}\n"
                "sys.exit(m.main([]))\n")
        code, out = self.p.run(sys.executable, "-B", "-c", code, stdin=json.dumps(event), cwd=str(self.p.work))
        self.assertEqual(code, 0, out)
        return out

    def hook_edit(self, old, new, rel="src/s.py"):
        event = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "cwd": str(self.p.work),
                 "tool_input": {"file_path": rel, "old_string": old, "new_string": new}}
        code, out = self.p.run(sys.executable, "-B", str(self.p.work / ".claude/gw/scripts/scope-guard.py"),
                               stdin=json.dumps(event), cwd=str(self.p.work))
        self.assertEqual(code, 0, out)
        return out

    def test_hook_does_not_exempt_a_vendored_copy_before_the_edit(self):
        self.p.write("src/b.py", "b = 5\n")
        out = self.spec(self.hook_with_vendored("src/b.py", {"src/b.py"}))  # before an edit a copy is always unchanged
        self.assertIn("`src/b.py` is outside the scope of task C13", out["additionalContext"])

    def test_vendored_set_is_empty_when_apply_times_out(self):
        import subprocess as sp
        mod = self.load_guard()
        mod.rs.workflow_dir = lambda arg: Path(".")

        def slow(*a, **k):
            raise sp.TimeoutExpired("apply.py", k.get("timeout"))
        saved, sp.run = sp.run, slow
        try:
            self.assertEqual(mod.vendored_set(self.p.work), set())  # nothing skipped: the safe side
        finally:
            sp.run = saved

    def test_skip_keys_off_make_stamps_and_copies_count_again(self):
        self.set_config(scopeGuard={"mode": "warn", "skipStamps": False, "skipVendored": False})
        self.stamped("0.8.1")
        self.p.git("add", "-A")
        code, err = self.staged_err()
        self.assertEqual(code, 0)
        self.assertIn("  src/s.py", err)  # skipStamps false: the stamp-only change is a deviation
        self.p.write("src/b.py", "b = 5\n")
        self.p.git("add", "-A")
        code, err = self.staged_err({"src/b.py"})
        self.assertIn("  src/b.py", err)  # skipVendored false: the copy counts
        out = self.spec(self.hook_edit("# galivelop-workflow v0.8.0", "# galivelop-workflow v0.8.1"))
        self.assertIn("`src/s.py` is outside the scope of task C13", out["additionalContext"])

    def test_a_json_version_outside_the_stamped_files_is_not_a_stamp(self):
        self.p.write("src/package.json", '{\n  "version": "4.17.20"\n}\n')
        self.p.git("add", "-A")
        self.p.commit("a package")
        self.p.write("src/package.json", '{\n  "version": "4.17.21"\n}\n')
        self.p.git("add", "-A")
        code, err = self.staged_err()
        self.assertIn("  src/package.json", err)

    def test_the_staged_diff_takes_a_bracket_path_literally(self):
        self.p.write("app/[id].py", "# galivelop-workflow v0.8.0\n")
        self.p.write("app/i.py", "x = 1\n")
        self.p.git("add", "-A")
        self.p.commit("two files")
        self.p.write("app/[id].py", "# galivelop-workflow v0.8.1\n")
        self.p.write("app/i.py", "x = 2\n")
        self.p.git("add", "-A")
        code, err = self.staged_err()
        self.assertIn("  app/i.py", err)
        self.assertNotIn("app/[id].py", err)  # a glob `[id]` would have read i.py's change into the stamp file's


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
