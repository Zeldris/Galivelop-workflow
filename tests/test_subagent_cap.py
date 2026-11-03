"""PreToolUse hook: scripts/subagent-cap.py (P3 of docs/proposals/2026-10-25-repos-x.md), in a temporary project
laid out like one that applied the workflow, run the way Claude Code runs a hook: the event JSON on stdin, the answer on
stdout with exit 0. `ask` is the documented PreToolUse JSON; "no opinion" is no output at all.

Every case that expects an `ask` checks the reason, not only the exit code. The counter lives in a folder the tests
point at with GW_SUBAGENT_COUNTER_DIR, except the one case that proves the default is the temp directory.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_hooks import ROOT, Project

SCRIPT = "subagent-cap.py"


class SubagentCapProject(Project):
    def __init__(self, tmp, config=None):
        super().__init__(tmp, config=config, hooks=())
        self.scripts = self.work / ".claude" / "gw" / "scripts"
        shutil.copy2(ROOT / "scripts" / SCRIPT, self.scripts / SCRIPT)
        self.counters = tmp / "counters"
        self.counters.mkdir()
        self.env["GW_SUBAGENT_COUNTER_DIR"] = str(self.counters)
        self.home = tmp / "home"
        self.home.mkdir()
        self.env["HOME"] = str(self.home)

    def agent(self, name, text, user=False):
        folder = (self.home if user else self.work) / ".claude" / "agents"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / (name + ".md")).write_text(text)

    def event(self, session="s1", tool="Agent", **extra):
        data = {"hook_event_name": "PreToolUse", "cwd": str(self.work), "tool_name": tool,
                "tool_input": {"prompt": "do it", "model": "haiku"}}
        if session is not None:
            data["session_id"] = session
        data.update(extra)
        return data

    def call(self, session="s1", tool="Agent", env=None, **extra):
        return self.run("python3", str(self.scripts / SCRIPT), stdin=json.dumps(self.event(session, tool, **extra)),
                        env=env)

    def raw(self, text, env=None):
        return self.run("python3", str(self.scripts / SCRIPT), stdin=text or None, env=env)


class Base(unittest.TestCase):
    cfg = None

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-tope-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.p = SubagentCapProject(self.tmp, self.cfg)

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

    def assertQuiet(self, result):
        code, out = result
        self.assertEqual(code, 0, out)
        self.assertEqual(out.strip(), "", "below the cap there is no output at all")

    def reason(self, n, cap):
        return (f"{n} subagents in this session (subagentCap {cap} in .claude/gw.json): "
                f"check they are not looping (gw-opt-tokens)")


class CustomCap(Base):
    cfg = {"subagentCap": 3}

    def test_quiet_below_the_cap_then_asks_at_it_and_every_ten_after(self):
        for n in range(1, 24):
            with self.subTest(n=n):
                result = self.p.call()
                if n in (3, 13, 23):
                    self.assertEqual(self.assertAsks(result), self.reason(n, 3))
                else:
                    self.assertQuiet(result)

    def test_the_task_tool_counts_the_same(self):
        self.assertQuiet(self.p.call(tool="Task"))
        self.assertQuiet(self.p.call(tool="Agent"))
        self.assertAsks(self.p.call(tool="Task"), "3 subagents")

    def test_each_session_has_its_own_counter(self):
        self.assertQuiet(self.p.call("a"))
        self.assertQuiet(self.p.call("a"))
        self.assertQuiet(self.p.call("b"))
        self.assertQuiet(self.p.call("b"))
        self.assertAsks(self.p.call("a"), "3 subagents")
        self.assertAsks(self.p.call("b"), "3 subagents")

    def test_a_garbage_counter_file_restarts_at_zero(self):
        for garbage in (b"garbage", b"\xff\xfe\x00", b"-5", b"", b"2.5"):
            with self.subTest(garbage=garbage):
                shutil.rmtree(self.p.counters)
                self.p.counters.mkdir()
                self.assertQuiet(self.p.call())
                (path,) = list(self.p.counters.iterdir())
                path.write_bytes(garbage)
                self.assertQuiet(self.p.call())  # 1 again, not 2
                self.assertQuiet(self.p.call())  # 2
                self.assertAsks(self.p.call(), "3 subagents")

    def test_a_session_id_cannot_leave_the_counter_folder(self):
        self.assertQuiet(self.p.call("../../escape/../x"))
        self.assertEqual(len(list(self.p.counters.iterdir())), 1)
        self.assertFalse((self.tmp / "escape").exists())
        self.assertFalse((self.tmp / "x").exists())
        for rel in ("..", "../.."):
            self.assertQuiet(self.p.call(rel))

    def test_parallel_launches_are_all_counted(self):
        procs = [subprocess.Popen(["python3", str(self.p.scripts / SCRIPT)], cwd=self.p.work,
                                  env=dict(self.p.env), stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
                 for _ in range(3)]
        outs = [proc.communicate(json.dumps(self.p.event("par")))[0] for proc in procs]
        asked = [out for out in outs if out.strip()]
        self.assertEqual(len(asked), 1, outs)
        self.assertIn("3 subagents", asked[0])


class OldCountersAndLinks(Base):
    cfg = {"subagentCap": 3}

    def stale(self, name, days=8):
        path = self.p.counters / name
        path.write_text("5")
        old = path.stat().st_mtime - days * 86400
        os.utime(path, (old, old))
        return path

    def test_an_old_counter_is_cleaned_when_a_new_one_is_created(self):
        old = self.stale("gw-subagents-gone")
        other = self.p.counters / "unrelated-file"
        other.write_text("x")
        os.utime(other, (1, 1))
        self.assertQuiet(self.p.call("fresh"))
        self.assertFalse(old.exists(), "the stale counter must be deleted")
        self.assertTrue(other.exists(), "only gw-subagents-* files are touched")
        self.assertTrue((self.p.counters / "gw-subagents-fresh").exists())

    def test_a_counter_in_use_is_kept_and_keeps_counting(self):
        recent = self.stale("gw-subagents-live", days=1)
        self.assertQuiet(self.p.call("fresh"))
        self.assertEqual(recent.read_text(), "5")
        self.assertQuiet(self.p.call("fresh"))
        self.assertAsks(self.p.call("fresh"), "3 subagents")

    def test_clean_old_never_deletes_the_counter_in_use_even_when_it_is_stale(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("subagent_cap_under_test", ROOT / "scripts" / SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        keep = self.stale("gw-subagents-same")
        other = self.stale("gw-subagents-other")
        module.clean_old(str(keep))
        self.assertTrue(keep.exists(), "the guard path == keep must protect the counter in use")
        self.assertFalse(other.exists())

    @unittest.skipUnless(hasattr(os, "geteuid") and os.geteuid() == 0, "needs root to chown")
    def test_cleaning_leaves_the_stale_counters_of_other_users(self):
        theirs = self.stale("gw-subagents-theirs")
        os.chown(theirs, 12345, 12345)
        mine = self.stale("gw-subagents-mine")
        self.assertQuiet(self.p.call("fresh"))
        self.assertTrue(theirs.exists(), "a counter of another uid is not ours to delete")
        self.assertFalse(mine.exists())

    @unittest.skipUnless(hasattr(os, "geteuid") and os.geteuid() == 0, "needs root to chown")
    def test_a_counter_of_another_user_is_refused(self):
        path = self.p.counters / "gw-subagents-s1"
        path.write_text("1")
        os.chown(path, 12345, 12345)
        self.assertAsks(self.p.call("s1"), "cannot count", "not a regular file of this user")
        self.assertEqual(path.read_text(), "1")

    def test_a_counter_that_is_not_a_regular_file_is_refused(self):
        fifo = self.p.counters / "gw-subagents-s1"
        os.mkfifo(fifo)
        self.assertAsks(self.p.call("s1"), "cannot count", "not a regular file of this user")

    def test_a_hard_link_as_the_counter_is_refused_and_never_overwritten(self):
        victim = self.tmp / "victim"
        victim.write_text("important data")
        os.link(victim, self.p.counters / "gw-subagents-s1")
        self.assertAsks(self.p.call("s1"), "cannot count", "single link")
        self.assertEqual(victim.read_text(), "important data")

    def test_no_cleaning_when_the_counter_already_exists(self):
        self.assertQuiet(self.p.call("a"))
        old = self.stale("gw-subagents-gone")
        self.assertQuiet(self.p.call("a"))
        self.assertTrue(old.exists())

    def test_a_link_named_like_a_counter_is_not_deleted_nor_followed_by_the_cleaning(self):
        target = self.tmp / "target"
        target.write_text("keep")
        link = self.p.counters / "gw-subagents-link"
        link.symlink_to(target)
        os.utime(link, (1, 1), follow_symlinks=False)
        self.assertQuiet(self.p.call("fresh"))
        self.assertTrue(link.is_symlink())
        self.assertEqual(target.read_text(), "keep")

    def test_a_symlink_as_the_counter_is_refused_and_never_written_through(self):
        target = self.tmp / "victim"
        target.write_text("precious")
        (self.p.counters / "gw-subagents-s1").symlink_to(target)
        self.assertAsks(self.p.call("s1"), "cannot count", "symbolic link", "not followed")
        self.assertEqual(target.read_text(), "precious")

    def test_a_dangling_symlink_is_refused_and_creates_nothing(self):
        target = self.tmp / "nowhere"
        (self.p.counters / "gw-subagents-s1").symlink_to(target)
        self.assertAsks(self.p.call("s1"), "symbolic link")
        self.assertFalse(target.exists())


class ModelWarning(Base):
    cfg = {"subagentCap": 3}

    def context(self, result):
        code, out = result
        self.assertEqual(code, 0, out)
        spec = self.answer(out)
        self.assertNotIn("permissionDecision", spec, "a missing model warns, it never asks or denies")
        return spec["additionalContext"]

    def no_model(self, tool_input):
        return self.p.call(tool_input=tool_input)

    def test_a_call_without_model_gets_a_warning_and_is_not_blocked(self):
        for tool_input in ({"prompt": "x"}, {"prompt": "x", "model": ""}, {"prompt": "x", "model": "  "},
                           {"prompt": "x", "model": None}, {"prompt": "x", "model": 3}, "text", None):
            with self.subTest(tool_input=tool_input):
                shutil.rmtree(self.p.counters)
                self.p.counters.mkdir()
                note = self.context(self.no_model(tool_input))
                self.assertIn("no `model`", note)
                self.assertIn("gw-selector", note)

    def test_a_call_with_model_has_no_warning(self):
        for model in ("haiku", "sonnet", "claude-sonnet-5-5"):
            with self.subTest(model=model):
                shutil.rmtree(self.p.counters)
                self.p.counters.mkdir()
                self.assertQuiet(self.p.call(tool_input={"prompt": "x", "model": model}))

    def test_inherit_in_the_call_is_not_a_model(self):
        for model in ("inherit", " Inherit "):
            with self.subTest(model=model):
                shutil.rmtree(self.p.counters)
                self.p.counters.mkdir()
                self.assertIn("gw-selector", self.context(self.p.call(tool_input={"prompt": "x", "model": model})))

    def test_the_warning_says_it_is_for_the_next_calls(self):
        self.assertIn("next calls", self.context(self.p.call(tool_input={"prompt": "x"})))

    def test_a_subagent_type_that_sets_its_model_is_not_warned(self):
        self.p.agent("cheap", "---\nname: cheap\nmodel: haiku\n---\nbody\n")
        self.p.agent("quoted", "---\nmodel: 'sonnet'\n---\n", user=True)
        for name in ("cheap", "quoted"):
            with self.subTest(name=name):
                self.assertQuiet(self.p.call(name, tool_input={"prompt": "x", "subagent_type": name}))

    def test_a_subagent_type_that_inherits_or_has_no_definition_is_warned(self):
        self.p.agent("inh", "---\nmodel: inherit\n---\n")
        self.p.agent("nomodel", "---\nname: nomodel\n---\nmodel: haiku\n")  # outside the frontmatter
        self.p.agent("nofront", "model: haiku\n")
        for name in ("inh", "nomodel", "nofront", "missing", "../x", ""):
            with self.subTest(name=name):
                shutil.rmtree(self.p.counters)
                self.p.counters.mkdir()
                self.assertIn("gw-selector",
                              self.context(self.p.call(tool_input={"prompt": "x", "subagent_type": name})))

    def test_the_warning_is_also_added_when_the_hook_asks(self):
        (self.p.counters / "gw-subagents-s1").symlink_to(self.tmp / "nowhere")
        code, out = self.p.call("s1", tool_input={"prompt": "x"})
        spec = self.answer(out)
        self.assertEqual(spec["permissionDecision"], "ask", out)
        self.assertIn("symbolic link", spec["permissionDecisionReason"])
        self.assertIn("gw-selector", spec["additionalContext"])
        code, out = self.p.raw(json.dumps({"tool_input": {"prompt": "x"}}))
        spec = self.answer(out)
        self.assertIn("no session_id", spec["permissionDecisionReason"])
        self.assertIn("gw-selector", spec["additionalContext"])

    def test_an_ask_with_a_model_has_no_warning(self):
        (self.p.counters / "gw-subagents-s1").symlink_to(self.tmp / "nowhere")
        spec = self.answer(self.p.call("s1")[1])
        self.assertNotIn("additionalContext", spec)

    def test_the_task_tool_is_warned_too(self):
        self.assertIn("gw-selector", self.context(self.p.call(tool="Task", tool_input={"prompt": "x"})))

    def test_at_the_cap_without_model_one_answer_has_the_ask_and_the_warning(self):
        self.assertQuiet(self.p.call())
        self.assertQuiet(self.p.call())
        code, out = self.p.call(tool_input={"prompt": "x"})
        spec = self.answer(out)
        self.assertEqual(spec["permissionDecision"], "ask", out)
        self.assertIn("3 subagents", spec["permissionDecisionReason"])
        self.assertIn("gw-selector", spec["additionalContext"])

    def test_the_call_without_model_is_still_counted(self):
        self.context(self.p.call(tool_input={"prompt": "x"}))
        self.context(self.p.call(tool_input={"prompt": "x"}))
        self.assertAsks(self.p.call(), "3 subagents")


class CapOfOne(Base):
    cfg = {"subagentCap": 1}

    def test_asks_at_the_first_and_at_the_eleventh(self):
        for n in range(1, 13):
            with self.subTest(n=n):
                result = self.p.call()
                if n in (1, 11):
                    self.assertAsks(result, self.reason(n, 1))
                else:
                    self.assertQuiet(result)


class DefaultCap(Base):
    def test_default_is_thirty_and_never_denies(self):
        for n in range(1, 41):
            with self.subTest(n=n):
                result = self.p.call()
                if n in (30, 40):
                    self.assertEqual(self.assertAsks(result), self.reason(n, 30))
                    self.assertNotIn("deny", result[1])
                else:
                    self.assertQuiet(result)

    def test_the_counter_defaults_to_the_temp_directory(self):
        env = {"GW_SUBAGENT_COUNTER_DIR": "", "TMPDIR": str(self.tmp)}
        self.assertQuiet(self.p.call("in-the-temp-dir", env=env))
        found = [f for f in self.tmp.iterdir() if f.is_file() and "in-the-temp-dir" in f.name]
        self.assertEqual(len(found), 1, sorted(f.name for f in self.tmp.iterdir()))
        self.assertEqual(list(self.p.counters.iterdir()), [])


class ConfigProblems(Base):
    def test_an_unreadable_config_uses_the_default_and_still_counts(self):
        (self.p.work / ".claude" / "gw.json").write_text("{ this is not json")
        for n in range(1, 31):
            with self.subTest(n=n):
                result = self.p.call()
                if n == 30:
                    self.assertAsks(result, self.reason(30, 30))
                else:
                    self.assertQuiet(result)

    def test_an_invalid_cap_in_the_config_uses_the_default(self):
        cfg = json.loads((self.p.work / ".claude" / "gw.json").read_text())
        cfg["subagentCap"] = 0
        (self.p.work / ".claude" / "gw.json").write_text(json.dumps(cfg))
        for _ in range(29):
            self.assertQuiet(self.p.call())
        self.assertAsks(self.p.call(), "30 subagents", "subagentCap 30")


class FailClosed(Base):
    def test_unusable_stdin_asks_with_that_reason(self):
        cases = {"": "not valid JSON", "not json": "not valid JSON", "[1, 2]": "not a JSON object",
                 '"text"': "not a JSON object"}
        for text, why in cases.items():
            with self.subTest(stdin=text):
                result = self.p.raw(text)
                self.assertAsks(result, "could not use the hook event", "cannot count", why)

    def test_no_session_id_asks_that_it_cannot_count(self):
        for session in (None, "", 7, ["s"]):
            with self.subTest(session=session):
                event = self.p.event(None)
                if session is not None:
                    event["session_id"] = session
                self.assertAsks(self.p.raw(json.dumps(event)), "no session_id", "cannot count")

    def test_a_counter_it_cannot_write_asks_that_it_cannot_count(self):
        blocker = self.tmp / "not-a-folder"
        blocker.write_text("x")
        result = self.p.call(env={"GW_SUBAGENT_COUNTER_DIR": str(blocker)})
        self.assertAsks(result, "cannot count", "subagent counter")


if __name__ == "__main__":
    unittest.main()
