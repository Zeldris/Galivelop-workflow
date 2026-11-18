"""scripts/mode.py (C6, C7): list, line and set over the `modes` section of .claude/gw.json. Every failing case checks
the message, not only the exit code.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-mode-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        (self.tmp / ".claude").mkdir()
        self.config = self.tmp / ".claude" / "gw.json"
        self.write(dict(BASE_CONFIG))

    def write(self, data):
        self.config.write_text(json.dumps(data, indent=2) + "\n")

    def run_cli(self, *args):
        r = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "mode.py"), "--root", str(self.tmp), *args],
                           capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr

    def modes(self):
        return json.loads(self.config.read_text()).get("modes")


class List(Cli):
    def test_lists_every_boolean_mode_then_the_lists_read_only(self):
        code, out, err = self.run_cli("list")
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("careful: on (true) - "), lines)
        self.assertTrue(lines[1].startswith("questions: guide (false) - "), lines)
        self.assertIn("questions-guard.py (C4, C5)", lines[1])
        self.assertTrue(any(l.startswith("carefulExempt: [") and "read-only" in l for l in lines), lines)
        self.assertTrue(any(l.startswith("carefulWorktrees: [") and "read-only" in l for l in lines), lines)

    def test_questions_true_reads_restrictive(self):
        self.write(dict(BASE_CONFIG, modes={"questions": True}))
        code, out, err = self.run_cli("list")
        self.assertEqual(code, 0, err)
        self.assertIn("questions: restrictive (true) - ", out)
        self.assertEqual(self.run_cli("line")[1], "Modes: careful on, questions restrictive\n")

    def test_missing_modes_section_shows_the_defaults(self):
        self.assertNotIn("modes", json.loads(self.config.read_text()))
        code, out, err = self.run_cli("line")
        self.assertEqual((code, out), (0, "Modes: careful on, questions guide\n"), err)


class Set(Cli):
    def test_round_trip_keeps_the_rest_of_the_file(self):
        before = json.loads(self.config.read_text())
        self.assertEqual(self.run_cli("set", "questions", "on")[:2], (0, "modes.questions: restrictive (true)\n"))
        after = json.loads(self.config.read_text())
        self.assertEqual(after["modes"], {"questions": True})
        self.assertEqual({k: v for k, v in after.items() if k != "modes"}, before)
        self.assertTrue(self.config.read_text().startswith("{\n  \""))  # two-space JSON kept
        self.assertEqual(self.run_cli("set", "questions", "off")[:2], (0, "modes.questions: guide (false)\n"))
        self.assertEqual(self.modes(), {"questions": False})

    def test_keeps_the_other_keys_of_modes(self):
        self.write(dict(BASE_CONFIG, modes={"careful": True, "carefulExempt": ["/x/"]}))
        self.assertEqual(self.run_cli("set", "careful", "off")[0], 0)
        self.assertEqual(self.modes(), {"careful": False, "carefulExempt": ["/x/"]})

    def test_accepts_true_false_words_and_upper_case(self):
        self.assertEqual(self.run_cli("set", "careful", "FALSE")[0], 0)
        self.assertEqual(self.modes(), {"careful": False})
        self.assertEqual(self.run_cli("set", "careful", "Yes")[0], 0)
        self.assertEqual(self.modes(), {"careful": True})

    def test_unknown_mode_changes_nothing(self):
        old = self.config.read_text()
        code, out, err = self.run_cli("set", "bogus", "on")
        self.assertEqual(code, 2)
        self.assertIn("unknown mode `bogus` (known: careful, questions)", err)
        self.assertIn("python3 mode.py list", err)
        self.assertEqual(self.config.read_text(), old)

    def test_a_list_key_is_not_a_mode(self):
        code, out, err = self.run_cli("set", "carefulExempt", "on")
        self.assertEqual(code, 2)
        self.assertIn("unknown mode `carefulExempt`", err)

    def test_bad_value_changes_nothing(self):
        old = self.config.read_text()
        code, out, err = self.run_cli("set", "questions", "maybe")
        self.assertEqual(code, 2)
        self.assertIn("`maybe` is not on or off", err)
        self.assertIn("set questions on|off", err)
        self.assertEqual(self.config.read_text(), old)


class Broken(Cli):
    def test_invalid_json_fails_closed_with_the_fix(self):
        self.config.write_text("{not json")
        for args in (("list",), ("line",), ("set", "questions", "on")):
            with self.subTest(args=args):
                code, out, err = self.run_cli(*args)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("invalid JSON", err)
                self.assertIn("fix .claude/gw.json, then: python3 mode.py list", err)
        self.assertEqual(self.config.read_text(), "{not json")

    def test_missing_config_fails_closed(self):
        self.config.unlink()
        code, out, err = self.run_cli("set", "questions", "on")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("gw mode:", err)
        self.assertFalse(self.config.exists())

    def test_invalid_value_in_modes_fails_closed(self):
        self.write(dict(BASE_CONFIG, modes={"careful": "yes"}))
        old = self.config.read_text()
        code, out, err = self.run_cli("set", "questions", "on")
        self.assertEqual(code, 2)
        self.assertIn("modes.careful", err)
        self.assertEqual(self.config.read_text(), old)


class Writer(Cli):
    def test_a_write_that_makes_the_config_invalid_puts_the_old_text_back(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import importlib.util
        spec = importlib.util.spec_from_file_location("gw_mode", ROOT / "scripts" / "mode.py")
        mode = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mode)
        old = self.config.read_text()
        with self.assertRaises(mode.config.ConfigError):
            mode.write(self.tmp, "careful", "not a boolean")
        self.assertEqual(self.config.read_text(), old)


if __name__ == "__main__":
    unittest.main()
