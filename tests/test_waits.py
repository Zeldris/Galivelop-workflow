"""tests/waits.py (B37): the factor GW_TEST_TIMEOUT_SCALE, and no literal wait left in a test outside it."""
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import waits  # noqa: E402

# A literal wait: a timeout= number, a deadline `time()/monotonic() + n`, a watchdog Timer(n, …), or a polling loop
# `for _ in range(n):` with a sleep in its next lines. A line that is not a wait (a config value named timeout) says so
# with `# not a wait`.
LITERAL = re.compile(r"\btimeout\s*=\s*\d|\b(?:time|monotonic)\(\)\s*\+\s*\d|\bTimer\(\s*\d")
POLL = re.compile(r"^\s*for _ in range\(\s*\d+\s*\):")
MARK = "# not a wait"


def literal_waits(path, text):
    lines = text.splitlines()
    found = []
    for n, line in enumerate(lines, 1):
        if MARK in line:
            continue
        if LITERAL.search(line) or (POLL.search(line) and any("sleep(" in l for l in lines[n:n + 3])):
            found.append(f"{path}:{n}: {line.strip()}")
    return found


class Scale(unittest.TestCase):
    def env(self, value):
        env = {k: v for k, v in os.environ.items() if k != waits.VAR}
        if value is not None:
            env[waits.VAR] = value
        return mock.patch.dict(os.environ, env, clear=True)

    def test_unset_or_empty_is_one(self):
        for value in (None, "", "  "):
            with self.env(value):
                self.assertEqual((waits.scale(), waits.timeout(20)), (1.0, 20))

    def test_the_factor_multiplies_every_wait(self):
        with self.env("2.5"):
            self.assertEqual(waits.timeout(20), 50)
            with mock.patch.object(waits.time, "monotonic", side_effect=[0, 49, 51]), \
                    mock.patch.object(waits.time, "sleep") as sleep:
                self.assertFalse(waits.wait_for(lambda: False, 20))
            self.assertEqual(sleep.call_count, 1, "polled until 20 x 2.5 s, not 20 s")

    def test_a_bad_value_fails_closed_naming_the_variable_and_the_fix(self):
        for value in ("0", "-1", "abc", "nan", "inf"):
            with self.env(value), self.assertRaises(ValueError) as ctx:
                waits.timeout(1)
            self.assertIn(f"{waits.VAR}={value!r} is not a number > 0", str(ctx.exception))
            self.assertIn(f"export {waits.VAR}=1", str(ctx.exception))


class WaitFor(unittest.TestCase):
    def setUp(self):
        # the runner's own factor (3 on the macOS CI) would move the mocked deadlines
        env = {k: v for k, v in os.environ.items() if k != waits.VAR}
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_returns_true_as_soon_as_the_predicate_holds(self):
        calls = []
        with mock.patch.object(waits.time, "sleep") as sleep:
            self.assertTrue(waits.wait_for(lambda: calls.append(1) or len(calls) >= 3))
        self.assertEqual(sleep.call_count, 2)

    def test_returns_the_value_of_the_predicate(self):
        self.assertEqual(waits.wait_for(lambda: "found"), "found")

    def test_past_the_deadline_returns_the_predicate_checked_once_more(self):
        with mock.patch.object(waits.time, "monotonic", side_effect=[0, 30]), mock.patch.object(waits.time, "sleep"):
            self.assertFalse(waits.wait_for(lambda: False, 20))


class NoLiteralWaits(unittest.TestCase):
    def test_the_scan_finds_each_kind_and_skips_the_marked_line(self):
        text = "\n".join([
            "p.communicate(timeout=20)",
            "p.wait(timeout = 5)",
            "deadline = time.time() + 20",
            "deadline = time.monotonic() + 5",
            "threading.Timer(10, proc.kill)",
            "for _ in range(100):",
            "    if x: break",
            "    time.sleep(0.1)",
            "for _ in range(3):",
            "    run()",
            "self.config(timeout=7)  # not a wait",
            "p.communicate(timeout=waits.timeout(20))",
        ])
        self.assertEqual([f.split(":")[1] for f in literal_waits("t.py", text)], ["1", "2", "3", "4", "5", "6"])

    def test_no_test_has_a_literal_wait_outside_waits_py(self):
        files = subprocess.run(["git", "ls-files", "--", "tests/test_*.py", "skills/*/scripts/test_*.py"], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.split()
        self.assertIn("tests/test_hooks.py", files)
        found = [f for name in files if name != "tests/test_waits.py"  # this file: the scanner and its samples
                 for f in literal_waits(name, (ROOT / name).read_text(encoding="utf-8"))]
        self.assertEqual(found, [], "literal waits outside tests/waits.py: use waits.timeout(n) or waits.wait_for(...) "
                                    f"so {waits.VAR} scales them (or mark a non-wait with '{MARK}')")


if __name__ == "__main__":
    unittest.main()
