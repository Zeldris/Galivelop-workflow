"""scripts/models.py (B7): the rule that says which entry of `models.disabled` blocks a model, and the CLI that lists,
checks, disables and enables models in .claude/gw.json. Every failing case checks the message, not only the exit code.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_hooks import BASE_CONFIG, ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("gw_models", ROOT / "scripts" / "models.py")
models = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(models)


class BlockedBy(unittest.TestCase):
    def test_the_rule(self):
        cases = [
            ("claude-opus-5-5", ["claude-opus-5-5"], "claude-opus-5-5"),
            ("Claude-Opus-5-5[1m]", ["claude-opus-5-5"], "claude-opus-5-5"),  # case and context suffix ignored
            ("claude-opus-5-5", ["claude-opus"], "claude-opus"),  # an id prefix followed by `-`
            ("claude-haiku-4-5-20251001", ["claude-haiku-4-5"], "claude-haiku-4-5"),  # a dated id
            ("claude-opus-5-5", ["opus"], "opus"),  # the family alias covers every id of the family
            ("opus", ["OPUS"], "OPUS"),
            ("opus", ["claude-opus-5-5"], None),  # a full id never blocks the alias
            ("claude-opus-5-50", ["claude-opus-5-5"], None),  # a prefix needs the `-` after it
            ("claude-sonnet-5-5", ["opus", "haiku"], None),
            ("claude-fable-5-1", ["fable"], "fable"),
            ("gpt-5", ["opus"], None),
            ("", ["opus"], None),
            ("claude-opus-5-5", ["", 3, None], None),  # entries that are not names are skipped
        ]
        for model, disabled, expected in cases:
            with self.subTest(model=model, disabled=disabled):
                self.assertEqual(models.blocked_by(model, disabled), expected)


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gw-models-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        (self.tmp / ".claude").mkdir()
        self.config = self.tmp / ".claude" / "gw.json"
        self.config.write_text(json.dumps(BASE_CONFIG, indent=2) + "\n")

    def run_cli(self, *args):
        r = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "models.py"), "--root", str(self.tmp), *args],
                           capture_output=True, text=True)
        return r.returncode, r.stdout, r.stderr

    def disabled(self):
        return json.loads(self.config.read_text()).get("models", {}).get("disabled")

    def test_list_is_empty_by_default(self):
        self.assertEqual(self.run_cli("list"), (0, "", ""))

    def test_disable_then_check_then_enable(self):
        code, out, _ = self.run_cli("disable", "Opus", "claude-haiku-4-5", "opus")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.disabled(), ["opus", "claude-haiku-4-5"])  # lower case, once each
        self.assertEqual(self.run_cli("list")[1], "opus\nclaude-haiku-4-5\n")
        code, out, _ = self.run_cli("check", "claude-opus-5-5")
        self.assertEqual(code, 1)
        self.assertIn("disabled by `opus`", out)
        self.assertIn("enable opus", out)
        self.assertEqual(self.run_cli("check", "sonnet")[0], 0)
        code, out, _ = self.run_cli("enable", "OPUS")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.disabled(), ["claude-haiku-4-5"])

    def test_the_file_keeps_its_keys_in_order(self):
        self.run_cli("disable", "opus")
        data = json.loads(self.config.read_text())
        self.assertEqual(list(data)[:len(BASE_CONFIG)], list(BASE_CONFIG))
        self.assertTrue(self.config.read_text().endswith("}\n"))

    def test_enable_of_an_entry_not_in_the_list_fails_and_writes_nothing(self):
        self.run_cli("disable", "opus")
        before = self.config.read_text()
        code, _, err = self.run_cli("enable", "claude-opus-5-5")
        self.assertEqual(code, 2)
        self.assertIn("claude-opus-5-5 not in models.disabled (it holds: opus)", err)
        self.assertEqual(self.config.read_text(), before)

    def test_enable_says_when_another_entry_still_blocks(self):
        self.run_cli("disable", "opus", "claude-opus-5-5")
        code, out, _ = self.run_cli("enable", "claude-opus-5-5")
        self.assertEqual(code, 0)
        self.assertIn("claude-opus-5-5 is still blocked by `opus`", out)

    def test_an_empty_name_is_refused(self):
        code, _, err = self.run_cli("disable", " ")
        self.assertEqual(code, 2)
        self.assertIn("an empty model name", err)
        self.assertIsNone(self.disabled())

    def test_an_invalid_config_fails_closed(self):
        self.config.write_text(json.dumps(dict(BASE_CONFIG, models={"disabled": "opus"})))
        code, _, err = self.run_cli("list")
        self.assertEqual(code, 2)
        self.assertIn("gw models:", err)
        self.assertIn("models.disabled", err)

    def test_config_get_fills_the_inner_default(self):
        self.config.write_text(json.dumps(dict(BASE_CONFIG, models={})))
        r = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "config.py"), "--root", str(self.tmp), "get",
                            "models.disabled", "--json"], capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "[]"), r.stderr)


def said(text, model="claude-sonnet-5-5"):
    """An assistant transcript row with one text block."""
    return {"type": "assistant", "message": {"model": model, "content": [{"type": "text", "text": text}]}}


class SessionCheck(unittest.TestCase):
    """D142: the selector's `Session: <model> <effort>` line against the model the session runs on."""

    def check(self, rows, hook_model=None):
        return models.session_check(rows, hook_model)

    def test_a_different_family_warns_with_the_switch(self):
        line = self.check([said("Session: large high (current: Sonnet medium) · Subagents: none · Skill: none")])
        self.assertIn("recommends opus for this session, but it runs on claude-sonnet-5-5", line)
        self.assertIn("/model opus", line)
        self.assertIn("models.sessionCheck false", line)

    def test_cases_that_stay_silent(self):
        cases = {
            "same family, context suffix": [said("**Session:** Opus high", "claude-opus-5-5[1m]")],
            "either of two": [said("Session: medium or light low", "claude-haiku-4-5")],
            "no selector line": [said("Nothing to pick here")],
            "the skill's placeholder": [said("`Session: <model> <effort> (current: ...)`")],
            "a model outside the families": [said("Session: gpt-5 high")],
            "an unknown current model": [said("Session: large high", "gpt-5")],
            "only a synthetic model": [said("Session: large high", "<synthetic>")],
            "nothing": [],
        }
        for name, rows in cases.items():
            with self.subTest(name):
                self.assertIsNone(self.check(rows))

    def test_the_last_line_and_the_last_model_win(self):
        rows = [said("Session: large high", "claude-opus-5-5"), said("Session: medium medium", "claude-opus-5-5"),
                {"type": "user", "message": {"content": "Session: light low"}},
                said("done", "claude-sonnet-5-5")]
        self.assertIsNone(self.check(rows))  # the user's text is not the selector line; the newest model is sonnet
        self.assertIn("runs on claude-opus-5-5", self.check(rows, "claude-opus-5-5"))  # the hook's model wins

    def test_cli_reads_the_tail_and_respects_the_key(self):
        tmp = Path(tempfile.mkdtemp(prefix="gw-models-")).resolve()
        self.addCleanup(shutil.rmtree, tmp, True)
        subprocess.run(["git", "init", "-q", str(tmp)], check=True)
        (tmp / ".claude").mkdir()
        transcript = tmp / "t.jsonl"
        transcript.write_text('{"cut li\n' + json.dumps(said("Session: large high")) + "\n")

        def run(cfg, path=transcript):
            (tmp / ".claude" / "gw.json").write_text(json.dumps(cfg))
            return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "models.py"), "--root", str(tmp),
                                   "session-check", "--transcript", str(path)], capture_output=True, text=True)
        r = run(BASE_CONFIG)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("recommends opus", r.stdout)
        self.assertEqual(run(dict(BASE_CONFIG, models={"sessionCheck": False})).stdout, "")
        r = run(BASE_CONFIG, tmp / "missing.jsonl")
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
