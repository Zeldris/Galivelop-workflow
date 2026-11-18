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


class Format(Cli):
    """C7 review 3: `set` changes the text of one value and nothing else."""

    def check(self, text, mode, word, expected_text):
        self.config.write_bytes(text.encode())
        code, out, err = self.run_cli("set", mode, word)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.config.read_bytes().decode(), expected_text)
        self.assertFalse(self.config.with_name("gw.json.tmp").exists())

    def base(self, extra=""):
        data = json.dumps(BASE_CONFIG)[:-1]
        return data + extra + "}"

    def test_compact_sections_and_an_existing_value_change_one_word(self):
        text = self.base(', "modes": {"careful": true, "carefulExempt": ["/tmp/"]}, "models": {"disabled": []}') + "\n"
        self.check(text, "careful", "off", text.replace('"careful": true', '"careful": false'))

    def test_a_missing_key_is_added_after_the_last_member_with_its_indent(self):
        text = self.base(', "modes": {"careful": true}') + "\n"
        self.check(text, "questions", "on", text.replace('{"careful": true}', '{"careful": true, "questions": true}'))
        text = '{\r\n\t"a": 1,\r\n\t"modes": {\r\n\t\t"careful": true\r\n\t}\r\n}\r\n'
        self.config.write_bytes(text.encode())
        # not a valid config for the schema (unknown key a)? use the edit function directly for the byte check
        import importlib.util
        spec = importlib.util.spec_from_file_location("gw_mode_fmt", ROOT / "scripts" / "mode.py")
        mode = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mode)
        self.assertEqual(mode.edit_text(text, "questions", True),
                         '{\r\n\t"a": 1,\r\n\t"modes": {\r\n\t\t"careful": true,\r\n\t\t"questions": true\r\n\t}\r\n}\r\n')
        self.assertEqual(mode.edit_text(text, "careful", False).count("\r\n"), text.count("\r\n"))

    def test_a_missing_modes_section_is_added_and_crlf_is_kept(self):
        text = self.base().replace("{", "{\r\n  ", 1) + "\r\n"
        self.config.write_bytes(text.encode())
        code, out, err = self.run_cli("set", "questions", "on")
        self.assertEqual(code, 0, err)
        after = self.config.read_bytes().decode()
        self.assertIn('"modes": {"questions": true}', after)
        self.assertEqual(after.replace('"modes": {"questions": true}', "", 1).count("\n"), text.count("\n"))
        self.assertNotIn("\n", after.replace("\r\n", ""))  # no bare LF appeared
        self.assertEqual(json.loads(after).get("modes"), {"questions": True})

    def test_an_empty_modes_object_gets_its_member(self):
        text = self.base(', "modes": {}') + "\n"
        self.check(text, "questions", "on", text.replace('"modes": {}', '"modes": {"questions": true}'))


class Atomic(Cli):
    def test_a_failing_write_leaves_the_file_and_says_so(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("gw_mode_atomic", ROOT / "scripts" / "mode.py")
        mode = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mode)
        old = self.config.read_bytes()
        real = mode.os.replace
        mode.os.replace = lambda *a: (_ for _ in ()).throw(OSError("disk full"))
        try:
            with self.assertRaises(OSError):
                mode.write(self.tmp, "questions", True)
        finally:
            mode.os.replace = real
        self.assertEqual(self.config.read_bytes(), old)
        self.assertFalse(self.config.with_name("gw.json.tmp").exists())


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
