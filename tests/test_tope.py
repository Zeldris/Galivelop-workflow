"""PreToolUse hook: scripts/tope-subagentes.py (P3 of docs/propuestas/2026-10-25-repos-x.md), in a temporary project
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

from test_ganchos import ROOT, Project

SCRIPT = "tope-subagentes.py"


class TopeProject(Project):
    def __init__(self, tmp, config=None):
        super().__init__(tmp, config=config, hooks=())
        self.scripts = self.work / ".claude" / "gw" / "scripts"
        shutil.copy2(ROOT / "scripts" / SCRIPT, self.scripts / SCRIPT)
        self.counters = tmp / "counters"
        self.counters.mkdir()
        self.env["GW_SUBAGENT_COUNTER_DIR"] = str(self.counters)

    def event(self, session="s1", tool="Agent", **extra):
        data = {"hook_event_name": "PreToolUse", "cwd": str(self.work), "tool_name": tool,
                "tool_input": {"prompt": "do it"}}
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
        self.p = TopeProject(self.tmp, self.cfg)

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
                f"check they are not looping (opt-tokens)")


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
