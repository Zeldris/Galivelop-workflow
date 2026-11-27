"""PreToolUse hook: scripts/questions-guard.py (C4 restrictive mode, C5 guide mode), and `task.py current` (the current
task: the branch `agent/<id>-...` beats the mark gw/current-task of the git dir). A temporary project laid out like one
that applied the workflow; the event JSON on stdin, "allowed" is no output. Every case that expects a deny or a
warning checks what it says, not only the exit code."""
import json
import shutil
import sys
import unittest

from test_hooks import Base, ROOT

QUESTIONS = """# Questions

## Q-1
- Refs: C4
- Status: open
- Asked: 2026-11-18
- Question: Which folder does the guard watch?
- Recommendation: all code

## Q-2
- Refs: C9
- Status: open
- Asked: 2026-11-18
- Question: Another task's question

## Q-3
- Refs: C4
- Status: answered
- Asked: 2026-11-18
- Question: Already answered
- Answer: yes
"""


class Guard(Base):
    config = {"taskId": "[A-H]\\d+", "modes": {"questions": True}}

    def build(self):
        super().build()
        p = self.p
        for name in ("questions-guard.py", "questions.py", "task.py"):
            shutil.copy2(ROOT / "scripts" / name, p.work / ".claude" / "gw" / "scripts" / name)
        p.write("docs/questions.md", QUESTIONS)
        p.write("src/app.py", "x = 1\n")
        p.git("add", "-A")
        p.git("commit", "-q", "--no-verify", "-m", "questions")
        p.git("checkout", "-q", "-b", "agent/C4-guard")

    def hook(self, path="src/app.py", tool="Edit", stdin=None, cwd=None, key="file_path"):
        event = {"hook_event_name": "PreToolUse", "tool_name": tool, "cwd": str(cwd or self.p.work),
                 "tool_input": {key: path, "old_string": "a", "new_string": "b"}}
        code, out = self.p.run(sys.executable, "-B", str(self.p.work / ".claude" / "gw" / "scripts" / "questions-guard.py"),
                               stdin=json.dumps(event) if stdin is None else stdin)
        self.assertEqual(code, 0, out)
        return out

    def spec(self, out):
        data = json.loads(out)
        self.assertEqual(list(data), ["hookSpecificOutput"], out)
        self.assertEqual(data["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        return data["hookSpecificOutput"]

    def assertDenies(self, out, *needles):
        spec = self.spec(out)
        self.assertEqual(spec.get("permissionDecision"), "deny", out)
        for n in needles:
            self.assertIn(n, spec["permissionDecisionReason"])
        return spec["permissionDecisionReason"]

    def assertWarns(self, out, *needles):
        spec = self.spec(out)
        self.assertNotIn("permissionDecision", spec)
        for n in needles:
            self.assertIn(n, spec["additionalContext"])
        return spec["additionalContext"]

    def set_mode(self, restrictive):
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg["modes"] = {"questions": restrictive}
        self.p.write(".claude/gw.json", json.dumps(cfg))

    def task(self, *args, cwd=None):
        return self.p.run(sys.executable, "-B", str((cwd or self.p.work) / ".claude" / "gw" / "scripts" / "task.py"), *args,
                          cwd=cwd)


class Restrictive(Guard):
    def test_denies_code_naming_each_open_question_and_the_way_on(self):
        reason = self.assertDenies(self.hook(), "task C4", "Q-1: Which folder does the guard watch?", "`src/app.py`",
                                   'questions.py answer "1. <answer>"', "questions.py accept-risk --refs C4")
        self.assertNotIn("Q-2", reason)  # another task's question
        self.assertNotIn("Q-3", reason)  # answered

    def test_every_editing_tool_is_guarded_and_others_are_not(self):
        for tool in ("Write", "MultiEdit"):
            self.assertDenies(self.hook(tool=tool), "Q-1")
        self.assertDenies(self.hook("src/nb.ipynb", tool="NotebookEdit", key="notebook_path"), "Q-1")
        self.assertEqual(self.hook(tool="Read"), "")

    def test_docs_and_content_are_allowed(self):
        self.assertEqual(self.hook("docs/design.md"), "")
        self.assertEqual(self.hook(str(self.p.work / "README.md")), "")

    def test_workflow_policy_files_are_code(self):
        self.assertDenies(self.hook(".claude/gw.json"), "Q-1")

    def test_accepted_risk_stops_blocking(self):
        code, out = self.p.run(sys.executable, "-B", str(self.p.work / ".claude" / "gw" / "scripts" / "questions.py"),
                               "accept-risk", "--refs", "C4")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.hook(), "")

    def test_questions_of_another_task_do_not_block(self):
        self.p.git("checkout", "-q", "-b", "agent/C5-other")
        self.assertEqual(self.hook(), "")  # C5 has none; Q-2 is C9's

    def test_no_current_task_allows(self):
        self.p.git("checkout", "-q", "-b", "feature")
        self.assertEqual(self.hook(), "")

    def test_mark_names_the_task_without_an_agent_branch_and_the_branch_beats_it(self):
        code, out = self.task("current", "C9")  # the branch agent/C4-guard keeps C4 current
        self.assertEqual(code, 0, out)
        self.assertIn("beats the mark", out)
        self.assertEqual(self.task("current")[1].strip(), "C4")
        self.assertDenies(self.hook(), "task C4", "Q-1")
        self.p.git("checkout", "-q", "-b", "feature")
        self.assertEqual(self.task("current")[1].strip(), "C9")
        self.assertDenies(self.hook(), "task C9", "Q-2")
        self.assertEqual(self.task("current", "--clear")[0], 0)
        self.assertEqual(self.task("current")[1], "")
        self.assertEqual(self.hook(), "")

    def test_mark_with_a_bad_id_is_refused_or_ignored(self):
        self.p.git("checkout", "-q", "-b", "feature")
        code, out = self.task("current", "nope")
        self.assertEqual(code, 1)
        self.assertIn("does not have the shape of taskId", out)
        mark = self.p.work / ".git" / "gw" / "current-task"
        mark.parent.mkdir(parents=True, exist_ok=True)
        mark.write_text("../../x\n")
        self.assertEqual(self.task("current")[1], "")
        self.assertEqual(self.hook(), "")

    def test_task_new_writes_the_mark(self):
        self.p.git("checkout", "-q", "-b", "feature")
        code, out = self.task("new", "C9")
        self.assertEqual(code, 0, out)
        self.assertEqual((self.p.work / ".git" / "gw" / "current-task").read_text(), "C9\n")
        self.assertDenies(self.hook(), "task C9")

    def test_broken_questions_file_denies_with_the_fix(self):
        self.p.write("docs/questions.md", QUESTIONS.replace("Status: open", "Status: maybe", 1))
        self.assertDenies(self.hook(), "docs/questions.md cannot be read", "Status 'maybe'", "questions.py list")
        self.assertEqual(self.hook("docs/x.md"), "")  # documentation is classified first: still allowed
        self.assertEqual(self.hook("docs/questions.md"), "")  # and the questions file itself, to fix it

    def test_windows_style_paths(self):
        self.assertDenies(self.hook("src\\app.py"), "`src/app.py`")
        self.assertEqual(self.hook("docs\\design.md"), "")
        self.assertEqual(self.hook(str(self.p.work) + "\\docs\\design.md"), "")
        if sys.platform != "win32":  # a drive path cannot be placed here: treated as code of the hook's project
            self.assertDenies(self.hook("C:\\proj\\src\\app.py"), "Q-1")

    def test_a_file_outside_the_project_is_allowed(self):
        self.assertEqual(self.hook(str(self.tmp / "elsewhere" / "x.py")), "")
        self.assertEqual(self.hook("../outside.py"), "")

    def test_an_unreadable_event_counts_as_code(self):
        out = self.p.run(sys.executable, "-B", str(self.p.work / ".claude" / "gw" / "scripts" / "questions-guard.py"),
                         stdin="not json")[1]
        self.assertDenies(out, "Q-1", "the event named none")

    def test_task_new_never_switches_a_marked_task(self):  # the user switches it, with `current` (config-guard asks)
        self.p.git("checkout", "-q", "-b", "feature")
        self.assertEqual(self.task("current", "C4")[0], 0)
        code, out = self.task("new", "C99")
        self.assertEqual(code, 0, out)
        self.assertIn("the current task stays C4", out)
        self.assertEqual(self.task("current")[1].strip(), "C4")
        self.assertDenies(self.hook(), "task C4", "Q-1")

    def test_task_new_on_an_existing_record_does_not_mark(self):
        self.p.git("checkout", "-q", "-b", "feature")
        self.assertEqual(self.task("new", "C9")[0], 0)  # no mark: written
        self.assertEqual(self.task("current")[1].strip(), "C9")
        self.assertEqual(self.task("current", "--clear")[0], 0)
        code, out = self.task("new", "C9")
        self.assertEqual(code, 1)
        self.assertIn("exists already", out)
        self.assertEqual(self.task("current")[1], "")  # the refused `new` left no mark
        self.assertEqual(self.task("current", "C4")[0], 0)
        self.assertEqual(self.task("new", "C9")[0], 1)
        self.assertEqual(self.task("current")[1].strip(), "C4")

    def test_a_broken_config_denies_code_and_names_the_check(self):
        self.p.write(".claude/gw.json", "{ not json")
        self.p.git("checkout", "-q", "-b", "feature")  # no current task: a broken config still blocks code
        self.assertDenies(self.hook(), ".claude/gw.json cannot be read", "invalid JSON", "config.py validate")
        self.assertEqual(self.hook("docs/design.md"), "")
        self.assertEqual(self.hook(".claude/gw.json"), "")  # the fix itself

    def test_symlink_from_outside_to_code_is_that_code(self):
        link = self.tmp / "link.py"
        link.symlink_to(self.p.work / "src" / "app.py")
        self.assertDenies(self.hook(str(link)), "`src/app.py`")

    def test_a_path_spelled_through_another_name_of_the_root_is_placed(self):
        # what a case-insensitive file system does with /Users/x/Repo for /Users/x/repo: samefile, not the text
        import importlib.util
        spec = importlib.util.spec_from_file_location("qguard", ROOT / "scripts" / "questions-guard.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        alias = self.tmp / "Alias"
        alias.symlink_to(self.p.work)
        self.assertEqual(mod.relative(str(alias / "src" / "app.py"), str(self.p.work)), "src/app.py")
        self.assertIsNone(mod.relative(str(self.tmp / "other" / "x.py"), str(self.p.work)))

    def test_works_from_a_plugin_copy_outside_the_project(self):
        plugin = self.tmp / "plugin"
        (plugin / "scripts").mkdir(parents=True)
        (plugin / "schema").mkdir()
        for name in ("questions-guard.py", "questions.py", "task.py", "config.py", "handoff.py", "is-code.sh"):
            shutil.copy2(ROOT / "scripts" / name, plugin / "scripts" / name)
        shutil.copy2(ROOT / "schema" / "gw.schema.json", plugin / "schema" / "gw.schema.json")
        event = json.dumps({"tool_name": "Edit", "cwd": str(self.p.work), "tool_input": {"file_path": "src/app.py"}})
        code, out = self.p.run(sys.executable, "-B", str(plugin / "scripts" / "questions-guard.py"), stdin=event,
                               env={"CLAUDE_PROJECT_DIR": str(self.p.work)})
        self.assertEqual(code, 0, out)
        self.assertDenies(out, "task C4", "Q-1")
        event = json.dumps({"tool_name": "Edit", "cwd": str(self.p.work), "tool_input": {"file_path": "docs/a.md"}})
        self.assertEqual(self.p.run(sys.executable, "-B", str(plugin / "scripts" / "questions-guard.py"), stdin=event,
                                    env={"CLAUDE_PROJECT_DIR": str(self.p.work)})[1], "")

    def test_never_runs_an_is_code_sh_of_the_project(self):  # D5 (E28): only the workflow's own copy, next to the hook
        plugin = self.tmp / "plugin"
        (plugin / "scripts").mkdir(parents=True)
        (plugin / "schema").mkdir()
        for name in ("questions-guard.py", "questions.py", "task.py", "config.py", "handoff.py", "is-code.sh"):
            shutil.copy2(ROOT / "scripts" / name, plugin / "scripts" / name)
        shutil.copy2(ROOT / "schema" / "gw.schema.json", plugin / "schema" / "gw.schema.json")
        marker = self.tmp / "ran.txt"
        for folder in (self.p.work / "scripts", self.p.work / ".claude" / "gw" / "scripts"):
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "is-code.sh").write_text(f"echo ran >> '{marker}'\nexit 0\n")
        for rel, denied in (("src/app.py", True), ("docs/a.md", False)):
            event = json.dumps({"tool_name": "Edit", "cwd": str(self.p.work), "tool_input": {"file_path": rel}})
            code, out = self.p.run(sys.executable, "-B", str(plugin / "scripts" / "questions-guard.py"), stdin=event,
                                   env={"CLAUDE_PROJECT_DIR": str(self.p.work)})
            self.assertEqual(code, 0, out)
            if denied:
                self.assertDenies(out, "task C4", "Q-1")
            else:
                self.assertEqual(out, "")
        self.assertFalse(marker.exists(), "the project's is-code.sh ran")

    def test_questions_live_in_the_main_worktree(self):
        wt = self.tmp / "wt"
        self.p.git("worktree", "add", "-q", "-b", "agent/C9-side", str(wt))
        (wt / "docs" / "questions.md").write_text("# Questions\n")  # the worktree's copy has none ...
        reason = self.assertDenies(self.hook(str(wt / "src" / "app.py")), "task C9", "Q-2")  # ... the main one counts
        self.assertIn(f"--root {self.p.work}", reason)  # commands that write where the guard reads
        code, out = self.p.run(sys.executable, "-B", str(self.p.work / ".claude" / "gw" / "scripts" / "questions.py"),
                               "--root", str(self.p.work), "answer", "2. done")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.hook(str(wt / "src" / "app.py")), "")  # an answer recorded in main unblocks it

    def test_git_hanging_fails_closed(self):
        fake = self.tmp / "bin"
        fake.mkdir()
        real = shutil.which("git")
        (fake / "git").write_text(f'#!/bin/sh\nfor a in "$@"; do [ "$a" = symbolic-ref ] && exec sleep 60; done\n'
                                  f'exec "{real}" "$@"\n')
        (fake / "git").chmod(0o755)
        import os
        event = json.dumps({"tool_name": "Edit", "cwd": str(self.p.work), "tool_input": {"file_path": "src/app.py"}})
        code, out = self.p.run(sys.executable, "-B", str(self.p.work / ".claude" / "gw" / "scripts" / "questions-guard.py"),
                               stdin=event, env={"PATH": f"{fake}{os.pathsep}{os.environ.get('PATH', '')}"})
        self.assertDenies(out, "git did not answer", "symbolic-ref", "index.lock")

    def test_worktree_has_its_own_branch_and_mark(self):
        wt = self.tmp / "wt"
        self.p.git("worktree", "add", "-q", "-b", "agent/C9-side", str(wt))
        # an edit in the linked worktree reads that worktree's branch, with the hook of the main clone
        self.assertDenies(self.hook(str(wt / "src" / "app.py")), "task C9", "Q-2")
        self.p.git("checkout", "-q", "-b", "feature")
        self.assertEqual(self.task("current", "C4")[0], 0)  # the main clone's mark (git dir, not the common dir) ...
        self.p.git("-C", str(wt), "checkout", "-q", "-b", "plain")
        self.assertEqual(self.task("current", cwd=wt)[1], "")  # ... is not the worktree's
        self.assertEqual(self.hook(str(wt / "src" / "app.py")), "")
        self.assertDenies(self.hook(), "task C4")


class GuideMode(Guard):
    config = {"taskId": "[A-H]\\d+", "modes": {"questions": False}}

    def test_warns_once_per_set_of_open_questions_then_is_silent(self):
        self.assertWarns(self.hook(), "guide mode", "task C4", "Q-1: Which folder", "questions.py accept-risk --refs C4")
        self.assertEqual(self.hook(), "")
        self.assertEqual(self.hook("src/other.py"), "")
        code, out = self.p.run(sys.executable, "-B", str(self.p.work / ".claude" / "gw" / "scripts" / "questions.py"),
                               "add", "--refs", "C4", "A new one?")
        self.assertEqual(code, 0, out)
        self.assertWarns(self.hook(), "Q-1", "Q-4: A new one?")  # a new question warns again

    def test_docs_do_not_warn_nor_spend_the_warning(self):
        self.assertEqual(self.hook("docs/design.md"), "")
        self.assertWarns(self.hook(), "Q-1")

    def test_accepted_risk_stops_the_warning(self):
        self.p.run(sys.executable, "-B", str(self.p.work / ".claude" / "gw" / "scripts" / "questions.py"),
                   "accept-risk", "--refs", "C4")
        self.assertEqual(self.hook(), "")

    def test_broken_questions_file_is_a_one_line_warning(self):
        self.p.write("docs/questions.md", "## Q-1\n- Status: open\n\n## Q-1\n- Status: open\n")
        text = self.assertWarns(self.hook(), "cannot be read", "appears twice", "questions.py list")
        self.assertEqual(len(text.splitlines()), 1)
        self.assertEqual(self.hook(), "")  # once per reason, not on every edit
        self.assertEqual(self.hook("docs/questions.md"), "")


class MissingConfig(Guard):
    def test_without_a_config_the_defaults_apply_guide_mode(self):
        (self.p.work / ".claude" / "gw.json").unlink()
        self.assertEqual(self.hook(), "")  # the default taskId ([A-Z]{2,5}-<n>) does not read C4 in the branch
        self.p.write("docs/questions.md", QUESTIONS.replace("Refs: C4", "Refs: AB-7"))
        self.p.git("checkout", "-q", "-b", "agent/AB-7-x")
        self.assertWarns(self.hook(), "guide mode", "task AB-7", "Q-1")  # default questions.path and modes

    def test_restrictive_mode_switches_to_guide(self):
        self.set_mode(False)
        self.assertWarns(self.hook(), "guide mode")


if __name__ == "__main__":
    unittest.main()
